"""Behavioural tests for Chevron's opt-in conditional sections."""

from collections.abc import Callable, Iterator
import logging

import pytest

import chevron
from chevron import Extension
from chevron.tokenizer import tokenize
from section_cases import CONDITIONAL_SECTION_CASES, ConditionalCallable


class _SizedConditionalItems(Iterator[str]):
    def __init__(self) -> None:
        self.next_calls = 0

    def __len__(self) -> int:
        return 1

    def __next__(self) -> str:
        self.next_calls += 1
        raise StopIteration


def test_conditional_section_is_tokenized_when_its_extension_is_enabled(
    enable_extensions: Callable[..., None],
) -> None:
    enable_extensions(Extension.CONDITIONAL_SECTIONS)
    assert list(tokenize("{{?enabled}}shown{{/enabled}}")) == [
        ("conditional section", "enabled"),
        ("literal", "shown"),
        ("end", "enabled"),
    ]


def test_disabled_conditional_prefix_is_an_ordinary_variable() -> None:
    assert chevron.render("{{?enabled}}", {"?enabled": "shown"}) == "shown"


def test_disabled_conditional_section_warns_before_structural_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("conditional-section-test")
    with pytest.raises(chevron.ChevronError, match='close tag "enabled"'):
        chevron.render(
            "{{?enabled}}shown{{/enabled}}",
            {"enabled": True},
            logger=logger,
        )

    assert any(
        record.name == logger.name
        and "Extension.CONDITIONAL_SECTIONS" in record.message
        for record in caplog.records
    )


@pytest.mark.parametrize("case", CONDITIONAL_SECTION_CASES, ids=lambda case: case.name)
def test_conditional_section_cases(
    enable_extensions: Callable[..., None], case
) -> None:
    enable_extensions(Extension.CONDITIONAL_SECTIONS)

    assert (
        chevron.render(
            case.template,
            case.render_data(),
            partials_dict=case.partials,
            scopes=case.scopes,
            def_ldel=case.initial_delimiters[0],
            def_rdel=case.initial_delimiters[1],
        )
        == case.expected
    )


def test_conditional_section_does_not_invoke_a_callable(
    enable_extensions: Callable[..., None],
) -> None:
    enable_extensions(Extension.CONDITIONAL_SECTIONS)
    callback = ConditionalCallable()

    assert (
        chevron.render("{{?callback}}shown{{/callback}}", {"callback": callback})
        == "shown"
    )
    assert callback.calls == 0


def test_conditional_section_does_not_probe_a_sized_iterator(
    enable_extensions: Callable[..., None],
) -> None:
    enable_extensions(Extension.CONDITIONAL_SECTIONS)
    items = _SizedConditionalItems()

    assert chevron.render("{{?items}}shown{{/items}}", {"items": items}) == "shown"
    assert items.next_calls == 0
