from collections.abc import Sequence
import sys
from typing import overload

import pytest

import chevron


def test_deep_iterable_sections_do_not_use_the_python_call_stack() -> None:
    depth = sys.getrecursionlimit() + 10
    template = "{{#items}}" * depth + "complete" + "{{/items}}" * depth
    data = {"items": [{"items": []}]}
    current = data["items"][0]
    for _ in range(depth - 1):
        next_item = {"items": []}
        current["items"] = [next_item]
        current = next_item

    assert chevron.render(template, data) == "complete"


def test_section_iterator_error_has_no_stop_iteration_context() -> None:
    class Items:
        def __init__(self) -> None:
            self.first = True

        def __iter__(self) -> "Items":
            return self

        def __next__(self) -> str:
            if self.first:
                self.first = False
                return "item"
            raise ValueError("iterator failed")

    with pytest.raises(ValueError, match="iterator failed") as error:
        chevron.render("{{#items}}{{/items}}", {"items": Items()})

    assert error.value.__context__ is None


def test_lambda_result_sections_do_not_mutate_the_caller_scopes_container() -> None:
    scopes: list[dict[str, object]] = [{"item": {"value": "1"}}]

    @chevron.func
    def outer() -> str:
        return "{{#item}}{{inner}}{{/item}}"

    @chevron.func
    def inner() -> str:
        return str(len(scopes))

    scopes[0].update(outer=outer, inner=inner)

    assert chevron.render("{{outer}}", scopes=scopes) == "1"
    assert len(scopes) == 1


@pytest.mark.parametrize("scopes", ["text", b"bytes", {"name": "value"}])
def test_scopes_reject_non_sequence_containers(scopes: object) -> None:
    with pytest.raises(TypeError, match="scopes must be a sequence"):
        chevron.render("{{name}}", scopes=scopes)  # ty: ignore[invalid-argument-type]


def test_numeric_lookup_propagates_sequence_index_errors() -> None:
    class BrokenSequence(Sequence):
        @overload
        def __getitem__(self, index: int) -> object: ...

        @overload
        def __getitem__(self, index: slice) -> Sequence[object]: ...

        def __getitem__(self, index: int | slice) -> object | Sequence[object]:
            if isinstance(index, str):
                raise TypeError("string lookup is unsupported")
            raise TypeError("integer lookup failed")

        def __len__(self) -> int:
            return 1

    with pytest.raises(TypeError, match="integer lookup failed"):
        chevron.render("{{0}}", BrokenSequence())


def test_sync_render_rejects_async_iterable_sections() -> None:
    async def values():
        yield "value"

    with pytest.raises(TypeError, match="use chevron.async_render"):
        chevron.render("{{#values}}{{.}}{{/values}}", {"values": values()})


def test_sync_render_rejects_async_iterable_inverted_sections() -> None:
    async def values():
        yield "value"

    with pytest.raises(TypeError, match="use chevron.async_render"):
        chevron.render("{{^values}}empty{{/values}}", {"values": values()})
