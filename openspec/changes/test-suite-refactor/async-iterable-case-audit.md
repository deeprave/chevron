# Async-iterable case audit

## Convert to async-only shared cases

- an async iterable renders each mapping item in an ordinary section;
- falsey async iterable items retain normal current-context rendering;
- an empty async iterable renders its section zero times.

Each factory creates a fresh async generator and runs only through the async
runner under asyncio and Trio.

## Keep focused

Keep async template readers, inverted-section non-consumption, iterator
errors, cancellation, ownership, and scheduling behavior focused. Those
contracts cannot be established by rendered output alone.
