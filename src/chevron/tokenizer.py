from collections.abc import Generator
from dataclasses import dataclass
from typing import TypeAlias

Token: TypeAlias = tuple[str, str] | tuple[str, str, str]
RawToken: TypeAlias = tuple[str, str, str]


class ChevronError(SyntaxError):
    pass


@dataclass
class _TokenizationState:
    """Mutable diagnostics for one tokenisation operation."""

    current_line: int = 1
    last_tag_line: int | None = None


def _line_break_count(text: str) -> int:
    """Count CRLF, LF, and CR line endings as one line each."""
    return text.count("\r") + text.count("\n") - text.count("\r\n")


def _split_first_line(text: str) -> tuple[str, str]:
    """Return text before its first line ending and the remaining suffix."""
    carriage_return = text.find("\r")
    line_feed = text.find("\n")
    if carriage_return < 0:
        line_break = line_feed
    elif line_feed < 0:
        line_break = carriage_return
    else:
        line_break = min(carriage_return, line_feed)
    return (text, "") if line_break < 0 else (text[:line_break], text[line_break:])


#
# Helper functions
#


def grab_literal(
    template: str, l_del: str, state: _TokenizationState
) -> tuple[str, str]:
    """Parse a literal from the template"""

    try:
        # Look for the next tag and move the template to it
        literal, template = template.split(l_del, 1)
        state.current_line += _line_break_count(literal)
        return (literal, template)

    # There are no more tags in the template?
    except ValueError:
        # Then the rest of the template is a literal
        return (template, "")


def l_sa_check(template: str, literal: str, is_standalone: bool | None) -> bool | None:
    """Do a preliminary check to see if a tag could be a standalone"""

    # If there is a newline, or the previous tag was a standalone
    line_break = max(literal.rfind("\n"), literal.rfind("\r"))
    if line_break >= 0 or is_standalone:
        padding = literal[line_break + 1 :]

        # If all the characters since the last newline are spaces
        if padding.isspace() or padding == "":
            # Then the next tag could be a standalone
            return True
        else:
            # Otherwise it can't be
            return False


def r_sa_check(template: str, tag_type: str, is_standalone: bool | None) -> bool:
    """Do a final checkto see if a tag could be a standalone"""

    # Check right side if we might be a standalone
    if is_standalone and tag_type not in ["variable", "no escape"]:
        on_newline, _ = _split_first_line(template)

        # If the stuff to the right of us are spaces we're a standalone
        if on_newline.isspace() or not on_newline:
            return True
        else:
            return False

    # If we're a tag can't be a standalone
    else:
        return False


def parse_tag(
    template: str, l_del: str, r_del: str, state: _TokenizationState
) -> tuple[tuple[str, str], str]:
    """Parse a tag from a template"""
    tag_types = {
        "!": "comment",
        "#": "section",
        "^": "inverted section",
        "/": "end",
        ">": "partial",
        "<": "parent",
        "$": "block",
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
    template: str,
    def_ldel: str = "{{",
    def_rdel: str = "}}",
    include_raw: bool = False,
) -> Generator[Token, None, None]:
    """Tokenize a mustache template

    Tokenizes template text in a generator fashion without performing I/O.
    The renderer reads file-like inputs before calling this function.


    Arguments:

    template -- a string containing a mustache template

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
     * parent
     * block
     * no escape
     * comment
     * set delimiter

    And tag_key is either the key or in the case of a literal tag,
    the literal itself.

    Raises:

    TypeError -- If template is not source text. File-like templates are
                 supported by chevron.render(), which reads them before
                 tokenization.
    """

    if not isinstance(template, str):
        raise TypeError(
            "tokenize() requires template text; use chevron.render() for file-like input"
        )

    state = _TokenizationState()

    is_standalone = True
    open_sections: list[str] = []
    l_del = def_ldel
    r_del = def_rdel

    def token(token_type: str, token_key: str, raw: str) -> RawToken:
        return (token_type, token_key, raw)

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
        elif tag_type in ["section", "inverted section", "parent", "block"]:
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
                    f"line {state.current_line}"
                )
            if tag_key != last_section:
                # Otherwise we need to complain
                raise ChevronError(
                    f'Trying to close tag "{tag_key}"\n'
                    f'last open tag is "{last_section}"\n'
                    f"line {state.current_line}"
                )

        # Do the second check to see if we're a standalone
        is_standalone = r_sa_check(template, tag_type, is_standalone)

        # Which if we are
        raw_standalone_suffix = ""
        if is_standalone:
            # Remove the stuff before the newline
            remaining_template = template
            _, line_suffix = _split_first_line(template)
            if line_suffix.startswith("\r\n"):
                template = line_suffix[2:]
            elif line_suffix:
                template = line_suffix[1:]
            raw_standalone_suffix = (
                remaining_template[: -len(template)] if template else remaining_template
            )
            state.current_line += _line_break_count(raw_standalone_suffix)

            # Partials need to keep the spaces on their left
            if tag_type not in ("partial", "parent"):
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
