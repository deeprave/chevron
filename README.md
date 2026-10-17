[![PyPI version](https://badge.fury.io/py/chevron-ng.svg)](https://badge.fury.io/py/chevron-ng)

A Python implementation of the [Mustache templating language](https://mustache.github.io).

This is a direct fork of the now-unmaintained [noahmorrison/chevron](https://github.com/noahmorrison/chevron). It builds on that implementation, modernising the project, closing potential security gaps around template extensions, and bringing Mustache compliance up to date.

Future work includes asynchronous rendering and asynchronous partial handling.

Why chevron?
------------

I'm glad you asked!

### chevron is fast ###

Chevron runs in less than half the time of [pystache](http://github.com/defunkt/pystache) (Which is not even up to date on the spec).
And in about 70% the time of [Stache](https://github.com/hyperturtle/Stache) (A 'trimmed' version of mustache, also not spec compliant).

### chevron is spec compliant ###

Chevron includes a pinned copy of the [Mustache specification](https://github.com/mustache/spec) fixtures, including lambda cases. See the fixture [attribution README](tests/fixtures/mustache-spec/README.md).

If you find a test that Chevron does not pass, please [report it](https://github.com/deeprave/chevron/issues/new).

### chevron supports modern Python ###

Chevron requires Python 3.11 or later.

Development and verification
----------------------------

Install the development environment with `uv sync --dev`, then run `uv run pytest`. Chevron's own behavioural tests are separate from the vendored Mustache specification fixtures, which are retained unchanged as the deterministic conformance suite. Bounded Hypothesis properties complement those examples by exercising renderer and tokenizer invariants over generated input.

USAGE
-----

Commandline usage: (if installed via pypi)
```
usage: chevron [-h] [-v] [-d DATA] [-p PARTIALS_PATH] [-e PARTIALS_EXT]
               [-l DEF_LDEL] [-r DEF_RDEL]
               template

positional arguments:
  template              The mustache file

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -d DATA, --data DATA  The json data file
  -p PARTIALS_PATH, --path PARTIALS_PATH
                        The directory where your partials reside
  -e PARTIALS_EXT, --ext PARTIALS_EXT
                        The extension for your mustache partials, 'mustache'
                        by default
  -l DEF_LDEL, --left-delimiter DEF_LDEL
                        The default left delimiter, "{{" by default.
  -r DEF_RDEL, --right-delimiter DEF_RDEL
                        The default right delimiter, "}}" by default.
```

Python usage with strings
```python
import chevron

chevron.render("Hello, {{ mustache }}!", {"mustache": "World"})
```

Python usage with file
```python
import chevron

with open("file.mustache", "r") as f:
    chevron.render(f, {"mustache": "World"})
```

Python usage with unpacking
```python
import chevron

args = {"template": "Hello, {{ mustache }}!", "data": {"mustache": "World"}}

chevron.render(**args)
```

chevron supports partials (via dictionaries)
```python
import chevron

args = {"template": "Hello, {{> thing }}!", "partials_dict": {"thing": "World"}}

chevron.render(**args)
```

chevron supports partials (via the filesystem)
```python
import chevron

args = {
    "template": "Hello, {{> thing }}!",
    # filesystem lookup is enabled only when this path is supplied
    "partials_path": "partials/",
    # defaults to mustache
    "partials_ext": "ms",
}

# ./partials/thing.ms will be read and rendered
chevron.render(**args)
```

chevron supports lambdas

For new code, use the `lambdas=` mapping to declare the callable protocol for each render. Registered names are resolved before template data, and template-data callables are rejected in explicit mode. This keeps executable extensions separate from the data exposed to a template. This is the recommended mode for untrusted templates, although it is not a general template sandbox.

Use `@chevron.func` for a zero-argument interpolation lambda. Chevron renders its returned text with the render's configured default delimiters, then applies the escaping requested by the interpolation tag. The decorator is required for this new protocol whether the callable is supplied through `lambdas=` or ordinary compatibility-mode template data.

```python
import chevron


@chevron.func
def greeting():
    return "{{name}}"


chevron.render("Hello, {{greeting}}!", {"name": "Ada"}, lambdas={"greeting": greeting})
```

Use `@chevron.section` for a Mustache-standard one-argument section lambda. It receives the unprocessed text between its section tags and Chevron recursively renders its return value using the delimiters active when that section opens. The decorator is required for this new protocol in both explicit and compatibility modes.

```python
import chevron


@chevron.section
def repeat(text):
    return text + text


chevron.render(
    "{{#repeat}}{{name}}{{/repeat}}", {"name": "Ada"}, lambdas={"repeat": repeat}
)
```

Use `@chevron.compat` for Chevron’s original two-argument section callback. It receives the historical compatibility text and a `render()` callback which can render it with optional temporary data. That helper starts with the render's configured default delimiters. Undecorated section callbacks continue to use this protocol, but the decorator makes compatibility usage explicit and easy to find.

```python
import chevron


@chevron.compat
def select_first(text, render):
    return render(text).split(" || ", 1)[0]


chevron.render(
    "{{#select_first}}{{first}} || {{second}}{{/select_first}}",
    {"first": "one", "second": "two"},
    lambdas={"select_first": select_first},
)
```

Pass `lambdas={}` to configure no callable section tags explicitly. In explicit mode, callable values in template data are rejected and render as empty values; with `warn=True`, Chevron writes a diagnostic (currently to standard error). A lambda which returns `None` also renders as an empty value and emits that diagnostic when warnings are enabled. Callable values are also lookup leaves, so a template cannot traverse their attributes.

This is intentional for all callable values, including callable instances and classes. For example, `{{build.version}}` does not traverse a callable `build` in explicit mode. Expose only the needed plain data through an authorised section lambda instead:

```python
def build(text, render):
    return render(text, {"version": Build.version})


chevron.render(
    "{{#build}}{{version}}{{/build}}",
    {},
    lambdas={"build": build},
)
```

Omitting `lambdas` (or passing `None`) retains Chevron's permissive compatibility mode so existing two-argument section callbacks keep working. In this mode, callable values resolved through normal mapping or sequence lookup may execute, including after a non-callable object attribute. A callable obtained directly from an object attribute is still not invoked. Undecorated interpolation callables keep their historic stringification behaviour; use `@chevron.func` to invoke one.

For untrusted templates, always provide an explicit `lambdas` mapping, even if it is empty. This controls callable section execution only; it is not a general template sandbox. Keep secrets and rich objects out of template data, supply only plain values where possible.

Library renders now disable filesystem partial lookup by default. Use vetted partial source in `partials_dict`, or opt in to a trusted filesystem directory:

```python
chevron.render(template, data, partials_path="/srv/app/partials")
```

Use `partials_path="."` only when restoring the historic process-current-
directory lookup intentionally, but this can potentially leak server data if poorly crafted or untrusted templates are rendered.


TODO
---

* get popular
* have people complain
* fix those complaints
