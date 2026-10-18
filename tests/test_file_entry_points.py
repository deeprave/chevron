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
