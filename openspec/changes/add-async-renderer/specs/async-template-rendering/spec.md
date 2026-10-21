# Spec Delta

## Purpose

Allow async applications to render Chevron templates within their existing runtime while preserving template semantics and keeping renderer-owned I/O off the event-loop thread.

## ADDED Requirements

### Requirement: Awaitable rendering uses the caller's runtime

Chevron SHALL export `async_render` as an async function returning rendered text. It SHALL run within the caller's active asyncio or Trio runtime without creating, nesting or owning an event loop. Equivalent supported synchronous inputs SHALL produce the same text as `render`.

#### Scenario: Backend-independent rendering

- **WHEN** an application awaits the same template render under asyncio or Trio
- **THEN** it receives equivalent output without Chevron starting a runtime

#### Scenario: Synchronous API remains available

- **WHEN** an application uses `render` without installing async support
- **THEN** existing synchronous imports, rendering and CLI behaviour remain available without importing the async renderer or AnyIO

#### Scenario: Optional runtime is absent

- **WHEN** an application awaits `async_render` without installing AnyIO
- **THEN** it receives an error that directs it to install `chevron-ng[anyio]` or `chevron-ng[trio]`

### Requirement: Async lambda execution preserves source and protocol rules

Async rendering SHALL apply existing explicit-mapping precedence, validation, callable-data rejection and permissive lookup. It SHALL invoke a selected callable once through its declared protocol and await its result when awaitable. It SHALL preserve escaping, delimiter, padding, None-result and compatibility-cache rules.

#### Scenario: Explicit callable data is rejected before execution

- **WHEN** an async render supplies `lambdas={}` and template data contains an async callable
- **THEN** the callable is not invoked and existing rejection output and configured diagnostics apply

#### Scenario: Async interpolation and standard sections

- **WHEN** a permitted decorated interpolation or standard-section lambda returns an awaitable
- **THEN** the renderer awaits it and recursively renders its result using that protocol's existing semantics

#### Scenario: Ordinary synchronous callback result

- **WHEN** a permitted callback returns an ordinary value
- **THEN** the async renderer processes it through the same declared protocol without requiring a coroutine declaration

### Requirement: Compatibility callbacks receive an awaitable render operation

The async compatibility protocol SHALL supply an awaitable recursive-render callback retaining the active configuration and lambda policy. Truthy temporary data SHALL prepend a scope, while falsey temporary data SHALL retain current scopes. Callback exceptions SHALL propagate without signature inference or reinvocation.

#### Scenario: Async compatibility callback renders temporary data

- **WHEN** a compatibility lambda awaits its supplied render callback with temporary data
- **THEN** the nested result uses the temporary scope and leaves the caller's scopes restored

#### Scenario: Callback fails

- **WHEN** an invoked callback raises `TypeError` or another application exception
- **THEN** that exception propagates without trying a different callback signature

#### Scenario: Caller-provided scopes remain structurally unchanged

- **WHEN** a render receives a `scopes` collection and recursively enters sections or lambda results
- **THEN** Chevron resolves names through private render frames without inserting into, deleting from, or otherwise structurally mutating the caller's collection

### Requirement: Renderer-owned I/O does not block the async runtime

Async rendering SHALL await template reading and filesystem partial operations, directly or through worker adapters. It SHALL preserve partial mapping precedence, opt-in filesystem loading, containment and missing-partial behaviour. Diagnostics SHALL use the existing synchronous standard-Python logging contract without an async wrapper or backend-specific logger requirement. Caller-owned readers SHALL remain open; renderer-owned files SHALL be closed on completion or failure.

#### Scenario: Suspended template read

- **WHEN** an async template reader waits for input
- **THEN** other runtime tasks can progress before the template read completes

#### Scenario: Synchronous reader is adapted

- **WHEN** the template is an ordinary file-like reader
- **THEN** Chevron performs its blocking read outside the event-loop thread and leaves that reader open

#### Scenario: Invalid reader result

- **WHEN** an ordinary or native asynchronous reader returns a truthy non-text value
- **THEN** async rendering raises `TypeError` stating that template readers must return text

#### Scenario: Async partial containment

- **WHEN** an enabled filesystem partial resolves outside the configured root
- **THEN** async rendering treats it as missing just as synchronous rendering does

### Requirement: Async section iteration preserves order

Async rendering SHALL support asynchronous iterables as section values, awaiting each item and rendering it in source order. It SHALL not implicitly parallelise lambdas, partials or section items. Plain awaitables in template data SHALL not be implicitly awaited as lambdas.

#### Scenario: Async iterable section

- **WHEN** a section value yields items asynchronously
- **THEN** its body renders once per item in yield order, including zero times for an empty iterable

#### Scenario: Async iterable in an inverted section

- **WHEN** an inverted section references an async iterable
- **THEN** it uses the object's ordinary truthiness without consuming it to discover whether it yields items

### Requirement: Cancellation and concurrent renders preserve state isolation

Cancellation SHALL propagate through async rendering and restore scopes and diagnostic state. Independent renders SHALL not share mutable invocation state. CPU-only rendering SHALL include cooperative checkpoints without promising pre-emption within arbitrary caller code or a single pure parsing operation.

#### Scenario: AnyIO cancellation-scope cleanup

- **WHEN** cancellation is delivered through an AnyIO cancellation scope
- **THEN** renderer-owned resource cleanup and non-abandoning ordinary-reader operations complete before cancellation is observed
- **AND** raw asyncio timeout and task-cancellation APIs do not carry that guarantee

#### Scenario: Cancel a suspended lambda

- **WHEN** a render is cancelled while awaiting a lambda
- **THEN** cancellation propagates and its temporary render state is unwound

#### Scenario: Independent concurrent renders

- **WHEN** two async renders suspend and resume with different scopes, partials and lambda mappings
- **THEN** neither render observes the other's invocation state

### Requirement: Shared render context preserves synchronous boundaries

Chevron SHALL use private render context for supplied scope sequences in both
APIs, without structurally mutating the caller's sequence. Internal
inverted-section bookkeeping SHALL remain distinct from application values.
Synchronous rendering SHALL reject awaitable reader and lambda results, and
async iterable section values, including inverted sections, with guidance to
use `async_render()`.

#### Scenario: True current scope within an inverted section

- **WHEN** an inverted section renders escaped or unescaped current-scope interpolation with `True` as the active application scope
- **THEN** it renders `True` rather than substituting a parent scope

#### Scenario: Nested inverted sections preserve current scope

- **WHEN** nested inverted sections render current-scope interpolation or a
  current-scope section
- **THEN** Chevron resolves the nearest application scope rather than exposing
  internal inverted-section bookkeeping

#### Scenario: Synchronous awaitable reader

- **WHEN** a synchronous template reader returns an awaitable
- **THEN** Chevron closes it when possible and raises `TypeError` directing the caller to `async_render()`

#### Scenario: Synchronous async iterable section

- **WHEN** a synchronous section resolves to an async iterable
- **THEN** Chevron raises `TypeError` directing the caller to `async_render()`

#### Scenario: Synchronous inverted async iterable section

- **WHEN** a synchronous inverted section resolves to an async iterable
- **THEN** Chevron raises `TypeError` directing the caller to `async_render()`
