"""Shared AnyIO backend selection for async tests."""

from importlib.util import find_spec

import pytest


ANYIO_BACKENDS = ["asyncio"]
if find_spec("trio") is not None:
    ANYIO_BACKENDS.append("trio")


@pytest.fixture(params=ANYIO_BACKENDS)
def anyio_backend(request: pytest.FixtureRequest) -> str:
    """Run ordinary async tests on every installed AnyIO backend."""
    return request.param
