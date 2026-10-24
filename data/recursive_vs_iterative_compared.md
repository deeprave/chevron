# Recursive versus iterative renderer benchmark comparison

## Scope

This compares the committed recursive snapshot, `942281d`, with the iterative
renderer snapshot, `b1b7b1d`. Both used CPython 3.11.16 on macOS arm64 with
three warm-up runs, ten samples, and a 100 ms target per sample.

Only the eleven workloads present in both reports are compared below. The
iterative report adds four workloads for deep or scale-oriented cases; without
a recursive measurement they are reported separately, not treated as a
before/after result.

Positive percentages mean the iterative renderer took more milliseconds per
render and was therefore slower. These are single benchmark snapshots, not a
repeated-run statistical study. Changes in the low single digits overlap the
per-sample variation seen in the reports and should be treated cautiously.

## Overall result

The recursive renderer is faster in all 33 matched median comparisons. The
iterative renderer has an unweighted mean slowdown of **6.8%** and a median
slowdown of **6.1%** across the three modes and eleven common workloads.

| Mode | Matched workloads | Iterative mean change | Iterative median change | Faster / slower medians |
| --- | ---: | ---: | ---: | ---: |
| sync | 11 | +10.2% | +7.6% | 0 / 11 |
| asyncio | 11 | +4.7% | +2.2% | 0 / 11 |
| trio | 11 | +5.5% | +4.4% | 0 / 11 |

Sync is the fastest runtime in every workload in both reports. Across the
eleven common workloads, asyncio's median cost relative to sync is 3.74x for
the recursive renderer and 3.45x for the iterative renderer; Trio's is 3.74x
and 3.66x respectively. Asyncio is faster than Trio in every matched workload;
among all fifteen iterative workloads, Trio is faster only for `flat-partials`
(2.3%).

## Where the difference occurs

The slowdown is uneven. Section-heavy work accounts for the largest and most
consistent changes:

| Workload | sync | asyncio | trio |
| --- | ---: | ---: | ---: |
| list-section | +20.9% | +17.2% | +12.9% |
| explicit-empty-policy | +18.7% | +15.9% | +13.8% |
| mapped-partial | +12.5% | +1.8% | +4.4% |

Lambda-oriented workloads are closer, but still slower in the iterative
snapshot:

- Sync: +6.1% to +10.0% across the eight matched lambda workloads.
- Asyncio: +0.5% to +4.1%; several of these are within ordinary sample
  variation and need a repeated comparison before being treated as material.
- Trio: +0.2% to +7.4%; the +0.2% compatibility-section result is effectively
  indistinguishable at this resolution.

No matched category improves in the iterative snapshot. The largest observed
slowdown is synchronous `list-section` at +20.9%; the smallest is Trio
`compatibility-section-lambda-explicit` at +0.2%.

## Iterative-only workloads

These workloads exercise the newly relevant deep and scale paths. They are
measurements of the iterative implementation only, not comparison evidence:

| Workload | sync (ms) | asyncio (ms) | trio (ms) |
| --- | ---: | ---: | ---: |
| partial-chain | 0.2706 | 0.3887 | 0.3916 |
| function-lambda-chain | 0.3278 | 0.4592 | 0.4636 |
| flat-partials | 0.6394 | 0.9911 | 0.9688 |
| large-list-section | 1.8148 | 2.9383 | 2.9765 |

## Highlights and next interpretation

- The refactor achieves its primary safety objective, but this first controlled
  comparison does **not** show a performance improvement for ordinary matched
  workloads.
- The cost is most visible in section processing, especially synchronous list
  rendering and explicit-empty handling.
- Asyncio has the smallest overall change; sync has the largest.
- The new deep-chain workloads establish a baseline for the stack-safe paths
  that the recursive snapshot could not safely measure at comparable depth.
- Before changing the renderer for speed, repeat the controlled comparison to
  confirm the larger section-related differences. Optimisation should then
  target measured hot paths rather than the small, likely-noisy lambda deltas.

## Diagnosis of the measured slowdown

This section explains the likely sources of the result from code inspection.
It is not a profiling result and does not imply an optimisation decision.

The iterative renderer replaces implicit recursive calls with explicit active
work records. That is necessary for stack-safe finite expansion, but the work
record must retain the token stream, frame, delimiters, output, continuation,
partial-padding state, and resource-cleanup state required to resume its
parent. The relevant cost is therefore not simply “heap allocations instead of
stack allocations”: recursive Python calls also have interpreter-frame costs.
The change is that state is now represented by richer, longer-lived Python
objects and maintained explicitly.

The most likely contributors are:

- Every token now passes through the active-work driver and its dispatch and
  control-token helpers. The former direct token loop avoided those extra
  method and helper calls.
- Every output chunk goes through line and whitespace tracking so partial
  indentation can be recovered without rebuilding all prior output. This is a
  deliberate trade-off: it avoids the former quadratic partial-padding scan,
  but adds work even to templates that never use indented partials.
- Every child of an iterable section has a `_RenderWork` instance, output and
  padding lists, a token-close check, and a continuation instead of relying on
  an ordinary recursive call and local variables. This matches the largest
  slowdowns occurring in list-section and explicit-empty-policy workloads.
- Output is accumulated as chunks and joined when work completes. CPython can
  optimise local `str +=` in the recursive implementation, so a list-and-join
  strategy is not inherently faster for these small ordinary renders.

The shape of the data supports this diagnosis: synchronous rendering exposes
the added Python bookkeeping most directly; asyncio and Trio dilute it with
their existing runtime overhead. Section-heavy workloads show the largest
change, while callback-heavy lambda workloads are comparatively close because
lookup, callback execution, and tokenisation already account for more of their
total time.

The safety and conformance work takes priority. A future profiling pass should
first confirm the result with repeated controlled runs, then measure
`list-section` and `explicit-empty-policy` before considering any narrowly
targeted optimisation.
