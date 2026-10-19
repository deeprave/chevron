"""Behavioural tests for declared Mustache and Chevron lambda protocols."""

from io import StringIO

import chevron
import pytest
from chevron.tokenizer import ChevronError, tokenize


def test_tokenize_keeps_its_public_two_tuple_stream_by_default() -> None:
    assert list(tokenize("A{{name}}")) == [("literal", "A"), ("variable", "name")]


def test_tokenize_include_raw_exposes_source_without_changing_default_mode() -> None:
    assert list(tokenize("{{! comment }}", include_raw=True)) == [
        ("comment", "comment", "{{! comment }}")
    ]


def test_tokenize_rejects_file_like_inputs_with_actionable_guidance() -> None:
    with pytest.raises(TypeError, match=r"use chevron\.render\(\) for file-like input"):
        list(tokenize(StringIO("{{name}}")))


def test_nested_lambda_tokenisation_does_not_leak_syntax_state() -> None:
    @chevron.func
    def malformed() -> str:
        return "{{#unclosed}}"

    with pytest.raises(ChevronError, match='the tag "unclosed" was never closed'):
        chevron.render("{{malformed}}", lambdas={"malformed": malformed})

    with pytest.raises(ChevronError, match='the tag "outer" was never closed'):
        chevron.render("{{#outer}}")


def test_decorated_lambda_preserves_function_metadata_and_binding() -> None:
    class Greetings:
        @chevron.func
        def greeting(self) -> str:
            """Return the greeting source."""

            return "hello"

    assert Greetings.greeting.__name__ == "greeting"
    assert Greetings.greeting.__doc__ == "Return the greeting source."
    assert chevron.render("{{greeting}}", {"greeting": Greetings().greeting}) == "hello"


def test_decorated_callable_instance_has_fallback_metadata() -> None:
    class Greeting:
        """Return a greeting when called."""

        def __call__(self) -> str:
            return "hello"

    callback = Greeting()
    wrapped = chevron.func(callback)

    assert wrapped.__name__ == "Greeting"
    assert (
        wrapped.__qualname__
        == "test_decorated_callable_instance_has_fallback_metadata.<locals>.Greeting"
    )
    assert wrapped.__module__ == __name__
    assert wrapped.__doc__ == "Return a greeting when called."
    assert wrapped.__annotations__ == {}
    assert wrapped.__wrapped__ is callback
    assert chevron.render("{{greeting}}", lambdas={"greeting": wrapped}) == "hello"


def test_iterable_section_collects_nested_inverted_sections_with_the_same_name() -> (
    None
):
    template = "{{#items}}{{^items}}empty{{/items}}{{name}};{{/items}}"

    assert (
        chevron.render(
            template,
            {"items": [{"name": "first"}, {"name": "second"}]},
        )
        == "first;second;"
    )


def test_declared_function_renders_escaped_and_unescaped_interpolation() -> None:
    @chevron.func
    def markup() -> str:
        return "{{value}} >"

    assert (
        chevron.render(
            "{{markup}}|{{{markup}}}",
            {"value": "<tag>"},
            lambdas={"markup": markup},
        )
        == "&amp;lt;tag&amp;gt; &gt;|&lt;tag&gt; >"
    )


def test_declared_function_matches_ordinary_interpolation_in_an_indented_partial() -> (
    None
):
    template = "  {{>part}}\n"
    partials = {"part": "{{value}}\n"}

    @chevron.func
    def value() -> str:
        return "a\nb"

    ordinary = chevron.render(
        template,
        {"value": "a\nb"},
        partials_dict=partials,
    )
    interpolated = chevron.render(
        template,
        partials_dict=partials,
        lambdas={"value": value},
    )

    assert interpolated == ordinary == "  a\nb\n"


def test_declared_function_uses_default_delimiters_and_is_not_cached() -> None:
    calls: list[int] = []

    @chevron.func
    def value() -> str:
        calls.append(len(calls))
        return "{{planet}}"

    assert (
        chevron.render(
            "{{=| |=}}|value| == |value|",
            {"planet": "Earth"},
            lambdas={"value": value},
        )
        == "Earth == Earth"
    )
    assert calls == [0, 1]


def test_declared_function_uses_configured_render_default_delimiters() -> None:
    @chevron.func
    def value() -> str:
        return "<<planet>>"

    assert (
        chevron.render(
            "<<=| |=>>|value|",
            {"planet": "Earth"},
            lambdas={"value": value},
            def_ldel="<<",
            def_rdel=">>",
        )
        == "Earth"
    )


def test_declared_section_receives_raw_text_and_current_delimiters() -> None:
    received: list[str] = []

    @chevron.section
    def value(text: str) -> str:
        received.append(text)
        return f"{text}{{{{planet}}}} => |planet|{text}"

    assert (
        chevron.render(
            "{{=| |=}}<|#value|-|/value|>",
            {"planet": "Earth"},
            lambdas={"value": value},
        )
        == "<-{{planet}} => Earth->"
    )
    assert received == ["-"]


def test_declared_section_uses_its_opening_delimiters_after_body_changes_them() -> None:
    @chevron.section
    def repeat(text: str) -> str:
        return text

    assert (
        chevron.render(
            "{{=| |=}}|#repeat||planet||= {{ }} =|{{planet}}{{/repeat}}",
            {"planet": "Earth"},
            lambdas={"repeat": repeat},
        )
        == "EarthEarth"
    )


@pytest.mark.parametrize(
    ("template", "expected_source"),
    [
        ("{{#value}}A{{! comment }}B{{/value}}", "A{{! comment }}B"),
        (
            "{{#value}}\n  {{! standalone comment }}\n{{/value}}",
            "\n  {{! standalone comment }}\n",
        ),
    ],
)
def test_declared_section_receives_literal_source(
    template: str, expected_source: str
) -> None:
    received: list[str] = []

    @chevron.section
    def value(text: str) -> str:
        received.append(text)
        return ""

    assert chevron.render(template, lambdas={"value": value}) == ""
    assert received == [expected_source]


def test_declared_compatibility_lambda_retains_temporary_data_rendering() -> None:
    received: list[str] = []

    @chevron.compat
    def value(text: str, render) -> str:
        received.append(text)
        return render(text, {"message": "temporary"})

    assert (
        chevron.render(
            "{{#value}}{{message}}{{! comment}}{{/value}}",
            {"message": "outer"},
            lambdas={"value": value},
        )
        == "temporary"
    )
    assert received == ["{{ message}}"]


@pytest.mark.parametrize("temporary", [None, {}, [], False, 0, ""])
def test_compatibility_render_uses_parent_data_for_falsy_temporary_data(
    temporary,
) -> None:
    @chevron.compat
    def value(text: str, render) -> str:
        return render(text, temporary)

    assert (
        chevron.render(
            "{{#value}}{{message}}{{/value}}",
            {"message": "outer"},
            lambdas={"value": value},
        )
        == "outer"
    )


@pytest.mark.parametrize("decorator", [chevron.func, chevron.section, chevron.compat])
def test_lambda_returning_none_renders_empty_and_warns(decorator, caplog) -> None:
    if decorator is chevron.func:

        @decorator
        def value():
            return None

        template = "{{value}}"
    elif decorator is chevron.section:

        @decorator
        def value(text):
            return None

        template = "{{#value}}body{{/value}}"
    else:

        @decorator
        def value(text, render):
            return None

        template = "{{#value}}body{{/value}}"

    assert chevron.render(template, lambdas={"value": value}, warn=True) == ""
    assert caplog.messages == ["Lambda 'value' returned None; rendering an empty value"]


@pytest.mark.parametrize("protocol", [chevron.func, chevron.compat])
def test_compatibility_mode_none_lambda_result_renders_empty_and_warns(
    protocol, caplog
) -> None:
    if protocol is chevron.func:

        @protocol
        def value():
            return None

        template = "{{value}}"
    else:

        @protocol
        def value(text, render):
            return None

        template = "{{#value}}body{{/value}}"

    assert chevron.render(template, {"value": value}, warn=True) == ""
    assert caplog.messages == ["Lambda 'value' returned None; rendering an empty value"]


def test_undecorated_registered_lambda_remains_compatibility_protocol() -> None:
    def value(text: str, render) -> str:
        return render(text)

    assert (
        chevron.render(
            "{{#value}}{{message}}{{/value}}",
            {"message": "rendered"},
            lambdas={"value": value},
        )
        == "rendered"
    )


@pytest.mark.parametrize("explicit", [False, True])
def test_undecorated_interpolation_callable_is_not_invoked(explicit: bool) -> None:
    calls: list[None] = []

    class Value:
        def __call__(self) -> str:
            calls.append(None)
            return "unexpected"

        def __str__(self) -> str:
            return "callable value"

    value = Value()
    options = {"lambdas": {"value": value}} if explicit else {}
    assert chevron.render("{{value}}", {"value": value}, **options) == (
        "" if explicit else "callable value"
    )
    assert calls == []


def test_declared_function_takes_precedence_over_template_data() -> None:
    @chevron.func
    def value() -> str:
        return "registered"

    assert (
        chevron.render(
            "{{value}}",
            {"value": "template data"},
            lambdas={"value": value},
        )
        == "registered"
    )


@pytest.mark.parametrize("explicit", [False, True])
@pytest.mark.parametrize(
    ("decorator", "template"),
    [
        (chevron.func, "{{#value}}body{{/value}}"),
        (chevron.section, "{{value}}|{{{value}}}"),
        (chevron.compat, "{{value}}|{{{value}}}"),
    ],
)
def test_incompatible_lambda_tag_does_not_invoke_callable(
    explicit: bool, decorator, template: str
) -> None:
    calls: list[str] = []

    @decorator
    def value(*args) -> str:
        calls.append("called")
        return "unexpected"

    options = {"lambdas": {"value": value}} if explicit else {}
    assert chevron.render(template, {"value": value}, **options) == (
        "" if decorator is chevron.func else "|"
    )
    assert calls == []


def test_declared_lambda_protocols_remain_available_in_nested_partial_renders() -> None:
    @chevron.func
    def value() -> str:
        return "{{message}}"

    assert (
        chevron.render(
            "{{>partial}}",
            {"message": "rendered"},
            partials_dict={"partial": "{{value}}"},
            lambdas={"value": value},
        )
        == "rendered"
    )


def test_declared_section_returning_a_partial_uses_render_default_delimiters() -> None:
    @chevron.section
    def include(text: str) -> str:
        return "|>part|"

    assert (
        chevron.render(
            "{{=| |=}}|#include|ignored|/include|",
            {"value": "rendered"},
            partials_dict={"part": "{{value}}"},
            lambdas={"include": include},
        )
        == "rendered"
    )


def test_partial_resets_to_render_default_delimiters_after_a_change() -> None:
    assert (
        chevron.render(
            "{{=| |=}}|#items||>part||/items|",
            {"items": [{"value": "rendered"}]},
            partials_dict={"part": "{{value}}"},
        )
        == "rendered"
    )


def test_skipped_and_iterated_sections_propagate_delimiter_changes() -> None:
    assert (
        chevron.render(
            "{{#off}}{{=| |=}}|value||/off||value|",
            {"off": False, "value": "skipped"},
        )
        == "skipped"
    )
    assert (
        chevron.render(
            "{{#items}}{{=| |=}}|value||/items||value|",
            {"items": [{"value": "item"}], "value": "outer"},
        )
        == "itemouter"
    )


def test_declared_functions_remain_available_in_recursively_rendered_text() -> None:
    @chevron.func
    def outer() -> str:
        return "{{inner}}"

    @chevron.func
    def inner() -> str:
        return "rendered"

    assert (
        chevron.render(
            "{{outer}}",
            lambdas={"outer": outer, "inner": inner},
        )
        == "rendered"
    )


@pytest.mark.parametrize("decorator", [chevron.func, chevron.section, chevron.compat])
def test_declared_lambda_decorators_reject_non_callables(decorator) -> None:
    with pytest.raises(TypeError, match="callable"):
        decorator("not callable")


def test_compatibility_mode_classifies_uninspectable_callables_without_calling_them() -> (
    None
):
    class Uninspectable:
        def __init__(self) -> None:
            self.calls: list[tuple[object, ...]] = []

        @property
        def __signature__(self):
            raise ValueError("signature unavailable")

        def __call__(self, *args: object) -> str:
            self.calls.append(args)
            return "legacy"

        def __str__(self) -> str:
            return "legacy callable"

    value = Uninspectable()

    assert chevron.render("{{value}}", {"value": value}) == "legacy callable"
    assert value.calls == []
    assert chevron.render("{{#value}}body{{/value}}", {"value": value}) == "legacy"
    assert len(value.calls) == 1
    assert value.calls[0][0] == "body"
    assert callable(value.calls[0][1])
