"""Regression tests for Chevron's public import interface."""

import sys

import chevron


def test_public_exports_are_available() -> None:
    assert chevron.__all__ == ["main", "render", "cli_main", "ChevronError"]
    assert callable(chevron.main)
    assert callable(chevron.render)
    assert callable(chevron.cli_main)
    assert issubclass(chevron.ChevronError, SyntaxError)


def test_render_remains_available_from_the_package_root() -> None:
    assert chevron.render("Hello, {{name}}!", {"name": "World"}) == "Hello, World!"


def test_cli_renders_template_without_data_file(tmp_path, monkeypatch, capsys) -> None:
    template_path = tmp_path / "greeting.mustache"
    template_path.write_text("Hello, World!", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["chevron", str(template_path)])

    chevron.cli_main()

    assert capsys.readouterr().out == "Hello, World!"
