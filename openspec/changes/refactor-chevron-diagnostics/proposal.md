# Proposal

## Why

Chevron writes recoverable diagnostics directly to stderr, preventing applications from routing them through their own logging. A per-render diagnostic interface will centralise delivery and support useful severity levels without changing rendering results or requiring global logging configuration.

## What Changes

- Add an optional `logger(level, message)` callback to `render`, compatible with a standard-library logger's bound `log` method, and a minimum `log_level` defaulting to WARNING.
- Route diagnostics through a default stderr callback when no logger is supplied. Preserve existing warning wording and newline behaviour.
- Keep `warn=False` as the master switch: suppress all diagnostic delivery, even with a supplied logger or DEBUG threshold. Exceptions still propagate.
- With diagnostics enabled, distinguish fatal template errors (ERROR), recoverable conditions (WARNING), render lifecycle information (INFO), and bounded rendering decisions (DEBUG).
- Carry diagnostic configuration through recursive rendering in per-render state, without module-level mutable configuration.
- Keep tokenisation free of output side effects and preserve exception types, messages and rendering semantics.

## Capabilities

### New Capabilities

- `render-diagnostics`: Per-render diagnostic routing, suppression, severity filtering and recursive error reporting.

### Modified Capabilities

None. Existing lambda requirements already condition diagnostics on `warn=True`; their rendering behaviour is unchanged.

## Impact

Affects renderer diagnostics, the stderr adapter, focused behavioural tests and public API documentation. Uses only standard-library logging level constants, with no new dependency or global logging setup. New parameters are keyword-only and do not move existing positional arguments.

This can be implemented separately from `refactor-simplify-renderer`; if that change lands first, use its configuration/state separation. The later `add-async-renderer` must reuse this diagnostic contract and provide non-blocking delivery rather than introducing a separate hard-coded stderr path. Async execution itself is outside this change.
