"""Async conformance tests from the vendored Mustache fixtures."""

import pytest
from typing import cast

import chevron
from specification_fixtures import (
    declare_fixture_lambda,
    fixture_cases,
    materialise_lambdas,
)


pytestmark = pytest.mark.conformance


@pytest.mark.anyio
@pytest.mark.parametrize("case", fixture_cases())
async def test_async_mustache_specification_case(case: dict[str, object]) -> None:
    namespace: dict[str, object] = {}
    data = declare_fixture_lambda(case, materialise_lambdas(case["data"], namespace))

    result = await chevron.async_render(
        cast(str, case["template"]),
        data,
        partials_dict=cast(dict[str, object], case.get("partials", {})),
    )

    assert result == case["expected"]
