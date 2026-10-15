from os import linesep, path

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field

from .tokenizer import tokenize


import sys

if sys.version_info[0] == 3:
    python3 = True
    unicode_type = str
    string_type = str

    def unicode(x, y):
        return x

else:  # python 2
    python3 = False
    unicode_type = unicode
    string_type = basestring  # noqa: F821 (This is defined in python2)


#
# Helper functions
#


def _html_escape(string):
    """HTML escape all of these " & < >"""

    html_codes = {
        '"': "&quot;",
        "<": "&lt;",
        ">": "&gt;",
    }

    # & must be handled first
    string = string.replace("&", "&amp;")
    for char in html_codes:
        string = string.replace(char, html_codes[char])
    return string


def _get_key(key, scopes, warn=False, allow_callable_traversal=True):
    """Get a key from the current scope."""

    blocked_callable_traversal = False

    # If the key is a dot
    if key == ".":
        # Then just return the current scope
        return scopes[0]

    # Loop through the scopes
    for scope in scopes:
        try:
            # For every dot seperated key
            for child in key.split("."):
                if not allow_callable_traversal and isinstance(scope, Callable):
                    blocked_callable_traversal = True
                    raise KeyError("callable values are lookup leaves")

                # Move into the scope
                try:
                    # Try subscripting (Normal dictionaries)
                    scope = scope[child]
                except (TypeError, AttributeError):
                    try:
                        provisional_scope = getattr(scope, child)
                        if callable(provisional_scope):
                            raise TypeError("skipping callable")
                        scope = provisional_scope
                    except (TypeError, AttributeError):
                        # Try as a list
                        scope = scope[int(child)]

            # Return an empty string if falsy, with two exceptions
            # 0 should return 0, and False should return False
            if scope in (0, False):
                return scope

            try:
                # This allows for custom falsy data types
                # https://github.com/noahmorrison/chevron/issues/35
                if scope._CHEVRON_return_scope_when_falsy:
                    return scope
            except AttributeError:
                return scope or ""
        except (AttributeError, KeyError, IndexError, ValueError):
            # We couldn't find the key in the current scope
            # We'll try again on the next pass
            pass

    # We couldn't find the key in any of the scopes

    if warn:
        if blocked_callable_traversal:
            message = (
                "Could not resolve '%s': callable values cannot be traversed "
                "when lambdas= is supplied"
            ) % key
        else:
            message = "Could not find key '%s'" % key
        sys.stderr.write("%s%s" % (message, linesep))

    return ""


def _get_partial(name, partials_dict, partials_path, partials_ext):
    """Load a partial"""
    try:
        # Maybe the partial is in the dictionary
        return partials_dict[name]
    except KeyError:
        # Don't try loading from the file system if the partials_path is None or empty
        if partials_path is None or partials_path == "":
            return ""

        # Nope...
        try:
            # Maybe it's in the file system
            path_ext = "." + partials_ext if partials_ext else ""
            partial_path = path.join(partials_path, name + path_ext)
            with open(partial_path, "r", encoding="utf-8") as partial:
                return partial.read()

        except OSError:
            # Alright I give up on you
            return ""


@dataclass
class _RenderContext:
    """The scopes and configured section lambdas for one rendering operation."""

    scopes: list
    lambdas: dict | None
    token_cache: dict = field(default_factory=dict)

    @classmethod
    def from_inputs(cls, data, scopes, lambdas):
        render_scopes = scopes if scopes is not None else [data]
        explicit_lambdas = None
        if lambdas is not None:
            if not isinstance(lambdas, Mapping):
                raise TypeError(
                    "lambdas must be a mapping of section names to callables"
                )

            explicit_lambdas = dict(lambdas)
            for name, definition in explicit_lambdas.items():
                if not isinstance(name, str):
                    raise TypeError("lambdas mapping keys must be strings")
                if not isinstance(definition, Callable):
                    raise TypeError("lambdas mapping values must be callable")
        return cls(render_scopes, explicit_lambdas)

    @property
    def allows_callable_traversal(self):
        """Whether dotted lookup may traverse attributes of callable values."""

        return self.lambdas is None

    def prepend_scope(self, scope):
        self.scopes.insert(0, scope)

    def pop_scope(self):
        del self.scopes[0]

    def with_prepended_scope(self, scope):
        return _RenderContext(
            [scope] + self.scopes,
            self.lambdas,
            self.token_cache,
        )

    def lookup(self, key, warn=False):
        value = _get_key(
            key,
            self.scopes,
            warn=warn,
            allow_callable_traversal=self.allows_callable_traversal,
        )

        if self.lambdas is not None and isinstance(value, Callable):
            if warn:
                self.warn_rejected_callable_data(key)
            return ""
        return value

    def lambda_for(self, key):
        if self.lambdas is None:
            return None
        return self.lambdas.get(key)

    def warn_rejected_callable_data(self, key):
        message = "Callable template data '%s' is rejected when lambdas= is supplied"
        sys.stderr.write("%s%s" % (message % key, linesep))


def render(
    template="",
    data={},
    partials_path=None,
    partials_ext="mustache",
    partials_dict={},
    padding="",
    def_ldel="{{",
    def_rdel="}}",
    scopes=None,
    warn=False,
    lambdas=None,
):
    """Render a mustache template.

    Renders a mustache template with a data scope and partial capability.
    Given the file structure...
    ╷
    ├─╼ main.py
    ├─╼ main.ms
    └─┮ partials
      └── part.ms

    then main.py would make the following call:

    render(open('main.ms', 'r'), {...}, 'partials', 'ms')


    Arguments:

    template      -- A file-like object or a string containing the template

    data          -- A python dictionary with your data scope

    partials_path -- The path to where your partials are stored
                     If set to None, then partials won't be loaded from the file system
                     (defaults to None). Supply '.' to restore the historic
                     process-current-directory lookup behaviour.

    partials_ext  -- The extension that you want the parser to look for
                     (defaults to 'mustache')

    partials_dict -- A python dictionary which will be search for partials
                     before the filesystem is. {'include': 'foo'} is the same
                     as a file called include.mustache
                     (defaults to {})

    padding       -- This is for padding partials, and shouldn't be used
                     (but can be if you really want to)

    def_ldel      -- The default left delimiter
                     ("{{" by default, as in spec compliant mustache)

    def_rdel      -- The default right delimiter
                     ("}}" by default, as in spec compliant mustache)

    scopes        -- The list of scopes that get_key will look through

    warn -- Issue a warning to stderr when a template substitution isn't found in the data

    lambdas -- Optional mapping defining callable section names. In explicit mode,
               mapped names take precedence over template data. Callable values in
               template data are rejected; supplying an empty mapping disables
               callable sections. When omitted, callable values reached through
               template context retain legacy two-argument section-lambda behaviour.


    Returns:

    A string containing the rendered template.
    """

    context = _RenderContext.from_inputs(data, scopes, lambdas)
    return _render(
        template,
        context=context,
        partials_path=partials_path,
        partials_ext=partials_ext,
        partials_dict=partials_dict,
        padding=padding,
        def_ldel=def_ldel,
        def_rdel=def_rdel,
        warn=warn,
    )


def _render(
    template,
    *,
    context,
    partials_path,
    partials_ext,
    partials_dict,
    padding,
    def_ldel,
    def_rdel,
    warn,
):
    """Render a template with an existing private render context."""

    # If the template is a seqeuence but not derived from a string
    if isinstance(template, Sequence) and not isinstance(template, string_type):
        # Then we don't need to tokenize it
        # But it does need to be a generator
        tokens = (token for token in template)
    else:
        if template in context.token_cache:
            tokens = (token for token in context.token_cache[template])
        else:
            # Otherwise make a generator
            tokens = tokenize(template, def_ldel, def_rdel)

    output = unicode("", "utf-8")

    scopes = context.scopes

    # Run through the tokens
    for tag, key in tokens:
        # Set the current scope
        current_scope = scopes[0]

        # If we're an end tag
        if tag == "end":
            # Pop out of the latest scope
            context.pop_scope()

        # If the current scope is falsy and not the only scope
        elif not current_scope and len(scopes) != 1:
            if tag in ["section", "inverted section"]:
                # Set the most recent scope to a falsy value
                # (I heard False is a good one)
                context.prepend_scope(False)

        # If we're a literal tag
        elif tag == "literal":
            # Add padding to the key and add it to the output
            if not isinstance(key, unicode_type):  # python 2
                key = unicode(key, "utf-8")
            output += key.replace("\n", "\n" + padding)

        # If we're a variable tag
        elif tag == "variable":
            # Add the html escaped key to the output
            thing = context.lookup(key, warn=warn)
            if thing is True and key == ".":
                # if we've coerced into a boolean by accident
                # (inverted tags do this)
                # then get the un-coerced object (next in the stack)
                thing = scopes[1]
            if not isinstance(thing, unicode_type):
                thing = unicode(str(thing), "utf-8")
            output += _html_escape(thing)

        # If we're a no html escape tag
        elif tag == "no escape":
            # Just lookup the key and add it
            thing = context.lookup(key, warn=warn)
            if not isinstance(thing, unicode_type):
                thing = unicode(str(thing), "utf-8")
            output += thing

        # If we're a section tag
        elif tag == "section":
            # Explicit lambdas take precedence over template data.
            scope = context.lambda_for(key)
            if scope is None:
                scope = context.lookup(key, warn=warn)

            # If the scope is a callable (as described in
            # https://mustache.github.io/mustache.5.html)
            if isinstance(scope, Callable):
                # Generate template text from tags
                text = unicode("", "utf-8")
                tags = []
                for tag in tokens:
                    if tag == ("end", key):
                        break

                    tags.append(tag)
                    tag_type, tag_key = tag
                    if tag_type == "literal":
                        text += tag_key
                    elif tag_type == "no escape":
                        text += "%s& %s %s" % (def_ldel, tag_key, def_rdel)
                    else:
                        text += "%s%s %s%s" % (
                            def_ldel,
                            {
                                "commment": "!",
                                "section": "#",
                                "inverted section": "^",
                                "end": "/",
                                "partial": ">",
                                "set delimiter": "=",
                                "no escape": "&",
                                "variable": "",
                            }[tag_type],
                            tag_key,
                            def_rdel,
                        )

                context.token_cache[text] = tags

                rend = scope(
                    text,
                    lambda template, data=None: _render(
                        template,
                        context=(
                            context.with_prepended_scope(data) if data else context
                        ),
                        partials_path=partials_path,
                        partials_ext=partials_ext,
                        partials_dict=partials_dict,
                        padding=padding,
                        def_ldel=def_ldel,
                        def_rdel=def_rdel,
                        warn=warn,
                    ),
                )

                if python3:
                    output += rend
                else:  # python 2
                    output += rend.decode("utf-8")

            # If the scope is a sequence, an iterator or generator but not
            # derived from a string
            elif isinstance(scope, (Sequence, Iterator)) and not isinstance(
                scope, string_type
            ):
                # Then we need to do some looping

                # Gather up all the tags inside the section
                # (And don't be tricked by nested end tags with the same key)
                # TODO: This feels like it still has edge cases, no?
                tags = []
                tags_with_same_key = 0
                for tag in tokens:
                    if tag == ("section", key):
                        tags_with_same_key += 1
                    if tag == ("end", key):
                        tags_with_same_key -= 1
                        if tags_with_same_key < 0:
                            break
                    tags.append(tag)

                # For every item in the scope
                for thing in scope:
                    # Append it as the most recent scope and render
                    rend = _render(
                        template=tags,
                        context=context.with_prepended_scope(thing),
                        padding=padding,
                        partials_path=partials_path,
                        partials_ext=partials_ext,
                        partials_dict=partials_dict,
                        def_ldel=def_ldel,
                        def_rdel=def_rdel,
                        warn=warn,
                    )

                    if python3:
                        output += rend
                    else:  # python 2
                        output += rend.decode("utf-8")

            else:
                # Otherwise we're just a scope section
                context.prepend_scope(scope)

        # If we're an inverted section
        elif tag == "inverted section":
            # Add the flipped scope to the scopes
            scope = context.lambda_for(key)
            if scope is None:
                scope = context.lookup(key, warn=warn)
            context.prepend_scope(not scope)

        # If we're a partial
        elif tag == "partial":
            # Load the partial
            partial = _get_partial(key, partials_dict, partials_path, partials_ext)

            # Find what to pad the partial with
            left = output.rpartition("\n")[2]
            part_padding = padding
            if left.isspace():
                part_padding += left

            # Render the partial
            part_out = _render(
                template=partial,
                context=context,
                partials_path=partials_path,
                partials_ext=partials_ext,
                partials_dict=partials_dict,
                def_ldel=def_ldel,
                def_rdel=def_rdel,
                padding=part_padding,
                warn=warn,
            )

            # If the partial was indented
            if left.isspace():
                # then remove the spaces from the end
                part_out = part_out.rstrip(" \t")

            # Add the partials output to the ouput
            if python3:
                output += part_out
            else:  # python 2
                output += part_out.decode("utf-8")

    if python3:
        return output
    else:  # python 2
        return output.encode("utf-8")
