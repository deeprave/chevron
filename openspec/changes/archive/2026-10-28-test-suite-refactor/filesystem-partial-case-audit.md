# Filesystem partial case audit

## Convert to shared filesystem cases

- default `.mustache` partial lookup;
- custom `partials_ext` lookup;
- nested relative partial names;
- configured partial mappings taking precedence over same-named files;
- ordinary missing filesystem partials rendering empty.

Each scenario is an ordinary temporary file tree and rendered-output contract,
so it runs through the sync runner and the async runner under asyncio and
Trio.

## Keep focused

Keep parent traversal, absolute names, symlink escapes, disabled filesystem
lookup, reader ownership, cancellation, non-blocking I/O, errors, and logging
in focused tests. Those require security or resource-lifecycle observations
beyond output.
