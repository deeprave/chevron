# Design

## Context

See proposal.md for motivation. Currently `_get_key`, `_RenderContext.warn_rejected_callable_data` and `_RenderContext.warn_none_lambda_result` write directly to stderr. Their callers use `warn` to suppress output. The tokenizer raises `ChevronError` with line information rather than logging. `cli_main` separately handles syntax exceptions and writes rendered content to stdout.

The renderer simplification and async renderer are proposed, not implemented. This design works with today's `_RenderContext` or the refactor's separated configuration and invocation state; it does not require a second rendering engine.

## Goals / Non-Goals

Centralise diagnostic routing and filtering, preserve recursive configuration and exception semantics, and make the output boundary reusable by an async engine.

Do not configure Python's global logging, add handlers to application loggers, introduce a diagnostic framework or event bus, implement async rendering, change CLI argument parsing, or treat rendered output as logging. Application callback failures and arbitrary application exceptions are not automatically relabelled as template syntax errors.

## Decisions

### Small callback contract with an explicit gate

Extend `render(..., lambdas=None, *, logger=None, log_level=logging.WARNING)`. The callback accepts `(level: int, message: str)` and returns None; `logging.getLogger(...).log` can be passed directly. Use numeric logging levels rather than a Chevron enum or keyword-heavy record protocol. Validate callback callability and integer threshold as public configuration errors before rendering; do not inspect callback signatures. Async callbacks are not supported by the synchronous API.

`warn` remains the master switch for every severity. A custom sink and DEBUG threshold cannot bypass `warn=False`. When enabled, the threshold selects messages; the application logger can additionally apply its own filters. This avoids the confusing alternative in which supplying a logger silently enables warnings. The name `warn` is broader than its historical meaning, but renaming or replacing it is unnecessary API churn.

The default adapter reads the current `sys.stderr` when emitting, writes the message plus the platform newline, and adds no severity prefix to existing warnings. It implements the same callback contract as application sinks. No `basicConfig`, module-level active logger, global handler or ContextVar is needed. Do not construct expensive DEBUG messages or inspect application values when diagnostics are disabled.

### Configuration follows the render, not the process

Store the enabled flag, threshold and sink in the per-render configuration reachable from `_RenderContext`. Replace direct output in lookup and lambda result handling with calls through that interface. Keep lookup exception/fallback boundaries unchanged: routing diagnostics is not a reason to move value coercion outside `_get_key`'s compatibility exception handling.

Recursive frames, partials and supplied callbacks retain the same diagnostic configuration. A new public `render` call gets its own configuration even when invoked inside a lambda or diagnostic callback. No temporary global overrides or mutable current-frame references. Delivery is synchronous and in rendering order; thread safety of an application sink shared across multiple calls belongs to the application.

### Severity and initial event catalogue

| Level | Events |
| --- | --- |
| ERROR | Unhandled `ChevronError` escaping a public render, including source line information already supplied by that exception |
| WARNING | Existing missing key, prohibited callable traversal, rejected callable data and None lambda result warnings |
| INFO | Public render started and successfully completed; no completion event after failure |
| DEBUG | Name resolution outcome/source, selected lambda protocol, and partial source or missing/rejected outcome |

Keep missing partials' existing empty-result behaviour; DEBUG visibility is not a new WARNING or failure. Debug messages identify tag names and decisions, not scope values, template bodies, returned text, callable reprs or filesystem absolute paths. Escape control characters in new debug identifiers so template-controlled names cannot forge additional lines. Existing warning wording remains unchanged for compatibility. Do not promise secrecy for user-authored exception messages or legacy warning identifiers; document these limits.

### Report fatal template errors once

The tokenizer remains pure and continues raising its existing exceptions. Catch `ChevronError` at the public rendering boundary, emit one eligible ERROR event, then use bare raise to preserve the original failure. Do not log errors again in recursive frames. A syntax error caught by application lambda code before reaching that boundary is not an unhandled fatal render error. Independent nested public renders have their own reporting boundaries; no global deduplication machinery is introduced.

A normal diagnostic callback failure propagates without a retry or stderr fallback. Do not wrap sink invocation in the template-error catch region: a sink raising `ChevronError` must not recursively trigger itself. If the sink fails while reporting an existing template failure, catch ordinary sink exceptions solely to retain the original template error as primary; do not intercept process-control exceptions. This is a narrow safeguard, not general exception swallowing.

### CLI and async boundaries

Keep CLI parser errors, exit status and rendered stdout separate from render diagnostics. The existing terminal syntax-error presentation is still the CLI's responsibility. Route CLI calls through a small CLI-specific sink that forwards non-ERROR diagnostics to the default adapter and leaves fatal syntax presentation to its existing exception handler, avoiding duplicate ERROR text when `--warn` is enabled. This is an output adapter, not a tokenizer compatibility wrapper. Direct programmatic `main()` calls continue forwarding renderer options normally.

The async proposal currently describes ordered worker-backed stderr delivery. Its implementation must instead reuse this gate, severity and callback contract, with a default stderr adapter and non-blocking sink delivery. Pure event production must not write output itself; the async engine can drain per-operation events at awaitable boundaries. No async adapter or new dependency is implemented here. Whichever change lands second must preserve the shared contract.

## Risks / Trade-offs

- New ERROR reporting with `warn=True` increases library output on malformed templates → document the addition; default `warn=False` remains silent and errors retain their original exception semantics.
- Callback code can fail or re-enter rendering → isolate configuration, avoid recursive error reporting and test both cases through the public API.
- Debug instrumentation can cost time or expose data → check the gate before formatting and limit events to names and decisions, without dumping values.
- Recursive warning delivery can drift during the engine refactor → parametrise behavioural tests across sections, partials and the supported lambda protocols.
- Existing CLI syntax presentation could duplicate renderer errors → leave terminal presentation with the CLI handler and filter its renderer ERROR events locally.

## Migration Plan

Existing callers need no changes. To integrate application logging, supply `warn=True, logger=app_logger.log`. For debugging, additionally supply `log_level=logging.DEBUG`. Document that `warn=False` suppresses even ERROR delivery but never suppresses exceptions. Explain the synchronous callback contract and preserve all existing positional arguments. No deployment or release process changes are required.
