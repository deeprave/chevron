# Tasks

Prerequisite: implement `refactor-simplify-renderer`. Use its completed shared core; preserve parity with any conformance features implemented before this change.

## 1. Establish the async API and dependency boundary

- [x] 1.1 Add optional `anyio` and `trio` extras, matching development dependencies and AnyIO pytest backend fixtures; keep async tests separately collected only when AnyIO is installed, while a base installation imports and renders without it.
- [x] 1.2 Export a lazy async entry point matching render configuration and document installation/runtime ownership; keep the AnyIO-backed engine out of the synchronous renderer, and verify missing optional support gives an actionable error without breaking synchronous imports.

## 2. Implement shared-semantic async execution

- [x] 2.1 Build the private async engine using the refactored policies, tokens, body collector and formatting helpers, with branch-owned frames and explicit recursive awaits; verify normal, inverted and iterable sections, token sequences, delimiters and padding against synchronous public-API cases on both backends.
- [x] 2.2 Extract diagnostic production from direct writes while retaining immediate delivery through the shared synchronous Python logger under both APIs; verify default stderr and application-logger text, order and failure-path delivery, and briefly document that an async-render logger should remain minimal because it blocks that render.

## 3. Add awaitable lambda protocols

- [x] 3.1 Invoke selected callbacks once and await awaitable results before protocol-specific processing; add parametrised tests for all decorators, both source policies, callable instances, ordinary results, None and propagated exceptions.
- [x] 3.2 Supply the async compatibility render callback with temporary scope support and compatibility-only cache replay; document and test awaited recursion, falsey temporary data, synchronous awaitable-forwarding callbacks and recovered nested errors.
- [x] 3.3 Add user-facing examples for async lambdas and explicit adaptation of blocking user callbacks; verify examples under both backends and preserve synchronous decorator metadata and binding tests.

## 4. Adapt template and partial I/O

- [x] 4.1 Prepare async and ordinary file-like template inputs through awaited reads or worker adapters before pure tokenisation; verify suspended reads allow sibling progress and caller-owned readers remain open after success, errors and cancellation.
- [x] 4.2 Add awaited filesystem partial loading with existing mapping precedence, suffix rules and containment; verify mapped and filesystem partial output, traversal/symlink rejection and progressing sibling tasks during blocked filesystem work.
- [x] 4.3 Document resource ownership and worker-backed cancellation latency; verify renderer-owned resources close and filesystem exceptions preserve existing missing-partial semantics without swallowing cancellation.

## 5. Implement async iteration and cooperative state cleanup

- [x] 5.1 Render async iterable sections sequentially with callable precedence and defined inverted-section truthiness; document the iterable contract and verify empty, nested, failing and cancelled iterators without closing caller-owned iterators implicitly.
- [x] 5.2 Add cooperative checkpoints and exception-safe branch cleanup; use deterministic event/task-group tests for cancellation, independent renders and concurrent nested callback rendering without scope or diagnostic leakage.

## 6. Establish parity and performance evidence

- [x] 6.1 Adapt shared behavioural and vendored specification cases to exercise sync and async engines without editing upstream expectations; verify all supported conformance cases pass on asyncio and Trio, including newer Mustache modules if already landed.
- [x] 6.2 Extend benchmark scenarios for in-memory async rendering, recursive callbacks and partials with output checks; compare checkpoint overhead and representative synchronous performance without introducing timing-based test gates.

## 7. Address accepted implementation review findings

- [x] 7.1 Replace mutable scope stacks in both engines with immutable parent-linked `_RenderFrame` ownership; share protocol-neutral lookup and collection helpers where simple, keep async `collect_section` as a static method, and cover nested lambda/concurrent rendering without caller-scope mutation.
- [x] 7.2 Add `_aget_filesystem_partial()` in the async module using AnyIO's async path/file API, retaining mapping precedence, containment and diagnostics while keeping direct worker mechanics out of renderer logic.
- [x] 7.3 Consolidate shared async fixture helpers and add focused behavioural regressions for protocol mismatch, logging validation/default stderr, falsey ordinary readers, cancellation, disabled filesystem lookup, and deterministic blocked-filesystem coordination.
- [x] 7.4 Replace detailed README how-to material with a concise package overview; add complete runnable sync/async API documentation in `API.md`; and add Unreleased changelog entries for this and other recent missing user-visible work.
- [x] 7.5 Add a focused Python 3.11 and 3.15 compatibility matrix that exercises the declared AnyIO 4.14 and Trio 0.32 floors on their respective backends.
- [x] 7.6 Correct the async benchmark harness to run repeated awaited renders in one event loop.

## 8. Address accepted post-review findings

- [x] 8.1 Shield renderer-owned asynchronous filesystem-partial cleanup from cancellation and prove real file closure on both supported backends.
- [x] 8.2 Preserve the ordinary-reader contract when `read()` returns an awaitable by boxing worker results before awaiting them on the render task.
- [x] 8.3 Recover the parent scope for escaped and unescaped current-scope interpolation within inverted sections in both engines.
- [x] 8.4 Define and enforce the supported `scopes` input contract, including empty collections, consistently for synchronous and asynchronous rendering.
- [x] 8.5 Exercise successful real filesystem-partial loading and deterministic sibling progress during blocked renderer-owned filesystem I/O.
- [x] 8.6 Select Trio test backends only when Trio is installed, while retaining explicit Trio compatibility coverage.
- [x] 8.7 Reject awaitable lambda results from synchronous rendering with an actionable error and document the sync/async lambda boundary.
- [x] 8.8 Declare Trio support through `anyio[trio]`, regenerate the lockfile, and retain floor compatibility verification.

## 9. Address final review decisions

- [x] 9.1 Use distinct internal markers for skipped and inverted sections, preserving genuine falsey iterable items and `True` current-scope interpolation; verify matching sync/async regressions.
- [x] 9.2 Normalise template-reader contracts across both APIs, dispose of unconsumed awaitables on cancellation, and reject async reader results in synchronous rendering; verify reader-result and cancellation regressions under asyncio and Trio.
- [x] 9.3 Extend Python 3.11 floor tests with readers, partial containment, compatibility callbacks, and cancellation; use real renderer-owned filesystem coordination where it provides deterministic public I/O coverage.
- [x] 9.4 Use a dedicated async test-support fixture/module boundary, restore README user guidance, expand runnable API examples, and verify examples through async behavioural tests.
- [x] 9.5 Share only render setup and pure partial-name validation between engines while keeping lazy loading and explicit execution loops; verify sync and async public API parity.
- [x] 9.6 Add explicit synchronous, asynchronous, and comparison benchmark modes with equivalent output-validated workloads; verify every mode runs successfully.

## 10. Address final triage decisions

- [x] 10.1 Preserve numeric-key fallback around marker and scalar frames, and reject binary template inputs consistently across both public APIs.
- [x] 10.2 Reject async iterable section values in synchronous rendering while preserving native async section iteration.
- [x] 10.3 Retain the requested rejected filesystem-partial reference and its lexical rejection reason in diagnostics without exposing configured or resolved paths.
- [x] 10.4 Raise the AnyIO dependency floor to 4.14.0, align focused Python 3.11 compatibility coverage, and document the AnyIO cancellation-scope boundary.
- [x] 10.5 Keep README async requirements concise and PyPI-safe while retaining the developer API reference.

## 11. Address post-review regression findings

- [x] 11.1 Make current-context lookup skip consecutive inverted-section markers in the shared resolver, remove duplicated local recovery, and add nested-inversion sync/async regressions for interpolation and current-context sections.

Routine checks, OpenSpec verification, review and delivery remain workflow hygiene outside the implementation checklist.
