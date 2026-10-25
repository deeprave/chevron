# Tasks

## 1. Audit and test taxonomy

- [ ] 1.1 Measure collection and execution cost, catalogue repeated sync/async scenarios and private-implementation assertions, and verify every candidate has an identified observable behavior or public-contract reason to remain.
- [ ] 1.2 Document the durable test taxonomy and the boundary between vendored conformance, Chevron-owned behavioral cases, pytest resource fixtures, and focused public-contract tests; verify the guidance does not make transient test-status claims.

## 2. Shared behavioral case support

- [ ] 2.1 Add a typed, immutable Python case-record module for Chevron-owned source-template scenarios and verify named cases can express multiline templates, data, partials, and expected output without a new JSON loader.
- [ ] 2.2 Add explicit synchronous and asynchronous public-API runners for shared cases, retaining the existing asyncio and Trio backend coverage; verify failures identify the named case and renderer mode.

## 3. Behavioral consolidation

- [ ] 3.1 Consolidate partial, inheritance, whitespace, and standalone-line scenarios into topic-specific shared cases; verify sync, asyncio, and Trio results match their prior public behavior.
- [ ] 3.2 Consolidate other audited source-rendering scenarios only where their inputs and expected output are genuinely shared across renderers; verify parameterisation adds distinct behavioral coverage without unnecessary combinations.
- [ ] 3.3 Replace or remove implementation-coupled tests only after an equivalent public behavior assertion exists, while retaining focused token-sequence and other supported-public-contract tests; verify no private renderer API is used solely for implementation proof.
- [ ] 3.4 Keep resource-heavy filesystem, reader, concurrency, timing, and callback-protocol tests focused in their topical modules unless the audit identifies a clear shared behavioral case; verify retained tests remain behavior-oriented.

## 4. Comparative validation

- [ ] 4.1 Compare post-refactor collection, duration, and test counts against the audit baseline; verify the suite is no slower without an evidence-backed reason and failures remain locally diagnosable.
- [ ] 4.2 Verify vendored fixture contents, discovery, `conformance` marker behavior, and upstream module markers are unchanged; run the conformance group and full suite successfully.

## Workflow follow-up

- Review the completed test-suite refactor before applying release changes.
- Archive the change after the project's review requirements are satisfied.
