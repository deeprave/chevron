# Design

## Context

See [proposal.md](proposal.md) for the motivation. Both renderers recognise `collections.abc.Iterator` in ordinary sections and consume it item by item. Their inverted-section paths instead use Python truthiness, which cannot distinguish an empty iterator from one with remaining items. The async renderer also recognises `AsyncIterable`, whose inverted sections need an asynchronous emptiness check.

## Goals / Non-Goals

**Goals:**

- Give recognised synchronous and asynchronous iterators the same empty-section semantics as lists and tuples.
- Preserve every yielded item after an emptiness check.
- Keep synchronous iterator semantics identical between `render()` and `async_render()`, and preserve source order for asynchronous iterators.
- Cover the behaviour through shared public rendering cases.
- Make non-standard iterator inversion explicitly opt-in without adding per-render configuration.

**Non-Goals:**

- Materialise an iterator into a list or otherwise consume an unbounded source eagerly.
- Change lookup, interpolation, lambda, or arbitrary-iterable behaviour.
- Create a broad compatibility mode or expose an extension switch through individual template data or render calls.

## Decisions

### Configure extensions globally with a bitmask

`chevron.Extension` is a public `IntFlag` and the sole configuration surface for Chevron extensions. It provides `NONE`, `INVERTED_ITERATORS`, and `ALL`, along with class-level `enable()` and `is_enabled()` methods. The first `enable()` call selects the process-wide bitmask and freezes it:

```python
from chevron import Extension

Extension.enable(Extension.INVERTED_ITERATORS)
```

The default is `Extension.NONE`, preserving historic iterator behaviour unless the application opts in. `ALL` contains every extension currently implemented; it is not a promise that future, unimplemented flags already exist. Renderer code queries `Extension.is_enabled()` directly when it needs to apply an extension. A later `enable()` call raises `RuntimeError`.

This configuration is intentionally not synchronised. It is application-startup configuration and applications establish it before rendering begins. There is no public reset or disable operation.

### Keep one canonical cursor and tri-state emptiness per context value when enabled

When `Extension.INVERTED_ITERATORS` is enabled, Chevron creates one canonical cursor for each recognised synchronous `Iterator` or asynchronous `AsyncIterable` name in its supplying context during a render. Its private state exposes an `is_empty` result: `None` before Chevron examines the cursor, `False` once it has established that at least one item exists, and `True` only when the cursor yields no items. That verdict does not change when a non-empty cursor is later exhausted. A non-empty probe buffers only its first item, which the canonical cursor yields before continuing.

All later sections that use the same name in that context use that canonical state. Thus a partial can consume a buffered first item from an earlier inverted check, while an inner scope with a shadowing value remains independent. Chevron does not coordinate separate names merely because they happen to refer to the same iterator object. Once the cursor is exhausted, later ordinary sections render no items and Chevron does not restart a repeatable iterator or async iterable. Inverted sections retain the initial empty or non-empty verdict, so a non-empty source does not become a fallback merely because an earlier ordinary section consumed it.

This intentionally treats recognised iterator values as streaming sources. Lists, tuples, and other sequence handling remain unchanged. The alternative of materialising an iterator would use unbounded memory; reopening its cursor would make a render's output depend on whether the iterator happened to be repeatable.

When the extension is disabled, Chevron retains its existing section dispatch: it does not probe an iterator for inversion, buffer values, or retain a canonical cursor for the value.

### Test as public behaviour in the shared case set

Add a `RenderCase` with a fresh empty synchronous iterator and adjacent ordinary/inverted sections. Because the shared case set is exercised by `render()` and `async_render()` under asyncio and Trio, one fixture-based case verifies synchronous parity without testing private helpers. Add async-only cases for empty and non-empty asynchronous iterators under both supported AnyIO backends.

## Risks / Trade-offs

- [A context value is referenced in multiple sections during one render with the extension enabled] → Reuse its canonical cursor and known empty/non-empty state instead of reopening it.
- [Peeked value could be lost] → Yield the buffered item before continuing through the canonical cursor.
- [Repeatable iterator previously restarted] → Treat recognised iterator values as streaming sources for a render and document this compatibility change.
- [Existing caller code observes undocumented empty-iterator output] → The new result aligns with Chevron's established empty-list semantics and is documented as intentional behaviour.
- [An asynchronous peek adds an await point] → Perform only the required single `anext()` call and preserve the buffered item for normal rendering.

## Migration Plan

Applications that require empty iterators to select inverted sections enable `Extension.INVERTED_ITERATORS` during startup. Leaving extensions disabled retains historic behaviour. Rolling back consists of removing the startup configuration before the application begins rendering.
