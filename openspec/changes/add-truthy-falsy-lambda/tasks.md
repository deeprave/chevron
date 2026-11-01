# Tasks

## 1. Recognise invoked conditional syntax

- [ ] 1.1 Extend conditional-section tokenisation to recognise `{{?*name}}…{{/name}}` only when `Extension.CONDITIONAL_SECTIONS` is enabled, and verify enabled matching, disabled literal-name handling, and structural diagnostics with tokenizer or rendering tests.
- [ ] 1.2 Add behaviour fixtures for ordinary and invoked conditional syntax so that an ordinary callable remains uninvoked while the explicit `?*` form selects the body only from its callback result.

## 2. Render synchronous function conditions

- [ ] 2.1 Implement synchronous invoked-condition dispatch using the existing `@chevron.func` protocol, preserving context and ensuring truthy, falsey, text, unsupported-protocol, and explicit-lambda-mapping cases match the conditional contract.
- [ ] 2.2 Reject an awaitable result from a synchronous invoked condition through the existing `async_render()` guidance path, and verify it is closed when supported.

## 3. Render asynchronous function conditions

- [ ] 3.1 Implement asynchronous invoked-condition dispatch by awaiting `@chevron.func` results before testing truthiness, without rendering the returned value or changing context.
- [ ] 3.2 Add asyncio and Trio coverage for synchronous and asynchronous function results, falsey values, callback exceptions, and repeated encountered conditions.

## 4. Document the conditional function form

- [ ] 4.1 Document `{{?*name}}…{{/name}}` in the extensions, sections, lambda, async-rendering, and compatibility references, including the `@chevron.func` requirement, one-shot invocation per occurrence, result semantics, and lack of context injection; verify the strict MkDocs build passes.
