from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import update_wrapper
import logging
from pathlib import Path
from typing import Any, Protocol

from .tokenizer import ChevronError, tokenize as _tokenize

_MISSING = object()
_FUNCTION_PROTOCOL = "function"
_SECTION_PROTOCOL = "section"
_COMPAT_PROTOCOL = "compat"
_LOGGER_NAME = "chevron"
_DEFAULT_LOGGER = logging.getLogger(_LOGGER_NAME)


class _RenderLogger(logging.LoggerAdapter):
    """Apply one render's diagnostic threshold to its selected logger."""

    def __init__(
        self, logger: logging.Logger | logging.LoggerAdapter, log_level: int
    ) -> None:
        super().__init__(logger, {})
        self.log_level = log_level

    def log(self, level: int, message: object, *args, **kwargs) -> None:
        if level >= self.log_level:
            super().log(level, message, *args, **kwargs)


@dataclass
class _LambdaDefinition:
    """A callable together with its declared template protocol."""

    callback: Callable
    protocol: str

    def __post_init__(self):
        update_wrapper(self, self.callback)
        callback_type = type(self.callback)
        self.__module__ = getattr(self.callback, "__module__", callback_type.__module__)
        self.__name__ = getattr(self.callback, "__name__", callback_type.__name__)
        self.__qualname__ = getattr(
            self.callback, "__qualname__", callback_type.__qualname__
        )
        self.__doc__ = getattr(self.callback, "__doc__", callback_type.__doc__)
        self.__annotations__ = getattr(self.callback, "__annotations__", {})

    def __call__(self, *args, **kwargs):
        return self.callback(*args, **kwargs)

    def __get__(self, instance, owner):
        descriptor = getattr(self.callback, "__get__", None)
        if descriptor is None:
            return self
        return _LambdaDefinition(descriptor(instance, owner), self.protocol)


def _declare_lambda(callback, protocol):
    if not isinstance(callback, Callable):
        raise TypeError("lambda decorators require a callable")
    return _LambdaDefinition(callback, protocol)


def func(callback):
    """Declare a zero-argument Mustache interpolation lambda."""

    return _declare_lambda(callback, _FUNCTION_PROTOCOL)


def section(callback):
    """Declare a one-argument Mustache section lambda."""

    return _declare_lambda(callback, _SECTION_PROTOCOL)


def compat(callback):
    """Declare Chevron's legacy two-argument section-lambda protocol."""

    return _declare_lambda(callback, _COMPAT_PROTOCOL)


def _lambda_protocol(value, tag):
    """Resolve a callable's protocol without invoking it."""

    if isinstance(value, _LambdaDefinition):
        return value.protocol

    if tag == "section":
        return _COMPAT_PROTOCOL
    return None


def _normalise_value(key, value):
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


def _html_escape(string):
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


def _get_key(
    key,
    scopes,
    logger: _RenderLogger,
    allow_callable_traversal=True,
    value_handler=None,
):
    """Get a key from the current scope."""

    blocked_callable_traversal = False

    # If the key is a dot
    if key == ".":
        # Then just return the current scope
        scope = scopes[0]
        logger.debug("Resolved current template scope")
        return value_handler(scope) if value_handler is not None else scope

    # Loop through the scopes
    for scope in scopes:
        try:
            # For every dot-separated key
            for child in key.split("."):
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
                        scope = scope[int(child)]

            value = value_handler(scope) if value_handler is not None else scope
        except (AttributeError, KeyError, IndexError, ValueError):
            # Lookup and value normalisation both preserve fallback behaviour.
            continue

        logger.debug("Resolved template name '%s' from template data", key)
        return value

    # We couldn't find the key in any of the scopes

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
    name, partials_dict, partials_path, partials_ext, logger: _RenderLogger
):
    """Load a partial"""
    try:
        # Maybe the partial is in the dictionary
        partial = partials_dict[name]
        logger.debug("Resolved partial '%s' from configured partials", name)
        return partial
    except KeyError:
        # Don't try loading from the file system if the partials_path is None or empty
        if partials_path is None or partials_path == "":
            logger.debug("Partial '%s' was not configured", name)
            return ""

        try:
            path_ext = "." + partials_ext if partials_ext else ""
            base_path = Path(partials_path).resolve(strict=True)
            partial_name = Path(name + path_ext)
            if partial_name.is_absolute() or ".." in partial_name.parts:
                logger.debug(
                    "Rejected partial '%s' outside the configured path",
                    partial_name.name,
                )
                return ""

            partial_path = (base_path / partial_name).resolve(strict=True)
            partial_path.relative_to(base_path)
            with partial_path.open("r", encoding="utf-8") as partial:
                content = partial.read()
            logger.debug("Resolved partial '%s' from the configured path", name)
            return content

        except (OSError, RuntimeError, ValueError):
            logger.debug("Partial '%s' was unavailable", name)
            return ""


@dataclass(frozen=True)
class _RenderConfig:
    """Settings shared by all recursive operations in one public render."""

    partials_path: str | Path | None
    partials_ext: str
    partials_dict: Mapping
    logger: _RenderLogger
    default_delimiters: tuple[str, str]


@dataclass
class _RenderFrame:
    """Scopes, input delimiters and indentation local to a recursive operation."""

    scopes: list[Any]
    delimiters: tuple[str, str]
    padding: str = ""


@dataclass
class _RenderState:
    """Compatibility token reuse shared by recursive render frames."""

    token_cache: dict[str, list[tuple]] = field(default_factory=dict)


def _validated_tokens(tokens: Sequence[tuple]) -> Iterator[tuple]:
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
        value_handler: Callable[[Any], Any],
    ) -> tuple[Any, bool]:
        """Return the value and whether it came from the explicit mapping."""
        ...


@dataclass
class _PermissiveSource:
    logger: _RenderLogger

    def resolve(
        self, key: str, frame: _RenderFrame, value_handler: Callable[[Any], Any]
    ) -> tuple[Any, bool]:
        return _get_key(
            key, frame.scopes, logger=self.logger, value_handler=value_handler
        ), False


class _ExplicitSource:
    def __init__(self, lambdas: Mapping, logger: _RenderLogger) -> None:
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
        self, key: str, frame: _RenderFrame, value_handler: Callable[[Any], Any]
    ) -> tuple[Any, bool]:
        if key in self.lambdas:
            self.logger.debug(
                "Resolved template name '%s' from the lambda mapping", key
            )
            return self.lambdas[key], True

        def handle_value(value: Any) -> Any:
            if isinstance(value, Callable):
                self.logger.warning(
                    "Callable template data '%s' is rejected when lambdas= is supplied",
                    key,
                )
                return ""
            return value_handler(value)

        return _get_key(
            key,
            frame.scopes,
            logger=self.logger,
            allow_callable_traversal=False,
            value_handler=handle_value,
        ), False


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

    tokens: list[tuple]
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

    def compatibility(self, delimiters: tuple[str, str]) -> tuple[str, list[tuple]]:
        left, right = delimiters
        parts = []
        tokens = []
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
    tokens: Iterator, key: str, delimiters: tuple[str, str]
) -> _SectionBody:
    body = []
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

    def render(self, template: Any, frame: _RenderFrame) -> str:
        """Render source or tokens, restoring frame-local scopes after recursion."""
        original_scopes = list(frame.scopes)
        token_stream = None
        try:
            if isinstance(template, Sequence) and not isinstance(template, str):
                tokens = _validated_tokens(template)
            else:
                reader = getattr(template, "read", None)
                if reader is not None:
                    template = reader()
                if not template and not isinstance(template, str):
                    template = ""
                token_stream = _tokenize(template, *frame.delimiters, include_raw=True)
                tokens = token_stream
            return self.render_tokens(tokens, frame)
        finally:
            frame.scopes[:] = original_scopes
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

    def render_result(self, result: Any, key: str, frame: _RenderFrame) -> str:
        if result is None:
            return self.empty_result(key)
        return self.render(result if isinstance(result, str) else str(result), frame)

    def interpolation(self, key: str, frame: _RenderFrame) -> Any:
        value, explicit = self.resolve(key, frame)
        if not isinstance(value, Callable):
            return value
        protocol = _lambda_protocol(value, "interpolation")
        self.config.logger.debug(
            "Selected %s lambda protocol for '%s'", protocol or "unsupported", key
        )
        if protocol == _FUNCTION_PROTOCOL:
            result_frame = _RenderFrame(frame.scopes, self.config.default_delimiters)
            return self.render_result(value(), key, result_frame)
        if explicit or isinstance(value, _LambdaDefinition):
            return ""
        return value

    def standard_section(
        self, callback: Callable, key: str, body: _SectionBody, frame: _RenderFrame
    ) -> str:
        result_frame = _RenderFrame(frame.scopes, body.opening, frame.padding)
        return self.render_result(callback(body.source()), key, result_frame)

    def compatibility_section(
        self, callback: Callable, key: str, body: _SectionBody, frame: _RenderFrame
    ) -> str:
        text, tokens = body.compatibility(frame.delimiters)
        self.state.token_cache[text] = tokens

        def render_callback(template: Any, data: Any = None) -> str:
            child = _RenderFrame(
                [data] + frame.scopes if data else frame.scopes,
                self.config.default_delimiters,
                frame.padding,
            )
            return self.compatibility_render(template, child)

        result = callback(text, render_callback)
        return self.empty_result(key) if result is None else result

    def compatibility_render(self, template: Any, frame: _RenderFrame) -> str:
        """Only legacy callbacks replay the invocation's reconstructed tokens."""
        if not template and not isinstance(template, (str, Sequence)):
            template = ""
        if not (isinstance(template, Sequence) and not isinstance(template, str)):
            if template in self.state.token_cache:
                template = self.state.token_cache[template]
        return self.render(template, frame)

    _section_handlers = {
        _SECTION_PROTOCOL: standard_section,
        _COMPAT_PROTOCOL: compatibility_section,
    }

    def render_section(
        self,
        key: str,
        tokens: Iterator,
        frame: _RenderFrame,
        delimiters: tuple[str, str],
    ) -> tuple[str, tuple[str, str]]:
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
            return result, body.ending
        if isinstance(value, (Sequence, Iterator)) and not isinstance(value, str):
            body = _collect_section(tokens, key, delimiters)
            output = ""
            for item in value:
                child = _RenderFrame([item] + frame.scopes, body.opening, frame.padding)
                output += self.render(body.tokens, child)
            return output, body.ending
        frame.scopes.insert(0, value)
        return "", delimiters

    def render_partial(self, key: str, frame: _RenderFrame, output: str) -> str:
        config = self.config
        partial = _get_partial(
            key,
            config.partials_dict,
            config.partials_path,
            config.partials_ext,
            config.logger,
        )
        left = output.rpartition("\n")[2]
        padding = frame.padding + left if left.isspace() else frame.padding
        child = _RenderFrame(frame.scopes, config.default_delimiters, padding)
        result = self.render(partial, child)
        return result.rstrip(" \t") if left.isspace() else result

    def render_tokens(self, tokens: Iterator, frame: _RenderFrame) -> str:
        output = ""
        scopes = frame.scopes
        delimiters = frame.delimiters
        for token in tokens:
            tag, key = token[:2]
            current_scope = scopes[0]
            if tag == "end":
                del scopes[0]
                continue
            if tag == "set delimiter":
                delimiters = _changed_delimiters(key)
                continue
            if (
                not current_scope
                and not isinstance(current_scope, Callable)
                and len(scopes) != 1
            ):
                if tag in ("section", "inverted section"):
                    scopes.insert(0, False)
                continue

            match tag:
                case "literal":
                    output += key.replace("\n", "\n" + frame.padding)
                case "variable" | "no escape":
                    value = self.interpolation(key, frame)
                    if tag == "variable" and value is True and key == ".":
                        value = scopes[1]
                    text = value if isinstance(value, str) else str(value)
                    output += _html_escape(text) if tag == "variable" else text
                case "section":
                    result, delimiters = self.render_section(
                        key, tokens, frame, delimiters
                    )
                    output += result
                case "inverted section":
                    value, _ = self.policy.resolve(
                        key, frame, lambda value: _normalise_value(key, value)
                    )
                    scopes.insert(0, not value)
                case "partial":
                    output += self.render_partial(key, frame, output)
        return output


def render(
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
):
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
    frame = _RenderFrame(
        scopes if scopes is not None else [data], config.default_delimiters, padding
    )
    engine = ChevronRender(config, policy)
    diagnostics.info("Render started")
    try:
        result = engine.render(template, frame)
    except ChevronError as error:
        diagnostics.error("Template rendering failed: %s", error)
        raise
    diagnostics.info("Render completed successfully")
    return result
