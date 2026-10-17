import chevron


def test_unicode_partial_content_renders_unchanged() -> None:
    assert (
        chevron.render(
            "{{>table_flip}}", partials_dict={"table_flip": "(╯°□°）╯︵ ┻━┻"}
        )
        == "(╯°□°）╯︵ ┻━┻"
    )


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
