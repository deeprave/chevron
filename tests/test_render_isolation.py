from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

import chevron
from chevron.tokenizer import tokenize


@pytest.mark.parametrize("explicit", [False, True])
def test_concurrent_renders_keep_callback_scopes_independent(explicit: bool) -> None:
    barrier = Barrier(2)

    def render_name(name: str) -> str:
        def callback(text, render):
            barrier.wait(timeout=5)
            return render(text, {"name": name})

        options = {"lambdas": {"callback": callback}} if explicit else {}
        return chevron.render(
            "{{#callback}}{{name}}{{/callback}}|{{name}}",
            {"callback": callback, "name": "outer"},
            **options,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert list(executor.map(render_name, ["first", "second"])) == [
            "first|outer",
            "second|outer",
        ]


@pytest.mark.parametrize("include_raw", [False, True])
@pytest.mark.parametrize("decorator", [chevron.section, chevron.compat])
def test_section_callbacks_render_both_token_representations(
    include_raw: bool, decorator
) -> None:
    def standard(text):
        return text

    def compatible(text, render):
        return render(text)

    callback = decorator(standard if decorator is chevron.section else compatible)
    template = "{{#call}}A{{name}}{{{name}}}{{>part}}{{/call}}"
    assert (
        chevron.render(
            list(tokenize(template, include_raw=include_raw)),
            {"name": "B"},
            partials_dict={"part": "C"},
            lambdas={"call": callback},
        )
        == "ABBC"
    )
