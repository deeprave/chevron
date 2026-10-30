"""Chevron-owned public behavior cases for value and scope resolution."""

from collections import namedtuple

from rendering_cases import RenderCase


class _EqualityError:
    def __eq__(self, other: object) -> bool:
        raise ValueError("equality failed")


class _TruthinessError:
    def __eq__(self, other: object) -> bool:
        return False

    def __bool__(self) -> bool:
        raise ValueError("truthiness failed")


class _Complex:
    attr = 42


class _Data:
    value = "visible"


Coordinates = namedtuple("Coordinates", ["x", "y"])


SCOPE_CASES = (
    RenderCase(
        name="top-level sequence uses current context",
        template="{{#.}}({{.}}){{/.}}",
        data=[1, 2, 3, 4, 5],
        expected="(1)(2)(3)(4)(5)",
    ),
    RenderCase(
        name="nested dotted sections restore parent scope",
        template="{{#1.2}}{{#data}}{{.}}{{/data}}{{/1.2}}",
        data={"1": {"2": [{"data": ["1", "2", "3"]}]}},
        expected="123",
    ),
    RenderCase(
        name="unicode sequence items use current context",
        template="{{#items}}{{.}}{{/items}}",
        data={"items": ["☠"]},
        expected="☠",
    ),
    RenderCase(
        name="dotted lookup resolves public attributes without scalar traversal",
        template="{{complex.attr}} {{number.attr}}",
        data={"complex": _Complex(), "number": 1},
        expected="42 ",
    ),
    RenderCase(
        name="empty scopes render literal text",
        template="literal",
        scopes=(),
        expected="literal",
    ),
    RenderCase(
        name="empty scopes render missing interpolation empty",
        template="{{missing}}",
        scopes=(),
        expected="",
    ),
    *(
        RenderCase(
            name=f"inverted section uses parent current context {label}",
            template=f"{{{{^missing}}}}{tag}{{{{/missing}}}}",
            data="context",
            expected="context",
        )
        for label, tag in (("triple", "{{{.}}}"), ("ampersand", "{{& .}}"))
    ),
    *(
        RenderCase(
            name=f"true current context is not inverted marker {label}",
            template=f"{{{{^missing}}}}{tag}{{{{/missing}}}}",
            data=True,
            expected="True",
        )
        for label, tag in (
            ("escaped", "{{.}}"),
            ("triple", "{{{.}}}"),
            ("ampersand", "{{& .}}"),
        )
    ),
    *(
        RenderCase(
            name=f"nested inverted sections preserve current context {label}",
            template="{{^missing}}{{^other}}" + tag + "{{/other}}{{/missing}}",
            data="context",
            expected="context",
        )
        for label, tag in (
            ("escaped", "{{.}}"),
            ("triple", "{{{.}}}"),
            ("ampersand", "{{& .}}"),
        )
    ),
    RenderCase(
        name="nested inverted sections preserve current scope section",
        template="{{^missing}}{{^other}}{{#.}}{{.}}{{/.}}{{/other}}{{/missing}}",
        data="context",
        expected="context",
    ),
    *(
        RenderCase(
            name=f"dotted sequence lookup {name}",
            template=f"{{{{{name}}}}}",
            data={"count": [5, 4, 3, 2, 1]},
            expected=expected,
        )
        for name, expected in (
            ("count.0", "5"),
            ("count.1", "4"),
            ("count.100", ""),
            ("missing.0", ""),
        )
    ),
    RenderCase(
        name="dotted lookup does not fall back after resolved first name",
        template="{{#a}}{{b.c}}{{/a}}",
        data={"a": {"b": {}}, "b": {"c": "outer value"}},
        expected="",
    ),
    RenderCase(
        name="missing later dotted name does not render resolved prefix",
        template="{{a.b.c}}",
        data={"a": {"b": {"visible": "value"}}},
        expected="",
    ),
    RenderCase(
        name="numeric lookup falls back past scalar section frame",
        template="{{#items}}{{0}}{{/items}}",
        data={"items": [1], "0": "outer value"},
        expected="outer value",
    ),
    RenderCase(
        name="numeric lookup falls back past inverted section marker",
        template="{{^flag}}{{0}}{{/flag}}",
        data={"flag": False, "0": "outer value"},
        expected="outer value",
    ),
    RenderCase(
        name="namedtuple fields are template values",
        template="{{x}} {{y}}",
        data=Coordinates("hello", "world"),
        expected="hello world",
    ),
    RenderCase(
        name="public class attributes are template values",
        template="{{value}}",
        data=_Data(),
        expected="visible",
    ),
    RenderCase(
        name="builtin callable attributes are not template values",
        template="{{title}}",
        data="an ordinary string",
        expected="",
    ),
    *(
        RenderCase(
            name=f"ordinary falsey value {label} keeps tag behavior",
            template=(
                "{{value}}|{{{value}}}|{{#value}}section{{/value}}"
                "{{^value}}inverted{{/value}}"
            ),
            data={"value": value},
            expected=expected,
        )
        for label, value, expected in (
            ("zero", 0, "0|0|inverted"),
            ("false", False, "False|False|inverted"),
            ("none", None, "||inverted"),
            ("empty string", "", "||inverted"),
            ("empty list", [], "||inverted"),
            ("empty mapping", {}, "||inverted"),
        )
    ),
    RenderCase(
        name="missing and empty sections use ordinary falsey behavior",
        template=(
            "{{#outer}}{{#empty}}section{{/empty}}{{^empty}}inverted{{/empty}}"
            "{{/outer}}{{^missing}}missing{{/missing}}"
        ),
        data={"outer": {"empty": []}},
        expected="invertedmissing",
    ),
    *(
        RenderCase(
            name=f"coercion error falls back to later scope {label}",
            template="{{value}}",
            scopes=({"value": value}, {"value": "fallback"}),
            expected="fallback",
        )
        for label, value in (
            ("equality", _EqualityError()),
            ("truthiness", _TruthinessError()),
        )
    ),
    RenderCase(
        name="dotted lookup does not fall back after normalisation failure",
        template="{{a.b}}",
        scopes=(
            {"a": {"b": _TruthinessError()}},
            {"a": {"b": "outer value"}},
        ),
        expected="",
    ),
)
