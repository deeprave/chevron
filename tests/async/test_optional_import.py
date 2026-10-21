"""Optional async-runtime boundaries."""

import subprocess
import sys
from textwrap import dedent


def test_async_engine_loads_only_when_async_render_is_awaited() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            dedent(
                """
                import asyncio
                import sys

                import chevron

                assert "anyio" not in sys.modules
                assert "chevron.async_renderer" not in sys.modules
                assert asyncio.run(chevron.async_render("text")) == "text"
                assert "anyio" in sys.modules
                assert "chevron.async_renderer" in sys.modules
                """
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_async_render_explains_how_to_install_anyio() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            dedent(
                """
                import asyncio
                import builtins

                original_import = builtins.__import__

                def blocked_import(name, *args, **kwargs):
                    if name == "anyio":
                        raise ModuleNotFoundError(
                            "No module named 'anyio'", name="anyio"
                        )
                    return original_import(name, *args, **kwargs)

                builtins.__import__ = blocked_import

                import chevron

                async def main():
                    try:
                        await chevron.async_render("text")
                    except RuntimeError as error:
                        assert "chevron-ng[anyio]" in str(error)
                    else:
                        raise AssertionError("async_render unexpectedly succeeded")

                asyncio.run(main())
                """
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
