"""Chevron-owned source-template cases for inheritance behavior."""

from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class InheritanceCase:
    """One public rendering scenario shared by synchronous and async tests."""

    name: str
    template: str
    expected: str
    data: Mapping[str, Any] = field(default_factory=dict)
    partials: Mapping[str, str] = field(default_factory=dict)
    data_factory: Callable[[], Mapping[str, Any]] | None = None

    def render_data(self) -> Mapping[str, Any]:
        """Return fresh render data when the case owns a consumable value."""
        return self.data_factory() if self.data_factory is not None else self.data


async def _one_async_item() -> AsyncIterator[bool]:
    yield True


INHERITANCE_CASES = (
    InheritanceCase(
        name="indented parent multiline override keeps one prefix",
        template="  {{<parent}}{{$body}}one\ntwo\n{{/body}}{{/parent}}\n",
        partials={"parent": "head\n{{$body}}\ndefault\n{{/body}}\nfooter\n"},
        expected="  head\n  one\n  two\n  footer\n",
    ),
    InheritanceCase(
        name="indented parent override keeps intrinsic indentation",
        template="  {{<parent}}{{$body}}one\ntwo\n{{/body}}{{/parent}}\n",
        partials={"parent": "head\n{{$body}}\n    default\n{{/body}}\nfooter\n"},
        expected="  head\n      one\n      two\n  footer\n",
    ),
    InheritanceCase(
        name="standalone parent ignores interpolation inside block arguments",
        template="{{<parent}}{{$body}}{{name}}{{/body}}{{/parent}}\nAfter",
        data={"name": "hello"},
        partials={"parent": "[{{$body}}default{{/body}}]"},
        expected="[hello]After",
    ),
    InheritanceCase(
        name="standalone parent ignores sections inside block arguments",
        template="{{<parent}}{{$body}}{{#show}}{{name}}{{/show}}{{/body}}{{/parent}}\nAfter",
        data={"name": "hello", "show": True},
        partials={"parent": "[{{$body}}default{{/body}}]"},
        expected="[hello]After",
    ),
    InheritanceCase(
        name="inline block override ignores default indentation",
        template="{{<parent}}{{$body}}hello{{/body}}{{/parent}}",
        partials={"parent": "before {{$body}}\n  default\n{{/body}} after"},
        expected="before hello after",
    ),
    InheritanceCase(
        name="dynamic parent uses its first direct block override",
        template="{{<*layout}}{{$body}}first{{/body}}{{$body}}later{{/body}}{{/*layout}}",
        data={"layout": "page"},
        partials={"page": "[{{$body}}default{{/body}}]"},
        expected="[first]",
    ),
    InheritanceCase(
        name="inline parent block override preserves leading whitespace",
        template="{{<parent}}{{$body}}  hello{{/body}}{{/parent}}",
        partials={"parent": "[{{$body}}default{{/body}}]"},
        expected="[  hello]",
    ),
    InheritanceCase(
        name="inline default block preserves parent line context",
        template="before {{$body}}{{<parent}}{{/parent}}\nAfter{{/body}}",
        partials={"parent": "parent"},
        expected="before parent\nAfter",
    ),
    InheritanceCase(
        name="unoverridden multiline block keeps authored indentation",
        template="{{$body}}\n  default\n{{/body}}\n",
        expected="  default\n",
    ),
    InheritanceCase(
        name="CR-only block override preserves indentation",
        template="{{<parent}}{{$body}}\r    one\r    two\r{{/body}}{{/parent}}\r",
        partials={"parent": "Hi,\r  {{$body}}\r  {{/body}}\r"},
        expected="Hi,\r  one\r  two\r",
    ),
    *(
        InheritanceCase(
            name=f"standalone block opener ignores trailing {label}",
            template=(
                "{{<parent}}\n"
                + "{{$block}}"
                + suffix
                + "\n    one\n    two\n{{/block}}\n{{/parent}}\n"
            ),
            partials={"parent": "Hi,\n  {{$block}}\n  {{/block}}\n"},
            expected="Hi,\n  one\n  two\n",
        )
        for label, suffix in (("space", " "), ("tab", "\t"))
    ),
    InheritanceCase(
        name="same named nested block uses its own default body",
        template="{{<layout}}{{$body}}OUT{{$body}}IN{{/body}}{{/body}}{{/layout}}",
        partials={"layout": "[{{$body}}default{{/body}}]"},
        expected="[OUTIN]",
    ),
    InheritanceCase(
        name="multiline override keeps indentation after interpolation",
        template="{{<parent}}{{$body}}\n  {{name}}  after\n{{/body}}{{/parent}}",
        data={"name": "value"},
        partials={"parent": "{{$body}}default{{/body}}"},
        expected="value  after\n",
    ),
    InheritanceCase(
        name="nonstandalone parent does not indent its later lines",
        template="  {{<parent}}x{{/parent}}",
        partials={"parent": "one\ntwo"},
        expected="  one\ntwo",
    ),
    InheritanceCase(
        name="indented parent preserves override trailing spaces",
        template="  {{<parent}}{{$body}}hello  {{/body}}{{/parent}}\n",
        partials={"parent": "Hi,\n{{$body}}\n  default\n{{/body}}\n"},
        expected="  Hi,\n    hello  ",
    ),
    InheritanceCase(
        name="empty standalone override leaves no synthetic prefix",
        template="{{<parent}}{{$body}}{{/body}}{{/parent}}\nAfter",
        partials={"parent": "before\n  {{$body}}\n    default\n  {{/body}}\n"},
        expected="before\nAfter",
    ),
    InheritanceCase(
        name="block preserves trailing interpolation whitespace",
        template="{{<parent}}{{$block}}{{{value}}}{{/block}}{{/parent}}",
        data={"value": "x\n  "},
        partials={"parent": "{{$block}}\n  default\n{{/block}}"},
        expected="  x\n  ",
    ),
    InheritanceCase(
        name="parent preserves trailing interpolation whitespace",
        template="  {{<parent}}{{/parent}}\n",
        data={"value": "x\n  "},
        partials={"parent": "{{{value}}}"},
        expected="  x\n  ",
    ),
    InheritanceCase(
        name="ignored parent body text does not cancel standalone indentation",
        template="  {{<parent}}\nignored\n  {{/parent}}\n",
        partials={"parent": "one\ntwo\n"},
        expected="  one\n  two\n",
    ),
    InheritanceCase(
        name="nested standalone partial restores enclosing indentation",
        template="  {{>outer}}\n",
        partials={"outer": "head\n{{>inner}}\ntail\n", "inner": "a\nb\n"},
        expected="  head\n  a\n  b\n  tail\n",
    ),
    InheritanceCase(
        name="nested standalone parent restores enclosing indentation",
        template="  {{<outer}}{{/outer}}\n",
        partials={
            "outer": "head\n{{<inner}}{{/inner}}\nfoot\n",
            "inner": "one\ntwo\n",
        },
        expected="  head\n  one\n  two\n  foot\n",
    ),
    InheritanceCase(
        name="multiline nonstandalone parent preserves its closing suffix",
        template="X{{<parent}}\n{{/parent}}\nAFTER",
        partials={"parent": "PARENT"},
        expected="XPARENT\nAFTER",
    ),
    InheritanceCase(
        name="multiline nonstandalone parent with block preserves closing suffix",
        template="X{{<parent}}\n{{$body}}override{{/body}}\n{{/parent}}\nAFTER",
        partials={"parent": "[{{$body}}default{{/body}}]"},
        expected="X[override]\nAFTER",
    ),
    *(
        InheritanceCase(
            name=f"{label} parent and block tags stay inside a skipped section",
            template=template,
            data=data,
            partials=partials,
            expected="",
        )
        for label, template, data, partials in (
            (
                "section",
                "{{#show}}{{$body}}hidden{{/body}}leak{{/show}}",
                {"show": False},
                {},
            ),
            (
                "parent section",
                "{{#show}}{{<layout}}{{/layout}}leak{{/show}}",
                {"show": False},
                {"layout": "hidden"},
            ),
            (
                "inverted section",
                "{{^show}}{{$body}}hidden{{/body}}leak{{/show}}",
                {"show": True},
                {},
            ),
            (
                "inverted parent section",
                "{{^show}}{{<layout}}{{/layout}}leak{{/show}}",
                {"show": True},
                {"layout": "hidden"},
            ),
        )
    ),
    InheritanceCase(
        name="standalone parent leaves a following blank line intact",
        template="{{<layout}}\n{{/layout}}\n\nAfter",
        partials={"layout": "parent"},
        expected="parent\nAfter",
    ),
    InheritanceCase(
        name="inline parent leaves following interpolation intact",
        template="{{<layout}}{{/layout}}{{name}}\nAfter",
        data={"name": "Ada"},
        partials={"layout": "parent"},
        expected="parentAda\nAfter",
    ),
    *(
        InheritanceCase(
            name=f"same-line standalone parent consumes {label} suffix",
            template=f"{{{{<parent}}}}{{{{/parent}}}}{suffix}After",
            partials={"parent": "parent"},
            expected="parentAfter",
        )
        for label, suffix in (
            ("space LF", " \n"),
            ("tab LF", "\t\n"),
            ("space CRLF", " \r\n"),
            ("space CR", " \r"),
        )
    ),
    *(
        InheritanceCase(
            name=f"parent standalone status ignores {label} interpolation output",
            template="{{name}}{{<parent}}{{/parent}}\nAfter",
            data={"name": value},
            partials={"parent": "parent"},
            expected=expected,
        )
        for label, value, expected in (
            ("empty", None, "parent\nAfter"),
            ("whitespace", "   ", "   parent\nAfter"),
        )
    ),
    InheritanceCase(
        name="section scalar preserves parent line context",
        template="{{#items}}{{<parent}}{{/parent}}\nAfter{{/items}}",
        data={"items": True},
        partials={"parent": "parent"},
        expected="parent\nAfter",
    ),
    InheritanceCase(
        name="section sequence preserves parent line context",
        template="{{#items}}{{<parent}}{{/parent}}\nAfter{{/items}}",
        data={"items": [True]},
        partials={"parent": "parent"},
        expected="parent\nAfter",
    ),
    InheritanceCase(
        name="section iterator preserves parent line context",
        template="{{#items}}{{<parent}}{{/parent}}\nAfter{{/items}}",
        partials={"parent": "parent"},
        expected="parent\nAfter",
        data_factory=lambda: {"items": iter((True,))},
    ),
    *(
        InheritanceCase(
            name=f"ordinary partial indents {label} line endings",
            template=f"  {{{{>partial}}}}{ending}",
            partials={"partial": f"one{ending}two{ending}"},
            expected=f"  one{ending}  two{ending}",
        )
        for label, ending in (("LF", "\n"), ("CRLF", "\r\n"), ("CR", "\r"))
    ),
    *(
        InheritanceCase(
            name=f"standalone comment and section use {label} line endings",
            template=(
                f"before{ending}{{{{! comment }}}}{ending}{{{{#show}}}}{ending}"
                f"inside{ending}{{{{/show}}}}{ending}after"
            ),
            data={"show": True},
            expected=f"before{ending}inside{ending}after",
        )
        for label, ending in (("LF", "\n"), ("CRLF", "\r\n"), ("CR", "\r"))
    ),
)


ASYNC_INHERITANCE_CASES = (
    InheritanceCase(
        name="section async iterable preserves parent line context",
        template="{{#items}}{{<parent}}{{/parent}}\nAfter{{/items}}",
        partials={"parent": "parent"},
        expected="parent\nAfter",
        data_factory=lambda: {"items": _one_async_item()},
    ),
)
