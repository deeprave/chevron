"""Chevron-owned public behavior cases for ordinary section rendering."""

from collections.abc import Iterator

from rendering_cases import RenderCase


def _empty_items() -> Iterator[str]:
    return iter(())


def _many_items() -> Iterator[str]:
    return iter(("first", "second", "third"))


class _ResettingItems(Iterator[str]):
    def __iter__(self) -> "_ResettingItems":
        self.index = 0
        return self

    def __next__(self) -> str:
        if self.index == 2:
            raise StopIteration
        self.index += 1
        return str(self.index)


class _FreshIteratorScope:
    def __init__(self) -> None:
        self.cursor = iter(("first", "second", "third"))

    def __getitem__(self, key: str) -> object:
        if key == "items":
            return (item for item in self.cursor)
        if key == "wrap":
            return True
        raise KeyError(key)


class _CallableIterator(Iterator[str]):
    def __init__(self) -> None:
        self.items = iter(("ignored",))

    def __next__(self) -> str:
        return next(self.items)

    def __call__(self, _body: str, _render: object) -> str:
        return "called"


class _FalseyIterator(Iterator[str]):
    def __iter__(self) -> "_FalseyIterator":
        return self

    def __bool__(self) -> bool:
        return False

    def __next__(self) -> str:
        return "unreachable"


SECTION_CASES = (
    RenderCase(
        name="inverted sections evaluate mixed sequence items independently",
        template="{{#object}}{{^child}}{{.}}{{/child}}{{/object}}",
        data={"object": ["foo", "bar", {"child": True}, "baz"]},
        expected="foobarbaz",
    ),
    RenderCase(
        name="nested sections with same name restore outer scope",
        template="A{{#x}}B{{#x}}{{.}}{{/x}}C{{/x}}D",
        data={"x": ["z", "x"]},
        expected="ABzxCBzxCD",
    ),
    RenderCase(
        name="iterable section collects nested inverted sections with same name",
        template="{{#items}}{{^items}}empty{{/items}}{{name}};{{/items}}",
        data={"items": [{"name": "first"}, {"name": "second"}]},
        expected="first;second;",
    ),
)


ITERATOR_DEFAULT_CASES = (
    RenderCase(
        name="disabled iterator extension leaves a non-empty iterator unconsumed",
        template="{{^items}}fallback{{/items}}{{#items}}[{{.}}]{{/items}}",
        expected="[first][second][third]",
        data_factory=lambda: {"items": _many_items()},
    ),
    RenderCase(
        name="disabled iterator extension permits repeatable iterator restart",
        template="{{#items}}{{.}}{{/items}}/{{#items}}{{.}}{{/items}}",
        expected="12/12",
        data_factory=lambda: {"items": _ResettingItems()},
    ),
)


ITERATOR_EXTENSION_CASES = (
    RenderCase(
        name="empty iterator selects inverted section",
        template="{{^items}}fallback{{/items}}{{#items}}ordinary{{/items}}",
        expected="fallback",
        data_factory=lambda: {"items": _empty_items()},
    ),
    RenderCase(
        name="callable iterator keeps lambda precedence in an inverted section",
        template="{{^items}}fallback{{/items}}|{{#items}}body{{/items}}",
        expected="|called",
        data_factory=lambda: {"items": _CallableIterator()},
    ),
    RenderCase(
        name="falsey iterator selects an inverted section without iteration",
        template="{{^items}}fallback{{/items}}{{#items}}ordinary{{/items}}",
        expected="fallback",
        data_factory=lambda: {"items": _FalseyIterator()},
    ),
    RenderCase(
        name="exhausted empty iterator selects inverted section",
        template="{{#items}}ordinary{{/items}}{{^items}}fallback{{/items}}",
        expected="fallback",
        data_factory=lambda: {"items": _empty_items()},
    ),
    RenderCase(
        name="iterator peek preserves all ordinary section items",
        template="{{^items}}fallback{{/items}}{{#items}}[{{.}}]{{/items}}",
        expected="[first][second][third]",
        data_factory=lambda: {"items": _many_items()},
    ),
    RenderCase(
        name="exhausted non-empty iterator does not select inverted section",
        template="{{#items}}[{{.}}]{{/items}}{{^items}}fallback{{/items}}",
        expected="[first][second][third]",
        data_factory=lambda: {"items": _many_items()},
    ),
    RenderCase(
        name="iterator sections keep one canonical cursor",
        template="{{#items}}{{.}}{{/items}}/{{#items}}{{.}}{{/items}}",
        expected="12/",
        data_factory=lambda: {"items": _ResettingItems()},
    ),
    RenderCase(
        name="fresh iterator lookup retains pending inverted peek",
        template="{{^items}}fallback{{/items}}{{#items}}[{{.}}]{{/items}}",
        expected="[first][second][third]",
        data_factory=_FreshIteratorScope,
    ),
    RenderCase(
        name="repeated inverted checks retain the initial iterator peek",
        template="{{^items}}first fallback{{/items}}{{^items}}second fallback{{/items}}{{#items}}[{{.}}]{{/items}}",
        expected="[first][second][third]",
        data_factory=_FreshIteratorScope,
    ),
    RenderCase(
        name="nested inverted section retains the outer iterator item",
        template="{{#items}}{{^items}}X{{/items}}[{{.}}]{{/items}}",
        expected="[a][b][c]",
        data_factory=lambda: {"items": iter(("a", "b", "c"))},
    ),
    RenderCase(
        name="child ordinary section renders the outer iterator peek",
        template="{{^it}}E{{/it}}[{{#c}}{{#it}}{{.}},{{/it}}{{/c}}]",
        expected="[1,2,3,]",
        data_factory=lambda: {"c": {"name": "child"}, "it": iter((1, 2, 3))},
    ),
    RenderCase(
        name="child ordinary section keeps a shadowed iterator",
        template="{{^it}}E{{/it}}[{{#c}}{{#it}}{{.}},{{/it}}{{/c}}]",
        expected="[9,]",
        data_factory=lambda: {"c": {"it": iter((9,))}, "it": iter((1, 2, 3))},
    ),
    RenderCase(
        name="nested inverted iterator check retains an outer ordinary section item",
        template="{{#wrap}}{{^items}}fallback{{/items}}{{/wrap}}{{#items}}[{{.}}]{{/items}}",
        expected="[first][second][third]",
        data_factory=lambda: {"wrap": True, "items": _many_items()},
    ),
    RenderCase(
        name="iterator peek survives a partial render context",
        template="{{^items}}fallback{{/items}}{{>rows}}",
        expected="[first][second][third]",
        data_factory=lambda: {"items": _many_items()},
        partials={"rows": "{{#items}}[{{.}}]{{/items}}"},
    ),
    RenderCase(
        name="fresh iterator wrapper peek survives a partial render context",
        template="{{^items}}fallback{{/items}}{{>rows}}",
        expected="[first][second][third]",
        data_factory=_FreshIteratorScope,
        partials={"rows": "{{#items}}[{{.}}]{{/items}}"},
    ),
    RenderCase(
        name="fresh iterator wrapper peek survives an unshadowed child context",
        template="{{^items}}fallback{{/items}}{{#wrap}}{{#items}}[{{.}}]{{/items}}{{/wrap}}",
        expected="[first][second][third]",
        data_factory=_FreshIteratorScope,
    ),
    RenderCase(
        name="exhausted non-empty iterator retains its inverted result",
        template="{{#items}}[{{.}}]{{/items}}|{{#items}}[{{.}}]{{/items}}|{{^items}}fallback{{/items}}",
        expected="[first][second][third]||",
        data_factory=lambda: {"items": _many_items()},
    ),
)
