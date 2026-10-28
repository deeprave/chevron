# Template language overview

Mustache is deliberately small: tags look up values, sections select or repeat content, and partials compose templates. It is logic-light rather than logic-free; application code prepares meaningful data and templates render it predictably.

Read these chapters in order on a first pass:

1. [Values and contexts](values-and-contexts.md) explains interpolation and lookup.
2. [Sections](sections.md) adds conditional and repeated output.
3. [Partials and layouts](partials-and-layouts.md) composes reusable fragments and inheritance layouts.
4. [Syntax and whitespace](syntax-and-whitespace.md) records delimiter and indentation rules that affect real files.
5. [Lambdas](lambdas.md) covers the narrowly defined extension points where application code participates in rendering.

Chevron's language target is the pinned upstream Mustache manual, not an independently invented dialect. Read [Mustache and conformance](../reference/mustache.md) when you need the authoritative upstream context or fixture provenance.
