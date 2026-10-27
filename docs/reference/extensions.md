# Chevron extensions

Chevron adds a small set of documented interfaces around Mustache rather than changing the ordinary value, section, and partial model.

## Explicit lambda protocols

`chevron.func`, `chevron.section`, and `chevron.compat` make a callable's template role explicit. Passing a `lambdas` mapping enables explicit mode, where undeclared callable data is rejected and the mapping takes precedence. This is a Chevron API feature; see [Lambdas](../language/lambdas.md).

## Async rendering

`async_render()` integrates with a caller-owned AnyIO runtime. It awaits declared lambdas, async readers, and async iterables while preserving ordinary Mustache output semantics. It is an API extension, not an alternative template syntax; see [async rendering](../api/async-render.md).

## Safe filesystem partials

Library filesystem partials are opt-in. `partials_path` confines resolved partial files to one directory and rejects absolute or escaping names. This is an application boundary, not a claim that rendering untrusted data is generally safe; see [`render()`](../api/render.md).

## Direct token streams

The `chevron.tokenizer` submodule exposes pre-parsing for applications that own template caching or inspection. It does not introduce a compiled-template format or change the template language. See [the tokenizer API](../api/tokenizer.md).
