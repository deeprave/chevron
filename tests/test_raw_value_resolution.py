import pytest
from typing import Any

import chevron


class FalseyCallable:
    def __bool__(self) -> bool:
        return False

    def __call__(self, text: str, render: object) -> str:
        return "called"


class FailingString:
    def __str__(self) -> str:
        raise RuntimeError("render failed")


@pytest.mark.parametrize(
    ("template", "data"),
    [
        ("{{#callback}}body{{/callback}}", {"callback": FalseyCallable()}),
        (
            "{{#items}}{{#.}}body{{/.}}{{/items}}",
            {"items": [FalseyCallable()]},
        ),
    ],
)
def test_falsey_legacy_callable_section_executes(template: str, data: dict) -> None:
    assert chevron.render(template, data) == "called"


def test_falsey_template_callable_is_rejected_in_explicit_mode(caplog) -> None:
    assert (
        chevron.render(
            "{{#callback}}body{{/callback}}",
            {"callback": FalseyCallable()},
            lambdas={},
            warn=True,
        )
        == ""
    )
    assert caplog.messages == [
        "Callable template data 'callback' is rejected when lambdas= is supplied"
    ]


def test_falsey_registered_callable_section_executes() -> None:
    callback = FalseyCallable()

    assert (
        chevron.render(
            "{{#callback}}body{{/callback}}",
            {"callback": callback},
            lambdas={"callback": callback},
        )
        == "called"
    )


@pytest.mark.parametrize("template", ["{{missing}}", "{{{missing}}}"])
def test_missing_interpolation_renders_empty_and_warns(template: str, caplog) -> None:
    assert chevron.render(template, {}, warn=True) == ""
    assert caplog.messages == ["Could not find key 'missing'"]


@pytest.mark.parametrize("explicit_lambdas", [False, True])
def test_recovered_nested_render_failure_does_not_leak_temporary_scope(
    explicit_lambdas: bool,
) -> None:
    def callback(text: str, render: Any) -> str:
        try:
            render("{{#temporary}}{{bad}}{{/temporary}}")
        except RuntimeError:
            return render("{{name}}")
        raise AssertionError("nested render should fail")

    data = {
        "callback": callback,
        "name": "fresh",
        "temporary": {"name": "stale", "bad": FailingString()},
    }
    result = (
        chevron.render(
            "{{#callback}}body{{/callback}}", data, lambdas={"callback": callback}
        )
        if explicit_lambdas
        else chevron.render("{{#callback}}body{{/callback}}", data)
    )

    assert result == "fresh"
