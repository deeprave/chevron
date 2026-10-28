# `chevron.tokenizer`

The tokenizer is a supported submodule API for applications that inspect, cache, or transport template structure. Import it explicitly:

```python
from chevron.tokenizer import tokenize
```

There is no `chevron.tokenize` root export.

```python
import chevron
from chevron.tokenizer import tokenize

source = "{{#items}}<li>{{name}}</li>{{/items}}"
tokens = list(tokenize(source))

assert chevron.render(tokens, {"items": [{"name": "Ada"}]}) == "<li>Ada</li>"
```

`tokenize()` accepts source text only and returns a generator. Materialise it before caching or rendering more than once. `render()` and `async_render()` accept the materialised sequence and validate its structural nesting as they render it.

## Token shapes

By default every token is a two-item tuple: `(tag_type, tag_key)`. `include_raw=True` emits three items: `(tag_type, tag_key, raw_source)`. The raw stream retains source-only comment and standalone-whitespace records required by standard section lambdas.

```python
tokens = list(tokenize("Hello {{name}}", include_raw=True))
# [("literal", "Hello ", "Hello "), ("variable", "name", "{{name}}")]
```

The renderer accepts a complete token sequence representing one whole template, not an arbitrary fragment to be spliced into an active render. It checks matching section, parent, and block boundaries. Structural errors raise `chevron.ChevronError`; malformed token values raise `TypeError`.

Tokenisation avoids repeating lexical work; it does not cache lookup, partial resolution, lambdas, or rendering. Applications that cache tokens therefore remain responsible for choosing an appropriate cache lifetime and for rerendering with current data.
