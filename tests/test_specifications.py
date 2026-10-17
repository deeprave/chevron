"""Conformance tests from the vendored Mustache specification fixtures."""

import json
from pathlib import Path

import pytest

import chevron

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "mustache-spec"


def _fixture_cases() -> list[object]:
    cases = []
    for fixture_path in sorted(FIXTURE_PATH.glob("*.json")):
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        for case in fixture["tests"]:
            cases.append(
                pytest.param(
                    case, id=f"{fixture_path.stem.lstrip('~')}::{case['name']}"
                )
            )
    return cases


def _materialise_lambdas(value: object, namespace: dict[str, object]) -> object:
    if isinstance(value, dict):
        if value.get("__tag__") == "code":
            # Fixtures are pinned, reviewed Python source from mustache/spec.
            return eval(value["python"], namespace)
        return {
            key: _materialise_lambdas(item, namespace) for key, item in value.items()
        }
    if isinstance(value, list):
        return [_materialise_lambdas(item, namespace) for item in value]
    return value


def _declare_fixture_lambda(case: dict[str, object], data: object) -> object:
    """Adapt reviewed fixture callbacks to Chevron's declared protocols."""

    if not isinstance(data, dict) or not callable(data.get("lambda")):
        return data

    name = case["name"]
    callback = data["lambda"]
    if name.startswith("Interpolation") or name == "Escaping":
        data["lambda"] = chevron.func(callback)
    elif name.startswith("Section"):
        data["lambda"] = chevron.section(callback)
    return data


@pytest.mark.parametrize("case", _fixture_cases())
def test_mustache_specification_case(case: dict[str, object]) -> None:
    namespace: dict[str, object] = {}
    data = _declare_fixture_lambda(case, _materialise_lambdas(case["data"], namespace))
    result = chevron.render(
        case["template"],
        data,
        partials_dict=case.get("partials", {}),
    )

    assert result == case["expected"]
