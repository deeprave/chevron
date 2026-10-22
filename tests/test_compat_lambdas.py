import chevron
from typing import Any


def test_compatibility_callback_receives_normalised_section_text() -> None:
    received: list[str] = []

    def callback(text: str, render: Any) -> str:
        received.append(text)
        return "rendered"

    assert (
        chevron.render(
            "{{#callback}}{{{city}}} || {{{town}}}{{/callback}}",
            {"callback": callback, "city": "Mustache City"},
        )
        == "rendered"
    )
    assert received == ["{{& city }} || {{& town }}"]


def test_compatibility_callback_can_render_a_configured_partial() -> None:
    def callback(text: str, render: Any) -> str:
        return render(text)

    assert (
        chevron.render(
            "{{#callback}}{{>partial}}{{!comment}}{{/callback}}",
            {"callback": callback},
            partials_dict={"partial": "partial content"},
        )
        == "partial content"
    )
