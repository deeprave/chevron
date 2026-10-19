# Proposal

## Why

Chevron writes recoverable diagnostics directly to stderr, preventing applications from routing them through their own logging. A per-render Python logging interface will centralise delivery and support useful severity levels without changing rendering results or configuring the application's logging globally.

## What Changes

- Add an optional `logging.Logger` or `logging.LoggerAdapter` to `render`. Chevron uses native logging calls with deferred formatting; applications retain ownership of logger handlers, propagation and levels.
- Route diagnostics through the shared standard-library `chevron` logger when no logger is supplied. Preserve existing warning wording and newline behaviour without configuring global logging from the library.
- Retain `warn` as the truthiness-based opt-in switch for Chevron's default warning output. Add keyword-only `log_level=` for the delivery threshold of a supplied application logger; exceptions still propagate.
- With diagnostics enabled, distinguish fatal template errors (ERROR), recoverable conditions (WARNING), render lifecycle information (INFO), and bounded rendering decisions (DEBUG).
- Carry diagnostic configuration through recursive rendering in per-render state, without module-level mutable configuration.
- Keep tokenisation free of output side effects and preserve exception types, messages and rendering semantics.

## Capabilities

### New Capabilities

- `render-diagnostics`: Per-render diagnostic routing, suppression, severity filtering and recursive error reporting.

### Modified Capabilities

None. Existing lambda requirements already condition diagnostics on `warn=True`; their rendering behaviour is unchanged.

## Impact

Affects renderer diagnostics, the shared default logger, CLI logging configuration, focused behavioural tests and public API documentation. Uses only the standard library with no new dependency or library-owned global application logging setup. The new `logger=` and `log_level=` parameters are keyword-only and do not move existing positional arguments.

This builds on `refactor-simplify-renderer`'s configuration/state separation. The later `add-async-renderer` must reuse this diagnostic contract rather than introducing a separate hard-coded stderr path. Its supplied logger runs synchronously and should remain minimal because it blocks that render's execution. Async execution itself is outside this change.
