[![PyPI version](https://badge.fury.io/py/chevron.svg)](https://badge.fury.io/py/chevron)

A Python implementation of the [Mustache templating language](https://mustache.github.io).

Why chevron?
------------

I'm glad you asked!

### chevron is fast ###

Chevron runs in less than half the time of [pystache](http://github.com/defunkt/pystache) (Which is not even up to date on the spec).
And in about 70% the time of [Stache](https://github.com/hyperturtle/Stache) (A 'trimmed' version of mustache, also not spec compliant).

### chevron is consistently formatted ###

[Ruff](https://docs.astral.sh/ruff/) checks and formats the codebase, and
[ty](https://docs.astral.sh/ty/) checks the library's types.

### chevron is spec compliant ###

Chevron includes a pinned copy of the [Mustache specification](https://github.com/mustache/spec)
fixtures, including lambda cases. See the fixture [attribution README](tests/fixtures/mustache-spec/README.md).

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
    # defaults to .
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

INSTALL
-------

- with git
```
$ git clone https://github.com/deeprave/chevron.git
```

Also available on pypi!

- with pip
```
$ pip install chevron
```



TODO
---

* get popular
* have people complain
* fix those complaints
