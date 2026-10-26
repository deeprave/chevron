"""Chevron-owned async-only source-template behavior cases."""

from collections.abc import AsyncIterator

from rendering_cases import RenderCase


async def _mapping_items() -> AsyncIterator[dict[str, str]]:
    yield {"name": "first"}
    yield {"name": "second"}


async def _falsey_items() -> AsyncIterator[object]:
    yield 0
    yield False
    yield {}


async def _empty_items() -> AsyncIterator[None]:
    if False:
        yield None


ASYNC_ITERABLE_CASES = (
    RenderCase(
        name="async iterable renders mapping items in section",
        template="{{#items}}{{name}};{{/items}}",
        expected="first;second;",
        data_factory=lambda: {"items": _mapping_items()},
    ),
    RenderCase(
        name="async iterable falsey items use current context rendering",
        template="{{#items}}[{{.}}]{{/items}}",
        expected="[0][False][{}]",
        data_factory=lambda: {"items": _falsey_items()},
    ),
    RenderCase(
        name="empty async iterable renders section zero times",
        template="{{#items}}value{{/items}}",
        expected="",
        data_factory=lambda: {"items": _empty_items()},
    ),
)
