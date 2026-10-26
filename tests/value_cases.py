"""Chevron-owned public behavior cases for basic value rendering."""

from rendering_cases import RenderCase


VALUE_CASES = (
    RenderCase(name="literal text", template="plain text", expected="plain text"),
    RenderCase(
        name="unicode literal",
        template="(╯°□°）╯︵ ┻━┻",
        expected="(╯°□°）╯︵ ┻━┻",
    ),
    RenderCase(
        name="unicode interpolation",
        template="{{table_flip}}",
        data={"table_flip": "(╯°□°）╯︵ ┻━┻"},
        expected="(╯°□°）╯︵ ┻━┻",
    ),
    RenderCase(
        name="escaped interpolation",
        template="{{value}}",
        data={"value": '<tag>"'},
        expected="&lt;tag&gt;&quot;",
    ),
    RenderCase(
        name="unescaped interpolation",
        template="{{{value}}}",
        data={"value": '<tag>"'},
        expected='<tag>"',
    ),
)
