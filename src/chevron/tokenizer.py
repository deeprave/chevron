from dataclasses import dataclass


class ChevronError(SyntaxError):
    pass


@dataclass
class _TokenizationState:
    """Mutable diagnostics for one tokenisation operation."""

    current_line: int = 1
    last_tag_line: int | None = None


#
# Helper functions
#


def grab_literal(template, l_del, state):
    """Parse a literal from the template"""

    try:
        # Look for the next tag and move the template to it
        literal, template = template.split(l_del, 1)
        state.current_line += literal.count("\n")
        return (literal, template)

    # There are no more tags in the template?
    except ValueError:
        # Then the rest of the template is a literal
        return (template, "")


def l_sa_check(template, literal, is_standalone):
    """Do a preliminary check to see if a tag could be a standalone"""

    # If there is a newline, or the previous tag was a standalone
    if literal.find("\n") != -1 or is_standalone:
        padding = literal.split("\n")[-1]

        # If all the characters since the last newline are spaces
        if padding.isspace() or padding == "":
            # Then the next tag could be a standalone
            return True
        else:
            # Otherwise it can't be
            return False


def r_sa_check(template, tag_type, is_standalone):
    """Do a final checkto see if a tag could be a standalone"""

    # Check right side if we might be a standalone
    if is_standalone and tag_type not in ["variable", "no escape"]:
        on_newline = template.split("\n", 1)

        # If the stuff to the right of us are spaces we're a standalone
        if on_newline[0].isspace() or not on_newline[0]:
            return True
        else:
            return False

    # If we're a tag can't be a standalone
    else:
        return False


def parse_tag(template, l_del, r_del, state):
    """Parse a tag from a template"""
    tag_types = {
        "!": "comment",
        "#": "section",
        "^": "inverted section",
        "/": "end",
        ">": "partial",
        "=": "set delimiter?",
        "{": "no escape?",
        "&": "no escape",
    }

    # Get the tag
    try:
        tag, template = template.split(r_del, 1)
    except ValueError:
        raise ChevronError(f"unclosed tag at line {state.current_line}")

    # Find the type meaning of the first character
    tag_type = tag_types.get(tag[0], "variable")

    # If the type is not a variable
    if tag_type != "variable":
        # Then that first character is not needed
        tag = tag[1:]

    # If we might be a set delimiter tag
    if tag_type == "set delimiter?":
        # Double check to make sure we are
        if tag.endswith("="):
            tag_type = "set delimiter"
            # Remove the equal sign
            tag = tag[:-1]

        # Otherwise we should complain
        else:
            raise ChevronError(
                f"unclosed set delimiter tag\nat line {state.current_line}"
            )

    # If we might be a no html escape tag
    elif tag_type == "no escape?":
        # And we have a third curly brace
        # (And are using curly braces as delimiters)
        if l_del == "{{" and r_del == "}}" and template.startswith("}"):
            # Then we are a no html escape tag
            template = template[1:]
            tag_type = "no escape"

    # Strip the whitespace off the key and return
    return ((tag_type, tag.strip()), template)


#
# The main tokenizing function
#


def tokenize(
    template,
    def_ldel="{{",
    def_rdel="}}",
    include_raw=False,
    *,
    _state=None,
    _state_stack=None,
):
    """Tokenize a mustache template

    Tokenizes a mustache template in a generator fashion,
    using file-like objects. It also accepts a string containing
    the template.


    Arguments:

    template -- a file-like object, or a string of a mustache template

    def_ldel -- The default left delimiter
                ("{{" by default, as in spec compliant mustache)

    def_rdel -- The default right delimiter
                ("}}" by default, as in spec compliant mustache)

    include_raw -- Include the original source text for each token
                   as a third tuple item (defaults to False). The default
                   stream remains `(tag_type, tag_key)` for existing callers.


    Returns:

    A generator of mustache tags in the form of a tuple

    -- (tag_type, tag_key)

    When `include_raw=True`, each token is `(tag_type, tag_key, raw_source)`.
    That mode also retains source-only comment and standalone-whitespace tokens
    needed by the renderer's standard section-lambda protocol.

    Where tag_type is one of:
     * literal
     * section
     * inverted section
     * end
     * partial
     * no escape

    And tag_key is either the key or in the case of a literal tag,
    the literal itself.
    """

    state = _state if _state is not None else _TokenizationState()
    # If the template is a file-like object then read it
    try:
        template = template.read()
    except AttributeError:
        pass

    if _state_stack is not None:
        _state_stack.append(state)

    is_standalone = True
    open_sections = []
    l_del = def_ldel
    r_del = def_rdel

    def token(token_type, token_key, raw):
        return (token_type, token_key, raw)

    try:
        while template:
            literal, template = grab_literal(template, l_del, state)
            raw_literal = literal

            # If the template is completed
            if not template:
                # Then yield the literal and leave
                raw_token = token("literal", literal, literal)
                yield raw_token if include_raw else raw_token[:2]
                break

            # Do the first check to see if we could be a standalone
            is_standalone = l_sa_check(template, literal, is_standalone)

            # Parse the tag
            raw_tag = template
            tag, template = parse_tag(template, l_del, r_del, state)
            tag_type, tag_key = tag
            raw_tag = l_del + raw_tag[: len(raw_tag) - len(template)]

            # Special tag logic

            # If we are a set delimiter tag
            if tag_type == "set delimiter":
                # Then get and set the delimiters
                dels = tag_key.strip().split(" ")
                l_del, r_del = dels[0], dels[-1]

            # If we are a section tag
            elif tag_type in ["section", "inverted section"]:
                # Then open a new section
                open_sections.append(tag_key)
                state.last_tag_line = state.current_line

            # If we are an end tag
            elif tag_type == "end":
                # Then check to see if the last opened section
                # is the same as us
                try:
                    last_section = open_sections.pop()
                except IndexError:
                    raise ChevronError(
                        f'Trying to close tag "{tag_key}"\n'
                        "Looks like it was not opened.\n"
                        f"line {state.current_line + 1}"
                    )
                if tag_key != last_section:
                    # Otherwise we need to complain
                    raise ChevronError(
                        f'Trying to close tag "{tag_key}"\n'
                        f'last open tag is "{last_section}"\n'
                        f"line {state.current_line + 1}"
                    )

            # Do the second check to see if we're a standalone
            is_standalone = r_sa_check(template, tag_type, is_standalone)

            # Which if we are
            raw_standalone_suffix = ""
            if is_standalone:
                # Remove the stuff before the newline
                remaining_template = template
                template = template.split("\n", 1)[-1]
                raw_standalone_suffix = (
                    remaining_template[: -len(template)]
                    if template
                    else remaining_template
                )

                # Partials need to keep the spaces on their left
                if tag_type != "partial":
                    # But other tags don't
                    literal = literal.rstrip(" ")

            # Start yielding
            # Ignore literals that are empty
            if literal != "" or (include_raw and raw_literal != ""):
                raw_token = token("literal", literal, raw_literal)
                yield raw_token if include_raw else raw_token[:2]

            # Ignore comments and set delimiters
            if tag_type not in ["comment", "set delimiter?"]:
                raw_token = token(tag_type, tag_key, raw_tag)
                yield raw_token if include_raw else raw_token[:2]
            elif include_raw and tag_type == "comment":
                yield token(tag_type, tag_key, raw_tag)

            # Preserve source removed by standalone processing for standard section
            # lambdas without restoring it to rendered output.
            if include_raw and raw_standalone_suffix:
                yield token("literal", "", raw_standalone_suffix)

        if open_sections:
            raise ChevronError(
                "Unexpected EOF\n"
                f'the tag "{open_sections[-1]}" was never closed\n'
                f"was opened at line {state.last_tag_line}"
            )
    finally:
        if _state_stack is not None:
            if not _state_stack or _state_stack[-1] is not state:
                raise RuntimeError("tokenization state stack is unbalanced")
            _state_stack.pop()
