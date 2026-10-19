# Design

## Context

See proposal.md for motivation. Currently `_get_key`, `_ExplicitSource` and `ChevronRender.empty_result` write directly to stderr. Their callers use `warn` to suppress output. The tokenizer raises `ChevronError` with line information rather than logging. `cli_main` separately handles syntax exceptions and writes rendered content to stdout.

The renderer simplification is implemented: `ChevronRender` composes immutable `_RenderConfig`, a per-invocation `_RenderState`, frames and callable-resolution policies. The async renderer remains proposed. This change extends the existing configuration boundary and does not require a second rendering engine.

## Goals / Non-Goals

Centralise diagnostic routing through standard Python logging, preserve recursive configuration and exception semantics, and make the output boundary reusable by an async engine.

Do not configure Python's root logger from the library, add handlers to application loggers, introduce a diagnostic framework or event bus, implement async rendering, or treat rendered output as logging. The CLI configures ordinary process-level logging for its own invocation. Application logging failures and arbitrary application exceptions are not automatically relabelled as template syntax errors.

## Decisions

### Native Python logging with application-owned configuration

Extend `render(..., lambdas=None, *, logger=None)`, where `logger` is a `logging.Logger` or `logging.LoggerAdapter`. Chevron emits diagnostics using native methods and deferred format arguments such as `logger.warning("Could not find key '%s'", key)`. The application owns handlers, filters, propagation and log levels for a supplied logger. Chevron validates the logger type before rendering but does not inspect its configuration or callback signature.

Chevron uses one shared logger identifier, `chevron`, for its default destination. The library adds no handler, invokes no `basicConfig`, and keeps no module-level active-render configuration, global handler or `ContextVar`. A lightweight per-render adapter carries the selected logger and threshold in `_RenderConfig`; recursive rendering reuses that configuration and independent public renders do not share it.

### `warn` retains default-output compatibility

Without a supplied logger, falsey `warn` values remain silent and truthy values select the shared `chevron` logger at `logging.WARNING`. This preserves Chevron's established truthiness behaviour, warning text and newline behaviour. A supplied logger takes precedence over `warn`; its per-render threshold is selected with keyword-only `log_level=`, while the application's handlers, propagation and levels remain its responsibility.

### Configuration follows the render, not the process

Store the selected logger adapter in the per-render `_RenderConfig`. Replace direct output in lookup and lambda result handling with standard logging calls. Keep lookup exception/fallback boundaries unchanged, except ensure a logging failure is not caught and treated as an ordinary lookup failure.

Recursive frames, partials and supplied callbacks retain the same diagnostic configuration. A new public `render` call gets its own configuration even when invoked inside a lambda or logger handler. No temporary global overrides or mutable current-frame references. Delivery is synchronous and in rendering order; thread safety of an application logger shared across multiple calls belongs to the application.

### Severity and initial event catalogue

| Level | Events |
| --- | --- |
| ERROR | Unhandled `ChevronError` escaping a public render, including source line information already supplied by that exception |
| WARNING | Existing missing key, prohibited callable traversal, rejected callable data and None lambda result warnings |
| INFO | Public render started and successfully completed; no completion event after failure |
| DEBUG | Name resolution outcome/source, selected lambda protocol, and partial source or missing/rejected outcome |

Keep missing partials' existing empty-result behaviour; DEBUG visibility is not a new WARNING or failure. Debug messages identify tag names and decisions, not scope values, template bodies, returned text, callable reprs or filesystem absolute paths. Existing warning wording remains unchanged for compatibility. User-supplied template names and exception messages are passed to the configured logger as existing output did; applications that render untrusted templates remain responsible for their log handling.

### Report fatal template errors once

The tokenizer remains pure and continues raising its existing exceptions. Catch `ChevronError` at the public rendering boundary, emit one eligible ERROR event, then use bare raise to preserve the original failure. Do not log errors again in recursive frames. A syntax error caught by application lambda code before reaching that boundary is not an unhandled fatal render error. Independent nested public renders have their own reporting boundaries; no global deduplication machinery is introduced.

Chevron relies on Python logging's normal handler and error semantics. It does not wrap a logger exception, retry delivery, report logging failure through itself, or fall back to stderr. This removes bespoke sink-error handling from rendering and keeps error policy with the application logging configuration.

### CLI and async boundaries

Keep CLI parser errors, exit status and rendered stdout separate from render diagnostics. The CLI configures ordinary process-level logging with the historic message-only stderr format, then invokes `render()` normally. `--warn` selects WARNING output; there is no CLI `--log-level` option or CLI-specific diagnostic logger. Direct programmatic `main()` calls continue forwarding renderer options normally.

The async renderer must reuse this Python logging contract. It calls the selected logger directly in message order. Its API documentation will briefly note that a supplied logger runs synchronously and should remain minimal because it blocks that render's execution. Logging is normally inexpensive; applications needing queue-backed logging configure it themselves. Pure event production must not write output itself. No async adapter or new dependency is implemented here. Whichever change lands second must preserve the shared contract.

## Risks / Trade-offs

- New ERROR reporting with `warn=True` increases library output on malformed templates → document the addition; default `warn=False` remains silent and errors retain their original exception semantics.
- Application loggers can filter, re-route or fail while handling events → that is standard logging behaviour and remains application responsibility.
- Debug instrumentation can cost time or expose data → use deferred logging arguments and limit events to names and decisions, without dumping values.
- Recursive warning delivery can drift during the engine refactor → parametrise behavioural tests across sections, partials and the supported lambda protocols.
- CLI syntax presentation can appear alongside renderer ERROR output when warnings are enabled → retain the established CLI exit status and simple standard logging configuration rather than introduce CLI-only filtering.

## Migration Plan

Existing callers need no changes. To integrate application logging, supply `logger=app_logger`; it replaces Chevron's default destination and its handlers, levels and propagation determine delivery. Use `log_level=logging.DEBUG` to request detailed diagnostics from a supplied logger. Without a logger, a truthy `warn` selects default WARNING output; a falsey value keeps it silent. `warn` never suppresses exceptions or a supplied logger. Preserve all existing positional arguments. No deployment or release process changes are required.
