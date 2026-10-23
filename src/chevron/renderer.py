from collections.abc import (
    AsyncIterable,
    Callable,
    Generator,
    Iterator,
    Mapping,
    Sequence,
)
from dataclasses import dataclass, field
from functools import update_wrapper
import inspect
import logging
from pathlib import Path
from types import TracebackType
from typing import Any, Protocol, TypeAlias, cast

from .tokenizer import ChevronError, tokenize as _tokenize

_MISSING = object()
_INVERTED_SECTION_MARKER = object()
_SKIPPED_SECTION_MARKER = object()
_FUNCTION_PROTOCOL = "function"
_SECTION_PROTOCOL = "section"
_COMPAT_PROTOCOL = "compat"
_LOGGER_NAME = "chevron"
_DEFAULT_LOGGER = logging.getLogger(_LOGGER_NAME)

TemplateData: TypeAlias = Any
"""A value exposed to Mustache lookup, intentionally dynamically typed."""

Scope: TypeAlias = TemplateData
ScopeSequence: TypeAlias = Sequence[Scope]
NormalisedScopes: TypeAlias = tuple[Scope, ...]
Token: TypeAlias = tuple[str, str] | tuple[str, str, str]
TokenSequence: TypeAlias = Sequence[Token]
TokenIterator: TypeAlias = Iterator[Token]
TemplateInput: TypeAlias = TemplateData
PartialMapping: TypeAlias = Mapping[str, TemplateInput]
LambdaCallback: TypeAlias = Callable[..., TemplateData]
LambdaRegistry: TypeAlias = Mapping[str, LambdaCallback]
Logger: TypeAlias = logging.Logger | logging.LoggerAdapter[logging.Logger]
TemplateReader: TypeAlias = Callable[[], TemplateData]


class _RenderLogger(logging.LoggerAdapter[Logger]):
    """Apply one render's diagnostic threshold to its selected logger."""

    def __init__(self, logger: Logger, log_level: int) -> None:
        super().__init__(logger, {})
        self.log_level = log_level

    def log(
        self,
        level: int,
        msg: object,
        *args: object,
        exc_info: (
            None
            | bool
            | BaseException
            | tuple[type[BaseException], BaseException, TracebackType | None]
            | tuple[None, None, None]
        ) = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        if level >= self.log_level:
            super().log(
                level,
                msg,
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra,
                **kwargs,
            )


@dataclass
class _LambdaDefinition:
    """A callable together with its declared template protocol."""

    callback: LambdaCallback
    protocol: str
    __wrapped__: LambdaCallback = field(init=False)

    def __post_init__(self) -> None:
        update_wrapper(self, self.callback)
        callback_type = type(self.callback)
        self.__module__ = getattr(self.callback, "__module__", callback_type.__module__)
        self.__name__ = getattr(self.callback, "__name__", callback_type.__name__)
        self.__qualname__ = getattr(
            self.callback, "__qualname__", callback_type.__qualname__
        )
        self.__doc__ = getattr(self.callback, "__doc__", callback_type.__doc__)
        self.__annotations__ = getattr(self.callback, "__annotations__", {})

    def __call__(self, *args: TemplateData, **kwargs: TemplateData) -> TemplateData:
        return self.callback(*args, **kwargs)

    def __get__(
        self, instance: object, owner: type[object] | None
    ) -> "_LambdaDefinition":
        descriptor = getattr(self.callback, "__get__", None)
        if descriptor is None:
            return self
        return _LambdaDefinition(descriptor(instance, owner), self.protocol)


def _declare_lambda(callback: LambdaCallback, protocol: str) -> _LambdaDefinition:
    if not isinstance(callback, Callable):
        raise TypeError("lambda decorators require a callable")
    return _LambdaDefinition(callback, protocol)


def func(callback: LambdaCallback) -> _LambdaDefinition:
    """Declare a zero-argument Mustache interpolation lambda."""

    return _declare_lambda(callback, _FUNCTION_PROTOCOL)


def section(callback: LambdaCallback) -> _LambdaDefinition:
    """Declare a one-argument Mustache section lambda."""

    return _declare_lambda(callback, _SECTION_PROTOCOL)


def compat(callback: LambdaCallback) -> _LambdaDefinition:
    """Declare Chevron's legacy two-argument section-lambda protocol."""

    return _declare_lambda(callback, _COMPAT_PROTOCOL)


def _lambda_protocol(value: TemplateData, tag: str) -> str | None:
    """Resolve a callable's protocol without invoking it."""

    if isinstance(value, _LambdaDefinition):
        return value.protocol

    if tag == "section":
        return _COMPAT_PROTOCOL
    return None


def _normalise_value(key: str, value: TemplateData) -> TemplateData:
    """Apply Chevron's historic falsey-value rendering behaviour."""

    if value is _MISSING:
        return ""

    if key == ".":
        return value

    if value in (0, False):
        return value

    if getattr(value, "_CHEVRON_return_scope_when_falsy", False):
        return value

    return value or ""


def _close_awaitable(result: TemplateData) -> None:
    """Dispose of an awaitable that Chevron cannot consume."""
    close = getattr(result, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


def _reject_awaitable_lambda_result(result: TemplateData, key: str) -> TemplateData:
    """Keep awaitable lambda results within the asynchronous renderer."""
    if not inspect.isawaitable(result):
        return result

    _close_awaitable(result)
    raise TypeError(
        f"Lambda '{key}' returned an awaitable; use chevron.async_render instead"
    )


def _read_template_result(result: TemplateData) -> str:
    """Normalise the established falsey reader results and validate all others."""
    if not result and not isinstance(result, str):
        return ""
    if not isinstance(result, str):
        raise TypeError("template readers must return text")
    return result


def _read_sync_template(reader: TemplateReader) -> str:
    """Read synchronous input without allowing an awaitable to escape."""
    result = reader()
    if inspect.isawaitable(result):
        _close_awaitable(result)
        raise TypeError(
            "Template reader returned an awaitable; use chevron.async_render instead"
        )
    return _read_template_result(result)


def _html_escape(string: str) -> str:
    """HTML escape all of these " & < >"""

    html_codes = {
        '"': "&quot;",
        "<": "&lt;",
        ">": "&gt;",
    }

    # & must be handled first
    string = string.replace("&", "&amp;")
    for char in html_codes:
        string = string.replace(char, html_codes[char])
    return string


def _current_scope(frame: "_RenderFrame | None") -> TemplateData:
    """Return the nearest application scope for current-context lookup."""
    while frame is not None and frame.scope is _INVERTED_SECTION_MARKER:
        frame = frame.parent
    return _MISSING if frame is None else frame.scope


def _get_key(
    key: str,
    frame: "_RenderFrame",
    logger: _RenderLogger,
    allow_callable_traversal: bool = True,
    value_handler: Callable[[TemplateData], TemplateData] | None = None,
    log_resolution: bool = True,
) -> TemplateData:
    """Get a key from the current scope."""

    blocked_callable_traversal = False

    # If the key is a dot
    if key == ".":
        # Then just return the current scope
        scope = _current_scope(frame)
        if log_resolution:
            logger.debug("Resolved current template scope")
        return value_handler(scope) if value_handler is not None else scope

    # Loop through the scopes
    current_frame = frame
    while current_frame is not None:
        scope = current_frame.scope
        index = 0
        try:
            # For every dot-separated key
            for index, child in enumerate(key.split(".")):
                if not allow_callable_traversal and isinstance(scope, Callable):
                    blocked_callable_traversal = True
                    raise KeyError("callable values are lookup leaves")

                # Move into the scope
                try:
                    # Try subscripting (Normal dictionaries)
                    scope = scope[child]
                except (TypeError, AttributeError):
                    try:
                        provisional_scope = getattr(scope, child)
                        if callable(provisional_scope):
                            raise TypeError("skipping callable")
                        scope = provisional_scope
                    except (TypeError, AttributeError):
                        # Try as a list
                        if not isinstance(scope, Sequence):
                            raise KeyError(child)
                        scope = scope[int(child)]
        except (AttributeError, KeyError, IndexError, ValueError):
            if index:
                break
            current_frame = current_frame.parent
            continue

        try:
            value = value_handler(scope) if value_handler is not None else scope
        except (AttributeError, KeyError, IndexError, ValueError):
            # Lookup and value normalisation both preserve fallback behaviour.
            current_frame = current_frame.parent
            continue

        if log_resolution:
            logger.debug("Resolved template name '%s' from template data", key)
        return value

    # We couldn't find the key in any of the scopes

    if log_resolution:
        logger.debug("Template name '%s' was not found", key)
        if blocked_callable_traversal:
            logger.warning(
                "Could not resolve '%s': callable values cannot be traversed "
                "when lambdas= is supplied",
                key,
            )
        else:
            logger.warning("Could not find key '%s'", key)

    return value_handler(_MISSING) if value_handler is not None else _MISSING


def _get_partial(
    name: str,
    partials_dict: PartialMapping,
    partials_path: str | Path | None,
    partials_ext: str,
    logger: _RenderLogger,
    *,
    dynamic: bool = False,
) -> TemplateInput:
    """Load a partial"""
    try:
        # Maybe the partial is in the dictionary
        partial = partials_dict[name]
        if dynamic:
            logger.debug("Resolved dynamic partial from configured partials")
        else:
            logger.debug("Resolved partial '%s' from configured partials", name)
        return partial
    except KeyError:
        return _get_filesystem_partial(
            name, partials_path, partials_ext, logger, dynamic=dynamic
        )


def _filesystem_partial_name(name: str, partials_ext: str) -> Path | None:
    """Return a lexical-safe partial path relative to its configured root."""
    path_ext = "." + partials_ext if partials_ext else ""
    partial_name = Path(name + path_ext)
    if partial_name.is_absolute() or ".." in partial_name.parts:
        return None
    return partial_name


def _filesystem_partial_rejection_reason(name: str, partials_ext: str) -> str | None:
    """Return the safe lexical rejection reason for a partial reference."""
    path_ext = "." + partials_ext if partials_ext else ""
    partial_name = Path(name + path_ext)
    if partial_name.is_absolute():
        return "absolute path"
    if ".." in partial_name.parts:
        return "parent traversal"
    return None


def _get_filesystem_partial(
    name: str,
    partials_path: str | Path | None,
    partials_ext: str,
    logger: _RenderLogger,
    *,
    dynamic: bool = False,
) -> str:
    """Load a partial from the configured filesystem path."""
    # Don't try loading from the file system if the partials_path is None or empty
    if partials_path is None or partials_path == "":
        if dynamic:
            logger.debug("Dynamic partial was not configured")
        else:
            logger.debug("Partial '%s' was not configured", name)
        return ""

    try:
        base_path = Path(partials_path).resolve(strict=True)
        partial_name = _filesystem_partial_name(name, partials_ext)
        if partial_name is None:
            reason = _filesystem_partial_rejection_reason(name, partials_ext)
            if dynamic:
                logger.debug("Rejected dynamic partial reference: %s", reason)
            else:
                logger.debug("Rejected partial reference '%s': %s", name, reason)
            return ""

        partial_path = (base_path / partial_name).resolve(strict=True)
        partial_path.relative_to(base_path)
        with partial_path.open("r", encoding="utf-8") as partial:
            content = partial.read()
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


@dataclass(frozen=True)
class _RenderConfig:
    """Settings shared by all recursive operations in one public render."""

    partials_path: str | Path | None
    partials_ext: str
    partials_dict: PartialMapping
    logger: _RenderLogger
    default_delimiters: tuple[str, str]


@dataclass(frozen=True)
class _RenderFrame:
    """One private scope binding and its render context."""

    scope: Scope
    parent: "_RenderFrame | None"
    delimiters: tuple[str, str]
    padding: str = ""

    @classmethod
    def from_scopes(
        cls,
        scopes: ScopeSequence,
        delimiters: tuple[str, str],
        padding: str = "",
    ) -> "_RenderFrame":
        """Create a private frame chain without mutating the input collection."""
        if isinstance(scopes, (str, bytes, bytearray)) or not isinstance(
            scopes, Sequence
        ):
            raise TypeError("scopes must be a sequence")
        values: NormalisedScopes = tuple(scopes)
        if not values:
            values = ({},)
        frame = cls(values[-1], None, delimiters, padding)
        for scope in reversed(values[:-1]):
            frame = cls(scope, frame, delimiters, padding)
        return frame

    def child(
        self,
        scope: Scope,
        delimiters: tuple[str, str] | None = None,
        padding: str | None = None,
    ) -> "_RenderFrame":
        """Return a nested scope frame, preserving the current chain."""
        return _RenderFrame(
            scope,
            self,
            self.delimiters if delimiters is None else delimiters,
            self.padding if padding is None else padding,
        )

    def with_context(
        self, delimiters: tuple[str, str], padding: str | None = None
    ) -> "_RenderFrame":
        """Return this scope chain with a recursive render context."""
        return _RenderFrame(
            self.scope,
            self.parent,
            delimiters,
            self.padding if padding is None else padding,
        )


@dataclass
class _RenderState:
    """Compatibility token reuse shared by recursive render frames."""

    token_cache: dict[str, list[Token]] = field(default_factory=dict)


def _validated_tokens(tokens: TokenSequence) -> TokenIterator:
    """Yield direct token input after enforcing Chevron's public token shapes."""

    for token in tokens:
        if isinstance(token, str):
            raise TypeError("template tokens must be non-string sequences")
        match len(token):
            case 2 | 3:
                yield token
            case _:
                raise TypeError("template tokens must contain two or three values")


class _SourcePolicy(Protocol):
    def resolve(
        self,
        key: str,
        frame: _RenderFrame,
        value_handler: Callable[[TemplateData], TemplateData],
        log_resolution: bool = True,
    ) -> tuple[TemplateData, bool]:
        """Return the value and whether it came from the explicit mapping."""
        ...


@dataclass
class _PermissiveSource:
    logger: _RenderLogger

    def resolve(
        self,
        key: str,
        frame: _RenderFrame,
        value_handler: Callable[[TemplateData], TemplateData],
        log_resolution: bool = True,
    ) -> tuple[TemplateData, bool]:
        return _get_key(
            key,
            frame,
            logger=self.logger,
            value_handler=value_handler,
            log_resolution=log_resolution,
        ), False


class _ExplicitSource:
    def __init__(self, lambdas: LambdaRegistry, logger: _RenderLogger) -> None:
        if not isinstance(lambdas, Mapping):
            raise TypeError("lambdas must be a mapping of template names to callables")
        self.lambdas = dict(lambdas)
        self.logger = logger
        for name, definition in self.lambdas.items():
            if not isinstance(name, str):
                raise TypeError("lambdas mapping keys must be strings")
            if not isinstance(definition, Callable):
                raise TypeError("lambdas mapping values must be callable")

    def resolve(
        self,
        key: str,
        frame: _RenderFrame,
        value_handler: Callable[[TemplateData], TemplateData],
        log_resolution: bool = True,
    ) -> tuple[TemplateData, bool]:
        if key in self.lambdas:
            if log_resolution:
                self.logger.debug(
                    "Resolved template name '%s' from the lambda mapping", key
                )
            return self.lambdas[key], True

        def handle_value(value: TemplateData) -> TemplateData:
            if isinstance(value, Callable):
                if log_resolution:
                    self.logger.warning(
                        "Callable template data '%s' is rejected when lambdas= is supplied",
                        key,
                    )
                return ""
            return value_handler(value)

        return _get_key(
            key,
            frame,
            logger=self.logger,
            allow_callable_traversal=False,
            value_handler=handle_value,
            log_resolution=log_resolution,
        ), False


def _partial_name(
    key: str,
    frame: _RenderFrame,
    policy: _SourcePolicy,
    logger: _RenderLogger,
) -> str | None:
    """Resolve one dynamic partial name without changing the active frame."""
    if not key.startswith("*"):
        return key
    if key.startswith("**"):
        logger.debug("Dynamic partial selector requested nested dereferencing")
        return None

    dynamic_key = key[1:].strip()
    if not dynamic_key:
        logger.debug("Dynamic partial selector was empty")
        return None
    value, _ = policy.resolve(
        dynamic_key,
        frame,
        lambda resolved: _normalise_value(dynamic_key, resolved),
        log_resolution=False,
    )
    if isinstance(value, str) and value:
        return value
    logger.debug("Dynamic partial selector did not resolve to a non-empty string")
    return None


def _prepare_render_context(
    data: TemplateData,
    partials_path: str | Path | None,
    partials_ext: str,
    partials_dict: PartialMapping,
    padding: str,
    def_ldel: str,
    def_rdel: str,
    scopes: ScopeSequence | None,
    warn: TemplateData,
    lambdas: LambdaRegistry | None,
    logger: Logger | None,
    log_level: int,
) -> tuple[_RenderConfig, _SourcePolicy, _RenderFrame]:
    """Build the shared per-render configuration, policy, and root frame."""
    if logger is not None and not isinstance(
        logger, (logging.Logger, logging.LoggerAdapter)
    ):
        raise TypeError("logger must be a logging.Logger or logging.LoggerAdapter")
    if type(log_level) is not int:
        raise TypeError("log_level must be an integer")

    selected_logger = logger if logger is not None else _DEFAULT_LOGGER
    selected_log_level = (
        log_level
        if logger is not None
        else logging.WARNING
        if warn
        else logging.CRITICAL + 1
    )
    diagnostics = _RenderLogger(selected_logger, selected_log_level)
    config = _RenderConfig(
        partials_path,
        partials_ext,
        partials_dict,
        diagnostics,
        (def_ldel, def_rdel),
    )
    policy = (
        _PermissiveSource(diagnostics)
        if lambdas is None
        else _ExplicitSource(lambdas, diagnostics)
    )
    frame = _RenderFrame.from_scopes(
        scopes if scopes is not None else [data], config.default_delimiters, padding
    )
    return config, policy, frame


_TAG_SYMBOLS = {
    "comment": "!",
    "section": "#",
    "inverted section": "^",
    "end": "/",
    "partial": ">",
    "set delimiter": "=",
    "variable": "",
}


def _changed_delimiters(key: str) -> tuple[str, str]:
    delimiters = key.split()
    return delimiters[0], delimiters[-1]


@dataclass
class _SectionBody:
    """Collected tokens with lexical delimiter boundaries, not a parsed AST."""

    tokens: list[Token]
    opening: tuple[str, str]
    ending: tuple[str, str]

    def source(self) -> str:
        parts = []
        left, right = self.opening
        for token in self.tokens:
            tag, key = token[:2]
            raw = token[2] if len(token) == 3 else None
            if raw is not None:
                parts.append(raw)
            elif tag == "literal":
                parts.append(key)
            elif tag == "no escape":
                parts.append(f"{left}&{key}{right}")
            else:
                parts.append(f"{left}{_TAG_SYMBOLS[tag]}{key}{right}")
            if tag == "set delimiter":
                left, right = _changed_delimiters(key)
        return "".join(parts)

    def compatibility(self, delimiters: tuple[str, str]) -> tuple[str, list[Token]]:
        left, right = delimiters
        parts = []
        tokens: list[Token] = []
        for token in self.tokens:
            tag, key = token[:2]
            if tag == "comment" or (tag == "literal" and key == ""):
                continue
            tokens.append(token)
            if tag == "literal":
                parts.append(key)
            elif tag == "no escape":
                parts.append(f"{left}& {key} {right}")
            else:
                parts.append(f"{left}{_TAG_SYMBOLS[tag]} {key}{right}")
        return "".join(parts), tokens


def _collect_section(
    tokens: TokenIterator, key: str, delimiters: tuple[str, str]
) -> _SectionBody:
    body: list[Token] = []
    depth = 0
    ending = delimiters
    for token in tokens:
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


class ChevronRender:
    """Composed rendering engine; chevron.render remains the primary entry point."""

    def __init__(self, config: _RenderConfig, policy: _SourcePolicy) -> None:
        self.config = config
        self.policy = policy
        self.state = _RenderState()

    def render(self, template: TemplateInput, frame: _RenderFrame) -> str:
        """Render source or tokens using the supplied immutable frame chain."""
        token_stream: Generator[Token, None, None] | None = None
        try:
            if isinstance(template, (bytes, bytearray)):
                raise TypeError("templates must be text")
            if isinstance(template, Sequence) and not isinstance(template, str):
                tokens = _validated_tokens(template)
            else:
                reader = getattr(template, "read", None)
                if reader is not None:
                    template = _read_sync_template(reader)
                if not template and not isinstance(template, str):
                    template = ""
                token_stream = _tokenize(template, *frame.delimiters, include_raw=True)
                tokens = token_stream
            return self.render_tokens(tokens, frame)
        finally:
            if token_stream is not None:
                token_stream.close()

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

    def render_result(self, result: TemplateData, key: str, frame: _RenderFrame) -> str:
        result = _reject_awaitable_lambda_result(result, key)
        if result is None:
            return self.empty_result(key)
        return self.render(result if isinstance(result, str) else str(result), frame)

    def interpolation(self, key: str, frame: _RenderFrame) -> TemplateData:
        value, explicit = self.resolve(key, frame)
        if not isinstance(value, Callable):
            return value
        protocol = _lambda_protocol(value, "interpolation")
        self.config.logger.debug(
            "Selected %s lambda protocol for '%s'", protocol or "unsupported", key
        )
        if protocol == _FUNCTION_PROTOCOL:
            result_frame = frame.with_context(self.config.default_delimiters, "")
            return self.render_result(value(), key, result_frame)
        if explicit or isinstance(value, _LambdaDefinition):
            return ""
        return value

    def standard_section(
        self,
        callback: LambdaCallback,
        key: str,
        body: _SectionBody,
        frame: _RenderFrame,
    ) -> str:
        result_frame = frame.with_context(body.opening, frame.padding)
        return self.render_result(callback(body.source()), key, result_frame)

    def compatibility_section(
        self,
        callback: LambdaCallback,
        key: str,
        body: _SectionBody,
        frame: _RenderFrame,
    ) -> str:
        text, tokens = body.compatibility(frame.delimiters)
        self.state.token_cache[text] = tokens

        def render_callback(
            template: TemplateInput, data: TemplateData | None = None
        ) -> str:
            child = frame.with_context(self.config.default_delimiters, frame.padding)
            if data:
                child = child.child(data)
            return self.compatibility_render(template, child)

        result = _reject_awaitable_lambda_result(callback(text, render_callback), key)
        return self.empty_result(key) if result is None else cast(str, result)

    def compatibility_render(self, template: TemplateInput, frame: _RenderFrame) -> str:
        """Only legacy callbacks replay the invocation's reconstructed tokens."""
        if not template and not isinstance(template, (str, Sequence)):
            template = ""
        if isinstance(template, str) and template in self.state.token_cache:
            template = self.state.token_cache[template]
        return self.render(template, frame)

    _section_handlers = {
        _SECTION_PROTOCOL: standard_section,
        _COMPAT_PROTOCOL: compatibility_section,
    }

    def render_section(
        self,
        key: str,
        tokens: TokenIterator,
        frame: _RenderFrame,
        delimiters: tuple[str, str],
    ) -> tuple[str, tuple[str, str], _RenderFrame]:
        value, _ = self.resolve(key, frame)
        if isinstance(value, Callable):
            body = _collect_section(tokens, key, delimiters)
            protocol = _lambda_protocol(value, "section")
            self.config.logger.debug(
                "Selected %s lambda protocol for '%s'", protocol or "unsupported", key
            )
            handler = self._section_handlers.get(protocol)
            result = (
                handler(self, value, key, body, frame) if handler is not None else ""
            )
            return result, body.ending, frame
        if isinstance(value, AsyncIterable):
            raise TypeError(
                f"Section '{key}' resolved to an async iterable; "
                "use chevron.async_render instead"
            )
        if isinstance(value, (Sequence, Iterator)) and not isinstance(value, str):
            body = _collect_section(tokens, key, delimiters)
            output = ""
            for item in value:
                child = frame.child(item, body.opening, frame.padding)
                output += self.render(body.tokens, child)
            return output, body.ending, frame
        return "", delimiters, frame.child(value if value else _SKIPPED_SECTION_MARKER)

    def render_partial(self, key: str, frame: _RenderFrame, output: str) -> str:
        config = self.config
        dynamic = key.startswith("*")
        name = _partial_name(key, frame, self.policy, config.logger)
        if name is None:
            return ""
        partial = _get_partial(
            name,
            config.partials_dict,
            config.partials_path,
            config.partials_ext,
            config.logger,
            dynamic=dynamic,
        )
        left = output.rpartition("\n")[2]
        padding = frame.padding + left if left.isspace() else frame.padding
        child = frame.with_context(config.default_delimiters, padding)
        result = self.render(partial, child)
        return result.rstrip(" \t") if left.isspace() else result

    def render_tokens(self, tokens: TokenIterator, frame: _RenderFrame) -> str:
        output = ""
        delimiters = frame.delimiters
        for token in tokens:
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
                    value = self.interpolation(key, frame)
                    text = value if isinstance(value, str) else str(value)
                    output += _html_escape(text) if tag == "variable" else text
                case "section":
                    result, delimiters, frame = self.render_section(
                        key, tokens, frame, delimiters
                    )
                    output += result
                case "inverted section":
                    value, _ = self.policy.resolve(
                        key, frame, lambda value: _normalise_value(key, value)
                    )
                    if isinstance(value, AsyncIterable):
                        raise TypeError(
                            f"Section '{key}' resolved to an async iterable; "
                            "use chevron.async_render instead"
                        )
                    frame = frame.child(
                        _INVERTED_SECTION_MARKER
                        if not value
                        else _SKIPPED_SECTION_MARKER
                    )
                case "partial":
                    output += self.render_partial(key, frame, output)
        return output


def render(
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
    """Render a mustache template.

    Renders a mustache template with a data scope and partial capability.
    Given the file structure...
    ╷
    ├─╼ main.py
    ├─╼ main.ms
    └─┮ partials
      └── part.ms

    then main.py would make the following call:

    render(open('main.ms', 'r'), {...}, 'partials', 'ms')


    Arguments:

    template      -- A file-like object or a string containing the template

    data          -- A python dictionary with your data scope

    partials_path -- The path to where your partials are stored
                     If set to None, then partials won't be loaded from the file system
                     (defaults to None). Supply '.' to restore the historic
                     process-current-directory lookup behaviour.

    partials_ext  -- The extension that you want the parser to look for
                     (defaults to 'mustache')

    partials_dict -- A python dictionary which will be search for partials
                     before the filesystem is. {'include': 'foo'} is the same
                     as a file called include.mustache
                     (defaults to {})

    padding       -- This is for padding partials, and shouldn't be used
                     (but can be if you really want to)

    def_ldel      -- The default left delimiter
                     ("{{" by default, as in spec compliant mustache)

    def_rdel      -- The default right delimiter
                     ("}}" by default, as in spec compliant mustache)

    scopes        -- The list of scopes that get_key will look through

    warn -- Select Chevron's default diagnostic logger using its historic truthiness
            behaviour. It remains silent by default when no logger is supplied.

    lambdas -- Optional mapping defining callable template names. In explicit mode,
               mapped names take precedence over template data. Use chevron.func for
               zero-argument interpolation lambdas, chevron.section for standard
               one-argument section lambdas, and chevron.compat for Chevron's
               original two-argument section callbacks. Callable values in template
               data are rejected; supplying an empty mapping disables callable
               execution. When omitted, callable values reached through template
               context retain compatibility behaviour.

    logger -- Optional `logging.Logger` or `logging.LoggerAdapter` for diagnostics.
              It replaces Chevron's default logger regardless of warn. Chevron
              leaves its handlers, levels and propagation under application control.

    log_level -- Lowest numeric standard-library logging level Chevron sends to a
                 supplied logger. Defaults to `logging.WARNING`.


    Returns:

    A string containing the rendered template.
    """

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
    engine = ChevronRender(config, policy)
    config.logger.info("Render started")
    try:
        result = engine.render(template, frame)
    except ChevronError as error:
        config.logger.error("Template rendering failed: %s", error)
        raise
    config.logger.info("Render completed successfully")
    return result
