from collections.abc import Callable
from io import StringIO
from pathlib import Path

import pytest

import chevron


FIXTURE_PATH = Path(__file__).parent / "fixtures"


def test_render_propagates_reader_failure_without_changing_scopes() -> None:
    class BrokenTemplate:
        def read(self) -> str:
            raise OSError("unable to read template")

    scopes = [{"name": "intact"}]
    with pytest.raises(OSError, match="unable to read template"):
        chevron.render(BrokenTemplate(), scopes=scopes)

    assert scopes == [{"name": "intact"}]
    assert chevron.render("{{name}}", scopes=scopes) == "intact"


def test_render_reads_from_current_position_and_leaves_reader_open() -> None:
    with StringIO("prefix Hello {{name}}") as source:
        source.seek(len("prefix "))
        assert chevron.render(source, {"name": "world"}) == chevron.render(
            "Hello {{name}}", {"name": "world"}
        )
        assert not source.closed
        assert source.read() == ""


def test_render_rejects_awaitable_reader_results_without_leaking_coroutines() -> None:
    class AsyncOnlyTemplate:
        coroutine = None

        def read(self):
            async def template() -> str:
                return "Hello"

            self.coroutine = template()
            return self.coroutine

    template = AsyncOnlyTemplate()
    with pytest.raises(TypeError, match="use chevron.async_render"):
        chevron.render(template)

    assert template.coroutine is not None
    assert template.coroutine.cr_frame is None


@pytest.mark.parametrize("template", [b"Hello", bytearray(b"Hello")])
def test_render_rejects_binary_template_input(template: object) -> None:
    with pytest.raises(TypeError, match="templates must be text"):
        chevron.render(template)


@pytest.mark.parametrize("template", [None, 0, False], ids=["none", "zero", "false"])
def test_render_preserves_falsey_non_text_templates_as_empty(template: object) -> None:
    assert chevron.render(template) == ""


@pytest.mark.parametrize("partial", [None, 0, False], ids=["none", "zero", "false"])
def test_render_preserves_falsey_partial_values_as_empty(partial: object) -> None:
    assert chevron.render(
        "before{{> optional}}after", partials_dict={"optional": partial}
    ) == ("beforeafter")


def test_compatibility_callback_can_render_none_as_empty() -> None:
    calls = []

    def callback(text: str, render: Callable[[object], str]) -> str:
        calls.append(text)
        return render(None)

    assert (
        chevron.render("{{#callback}}ignored{{/callback}}", {"callback": callback})
        == ""
    )
    assert calls == ["ignored"]


def test_compatibility_callback_can_render_unhashable_falsey_data_as_empty() -> None:
    def callback(text: str, render: Callable[[object], str]) -> str:
        return render({})

    assert (
        chevron.render("{{#callback}}ignored{{/callback}}", {"callback": callback})
        == ""
    )


@pytest.mark.parametrize("tokens", [("literal",), ("literal", "text", "raw", "extra")])
def test_render_rejects_malformed_token_tuples(tokens: tuple[str, ...]) -> None:
    with pytest.raises(TypeError, match="two or three values"):
        chevron.render([tokens])


@pytest.mark.parametrize("token", ["li", "raw"], ids=["two", "three"])
def test_render_rejects_string_tokens(token: str) -> None:
    with pytest.raises(TypeError, match="non-string sequences"):
        chevron.render([token])


def test_render_accepts_list_tokens() -> None:
    assert chevron.render([["literal", "text"]]) == "text"


def test_main_renders_template_data_and_filesystem_partials() -> None:
    assert chevron.main(
        FIXTURE_PATH / "test.mustache",
        FIXTURE_PATH / "data.json",
        partials_path=FIXTURE_PATH,
    ) == (FIXTURE_PATH / "test.rendered").read_text(encoding="utf-8")


@pytest.mark.parametrize("partials_path", [None, ""], ids=["none", "empty"])
def test_main_disables_filesystem_partials_when_path_is_not_configured(
    partials_path: str | None,
) -> None:
    assert chevron.main(
        FIXTURE_PATH / "test.mustache",
        FIXTURE_PATH / "data.json",
        partials_path=partials_path,
    ) == (FIXTURE_PATH / "test-partials-disabled.rendered").read_text(encoding="utf-8")
