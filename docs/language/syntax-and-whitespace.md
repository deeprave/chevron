# Syntax and whitespace

Mustache normally uses `{{` and `}}`. Delimiters can change inside a template when embedding another language that uses braces:

```mustache
{{=<% %>=}}
const release = "<% version %>";
<%={{ }}=%>
Published by {{author}}.
```

The delimiter change itself produces no output. `render()` and `async_render()` can also set the initial pair through `def_ldel` and `def_rdel`.

## Standalone lines and indentation

When a comment, section tag, partial, parent, block, or delimiter-change tag is alone on a line apart from spaces, Mustache removes that whole line. This lets structural tags stay readable without leaving blank lines in the output.

Indented partials apply their leading whitespace to every non-empty line produced by the partial. This is useful for YAML, configuration, and HTML fragments:

```mustache
services:
  {{> worker}}
```

If `worker` contains `image: app:1\nports: [8080]`, the output remains indented under `services`. The same rules apply when a partial participates in an inheritance layout; see [partials and layouts](partials-and-layouts.md).
