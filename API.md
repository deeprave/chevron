# Chevron API

Chevron renders [Mustache](https://mustache.github.io/) templates to a complete string. It supports synchronous rendering by default and optional AnyIO-based asynchronous rendering for applications already running on asyncio or Trio.

For Mustache language syntax and general examples, see the [upstream Mustache
manual](https://github.com/mustache/mustache.github.com/blob/115baf277db1adc09354871271a7ec8dd7b73a5a/mustache.5.html).
This reference is pinned to its upstream revision; this document describes
Chevron's API and supported behaviour.

`async_render()` requires a caller-owned running runtime. Chevron never creates or selects an event loop.

## Render a template

```python
import chevron

chevron.render("Hello, {{name}}!", {"name": "Ada"})
```

Templates may be strings, token sequences, or ordinary file-like objects. `render()` owns only files it opens for configured filesystem partials; caller-owned readers stay open.

### Partials

Supply in-memory partials with `partials_dict`:

```python
chevron.render(
    "{{> greeting}}",
    {"name": "Ada"},
    partials_dict={
        "greeting": "Hello, {{name}}!",
    },
)
```

Filesystem partial loading is disabled unless `partials_path` is supplied:

```python
chevron.render("{{> greeting}}", {"name": "Ada"}, partials_path="partials")
```

Chevron rejects absolute names, parent traversal, and resolved paths outside that directory. Use `partials_path='.'` only when intentionally restoring the historical current-directory lookup.

### Dynamic partial names

Prefix a partial name with `*` to choose the partial from the active template
context. The remainder is a normal dotted name; its resolved text is used once
as the partial name. Resolving a dynamic name does not add a scope, so the
selected partial retains the surrounding context.

Because `*` introduces this syntax, a literal partial name cannot begin with
`*`. This is a small compatibility difference from Chevron 0.14.0, which
treated such names literally.

```python
chevron.render(
    "{{#items}}[{{>*presentation.partial}}]{{/items}}",
    {
        "presentation": {"partial": "card"},
        "items": ["first", "second"],
    },
    partials_dict={"card": "{{.}}"},
)
# "[first][second]"
```

Missing names, unavailable partials, and double dereferences such as
`{{>**partial}}` render nothing. Only non-empty strings can select a dynamic
partial; values such as `None`, `False`, and numbers render nothing.

Dynamic names use the same mapped-partial precedence and opt-in filesystem
containment rules as ordinary partials. With `partials_path`, selector data can
choose any contained partial file. Treat that data as trusted; to restrict
selection to an allow-list, omit `partials_path` and use `partials_dict` only.

## Lambdas

For new code, use `lambdas=` to explicitly authorize callable template names. In this mode, mapped names take precedence over template data and callable values in ordinary data are rejected. This limits callable execution but is not a general template sandbox: keep secrets and rich objects out of template data.

`@chevron.func` declares a zero-argument interpolation lambda. Chevron recursively renders its returned text using the configured default delimiters:

```python
@chevron.func
def greeting():
    return "{{name}}"


chevron.render("{{greeting}}", {"name": "Ada"}, lambdas={"greeting": greeting})
```

`@chevron.section` declares a one-argument Mustache section lambda. It receives the unprocessed body:

```python
@chevron.section
def repeat(body):
    return body + body


chevron.render(
    "{{#repeat}}{{name}}{{/repeat}}",
    {"name": "Ada"},
    lambdas={
        "repeat": repeat,
    },
)
```

`@chevron.compat` declares Chevron's historical two-argument callback. Its `render()` helper optionally accepts temporary data:

```python
@chevron.compat
def choose_first(body, render):
    return render(body, {"name": "Ada"})
```

Omit `lambdas` to retain the legacy compatibility behaviour for existing two-argument section callbacks. Pass `lambdas={}` to allow no callable template tags.

## Async rendering

Await `async_render()` inside your existing AnyIO-compatible runtime. It has the same configuration parameters and output semantics as `render()`:

```python
import chevron


async def page() -> str:
    return await chevron.async_render("Hello, {{name}}!", {"name": "Ada"})
```

All declared lambda protocols may return either a regular result or an awaitable result. Awaitable lambda results are supported only by `async_render()`; `render()` raises `TypeError` with guidance to use the async API instead. Async compatibility callbacks must await their recursive render callback:

```python
@chevron.func
async def greeting():
    return "{{name}}"


@chevron.compat
async def choose_message(body, render):
    return await render(body, {"name": "chosen"})


result = await chevron.async_render(
    "{{greeting}}",
    {"name": "Ada"},
    lambdas={
        "greeting": greeting,
    },
)
```

Async standard-section lambdas receive the literal section body and may return
renderable template source:

```python
@chevron.section
async def repeat(body: str) -> str:
    return body + body


assert (
    await chevron.async_render(
        "{{#repeat}}{{name}}{{/repeat}}",
        {"name": "Ada"},
        lambdas={"repeat": repeat},
    )
    == "AdaAda"
)
```

Async compatibility lambdas receive an awaitable callback that preserves the
active render configuration and can add truthy temporary data:

```python
@chevron.compat
async def choose_name(body: str, render) -> str:
    return await render(body, {"name": "Grace"})


assert (
    await chevron.async_render(
        "{{#choose_name}}{{name}}{{/choose_name}}",
        lambdas={"choose_name": choose_name},
    )
    == "Grace"
)
```

Async template readers and async section iterables are supported. Chevron uses AnyIO's asynchronous file API for its own filesystem partials. It adapts ordinary synchronous readers in a worker because regular Python file objects have no portable native asynchronous interface. Do not perform blocking I/O in application callbacks; use your runtime or AnyIO explicitly when needed.

Async readers must return text. Ordinary readers may also return an awaitable
text result; Chevron invokes their `read()` method in an AnyIO worker and
awaits that result on the render task. A synchronous `render()` call rejects an
awaitable reader result and directs the caller to `async_render()`.

```python
class Template:
    async def read(self) -> str:
        return "{{#people}}{{name}};{{/people}}"


async def people():
    yield {"name": "Ada"}
    yield {"name": "Grace"}


assert await chevron.async_render(Template(), {"people": people()}) == "Ada;Grace;"
```

Chevron never moves application callbacks into a worker because that would
change their thread affinity and context. Adapt a blocking callback explicitly:

```python
import anyio


def load_configuration_text() -> str:
    # Replace this with an application's blocking configuration operation.
    return "{{name}}"


@chevron.func
async def configuration() -> str:
    return await anyio.to_thread.run_sync(load_configuration_text)
```

Caller-owned readers and iterators remain open on success, errors, and cancellation. The non-abandoning ordinary-reader and renderer-owned-file cleanup guarantees apply when cancellation is delivered through an AnyIO cancellation scope, such as `anyio.fail_after()`, `anyio.move_on_after()`, or a task group's `cancel_scope`. Use those AnyIO APIs when that guarantee matters; raw `asyncio` timeout or task-cancellation APIs do not provide the same contract. A protected ordinary-reader operation may complete before AnyIO cancellation is observed.

## Diagnostics and logging

Rendering is quiet by default. Set `warn=True` to enable Chevron's default warning diagnostics. Applications can instead pass a standard-library `logging.Logger` or `logging.LoggerAdapter`; this replaces the default destination regardless of `warn`.

```python
import logging

logger = logging.getLogger(__name__)
chevron.render("{{missing}}", logger=logger, log_level=logging.WARNING)
```

`log_level=logging.INFO` includes render lifecycle messages, and `logging.DEBUG` adds bounded resolution and partial decisions. Logging is synchronous for both APIs, so supplied handlers should remain minimal; configure queue-backed logging through the standard logging package if required.

Missing or unreadable partials render empty as normal Mustache behaviour;
partial-resolution details are available only at `logging.DEBUG`.
