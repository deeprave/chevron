from html import escape

from hypothesis import given, settings, strategies as st

import chevron
from chevron.tokenizer import tokenize


LITERAL_ALPHABET = st.characters(exclude_characters="{}")
LITERAL_TEXT = st.text(alphabet=LITERAL_ALPHABET, max_size=80)
NONEMPTY_LITERAL_TEXT = st.text(alphabet=LITERAL_ALPHABET, min_size=1, max_size=80)
INTERPOLATED_TEXT = st.text(max_size=80)


@settings(max_examples=100, deadline=None)
@given(LITERAL_TEXT)
def test_literal_text_renders_unchanged(template: str) -> None:
    assert chevron.render(template) == template


@settings(max_examples=100, deadline=None)
@given(INTERPOLATED_TEXT)
def test_interpolation_preserves_raw_text_and_escapes_html_sensitive_characters(
    value: str,
) -> None:
    assert chevron.render("{{{value}}}", {"value": value}) == value
    assert chevron.render("{{value}}", {"value": value}) == escape(
        value, quote=False
    ).replace('"', "&quot;")


@settings(max_examples=100, deadline=None)
@given(NONEMPTY_LITERAL_TEXT)
def test_literal_tokenisation_preserves_the_complete_source(template: str) -> None:
    assert list(tokenize(template)) == [("literal", template)]
