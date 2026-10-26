"""Chevron-owned public behavior cases for ordinary section rendering."""

from rendering_cases import RenderCase


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
