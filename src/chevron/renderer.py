from collections.abc import (
    AsyncIterable,
    Callable,
    Iterator,
    Mapping,
    Sequence,
    Sized,
)
from dataclasses import dataclass, field
from functools import update_wrapper
import inspect
import logging
from pathlib import Path
from types import MappingProxyType, TracebackType
from typing import Any, Generic, Protocol, TypeAlias, TypeVar, cast

from .extensions import Extension
from .tokenizer import ChevronError, tokenize as _tokenize

_MISSING = object()
_INVERTED_SECTION_MARKER = object()
_SKIPPED_SECTION_MARKER = object()
_FUNCTION_PROTOCOL = "function"
_SECTION_PROTOCOL = "section"
_COMPAT_PROTOCOL = "compat"
_LOGGER_NAME = "chevron"
_DEFAULT_LOGGER = logging.getLogger(_LOGGER_NAME)
_MAX_ACTIVE_WORK = 10_000
_END_OF_TOKENS = object()
_BODY_OPENERS = frozenset(("section", "inverted section", "parent", "block"))

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
ContinuationResult = TypeVar("ContinuationResult")


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


def _current_scope_frame(frame: "_RenderFrame | None") -> "_RenderFrame | None":
    """Return the nearest frame carrying an application scope."""
    while frame is not None and frame.scope is _INVERTED_SECTION_MARKER:
        frame = frame.parent
    return frame


def _get_key(
    key: str,
    frame: "_RenderFrame",
    logger: _RenderLogger,
    allow_callable_traversal: bool = True,
    value_handler: Callable[[TemplateData], TemplateData] | None = None,
    log_resolution: bool = True,
) -> tuple[TemplateData, "_RenderFrame | None"]:
    """Get a key and the frame that supplied its direct binding."""

    blocked_callable_traversal = False

    if key.startswith(".") and key != ".":
        metadata, metadata_frame = _iteration_metadata_value(key, frame)
        if metadata is not _MISSING:
            value = value_handler(metadata) if value_handler is not None else metadata
            if log_resolution:
                logger.debug("Resolved iteration metadata '%s'", key)
            return value, metadata_frame

    # If the key is a dot
    if key == ".":
        # Then just return the current scope
        current_frame = _current_scope_frame(frame)
        scope = _MISSING if current_frame is None else current_frame.scope
        if log_resolution:
            logger.debug("Resolved current template scope")
        value = value_handler(scope) if value_handler is not None else scope
        return value, current_frame

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
            if index:
                break
            # Direct-name value normalisation preserves fallback behaviour.
            current_frame = current_frame.parent
            continue

        if log_resolution:
            logger.debug("Resolved template name '%s' from template data", key)
        return value, current_frame

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

    value = value_handler(_MISSING) if value_handler is not None else _MISSING
    return value, None


def _get_partial(
    name: str,
    partials_dict: PartialMapping,
    partials_path: str | Path | None,
    partials_ext: str,
    logger: _RenderLogger,
    *,
    dynamic: bool = False,
    kind: str = "partial",
) -> TemplateInput:
    """Load a partial-like template."""
    partial = _configured_partial(
        name, partials_dict, logger, dynamic=dynamic, kind=kind
    )
    if partial is not _MISSING:
        return partial
    return _get_filesystem_partial(
        name, partials_path, partials_ext, logger, dynamic=dynamic, kind=kind
    )


def _configured_partial(
    name: str,
    partials_dict: PartialMapping,
    logger: _RenderLogger,
    *,
    dynamic: bool = False,
    kind: str = "partial",
) -> TemplateInput | object:
    """Return a configured partial, or the private missing sentinel.

    This pure mapping lookup is shared by both renderers; their filesystem
    fallback remains explicit because synchronous and AnyIO I/O differ.
    """
    try:
        partial = partials_dict[name]
    except KeyError:
        return _MISSING
    if dynamic:
        logger.debug("Resolved dynamic %s from configured partials", kind)
    else:
        logger.debug("Resolved %s '%s' from configured partials", kind, name)
    return partial


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
    kind: str = "partial",
) -> str:
    """Load a partial from the configured filesystem path."""
    # Don't try loading from the file system if the partials_path is None or empty
    if partials_path is None or partials_path == "":
        if dynamic:
            logger.debug("Dynamic %s was not configured", kind)
        else:
            logger.debug("%s '%s' was not configured", kind.capitalize(), name)
        return ""

    try:
        base_path = Path(partials_path).resolve(strict=True)
        partial_name = _filesystem_partial_name(name, partials_ext)
        if partial_name is None:
            reason = _filesystem_partial_rejection_reason(name, partials_ext)
            if dynamic:
                logger.debug("Rejected dynamic %s reference: %s", kind, reason)
            else:
                logger.debug("Rejected %s reference '%s': %s", kind, name, reason)
            return ""

        partial_path = (base_path / partial_name).resolve(strict=True)
        partial_path.relative_to(base_path)
        with partial_path.open("r", encoding="utf-8") as partial:
            content = partial.read()
        if dynamic:
            logger.debug("Resolved dynamic %s from the configured path", kind)
        else:
            logger.debug("Resolved %s '%s' from the configured path", kind, name)
        return content

    except (OSError, RuntimeError, ValueError):
        if dynamic:
            logger.debug("Dynamic %s was unavailable", kind)
        else:
            logger.debug("%s '%s' was unavailable", kind.capitalize(), name)
        return ""


@dataclass(frozen=True)
class _RenderConfig:
    """Settings shared by all recursive operations in one public render."""

    partials_path: str | Path | None
    partials_ext: str
    partials_dict: PartialMapping
    logger: _RenderLogger
    default_delimiters: tuple[str, str]


def _iteration_metadata_value(
    key: str, frame: "_RenderFrame"
) -> tuple[TemplateData | object, "_RenderFrame | None"]:
    """Find the nearest repeated-section metadata binding for one name."""
    current_frame: _RenderFrame | None = frame
    while current_frame is not None:
        source = current_frame.iteration_source
        if source is not _MISSING:
            match key:
                case ".first":
                    return current_frame.iteration_index == 0, current_frame
                case ".last":
                    last = current_frame.iteration_last
                    if last is None:
                        length = _source_length(source)
                        last = (
                            length is not None
                            and current_frame.iteration_index == length - 1
                        )
                    return last, current_frame
                case ".index":
                    return current_frame.iteration_index, current_frame
                case ".ordinal":
                    return current_frame.iteration_index + 1, current_frame
                case ".length":
                    return _source_length(source), current_frame
            numeric = key[1:]
            if not numeric.isdecimal():
                return None, current_frame
            try:
                index = int(numeric)
            except ValueError:
                return None, current_frame
            length = _source_length(source)
            item_at = getattr(source, "__getitem__", None)
            if length is None or index >= length or not callable(item_at):
                return None, current_frame
            try:
                return item_at(index), current_frame
            except (IndexError, KeyError, TypeError):
                return None, current_frame
        current_frame = current_frame.parent
    return _MISSING, None


def _source_length(value: TemplateData) -> int | None:
    """Return a non-consuming source length while retaining mapping semantics."""
    return (
        len(value)
        if isinstance(value, Sized) and not isinstance(value, Mapping)
        else None
    )


@dataclass(frozen=True)
class _RenderFrame:
    """One private scope binding and its render context."""

    scope: Scope
    parent: "_RenderFrame | None"
    delimiters: tuple[str, str]
    padding: str = ""
    overrides: Mapping[str, "_SectionBody"] = field(default_factory=dict)
    iterator_states: dict[str, "_IteratorState"] = field(
        default_factory=dict, compare=False, repr=False
    )
    async_iterator_states: dict[str, object] = field(
        default_factory=dict, compare=False, repr=False
    )
    iteration_source: TemplateData | object = field(
        default=_MISSING, compare=False, repr=False
    )
    iteration_index: int = field(default=0, compare=False, repr=False)
    iteration_last: bool | None = field(default=None, compare=False, repr=False)

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
        iteration_source: TemplateData | object = _MISSING,
        iteration_index: int = 0,
        iteration_last: bool | None = None,
    ) -> "_RenderFrame":
        """Return a nested scope frame, preserving the current chain."""
        return _RenderFrame(
            scope,
            self,
            self.delimiters if delimiters is None else delimiters,
            self.padding if padding is None else padding,
            self.overrides,
            iteration_source=iteration_source,
            iteration_index=iteration_index,
            iteration_last=iteration_last,
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
            self.overrides,
            self.iterator_states,
            self.async_iterator_states,
            self.iteration_source,
            self.iteration_index,
            self.iteration_last,
        )

    def with_overrides(self, overrides: Mapping[str, "_SectionBody"]) -> "_RenderFrame":
        """Return this context with parent-local block overrides applied."""
        combined = dict(overrides)
        combined.update(self.overrides)
        return _RenderFrame(
            self.scope,
            self.parent,
            self.delimiters,
            self.padding,
            MappingProxyType(combined),
            self.iterator_states,
            self.async_iterator_states,
            self.iteration_source,
            self.iteration_index,
            self.iteration_last,
        )

    def without_override(self, key: str) -> "_RenderFrame":
        """Return a frame where one active block override is masked."""
        if key not in self.overrides:
            return self
        overrides = dict(self.overrides)
        del overrides[key]
        return _RenderFrame(
            self.scope,
            self.parent,
            self.delimiters,
            self.padding,
            MappingProxyType(overrides),
            self.iterator_states,
            self.async_iterator_states,
            self.iteration_source,
            self.iteration_index,
            self.iteration_last,
        )


@dataclass
class _IteratorState:
    """One synchronous render cursor with tri-state emptiness."""

    iterator: Iterator[TemplateData]
    sized: bool
    empty: bool | None = None
    first_item: TemplateData | object = _MISSING

    def is_empty(self) -> bool | None:
        """Return unknown, non-empty, or empty without advancing the cursor."""
        return self.empty

    def probe(self) -> bool:
        """Determine emptiness without losing a first yielded item."""
        if self.empty is None:
            try:
                self.first_item = next(self.iterator)
            except StopIteration:
                self.empty = True
            else:
                self.empty = False
        return self.empty

    def __next__(self) -> TemplateData:
        """Yield the buffered item, then continue through the source iterator."""
        if self.first_item is not _MISSING:
            item = self.first_item
            self.first_item = _MISSING
            return item
        try:
            item = next(self.iterator)
        except StopIteration:
            if self.empty is None:
                self.empty = True
            raise
        self.empty = False
        return item

    def next_with_last(self) -> tuple[TemplateData, bool | None]:
        """Yield one item and retain bounded lookahead for an unsized source."""
        item = next(self)
        if self.sized:
            return item, None
        try:
            self.first_item = next(self.iterator)
        except StopIteration:
            return item, True
        return item, False


@dataclass
class _RenderState:
    """Private state shared by one renderer instance."""

    token_cache: dict[str, list[Token]] = field(default_factory=dict)


def _iterator_state(
    frame: _RenderFrame, key: str, value: Iterator[TemplateData]
) -> _IteratorState:
    """Return the canonical cursor stored on one supplying render frame."""
    if state := frame.iterator_states.get(key):
        return state
    state = _IteratorState(
        iter(value), isinstance(value, Sized) and not isinstance(value, Mapping)
    )
    frame.iterator_states[key] = state
    return state


@dataclass
class _RenderWork(Generic[ContinuationResult]):
    """One active token stream and the state needed to resume it."""

    tokens: TokenIterator
    frame: _RenderFrame
    delimiters: tuple[str, str]
    continuation: Callable[[str, str], ContinuationResult] | None = None
    output: list[str] = field(default_factory=list)
    current_line_padding: list[str] = field(default_factory=list)
    current_line_has_content: bool = False
    current_line_is_whitespace: bool = False
    source_line_has_content: bool = False
    strip_parent_suffix: bool = False
    restore_parent_suffix: bool = False
    terminal_padding: str = ""
    token_close: Callable[[], object] | None = field(init=False, repr=False)

    def __post_init__(self) -> None:
        close = getattr(self.tokens, "close", None)
        self.token_close = close if callable(close) else None

    def close_tokens(self) -> None:
        """Close an owned generator at most once."""
        if self.token_close is not None:
            close, self.token_close = self.token_close, None
            close()

    @classmethod
    def from_tokens(
        cls,
        tokens: TokenIterator,
        frame: _RenderFrame,
        continuation: Callable[[str, str], ContinuationResult] | None = None,
        *,
        source_line_has_content: bool = False,
    ) -> "_RenderWork[ContinuationResult]":
        """Create work whose token context matches its frame."""
        return cls(
            tokens,
            frame,
            frame.delimiters,
            continuation,
            source_line_has_content=source_line_has_content,
        )

    def append(self, text: str, terminal_padding: str = "") -> None:
        """Append output and retain the suffix needed for partial padding."""
        self.output.append(text)
        self.terminal_padding = terminal_padding if text else self.terminal_padding
        line_break = max(text.rfind("\n"), text.rfind("\r"))
        if line_break >= 0:
            self._set_current_line(text[line_break + 1 :])
        elif text:
            self._append_current_line(text)

    def partial_padding(self) -> str:
        """Return current-line indentation when it is whitespace only."""
        return "".join(self.current_line_padding)

    def observe_source_literal(self, token: Token) -> None:
        """Track whether the current source line contains non-whitespace text."""
        text = token[2] if len(token) == 3 else token[1]
        line_break = max(text.rfind("\n"), text.rfind("\r"))
        if line_break >= 0:
            self.source_line_has_content = bool(text[line_break + 1 :].strip())
        elif text.strip():
            self.source_line_has_content = True

    def _set_current_line(self, text: str) -> None:
        self.current_line_has_content = bool(text)
        self.current_line_is_whitespace = text.isspace()
        self.current_line_padding = [text] if self.current_line_is_whitespace else []

    def _append_current_line(self, text: str) -> None:
        if not self.current_line_has_content:
            self._set_current_line(text)
        elif self.current_line_is_whitespace and text.isspace():
            self.current_line_padding.append(text)
        elif not text.isspace():
            self.current_line_is_whitespace = False
            self.current_line_padding.clear()


def _push_work(
    active: list[_RenderWork[ContinuationResult]], work: _RenderWork[ContinuationResult]
) -> None:
    """Push bounded engine-owned work, closing rejected token streams."""
    if len(active) >= _MAX_ACTIVE_WORK:
        work.close_tokens()
        raise RecursionError("nested template expansion exceeded the active-work limit")
    active.append(work)


def _apply_control_token(
    work: _RenderWork[ContinuationResult], tag: str, key: str
) -> bool:
    """Apply context-only tokens and report whether no dispatch remains."""
    if tag == "end":
        if work.frame.parent is not None:
            work.frame = work.frame.parent
        return True
    if tag == "set delimiter":
        work.delimiters = _changed_delimiters(key)
        return True
    if work.frame.scope is _SKIPPED_SECTION_MARKER and work.frame.parent is not None:
        if tag in _BODY_OPENERS:
            work.frame = work.frame.child(_SKIPPED_SECTION_MARKER)
        return True
    return False


def _interpolation_text(value: TemplateData, tag: str) -> str:
    """Normalise and escape one interpolation result."""
    text = value if isinstance(value, str) else str(value)
    return _html_escape(text) if tag == "variable" else text


def _validated_tokens(tokens: TokenSequence) -> TokenIterator:
    """Yield direct tokens after validating their structural nesting."""

    open_tags: list[tuple[str, int]] = []
    for position, token in enumerate(tokens, start=1):
        if isinstance(token, str):
            raise TypeError("template tokens must be non-string sequences")
        match len(token):
            case 2 | 3:
                tag, key = token[:2]
                if tag in _BODY_OPENERS:
                    open_tags.append((key, position))
                elif tag == "end":
                    if not open_tags:
                        raise ChevronError(
                            f'Token {position}: trying to close tag "{key}", '
                            "but it was not opened"
                        )
                    open_tag, open_position = open_tags.pop()
                    if key != open_tag:
                        raise ChevronError(
                            f'Token {position}: trying to close tag "{key}"; '
                            f'last open tag is "{open_tag}" at token {open_position}'
                        )
                yield token
            case _:
                raise TypeError("template tokens must contain two or three values")

    if open_tags:
        tag, position = open_tags[-1]
        raise ChevronError(
            "Unexpected EOF in template tokens: "
            f'tag "{tag}" opened at token {position} was never closed'
        )


class _SourcePolicy(Protocol):
    def resolve(
        self,
        key: str,
        frame: _RenderFrame,
        value_handler: Callable[[TemplateData], TemplateData],
        log_resolution: bool = True,
    ) -> tuple[TemplateData, bool, _RenderFrame | None]:
        """Return the value, its explicit status, and supplying frame."""
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
    ) -> tuple[TemplateData, bool, _RenderFrame | None]:
        value, binding = _get_key(
            key,
            frame,
            logger=self.logger,
            value_handler=value_handler,
            log_resolution=log_resolution,
        )
        return value, False, binding


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
    ) -> tuple[TemplateData, bool, _RenderFrame | None]:
        if key in self.lambdas:
            if log_resolution:
                self.logger.debug(
                    "Resolved template name '%s' from the lambda mapping", key
                )
            return self.lambdas[key], True, None

        def handle_value(value: TemplateData) -> TemplateData:
            if isinstance(value, Callable):
                if log_resolution:
                    self.logger.warning(
                        "Callable template data '%s' is rejected when lambdas= is supplied",
                        key,
                    )
                return ""
            return value_handler(value)

        value, binding = _get_key(
            key,
            frame,
            logger=self.logger,
            allow_callable_traversal=False,
            value_handler=handle_value,
            log_resolution=log_resolution,
        )
        return value, False, binding


def _partial_name(
    key: str,
    frame: _RenderFrame,
    policy: _SourcePolicy,
    logger: _RenderLogger,
    *,
    kind: str = "partial",
) -> str | None:
    """Resolve one dynamic template name without changing the active frame."""
    if not key.startswith("*"):
        return key
    if key.startswith("**"):
        logger.debug("Dynamic %s selector requested nested dereferencing", kind)
        return None

    dynamic_key = key[1:].strip()
    if not dynamic_key:
        logger.debug("Dynamic %s selector was empty", kind)
        return None
    value, _, _ = policy.resolve(
        dynamic_key,
        frame,
        lambda resolved: _normalise_value(dynamic_key, resolved),
        log_resolution=False,
    )
    if isinstance(value, str) and value:
        return value
    logger.debug("Dynamic %s selector did not resolve to a non-empty string", kind)
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
    "parent": "<",
    "block": "$",
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


def _collect_body(
    tokens: TokenIterator, key: str, delimiters: tuple[str, str]
) -> _SectionBody:
    body: list[Token] = []
    nested: list[str] = []
    ending = delimiters
    for token in tokens:
        tag, name = token[:2]
        if tag == "end":
            if not nested and name == key:
                break
            if nested:
                nested.pop()
        elif tag in _BODY_OPENERS:
            nested.append(name)
        body.append(token)
        if tag == "set delimiter":
            ending = _changed_delimiters(name)
    return _SectionBody(body, delimiters, ending)


def _parent_overrides(body: _SectionBody) -> Mapping[str, _SectionBody]:
    """Collect first direct block arguments from one parent invocation."""
    overrides: dict[str, _SectionBody] = {}
    tokens = iter(body.tokens)
    delimiters = body.opening
    nested = 0
    for token in tokens:
        tag, key = token[:2]
        if tag == "block" and nested == 0:
            block = _collect_body(tokens, key, delimiters)
            overrides.setdefault(key, block)
            delimiters = block.ending
            continue
        if tag in _BODY_OPENERS:
            nested += 1
        elif tag == "end" and nested:
            nested -= 1
        if tag == "set delimiter":
            delimiters = _changed_delimiters(key)
    return MappingProxyType(overrides)


def _parent_is_standalone(
    work: _RenderWork[ContinuationResult], body: _SectionBody
) -> bool:
    """Return whether a parent invocation occupies its whole logical line."""
    if work.source_line_has_content:
        return False
    source = body.source()
    if source.lstrip(" \t").startswith(("\n", "\r")):
        return True
    nested = 0
    for token in body.tokens:
        tag, key = token[:2]
        if nested == 0:
            if tag == "literal" and key.strip():
                return False
            if tag not in ("literal", "block", "comment", "set delimiter", "end"):
                return False
        if tag in _BODY_OPENERS:
            nested += 1
        elif tag == "end" and nested:
            nested -= 1
    return True


def _common_indentation(source: str) -> str:
    """Return the leading whitespace shared by non-blank source lines."""
    common: str | None = None
    for line in source.splitlines():
        content = line.lstrip(" \t")
        if not content:
            continue
        indentation = line[: len(line) - len(content)]
        if common is None:
            common = indentation
            continue
        while common and not indentation.startswith(common):
            common = common[:-1]
    return common or ""


def _dedent_literal(
    text: str, indentation: str, at_line_start: bool
) -> tuple[str, bool]:
    """Remove shared definition indentation from one literal token."""
    parts: list[str] = []
    for line in text.splitlines(keepends=True):
        if at_line_start and line.startswith(indentation):
            line = line[len(indentation) :]
        parts.append(line)
        at_line_start = line.endswith(("\n", "\r"))
    return "".join(parts), at_line_start


def _standalone_opening_source(source: str) -> str:
    """Remove horizontal whitespace preceding a standalone opening newline."""
    suffix = source.lstrip(" \t")
    return suffix if suffix.startswith(("\n", "\r")) else source


def _block_tokens(body: _SectionBody) -> TokenSequence:
    """Prepare override tokens without turning literal data back into syntax."""
    source = _standalone_opening_source(body.source())
    if not source.startswith(("\n", "\r")):
        return body.tokens

    indentation = _common_indentation(source)
    drop_newline = True
    at_line_start = True
    raw_at_line_start = True
    tokens: list[Token] = []
    for token in body.tokens:
        tag, text = token[:2]
        if tag != "literal":
            raw = token[2] if len(token) == 3 else text
            _, at_line_start = _dedent_literal(raw, "", at_line_start)
            _, raw_at_line_start = _dedent_literal(raw, "", raw_at_line_start)
            tokens.append(token)
            continue

        raw = token[2] if len(token) == 3 else text
        if drop_newline:
            raw = _standalone_opening_source(raw)
            if text.startswith("\r\n"):
                text = text[2:]
            elif text.startswith(("\n", "\r")):
                text = text[1:]
            elif not text and raw.startswith(("\r\n", "\n", "\r")):
                pass
            else:
                tokens.append(token)
                continue
            if raw.startswith("\r\n"):
                raw = raw[2:]
            elif raw.startswith(("\n", "\r")):
                raw = raw[1:]
            drop_newline = False
        text, at_line_start = _dedent_literal(text, indentation, at_line_start)
        raw, raw_at_line_start = _dedent_literal(raw, indentation, raw_at_line_start)
        tokens.append((tag, text, raw) if len(token) == 3 else (tag, text))
    return tokens


def _block_indentation(body: _SectionBody) -> str:
    """Return the default block body's intrinsic indentation, if any."""
    source = _standalone_opening_source(body.source())
    if not source.startswith(("\n", "\r")):
        return ""
    lines = source.splitlines()
    for line in lines:
        if line.strip():
            return line[: len(line) - len(line.lstrip(" \t"))]
    return lines[-1] if lines else ""


def _prepare_block(
    key: str,
    body: _SectionBody,
    frame: _RenderFrame,
    site_padding: str,
    opening_is_standalone: bool,
) -> tuple[TokenSequence, _RenderFrame, str]:
    """Choose block content and its inherited render context."""
    override = frame.overrides.get(key)
    if override is None:
        return body.tokens, frame.with_context(body.opening, frame.padding), ""

    local_padding = (
        site_padding.removeprefix(frame.padding)
        if site_padding.startswith(frame.padding)
        else site_padding
    )
    indentation = local_padding or (
        _block_indentation(body) if opening_is_standalone else ""
    )
    prefix = indentation if not local_padding else ""
    child = frame.without_override(key).with_context(
        override.opening, frame.padding + indentation
    )
    return _block_tokens(override), child, prefix


def _consume_parent_suffix(text: str, pending: bool) -> tuple[str, bool]:
    """Remove exactly the standalone parent closing-line suffix."""
    if not pending:
        return text, False
    suffix = text.lstrip(" \t")
    if suffix.startswith("\r\n"):
        return suffix[2:], False
    if suffix.startswith(("\n", "\r")):
        return suffix[1:], False
    return text, False


def _restore_parent_suffix(text: str, raw: str, pending: bool) -> tuple[str, bool]:
    """Restore a tokenizer-removed suffix for a non-standalone parent."""
    if not pending or text:
        return text, False
    suffix = raw.lstrip(" \t")
    if suffix.startswith("\r\n"):
        return "\r\n", False
    if suffix.startswith(("\n", "\r")):
        return suffix[0], False
    return text, False


def _restore_enclosing_padding(
    result: str, terminal_padding: str, enclosing_padding: str
) -> tuple[str, str]:
    """Replace known engine-added terminal padding with enclosing padding."""
    if not terminal_padding:
        return result, ""
    return result[: -len(terminal_padding)] + enclosing_padding, enclosing_padding


def _apply_line_padding(text: str, padding: str) -> str:
    """Prefix each line following a supported line ending with padding."""
    if not padding:
        return text
    return "".join(
        line + padding if line.endswith(("\n", "\r")) else line
        for line in text.splitlines(keepends=True)
    )


class ChevronRender:
    """Composed rendering engine; chevron.render remains the primary entry point."""

    def __init__(self, config: _RenderConfig, policy: _SourcePolicy) -> None:
        self.config = config
        self.policy = policy
        self.state = _RenderState()

    def render(self, template: TemplateInput, frame: _RenderFrame) -> str:
        """Render source or tokens using the supplied immutable frame chain."""
        return self._drive(self._template_work(template, frame))

    def _template_work(
        self,
        template: TemplateInput,
        frame: _RenderFrame,
        continuation: Callable[[str, str], None] | None = None,
        *,
        source_line_has_content: bool = False,
    ) -> _RenderWork[None]:
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
            tokens = _tokenize(template, *frame.delimiters, include_raw=True)
        return _RenderWork[None](
            tokens,
            frame,
            frame.delimiters,
            continuation,
            source_line_has_content=source_line_has_content,
        )

    def _drive(self, root: _RenderWork[None]) -> str:
        """Run active work without placing nested template expansion on the stack."""
        active = [root]
        try:
            while active:
                work = active[-1]
                token = next(work.tokens, _END_OF_TOKENS)
                if token is _END_OF_TOKENS:
                    active.pop()
                    work.close_tokens()
                    result = "".join(work.output)
                    if not active:
                        return (
                            result[: -len(work.terminal_padding)]
                            if work.terminal_padding
                            else result
                        )
                    assert work.continuation is not None
                    work.continuation(result, work.terminal_padding)
                    continue
                self._render_token(work, cast(Token, token), active)
        finally:
            for work in reversed(active):
                work.close_tokens()
        raise RuntimeError("render work completed without a root result")

    def resolve(
        self, key: str, frame: _RenderFrame
    ) -> tuple[TemplateData, bool, _RenderFrame | None]:
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

    def _schedule_result(
        self,
        result: TemplateData,
        key: str,
        frame: _RenderFrame,
        active: list[_RenderWork[None]],
        continuation: Callable[[str, str], None],
    ) -> None:
        result = _reject_awaitable_lambda_result(result, key)
        if result is None:
            continuation(self.empty_result(key), "")
            return
        _push_work(
            active,
            self._template_work(
                result if isinstance(result, str) else str(result), frame, continuation
            ),
        )

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
        if result is None:
            return self.empty_result(key)
        if not isinstance(result, str):
            raise TypeError(f"Compatibility lambda '{key}' must return text")
        return result

    def compatibility_render(self, template: TemplateInput, frame: _RenderFrame) -> str:
        """Only legacy callbacks replay the invocation's reconstructed tokens."""
        if not template and not isinstance(template, (str, Sequence)):
            template = ""
        if isinstance(template, str) and template in self.state.token_cache:
            template = self.state.token_cache[template]
        return self.render(template, frame)

    def _render_section(
        self,
        key: str,
        work: _RenderWork[None],
        active: list[_RenderWork[None]],
    ) -> None:
        use_enhanced_iterators = Extension.is_enabled(Extension.ENHANCED_ITERATORS)
        value, _, binding_frame = self.resolve(key, work.frame)
        if isinstance(value, AsyncIterable):
            raise TypeError(
                f"Section '{key}' resolved to an async iterable; "
                "use chevron.async_render instead"
            )
        if isinstance(value, Callable):
            body = _collect_body(work.tokens, key, work.delimiters)
            work.delimiters = body.ending
            protocol = _lambda_protocol(value, "section")
            self.config.logger.debug(
                "Selected %s lambda protocol for '%s'", protocol or "unsupported", key
            )
            if protocol == _SECTION_PROTOCOL:
                result_frame = work.frame.with_context(body.opening, work.frame.padding)
                self._schedule_result(
                    value(body.source()),
                    key,
                    result_frame,
                    active,
                    work.append,
                )
            elif protocol == _COMPAT_PROTOCOL:
                work.append(self.compatibility_section(value, key, body, work.frame))
            return
        if not value:
            work.frame = work.frame.child(_SKIPPED_SECTION_MARKER)
            return
        if isinstance(value, (Sequence, Iterator)) and not isinstance(value, str):
            assert binding_frame is not None
            values = (
                (
                    _iterator_state(
                        binding_frame,
                        key,
                        value,
                    )
                    if use_enhanced_iterators
                    else iter(value)
                )
                if isinstance(value, Iterator)
                else iter(value)
            )
        else:
            work.frame = work.frame.child(value if value else _SKIPPED_SECTION_MARKER)
            return

        body = _collect_body(work.tokens, key, work.delimiters)
        work.delimiters = body.ending

        index = 0

        def render_next(result: str | None = None, terminal_padding: str = "") -> None:
            nonlocal index
            if result is not None:
                work.append(result, terminal_padding=terminal_padding)
            try:
                if not use_enhanced_iterators:
                    item = next(values)
                    last = None
                elif isinstance(values, _IteratorState):
                    item, last = values.next_with_last()
                else:
                    item = next(values)
                    last = None
            except StopIteration:
                return
            index += 1
            child = work.frame.child(
                item,
                body.opening,
                work.frame.padding,
                value if use_enhanced_iterators else _MISSING,
                index - 1,
                last,
            )
            _push_work(
                active,
                _RenderWork.from_tokens(
                    iter(body.tokens),
                    child,
                    render_next,
                    source_line_has_content=work.source_line_has_content,
                ),
            )

        render_next()
        return

    def _render_partial(
        self, key: str, work: _RenderWork[None], active: list[_RenderWork[None]]
    ) -> None:
        config = self.config
        dynamic = key.startswith("*")
        name = _partial_name(key, work.frame, self.policy, config.logger)
        if name is None:
            return
        partial = _get_partial(
            name,
            config.partials_dict,
            config.partials_path,
            config.partials_ext,
            config.logger,
            dynamic=dynamic,
        )
        site_padding = work.partial_padding()
        left = (
            site_padding.removeprefix(work.frame.padding)
            if site_padding.startswith(work.frame.padding)
            else site_padding
        )
        padding = work.frame.padding + left if left.isspace() else work.frame.padding
        child = work.frame.with_context(config.default_delimiters, padding)

        def append_partial(result: str, terminal_padding: str) -> None:
            result, terminal_padding = _restore_enclosing_padding(
                result, terminal_padding, work.frame.padding
            )
            work.append(result, terminal_padding=terminal_padding)

        _push_work(active, self._template_work(partial, child, append_partial))

    def _render_block(
        self,
        key: str,
        work: _RenderWork[None],
        active: list[_RenderWork[None]],
        opening_is_standalone: bool,
        source_line_has_content: bool,
    ) -> None:
        body = _collect_body(work.tokens, key, work.delimiters)
        work.delimiters = body.ending
        is_override = key in work.frame.overrides
        template, frame, prefix = _prepare_block(
            key, body, work.frame, work.partial_padding(), opening_is_standalone
        )

        def append_block(result: str, terminal_padding: str) -> None:
            if prefix and result.strip():
                result = prefix + result
            result, terminal_padding = _restore_enclosing_padding(
                result, terminal_padding, work.frame.padding
            )
            work.append(result, terminal_padding=terminal_padding)

        _push_work(
            active,
            self._template_work(
                template,
                frame,
                append_block,
                source_line_has_content=(
                    source_line_has_content if not is_override else False
                ),
            ),
        )

    def _render_parent(
        self, key: str, work: _RenderWork[None], active: list[_RenderWork[None]]
    ) -> None:
        body = _collect_body(work.tokens, key, work.delimiters)
        work.delimiters = body.ending
        is_standalone = _parent_is_standalone(work, body)
        work.strip_parent_suffix = is_standalone
        work.restore_parent_suffix = not is_standalone
        dynamic = key.startswith("*")
        name = _partial_name(
            key, work.frame, self.policy, self.config.logger, kind="parent"
        )
        if name is None:
            return
        parent = _get_partial(
            name,
            self.config.partials_dict,
            self.config.partials_path,
            self.config.partials_ext,
            self.config.logger,
            dynamic=dynamic,
            kind="parent",
        )
        site_padding = work.partial_padding() if is_standalone else ""
        left = (
            site_padding.removeprefix(work.frame.padding)
            if site_padding.startswith(work.frame.padding)
            else site_padding
        )
        padding = work.frame.padding + left if left.isspace() else work.frame.padding
        frame = work.frame.with_context(self.config.default_delimiters, padding)
        frame = frame.with_overrides(_parent_overrides(body))

        def append_parent(result: str, terminal_padding: str) -> None:
            result, terminal_padding = _restore_enclosing_padding(
                result, terminal_padding, work.frame.padding
            )
            work.append(result, terminal_padding=terminal_padding)

        _push_work(active, self._template_work(parent, frame, append_parent))

    def _render_token(
        self,
        work: _RenderWork[None],
        token: Token,
        active: list[_RenderWork[None]],
    ) -> None:
        tag, key = token[:2]
        source_line_has_content = work.source_line_has_content
        if tag == "literal":
            work.observe_source_literal(token)
        elif tag != "parent":
            work.source_line_has_content = True
        if work.strip_parent_suffix and tag != "literal":
            work.strip_parent_suffix = False
        if work.restore_parent_suffix and tag != "literal":
            work.restore_parent_suffix = False
        if _apply_control_token(work, tag, key):
            if tag == "parent":
                work.source_line_has_content = True
            return

        match tag:
            case "literal":
                raw = token[2] if len(token) == 3 else key
                key, work.restore_parent_suffix = _restore_parent_suffix(
                    key, raw, work.restore_parent_suffix
                )
                key, work.strip_parent_suffix = _consume_parent_suffix(
                    key, work.strip_parent_suffix
                )
                rendered = _apply_line_padding(key, work.frame.padding)
                terminal_padding = (
                    work.frame.padding
                    if key.endswith(("\n", "\r")) and work.frame.padding
                    else ""
                )
                work.append(rendered, terminal_padding=terminal_padding)
            case "variable" | "no escape":
                self._render_interpolation(key, tag, work, active)
            case "section":
                self._render_section(key, work, active)
            case "inverted section":
                use_enhanced_iterators = Extension.is_enabled(
                    Extension.ENHANCED_ITERATORS
                )
                value, _, binding_frame = self.policy.resolve(
                    key, work.frame, lambda value: _normalise_value(key, value)
                )
                if isinstance(value, AsyncIterable):
                    raise TypeError(
                        f"Section '{key}' resolved to an async iterable; "
                        "use chevron.async_render instead"
                    )
                if not value:
                    is_empty = True
                elif isinstance(value, Callable):
                    is_empty = False
                elif isinstance(value, Sized):
                    is_empty = False
                elif use_enhanced_iterators and isinstance(value, Iterator):
                    assert binding_frame is not None
                    is_empty = _iterator_state(
                        binding_frame,
                        key,
                        value,
                    ).probe()
                else:
                    is_empty = False
                work.frame = work.frame.child(
                    _INVERTED_SECTION_MARKER if is_empty else _SKIPPED_SECTION_MARKER
                )
            case "partial":
                self._render_partial(key, work, active)
            case "parent":
                self._render_parent(key, work, active)
                work.source_line_has_content = True
            case "block":
                self._render_block(
                    key,
                    work,
                    active,
                    opening_is_standalone=not source_line_has_content,
                    source_line_has_content=source_line_has_content,
                )

    def _render_interpolation(
        self,
        key: str,
        tag: str,
        work: _RenderWork[None],
        active: list[_RenderWork[None]],
    ) -> None:
        value, explicit, _ = self.resolve(key, work.frame)

        def append_value(result: TemplateData, _terminal_padding: str = "") -> None:
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
            self._schedule_result(value(), key, result_frame, active, append_value)
        elif explicit or isinstance(value, _LambdaDefinition):
            append_value("")
        else:
            append_value(value)


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
