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


def test_namedtuple_fields_are_template_values() -> None:
    Coordinates = namedtuple("Coordinates", ["x", "y"])

    assert chevron.render("{{x}} {{y}}", Coordinates("hello", "world")) == "hello world"


def test_public_class_attributes_are_template_values() -> None:
    class Data:
        value = "visible"

    assert chevron.render("{{value}}", Data()) == "visible"


def test_builtin_callable_attributes_are_not_template_values() -> None:
    assert chevron.render("{{title}}", "an ordinary string") == ""
