"""Behaviour cases for the opt-in iterator inversion extension."""

from collections.abc import Iterator

import pytest

import chevron
from chevron import Extension
from section_cases import ITERATOR_DEFAULT_CASES, ITERATOR_EXTENSION_CASES


@pytest.fixture
def inverted_iterators_enabled() -> Iterator[None]:
    Extension.disable(Extension.ALL)
    Extension.enable(Extension.INVERTED_ITERATORS)
    try:
        yield
    finally:
        Extension.disable(Extension.ALL)


@pytest.fixture
def extensions_disabled() -> Iterator[None]:
    Extension.disable(Extension.ALL)
    try:
        yield
    finally:
        Extension.disable(Extension.ALL)


@pytest.mark.parametrize("case", ITERATOR_DEFAULT_CASES, ids=lambda case: case.name)
def test_sync_iterator_default_cases(extensions_disabled: None, case) -> None:
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


def test_empty_iterator_does_not_select_an_inverted_section_by_default(
    extensions_disabled: None,
) -> None:
    assert chevron.render("{{^items}}fallback{{/items}}", {"items": iter(())}) == ""


def test_extensions_can_be_enabled_and_disabled_as_a_group(
    extensions_disabled: None,
) -> None:
    Extension.disable(Extension.ALL)
    assert not Extension.is_enabled(Extension.INVERTED_ITERATORS)

    Extension.enable(Extension.INVERTED_ITERATORS)
    assert Extension.is_enabled(Extension.INVERTED_ITERATORS)

    Extension.disable(Extension.INVERTED_ITERATORS)
    assert not Extension.is_enabled(Extension.INVERTED_ITERATORS)

    Extension.enable(Extension.ALL)
    assert Extension.is_enabled(Extension.INVERTED_ITERATORS)

    Extension.disable(Extension.ALL)
    assert not Extension.is_enabled(Extension.INVERTED_ITERATORS)


@pytest.mark.parametrize("case", ITERATOR_EXTENSION_CASES, ids=lambda case: case.name)
def test_sync_iterator_extension_cases(inverted_iterators_enabled: None, case) -> None:
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
