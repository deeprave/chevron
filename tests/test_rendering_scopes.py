from collections import namedtuple

import pytest

import chevron


def test_top_level_sequence_uses_the_current_context_name() -> None:
    assert chevron.render("{{#.}}({{.}}){{/.}}", [1, 2, 3, 4, 5]) == "(1)(2)(3)(4)(5)"


def test_nested_dotted_sections_restore_the_parent_scope() -> None:
    assert (
        chevron.render(
            "{{#1.2}}{{#data}}{{.}}{{/data}}{{/1.2}}",
            {"1": {"2": [{"data": ["1", "2", "3"]}]}},
        )
        == "123"
    )


def test_unicode_sequence_items_render_through_the_current_context_name() -> None:
    assert chevron.render("{{#items}}{{.}}{{/items}}", {"items": ["☠"]}) == "☠"


def test_dotted_lookup_resolves_public_attributes_without_traversing_scalars() -> None:
    class Complex:
        attr = 42

    assert (
        chevron.render(
            "{{complex.attr}} {{number.attr}}", {"complex": Complex(), "number": 1}
        )
        == "42 "
    )


def test_inverted_sections_evaluate_mixed_sequence_items_independently() -> None:
    assert (
        chevron.render(
            "{{#object}}{{^child}}{{.}}{{/child}}{{/object}}",
            {"object": ["foo", "bar", {"child": True}, "baz"]},
        )
        == "foobarbaz"
    )


def test_nested_sections_with_the_same_name_restore_the_outer_scope() -> None:
    assert (
        chevron.render("A{{#x}}B{{#x}}{{.}}{{/x}}C{{/x}}D", {"x": ["z", "x"]})
        == "ABzxCBzxCD"
    )


def test_lambda_result_sections_do_not_mutate_the_caller_scopes_container() -> None:
    scopes: list[dict[str, object]] = [{"item": {"value": "1"}}]

    @chevron.func
    def outer() -> str:
        return "{{#item}}{{inner}}{{/item}}"

    @chevron.func
    def inner() -> str:
        return str(len(scopes))

    scopes[0].update(outer=outer, inner=inner)

    assert chevron.render("{{outer}}", scopes=scopes) == "1"
    assert len(scopes) == 1


@pytest.mark.parametrize("template", ["literal", "{{missing}}"])
def test_empty_scopes_are_a_valid_empty_context(template: str) -> None:
    assert chevron.render(template, scopes=[]) == (
        "literal" if template == "literal" else ""
    )


@pytest.mark.parametrize("scopes", ["text", b"bytes", {"name": "value"}])
def test_scopes_reject_non_sequence_containers(scopes: object) -> None:
    with pytest.raises(TypeError, match="scopes must be a sequence"):
        chevron.render("{{name}}", scopes=scopes)


@pytest.mark.parametrize("tag", ["{{{.}}}", "{{& .}}"])
def test_unescaped_current_scope_in_inverted_section_uses_the_parent_scope(
    tag: str,
) -> None:
    assert (
        chevron.render(f"{{{{^missing}}}}{tag}{{{{/missing}}}}", "context") == "context"
    )


@pytest.mark.parametrize("tag", ["{{.}}", "{{{.}}}", "{{& .}}"])
def test_true_current_scope_is_not_an_inverted_section_marker(tag: str) -> None:
    assert chevron.render(f"{{{{^missing}}}}{tag}{{{{/missing}}}}", True) == "True"


@pytest.mark.parametrize("tag", ["{{.}}", "{{{.}}}", "{{& .}}"])
def test_nested_inverted_sections_resolve_current_scope(tag: str) -> None:
    assert (
        chevron.render(
            "{{^missing}}{{^other}}" + tag + "{{/other}}{{/missing}}",
            "context",
        )
        == "context"
    )


def test_nested_inverted_sections_resolve_current_scope_sections() -> None:
    assert (
        chevron.render(
            "{{^missing}}{{^other}}{{#.}}{{.}}{{/.}}{{/other}}{{/missing}}",
            "context",
        )
        == "context"
    )


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("count.0", "5"),
        ("count.1", "4"),
        ("count.100", ""),
        ("missing.0", ""),
    ],
)
def test_dotted_sequence_lookup_resolves_indices_or_renders_empty(
    name: str, expected: str
) -> None:
    assert chevron.render("{{%s}}" % name, {"count": [5, 4, 3, 2, 1]}) == expected


def test_numeric_lookup_falls_back_past_a_scalar_section_frame() -> None:
    assert (
        chevron.render("{{#items}}{{0}}{{/items}}", {"items": [1], "0": "outer value"})
        == "outer value"
    )


def test_numeric_lookup_falls_back_past_an_inverted_section_marker() -> None:
    assert (
        chevron.render("{{^flag}}{{0}}{{/flag}}", {"flag": False, "0": "outer value"})
        == "outer value"
    )


def test_sync_render_rejects_async_iterable_sections() -> None:
    async def values():
        yield "value"

    with pytest.raises(TypeError, match="use chevron.async_render"):
        chevron.render("{{#values}}{{.}}{{/values}}", {"values": values()})


def test_namedtuple_fields_are_template_values() -> None:
    Coordinates = namedtuple("Coordinates", ["x", "y"])

    assert chevron.render("{{x}} {{y}}", Coordinates("hello", "world")) == "hello world"


def test_public_class_attributes_are_template_values() -> None:
    class Data:
        value = "visible"

    assert chevron.render("{{value}}", Data()) == "visible"


def test_builtin_callable_attributes_are_not_template_values() -> None:
    assert chevron.render("{{title}}", "an ordinary string") == ""
