# Compatibility

Chevron preserves the ordinary Mustache rendering model while documenting a few deliberate compatibility boundaries introduced by current conformance support.

## Names with reserved prefixes

`*` begins a dynamic partial or parent name. A literal partial whose name begins with `*` is therefore no longer available. Chevron 0.14.0 treated that form as a literal name. Names that use special tag-prefix characters are not a portable partial naming convention.

`<` begins a parent tag and `$` begins a named block tag. Consequently, `{{<name}}` and `{{$name}}` are not interpolations of variables beginning with those characters; they must form matching parent or block structures.

## Existing lambda callbacks

When `lambdas` is omitted, Chevron retains historical compatibility behavior for callable values found through template data. New applications should use an explicit mapping and decorators so their callable policy is visible. See [Lambdas](../language/lambdas.md) and the [`async_render()` compatibility contract](../api/async-render.md#compatibility-callbacks).

## Current-directory partial lookup

The library API disables filesystem partial lookup by default. Passing `partials_path="."` deliberately restores the historical current-directory behavior. The command-line interface retains its established current-directory default; use `--path` to select a directory explicitly.
