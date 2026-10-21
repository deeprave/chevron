"""Minimal contract coverage for declared async dependency floors."""

import os

import anyio
import pytest

import chevron


@pytest.mark.anyio
@pytest.mark.parametrize(
    "anyio_backend", [os.environ.get("CHEVRON_ANYIO_BACKEND", "asyncio")]
)
async def test_async_rendering_compatibility_contract(
    anyio_backend: str, tmp_path
) -> None:
    @chevron.func
    async def greeting() -> str:
        return "{{name}}"

    async def names():
        yield {"name": "Ada"}

    assert (
        await chevron.async_render(
            "{{greeting}} {{#people}}{{name}}{{/people}}",
            {"name": "Hello", "people": names()},
            lambdas={"greeting": greeting},
        )
        == "Hello Ada"
    )

    class OrdinaryReader:
        def read(self) -> str:
            return "ordinary {{name}}"

    class AsyncReader:
        async def read(self) -> str:
            return "async {{name}}"

    assert (
        await chevron.async_render(OrdinaryReader(), {"name": "reader"})
        == "ordinary reader"
    )
    assert (
        await chevron.async_render(AsyncReader(), {"name": "reader"}) == "async reader"
    )

    (tmp_path / "part.mustache").write_text("partial {{name}}", encoding="utf-8")
    (tmp_path.parent / "outside.mustache").write_text("outside", encoding="utf-8")
    assert (
        await chevron.async_render(
            "{{>part}}|{{>../outside}}", {"name": "reader"}, partials_path=tmp_path
        )
        == "partial reader|"
    )

    @chevron.compat
    async def compatibility(body: str, render) -> str:
        return await render(body, {"name": "callback"})

    assert (
        await chevron.async_render(
            "{{#compatibility}}{{name}}{{/compatibility}}",
            lambdas={"compatibility": compatibility},
        )
        == "callback"
    )

    started = anyio.Event()

    @chevron.func
    async def waiting() -> str:
        started.set()
        await anyio.sleep_forever()

    async def render_waiting() -> None:
        await chevron.async_render("{{waiting}}", lambdas={"waiting": waiting})

    async with anyio.create_task_group() as tasks:
        tasks.start_soon(render_waiting)
        await started.wait()
        tasks.cancel_scope.cancel()
