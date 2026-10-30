# Sections

Sections use `{{#name}}...{{/name}}`. They are the main way to express optional and repeated content without placing conditional code in a template. At their simplest, ordinary sections are conditional: when `name` resolves to a truthy value, Chevron renders the content between the opening and closing tags; when it is missing, false, or empty, Chevron skips that content.

Within a section whose value is a scalar, `{{.}}` interpolates that current value. For example, `{{#status}}Status: {{.}}{{/status}}` renders `Status: ready` when `status` is `"ready"`.

Inverted sections use `{{^name}}...{{/name}}`. They select their content when `name` is missing, false, or empty, and skip it when `name` is truthy. Use an inverted section beside an ordinary section when a template needs a fallback for absent content.

## Repeating a section

Sections are Mustache's loop construct: a section whose value is a list, tuple, or iterator renders its body once for each item. There is no separate loop syntax. This template renders a release summary:

```mustache
{{#release}}
## {{version}}
{{#changes}}- {{kind}}: {{summary}}
  Labels: {{#labels}}{{.}} {{/labels}}
{{/changes}}
{{^changes}}- No user-facing changes.
{{/changes}}
{{/release}}
```

This data produces one bullet for each change:

```python
{
    "release": {
        "version": "0.17.1",
        "changes": [
            {
                "kind": "Added",
                "summary": "Async rendering",
                "labels": ["feature", "optional-dependency"],
            },
            {
                "kind": "Fixed",
                "summary": "Partial indentation",
                "labels": ["bugfix"],
            },
        ],
    },
}
```

Each `changes` item becomes the nearest context while its iteration is rendered, so `{{kind}}` and `{{summary}}` resolve from that item's mapping. The nested `labels` section repeats for each string label; strings do not have named fields, so `{{.}}` means the current label itself. Lookup still falls back to outer contexts, so `{{version}}` remains available from `release` inside every `changes` item. An empty collection, `false`, or a missing value skips the ordinary section and selects the inverted section, `{{^changes}}...{{/changes}}`.

The rendered output is:

```text
## 0.17.1
- Added: Async rendering
  Labels: feature optional-dependency
- Fixed: Partial indentation
  Labels: bugfix
```

For a list of strings, `{{.}}` refers to each current item. For a boolean, a truthy value renders the body once without adding a new useful mapping context.

Sections are also the historical shape of Mustache lambdas. Chevron supports them deliberately, but they are application callbacks rather than template-defined functions; see [lambdas](lambdas.md).

## Iterators and generators

Python iterators and asynchronous iterables are streaming section sources. By default, Chevron follows ordinary Python truthiness for them: an iterator object is truthy even when it has no remaining items. Enable [`Extension.INVERTED_ITERATORS`](../reference/extensions.md#optional-rendering-extensions) during application startup when an empty generator should select `{{^items}}...{{/items}}`.

With that extension enabled, Chevron uses one cursor for an iterator name in its supplying context during a render. An inverted section may advance one item to determine whether that cursor is empty; it retains that item for a later ordinary section and does not materialise the rest of the source. A recognised iterator or asynchronous iterable can then be traversed only once in a render: once Chevron exhausts a non-empty cursor, later ordinary sections render no items rather than restarting it. Its non-empty result remains stable for inverted sections, so it does not become a fallback merely because an earlier ordinary section consumed it. Lists and tuples retain their normal repeatable section behaviour. `async_render()` applies the same rule to asynchronous iterables.

This rule applies only after Chevron has classified the resolved value. A callable keeps its lambda behaviour and is never invoked merely to decide an inverted section.

When `INVERTED_ITERATORS` is enabled and a template needs to traverse a streaming collection or generator more than once, provide an independently constructed iterator under a separate name for each traversal. Chevron preserves a cursor only for repeated use of the same name in the same context; it does not coordinate aliases that happen to reference one iterator object.
