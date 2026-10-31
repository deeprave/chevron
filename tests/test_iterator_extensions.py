"""Behaviour cases for the opt-in iterator inversion extension."""

from collections.abc import Callable

import pytest

import chevron
from chevron import Extension
from section_cases import (
    ITERATION_METADATA_CASES,
    ITERATOR_DEFAULT_CASES,
    ITERATOR_EXTENSION_CASES,
    _LengthTrackingItems,
)


@pytest.mark.parametrize("case", ITERATOR_DEFAULT_CASES, ids=lambda case: case.name)
def test_sync_iterator_default_cases(case) -> None:
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


def test_empty_iterator_does_not_select_an_inverted_section_by_default() -> None:
    assert chevron.render("{{^items}}fallback{{/items}}", {"items": iter(())}) == ""


def test_iteration_metadata_names_are_unresolved_by_default() -> None:
    assert (
        chevron.render(
            "{{#items}}[{{.index}}/{{.length}}]{{/items}}", {"items": ["one"]}
        )
        == "[/]"
    )


def test_extensions_can_be_enabled_as_a_group(
    enable_extensions: Callable[..., None],
) -> None:
    assert not Extension.is_enabled(Extension.ENHANCED_ITERATORS)

    enable_extensions(Extension.ALL)
    assert Extension.is_enabled(Extension.ENHANCED_ITERATORS)


def test_extensions_are_immutable_after_configuration(
    enable_extensions: Callable[..., None],
) -> None:
    enable_extensions(Extension.ENHANCED_ITERATORS)

    with pytest.raises(RuntimeError, match="already been configured"):
        Extension.enable(Extension.ALL)


@pytest.mark.parametrize(
    "case",
    ITERATOR_EXTENSION_CASES + ITERATION_METADATA_CASES,
    ids=lambda case: case.name,
)
def test_sync_iterator_extension_cases(
    enable_extensions: Callable[..., None], case
) -> None:
    enable_extensions(Extension.ENHANCED_ITERATORS)
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


def test_index_metadata_does_not_request_an_unused_length(
    enable_extensions: Callable[..., None],
) -> None:
    enable_extensions(Extension.ENHANCED_ITERATORS)
    items = _LengthTrackingItems()

    assert (
        chevron.render("{{#items}}{{.index}}:{{.}};{{/items}}", {"items": items})
        == "0:one;1:two;"
    )
    assert items.length_calls == 0


def test_oversized_numeric_metadata_name_is_unavailable(
    enable_extensions: Callable[..., None],
) -> None:
    enable_extensions(Extension.ENHANCED_ITERATORS)
    selector = "." + "1" * 4_301
    template = "{{#items}}[{{" + selector + "}}]{{/items}}"

    assert (
        chevron.render(
            template,
            {"": {selector[1:]: "leaked"}, "items": ["one"]},
        )
        == "[]"
    )
