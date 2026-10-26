"""Chevron-owned public behavior cases for partial and parent rendering."""

from rendering_cases import RenderCase


PARTIAL_CASES = (
    RenderCase(
        name="unicode partial content",
        template="{{>table_flip}}",
        partials={"table_flip": "(╯°□°）╯︵ ┻━┻"},
        expected="(╯°□°）╯︵ ┻━┻",
    ),
    RenderCase(
        name="partial missing section value",
        template="before, {{>partial}}, after",
        partials={"partial": "partial: {{#missing}}bloop{{/missing}}"},
        expected="before, partial: , after",
    ),
    RenderCase(
        name="tab-indented standalone partial",
        template="\t{{>count}}",
        partials={"count": "\tone\n\ttwo"},
        expected="\t\tone\n\t\ttwo",
    ),
    RenderCase(
        name="nested partial and iterable indentation",
        template="{{>count}}",
        data={"thing": ["foo", "bar", "baz"]},
        partials={
            "count": "    {{>iter_scope}}",
            "iter_scope": "foobar\n{{#thing}}\n {{.}}\n{{/thing}}",
        },
        expected="    foobar\n     foo\n     bar\n     baz\n",
    ),
    RenderCase(
        name="partial missing interpolation value",
        template="{{first}} {{>partial}} {{third}}",
        data={"first": "1st", "third": "3rd"},
        partials={"partial": "partial: {{missing}}"},
        expected="1st partial:  3rd",
    ),
    RenderCase(
        name="dynamic partial uses current section scope",
        template="{{#items}}[{{>*presentation.name}}]{{/items}}",
        data={"presentation": {"name": "item"}, "items": ["first", "second"]},
        partials={"item": "{{.}}"},
        expected="[first][second]",
    ),
    RenderCase(
        name="missing dynamic partial is empty",
        template="{{>*missing}}",
        partials={"missing": "wrong"},
        expected="",
    ),
    RenderCase(
        name="empty dynamic partial selector is empty",
        template="{{>*}}",
        partials={"*": "wrong"},
        expected="",
    ),
    RenderCase(
        name="nested dynamic partial selector is rejected",
        template="{{>**template}}",
        data={"template": "name", "name": "content"},
        partials={"**template": "wrong", "content": "wrong"},
        expected="",
    ),
    RenderCase(
        name="missing later dynamic partial selector name is empty",
        template="{{>*partial.name}}",
        data={"partial": "selected"},
        partials={"selected": "incorrect partial"},
        expected="",
    ),
    RenderCase(
        name="parent uses default block",
        template="{{<layout}}{{/layout}}",
        data={"name": "Ada"},
        partials={"layout": "<main>{{$body}}default {{name}}{{/body}}</main>"},
        expected="<main>default Ada</main>",
    ),
    RenderCase(
        name="parent block override",
        template="{{<layout}}{{$body}}override {{name}}{{/body}}{{/layout}}",
        data={"name": "Ada"},
        partials={"layout": "<main>{{$body}}default {{name}}{{/body}}</main>"},
        expected="<main>override Ada</main>",
    ),
    RenderCase(
        name="parent override uses parent expansion scope",
        template="{{<parent}}{{$block}}child {{fruit}}{{/block}}{{/parent}}",
        data={"fruit": "apples", "nested": {"fruit": "bananas"}},
        partials={
            "parent": "{{#nested}}{{$block}}parent {{fruit}}{{/block}}{{/nested}}"
        },
        expected="child bananas",
    ),
    RenderCase(
        name="missing dynamic parent is empty",
        template="before {{<*layout}}{{$body}}discard{{/body}}{{/*layout}} after",
        expected="before  after",
    ),
    RenderCase(
        name="intrinsic block reindentation preserves trailing spaces",
        template="{{<parent}}{{$block}}hello  {{/block}}{{/parent}}",
        partials={"parent": "Hi,\n{{$block}}\n  default\n{{/block}}\n"},
        expected="Hi,\n  hello  ",
    ),
)
