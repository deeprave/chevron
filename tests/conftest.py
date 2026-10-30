"""Shared test fixtures."""

from collections.abc import Callable

import pytest

from chevron import Extension
from chevron import extensions as extension_module


@pytest.fixture
def enable_extensions(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Configure the requested extensions for one test only."""
    monkeypatch.setattr(extension_module, "_enabled_extensions", Extension.NONE)
    monkeypatch.setattr(extension_module, "_extensions_frozen", False)

    def enable(*extensions: Extension) -> None:
        selected = Extension.NONE
        for extension in extensions:
            selected |= extension
        Extension.enable(selected)

    return enable
