# Chevron extensions

Chevron extensions are opt-in behaviour beyond the Mustache specification. They leave ordinary Mustache templates unchanged and are disabled by default. This chapter is the reference for choosing and configuring them; the [template-language chapters](../language/index.md) explain how their syntax behaves in a template.

## Enable extensions once at startup

Configure extensions before the application performs its first render:

```python
from chevron import Extension

Extension.enable(Extension.ENHANCED_ITERATORS)
```

The first `Extension.enable()` call selects the complete, process-wide extension mask and freezes it. A later call raises `RuntimeError`. Chevron deliberately has no per-template or per-render switch, and changing the setting while rendering is not supported. Choose the mask once during application startup, alongside other application-wide configuration.

`Extension.NONE` is the default. Enable more than one extension with `|`:

```python
Extension.enable(
    Extension.ENHANCED_ITERATORS | Extension.CONDITIONAL_SECTIONS
)
```

`Extension.ALL` enables every extension implemented by the installed Chevron version:

```python
Extension.enable(Extension.ALL)
```

Use an explicit mask when an application needs a deliberately stable set of behaviours. Use `ALL` when adopting every extension supplied by the installed version is intended.

## Enhanced iterators

`Extension.ENHANCED_ITERATORS` adds two related behaviours for Python iterators and asynchronous iterables:

- An empty streaming value selects its inverted section, as an empty list does.
- A repeated section exposes positional metadata for its current item.

### Empty streaming values

Without the extension, an iterator object is truthy even after it has yielded its last value. With the extension, Chevron may observe one value to determine whether a stream is empty. That observed value remains available when the ordinary section renders later in the same supplying context.

```mustache
{{^events}}No events recorded.{{/events}}
{{#events}}- {{.}}
{{/events}}
```

With `events` set to `iter(())`, the output is:

```text
No events recorded.
```

With `events` set to `iter(["created", "published"])`, it is:

```text
- created
- published
```

Chevron does not materialise a stream or clone it. A streaming iterator or asynchronous iterable has one traversal for a given name in its supplying context during a render. Once it is exhausted, a later ordinary section using that name has no items. Lists and tuples remain normally reusable and can be repeated in separate sections.

### Positional metadata

Inside a repeated section, Chevron reserves leading-dot names other than `{{.}}` for metadata. The original item remains available as `{{.}}`.

```mustache
{{#steps}}
Step {{.ordinal}} of {{.length}}: {{.}}
{{/steps}}
```

For `steps=["draft", "review", "publish"]`, this renders:

```text
Step 1 of 3: draft
Step 2 of 3: review
Step 3 of 3: publish
```

| Name | Value |
| --- | --- |
| `.first` | True for the first item. |
| `.last` | True for the final item when Chevron can determine it. |
| `.index` | Zero-based position. |
| `.ordinal` | One-based position. |
| `.length` | Source length when `__len__` is available; otherwise `None`. |
| `.0`, `.1`, … | Values at non-negative indexes when the source supports both `__len__` and `__getitem__`; otherwise `None`. |

For example, `.first` and `.last` can format a comma-separated list without a trailing comma:

```mustache
{{#names}}{{#.first}}Contributors: {{/.first}}{{.}}{{^.last}}, {{/.last}}{{/names}}
```

With `names=["Ari", "Blake", "Casey"]`, this produces `Contributors: Ari, Blake, Casey`. Metadata is scoped to the nearest repeated section. Mapping sections retain normal Mustache context behaviour: Chevron does not iterate a mapping's keys or entries to create metadata.

## Conditional sections

`Extension.CONDITIONAL_SECTIONS` enables `{{?name}}...{{/name}}`. It tests a value and renders its body once only when the value is truthy. Unlike an ordinary section, it neither changes the active context nor repeats its body for a collection.

```python
from chevron import Extension

Extension.enable(Extension.CONDITIONAL_SECTIONS)
```

```mustache
{{?changes}}
## {{release_name}}
{{/changes}}
```

Given:

```python
{
    "release_name": "0.18.0",
    "changes": [{"summary": "Conditional sections"}],
}
```

the output is `## 0.18.0`. `changes` establishes whether the body renders, but it does not become the current context. `{{release_name}}` therefore continues to resolve from the surrounding data, and a non-empty `changes` collection still renders the body only once. A callable is tested as a value and is not invoked by a conditional section.

When this extension is disabled, `?` remains part of an ordinary variable name. For example, `{{?changes}}` can interpolate a context value stored under the literal key `"?changes"`. A paired `{{?changes}}...{{/changes}}` is structurally invalid until the extension is enabled; Chevron logs a warning naming `Extension.CONDITIONAL_SECTIONS` before raising its ordinary template error.

For an unsized iterator or asynchronous iterable, a conditional section may observe one item to establish truthiness and retains it for a later ordinary section using the identical lookup name in the same render frame. Conditional sections do not expose positional metadata; enable `ENHANCED_ITERATORS` separately when a repeated section needs it.

## Other Chevron APIs

The following opt-in APIs are not extensions and do not use `Extension.enable()`:

- [Lambdas](../language/lambdas.md) documents `chevron.func`, `chevron.section`, and `chevron.compat`.
- [Async rendering](../api/async-render.md) documents `async_render()` and its optional AnyIO support.
- [`render()`](../api/render.md) documents filesystem-partial confinement.
- [The tokenizer API](../api/tokenizer.md) documents pre-parsed token streams.

For release-to-release differences from Chevron 0.14.0, see the [compatibility reference](compatibility.md).
