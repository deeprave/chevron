import pytest

import chevron


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


def test_unclosed_tag_reports_its_line() -> None:
    with pytest.raises(chevron.ChevronError, match="unclosed tag at line 3"):
        chevron.render("first line\nsecond line\n {{foo} bar")


def test_unopened_closing_tag_reports_its_name_and_line() -> None:
    with pytest.raises(
        chevron.ChevronError,
        match='Trying to close tag "closing_tag"\\nLooks like it was not opened.\\nline 2',
    ):
        chevron.render("oops, no opening tag {{/closing_tag}}")
