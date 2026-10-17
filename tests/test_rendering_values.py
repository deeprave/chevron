import pytest

import chevron


@pytest.mark.parametrize(
    ("template", "data", "expected"),
    [
        ("(╯°□°）╯︵ ┻━┻", {}, "(╯°□°）╯︵ ┻━┻"),
        ("{{table_flip}}", {"table_flip": "(╯°□°）╯︵ ┻━┻"}, "(╯°□°）╯︵ ┻━┻"),
    ],
    ids=["literal", "interpolation"],
)
def test_unicode_text_renders_unchanged(
    template: str, data: dict[str, str], expected: str
) -> None:
    assert chevron.render(template, data) == expected


def test_custom_falsey_values_can_opt_into_rendering() -> None:
    class LowercaseBool:
        _CHEVRON_return_scope_when_falsy = True

        def __init__(self, value: bool) -> None:
            self.value = value

        def __bool__(self) -> bool:
            return self.value

        def __str__(self) -> str:
            return str(self.value).lower()

    class CustomData(dict[str, object]):
        def __getitem__(self, key: str) -> object:
            item = super().__getitem__(key)
            return LowercaseBool(item) if isinstance(item, bool) else item

    assert (
        chevron.render(
            "{{truthy}} {{falsy}}",
            CustomData({"truthy": True, "falsy": False}),
        )
        == "true false"
    )
