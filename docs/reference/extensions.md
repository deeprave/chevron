# Chevron extensions

Chevron adds a small set of documented interfaces around Mustache rather than changing the ordinary value, section, and partial model.

## Optional rendering extensions

`chevron.Extension` controls optional rendering behaviour that the Mustache specification does not define. Configure extensions once during application startup, before the application begins rendering templates. They are process-wide settings; changing them later at runtime or while a render is active is outside Chevron's supported contract.

```python
from chevron import Extension

Extension.enable(Extension.ENHANCED_ITERATORS)
```

`ENHANCED_ITERATORS` makes an empty Python iterator or async iterable select its paired inverted section, just as an empty list does. Within a repeated section it also exposes `.first`, `.last`, `.index`, `.ordinal`, and `.length`; sized, indexable sources additionally expose `.0`, `.1`, and later values. It gives a streaming source one cursor for the render, retaining only the bounded lookahead needed for inversion and last-item metadata. See [sections](../language/sections.md#iterators-and-generators) for the template contract.

Enable every extension implemented by the installed Chevron version with `Extension.ALL`:

```python
Extension.enable(Extension.ALL)
```

`Extension.NONE` is the default. The first call to `enable()` selects the complete process-wide extension mask and freezes it; a later call raises `RuntimeError`. Configure extensions during application startup, before rendering any templates. Renderer code can inspect a particular setting with `Extension.is_enabled(...)`; applications normally only need `enable()` during startup.

## Explicit lambda protocols

`chevron.func`, `chevron.section`, and `chevron.compat` make a callable's template role explicit. Passing a `lambdas` mapping enables explicit mode, where undeclared callable data is rejected and the mapping takes precedence. This is a Chevron API feature; see [Lambdas](../language/lambdas.md).

## Async rendering

`async_render()` integrates with a caller-owned AnyIO runtime. It awaits declared lambdas, async readers, and async iterables while preserving ordinary Mustache output semantics. It is an API extension, not an alternative template syntax; see [async rendering](../api/async-render.md).

## Safe filesystem partials

Library filesystem partials are opt-in. `partials_path` confines resolved partial files to one directory and rejects absolute or escaping names. This is an application boundary, not a claim that rendering untrusted data is generally safe; see [`render()`](../api/render.md).

## Direct token streams

The `chevron.tokenizer` submodule exposes pre-parsing for applications that own template caching or inspection. It does not introduce a compiled-template format or change the template language. See [the tokenizer API](../api/tokenizer.md).
