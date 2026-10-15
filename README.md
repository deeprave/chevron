[![PyPI version](https://badge.fury.io/py/chevron-ng.svg)](https://badge.fury.io/py/chevron-ng)

A Python implementation of the [Mustache templating language](https://mustache.github.io).

This is a direct fork of the now-unmaintained [noahmorrison/chevron](https://github.com/noahmorrison/chevron). It builds on that implementation, modernising the project, closing potential security gaps around template extensions, and bringing Mustache compliance up to date.

Future work includes asynchronous rendering and partial support.

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
```python
import chevron


def first(text, render):
    # Return only the first occurrence of items.
    result = render(text)
    return [x.strip() for x in result.split(" || ") if x.strip()][0]


def inject_x(text, render):
    # inject data into scope
    return render(text, {"x": "data"})


args = {
    "template": "Hello, {{# first}} {{x}} || {{y}} || {{z}} {{/ first}}!  {{# inject_x}} {{x}} {{/ inject_x}}",
    "data": {"y": "foo", "z": "bar", "first": first, "inject_x": inject_x},
}

chevron.render(**args)
```

For new code using this implementation, use the `lambdas=` mapping to provide callables for a render. Chevron resolves tag names from template data first and, when a name is absent there, then from lambdas. When a callable is resolved from lambdas, it is invoked and replaced by what that callable returns. If the tag is a section tag, it receives the raw text between `{{#tagname}}` and `{{/tagname}}`.

```python
import chevron


def select_first(text, render):
    return render(text).split(" || ", 1)[0]


chevron.render(
    "{{#select_first}}{{first}} || {{second}}{{/select_first}}",
    {"select_first": select_first, "first": "one", "second": "two"},
    lambdas={"select_first": select_first},
)
```

Pass `lambdas={}` to disallow callables in templates explicitly. In explicit mode, callable values are lookup leaves: a template cannot traverse their attributes. A callable section absent from the supplied mapping behaves as a missing value; with `warn=True`, Chevron writes a diagnostic (currently to standard error).

This is intentional for all callable values, including callable instances and classes. For example, `{{build.version}}` does not traverse a callable `build` in explicit mode. Expose only the needed plain data through an authorised section lambda instead:

```python
def build(text, render):
    return render(text, {"version": Build.version})


chevron.render(
    "{{#build}}{{version}}{{/build}}",
    {"build": build},
    lambdas={"build": build},
)
```

Omitting `lambdas` (or passing `None`) retains Chevron's compatibility mode so existing two-argument section callbacks keep working. In this mode, callable values resolved through normal mapping or sequence lookup may execute, including after a non-callable object attribute. A callable obtained directly from an object attribute is still not invoked.

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
