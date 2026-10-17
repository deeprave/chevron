from os import linesep
from pathlib import Path

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import update_wrapper

from .tokenizer import _TokenizationState, tokenize as _tokenize


import sys

if sys.version_info[0] == 3:
    python3 = True
    unicode_type = str
    string_type = str

    def unicode(x, _):
        return x

else:  # python 2
    python3 = False
    unicode_type = unicode
    string_type = basestring  # noqa: F821 (This is defined in python2)


#
# Helper functions
#


_MISSING = object()
_FUNCTION_PROTOCOL = "function"
_SECTION_PROTOCOL = "section"
_COMPAT_PROTOCOL = "compat"


@dataclass
class _LambdaDefinition:
    """A callable together with its declared template protocol."""

    callback: Callable
    protocol: str

    def __post_init__(self):
        update_wrapper(self, self.callback)

    def __call__(self, *args, **kwargs):
        return self.callback(*args, **kwargs)

    def __get__(self, instance, owner):
        descriptor = getattr(self.callback, "__get__", None)
        if descriptor is None:
            return self
        return _LambdaDefinition(descriptor(instance, owner), self.protocol)


def _declare_lambda(callback, protocol):
    if not isinstance(callback, Callable):
        raise TypeError("lambda decorators require a callable")
    return _LambdaDefinition(callback, protocol)


def func(callback):
    """Declare a zero-argument Mustache interpolation lambda."""

    return _declare_lambda(callback, _FUNCTION_PROTOCOL)


def section(callback):
    """Declare a one-argument Mustache section lambda."""

    return _declare_lambda(callback, _SECTION_PROTOCOL)


def compat(callback):
    """Declare Chevron's legacy two-argument section-lambda protocol."""

    return _declare_lambda(callback, _COMPAT_PROTOCOL)


def _lambda_protocol(value, tag):
    """Resolve a callable's protocol without invoking it."""

    if isinstance(value, _LambdaDefinition):
        return value.protocol

    if tag == "section":
        return _COMPAT_PROTOCOL
    return None


def _normalise_value(key, value):
    """Apply Chevron's historic falsey-value rendering behaviour."""

    if value is _MISSING:
        return ""

    if key == ".":
        return value

    if value in (0, False):
        return value

    try:
        if value._CHEVRON_return_scope_when_falsy:
            return value
    except AttributeError:
        return value or ""

    return value or ""


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


def _get_key(
    key,
    scopes,
    warn=False,
    allow_callable_traversal=True,
    value_handler=None,
):
    """Get a key from the current scope."""

    blocked_callable_traversal = False

    # If the key is a dot
    if key == ".":
        # Then just return the current scope
        scope = scopes[0]
        return value_handler(scope) if value_handler is not None else scope

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

            return value_handler(scope) if value_handler is not None else scope
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

    return value_handler(_MISSING) if value_handler is not None else _MISSING


def _get_partial(name, partials_dict, partials_path, partials_ext):
    """Load a partial"""
    try:
        # Maybe the partial is in the dictionary
        return partials_dict[name]
    except KeyError:
        # Don't try loading from the file system if the partials_path is None or empty
        if partials_path is None or partials_path == "":
            return ""

        try:
            path_ext = "." + partials_ext if partials_ext else ""
            base_path = Path(partials_path).resolve(strict=True)
            partial_name = Path(name + path_ext)
            if partial_name.is_absolute() or ".." in partial_name.parts:
                return ""

            partial_path = (base_path / partial_name).resolve(strict=True)
            partial_path.relative_to(base_path)
            with partial_path.open("r", encoding="utf-8") as partial:
                return partial.read()

        except (OSError, RuntimeError, ValueError):
            return ""


@dataclass
class _RenderContext:
    """The scopes and configured section lambdas for one rendering operation."""

    scopes: list
    lambdas: dict | None
    default_ldel: str
    default_rdel: str
    token_cache: dict = field(default_factory=dict)
    tokenization_states: list[_TokenizationState] = field(default_factory=list)

    @classmethod
    def from_inputs(cls, data, scopes, lambdas, def_ldel, def_rdel):
        render_scopes = scopes if scopes is not None else [data]
        explicit_lambdas = None
        if lambdas is not None:
            if not isinstance(lambdas, Mapping):
                raise TypeError(
                    "lambdas must be a mapping of template names to callables"
                )

            explicit_lambdas = dict(lambdas)
            for name, definition in explicit_lambdas.items():
                if not isinstance(name, str):
                    raise TypeError("lambdas mapping keys must be strings")
                if not isinstance(definition, Callable):
                    raise TypeError("lambdas mapping values must be callable")
        return cls(render_scopes, explicit_lambdas, def_ldel, def_rdel)

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
            self.default_ldel,
            self.default_rdel,
            self.token_cache,
            self.tokenization_states,
        )

    def tokenize(self, template, def_ldel, def_rdel):
        """Tokenize within this render's nested diagnostic-state stack."""

        state = _TokenizationState()

        def tokens():
            self.tokenization_states.append(state)
            try:
                yield from _tokenize(
                    template,
                    def_ldel,
                    def_rdel,
                    include_raw=True,
                    _state=state,
                )
            finally:
                if (
                    not self.tokenization_states
                    or self.tokenization_states[-1] is not state
                ):
                    raise RuntimeError("tokenization state stack is unbalanced")
                self.tokenization_states.pop()

        return tokens()

    def lookup(self, key, warn=False, value_handler=None):
        def handle_value(value):
            if self.lambdas is not None and isinstance(value, Callable):
                if warn:
                    self.warn_rejected_callable_data(key)
                return ""
            if value_handler is not None:
                return value_handler(value)
            return value

        return _get_key(
            key,
            self.scopes,
            warn=warn,
            allow_callable_traversal=self.allows_callable_traversal,
            value_handler=handle_value,
        )

    def lambda_for(self, key):
        if self.lambdas is None:
            return None
        return self.lambdas.get(key)

    def warn_rejected_callable_data(self, key):
        message = "Callable template data '%s' is rejected when lambdas= is supplied"
        sys.stderr.write("%s%s" % (message % key, linesep))

    def warn_none_lambda_result(self, key):
        message = "Lambda '%s' returned None; rendering an empty value"
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

    lambdas -- Optional mapping defining callable template names. In explicit mode,
               mapped names take precedence over template data. Use chevron.func for
               zero-argument interpolation lambdas, chevron.section for standard
               one-argument section lambdas, and chevron.compat for Chevron's
               original two-argument section callbacks. Callable values in template
               data are rejected; supplying an empty mapping disables callable
               execution. When omitted, callable values reached through template
               context retain compatibility behaviour.


    Returns:

    A string containing the rendered template.
    """

    context = _RenderContext.from_inputs(data, scopes, lambdas, def_ldel, def_rdel)
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
    use_token_cache=False,
):
    """Render a template while restoring the incoming scope stack."""

    scopes = context.scopes
    original_scopes = list(scopes)
    try:
        return _render_inner(
            template,
            context=context,
            partials_path=partials_path,
            partials_ext=partials_ext,
            partials_dict=partials_dict,
            padding=padding,
            def_ldel=def_ldel,
            def_rdel=def_rdel,
            warn=warn,
            use_token_cache=use_token_cache,
        )
    finally:
        scopes[:] = original_scopes


def _render_inner(
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
    use_token_cache,
):
    """Render a template with an existing private render context."""

    # If the template is a seqeuence but not derived from a string
    if isinstance(template, Sequence) and not isinstance(template, string_type):
        # Then we don't need to tokenize it
        # But it does need to be a generator
        tokens = (token for token in template)
    else:
        if use_token_cache and template in context.token_cache:
            tokens = (token for token in context.token_cache[template])
        else:
            # Otherwise make a generator
            tokens = context.tokenize(template, def_ldel, def_rdel)

    output = unicode("", "utf-8")

    scopes = context.scopes
    current_ldel = def_ldel
    current_rdel = def_rdel

    def render_lambda_result(
        result, key, left_delimiter, right_delimiter, result_padding
    ):
        if result is None:
            if warn:
                context.warn_none_lambda_result(key)
            return ""
        if not isinstance(result, unicode_type):
            result = unicode(str(result), "utf-8")
        return _render(
            result,
            context=context,
            partials_path=partials_path,
            partials_ext=partials_ext,
            partials_dict=partials_dict,
            padding=result_padding,
            def_ldel=left_delimiter,
            def_rdel=right_delimiter,
            warn=warn,
        )

    def interpolation_value(key):
        registered = context.lambda_for(key)
        explicit = registered is not None
        if explicit:
            value = registered
        else:
            value = context.lookup(
                key,
                warn=warn,
                value_handler=lambda candidate: (
                    candidate
                    if isinstance(candidate, Callable)
                    else _normalise_value(key, candidate)
                ),
            )

        if not isinstance(value, Callable):
            return value

        protocol = _lambda_protocol(value, "interpolation")
        if protocol == _FUNCTION_PROTOCOL:
            return render_lambda_result(
                value(), key, context.default_ldel, context.default_rdel, ""
            )
        if explicit or isinstance(value, _LambdaDefinition):
            return ""
        return value

    # Run through the tokens
    for token in tokens:
        if len(token) == 3:
            tag, key, _ = token
        else:
            tag, key = token
        # Set the current scope
        current_scope = scopes[0]

        # If we're an end tag
        if tag == "end":
            # Pop out of the latest scope
            context.pop_scope()

        # If we're a set delimiter tag
        elif tag == "set delimiter":
            delimiters = key.split()
            current_ldel, current_rdel = delimiters[0], delimiters[-1]

        # If the current scope is falsy and not the only scope
        elif (
            not current_scope
            and not isinstance(current_scope, Callable)
            and len(scopes) != 1
        ):
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
            thing = interpolation_value(key)
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
            thing = interpolation_value(key)
            if not isinstance(thing, unicode_type):
                thing = unicode(str(thing), "utf-8")
            output += thing

        # If we're a section tag
        elif tag == "section":
            # Explicit lambdas take precedence over template data.
            scope = context.lambda_for(key)
            if scope is None:
                scope = context.lookup(
                    key,
                    warn=warn,
                    value_handler=lambda value: (
                        value
                        if isinstance(value, Callable)
                        else _normalise_value(key, value)
                    ),
                )

            # If the scope is a callable (as described in
            # https://mustache.github.io/mustache.5.html)
            if isinstance(scope, Callable):
                # Generate template text from tags
                raw_text = unicode("", "utf-8")
                compatibility_text = unicode("", "utf-8")
                tags = []
                section_start_ldel = current_ldel
                section_start_rdel = current_rdel
                section_ldel = section_start_ldel
                section_rdel = section_start_rdel
                nested_sections = 0
                for section_token in tokens:
                    if len(section_token) == 3:
                        tag_type, tag_key, raw_tag = section_token
                    else:
                        tag_type, tag_key = section_token
                        raw_tag = None

                    if tag_type in ("section", "inverted section") and tag_key == key:
                        nested_sections += 1
                    elif tag_type == "end" and tag_key == key:
                        if nested_sections == 0:
                            break
                        nested_sections -= 1

                    if raw_tag is not None:
                        raw_text += raw_tag
                    elif tag_type == "literal":
                        raw_text += tag_key
                    elif tag_type == "no escape":
                        raw_text += "%s&%s%s" % (
                            section_ldel,
                            tag_key,
                            section_rdel,
                        )
                    else:
                        raw_text += "%s%s%s%s" % (
                            section_ldel,
                            {
                                "comment": "!",
                                "section": "#",
                                "inverted section": "^",
                                "end": "/",
                                "partial": ">",
                                "set delimiter": "=",
                                "variable": "",
                            }[tag_type],
                            tag_key,
                            section_rdel,
                        )

                    # Keep Chevron's historical callback input and token cache
                    # unchanged. Raw-only literals and comments exist only to
                    # retain exact source for standard section lambdas.
                    if tag_type == "comment" or (
                        tag_type == "literal" and tag_key == ""
                    ):
                        continue

                    tags.append(section_token)
                    if tag_type == "literal":
                        compatibility_text += tag_key
                    elif tag_type == "no escape":
                        compatibility_text += "%s& %s %s" % (
                            def_ldel,
                            tag_key,
                            def_rdel,
                        )
                    else:
                        compatibility_text += "%s%s %s%s" % (
                            def_ldel,
                            {
                                "comment": "!",
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

                    if tag_type == "set delimiter":
                        delimiters = tag_key.split()
                        section_ldel, section_rdel = delimiters[0], delimiters[-1]

                current_ldel, current_rdel = section_ldel, section_rdel
                protocol = _lambda_protocol(scope, "section")

                if protocol == _SECTION_PROTOCOL:
                    rend = render_lambda_result(
                        scope(raw_text),
                        key,
                        section_start_ldel,
                        section_start_rdel,
                        padding,
                    )
                elif protocol == _COMPAT_PROTOCOL:
                    context.token_cache[compatibility_text] = tags
                    rend = scope(
                        compatibility_text,
                        lambda template, data=None: _render(
                            template,
                            context=(
                                context.with_prepended_scope(data) if data else context
                            ),
                            partials_path=partials_path,
                            partials_ext=partials_ext,
                            partials_dict=partials_dict,
                            padding=padding,
                            def_ldel=context.default_ldel,
                            def_rdel=context.default_rdel,
                            warn=warn,
                            use_token_cache=True,
                        ),
                    )
                else:
                    rend = ""

                if rend is None:
                    if warn:
                        context.warn_none_lambda_result(key)
                    rend = ""

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
                section_start_ldel = current_ldel
                section_start_rdel = current_rdel
                section_end_ldel = section_start_ldel
                section_end_rdel = section_start_rdel
                for section_token in tokens:
                    tag_type, tag_key = section_token[:2]
                    if tag_type == "section" and tag_key == key:
                        tags_with_same_key += 1
                    if tag_type == "end" and tag_key == key:
                        tags_with_same_key -= 1
                        if tags_with_same_key < 0:
                            break
                    tags.append(section_token)
                    if tag_type == "set delimiter":
                        delimiters = tag_key.split()
                        section_end_ldel, section_end_rdel = (
                            delimiters[0],
                            delimiters[-1],
                        )

                current_ldel, current_rdel = section_end_ldel, section_end_rdel

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
                        def_ldel=section_start_ldel,
                        def_rdel=section_start_rdel,
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
                scope = context.lookup(
                    key,
                    warn=warn,
                    value_handler=lambda value: _normalise_value(key, value),
                )
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
                def_ldel=context.default_ldel,
                def_rdel=context.default_rdel,
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
