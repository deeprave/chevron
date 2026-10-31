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


class _SizedItems(Iterator[str]):
    """A single-pass source that supplies a stable initial size."""

    def __init__(self) -> None:
        self.items = ("one", "two", "three")
        self.index = 0

    def __len__(self) -> int:
        return len(self.items)

    def __next__(self) -> str:
        if self.index == len(self.items):
            raise StopIteration
        item = self.items[self.index]
        self.index += 1
        return item

    def __getitem__(self, index: int) -> str:
        return self.items[index]


class _LengthTrackingItems(Iterator[str]):
    """A truthy sized iterator that records whether its length was requested."""

    def __init__(self) -> None:
        self.items = iter(("one", "two"))
        self.length_calls = 0

    def __bool__(self) -> bool:
        return True

    def __len__(self) -> int:
        self.length_calls += 1
        return 2

    def __next__(self) -> str:
        return next(self.items)


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


ITERATION_METADATA_CASES = (
    RenderCase(
        name="iteration metadata formats a separator without a trailing comma",
        template="{{#values}}{{#.first}}- {{/.first}}{{.}}{{^.last}}, {{/.last}}{{/values}}",
        expected="- one, two, three",
        data={"values": ["one", "two", "three"]},
    ),
    RenderCase(
        name="iteration metadata preserves a streaming iterator while determining last",
        template="{{#values}}{{#.first}}- {{/.first}}{{.}}{{^.last}}, {{/.last}}{{/values}}",
        expected="- first, second, third",
        data_factory=lambda: {"values": _many_items()},
    ),
    RenderCase(
        name="iteration metadata exposes index ordinal and length",
        template="{{#values}}{{.index}}/{{.ordinal}}/{{.length}}:{{.}};{{/values}}",
        expected="0/1/3:one;1/2/3:two;2/3/3:three;",
        data={"values": ["one", "two", "three"]},
    ),
    RenderCase(
        name="iteration metadata exposes length for a sized iterator",
        template="{{#values}}{{.length}}:{{.}};{{/values}}",
        expected="3:one;3:two;3:three;",
        data_factory=lambda: {"values": _SizedItems()},
    ),
    RenderCase(
        name="iteration metadata keeps an unsized iterator length unavailable",
        template="{{#values}}[{{.length}}{{^.length}}none{{/.length}}:{{.}}]{{/values}}",
        expected="[none:first][none:second][none:third]",
        data_factory=lambda: {"length": "outer", "values": _many_items()},
    ),
    RenderCase(
        name="iteration metadata resolves numeric names from an indexable source",
        template="{{#values}}{{.index}}={{.0}}/{{.1}}/{{.3}};{{/values}}",
        expected="0=one/two/;1=one/two/;2=one/two/;",
        data={
            "": {"3": "leaked"},
            "values": ["one", "two", "three"],
        },
    ),
    RenderCase(
        name="iteration metadata resolves numeric names from an indexable iterator",
        template="{{#values}}{{.index}}={{.0}}/{{.2}};{{/values}}",
        expected="0=one/three;1=one/three;2=one/three;",
        data_factory=lambda: {"values": _SizedItems()},
    ),
    RenderCase(
        name="iteration metadata leaves numeric names unavailable for a generator",
        template="{{#values}}[{{.0}}{{^.0}}none{{/.0}}:{{.}}]{{/values}}",
        expected="[none:first][none:second][none:third]",
        data_factory=lambda: {"": {"0": "leaked"}, "values": _many_items()},
    ),
    RenderCase(
        name="nested repeated sections use their nearest iteration metadata",
        template="{{#groups}}g{{.index}}:{{#items}}{{.index}}{{/items}}:{{.index}};{{/groups}}",
        expected="g0:01:0;g1:0:1;",
        data={
            "groups": [
                {"items": ["one", "two"]},
                {"items": ["three"]},
            ]
        },
    ),
    RenderCase(
        name="iteration metadata preserves named fields on mapping items",
        template="{{#items}}{{name}}/{{.index}}/{{.length}};{{/items}}",
        expected="one/0/2;two/1/2;",
        data={"items": [{"name": "one"}, {"name": "two"}]},
    ),
    RenderCase(
        name="nested same-binding sections restart positional metadata",
        template="{{#items}}outer={{.index}}({{#items}}inner={{.index}}/{{.first}};{{/items}}){{/items}}",
        expected="outer=0(inner=0/True;inner=1/False;)",
        data_factory=lambda: {"items": iter(("a", "b", "c"))},
    ),
    RenderCase(
        name="invalid leading-dot names remain unavailable metadata",
        template="{{#items}}[{{.-1}}|{{.unknown}}]{{/items}}",
        expected="[|]",
        data={"items": [{"": {"-1": "unexpected", "unknown": "unexpected"}}]},
    ),
)
