import sys

import pytest

import chevron


def test_deep_finite_partial_expansion_does_not_use_the_python_call_stack() -> None:
    depth = sys.getrecursionlimit() + 10
    partials = {
        f"partial-{index}": f"{{{{>partial-{index + 1}}}}}" for index in range(depth)
    }
    partials[f"partial-{depth}"] = "complete"

    assert chevron.render("{{>partial-0}}", partials_dict=partials) == "complete"


def test_deep_partial_resumes_parent_scope_and_indentation() -> None:
    depth = sys.getrecursionlimit() + 10
    partials = {
        f"partial-{index}": f"{{{{>partial-{index + 1}}}}}" for index in range(depth)
    }
    partials[f"partial-{depth}"] = "{{name}}\n{{name}}"

    shallow = chevron.render(
        "{{#item}}  {{>partial-0}}|{{name}}{{/item}}",
        {"item": {"name": "inner"}},
        partials_dict={"partial-0": "{{name}}\n{{name}}"},
    )
    deep = chevron.render(
        "{{#item}}  {{>partial-0}}|{{name}}{{/item}}",
        {"item": {"name": "inner"}},
        partials_dict=partials,
    )

    assert deep == shallow == "  inner\n  inner|inner"


def test_cyclic_partial_fails_with_a_bounded_error() -> None:
    with pytest.raises(RecursionError, match="nested template expansion"):
        chevron.render("{{>self}}", partials_dict={"self": "{{>self}}"})


def test_dynamic_partial_cycle_fails_with_a_bounded_error() -> None:
    with pytest.raises(RecursionError, match="nested template expansion"):
        chevron.render(
            "{{>*name}}",
            {"name": "self"},
            partials_dict={"self": "{{>*name}}"},
        )


def test_dynamic_partial_keeps_mapping_precedence_and_filesystem_containment(
    tmp_path,
) -> None:
    (tmp_path / "choice.mustache").write_text("filesystem", encoding="utf-8")
    (tmp_path.parent / "outside.mustache").write_text("outside", encoding="utf-8")

    assert (
        chevron.render(
            "{{>*selector}}",
            {"selector": "choice"},
            partials_path=tmp_path,
            partials_dict={"choice": "mapping"},
        )
        == "mapping"
    )
    assert (
        chevron.render(
            "{{>*selector}}",
            {"selector": "../outside"},
            partials_path=tmp_path,
        )
        == ""
    )


def test_dynamic_partial_respects_explicit_lambda_policy() -> None:
    called = False

    def selector() -> str:
        nonlocal called
        called = True
        return "choice"

    assert (
        chevron.render(
            "{{>*selector}}",
            {"selector": "choice"},
            partials_dict={"choice": "wrong"},
            lambdas={"selector": selector},
        )
        == ""
    )
    assert not called


def test_parent_override_preserves_literal_tokens() -> None:
    tokens = [
        ("parent", "layout"),
        ("block", "body"),
        ("literal", "{{name}}"),
        ("end", "body"),
        ("end", "layout"),
    ]

    assert (
        chevron.render(
            tokens,
            {"name": "Ada"},
            partials_dict={"layout": "parent:[{{$body}}default{{/body}}]"},
        )
        == "parent:[{{name}}]"
    )
