"""Typed case support for Chevron-owned source-template behavior tests."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


LambdaMapping = Mapping[str, Any]
LambdaFactory = Callable[[], LambdaMapping]


def _empty_lambdas() -> LambdaMapping:
    return {}


@dataclass(frozen=True)
class RenderCase:
    """One named public rendering scenario reusable by sync and async tests."""

    name: str
    template: str
    expected: str
    data: Any = field(default_factory=dict)
    partials: Mapping[str, str] = field(default_factory=dict)
    scopes: Sequence[Any] | None = None
    initial_delimiters: tuple[str, str] = ("{{", "}}")
    data_factory: Callable[[], Any] | None = None

    def render_data(self) -> Any:
        """Return fresh data when a case owns a consumable value."""
        return self.data_factory() if self.data_factory is not None else self.data


@dataclass(frozen=True)
class LambdaRenderCase(RenderCase):
    """A rendering case with a fresh mapping of declared lambda protocols."""

    lambdas_factory: LambdaFactory = _empty_lambdas

    def render_lambdas(self) -> LambdaMapping:
        """Create lambda state isolated to this one render."""
        return self.lambdas_factory()


@dataclass(frozen=True)
class FilesystemPartialRenderCase(RenderCase):
    """A rendering case with a temporary tree of ordinary partial files."""

    filesystem_partials: Mapping[str, str] = field(default_factory=dict)
    partials_ext: str = "mustache"

    def materialise_partials(self, root: Path) -> None:
        """Write the declared relative partial files under a temporary root."""
        for relative_path, content in self.filesystem_partials.items():
            partial_path = root / relative_path
            partial_path.parent.mkdir(parents=True, exist_ok=True)
            partial_path.write_text(content, encoding="utf-8")
