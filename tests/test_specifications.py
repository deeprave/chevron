"""Conformance tests from the vendored Mustache specification fixtures."""

import pytest
from typing import cast

import chevron
from specification_fixtures import (
    declare_fixture_lambda,
    fixture_cases,
    materialise_lambdas,
)


@pytest.mark.parametrize("case", fixture_cases())
def test_mustache_specification_case(case: dict[str, object]) -> None:
    namespace: dict[str, object] = {}
    data = declare_fixture_lambda(case, materialise_lambdas(case["data"], namespace))
    result = chevron.render(
        cast(str, case["template"]),
        data,
        partials_dict=cast(dict[str, object], case.get("partials", {})),
    )

    assert result == case["expected"]
