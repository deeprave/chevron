# Tasks

## 1. Audit and test taxonomy

- [x] 1.1 Measure collection and execution cost, catalogue repeated sync/async scenarios and private-implementation assertions, and verify every candidate has an identified observable behavior or public-contract reason to remain.
- [x] 1.2 Document the durable test taxonomy and the boundary between vendored conformance, Chevron-owned behavioral cases, pytest resource fixtures, and focused public-contract tests; verify the guidance does not make transient test-status claims.

## 2. Shared behavioral case support

- [x] 2.1 Add a typed, immutable Python case-record module for Chevron-owned source-template scenarios and verify named cases can express multiline templates, data, partials, and expected output without a new JSON loader.
- [x] 2.2 Add explicit synchronous and asynchronous public-API runners for shared cases, retaining the existing asyncio and Trio backend coverage; verify failures identify the named case and renderer mode.

## 3. Behavioral consolidation

- [x] 3.1 Consolidate partial, inheritance, whitespace, and standalone-line scenarios into topic-specific shared cases; verify sync, asyncio, and Trio results match their prior public behavior.
- [x] 3.2 Consolidate other audited source-rendering scenarios only where their inputs and expected output are genuinely shared across renderers; verify parameterisation adds distinct behavioral coverage without unnecessary combinations.
- [x] 3.3 Replace or remove implementation-coupled tests only after an equivalent public behavior assertion exists, while retaining focused token-sequence and other supported-public-contract tests; verify no private renderer API is used solely for implementation proof.
- [x] 3.4 Keep resource-heavy filesystem, reader, concurrency, timing, and callback-protocol tests focused in their topical modules unless the audit identifies a clear shared behavioral case; verify retained tests remain behavior-oriented.

## 4. Comparative validation

- [x] 4.1 Compare post-refactor collection, duration, and test counts against the audit baseline as context for the refactor; retain distinct behavioral coverage and locally diagnosable failures regardless of any timing change.

## 5. Second behavioral consolidation

- [x] 5.1 Consolidate the audited value and scope-resolution scenarios into named shared source-template cases; retain focused tests for invalid scopes, exception propagation, and caller-owned scope lifecycle.
- [x] 5.2 Consolidate the audited ordinary and inverted-section scenarios into named shared source-template cases; retain focused tests for iterators, async iterables, deep-expansion bounds, and error semantics.
- [x] 5.3 Consolidate the audited whitespace, standalone-line, line-ending, and delimiter scenarios into named shared source-template cases without duplicating the immutable vendored conformance corpus.
- [x] 5.4 Move only the matching async source-output examples to the shared runners, retaining focused async tests for awaiting, I/O, cancellation, scheduling, concurrency, and logging.

## 6. Lambda behavioral consolidation

- [x] 6.1 Add a narrow lambda-case variant that supplies a fresh declared-lambda mapping per render without introducing general setup or arbitrary render options.
- [x] 6.2 Consolidate the audited synchronous declared-lambda output scenarios into shared cases, retaining focused callable invocation, callback-argument, warning, error, metadata, and protocol-policy tests.
- [x] 6.3 Consolidate the audited async-only lambda output scenarios into the async collection so they run under asyncio and Trio without being sent through synchronous rendering.

## 7. Initial-delimiter behavioral coverage

- [x] 7.1 Add explicit initial-delimiter support to shared rendering cases without introducing a generic render-options mapping.
- [x] 7.2 Cover initial custom delimiters for direct interpolation, partial expansion, and declared-lambda expansion through the sync, asyncio, and Trio runners.

## 8. Explicit lambda-mapping behavioral coverage

- [x] 8.1 Consolidate the audited output-only explicit lambda-mapping scenarios into `LambdaRenderCase` entries, retaining focused invocation, rejection, warning, snapshot, and error tests.
- [x] 8.2 Run the converted explicit-mapping scenarios through the sync, asyncio, and Trio runners without extending the case variant to legacy implicit callbacks.

## 9. Filesystem partial behavioral coverage

- [x] 9.1 Add a narrow filesystem-partial case variant and dedicated temporary-directory runners for ordinary file-tree-to-output scenarios.
- [x] 9.2 Cover default and custom extensions, nested names, configured-mapping precedence, and missing filesystem partials through sync, asyncio, and Trio while retaining focused security and lifecycle tests.

## 10. Async-iterable behavioral coverage

- [x] 10.1 Consolidate ordinary async-iterable section output into async-only shared cases without adding a new case variant.
- [x] 10.2 Retain focused iterator consumption, errors, cancellation, and ownership tests while running ordinary async-iterable output cases under asyncio and Trio.
