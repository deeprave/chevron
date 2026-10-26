"""Shared AnyIO backend selection for async tests."""

from importlib.util import find_spec


ANYIO_BACKENDS = ["asyncio"]
if find_spec("trio") is not None:
    ANYIO_BACKENDS.append("trio")
