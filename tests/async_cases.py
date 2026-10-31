"""Chevron-owned async-only source-template behavior cases."""

from collections.abc import AsyncIterable, AsyncIterator

from rendering_cases import LambdaRenderCase, RenderCase


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


async def _many_items() -> AsyncIterator[str]:
    yield "first"
    yield "second"
    yield "third"


async def _nested_items() -> AsyncIterator[str]:
    yield "a"
    yield "b"
    yield "c"


async def _numbered_items() -> AsyncIterator[int]:
    yield 1
    yield 2
    yield 3


async def _shadowed_item() -> AsyncIterator[int]:
    yield 9


class _RepeatableItems(AsyncIterable[str]):
    def __aiter__(self) -> AsyncIterator[str]:
        return self._items()

    async def _items(self) -> AsyncIterator[str]:
        yield "item"


class _WrappedSinglePassItems(AsyncIterable[str]):
    def __init__(self) -> None:
        self.items = self._items()

    def __aiter__(self) -> AsyncIterator[str]:
        return self.items

    async def _items(self) -> AsyncIterator[str]:
        yield "first"
        yield "second"
        yield "third"


class _AsyncIteratorWrapper(AsyncIterable[str]):
    def __init__(self, items: AsyncIterator[str]) -> None:
        self.items = items

    def __aiter__(self) -> AsyncIterator[str]:
        return self.items


class _CallableAsyncItems(AsyncIterable[str]):
    def __aiter__(self) -> AsyncIterator[str]:
        return self.items()

    async def items(self) -> AsyncIterator[str]:
        yield "ignored"

    def __call__(self, _body: str, _render: object) -> str:
        return "called"


class _FalseyAsyncIterable(AsyncIterable[str]):
    def __bool__(self) -> bool:
        return False

    def __aiter__(self) -> AsyncIterator[str]:
        return self.items()

    async def items(self) -> AsyncIterator[str]:
        yield "unreachable"


class _FreshAsyncIteratorScope:
    def __init__(self) -> None:
        self.cursor = self._items()

    def __getitem__(self, key: str) -> object:
        if key == "items":
            return _AsyncIteratorWrapper(self.cursor)
        if key == "wrap":
            return True
        raise KeyError(key)

    async def _items(self) -> AsyncIterator[str]:
        yield "first"
        yield "second"
        yield "third"


ASYNC_ITERABLE_CASES = (
    RenderCase(
        name="callable async iterable keeps lambda precedence in an inverted section",
        template="{{^items}}fallback{{/items}}|{{#items}}body{{/items}}",
        expected="|called",
        data_factory=lambda: {"items": _CallableAsyncItems()},
    ),
    LambdaRenderCase(
        name="configured callable async iterable keeps lambda precedence in an inverted section",
        template="{{^items}}fallback{{/items}}|{{#items}}body{{/items}}",
        expected="|called",
        lambdas_factory=lambda: {"items": _CallableAsyncItems()},
    ),
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


ASYNC_ITERATOR_DEFAULT_CASES = (
    RenderCase(
        name="disabled async iterator extension leaves a non-empty iterable unconsumed",
        template="{{^items}}fallback{{/items}}{{#items}}[{{.}}]{{/items}}",
        expected="[first][second][third]",
        data_factory=lambda: {"items": _many_items()},
    ),
    RenderCase(
        name="disabled async iterator extension permits repeatable iterable restart",
        template="{{#items}}{{.}}{{/items}}/{{#items}}{{.}}{{/items}}",
        expected="item/item",
        data_factory=lambda: {"items": _RepeatableItems()},
    ),
)


ASYNC_ITERATOR_EXTENSION_CASES = (
    RenderCase(
        name="empty async iterator selects inverted section",
        template="{{^items}}fallback{{/items}}{{#items}}ordinary{{/items}}",
        expected="fallback",
        data_factory=lambda: {"items": _empty_items()},
    ),
    RenderCase(
        name="falsey async iterable selects an inverted section without iteration",
        template="{{^items}}fallback{{/items}}{{#items}}ordinary{{/items}}",
        expected="fallback",
        data_factory=lambda: {"items": _FalseyAsyncIterable()},
    ),
    RenderCase(
        name="exhausted empty async iterator selects inverted section",
        template="{{#items}}ordinary{{/items}}{{^items}}fallback{{/items}}",
        expected="fallback",
        data_factory=lambda: {"items": _empty_items()},
    ),
    RenderCase(
        name="async iterator peek preserves all ordinary section items",
        template="{{^items}}fallback{{/items}}{{#items}}[{{.}}]{{/items}}",
        expected="[first][second][third]",
        data_factory=lambda: {"items": _many_items()},
    ),
    RenderCase(
        name="exhausted non-empty async iterator does not select inverted section",
        template="{{#items}}[{{.}}]{{/items}}{{^items}}fallback{{/items}}",
        expected="[first][second][third]",
        data_factory=lambda: {"items": _many_items()},
    ),
    RenderCase(
        name="async iterable sections keep one canonical cursor",
        template="{{#items}}{{.}}{{/items}}/{{#items}}{{.}}{{/items}}",
        expected="item/",
        data_factory=lambda: {"items": _RepeatableItems()},
    ),
    RenderCase(
        name="repeatable async iterable preserves later ordinary section",
        template="{{^items}}fallback{{/items}}{{#items}}[{{.}}]{{/items}}",
        expected="[item]",
        data_factory=lambda: {"items": _RepeatableItems()},
    ),
    RenderCase(
        name="wrapped single-pass async iterable retains pending inverted peek",
        template="{{^items}}fallback{{/items}}{{#items}}[{{.}}]{{/items}}",
        expected="[first][second][third]",
        data_factory=lambda: {"items": _WrappedSinglePassItems()},
    ),
    RenderCase(
        name="repeated inverted checks retain a fresh async iterator wrapper peek",
        template="{{^items}}first fallback{{/items}}{{^items}}second fallback{{/items}}{{#items}}[{{.}}]{{/items}}",
        expected="[first][second][third]",
        data_factory=_FreshAsyncIteratorScope,
    ),
    RenderCase(
        name="nested inverted section retains the outer async iterator item",
        template="{{#items}}{{^items}}X{{/items}}[{{.}}]{{/items}}",
        expected="[a][b][c]",
        data_factory=lambda: {"items": _nested_items()},
    ),
    RenderCase(
        name="child ordinary section renders the outer async iterator peek",
        template="{{^it}}E{{/it}}[{{#c}}{{#it}}{{.}},{{/it}}{{/c}}]",
        expected="[1,2,3,]",
        data_factory=lambda: {"c": {"name": "child"}, "it": _numbered_items()},
    ),
    RenderCase(
        name="child ordinary section keeps a shadowed async iterator",
        template="{{^it}}E{{/it}}[{{#c}}{{#it}}{{.}},{{/it}}{{/c}}]",
        expected="[9,]",
        data_factory=lambda: {
            "c": {"it": _shadowed_item()},
            "it": _numbered_items(),
        },
    ),
    RenderCase(
        name="nested inverted async iterator check retains an outer ordinary section item",
        template="{{#wrap}}{{^items}}fallback{{/items}}{{/wrap}}{{#items}}[{{.}}]{{/items}}",
        expected="[first][second][third]",
        data_factory=lambda: {"wrap": True, "items": _many_items()},
    ),
    RenderCase(
        name="async iterator peek survives a partial render context",
        template="{{^items}}fallback{{/items}}{{>rows}}",
        expected="[first][second][third]",
        data_factory=lambda: {"items": _many_items()},
        partials={"rows": "{{#items}}[{{.}}]{{/items}}"},
    ),
    RenderCase(
        name="fresh async iterator wrapper peek survives a partial render context",
        template="{{^items}}fallback{{/items}}{{>rows}}",
        expected="[first][second][third]",
        data_factory=_FreshAsyncIteratorScope,
        partials={"rows": "{{#items}}[{{.}}]{{/items}}"},
    ),
    RenderCase(
        name="fresh async iterator wrapper peek survives an unshadowed child context",
        template="{{^items}}fallback{{/items}}{{#wrap}}{{#items}}[{{.}}]{{/items}}{{/wrap}}",
        expected="[first][second][third]",
        data_factory=_FreshAsyncIteratorScope,
    ),
    RenderCase(
        name="exhausted non-empty async iterator retains its inverted result",
        template="{{#items}}[{{.}}]{{/items}}|{{#items}}[{{.}}]{{/items}}|{{^items}}fallback{{/items}}",
        expected="[first][second][third]||",
        data_factory=lambda: {"items": _many_items()},
    ),
)
