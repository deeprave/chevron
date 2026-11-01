# Spec Delta

## MODIFIED Requirements

### Requirement: Async lambda execution preserves source and protocol rules

Async rendering SHALL apply existing explicit-mapping precedence, validation, callable-data rejection and permissive lookup. It SHALL invoke a selected callable once through its declared protocol and await its result when awaitable. It SHALL preserve escaping, delimiter, padding, None-result and compatibility-cache rules. For an enabled invoked conditional section, it SHALL await a `@chevron.func` result when awaitable and use the resulting value only for truthiness.

#### Scenario: Explicit callable data is rejected before execution

- **WHEN** an async render supplies `lambdas={}` and template data contains an async callable
- **THEN** the callable is not invoked and existing rejection output and configured diagnostics apply

#### Scenario: Async interpolation and standard sections

- **WHEN** a permitted decorated interpolation or standard-section lambda returns an awaitable
- **THEN** the renderer awaits it and recursively renders its result using that protocol's existing semantics

#### Scenario: Ordinary synchronous callback result

- **WHEN** a permitted callback returns an ordinary value
- **THEN** the async renderer processes it through the same declared protocol without requiring a coroutine declaration

#### Scenario: Async invoked conditional function

- **WHEN** an enabled invoked conditional section resolves to a `@chevron.func` callback that returns an awaitable truthy or falsey value
- **THEN** `async_render()` awaits it once and selects or skips the body according to the resolved value

#### Scenario: Synchronous invoked conditional function rejects an awaitable

- **WHEN** `render()` invokes a conditional function callback that returns an awaitable
- **THEN** it closes the awaitable when possible and raises `TypeError` directing the caller to `async_render()`
