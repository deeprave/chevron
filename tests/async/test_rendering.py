"""Behavioural tests for Chevron's async public API."""

from io import StringIO
import logging
from collections.abc import AsyncIterator, Iterator, Sequence
import sys
from typing import overload

import pytest

import chevron
from async_support import ANYIO_BACKENDS
from chevron import ChevronError, Extension
from async_cases import ASYNC_ITERATOR_DEFAULT_CASES, ASYNC_ITERATOR_EXTENSION_CASES
from filesystem_partial_cases import FILESYSTEM_PARTIAL_CASES
from rendering_case_sets import ASYNC_RENDER_CASES
from rendering_cases import FilesystemPartialRenderCase, LambdaRenderCase, RenderCase
from section_cases import ITERATOR_DEFAULT_CASES, ITERATOR_EXTENSION_CASES
from token_cases import MALFORMED_RESERVED_TAG_TEMPLATES, TOKEN_VALIDATION_CASES


class _CallerOwnedItems:
    def __init__(self) -> None:
        self.cursor = self.items()

    def __aiter__(self) -> AsyncIterator[str]:
        return self.cursor

    async def items(self) -> AsyncIterator[str]:
        yield "first"
        yield "second"


@pytest.fixture
def inverted_iterators_enabled() -> Iterator[None]:
    Extension.disable(Extension.ALL)
    Extension.enable(Extension.INVERTED_ITERATORS)
    try:
        yield
    finally:
        Extension.disable(Extension.ALL)


@pytest.fixture
def extensions_disabled() -> Iterator[None]:
    Extension.disable(Extension.ALL)
    try:
        yield
    finally:
        Extension.disable(Extension.ALL)


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("case", ASYNC_RENDER_CASES, ids=lambda case: case.name)
async def test_async_rendering_case(anyio_backend: str, case: RenderCase) -> None:
    """Render every shared source-template case through the public async API."""
    lambdas = case.render_lambdas() if isinstance(case, LambdaRenderCase) else None
    def_ldel, def_rdel = case.initial_delimiters
    assert (
        await chevron.async_render(
            case.template,
            case.render_data(),
            partials_dict=case.partials,
            scopes=case.scopes,
            lambdas=lambdas,
            def_ldel=def_ldel,
            def_rdel=def_rdel,
        )
        == case.expected
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize(
    "case",
    ITERATOR_EXTENSION_CASES + ASYNC_ITERATOR_EXTENSION_CASES,
    ids=lambda case: case.name,
)
async def test_async_iterator_extension_case(
    anyio_backend: str, inverted_iterators_enabled: None, case: RenderCase
) -> None:
    assert (
        await chevron.async_render(
            case.template,
            case.render_data(),
            partials_dict=case.partials,
            scopes=case.scopes,
            def_ldel=case.initial_delimiters[0],
            def_rdel=case.initial_delimiters[1],
        )
        == case.expected
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_inverted_iterators_are_disabled_by_default(
    anyio_backend: str, extensions_disabled: None
) -> None:
    async def items():
        if False:
            yield None

    assert (
        await chevron.async_render("{{^items}}fallback{{/items}}", {"items": items()})
        == ""
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize(
    "case",
    ITERATOR_DEFAULT_CASES + ASYNC_ITERATOR_DEFAULT_CASES,
    ids=lambda case: case.name,
)
async def test_async_iterator_default_cases(
    anyio_backend: str, extensions_disabled: None, case: RenderCase
) -> None:
    assert (
        await chevron.async_render(
            case.template,
            case.render_data(),
            partials_dict=case.partials,
            scopes=case.scopes,
            def_ldel=case.initial_delimiters[0],
            def_rdel=case.initial_delimiters[1],
        )
        == case.expected
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_inverted_async_iterable_leaves_caller_iterator_open(
    anyio_backend: str, inverted_iterators_enabled: None
) -> None:
    items = _CallerOwnedItems()

    assert (
        await chevron.async_render("{{^items}}fallback{{/items}}", {"items": items})
        == ""
    )
    assert await anext(items.cursor) == "second"


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_iterator_probe_does_not_mask_render_errors(
    anyio_backend: str, inverted_iterators_enabled: None
) -> None:
    class RenderError(Exception):
        pass

    @chevron.func
    def fail() -> str:
        raise RenderError("render failure")

    items = _CallerOwnedItems()
    with pytest.raises(RenderError, match="render failure"):
        await chevron.async_render(
            "{{#outer}}{{^items}}fallback{{/items}}{{fail}}{{/outer}}",
            {"outer": True, "items": items},
            lambdas={"fail": fail},
        )
    assert await anext(items.cursor) == "second"


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_iterator_probe_preserves_caller_source_through_cancellation(
    anyio_backend: str, inverted_iterators_enabled: None
) -> None:
    import anyio

    cancel_scope = anyio.CancelScope()

    @chevron.func
    async def cancel() -> str:
        cancel_scope.cancel()
        await anyio.lowlevel.checkpoint()
        return ""

    items = _CallerOwnedItems()
    with cancel_scope:
        await chevron.async_render(
            "{{#outer}}{{^items}}fallback{{/items}}{{cancel}}{{/outer}}",
            {"outer": True, "items": items},
            lambdas={"cancel": cancel},
        )

    assert await anext(items.cursor) == "second"


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("case", FILESYSTEM_PARTIAL_CASES, ids=lambda case: case.name)
async def test_async_filesystem_partial_case(
    anyio_backend: str, tmp_path, case: FilesystemPartialRenderCase
) -> None:
    """Render every ordinary filesystem partial case through the async API."""
    case.materialise_partials(tmp_path)
    def_ldel, def_rdel = case.initial_delimiters
    assert (
        await chevron.async_render(
            case.template,
            case.render_data(),
            partials_dict=case.partials,
            partials_path=tmp_path,
            partials_ext=case.partials_ext,
            scopes=case.scopes,
            def_ldel=def_ldel,
            def_rdel=def_rdel,
        )
        == case.expected
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize(
    ("_name", "tokens", "message"),
    TOKEN_VALIDATION_CASES,
    ids=[case[0] for case in TOKEN_VALIDATION_CASES],
)
async def test_async_direct_token_sequences_validate_structure(
    anyio_backend: str,
    _name: str,
    tokens: tuple[tuple[str, str], ...],
    message: str,
) -> None:
    with pytest.raises(ChevronError, match=message):
        await chevron.async_render(tokens)


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("template", MALFORMED_RESERVED_TAG_TEMPLATES)
async def test_async_unclosed_reserved_inheritance_tags_raise_chevron_syntax_errors(
    anyio_backend: str, template: str
) -> None:
    with pytest.raises(ChevronError):
        await chevron.async_render(template)


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_deep_async_lambda_expansion_does_not_use_the_python_call_stack(
    anyio_backend: str,
) -> None:
    depth = sys.getrecursionlimit() + 10
    lambdas = {}

    for index in range(depth):

        @chevron.func
        async def expansion(index: int = index) -> str:
            return f"{{{{lambda-{index + 1}}}}}"

        lambdas[f"lambda-{index}"] = expansion

    @chevron.func
    async def complete() -> str:
        return "complete"

    lambdas[f"lambda-{depth}"] = complete

    assert await chevron.async_render("{{lambda-0}}", lambdas=lambdas) == "complete"


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_deep_async_partial_resumes_parent_scope_and_indentation(
    anyio_backend: str,
) -> None:
    depth = sys.getrecursionlimit() + 10
    partials = {
        f"partial-{index}": f"{{{{>partial-{index + 1}}}}}" for index in range(depth)
    }
    partials[f"partial-{depth}"] = "{{name}}\n{{name}}"

    shallow = await chevron.async_render(
        "{{#item}}  {{>partial-0}}|{{name}}{{/item}}",
        {"item": {"name": "inner"}},
        partials_dict={"partial-0": "{{name}}\n{{name}}"},
    )
    deep = await chevron.async_render(
        "{{#item}}  {{>partial-0}}|{{name}}{{/item}}",
        {"item": {"name": "inner"}},
        partials_dict=partials,
    )

    assert deep == shallow == "  inner\n  inner|inner"


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_deep_async_standard_section_lambda_expansion_does_not_use_the_python_call_stack(
    anyio_backend: str,
) -> None:
    depth = sys.getrecursionlimit() + 10
    lambdas = {}

    for index in range(depth):

        @chevron.section
        async def expansion(body: str, index: int = index) -> str:
            return f"{{{{#section-{index + 1}}}}}{body}{{{{/section-{index + 1}}}}}"

        lambdas[f"section-{index}"] = expansion

    @chevron.section
    async def complete(body: str) -> str:
        return body

    lambdas[f"section-{depth}"] = complete

    assert (
        await chevron.async_render(
            "{{#section-0}}complete{{/section-0}}", lambdas=lambdas
        )
        == "complete"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_deep_async_iterable_sections_do_not_use_the_python_call_stack(
    anyio_backend: str,
) -> None:
    depth = sys.getrecursionlimit() + 10
    template = "{{#items}}" * depth + "complete" + "{{/items}}" * depth
    data = {"items": [{"items": []}]}
    current = data["items"][0]
    for _ in range(depth - 1):
        next_item = {"items": []}
        current["items"] = [next_item]
        current = next_item

    assert await chevron.async_render(template, data) == "complete"


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_empty_section_observes_cancellation(
    anyio_backend: str,
) -> None:
    import anyio

    consumed: list[int] = []
    cancel_scope = anyio.CancelScope()

    def items():
        for item in range(10_000):
            consumed.append(item)
            if item == 0:
                cancel_scope.cancel()
            yield item

    with cancel_scope:
        await chevron.async_render("{{#items}}{{/items}}", {"items": items()})

    assert len(consumed) < 10_000


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_cyclic_partial_fails_with_a_bounded_error(
    anyio_backend: str,
) -> None:
    with pytest.raises(RecursionError, match="nested template expansion"):
        await chevron.async_render("{{>self}}", partials_dict={"self": "{{>self}}"})


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_dynamic_partial_cycle_fails_with_a_bounded_error(
    anyio_backend: str,
) -> None:
    with pytest.raises(RecursionError, match="nested template expansion"):
        await chevron.async_render(
            "{{>*name}}",
            {"name": "self"},
            partials_dict={"self": "{{>*name}}"},
        )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_parent_override_preserves_literal_tokens(
    anyio_backend: str,
) -> None:
    tokens = [
        ("parent", "layout"),
        ("block", "body"),
        ("literal", "{{name}}"),
        ("end", "body"),
        ("end", "layout"),
    ]

    assert (
        await chevron.async_render(
            tokens,
            {"name": "Ada"},
            partials_dict={"layout": "parent:[{{$body}}default{{/body}}]"},
        )
        == "parent:[{{name}}]"
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_function_lambda_cycle_fails_with_a_bounded_error(
    anyio_backend: str,
) -> None:
    @chevron.func
    async def loop() -> str:
        return "{{loop}}"

    with pytest.raises(RecursionError, match="nested template expansion"):
        await chevron.async_render("{{loop}}", lambdas={"loop": loop})


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_iterator_error_does_not_gain_stop_iteration_context(
    anyio_backend: str,
) -> None:
    class Items:
        def __init__(self) -> None:
            self.first = True

        def __iter__(self) -> "Items":
            return self

        def __next__(self) -> str:
            if self.first:
                self.first = False
                return "item"
            raise ValueError("iterator failed")

    with pytest.raises(ValueError, match="iterator failed") as error:
        await chevron.async_render("{{#items}}{{/items}}", {"items": Items()})

    assert error.value.__context__ is None


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_compatibility_section_rejects_non_string_results_promptly(
    anyio_backend: str,
) -> None:
    called = False

    @chevron.compat
    async def invalid_result(text: str, render) -> int:
        return 1

    @chevron.func
    async def later() -> str:
        nonlocal called
        called = True
        return "later"

    with pytest.raises(TypeError, match="Compatibility lambda 'invalid_result'"):
        await chevron.async_render(
            "{{#invalid_result}}body{{/invalid_result}}{{later}}",
            lambdas={"invalid_result": invalid_result, "later": later},
        )

    assert not called


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
async def test_async_section_lambda_does_not_leave_terminal_padding(
    anyio_backend: str,
) -> None:
    @chevron.section
    async def section(_body: str) -> str:
        return "value\n"

    assert (
        await chevron.async_render(
            "{{#section}}ignored{{/section}}",
            padding="  ",
            lambdas={"section": section},
        )
        == "value\n"
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
async def test_async_compatibility_callback_can_render_an_unhashable_reader(
    anyio_backend: str,
) -> None:
    class Reader:
        __hash__ = None

        def read(self) -> str:
            return "{{name}}"

    @chevron.compat
    async def callback(text: str, render) -> str:
        return await render(Reader())

    assert (
        await chevron.async_render(
            "{{#callback}}ignored{{/callback}}",
            {"name": "reader"},
            lambdas={"callback": callback},
        )
        == "reader"
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
    calls = 0

    class Empty:
        async def __call__(self) -> None:
            nonlocal calls
            calls += 1
            return None

    value = chevron.func(Empty())

    assert await chevron.async_render("{{value}}", lambdas={"value": value}) == ""
    assert calls == 1


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
        async def read(self) -> None:
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

        async def read(self) -> None:
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
async def test_async_dynamic_partial_keeps_mapping_precedence_and_filesystem_containment(
    anyio_backend: str, tmp_path
) -> None:
    (tmp_path / "choice.mustache").write_text("filesystem", encoding="utf-8")
    (tmp_path.parent / "outside.mustache").write_text("outside", encoding="utf-8")

    assert (
        await chevron.async_render(
            "{{>*selector}}",
            {"selector": "choice"},
            partials_path=tmp_path,
            partials_dict={"choice": "mapping"},
        )
        == "mapping"
    )
    assert (
        await chevron.async_render(
            "{{>*selector}}",
            {"selector": "../outside"},
            partials_path=tmp_path,
        )
        == ""
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_dynamic_partial_respects_explicit_lambda_policy(
    anyio_backend: str,
) -> None:
    called = False

    def selector() -> str:
        nonlocal called
        called = True
        return "choice"

    assert (
        await chevron.async_render(
            "{{>*selector}}",
            {"selector": "choice"},
            partials_dict={"choice": "wrong"},
            lambdas={"selector": selector},
        )
        == ""
    )
    assert not called


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_async_dynamic_partial_debug_messages_do_not_disclose_selector_data(
    anyio_backend: str, tmp_path
) -> None:
    messages: list[str] = []

    class Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            messages.append(record.getMessage())

    logger = logging.Logger("test.async-dynamic-partial", logging.DEBUG)
    logger.addHandler(Handler())

    assert (
        await chevron.async_render(
            "{{>*selector_secret}}{{>*}}{{>**selector_secret}}{{>*number_secret}}{{>*path_secret}}",
            {
                "selector_secret": "selected-by-data",
                "number_secret": 42,
                "path_secret": "../outside",
            },
            partials_dict={"selected-by-data": "content"},
            partials_path=tmp_path,
            logger=logger,
            log_level=logging.DEBUG,
        )
        == "content"
    )

    assert "Resolved dynamic partial from configured partials" in messages
    assert "Dynamic partial selector was empty" in messages
    assert "Dynamic partial selector requested nested dereferencing" in messages
    assert "Dynamic partial selector did not resolve to a non-empty string" in messages
    assert "Rejected dynamic partial reference: parent traversal" in messages
    assert all(
        secret not in "\n".join(messages)
        for secret in (
            "selector_secret",
            "selected-by-data",
            "number_secret",
            "42",
            "path_secret",
            "../outside",
        )
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
@pytest.mark.parametrize("scopes", ["text", b"bytes", {"name": "value"}])
async def test_async_scopes_reject_non_sequence_containers(
    anyio_backend: str, scopes: object
) -> None:
    with pytest.raises(TypeError, match="scopes must be a sequence"):
        await chevron.async_render("{{name}}", scopes=scopes)  # ty: ignore[invalid-argument-type]


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
    anyio_backend: str, monkeypatch, tmp_path
) -> None:
    import anyio
    import os

    partial_path = tmp_path / "part.mustache"
    os.mkfifo(partial_path)
    partial_open_requested = anyio.Event()
    sibling_progressed = anyio.Event()
    result: list[str] = []
    path_open = anyio.Path.open

    async def signalling_open(path, *args, **kwargs):
        partial_open_requested.set()
        return await path_open(path, *args, **kwargs)

    monkeypatch.setattr(anyio.Path, "open", signalling_open)

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

    with anyio.fail_after(5):
        async with anyio.create_task_group() as tasks:
            tasks.start_soon(render_template)
            await partial_open_requested.wait()
            tasks.start_soon(prove_sibling_progress)
            await sibling_progressed.wait()
            assert result == []
            tasks.start_soon(release_partial)

    assert result == ["loaded"]


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ANYIO_BACKENDS)
async def test_cancelling_a_filesystem_partial_closes_the_opened_resource(
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

        async def blocking_read() -> None:
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
    async def value() -> None:
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

    def make_value():
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
async def test_async_numeric_lookup_propagates_sequence_index_errors(
    anyio_backend: str,
) -> None:
    class BrokenSequence(Sequence):
        @overload
        def __getitem__(self, index: int) -> object: ...

        @overload
        def __getitem__(self, index: slice) -> Sequence[object]: ...

        def __getitem__(self, index: int | slice) -> object | Sequence[object]:
            if isinstance(index, str):
                raise TypeError("string lookup is unsupported")
            raise TypeError("integer lookup failed")

        def __len__(self) -> int:
            return 1

    with pytest.raises(TypeError, match="integer lookup failed"):
        await chevron.async_render("{{0}}", BrokenSequence())


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
        await chevron.async_render("", logger=object())  # ty: ignore[invalid-argument-type]
    with pytest.raises(TypeError, match="log_level must be an integer"):
        await chevron.async_render("", log_level="WARNING")  # ty: ignore[invalid-argument-type]


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
