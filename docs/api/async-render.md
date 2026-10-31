# `async_render()`

```python
await chevron.async_render(template="", data={}, ..., logger=None, log_level=logging.WARNING)
```

`async_render()` has the same arguments and rendering semantics as [`render()`](render.md), but it may await template readers, iterable values, and declared lambdas. It is available only with the optional AnyIO support and must be called from an existing AnyIO-compatible runtime. Chevron never creates or chooses an event loop for you.

```python
import chevron


async def render_dashboard() -> str:
    return await chevron.async_render(
        "{{#jobs}}{{> job}}{{/jobs}}",
        {"jobs": await load_jobs()},
        partials_dict={"job": "<li>{{name}}: {{status}}</li>\n"},
    )
```

## Awaitable values and readers

Declared interpolation and section lambdas may return an ordinary result or an awaitable. Async template readers may implement an async `read()` method, and values may be asynchronous iterables. A synchronous reader is adapted only where necessary because regular Python file objects do not have portable native async reads.

Do not perform blocking application I/O directly in a callback. Use the application runtime or AnyIO explicitly, for example `await anyio.to_thread.run_sync(blocking_function)`. Chevron does not move application callbacks to workers because doing so would alter their thread affinity and context.

## Compatibility callbacks

An `@chevron.compat` callback receives `(body, render)`. Under `async_render()`, `render` is always an asynchronous callable: calling it returns an awaitable string. This is true even if the compatibility callback itself is a normal synchronous `def`.

A synchronous callback may forward that awaitable unchanged, allowing Chevron to await it:

```python
@chevron.compat
def forward(body: str, render):
    return render(body, {"name": "Ada"})


result = await chevron.async_render(
    "{{#forward}}Hello {{name}}{{/forward}}",
    lambdas={"forward": forward},
)
# "Hello Ada"
```

It cannot inspect or transform the nested string because it has no async context in which to await it. Use `async def` whenever the callback needs that result:

```python
@chevron.compat
async def emphasize(body: str, render) -> str:
    nested = await render(body, {"name": "Grace"})
    return f"<strong>{nested}</strong>"


result = await chevron.async_render(
    "{{#emphasize}}Hello {{name}}{{/emphasize}}",
    lambdas={"emphasize": emphasize},
)
# "<strong>Hello Grace</strong>"
```

The supplied helper retains the active rendering configuration and accepts optional temporary data. The recursion caused by application code calling this helper is application-owned; it uses the host Python call stack. Engine-owned expansion of partials and lambda results is iterative and has a finite safety bound.

## Cancellation and ownership

Chevron does not close caller-owned readers or iterators itself. Cancellation can be delivered to an async reader or iterator while Chevron awaits it, including an inverted-section probe; applications that cancel a render must treat that source as cancelled and must not assume it remains reusable. When [`Extension.ENHANCED_ITERATORS`](../reference/extensions.md#optional-rendering-extensions) is enabled during application startup, async iterables are streaming section sources: Chevron uses one cursor per name in its supplying context during a render, so an inverted section may advance one item while checking whether it is empty and retain it only for a later ordinary section in that render. An async iterable can then be traversed only once in a render: once its non-empty cursor is exhausted, later ordinary sections render no items rather than restarting, while inverted sections retain its non-empty result. Chevron closes filesystem partial resources that it opens, but leaves iterator lifecycle with the application. Filesystem-partial cleanup is guaranteed when cancellation is delivered by an AnyIO cancellation scope such as `anyio.fail_after()`, `anyio.move_on_after()`, or a task group's `cancel_scope`; raw `asyncio` cancellation APIs do not make the same guarantee.

With `ENHANCED_ITERATORS` enabled, supply independently constructed async iterator instances under separate names when a template needs more than one traversal. Chevron preserves a cursor only for repeated use of the same name in the same context.
