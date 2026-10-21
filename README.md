[![PyPI version](https://badge.fury.io/py/chevron-ng.svg)](https://badge.fury.io/py/chevron-ng)

# Chevron

Chevron is a modern Python implementation of the [Mustache templating language](https://mustache.github.io/). It is a maintained fork of the original `chevron`, with current Python support, pinned Mustache conformance fixtures, safe opt-in filesystem partials, explicit lambda protocols, and optional runtime-neutral async rendering.

Chevron requires Python 3.11 or later.

```python
import chevron

chevron.render("Hello, {{name}}!", {"name": "Ada"})
```

## Command line

Render a template file with optional JSON data and a trusted partial directory:

```shell
chevron greeting.mustache --data values.json --path partials
```

Run `chevron --help` for delimiters, partial extension, and version options.
The CLI retains its historical current-directory partial lookup default; use
`--path` to select the directory deliberately.

## Library use

`render()` accepts template text, tokens, and ordinary file-like objects.
Provide in-memory partials through `partials_dict`; filesystem lookup is
disabled for library calls until `partials_path` is supplied.

```python
chevron.render(
    "{{> greeting}}",
    {"name": "Ada"},
    partials_dict={"greeting": "Hello, {{name}}!"},
)
```

For untrusted templates, supply an explicit `lambdas` mapping, including
`lambdas={}` when no callable tags are allowed. This restricts callable
template extensions but is not a general template sandbox: keep secrets and
rich objects out of template data. Filesystem partials reject absolute names,
parent traversal, and resolved paths outside the configured directory.

Chevron is quiet by default. Use `warn=True` for recoverable diagnostics, or
pass a standard-library logger for application-owned logging configuration.

Async rendering requires the optional `anyio` extra; applications using Trio
also require the `trio` extra. For the complete synchronous and asynchronous
API, lambda protocols, logging, resource ownership, and migration guidance,
see the [API reference](https://github.com/deeprave/chevron/blob/main/API.md).

Chevron retains a pinned copy of the Mustache specification fixtures, including lambda cases. See its [attribution](tests/fixtures/mustache-spec/README.md). If Chevron fails a Mustache case, please [open an issue](https://github.com/deeprave/chevron/issues/new).

## Development

The suite combines Chevron behavioural tests, pinned Mustache fixtures, and bounded property tests.
