# Values and contexts

`{{name}}` interpolates a value from the active context and HTML-escapes it. Use `{{{name}}}` or `{{& name}}` only when the application intentionally supplies already-safe markup.

```mustache
<h2>{{project.name}}</h2>
<p>Requested by {{requester}}</p>
<div class="preview">{{{preview_html}}}</div>
```

With `{"project": {"name": "Quarterly plan"}, "requester": "Ari & Co.", "preview_html": "<em>Draft</em>"}`, this renders `Ari &amp; Co.` in ordinary interpolation and retains the trusted `<em>` element only for the explicit unescaped tag.

## Lookup rules

Names can be dotted: `{{project.name}}` traverses mapping-like or attribute-based values. Chevron searches the current context first and then outer contexts, which is why a page-level value can remain visible within a section. `{{.}}` selects the current context itself, useful when iterating simple values.

Missing values render as an empty string. That makes optional display data straightforward, but an application should validate required business data before rendering rather than relying on an empty result.

Comments, `{{! internal note }}`, never appear in output. See [syntax and whitespace](syntax-and-whitespace.md) for how a comment on its own line also removes that line's indentation and newline.
