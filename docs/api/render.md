# `render()`

```python
chevron.render(template="", data={}, partials_path=None, partials_ext="mustache", partials_dict={}, padding="", def_ldel="{{", def_rdel="}}", scopes=None, warn=False, lambdas=None, *, logger=None, log_level=logging.WARNING)
```

`render()` returns the complete rendered string synchronously. It accepts template source text, a materialised token sequence, or an ordinary file-like object whose `read()` returns text. It does not close caller-owned readers.

```python
import chevron

email = chevron.render(
    "Subject: {{subject}}\n\n{{> body}}",
    {"subject": "Build complete", "recipient": "Mina"},
    partials_dict={"body": "Hello {{recipient}}, your build is ready."},
)
```

## Inputs and configuration

`data` is the initial context. `scopes` supplies an existing sequence of contexts when an embedding application intentionally continues a render; ordinary callers should supply `data` instead. Chevron treats the outer scope sequence as private render state and does not mutate the caller's sequence.

`def_ldel` and `def_rdel` select initial delimiters. `padding` is an internal-compatible partial-indentation input and is rarely appropriate for application calls.

`partials_dict` is searched before `partials_path`. If filesystem partials are enabled, Chevron appends `partials_ext` (default `mustache`) and permits only resolved files contained by `partials_path`. An absolute partial name, parent traversal, unreadable file, or unavailable name renders as an empty partial and can be inspected through [diagnostics](diagnostics.md).

`lambdas` selects explicit lambda mode; read [Lambdas](../language/lambdas.md) before exposing callbacks to template authors.

## Token streams

Pass a materialised token sequence when template source has already been tokenized and validated. Do not pass the `tokenize()` generator directly if it must be reused: a generator is consumed after one render. The [tokenizer API](tokenizer.md) documents the accepted tuple shapes and structural validation.

## Errors

Malformed template source raises `chevron.ChevronError`, a `SyntaxError` subclass. Direct-token structural errors also raise `ChevronError`, while malformed token values raise `TypeError`. An awaitable returned by a reader or lambda, or an async iterable used as a section value, is rejected by `render()` with a `TypeError` that directs callers to [`async_render()`](async-render.md).
