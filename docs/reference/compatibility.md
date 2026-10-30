# Compatibility

This page records deliberate public differences from Chevron 0.14.0. It is a concise migration index, not a replacement for the linked feature documentation.

## Compatibility callouts

| Area | Difference from 0.14.0 | Reason and further reading |
| --- | --- | --- |
| Filesystem partials | Library rendering now defaults to `partials_path=None`; filesystem lookup is disabled until an application supplies a trusted directory. The CLI retains its current-directory default. | Avoid accidental access to files relative to the process working directory. See [partials and layouts](../language/partials-and-layouts.md) and [`render()`](../api/render.md). |
| Falsey values | `_CHEVRON_return_scope_when_falsy` is no longer read or honoured. | It was an undocumented private escape hatch that made falsey rendering depend on application object internals. Transform data before rendering instead. |
| Lambda policy | `lambdas=` enables an explicit callable allow-list. `@chevron.func`, `@chevron.section`, and `@chevron.compat` declare interpolation, standard-section, and compatibility protocols. Omitting `lambdas` retains legacy callable template-data behaviour. | Makes the application boundary and callback intent visible. See [lambdas](../language/lambdas.md). |
| Async rendering | `async_render()` adds support for declared async lambdas, async readers, and async iterables inside a caller-owned AnyIO runtime. Synchronous `render()` rejects awaitable reader or lambda results and async iterable section values. | A synchronous API cannot await those values. See [`async_render()`](../api/async-render.md) and [`render()`](../api/render.md). |
| Iterator inversion | `Extension.INVERTED_ITERATORS` optionally makes empty iterators and async iterables select their inverted sections. When enabled, a streaming value is traversed once per name in its supplying context during a render. | This is a non-standard extension that permits useful empty-generator behaviour without materialising a stream. See [sections](../language/sections.md#iterators-and-generators). |
| Extension configuration | Optional extensions are process-wide and disabled by default. Configure them once during application startup with `Extension.enable()`; the selected mask is then frozen. | Keeps template and render-call APIs stable. See [Chevron extensions](extensions.md). |
| Dynamic and inheritance syntax | `*`, `<`, and `$` are now reserved tag prefixes for dynamic partial or parent names, parents, and named blocks. Literal partial names beginning with `*`, and interpolation names beginning with `<` or `$`, are no longer available in those tag forms. | Required for current Mustache dynamic-name and inheritance support. See [partials and layouts](../language/partials-and-layouts.md). |
| Scope handling | Chevron no longer structurally mutates a caller-provided `scopes` sequence while rendering. | Nested rendering now has private frame state, preventing caller-visible scope-stack mutation. See [`render()`](../api/render.md). |
| Tokenizer input | `chevron.tokenizer.tokenize()` accepts template source text only; file-like input belongs to `render()` or `async_render()`. | Keeps tokenisation synchronous and makes input I/O a renderer concern. See [the tokenizer API](../api/tokenizer.md). |
| Deep expansion | Engine-owned nested partial, iterable-section, and lambda-result expansion is iterative and bounded; a cyclic expansion raises `RecursionError` rather than exhausting the Python call stack. | Provides predictable safety for deeply nested or cyclic templates. Application-initiated compatibility callback recursion remains application-owned. See [`async_render()`](../api/async-render.md#compatibility-callbacks). |

## Migration notes

The filesystem and explicit-lambda changes are the most important security-related migrations. Use `partials_dict` for an in-memory allow-list, pass an explicit trusted `partials_path` only when filesystem partials are required, and provide `lambdas={}` when callable tags are not allowed.

Iterator inversion is disabled unless an application enables `Extension.INVERTED_ITERATORS`. Leaving it disabled preserves Chevron's earlier iterator truthiness behaviour. When enabled, supply independently constructed iterators under separate names if a template needs more than one traversal of the same underlying collection.

The Mustache language target itself is the pinned [upstream Mustache manual](mustache.md). The additions and restrictions above describe Chevron-specific API and compatibility behaviour.
