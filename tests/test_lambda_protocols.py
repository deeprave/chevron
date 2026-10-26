"""Behavioural tests for declared Mustache and Chevron lambda protocols."""

from io import StringIO
import sys

import chevron
import pytest
from chevron.tokenizer import ChevronError, tokenize


def test_deep_function_lambda_expansion_does_not_use_the_python_call_stack() -> None:
    depth = sys.getrecursionlimit() + 10
    lambdas = {}

    for index in range(depth):

        @chevron.func
        def expansion(index: int = index) -> str:
            return f"{{{{lambda-{index + 1}}}}}"

        lambdas[f"lambda-{index}"] = expansion

    @chevron.func
    def complete() -> str:
        return "complete"

    lambdas[f"lambda-{depth}"] = complete

    assert chevron.render("{{lambda-0}}", lambdas=lambdas) == "complete"


def test_function_lambda_cycle_fails_with_a_bounded_error() -> None:
    @chevron.func
    def loop() -> str:
        return "{{loop}}"

    with pytest.raises(RecursionError, match="nested template expansion"):
        chevron.render("{{loop}}", lambdas={"loop": loop})


def test_compatibility_section_rejects_non_string_results_promptly() -> None:
    called = False

    @chevron.compat
    def invalid_result(text: str, render: object) -> int:
        return 1

    @chevron.func
    def later() -> str:
        nonlocal called
        called = True
        return "later"

    with pytest.raises(TypeError, match="Compatibility lambda 'invalid_result'"):
        chevron.render(
            "{{#invalid_result}}body{{/invalid_result}}{{later}}",
            lambdas={"invalid_result": invalid_result, "later": later},
        )

    assert not called


def test_tokenize_keeps_its_public_two_tuple_stream_by_default() -> None:
    assert list(tokenize("A{{name}}")) == [("literal", "A"), ("variable", "name")]


def test_tokenize_include_raw_exposes_source_without_changing_default_mode() -> None:
    assert list(tokenize("{{! comment }}", include_raw=True)) == [
        ("comment", "comment", "{{! comment }}")
    ]


def test_tokenize_rejects_file_like_inputs_with_actionable_guidance() -> None:
    with pytest.raises(TypeError, match=r"use chevron\.render\(\) for file-like input"):
        list(tokenize(StringIO("{{name}}")))  # ty: ignore[invalid-argument-type]


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


@pytest.mark.parametrize(
    ("decorator", "template"),
    [
        (chevron.func, "{{value}}"),
        (chevron.section, "{{#value}}body{{/value}}"),
        (chevron.compat, "{{#value}}body{{/value}}"),
    ],
)
def test_sync_render_rejects_awaitable_lambda_results(decorator, template: str) -> None:
    if decorator is chevron.func:

        @decorator
        async def value() -> str:
            return "value"

    elif decorator is chevron.section:

        @decorator
        async def value(body: str) -> str:
            return body

    else:

        @decorator
        async def value(body: str, render) -> str:
            return body

    with pytest.raises(TypeError, match=r"use chevron\.async_render"):
        chevron.render(template, lambdas={"value": value})


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
    result = (
        chevron.render("{{value}}", {"value": value}, lambdas={"value": value})
        if explicit
        else chevron.render("{{value}}", {"value": value})
    )
    assert result == ("" if explicit else "callable value")
    assert calls == []


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

    result = (
        chevron.render(template, {"value": value}, lambdas={"value": value})
        if explicit
        else chevron.render(template, {"value": value})
    )
    assert result == ("" if decorator is chevron.func else "|")
    assert calls == []


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
