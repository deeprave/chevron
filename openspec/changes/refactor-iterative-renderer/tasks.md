# Tasks

## 0. Current-Mustache compatibility constraints

- [ ] 0.1 Review the recorded `update-to-latest-mustache` compatibility map before finalising active-work records; verify the state design preserves first-resolved dotted scope, existing partial lookup for dynamic names, and renderer-local inheritance override context without adding extension syntax or public API.

## 1. Synchronous iterative rendering

- [ ] 1.1 Define the private active-work and completion-continuation state that pairs immutable `_RenderFrame` context with token iteration, output chunks, delimiter state, and deterministic token-stream cleanup; verify focused unit tests cover frame ownership and child completion.
- [ ] 1.2 Replace recursive synchronous rendering of partials, iterable sections, interpolation-lambda results, and standard-section-lambda results with the active-work driver; verify existing synchronous renderer and lambda test modules pass.
- [ ] 1.3 Preserve legacy compatibility callback re-entry through the iterative renderer boundary; verify callback token reuse, temporary data, delimiter, padding, and parent-resumption regression tests pass.
- [ ] 1.4 Add finite deep synchronous expansion tests for partial and lambda-result chains, including parent-context resumption; verify they complete beyond the interpreter recursion limit with expected output.

## 2. Asynchronous iterative rendering

- [ ] 2.1 Convert `AsyncChevronRender` to the corresponding explicit active-work driver while retaining awaited lambdas, async iterables, AnyIO filesystem partial reads, and established checkpoint locations; verify the async renderer tests pass under asyncio.
- [ ] 2.2 Preserve cancellation and owned-resource cleanup when asynchronous child work fails or is cancelled; verify targeted cancellation and file-handle cleanup tests pass.
- [ ] 2.3 Add deep finite asynchronous expansion and parent-context parity tests, including async lambda results; verify they pass under asyncio and Trio when Trio is installed.

## 3. Documentation and performance evidence

- [ ] 3.1 Document the stack-safe finite-expansion guarantee and its caller-defined-recursion boundary in API.md; verify the examples and terminology match the public sync and async entry points.
- [ ] 3.2 Extend the benchmark harness with explicit synchronous, asynchronous, and comparison workloads that validate equivalent output; verify each selected workload runs and reports its measured result without a timing pass/fail threshold.

## 4. Integration verification

- [ ] 4.1 Run the full test suite, lint, type checks, and OpenSpec validation after both drivers use active work; verify all commands succeed on every supported optional-dependency configuration.
