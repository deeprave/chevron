import pytest

import chevron
from token_cases import MALFORMED_RESERVED_TAG_TEMPLATES, TOKEN_VALIDATION_CASES


@pytest.mark.parametrize(
    "template",
    [
        "{{#section}}oops{{/wrong_section}}",
        "{{#section}}end of file",
        "{{foo} bar",
        "{{= bad!}}",
    ],
    ids=[
        "mismatched-section",
        "unclosed-section",
        "unclosed-tag",
        "invalid-delimiter-change",
    ],
)
def test_malformed_templates_raise_chevron_syntax_errors(template: str) -> None:
    with pytest.raises(chevron.ChevronError) as error:
        chevron.render(template)

    assert isinstance(error.value, SyntaxError)


@pytest.mark.parametrize("template", MALFORMED_RESERVED_TAG_TEMPLATES)
def test_unclosed_reserved_inheritance_tags_raise_chevron_syntax_errors(
    template: str,
) -> None:
    with pytest.raises(chevron.ChevronError):
        chevron.render(template)


def test_unclosed_tag_reports_its_line() -> None:
    with pytest.raises(chevron.ChevronError, match="unclosed tag at line 3"):
        chevron.render("first line\nsecond line\n {{foo} bar")


@pytest.mark.parametrize(
    ("template", "line"),
    [
        ("oops, no opening tag {{/closing_tag}}", 1),
        ("first line\n{{/closing_tag}}", 2),
    ],
    ids=["first-line", "second-line"],
)
def test_unopened_closing_tag_reports_its_name_and_line(
    template: str, line: int
) -> None:
    with pytest.raises(
        chevron.ChevronError,
        match=(
            'Trying to close tag "closing_tag"\\nLooks like it was not opened.\\n'
            f"line {line}"
        ),
    ):
        chevron.render(template)


def test_mismatched_closing_tag_reports_its_actual_line() -> None:
    with pytest.raises(
        chevron.ChevronError,
        match=(
            'Trying to close tag "wrong_section"\\nlast open tag is "section"\\nline 3'
        ),
    ):
        chevron.render("first line\n{{#section}}\n{{/wrong_section}}")


@pytest.mark.parametrize(
    ("_name", "tokens", "message"),
    TOKEN_VALIDATION_CASES,
    ids=[case[0] for case in TOKEN_VALIDATION_CASES],
)
def test_direct_token_sequences_validate_structure(
    _name: str, tokens: tuple[tuple[str, str], ...], message: str
) -> None:
    with pytest.raises(chevron.ChevronError, match=message):
        chevron.render(tokens)
