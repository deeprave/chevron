from pathlib import Path

import pytest

import chevron


FIXTURE_PATH = Path(__file__).parent / "fixtures"


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
