# Design

## Context

See [proposal.md](proposal.md) for the motivation. `ChevronRender` and
`AsyncChevronRender` currently recurse through `render()`, `render_tokens()`,
section bodies, partials, and lambda-produced text. `_RenderFrame` already
provides an immutable parent-linked scope and rendering-context chain, but the
engine's outstanding render work still lives on Python's call stack.

## Goals / Non-Goals

**Goals:**

- Make engine-owned nested rendering iterative in both renderers.
- Preserve all existing public APIs and rendering semantics, including legacy
  compatibility callbacks.
- Keep `_RenderFrame` immutable and use it for scope, delimiters, and padding
  ownership.
- Keep the synchronous and asynchronous drivers explicit while sharing only
  small, await-free semantic helpers that have immediate use in both.

**Non-Goals:**

- Changing Mustache syntax, lambda protocols, partial-loading policy, or
  logger behaviour.
- Adding a general-purpose shared renderer abstraction or a new async runtime
  configuration layer.
- Guaranteeing termination for self-recursive templates or changing the
  behaviour of caller-defined recursive lambdas.
- Enforcing performance thresholds in the test suite.

## Decisions

### Use an explicit active-work stack

Each driver will own a stack of small active-work records. A record contains a
token iterator, its immutable `_RenderFrame`, the current delimiters, output
chunks, and the continuation that receives its completed text. When a partial,
iterable section item, or supported lambda result needs rendering, the driver
pushes child work and later resumes the parent rather than calling `render()`
recursively.

This makes nested engine work visible and bounded by heap state instead of the
Python call stack. A direct recursive rewrite would retain the failure mode;
an AST rewrite would add unnecessary parser and compatibility risk.

### Separate immutable context from mutable execution state

`_RenderFrame` remains the immutable parent-linked context chain. Active-work
records hold only temporary execution state and never mutate a frame or a
caller-provided scope collection. Parent output receives a child's final text
through an explicit continuation, so resuming work cannot leak delimiter,
padding, or scope changes across frame boundaries.

This retains the accepted render-scoped ownership model. Copying scopes or
building a second mutable scope stack would obscure that ownership without
solving the execution problem.

### Keep two small drivers, with only narrow shared helpers

The synchronous driver processes work directly. The AnyIO driver uses the same
state-machine shape but awaits lambda results, async iterables, and
renderer-owned filesystem operations. Pure helpers for token interpretation,
partial-path validation, and frame construction may be shared when they reduce
duplicated logic immediately; the drivers will not be forced through a
protocol-neutral scheduling framework.

This avoids sync/async drift without concealing asynchronous control flow or
requiring an optional dependency for synchronous rendering.

### Preserve callback contracts at the renderer boundary

Interpolation and standard-section lambdas produce child work after their
callable returns. A legacy compatibility callback still receives a synchronous
renderer callback (or an async callback from `async_render`) and receives the
same completed text as today. Its re-entrant invocation uses the same
iterative engine boundary and render-scoped state, rather than restoring the
old recursive token-dispatch path.

The callback's synchronous control flow cannot be suspended or rewritten by
Chevron; this design removes engine-owned recursion while retaining that public
contract.

### Retain established asynchronous cancellation points

The asynchronous driver keeps checkpoints while scanning tokens and collecting
sections, and awaits actual asynchronous operations normally. Frame transitions
do not introduce a separate fairness or performance-accounting mechanism.

### Verify output parity and measure equivalent workloads

Regression tests will cover deep finite partial and lambda-result expansion,
then exercise resumed parent context. Benchmark tooling will offer explicit
synchronous, asynchronous, and comparison workloads with output validation;
benchmark results inform review but are not pass/fail timing gates.

## Risks / Trade-offs

- [Continuation handling changes parent/child output ordering] → Cover partial,
  iterable-section, lambda, delimiter, indentation, and compatibility-callback
  parity before replacing either driver.
- [Active-work cleanup leaks token streams on errors or cancellation] → Give
  each owned token stream a deterministic close path and test error and
  cancellation cleanup.
- [Async and sync drivers drift] → Share only validated pure helpers and run
  the same behavioural cases through both public entry points.
- [A caller recursively invokes its own compatibility callback] → Preserve its
  existing contract while documenting that the stack-safety guarantee covers
  engine-owned finite expansion, not recursion created by caller code.

## Migration Plan

The change is internal and requires no caller migration. Implement and verify
the synchronous driver first, then the AnyIO driver against the same behaviour
matrix. If a regression is found before release, revert the renderer internals
as one change; the public APIs and stored templates remain compatible.
