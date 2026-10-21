"""Behavioural tests for Chevron's async public API."""

from io import StringIO
import logging

import pytest

import chevron
from async_support import ANYIO_BACKENDS
from chevron import ChevronError


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_renders_text_on_supported_backends(
    anyio_backend: str,
) -> None:
    assert await chevron.async_render("Hello, {{name}}!", {"name": "World"}) == (
        "Hello, World!"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("template", [b"Hello", bytearray(b"Hello")])
async def test_async_render_rejects_binary_template_input(
    anyio_backend: str, template: object
) -> None:
    with pytest.raises(TypeError, match="templates must be text"):
        await chevron.async_render(template)

    assert (
        await chevron.async_render(
            [("literal", "Hello, "), ("variable", "name"), ("literal", "!")],
            {"name": "World"},
        )
        == "Hello, World!"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_awaits_each_declared_lambda_protocol(
    anyio_backend: str,
) -> None:
    @chevron.func
    async def interpolation() -> str:
        return "{{name}}"

    @chevron.section
    async def section(body: str) -> str:
        return body

    @chevron.compat
    async def compatibility(body: str, render) -> str:
        return await render(body, {"name": "compatibility"})

    assert (
        await chevron.async_render(
            "{{interpolation}}|{{#section}}{{name}}{{/section}}|{{#compatibility}}{{name}}{{/compatibility}}",
            {"name": "declared"},
            lambdas={
                "interpolation": interpolation,
                "section": section,
                "compatibility": compatibility,
            },
        )
        == "declared|declared|compatibility"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_reads_async_templates_and_async_iterable_sections(
    anyio_backend: str,
) -> None:
    class AsyncTemplate:
        async def read(self) -> str:
            return "{{#items}}{{name}};{{/items}}"

    async def items():
        yield {"name": "first"}
        yield {"name": "second"}

    assert await chevron.async_render(AsyncTemplate(), {"items": items()}) == (
        "first;second;"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_awaits_awaitables_returned_by_synchronous_lambdas(
    anyio_backend: str,
) -> None:
    async def result() -> str:
        return "value"

    @chevron.func
    def value():
        return result()

    assert await chevron.async_render("{{value}}", lambdas={"value": value}) == "value"


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_function_matches_ordinary_interpolation_in_an_indented_partial(
    anyio_backend: str,
) -> None:
    @chevron.func
    async def value() -> str:
        return "a\nb"

    template = "  {{>part}}\n"
    partials = {"part": "{{value}}\n"}
    ordinary = await chevron.async_render(
        template,
        {"value": "a\nb"},
        partials_dict=partials,
    )
    interpolated = await chevron.async_render(
        template,
        partials_dict=partials,
        lambdas={"value": value},
    )

    assert interpolated == ordinary == "  a\nb\n"


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_does_not_invoke_awaitable_template_data_in_explicit_mode(
    anyio_backend: str,
) -> None:
    called = False

    async def value() -> str:
        nonlocal called
        called = True
        return "unexpected"

    assert await chevron.async_render("{{value}}", {"value": value}, lambdas={}) == ""
    assert not called


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_compatibility_callback_keeps_parent_scope_for_falsey_data(
    anyio_backend: str,
) -> None:
    @chevron.compat
    async def value(text: str, render) -> str:
        return await render(text, {})

    assert (
        await chevron.async_render(
            "{{#value}}{{message}}{{/value}}",
            {"message": "outer"},
            lambdas={"value": value},
        )
        == "outer"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_synchronous_compatibility_lambda_can_forward_the_awaitable_callback(
    anyio_backend: str,
) -> None:
    @chevron.compat
    def value(text: str, render):
        return render(text, {"message": "forwarded"})

    assert (
        await chevron.async_render(
            "{{#value}}{{message}}{{/value}}", lambdas={"value": value}
        )
        == "forwarded"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_compatibility_callback_can_recover_from_nested_errors(
    anyio_backend: str,
) -> None:
    @chevron.compat
    async def value(text: str, render) -> str:
        with pytest.raises(ChevronError):
            await render("{{#unclosed}}")
        return await render(text, {"message": "recovered"})

    assert (
        await chevron.async_render(
            "{{#value}}{{message}}{{/value}}", lambdas={"value": value}
        )
        == "recovered"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_propagates_lambda_errors_without_reinvoking(
    anyio_backend: str,
) -> None:
    calls = 0

    @chevron.func
    async def value() -> str:
        nonlocal calls
        calls += 1
        raise TypeError("application failure")

    with pytest.raises(TypeError, match="application failure"):
        await chevron.async_render("{{value}}", lambdas={"value": value})

    assert calls == 1


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_callable_instances_returning_none_render_empty(
    anyio_backend: str,
) -> None:
    class Empty:
        async def __call__(self) -> None:
            return None

    value = chevron.func(Empty())

    assert await chevron.async_render("{{value}}", lambdas={"value": value}) == ""


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_leaves_synchronous_template_readers_open(
    anyio_backend: str,
) -> None:
    with StringIO("prefix Hello {{name}}") as source:
        source.seek(len("prefix "))

        assert await chevron.async_render(source, {"name": "world"}) == "Hello world"
        assert not source.closed
        assert source.read() == ""


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("value", [None, 0, False])
async def test_async_ordinary_readers_preserve_falsey_sync_results(
    anyio_backend: str, value: object
) -> None:
    class FalseyTemplate:
        def read(self) -> object:
            return value

    assert await chevron.async_render(FalseyTemplate()) == ""


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_ordinary_readers_may_return_awaitable_text(
    anyio_backend: str,
) -> None:
    class AwaitableTemplate:
        def read(self):
            async def template() -> str:
                return "Hello {{name}}"

            return template()

    assert (
        await chevron.async_render(AwaitableTemplate(), {"name": "Ada"}) == "Hello Ada"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_cancelling_an_ordinary_reader_closes_its_unconsumed_awaitable(
    anyio_backend: str, monkeypatch
) -> None:
    import anyio

    from chevron import async_renderer

    checkpoint_started = anyio.Event()
    awaitable = None
    checkpoint_count = 0
    original_checkpoint = async_renderer.anyio.lowlevel.checkpoint

    class ReaderResult:
        closed = False

        def __await__(self):
            if False:
                yield None
            return "text"

        def close(self) -> None:
            self.closed = True

    class OrdinaryReader:
        def read(self) -> ReaderResult:
            nonlocal awaitable
            awaitable = ReaderResult()
            return awaitable

    async def blocked_checkpoint() -> None:
        nonlocal checkpoint_count
        checkpoint_count += 1
        if checkpoint_count == 2:
            checkpoint_started.set()
            await anyio.sleep_forever()
        await original_checkpoint()

    monkeypatch.setattr(async_renderer.anyio.lowlevel, "checkpoint", blocked_checkpoint)

    async def render_template() -> None:
        await chevron.async_render(OrdinaryReader())

    async with anyio.create_task_group() as tasks:
        tasks.start_soon(render_template)
        await checkpoint_started.wait()
        tasks.cancel_scope.cancel()

    assert awaitable is not None
    assert awaitable.closed


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("reader_kind", ["ordinary", "native"])
async def test_async_reader_results_must_be_text(
    anyio_backend: str, reader_kind: str
) -> None:
    if reader_kind == "ordinary":

        class InvalidTemplate:
            def read(self) -> int:
                return 1

    else:

        class InvalidTemplate:
            async def read(self) -> int:
                return 1

    with pytest.raises(TypeError, match="template readers must return text"):
        await chevron.async_render(InvalidTemplate())


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_reader_failures_preserve_the_caller_scope(
    anyio_backend: str,
) -> None:
    class BrokenTemplate:
        async def read(self) -> str:
            raise OSError("unable to read template")

    scopes = [{"name": "intact"}]
    with pytest.raises(OSError, match="unable to read template"):
        await chevron.async_render(BrokenTemplate(), scopes=scopes)

    assert scopes == [{"name": "intact"}]


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_lambda_result_sections_do_not_mutate_caller_scopes(
    anyio_backend: str,
) -> None:
    scopes: list[dict[str, object]] = [{"item": {"value": "1"}}]

    @chevron.func
    async def outer() -> str:
        return "{{#item}}{{inner}}{{/item}}"

    @chevron.func
    async def inner() -> str:
        return str(len(scopes))

    scopes[0].update(outer=outer, inner=inner)

    assert await chevron.async_render("{{outer}}", scopes=scopes) == "1"
    assert len(scopes) == 1


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_reader_cancellation_leaves_the_reader_owned_by_the_caller(
    anyio_backend: str,
) -> None:
    import anyio

    started = anyio.Event()

    class WaitingTemplate:
        closed = False

        async def read(self) -> str:
            started.set()
            await anyio.sleep_forever()

        async def aclose(self) -> None:
            self.closed = True

    template = WaitingTemplate()

    async def render_template() -> None:
        await chevron.async_render(template)

    async with anyio.create_task_group() as tasks:
        tasks.start_soon(render_template)
        await started.wait()
        tasks.cancel_scope.cancel()

    assert not template.closed


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_template_reads_do_not_block_sibling_tasks(
    anyio_backend: str,
) -> None:
    import anyio

    started = anyio.Event()
    release = anyio.Event()
    completed = anyio.Event()
    result: list[str] = []

    class AsyncTemplate:
        async def read(self) -> str:
            started.set()
            await release.wait()
            return "{{value}}"

    async def render_template() -> None:
        result.append(await chevron.async_render(AsyncTemplate(), {"value": "done"}))
        completed.set()

    async with anyio.create_task_group() as tasks:
        tasks.start_soon(render_template)
        await started.wait()
        assert not completed.is_set()
        release.set()

    assert result == ["done"]


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_keeps_mapping_partial_precedence_and_containment(
    anyio_backend: str, tmp_path
) -> None:
    (tmp_path / "part.mustache").write_text("filesystem", encoding="utf-8")
    (tmp_path.parent / "outside.mustache").write_text("outside", encoding="utf-8")

    assert (
        await chevron.async_render(
            "{{>part}}|{{>../outside}}",
            partials_path=tmp_path,
            partials_dict={"part": "mapping"},
        )
        == "mapping|"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_loads_a_real_filesystem_partial(
    anyio_backend: str, tmp_path
) -> None:
    (tmp_path / "greeting.mustache").write_text("Hello, {{name}}!", encoding="utf-8")

    assert (
        await chevron.async_render(
            "{{>greeting}}", {"name": "Ada"}, partials_path=tmp_path
        )
        == "Hello, Ada!"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("template", ["literal", "{{missing}}"])
async def test_async_empty_scopes_are_a_valid_empty_context(
    anyio_backend: str, template: str
) -> None:
    assert await chevron.async_render(template, scopes=[]) == (
        "literal" if template == "literal" else ""
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("scopes", ["text", b"bytes", {"name": "value"}])
async def test_async_scopes_reject_non_sequence_containers(
    anyio_backend: str, scopes: object
) -> None:
    with pytest.raises(TypeError, match="scopes must be a sequence"):
        await chevron.async_render("{{name}}", scopes=scopes)


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("tag", ["{{{.}}}", "{{& .}}"])
async def test_async_unescaped_current_scope_in_inverted_section_uses_parent_scope(
    anyio_backend: str, tag: str
) -> None:
    assert (
        await chevron.async_render(f"{{{{^missing}}}}{tag}{{{{/missing}}}}", "context")
        == "context"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("tag", ["{{.}}", "{{{.}}}", "{{& .}}"])
async def test_async_true_current_scope_is_not_an_inverted_section_marker(
    anyio_backend: str, tag: str
) -> None:
    assert (
        await chevron.async_render(f"{{{{^missing}}}}{tag}{{{{/missing}}}}", True)
        == "True"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("tag", ["{{.}}", "{{{.}}}", "{{& .}}"])
async def test_async_nested_inverted_sections_resolve_current_scope(
    anyio_backend: str, tag: str
) -> None:
    assert (
        await chevron.async_render(
            "{{^missing}}{{^other}}" + tag + "{{/other}}{{/missing}}",
            "context",
        )
        == "context"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_nested_inverted_sections_resolve_current_scope_sections(
    anyio_backend: str,
) -> None:
    assert (
        await chevron.async_render(
            "{{^missing}}{{^other}}{{#.}}{{.}}{{/.}}{{/other}}{{/missing}}",
            "context",
        )
        == "context"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_numeric_lookup_falls_back_past_a_scalar_section_frame(
    anyio_backend: str,
) -> None:
    assert (
        await chevron.async_render(
            "{{#items}}{{0}}{{/items}}", {"items": [1], "0": "outer value"}
        )
        == "outer value"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_numeric_lookup_falls_back_past_an_inverted_section_marker(
    anyio_backend: str,
) -> None:
    assert (
        await chevron.async_render(
            "{{^flag}}{{0}}{{/flag}}", {"flag": False, "0": "outer value"}
        )
        == "outer value"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("value", [0, False, {}])
async def test_async_iterable_falsey_items_match_synchronous_sections(
    anyio_backend: str, value: object
) -> None:
    async def values():
        yield value

    template = "{{#values}}[{{.}}]{{/values}}"
    assert await chevron.async_render(template, {"values": values()}) == chevron.render(
        template, {"values": [value]}
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_looks_up_mapped_partials_on_the_render_task(
    anyio_backend: str,
) -> None:
    import threading

    render_thread = threading.current_thread()

    class RenderTaskPartials(dict):
        def __getitem__(self, key):
            assert threading.current_thread() is render_thread
            return super().__getitem__(key)

    assert (
        await chevron.async_render(
            "{{>part}}", partials_dict=RenderTaskPartials(part="mapping")
        )
        == "mapping"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_treats_missing_partials_as_empty_when_filesystem_loading_is_disabled(
    anyio_backend: str,
) -> None:
    assert await chevron.async_render("{{>missing}}") == ""


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_filesystem_partials_reject_symlink_escapes(
    anyio_backend: str, tmp_path
) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "part.mustache").write_text("outside", encoding="utf-8")
    (root / "escape").symlink_to(outside, target_is_directory=True)

    assert await chevron.async_render("{{>escape/part}}", partials_path=root) == ""


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_filesystem_partial_loading_does_not_block_sibling_tasks(
    anyio_backend: str, tmp_path
) -> None:
    import anyio
    import os

    partial_path = tmp_path / "part.mustache"
    os.mkfifo(partial_path)
    sibling_progressed = anyio.Event()
    result: list[str] = []

    async def render_template() -> None:
        result.append(await chevron.async_render("{{>part}}", partials_path=tmp_path))

    async def prove_sibling_progress() -> None:
        sibling_progressed.set()

    async def release_partial() -> None:
        descriptor = await anyio.to_thread.run_sync(os.open, partial_path, os.O_WRONLY)
        try:
            await anyio.to_thread.run_sync(os.write, descriptor, b"loaded")
        finally:
            await anyio.to_thread.run_sync(os.close, descriptor)

    async with anyio.create_task_group() as tasks:
        tasks.start_soon(render_template)
        tasks.start_soon(prove_sibling_progress)
        await sibling_progressed.wait()
        assert result == []
        tasks.start_soon(release_partial)

    assert result == ["loaded"]


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_filesystem_partial_closes_on_cancellation(
    anyio_backend: str, monkeypatch, tmp_path
) -> None:
    import anyio

    from chevron import async_renderer

    (tmp_path / "part.mustache").write_text("loaded", encoding="utf-8")
    started = anyio.Event()
    opened = []
    path_open = async_renderer.anyio.Path.open

    async def blocking_open(path, *args, **kwargs):
        partial = await path_open(path, *args, **kwargs)
        opened.append(partial)

        async def blocking_read() -> str:
            started.set()
            await anyio.sleep_forever()

        partial.read = blocking_read
        return partial

    monkeypatch.setattr(async_renderer.anyio.Path, "open", blocking_open)

    async def render_template() -> None:
        await chevron.async_render("{{>part}}", partials_path=tmp_path)

    async with anyio.create_task_group() as tasks:
        tasks.start_soon(render_template)
        await started.wait()
        tasks.cancel_scope.cancel()

    assert opened[0].wrapped.closed


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_cancellation_restores_the_caller_scope(
    anyio_backend: str,
) -> None:
    import anyio

    started = anyio.Event()
    scopes = [{"value": "intact"}]

    @chevron.func
    async def value() -> str:
        started.set()
        await anyio.sleep_forever()

    async def render_template() -> None:
        await chevron.async_render("{{value}}", scopes=scopes, lambdas={"value": value})

    async with anyio.create_task_group() as tasks:
        tasks.start_soon(render_template)
        await started.wait()
        tasks.cancel_scope.cancel()

    assert scopes == [{"value": "intact"}]


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_concurrent_async_renders_keep_scopes_isolated(
    anyio_backend: str,
) -> None:
    import anyio

    release = anyio.Event()
    started = 0
    results: list[str] = []

    def make_value() -> object:
        @chevron.func
        async def value() -> str:
            nonlocal started
            started += 1
            if started == 2:
                release.set()
            await release.wait()
            return "{{name}}"

        return value

    async def render(name: str) -> None:
        value = make_value()
        results.append(
            await chevron.async_render(
                "{{value}}", {"name": name}, lambdas={"value": value}
            )
        )

    async with anyio.create_task_group() as tasks:
        tasks.start_soon(render, "first")
        tasks.start_soon(render, "second")

    assert sorted(results) == ["first", "second"]


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_concurrent_nested_compatibility_renders_keep_scopes_isolated(
    anyio_backend: str,
) -> None:
    import anyio

    @chevron.compat
    async def values(text: str, render) -> str:
        results: list[str] = []

        async def render_with(data: dict[str, str]) -> None:
            results.append(await render(text, data))

        async with anyio.create_task_group() as tasks:
            tasks.start_soon(render_with, {"name": "first"})
            tasks.start_soon(render_with, {"name": "second"})

        return "|".join(sorted(results))

    assert (
        await chevron.async_render(
            "{{#values}}{{name}}{{/values}}", lambdas={"values": values}
        )
        == "first|second"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_inverted_async_iterable_is_not_consumed(anyio_backend: str) -> None:
    async def values():
        raise AssertionError("inverted sections must not consume async iterables")
        yield None

    assert (
        await chevron.async_render("{{^values}}empty{{/values}}", {"values": values()})
        == ""
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_empty_async_iterables_render_the_section_zero_times(
    anyio_backend: str,
) -> None:
    async def values():
        if False:
            yield None

    assert (
        await chevron.async_render("{{#values}}value{{/values}}", {"values": values()})
        == ""
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_iterable_errors_propagate_without_closing_the_iterator(
    anyio_backend: str,
) -> None:
    class FailingItems:
        closed = False

        def __aiter__(self):
            return self

        async def __anext__(self):
            raise RuntimeError("iteration failure")

        async def aclose(self) -> None:
            self.closed = True

    items = FailingItems()
    with pytest.raises(RuntimeError, match="iteration failure"):
        await chevron.async_render("{{#items}}value{{/items}}", {"items": items})

    assert not items.closed


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_cancelled_async_iterables_remain_caller_owned(
    anyio_backend: str,
) -> None:
    import anyio

    started = anyio.Event()

    class WaitingItems:
        closed = False

        def __aiter__(self):
            return self

        async def __anext__(self):
            started.set()
            await anyio.sleep_forever()

        async def aclose(self) -> None:
            self.closed = True

    items = WaitingItems()

    async def render_template() -> None:
        await chevron.async_render("{{#items}}value{{/items}}", {"items": items})

    async with anyio.create_task_group() as tasks:
        tasks.start_soon(render_template)
        await started.wait()
        tasks.cancel_scope.cancel()

    assert not items.closed


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_delivers_diagnostics_to_standard_python_logging(
    anyio_backend: str,
) -> None:
    records: list[str] = []

    class Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record.getMessage())

    logger = logging.Logger("test.async-diagnostics", logging.WARNING)
    logger.addHandler(Handler())

    assert await chevron.async_render("{{missing}}", logger=logger) == ""
    assert records == ["Could not find key 'missing'"]


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize(
    ("partial", "reason"),
    [("/etc/passwd", "absolute path"), ("../secret", "parent traversal")],
)
async def test_async_rejected_filesystem_partial_diagnostics_retain_safe_context(
    anyio_backend: str, tmp_path, partial: str, reason: str
) -> None:
    records: list[str] = []

    class Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record.getMessage())

    logger = logging.Logger("test.async-rejected-partials", logging.DEBUG)
    logger.addHandler(Handler())

    assert (
        await chevron.async_render(
            "{{> " + partial + "}}",
            partials_path=tmp_path,
            logger=logger,
            log_level=logging.DEBUG,
        )
        == ""
    )

    assert f"Rejected partial reference '{partial}': {reason}" in records
    assert str(tmp_path) not in "\n".join(records)


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_warns_through_the_default_logger(
    anyio_backend: str, caplog
) -> None:
    assert await chevron.async_render("{{missing}}", warn=True) == ""
    assert [record.getMessage() for record in caplog.records] == [
        "Could not find key 'missing'"
    ]


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_validates_logging_arguments(anyio_backend: str) -> None:
    with pytest.raises(TypeError, match="logger must be a logging.Logger"):
        await chevron.async_render("", logger=object())
    with pytest.raises(TypeError, match="log_level must be an integer"):
        await chevron.async_render("", log_level="WARNING")


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize(
    ("decorator", "template"),
    [
        (chevron.func, "{{#value}}body{{/value}}"),
        (chevron.section, "{{value}}"),
        (chevron.compat, "{{value}}"),
    ],
)
async def test_async_lambda_protocol_mismatches_do_not_invoke_callbacks(
    anyio_backend: str, decorator, template: str
) -> None:
    calls: list[tuple[object, ...]] = []

    @decorator
    async def value(*args: object) -> str:
        calls.append(args)
        return "unexpected"

    assert await chevron.async_render(template, lambdas={"value": value}) == ""
    assert calls == []


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_render_logs_template_errors_before_propagating(
    anyio_backend: str,
) -> None:
    records: list[tuple[int, str]] = []

    class Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append((record.levelno, record.getMessage()))

    logger = logging.Logger("test.async-errors", logging.ERROR)
    logger.addHandler(Handler())

    with pytest.raises(ChevronError, match='tag "unclosed" was never closed'):
        await chevron.async_render("{{#unclosed}}", logger=logger)

    assert records == [
        (
            logging.ERROR,
            "Template rendering failed: Unexpected EOF\n"
            'the tag "unclosed" was never closed\n'
            "was opened at line 1",
        )
    ]
