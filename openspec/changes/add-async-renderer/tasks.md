# Tasks

Prerequisite: implement `refactor-simplify-renderer`. Use its completed shared core; preserve parity with any conformance features implemented before this change.

## 1. Establish the async API and dependency boundary

- [ ] 1.1 Add the optional AnyIO async extra, Trio development dependency and AnyIO pytest backend fixtures; verify marked tests execute under asyncio and Trio while a base installation imports and renders without AnyIO.
- [ ] 1.2 Export an async entry point matching render configuration and document installation/runtime ownership; verify awaiting a basic template returns text and missing optional support gives an actionable error without breaking synchronous imports.

## 2. Implement shared-semantic async execution

- [ ] 2.1 Build the private async engine using the refactored policies, tokens, body collector and formatting helpers, with branch-owned frames and explicit recursive awaits; verify normal, inverted and iterable sections, token sequences, delimiters and padding against synchronous public-API cases on both backends.
- [ ] 2.2 Extract diagnostic production from direct writes while retaining immediate delivery through the shared synchronous Python logger under both APIs; verify default stderr and application-logger text, order and failure-path delivery, and briefly document that an async-render logger should remain minimal because it blocks that render.

## 3. Add awaitable lambda protocols

- [ ] 3.1 Invoke selected callbacks once and await awaitable results before protocol-specific processing; add parametrised tests for all decorators, both source policies, callable instances, ordinary results, None and propagated exceptions.
- [ ] 3.2 Supply the async compatibility render callback with temporary scope support and compatibility-only cache replay; document and test awaited recursion, falsey temporary data, synchronous awaitable-forwarding callbacks and recovered nested errors.
- [ ] 3.3 Add user-facing examples for async lambdas and explicit adaptation of blocking user callbacks; verify examples under both backends and preserve synchronous decorator metadata and binding tests.

## 4. Adapt template and partial I/O

- [ ] 4.1 Prepare async and ordinary file-like template inputs through awaited reads or worker adapters before pure tokenisation; verify suspended reads allow sibling progress and caller-owned readers remain open after success, errors and cancellation.
- [ ] 4.2 Add awaited filesystem partial loading with existing mapping precedence, suffix rules and containment; verify mapped and filesystem partial output, traversal/symlink rejection and progressing sibling tasks during blocked filesystem work.
- [ ] 4.3 Document resource ownership and worker-backed cancellation latency; verify renderer-owned resources close and filesystem exceptions preserve existing missing-partial semantics without swallowing cancellation.

## 5. Implement async iteration and cooperative state cleanup

- [ ] 5.1 Render async iterable sections sequentially with callable precedence and defined inverted-section truthiness; document the iterable contract and verify empty, nested, failing and cancelled iterators without closing caller-owned iterators implicitly.
- [ ] 5.2 Add cooperative checkpoints and exception-safe branch cleanup; use deterministic event/task-group tests for cancellation, independent renders and concurrent nested callback rendering without scope or diagnostic leakage.

## 6. Establish parity and performance evidence

- [ ] 6.1 Adapt shared behavioural and vendored specification cases to exercise sync and async engines without editing upstream expectations; verify all supported conformance cases pass on asyncio and Trio, including newer Mustache modules if already landed.
- [ ] 6.2 Extend benchmark scenarios for in-memory async rendering, recursive callbacks and partials with output checks; compare checkpoint overhead and representative synchronous performance without introducing timing-based test gates.

Routine checks, OpenSpec verification, review and delivery remain workflow hygiene outside the implementation checklist.
