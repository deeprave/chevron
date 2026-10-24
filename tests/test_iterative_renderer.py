"""Behavioural regression tests for the iterative renderer."""

import sys

import pytest

import chevron


def test_deep_sync_lambda_expansion_does_not_use_the_python_call_stack() -> None:
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


def test_lambda_expansion_resumes_parent_delimiters() -> None:
    @chevron.func
    def value() -> str:
        return "{{name}}"

    assert (
        chevron.render(
            "{{#item}}{{=<% %>=}}<%value%>|<%name%><%/item%>",
            {"item": {"name": "inner"}},
            lambdas={"value": value},
        )
        == "inner|inner"
    )


def test_dynamic_partial_cycle_fails_with_a_bounded_error() -> None:
    with pytest.raises(RecursionError, match="nested template expansion"):
        chevron.render(
            "{{>*name}}",
            {"name": "self"},
            partials_dict={"self": "{{>*name}}"},
        )


def test_function_lambda_cycle_fails_with_a_bounded_error() -> None:
    @chevron.func
    def loop() -> str:
        return "{{loop}}"

    with pytest.raises(RecursionError, match="nested template expansion"):
        chevron.render("{{loop}}", lambdas={"loop": loop})


def test_iterator_error_does_not_gain_stop_iteration_context() -> None:
    class Items:
        def __init__(self) -> None:
            self.first = True

        def __iter__(self) -> "Items":
            return self

        def __next__(self) -> str:
            if self.first:
                self.first = False
                return "item"
            raise ValueError("iterator failed")

    with pytest.raises(ValueError, match="iterator failed") as error:
        chevron.render("{{#items}}{{/items}}", {"items": Items()})

    assert error.value.__context__ is None


def test_compatibility_section_rejects_non_string_results_promptly() -> None:
    called = False

    @chevron.compat
    def invalid_result(text: str, render) -> int:
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


def test_deep_standard_section_lambda_expansion_does_not_use_the_python_call_stack() -> (
    None
):
    depth = sys.getrecursionlimit() + 10
    lambdas = {}

    for index in range(depth):

        @chevron.section
        def expansion(body: str, index: int = index) -> str:
            return f"{{{{#section-{index + 1}}}}}{body}{{{{/section-{index + 1}}}}}"

        lambdas[f"section-{index}"] = expansion

    @chevron.section
    def complete(body: str) -> str:
        return body

    lambdas[f"section-{depth}"] = complete

    assert (
        chevron.render("{{#section-0}}complete{{/section-0}}", lambdas=lambdas)
        == "complete"
    )


def test_deep_iterable_sections_do_not_use_the_python_call_stack() -> None:
    depth = sys.getrecursionlimit() + 10
    template = "{{#items}}" * depth + "complete" + "{{/items}}" * depth
    data = {"items": [{"items": []}]}
    current = data["items"][0]
    for _ in range(depth - 1):
        next_item = {"items": []}
        current["items"] = [next_item]
        current = next_item

    assert chevron.render(template, data) == "complete"
