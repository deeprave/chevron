# Tasks

## 1. Synchronous iterative rendering

- [x] 1.1 Define the private active-work and completion-continuation state that pairs immutable `_RenderFrame` context with token iteration, output chunks, delimiter state, and deterministic token-stream cleanup.
- [x] 1.2 Replace recursive synchronous rendering of partials, iterable sections, interpolation-lambda results, and standard-section-lambda results with the active-work driver.
- [x] 1.3 Preserve legacy compatibility callback re-entry through the iterative renderer boundary.

## 2. Asynchronous iterative rendering

- [x] 2.1 Convert `AsyncChevronRender` to the corresponding explicit active-work driver while retaining awaited lambdas, async iterables, AnyIO filesystem partial reads, and established checkpoint locations.
- [x] 2.2 Preserve cancellation and owned-resource cleanup when asynchronous child work fails or is cancelled.

## 3. Benchmark support

- [x] 3.1 Extend the benchmark harness with explicit synchronous, asyncio, Trio, and comparison workloads that validate equivalent output; use descriptive workload identifiers and a concise legend; add configurable `--warm`, `--samples`, and millisecond `--sample` calibration per mode; provide `--sync`, `--async`, `--trio`, and `--compare` selectors; collect results before rendering them; report liveness to standard error; and provide `--json` output with whole-run timing metadata, raw samples, and median plus sample-standard-deviation per-iteration statistics without a timing pass/fail threshold.
