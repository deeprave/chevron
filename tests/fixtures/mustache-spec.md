# Mustache conformance baseline

This report records Chevron's behaviour against the vendored Mustache
specification fixtures when the fixture snapshot was refreshed.

- Upstream snapshot: [`e8ec001db7f594521e773c34866aca2b5d6b0037`](https://github.com/mustache/spec/tree/e8ec001db7f594521e773c34866aca2b5d6b0037)
- Upstream `HEAD` when this baseline was captured:
  `e8ec001db7f594521e773c34866aca2b5d6b0037`
- Command: `uv run pytest -m conformance -q --tb=no`
- Fixture examples: 194 across nine modules

The updated dynamic-name and inheritance modules are intentionally included in
this baseline even though their unsupported cases currently fail. Future
conformance work should compare against this snapshot rather than a moving
upstream `HEAD`.

## Synchronous renderer

| Fixture module | Cases | Passed | Failed |
| --- | ---: | ---: | ---: |
| comments | 12 | 12 | 0 |
| delimiters | 14 | 14 | 0 |
| interpolation | 42 | 41 | 1 |
| inverted | 22 | 22 | 0 |
| partials | 12 | 12 | 0 |
| sections | 34 | 34 | 0 |
| lambdas | 10 | 10 | 0 |
| dynamic names | 21 | 5 | 16 |
| inheritance | 27 | 0 | 27 |
| **Total** | **194** | **150** | **44** |

The interpolation failure is `Dotted Names - Context Precedence`. The remaining
failures are the dynamic-name and inheritance extension cases shown above.

## Asynchronous renderer

The asynchronous suite runs each fixture example on both installed AnyIO
backends. Each backend has the same result profile as the synchronous renderer.

| Fixture module | Cases per backend | asyncio passed | asyncio failed | Trio passed | Trio failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| comments | 12 | 12 | 0 | 12 | 0 |
| delimiters | 14 | 14 | 0 | 14 | 0 |
| interpolation | 42 | 41 | 1 | 41 | 1 |
| inverted | 22 | 22 | 0 | 22 | 0 |
| partials | 12 | 12 | 0 | 12 | 0 |
| sections | 34 | 34 | 0 | 34 | 0 |
| lambdas | 10 | 10 | 0 | 10 | 0 |
| dynamic names | 21 | 5 | 16 | 5 | 16 |
| inheritance | 27 | 0 | 27 | 0 | 27 |
| **Total per backend** | **194** | **150** | **44** | **150** | **44** |

Across the synchronous, asyncio, and Trio executions, the baseline comprises
582 test executions: 450 pass and 132 fail.
