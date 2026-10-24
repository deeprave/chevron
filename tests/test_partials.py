import sys

import pytest

import chevron
from chevron import renderer


def test_unicode_partial_content_renders_unchanged() -> None:
    assert (
        chevron.render(
            "{{>table_flip}}", partials_dict={"table_flip": "(╯°□°）╯︵ ┻━┻"}
        )
        == "(╯°□°）╯︵ ┻━┻"
    )


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
    partials[f"partial-{depth}"] = "{{name}}"

    shallow = chevron.render(
        "{{#item}}  {{>partial-0}}|{{name}}{{/item}}",
        {"item": {"name": "inner"}},
        partials_dict={"partial-0": "{{name}}"},
    )
    deep = chevron.render(
        "{{#item}}  {{>partial-0}}|{{name}}{{/item}}",
        {"item": {"name": "inner"}},
        partials_dict=partials,
    )

    assert deep == shallow == "  inner|inner"


def test_cyclic_partial_fails_with_a_bounded_error(monkeypatch) -> None:
    monkeypatch.setattr(renderer, "_MAX_ACTIVE_WORK", 4)

    with pytest.raises(RecursionError, match="nested template expansion"):
        chevron.render("{{>self}}", partials_dict={"self": "{{>self}}"})


def test_missing_values_in_configured_partials_render_empty() -> None:
    assert (
        chevron.render(
            "before, {{>partial}}, after",
            partials_dict={"partial": "partial: {{#missing}}bloop{{/missing}}"},
        )
        == "before, partial: , after"
    )


def test_standalone_partial_indentation_is_preserved() -> None:
    assert (
        chevron.render("\t{{>count}}", partials_dict={"count": "\tone\n\ttwo"})
        == "\t\tone\n\t\ttwo"
    )


def test_nested_partial_and_iterable_indentation_is_preserved() -> None:
    assert (
        chevron.render(
            "{{>count}}",
            {"thing": ["foo", "bar", "baz"]},
            partials_dict={
                "count": "    {{>iter_scope}}",
                "iter_scope": "foobar\n{{#thing}}\n {{.}}\n{{/thing}}",
            },
        )
        == "    foobar\n     foo\n     bar\n     baz\n"
    )


def test_missing_interpolation_values_in_partials_render_empty() -> None:
    assert (
        chevron.render(
            "{{first}} {{>partial}} {{third}}",
            {"first": "1st", "third": "3rd"},
            partials_dict={"partial": "partial: {{missing}}"},
        )
        == "1st partial:  3rd"
    )


def test_dynamic_partial_keeps_the_current_section_scope() -> None:
    assert (
        chevron.render(
            "{{#items}}[{{>*presentation.name}}]{{/items}}",
            {
                "presentation": {"name": "item"},
                "items": ["first", "second"],
            },
            partials_dict={"item": "{{.}}"},
        )
        == "[first][second]"
    )


def test_missing_or_nested_dynamic_partial_names_render_empty() -> None:
    assert chevron.render("{{>*missing}}", partials_dict={"missing": "wrong"}) == ""
    assert chevron.render("{{>*}}", partials_dict={"*": "wrong"}) == ""
    assert (
        chevron.render(
            "{{>**template}}",
            {"template": "name", "name": "content"},
            partials_dict={"**template": "wrong", "content": "wrong"},
        )
        == ""
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
