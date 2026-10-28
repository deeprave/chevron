# Sections

Sections use `{{#name}}...{{/name}}`. They are the main way to express optional and repeated content without placing conditional code in a template.

```mustache
{{#release}}
## {{version}}
{{#changes}}- {{kind}}: {{summary}}
{{/changes}}
{{^changes}}- No user-facing changes.
{{/changes}}
{{/release}}
```

When `release` is a mapping, its fields become the nearest context for its body. When `changes` is a list, the body renders once per item; outer values such as `version` remain available. An empty list, `false`, or a missing value skips the ordinary section and selects the inverted section, `{{^changes}}...{{/changes}}`.

For a list of strings, `{{.}}` refers to each current item. For a boolean, a truthy value renders the body once without adding a new useful mapping context.

Sections are also the historical shape of Mustache lambdas. Chevron supports them deliberately, but they are application callbacks rather than template-defined functions; see [lambdas](lambdas.md).
