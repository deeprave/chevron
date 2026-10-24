"""AnyIO-backed rendering, loaded only by :func:`chevron.async_render`."""

from collections.abc import AsyncIterable, Awaitable, Callable, Iterator, Sequence
import inspect
import logging
from pathlib import Path
from typing import cast
import anyio

from .renderer import (
    _COMPAT_PROTOCOL,
    _END_OF_TOKENS,
    _FUNCTION_PROTOCOL,
    _LambdaDefinition,
    _RenderConfig,
    _RenderFrame,
    _RenderLogger,
    _RenderState,
    _RenderWork,
    _SECTION_PROTOCOL,
    _INVERTED_SECTION_MARKER,
    _SKIPPED_SECTION_MARKER,
    _SourcePolicy,
    _SectionBody,
    _changed_delimiters,
    _apply_control_token,
    _interpolation_text,
    _close_awaitable,
    _filesystem_partial_name,
    _filesystem_partial_rejection_reason,
    _lambda_protocol,
    _normalise_value,
    _partial_name,
    _push_work,
    _prepare_render_context,
    _read_template_result,
    _validated_tokens,
    LambdaCallback,
    LambdaRegistry,
    Logger,
    PartialMapping,
    ScopeSequence,
    TemplateData,
    TemplateInput,
    Token,
    TokenIterator,
)
from .tokenizer import ChevronError, tokenize as _tokenize


def _read_in_worker(reader: Callable[[], TemplateData]) -> tuple[TemplateData]:
    """Box a reader result so worker adapters never return an awaitable directly."""
    return (reader(),)


async def _aget_filesystem_partial(
    name: str,
    partials_path: str | Path | None,
    partials_ext: str,
    logger: _RenderLogger,
    *,
    dynamic: bool = False,
) -> str:
    """Load a partial through AnyIO's asynchronous path and file API."""
    if partials_path is None or partials_path == "":
        if dynamic:
            logger.debug("Dynamic partial was not configured")
        else:
            logger.debug("Partial '%s' was not configured", name)
        return ""

    try:
        base_path = await anyio.Path(partials_path).resolve(strict=True)
        partial_name = _filesystem_partial_name(name, partials_ext)
        if partial_name is None:
            reason = _filesystem_partial_rejection_reason(name, partials_ext)
            if dynamic:
                logger.debug("Rejected dynamic partial reference: %s", reason)
            else:
                logger.debug("Rejected partial reference '%s': %s", name, reason)
            return ""

        partial_path = await (base_path / partial_name).resolve(strict=True)
        partial_path.relative_to(base_path)
        partial = await partial_path.open("r", encoding="utf-8")
        try:
            content = await partial.read()
        finally:
            with anyio.CancelScope(shield=True):
                await partial.aclose()
        if dynamic:
            logger.debug("Resolved dynamic partial from the configured path")
        else:
            logger.debug("Resolved partial '%s' from the configured path", name)
        return content
    except (OSError, RuntimeError, ValueError):
        if dynamic:
            logger.debug("Dynamic partial was unavailable")
        else:
            logger.debug("Partial '%s' was unavailable", name)
        return ""


class AsyncChevronRender:
    """Await-aware counterpart to the synchronous render engine."""

    def __init__(self, config: _RenderConfig, policy: _SourcePolicy) -> None:
        self.config = config
        self.policy = policy
        self.state = _RenderState()

    async def _await_result(self, value: TemplateData) -> TemplateData:
        return await value if inspect.isawaitable(value) else value

    async def _read_template(self, template: TemplateInput) -> TemplateInput:
        reader = getattr(template, "read", None)
        if reader is None:
            return template
        if inspect.iscoroutinefunction(reader):
            value = await reader()
            return _read_template_result(value)

        (value,) = await anyio.to_thread.run_sync(
            _read_in_worker, reader, abandon_on_cancel=False
        )
        if inspect.isawaitable(value):
            try:
                await anyio.lowlevel.checkpoint()
                value = await value
            except BaseException:
                _close_awaitable(value)
                raise
        return _read_template_result(value)

    async def render(self, template: TemplateInput, frame: _RenderFrame) -> str:
        await anyio.lowlevel.checkpoint()
        return await self._drive(await self._template_work(template, frame))

    async def _template_work(
        self,
        template: TemplateInput,
        frame: _RenderFrame,
        continuation: Callable[[str], Awaitable[None]] | None = None,
    ) -> _RenderWork[Awaitable[None]]:
        if isinstance(template, (bytes, bytearray)):
            raise TypeError("templates must be text")
        if isinstance(template, Sequence) and not isinstance(template, str):
            tokens = _validated_tokens(template)
        else:
            template = await self._read_template(template)
            if not template and not isinstance(template, str):
                template = ""
            tokens = _tokenize(template, *frame.delimiters, include_raw=True)
        return _RenderWork[Awaitable[None]](
            tokens, frame, frame.delimiters, continuation
        )

    async def _drive(self, root: _RenderWork[Awaitable[None]]) -> str:
        """Run active work while preserving the renderer's checkpoint cadence."""
        active = [root]
        progress_count = 0
        try:
            while active:
                work = active[-1]
                progress_count += 1
                if progress_count % 64 == 0:
                    await anyio.lowlevel.checkpoint()
                try:
                    token = next(work.tokens)
                except StopIteration:
                    token = _END_OF_TOKENS
                if token is _END_OF_TOKENS:
                    active.pop()
                    work.close_tokens()
                    result = "".join(work.output)
                    if not active:
                        return result
                    assert work.continuation is not None
                    await work.continuation(result)
                    continue
                await self._render_token(work, cast(Token, token), active)
        finally:
            for work in reversed(active):
                work.close_tokens()
        raise RuntimeError("render work completed without a root result")

    def resolve(self, key: str, frame: _RenderFrame) -> tuple[TemplateData, bool]:
        return self.policy.resolve(
            key,
            frame,
            lambda value: (
                value if isinstance(value, Callable) else _normalise_value(key, value)
            ),
        )

    def empty_result(self, key: str) -> str:
        self.config.logger.warning(
            "Lambda '%s' returned None; rendering an empty value", key
        )
        return ""

    async def _schedule_result(
        self,
        result: TemplateData,
        key: str,
        frame: _RenderFrame,
        active: list[_RenderWork[Awaitable[None]]],
        continuation: Callable[[str], Awaitable[None]],
    ) -> None:
        result = await self._await_result(result)
        if result is None:
            await continuation(self.empty_result(key))
            return
        _push_work(
            active,
            await self._template_work(
                result if isinstance(result, str) else str(result), frame, continuation
            ),
        )

    async def compatibility_section(
        self,
        callback: LambdaCallback,
        key: str,
        body: _SectionBody,
        frame: _RenderFrame,
    ) -> str:
        text, tokens = body.compatibility(frame.delimiters)
        self.state.token_cache[text] = tokens

        async def render_callback(
            template: TemplateInput, data: TemplateData | None = None
        ) -> str:
            child = frame.with_context(self.config.default_delimiters, frame.padding)
            if data:
                child = child.child(data)
            return await self.compatibility_render(template, child)

        result = await self._await_result(callback(text, render_callback))
        if result is None:
            return self.empty_result(key)
        if not isinstance(result, str):
            raise TypeError(f"Compatibility lambda '{key}' must return text")
        return result

    async def compatibility_render(
        self, template: TemplateInput, frame: _RenderFrame
    ) -> str:
        if not template and not isinstance(template, (str, Sequence)):
            template = ""
        if isinstance(template, str) and template in self.state.token_cache:
            template = self.state.token_cache[template]
        return await self.render(template, frame)

    @staticmethod
    async def collect_section(
        tokens: TokenIterator, key: str, delimiters: tuple[str, str]
    ) -> _SectionBody:
        body: list[Token] = []
        depth = 0
        ending = delimiters
        for index, token in enumerate(tokens):
            if index and index % 64 == 0:
                await anyio.lowlevel.checkpoint()
            tag, name = token[:2]
            if tag in ("section", "inverted section") and name == key:
                depth += 1
            elif tag == "end" and name == key:
                if depth == 0:
                    break
                depth -= 1
            body.append(token)
            if tag == "set delimiter":
                ending = _changed_delimiters(name)
        return _SectionBody(body, delimiters, ending)

    async def _render_section(
        self,
        key: str,
        work: _RenderWork[Awaitable[None]],
        active: list[_RenderWork[Awaitable[None]]],
    ) -> None:
        value, _ = self.resolve(key, work.frame)
        if isinstance(value, Callable):
            body = await self.collect_section(work.tokens, key, work.delimiters)
            work.delimiters = body.ending
            protocol = _lambda_protocol(value, "section")
            self.config.logger.debug(
                "Selected %s lambda protocol for '%s'", protocol or "unsupported", key
            )
            if protocol == _SECTION_PROTOCOL:
                result_frame = work.frame.with_context(body.opening, work.frame.padding)

                async def append_result(result: str) -> None:
                    work.append(result)

                await self._schedule_result(
                    value(body.source()),
                    key,
                    result_frame,
                    active,
                    append_result,
                )
            elif protocol == _COMPAT_PROTOCOL:
                work.append(
                    await self.compatibility_section(value, key, body, work.frame)
                )
            return
        if isinstance(value, AsyncIterable):
            body = await self.collect_section(work.tokens, key, work.delimiters)
            work.delimiters = body.ending
            values = aiter(value)

            async def render_next(result: str | None = None) -> None:
                if result is not None:
                    work.append(result)
                try:
                    item = await anext(values)
                except StopAsyncIteration:
                    return
                child = work.frame.child(item, body.opening, work.frame.padding)
                _push_work(
                    active,
                    _RenderWork.from_tokens(iter(body.tokens), child, render_next),
                )

            await render_next()
            return
        if isinstance(value, (Sequence, Iterator)) and not isinstance(value, str):
            body = await self.collect_section(work.tokens, key, work.delimiters)
            work.delimiters = body.ending
            values = iter(value)

            async def render_next(result: str | None = None) -> None:
                if result is not None:
                    work.append(result)
                try:
                    item = next(values)
                except StopIteration:
                    return
                child = work.frame.child(item, body.opening, work.frame.padding)
                _push_work(
                    active,
                    _RenderWork.from_tokens(iter(body.tokens), child, render_next),
                )

            await render_next()
            return
        work.frame = work.frame.child(value if value else _SKIPPED_SECTION_MARKER)

    async def _render_partial(
        self,
        key: str,
        work: _RenderWork[Awaitable[None]],
        active: list[_RenderWork[Awaitable[None]]],
    ) -> None:
        config = self.config
        dynamic = key.startswith("*")
        name = _partial_name(key, work.frame, self.policy, config.logger)
        if name is None:
            return
        try:
            partial = config.partials_dict[name]
            if dynamic:
                config.logger.debug("Resolved dynamic partial from configured partials")
            else:
                config.logger.debug(
                    "Resolved partial '%s' from configured partials", name
                )
        except KeyError:
            partial = await _aget_filesystem_partial(
                name,
                config.partials_path,
                config.partials_ext,
                config.logger,
                dynamic=dynamic,
            )
        left = work.partial_padding()
        padding = work.frame.padding + left if left.isspace() else work.frame.padding
        child = work.frame.with_context(config.default_delimiters, padding)

        def append_partial(result: str) -> None:
            work.append(result.rstrip(" \t") if left.isspace() else result)

        async def append_partial_result(result: str) -> None:
            append_partial(result)

        _push_work(
            active,
            await self._template_work(partial, child, append_partial_result),
        )

    async def _render_token(
        self,
        work: _RenderWork[Awaitable[None]],
        token: Token,
        active: list[_RenderWork[Awaitable[None]]],
    ) -> None:
        tag, key = token[:2]
        if _apply_control_token(work, tag, key):
            return

        match tag:
            case "literal":
                work.append(key.replace("\n", "\n" + work.frame.padding))
            case "variable" | "no escape":
                await self._render_interpolation(key, tag, work, active)
            case "section":
                await self._render_section(key, work, active)
            case "inverted section":
                value, _ = self.policy.resolve(
                    key, work.frame, lambda value: _normalise_value(key, value)
                )
                work.frame = work.frame.child(
                    _INVERTED_SECTION_MARKER if not value else _SKIPPED_SECTION_MARKER
                )
            case "partial":
                await self._render_partial(key, work, active)

    async def _render_interpolation(
        self,
        key: str,
        tag: str,
        work: _RenderWork[Awaitable[None]],
        active: list[_RenderWork[Awaitable[None]]],
    ) -> None:
        value, explicit = self.resolve(key, work.frame)

        def append_value(result: TemplateData) -> None:
            work.append(_interpolation_text(result, tag))

        if not isinstance(value, Callable):
            append_value(value)
            return
        protocol = _lambda_protocol(value, "interpolation")
        self.config.logger.debug(
            "Selected %s lambda protocol for '%s'", protocol or "unsupported", key
        )
        if protocol == _FUNCTION_PROTOCOL:
            result_frame = work.frame.with_context(self.config.default_delimiters, "")

            async def append_result(result: str) -> None:
                append_value(result)

            await self._schedule_result(
                value(), key, result_frame, active, append_result
            )
        elif explicit or isinstance(value, _LambdaDefinition):
            append_value("")
        else:
            append_value(value)


async def async_render(
    template: TemplateInput = "",
    data: TemplateData = {},
    partials_path: str | Path | None = None,
    partials_ext: str = "mustache",
    partials_dict: PartialMapping = {},
    padding: str = "",
    def_ldel: str = "{{",
    def_rdel: str = "}}",
    scopes: ScopeSequence | None = None,
    warn: TemplateData = False,
    lambdas: LambdaRegistry | None = None,
    *,
    logger: Logger | None = None,
    log_level: int = logging.WARNING,
) -> str:
    """Render a template inside the caller's active AnyIO runtime."""
    config, policy, frame = _prepare_render_context(
        data,
        partials_path,
        partials_ext,
        partials_dict,
        padding,
        def_ldel,
        def_rdel,
        scopes,
        warn,
        lambdas,
        logger,
        log_level,
    )
    engine = AsyncChevronRender(config, policy)
    config.logger.info("Render started")
    try:
        result = await engine.render(template, frame)
    except ChevronError as error:
        config.logger.error("Template rendering failed: %s", error)
        raise
    config.logger.info("Render completed successfully")
    return result
