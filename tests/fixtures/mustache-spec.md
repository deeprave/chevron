# Mustache conformance checkpoint

This report records Chevron's current behaviour against the vendored Mustache
specification fixtures. It began as the refresh baseline and is updated as
conformance corrections land against the same upstream snapshot.

- Upstream snapshot: [`e8ec001db7f594521e773c34866aca2b5d6b0037`](https://github.com/mustache/spec/tree/e8ec001db7f594521e773c34866aca2b5d6b0037)
- Upstream `HEAD` when this baseline was captured:
  `e8ec001db7f594521e773c34866aca2b5d6b0037`
- Command: `uv run pytest -m conformance -q --tb=no`
- Fixture examples: 194 across nine modules

All vendored modules currently pass. Future conformance work should compare
against this snapshot rather than a moving upstream `HEAD`.

## Synchronous renderer

| Fixture module | Cases | Passed | Failed |
| --- | ---: | ---: | ---: |
| comments | 12 | 12 | 0 |
| delimiters | 14 | 14 | 0 |
| interpolation | 42 | 42 | 0 |
| inverted | 22 | 22 | 0 |
| partials | 12 | 12 | 0 |
| sections | 34 | 34 | 0 |
| lambdas | 10 | 10 | 0 |
| dynamic names | 21 | 21 | 0 |
| inheritance | 27 | 27 | 0 |
| **Total** | **194** | **194** | **0** |

The synchronous renderer passes every fixture in the pinned suite.

## Asynchronous renderer

The asynchronous suite runs each fixture example on both installed AnyIO
backends. Each backend has the same result profile as the synchronous renderer.

| Fixture module | Cases per backend | asyncio passed | asyncio failed | Trio passed | Trio failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| comments | 12 | 12 | 0 | 12 | 0 |
| delimiters | 14 | 14 | 0 | 14 | 0 |
| interpolation | 42 | 42 | 0 | 42 | 0 |
| inverted | 22 | 22 | 0 | 22 | 0 |
| partials | 12 | 12 | 0 | 12 | 0 |
| sections | 34 | 34 | 0 | 34 | 0 |
| lambdas | 10 | 10 | 0 | 10 | 0 |
| dynamic names | 21 | 21 | 0 | 21 | 0 |
| inheritance | 27 | 27 | 0 | 27 | 0 |
| **Total per backend** | **194** | **194** | **0** | **194** | **0** |

Across the synchronous, asyncio, and Trio executions, the suite comprises 582
test executions, all passing.
