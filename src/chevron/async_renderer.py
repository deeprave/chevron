"""AnyIO-backed rendering, loaded only by :func:`chevron.async_render`."""

from collections.abc import AsyncIterable, Callable, Iterator, Sequence
import inspect
import logging
from pathlib import Path
from typing import Any

import anyio

from .renderer import (
    _COMPAT_PROTOCOL,
    _FUNCTION_PROTOCOL,
    _LambdaDefinition,
    _RenderConfig,
    _RenderFrame,
    _RenderLogger,
    _RenderState,
    _SECTION_PROTOCOL,
    _INVERTED_SECTION_MARKER,
    _SKIPPED_SECTION_MARKER,
    _SourcePolicy,
    _SectionBody,
    _changed_delimiters,
    _html_escape,
    _close_awaitable,
    _filesystem_partial_name,
    _filesystem_partial_rejection_reason,
    _lambda_protocol,
    _normalise_value,
    _prepare_render_context,
    _read_template_result,
    _validated_tokens,
)
from .tokenizer import ChevronError, tokenize as _tokenize


def _read_in_worker(reader: Callable[[], Any]) -> tuple[Any]:
    """Box a reader result so worker adapters never return an awaitable directly."""
    return (reader(),)


async def _aget_filesystem_partial(
    name: str,
    partials_path: str | Path | None,
    partials_ext: str,
    logger: _RenderLogger,
) -> str:
    """Load a partial through AnyIO's asynchronous path and file API."""
    if partials_path is None or partials_path == "":
        logger.debug("Partial '%s' was not configured", name)
        return ""

    try:
        base_path = await anyio.Path(partials_path).resolve(strict=True)
        partial_name = _filesystem_partial_name(name, partials_ext)
        if partial_name is None:
            logger.debug(
                "Rejected partial reference '%s': %s",
                name,
                _filesystem_partial_rejection_reason(name, partials_ext),
            )
            return ""

        partial_path = await (base_path / partial_name).resolve(strict=True)
        partial_path.relative_to(base_path)
        partial = await partial_path.open("r", encoding="utf-8")
        try:
            content = await partial.read()
        finally:
            with anyio.CancelScope(shield=True):
                await partial.aclose()
        logger.debug("Resolved partial '%s' from the configured path", name)
        return content
    except (OSError, RuntimeError, ValueError):
        logger.debug("Partial '%s' was unavailable", name)
        return ""


class AsyncChevronRender:
    """Await-aware counterpart to the synchronous render engine."""

    def __init__(self, config: _RenderConfig, policy: _SourcePolicy) -> None:
        self.config = config
        self.policy = policy
        self.state = _RenderState()

    async def _await_result(self, value: Any) -> Any:
        return await value if inspect.isawaitable(value) else value

    async def _read_template(self, template: Any) -> Any:
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

    async def render(self, template: Any, frame: _RenderFrame) -> str:
        token_stream = None
        try:
            await anyio.lowlevel.checkpoint()
            if isinstance(template, (bytes, bytearray)):
                raise TypeError("templates must be text")
            if isinstance(template, Sequence) and not isinstance(template, str):
                tokens = _validated_tokens(template)
            else:
                template = await self._read_template(template)
                if not template and not isinstance(template, str):
                    template = ""
                token_stream = _tokenize(template, *frame.delimiters, include_raw=True)
                tokens = token_stream
            return await self.render_tokens(tokens, frame)
        finally:
            if token_stream is not None:
                token_stream.close()

    def resolve(self, key: str, frame: _RenderFrame) -> tuple[Any, bool]:
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

    async def render_result(self, result: Any, key: str, frame: _RenderFrame) -> str:
        if result is None:
            return self.empty_result(key)
        return await self.render(
            result if isinstance(result, str) else str(result), frame
        )

    async def interpolation(self, key: str, frame: _RenderFrame) -> Any:
        value, explicit = self.resolve(key, frame)
        if not isinstance(value, Callable):
            return value
        protocol = _lambda_protocol(value, "interpolation")
        self.config.logger.debug(
            "Selected %s lambda protocol for '%s'", protocol or "unsupported", key
        )
        if protocol == _FUNCTION_PROTOCOL:
            result_frame = frame.with_context(self.config.default_delimiters, "")
            result = await self._await_result(value())
            return await self.render_result(result, key, result_frame)
        if explicit or isinstance(value, _LambdaDefinition):
            return ""
        return value

    async def standard_section(
        self, callback: Callable, key: str, body: _SectionBody, frame: _RenderFrame
    ) -> str:
        result_frame = frame.with_context(body.opening, frame.padding)
        result = await self._await_result(callback(body.source()))
        return await self.render_result(result, key, result_frame)

    async def compatibility_section(
        self, callback: Callable, key: str, body: _SectionBody, frame: _RenderFrame
    ) -> str:
        text, tokens = body.compatibility(frame.delimiters)
        self.state.token_cache[text] = tokens

        async def render_callback(template: Any, data: Any = None) -> str:
            child = frame.with_context(self.config.default_delimiters, frame.padding)
            if data:
                child = child.child(data)
            return await self.compatibility_render(template, child)

        result = await self._await_result(callback(text, render_callback))
        return self.empty_result(key) if result is None else result

    async def compatibility_render(self, template: Any, frame: _RenderFrame) -> str:
        if not template and not isinstance(template, (str, Sequence)):
            template = ""
        if isinstance(template, str) and template in self.state.token_cache:
            template = self.state.token_cache[template]
        return await self.render(template, frame)

    @staticmethod
    async def collect_section(
        tokens: Iterator, key: str, delimiters: tuple[str, str]
    ) -> _SectionBody:
        body = []
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

    async def render_section(
        self,
        key: str,
        tokens: Iterator,
        frame: _RenderFrame,
        delimiters: tuple[str, str],
    ) -> tuple[str, tuple[str, str], _RenderFrame]:
        value, _ = self.resolve(key, frame)
        if isinstance(value, Callable):
            body = await self.collect_section(tokens, key, delimiters)
            protocol = _lambda_protocol(value, "section")
            self.config.logger.debug(
                "Selected %s lambda protocol for '%s'", protocol or "unsupported", key
            )
            if protocol == _SECTION_PROTOCOL:
                result = await self.standard_section(value, key, body, frame)
            elif protocol == _COMPAT_PROTOCOL:
                result = await self.compatibility_section(value, key, body, frame)
            else:
                result = ""
            return result, body.ending, frame
        if isinstance(value, AsyncIterable):
            body = await self.collect_section(tokens, key, delimiters)
            output = []
            async for item in value:
                child = frame.child(item, body.opening, frame.padding)
                output.append(await self.render(body.tokens, child))
            return "".join(output), body.ending, frame
        if isinstance(value, (Sequence, Iterator)) and not isinstance(value, str):
            body = await self.collect_section(tokens, key, delimiters)
            output = []
            for item in value:
                child = frame.child(item, body.opening, frame.padding)
                output.append(await self.render(body.tokens, child))
            return "".join(output), body.ending, frame
        return "", delimiters, frame.child(value if value else _SKIPPED_SECTION_MARKER)

    async def render_partial(self, key: str, frame: _RenderFrame, output: str) -> str:
        config = self.config
        try:
            partial = config.partials_dict[key]
            config.logger.debug("Resolved partial '%s' from configured partials", key)
        except KeyError:
            partial = await _aget_filesystem_partial(
                key,
                config.partials_path,
                config.partials_ext,
                config.logger,
            )
        left = output.rpartition("\n")[2]
        padding = frame.padding + left if left.isspace() else frame.padding
        child = frame.with_context(config.default_delimiters, padding)
        result = await self.render(partial, child)
        return result.rstrip(" \t") if left.isspace() else result

    async def render_tokens(self, tokens: Iterator, frame: _RenderFrame) -> str:
        output = ""
        delimiters = frame.delimiters
        for index, token in enumerate(tokens):
            if index and index % 64 == 0:
                await anyio.lowlevel.checkpoint()
            tag, key = token[:2]
            current_scope = frame.scope
            if tag == "end":
                if frame.parent is not None:
                    frame = frame.parent
                continue
            if tag == "set delimiter":
                delimiters = _changed_delimiters(key)
                continue
            if current_scope is _SKIPPED_SECTION_MARKER and frame.parent is not None:
                if tag in ("section", "inverted section"):
                    frame = frame.child(_SKIPPED_SECTION_MARKER)
                continue

            match tag:
                case "literal":
                    output += key.replace("\n", "\n" + frame.padding)
                case "variable" | "no escape":
                    value = await self.interpolation(key, frame)
                    text = value if isinstance(value, str) else str(value)
                    output += _html_escape(text) if tag == "variable" else text
                case "section":
                    result, delimiters, frame = await self.render_section(
                        key, tokens, frame, delimiters
                    )
                    output += result
                case "inverted section":
                    value, _ = self.policy.resolve(
                        key, frame, lambda value: _normalise_value(key, value)
                    )
                    frame = frame.child(
                        _INVERTED_SECTION_MARKER
                        if not value
                        else _SKIPPED_SECTION_MARKER
                    )
                case "partial":
                    output += await self.render_partial(key, frame, output)
        return output


async def async_render(
    template="",
    data={},
    partials_path=None,
    partials_ext="mustache",
    partials_dict={},
    padding="",
    def_ldel="{{",
    def_rdel="}}",
    scopes=None,
    warn=False,
    lambdas=None,
    *,
    logger=None,
    log_level=logging.WARNING,
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
