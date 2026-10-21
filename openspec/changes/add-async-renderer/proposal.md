# Proposal

## Why

Async applications need to render templates whose lambdas, input readers and partial loading can suspend without blocking their runtime. After `refactor-simplify-renderer` establishes shared policies and render state, Chevron can add an async execution branch without mixing await decisions into its synchronous engine.

## What Changes

- Export `async def async_render(...) -> str` with the synchronous renderer's configuration parameters and precedence rules.
- Share pure tokenisation, name resolution, source policies, body collection and formatting with the refactored synchronous renderer, while giving recursive execution and I/O explicit async implementations.
- Support awaitable lambda results and an awaitable compatibility rendering callback using the existing decorators and explicit/permissive source policies.
- Read async template readers and filesystem partials without blocking the event loop; adapt ordinary file readers through worker execution. Preserve mapping-first partial lookup and containment rules.
- Support asynchronous section iterables in source order, cancellation cleanup and independent concurrent renders.
- Give both APIs immutable parent-linked render frames so caller-provided
  `scopes` collections are input only, and keep internal inverted-section
  state distinct from application values such as `True`, including through
  nested inverted sections.
- Reject awaitable reader and lambda results from synchronous rendering with
  actionable guidance to use `async_render()`.
- Use AnyIO for portable I/O and cooperative execution, with tests under asyncio and Trio. Chevron never starts or owns an event loop.
- Supply AnyIO through an optional `anyio` extra and Trio through a `trio` extra so synchronous installations retain their existing dependency footprint; document callback migration and the supported backend boundary.

## Capabilities

### New Capabilities

- `async-template-rendering`: Awaitable rendering, async callback and input contracts, portable I/O, cancellation and synchronous semantic parity.

### Modified Capabilities

None. Existing synchronous lambda and value-resolution contracts remain
compatible; this change records the scope-ownership and awaitable-boundary
guarantees needed to keep both APIs aligned.

## Impact

Requires `refactor-simplify-renderer` first. A private `async_renderer` module and I/O adapters extend the planned shared core; package exports, optional dependencies, documentation, and behavioural tests change. AnyIO is an optional runtime dependency and Trio is available through a separate optional extra and the development environment. `update-to-latest-mustache` remains separate: whichever renderer features exist when this change lands must work in both engines, including inheritance and dynamic names if already implemented. No async CLI, streaming-output API, network partial loader or event-loop bridge is introduced.
