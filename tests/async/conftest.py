"""Collect async tests only when their optional runtime is installed."""

from importlib.util import find_spec


collect_ignore_glob = ["test_*.py"] if find_spec("anyio") is None else []
