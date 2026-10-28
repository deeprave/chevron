# Lambdas

Most templates need only data, sections, and partials. Lambdas are an explicit bridge to application code for cases such as localized fragments or a controlled transformation. They are not a general sandbox.

For new applications, pass a `lambdas` mapping. That enables only declared callable names and gives that mapping precedence over template data. `lambdas={}` disables callable tags altogether. Callable values found in ordinary template data are rejected in explicit mode.

## Interpolation and section lambdas

`@chevron.func` declares a zero-argument interpolation lambda. Its returned template source is rendered using the configured default delimiters:

```python
@chevron.func
def banner() -> str:
    return "{{environment}} deployment"
```

`@chevron.section` declares a standard one-argument section lambda. It receives the literal section body and returns template source:

```python
@chevron.section
def twice(body: str) -> str:
    return body + body
```

These definitions make the callable's intent visible. Both protocols may return awaitables under [`async_render()`](../api/async-render.md), but not under synchronous `render()`.

## Compatibility callbacks

`@chevron.compat` marks Chevron's historical two-argument section callback. It receives the literal body and a `render` helper. In synchronous rendering the helper is a normal callable. In async rendering it always returns an awaitable, even for a synchronous callback; read the [async compatibility contract](../api/async-render.md#compatibility-callbacks) before using it.
