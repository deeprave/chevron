# Getting started

Chevron requires Python 3.11 or later. The core package renders synchronously. Async rendering additionally needs the `anyio` extra; applications that run on Trio also need the `trio` extra.

The following example renders a useful page fragment rather than a single replacement. The template can stay with the application, while the view data is a normal Python mapping.

```python
import chevron

template = """<article>
  <h1>{{title}}</h1>
  {{#summary}}<p>{{summary}}</p>{{/summary}}
  <ul>{{#tags}}<li>{{.}}</li>{{/tags}}</ul>
</article>"""

page = chevron.render(
    template,
    {
        "title": "Release notes",
        "summary": "Changes ready for review.",
        "tags": ["documentation", "mustache"],
    },
)
```

The result is one complete string. Values are HTML-escaped by default, sections repeat or omit content according to their value, and `{{.}}` means the current list item. Continue with [values and contexts](language/values-and-contexts.md) for those rules.

## A useful division of responsibility

Templates decide presentation. Application code decides which data, partial mappings, filesystem directory, lambda mapping, and logger are safe to expose. Chevron does not turn a template into a sandbox: do not place secrets or powerful application objects in template data merely because a template is untrusted.

For an application that keeps reusable components in memory, pass `partials_dict`; for a controlled template directory, pass `partials_path`. The [partials and layouts](language/partials-and-layouts.md) chapter covers both patterns.
