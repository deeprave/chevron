import chevron
import pytest
from collections import ChainMap
from types import MappingProxyType
from typing import Any


def test_explicit_mapping_invokes_the_exact_registered_callable() -> None:
    calls: list[str] = []

    def registered(text: str, render: Any) -> str:
        calls.append(text)
        return "registered"

    result = chevron.render(
        "{{#action}}ignored{{/action}}",
        {"action": registered},
        lambdas={"action": registered},
    )

    assert result == "registered"
    assert calls == ["ignored"]


def test_explicit_mapping_does_not_invoke_an_unregistered_callable() -> None:
    calls: list[str] = []

    def unregistered(text: str, render: object) -> str:
        calls.append(text)
        return "should not render"

    result = chevron.render(
        "{{#action}}body{{/action}}",
        {"action": unregistered},
        lambdas={},
    )

    assert result == ""
    assert calls == []


@pytest.mark.parametrize("template", ["{{action}}", "{{{action}}}"])
def test_explicit_mode_rejects_callable_template_data_in_interpolation(
    template: str, caplog
) -> None:
    def action(text: str, render: object) -> str:
        return "called"

    assert chevron.render(template, {"action": action}, lambdas={}, warn=True) == ""
    assert caplog.messages == [
        "Callable template data 'action' is rejected when lambdas= is supplied"
    ]


def test_explicit_mode_keeps_non_callable_template_data() -> None:
    assert chevron.render("{{action}}", {"action": "data"}, lambdas={}) == "data"


def test_explicit_mapping_shadows_callable_template_data() -> None:
    calls: list[str] = []

    def registered(text: str, render: Any) -> str:
        calls.append("registered")
        return "registered"

    def shadowing(text: str, render: object) -> str:
        calls.append("shadowing")
        return "shadowing"

    result = chevron.render(
        "{{#action}}body{{/action}}",
        {"action": shadowing},
        lambdas={"action": registered},
    )

    assert result == "registered"
    assert calls == ["registered"]


def test_explicit_mapping_supplies_a_section_callable() -> None:
    def registered(text: str, render: Any) -> str:
        return "registered"

    result = chevron.render(
        "{{#action}}body{{/action}}",
        {},
        lambdas={"action": registered},
    )

    assert result == "registered"


def test_explicit_mapping_supports_dotted_names_and_partials() -> None:
    def registered(text: str, render: Any) -> str:
        return render(text)

    result = chevron.render(
        "{{> included}}",
        {"workflow": {"contains": registered}, "value": "rendered"},
        partials_dict={
            "included": "{{#workflow.contains}}{{value}}{{/workflow.contains}}"
        },
        lambdas={"workflow.contains": registered},
    )

    assert result == "rendered"


def test_explicit_mapping_requires_the_complete_dotted_name() -> None:
    calls: list[str] = []

    def callback(text: str, render: object) -> str:
        calls.append(text)
        return "called"

    assert (
        chevron.render(
            "{{#workflow.contains}}body{{/workflow.contains}}",
            {"workflow": {"contains": callback}},
            lambdas={"contains": callback},
        )
        == ""
    )
    assert calls == []


def test_explicit_mapping_survives_iterable_section_scopes() -> None:
    def registered(text: str, render: Any) -> str:
        return render(text)

    result = chevron.render(
        "{{#items}}{{#action}}{{value}}{{/action}}{{/items}}",
        {"items": [{"action": registered, "value": "first"}]},
        lambdas={"action": registered},
    )

    assert result == "first"


def test_omitted_lambda_mapping_preserves_legacy_section_callbacks() -> None:
    def legacy(text: str, render: Any) -> str:
        return render(text)

    result = chevron.render(
        "{{#legacy}}{{value}}{{/legacy}}",
        {"legacy": legacy, "value": "rendered"},
    )

    assert result == "rendered"


def test_legacy_callback_render_accepts_temporary_data() -> None:
    def legacy(text: str, render: Any) -> str:
        return render(text, {"value": "temporary"})

    result = chevron.render(
        "{{#legacy}}{{value}}{{/legacy}}",
        {"legacy": legacy, "value": "outer"},
    )

    assert result == "temporary"


def test_legacy_scope_argument_retains_section_callback_compatibility() -> None:
    def legacy(text: str, render: Any) -> str:
        return render(text)

    result = chevron.render(
        "{{#legacy}}{{value}}{{/legacy}}",
        scopes=[{"legacy": legacy, "value": "rendered"}],
    )

    assert result == "rendered"


def test_legacy_mode_authorises_an_aliased_mapping_at_each_dotted_path() -> None:
    def legacy(text: str, render: object) -> str:
        return "called"

    shared = {"fn": legacy}

    result = chevron.render(
        "{{#b.fn}}body{{/b.fn}}",
        {"a": shared, "b": shared},
    )

    assert result == "called"


def test_explicit_mode_does_not_iterate_unused_template_data() -> None:
    class NonIterableData(dict):
        def items(self):
            raise AssertionError("explicit lambda mode must not inspect template data")

    assert chevron.render("literal", NonIterableData(), lambdas={}) == "literal"


def test_legacy_mode_authorises_callable_in_tuple_backed_path() -> None:
    def legacy(text: str, render: object) -> str:
        return "called"

    result = chevron.render(
        "{{#items.0.fn}}body{{/items.0.fn}}",
        {"items": ({"fn": legacy},)},
    )

    assert result == "called"


def test_legacy_mode_renders_literal_with_deep_unused_data() -> None:
    data: dict[str, object] = {}
    current = data
    for _ in range(1_100):
        child: dict[str, object] = {}
        current["child"] = child
        current = child

    assert chevron.render("literal", data) == "literal"


def test_rejected_callable_does_not_become_the_section_scope() -> None:
    class Handler:
        secret = "secret"

        def action(self, text: str, render: object) -> str:
            return "called"

    assert (
        chevron.render(
            "{{#action}}{{__self__.secret}}{{/action}}",
            {"action": Handler().action},
            lambdas={},
        )
        == ""
    )


def test_legacy_mode_invokes_a_callable_current_scope() -> None:
    def legacy(text: str, render: object) -> str:
        return "called"

    assert (
        chevron.render("{{#items}}{{#.}}body{{/.}}{{/items}}", {"items": [legacy]})
        == "called"
    )


def test_legacy_mode_prefers_nested_lookup_over_literal_dotted_key() -> None:
    def nested(text: str, render: object) -> str:
        return "nested"

    def literal(text: str, render: object) -> str:
        return "literal"

    assert (
        chevron.render(
            "{{#a.b}}body{{/a.b}}",
            {"a": {"b": nested}, "a.b": literal},
        )
        == "nested"
    )


def test_legacy_callback_preserves_explicit_lambda_restrictions() -> None:
    calls: list[str] = []

    def outer(text: str, render: Any) -> str:
        calls.append("outer")
        return render(text, {"inner": inner})

    def inner(text: str, render: object) -> str:
        calls.append("inner")
        return "called"

    assert (
        chevron.render(
            "{{#outer}}{{#inner}}body{{/inner}}{{/outer}}",
            {"outer": outer},
            lambdas={"outer": outer},
        )
        == ""
    )
    assert calls == ["outer"]


def test_legacy_mode_resolves_a_callable_through_a_cyclic_mapping() -> None:
    def legacy(text: str, render: object) -> str:
        return "called"

    data = {"fn": legacy}
    data["self"] = data

    assert chevron.render("{{#self.fn}}body{{/self.fn}}", data) == "called"


def test_legacy_mode_does_not_inspect_unused_custom_mapping() -> None:
    class NonIterableData(dict):
        def items(self):
            raise AssertionError("unused data must not be inspected")

    assert chevron.render("literal", {"unused": NonIterableData()}) == "literal"


def test_public_render_does_not_accept_private_context() -> None:
    with pytest.raises(TypeError):
        chevron.render("literal", _context=object())  # ty: ignore[unknown-argument]


def test_legacy_mode_invokes_a_callable_after_an_object_attribute_mapping() -> None:
    def legacy(text: str, render: object) -> str:
        return "called"

    class Workflow:
        helpers = {"contains": legacy}

    assert (
        chevron.render(
            "{{#workflow.helpers.contains}}body{{/workflow.helpers.contains}}",
            {"workflow": Workflow()},
        )
        == "called"
    )


def test_legacy_mode_invokes_a_callable_after_an_object_attribute_sequence() -> None:
    def legacy(text: str, render: object) -> str:
        return "called"

    class Workflow:
        helpers = (legacy,)

    assert (
        chevron.render(
            "{{#workflow.helpers.0}}body{{/workflow.helpers.0}}",
            {"workflow": Workflow()},
        )
        == "called"
    )


def test_explicit_mode_rejects_unregistered_callable_in_a_partial() -> None:
    calls: list[str] = []

    def unregistered(text: str, render: object) -> str:
        calls.append(text)
        return "called"

    assert (
        chevron.render(
            "{{> partial}}",
            {"inner": unregistered},
            partials_dict={"partial": "{{#inner}}body{{/inner}}"},
            lambdas={},
        )
        == ""
    )
    assert calls == []


def test_explicit_mapping_shadows_callable_iterable_data() -> None:
    calls: list[str] = []

    def registered(text: str, render: object) -> str:
        calls.append("registered")
        return "registered"

    def shadowing(text: str, render: object) -> str:
        calls.append("shadowing")
        return "shadowing"

    assert (
        chevron.render(
            "{{#items}}{{#action}}body{{/action}}{{/items}}",
            {"action": registered, "items": [{"action": shadowing}]},
            lambdas={"action": registered},
        )
        == "registered"
    )
    assert calls == ["registered"]


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ("{{callback.__closure__.0.cell_contents}}", ""),
        ("{{{callback.__closure__.0.cell_contents}}}", ""),
        (
            "{{#callback.__closure__.0.cell_contents}}body{{/callback.__closure__.0.cell_contents}}",
            "",
        ),
        (
            "{{^callback.__closure__.0.cell_contents}}fallback{{/callback.__closure__.0.cell_contents}}",
            "fallback",
        ),
    ],
)
def test_explicit_mode_treats_callable_internals_as_missing(
    template: str, expected: str
) -> None:
    secret = "secret"

    def callback(text: str, render: object) -> str:
        return secret

    assert (
        chevron.render(
            template,
            {"callback": callback},
            lambdas={"callback": callback},
        )
        == expected
    )


def test_explicit_mode_treats_callable_iterable_scope_internals_as_missing() -> None:
    secret = "secret"

    def callback(text: str, render: object) -> str:
        return secret

    assert (
        chevron.render(
            "{{#callbacks}}{{__closure__.0.cell_contents}}{{/callbacks}}",
            {"callbacks": [callback]},
            lambdas={},
        )
        == ""
    )


def test_explicit_mode_renders_an_unregistered_callable_as_missing(caplog) -> None:
    def callback(text: str, render: object) -> str:
        return "called"

    assert (
        chevron.render(
            "{{#callback}}body{{/callback}}",
            {"callback": callback},
            lambdas={},
            warn=True,
        )
        == ""
    )
    assert caplog.messages == [
        "Callable template data 'callback' is rejected when lambdas= is supplied"
    ]
    assert (
        chevron.render(
            "{{^callback}}fallback{{/callback}}",
            {"callback": callback},
            lambdas={},
        )
        == "fallback"
    )


def test_explicit_mode_accepts_separately_accessed_bound_methods() -> None:
    class Handler:
        def action(self, text: str, render: object) -> str:
            return "called"

    handler = Handler()

    assert (
        chevron.render(
            "{{#action}}body{{/action}}",
            {"action": handler.action},
            lambdas={"action": handler.action},
        )
        == "called"
    )


def test_explicit_mapping_uses_a_bound_method_without_template_data() -> None:
    class Handler:
        def action(self, text: str, render: object) -> str:
            return "called"

    assert (
        chevron.render(
            "{{#action}}body{{/action}}",
            {},
            lambdas={"action": Handler().action},
        )
        == "called"
    )


def test_explicit_mapping_shadows_a_different_bound_method() -> None:
    calls: list[str] = []

    class Handler:
        def permitted(self, text: str, render: object) -> str:
            calls.append("permitted")
            return "permitted"

        def rejected(self, text: str, render: object) -> str:
            calls.append("rejected")
            return "rejected"

    handler = Handler()

    assert (
        chevron.render(
            "{{#action}}body{{/action}}",
            {"action": handler.rejected},
            lambdas={"action": handler.permitted},
        )
        == "permitted"
    )
    assert calls == ["permitted"]


@pytest.mark.parametrize(
    "lambdas",
    [[], {"action": "not callable"}, {1: lambda text, render: "called"}],
)
def test_explicit_mode_rejects_invalid_lambda_mappings(lambdas: object) -> None:
    with pytest.raises(TypeError, match="lambdas"):
        chevron.render("literal", lambdas=lambdas)  # ty: ignore[invalid-argument-type]


def test_legacy_callback_can_introduce_a_temporary_callable() -> None:
    def inner(text: str, render: object) -> str:
        return "called"

    def outer(text: str, render: Any) -> str:
        return render(text, {"inner": inner})

    assert (
        chevron.render(
            "{{#outer}}{{#inner}}body{{/inner}}{{/outer}}",
            {"outer": outer},
        )
        == "called"
    )


def test_explicit_mode_treats_callable_classes_as_lookup_leaves() -> None:
    class Build:
        version = "0.15.0"

    assert chevron.render("{{build.version}}", {"build": Build}, lambdas={}) == ""


def test_explicit_mode_treats_callable_instances_as_lookup_leaves() -> None:
    class Build:
        version = "0.15.0"

        def __call__(self) -> str:
            return "build"

    assert chevron.render("{{build.version}}", {"build": Build()}, lambdas={}) == ""


def test_lambdas_none_retains_compatibility_mode() -> None:
    def callback(text: str, render: object) -> str:
        return "called"

    assert (
        chevron.render(
            "{{#callback}}body{{/callback}}", {"callback": callback}, lambdas=None
        )
        == "called"
    )


def test_explicit_mapping_works_with_scopes_argument() -> None:
    def callback(text: str, render: object) -> str:
        return "called"

    assert (
        chevron.render(
            "{{#callback}}body{{/callback}}",
            scopes=[{"callback": callback}],
            lambdas={"callback": callback},
        )
        == "called"
    )


def test_explicit_mapping_accepts_class_bound_methods() -> None:
    class Handler:
        @classmethod
        def action(cls, text: str, render: object) -> str:
            return "called"

    assert (
        chevron.render(
            "{{#action}}body{{/action}}",
            {"action": Handler.action},
            lambdas={"action": Handler.action},
        )
        == "called"
    )


@pytest.mark.parametrize(
    "mapping_factory", [lambda value: ChainMap(value), MappingProxyType]
)
def test_explicit_mapping_accepts_mapping_implementations(mapping_factory) -> None:
    def callback(text: str, render: object) -> str:
        return "called"

    assert (
        chevron.render(
            "{{#callback}}body{{/callback}}",
            {"callback": callback},
            lambdas=mapping_factory({"callback": callback}),
        )
        == "called"
    )


def test_registered_callable_is_truthy_in_an_inverted_section() -> None:
    def callback(text: str, render: object) -> str:
        return "called"

    assert (
        chevron.render(
            "{{^callback}}fallback{{/callback}}",
            {"callback": callback},
            lambdas={"callback": callback},
        )
        == ""
    )


def test_explicit_mapping_precedes_scope_precedence() -> None:
    def outer(text: str, render: object) -> str:
        return "outer"

    def inner(text: str, render: object) -> str:
        return "inner"

    assert (
        chevron.render(
            "{{#action}}body{{/action}}",
            scopes=[{"action": inner}, {"action": outer}],
            lambdas={"action": outer},
        )
        == "outer"
    )


def test_lambda_mapping_is_snapshotted_for_a_render() -> None:
    mapping: dict[str, Any] = {}

    def inner(text: str, render: object) -> str:
        return "inner"

    def outer(text: str, render: Any) -> str:
        mapping["inner"] = inner
        return render(text)

    mapping["outer"] = outer
    assert (
        chevron.render(
            "{{#outer}}{{#inner}}body{{/inner}}{{/outer}}",
            {"outer": outer, "inner": inner},
            lambdas=mapping,
        )
        == ""
    )


def test_warning_identifies_rejected_callable_template_data(caplog) -> None:
    def resolved(text: str, render: object) -> str:
        return "resolved"

    assert (
        chevron.render(
            "{{#action}}body{{/action}}",
            {"action": resolved},
            lambdas={},
            warn=True,
        )
        == ""
    )
    assert caplog.messages == [
        "Callable template data 'action' is rejected when lambdas= is supplied"
    ]


def test_inverted_section_warning_identifies_an_unregistered_callable(caplog) -> None:
    def callback(text: str, render: object) -> str:
        return "called"

    assert (
        chevron.render(
            "{{^callback}}fallback{{/callback}}",
            {"callback": callback},
            lambdas={},
            warn=True,
        )
        == "fallback"
    )
    assert caplog.messages == [
        "Callable template data 'callback' is rejected when lambdas= is supplied"
    ]


def test_warning_identifies_blocked_callable_traversal(caplog) -> None:
    class Build:
        version = "0.15.0"

    assert (
        chevron.render("{{build.version}}", {"build": Build}, lambdas={}, warn=True)
        == ""
    )
    assert caplog.messages == [
        "Could not resolve 'build.version': callable values cannot be traversed "
        "when lambdas= is supplied"
    ]


def test_library_default_does_not_load_filesystem_partials(
    monkeypatch, tmp_path
) -> None:
    (tmp_path / "secret.mustache").write_text("secret", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert chevron.render("{{> secret}}") == ""
    assert chevron.render("{{> secret}}", partials_path=".") == "secret"


def test_filesystem_partials_reject_parent_directory_traversal(tmp_path) -> None:
    partials_path = tmp_path / "partials"
    partials_path.mkdir()
    (tmp_path / "secret.mustache").write_text("secret", encoding="utf-8")

    assert chevron.render("{{> ../secret}}", partials_path=partials_path) == ""


def test_filesystem_partials_reject_absolute_names(tmp_path) -> None:
    partials_path = tmp_path / "partials"
    partials_path.mkdir()
    secret_name = tmp_path / "secret"
    secret_name.with_suffix(".mustache").write_text("secret", encoding="utf-8")

    assert (
        chevron.render(f"{{{{> {secret_name} }}}}", partials_path=partials_path) == ""
    )


def test_filesystem_partials_reject_escaping_nested_symlinks(tmp_path) -> None:
    partials_path = tmp_path / "partials"
    partials_path.mkdir()
    outside_path = tmp_path / "outside"
    outside_path.mkdir()
    (outside_path / "secret.mustache").write_text("secret", encoding="utf-8")
    (partials_path / "linked").symlink_to(outside_path, target_is_directory=True)

    assert chevron.render("{{> linked/secret}}", partials_path=partials_path) == ""


def test_filesystem_partials_allow_a_symlinked_root(tmp_path) -> None:
    partials_path = tmp_path / "partials"
    partials_path.mkdir()
    (partials_path / "included.mustache").write_text("included", encoding="utf-8")
    symlinked_root = tmp_path / "partial-root"
    symlinked_root.symlink_to(partials_path, target_is_directory=True)

    assert chevron.render("{{> included}}", partials_path=symlinked_root) == "included"
