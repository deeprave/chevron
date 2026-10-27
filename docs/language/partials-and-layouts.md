# Partials and layouts

A partial, `{{> card}}`, renders another template with the active context. Supply reusable fragments through `partials_dict` when the application owns them in memory:

```python
chevron.render(
    "{{#products}}{{> product_card}}{{/products}}",
    {"products": [{"name": "Keyboard"}, {"name": "Trackpad"}]},
    partials_dict={"product_card": "<article>{{name}}</article>\n"},
)
```

Filesystem lookup is disabled unless `partials_path` is supplied. Chevron rejects absolute names, parent traversal, and resolved paths outside that directory. Use a mapping when selection must be an allow-list; see [`render()`](../api/render.md) for the partial lookup order.

## Dynamic names

`{{>*selector}}` resolves `selector` from the active context and uses its string value as the partial name. It is useful when data selects one of a known set of components:

```mustache
{{#notifications}}
  {{>*presentation.partial}}
{{/notifications}}
```

With `presentation.partial` set to `warning` or `success`, the surrounding context remains available to the selected partial. A dynamic name still uses mapped-partial precedence and filesystem containment. Empty, non-string, missing, or doubly dereferenced names render nothing.

## Inheritance layouts

Parents provide named blocks; a child invocation replaces those blocks:

```mustache
{{< page}}
  {{$title}}Release {{version}}{{/title}}
  {{$body}}{{> release_body}}{{/body}}
{{/page}}
```

The parent `page` might contain `<title>{{$title}}Untitled{{/title}}</title>` and `<main>{{$body}}Empty{{/body}}</main>`. The first block of a given name in the invoking template is the deterministic replacement. Parent names may also be dynamic with `{{<*layout}}...{{/*layout}}`.

`*`, `<`, and `$` are meaningful tag prefixes. See [compatibility](../reference/compatibility.md) before relying on literal partial names beginning with `*` or variables beginning with `<` or `$`.
