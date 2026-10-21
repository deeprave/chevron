"""Behavioural coverage for per-render Python logging diagnostics."""

from concurrent.futures import ThreadPoolExecutor
import inspect
import logging

import chevron
import pytest
from chevron.tokenizer import tokenize


class _CapturingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _logger(
    name: str, level: int = logging.DEBUG
) -> tuple[logging.Logger, _CapturingHandler]:
    logger = logging.Logger(name, level)
    logger.propagate = False
    handler = _CapturingHandler()
    logger.addHandler(handler)
    return logger, handler


def _events(handler: _CapturingHandler) -> list[tuple[int, str]]:
    return [(record.levelno, record.getMessage()) for record in handler.records]


def test_diagnostic_options_are_keyword_only_without_moving_existing_positions() -> (
    None
):
    assert (
        chevron.render(
            "{{name}}",
            {"name": "Ada"},
            None,
            "mustache",
            {},
            "",
            "{{",
            "}}",
            None,
            False,
            None,
        )
        == "Ada"
    )
    signature = inspect.signature(chevron.render)
    assert signature.parameters["logger"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["log_level"].kind is inspect.Parameter.KEYWORD_ONLY


def test_application_logger_receives_warning_without_default_stderr(capsys) -> None:
    logger, handler = _logger("test.application", logging.WARNING)

    assert chevron.render("{{missing}}", {}, logger=logger) == ""

    assert _events(handler) == [(logging.WARNING, "Could not find key 'missing'")]
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("warn", [False, True, logging.DEBUG])
def test_application_logger_replaces_default_stderr(warn: bool | int, capsys) -> None:
    logger, handler = _logger("test.replacement", logging.WARNING)

    assert chevron.render("{{missing}}", {}, warn=warn, logger=logger) == ""

    assert _events(handler) == [(logging.WARNING, "Could not find key 'missing'")]
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize(
    ("warn", "expected"),
    [
        (False, ""),
        (True, "Could not find key 'missing'\n"),
        (logging.ERROR, "Could not find key 'missing'\n"),
    ],
)
def test_default_stderr_logger_respects_warn(
    warn: bool | int, expected: str, caplog
) -> None:
    chevron.render("{{missing}}", {}, warn=warn)

    assert [record.getMessage() for record in caplog.records] == (
        [expected.rstrip("\n")] if expected else []
    )


def test_default_stderr_logger_preserves_warning_text(caplog) -> None:
    assert chevron.render("{{missing}}", {}, warn=True) == ""

    assert [record.getMessage() for record in caplog.records] == [
        "Could not find key 'missing'"
    ]


def test_log_level_enables_lifecycle_and_debug_events() -> None:
    logger, handler = _logger("test.log-level")

    assert (
        chevron.render("{{missing}}", {}, logger=logger, log_level=logging.DEBUG) == ""
    )

    assert _events(handler) == [
        (logging.INFO, "Render started"),
        (logging.DEBUG, "Template name 'missing' was not found"),
        (logging.WARNING, "Could not find key 'missing'"),
        (logging.INFO, "Render completed successfully"),
    ]


@pytest.mark.parametrize("logger", [object(), logging.getLogger("test").log])
def test_invalid_logger_fails_before_rendering(logger: object) -> None:
    with pytest.raises(TypeError, match="logger must be a logging.Logger"):
        chevron.render("{{#unclosed}}", logger=logger)


def test_invalid_log_level_fails_before_rendering() -> None:
    with pytest.raises(TypeError, match="log_level must be an integer"):
        chevron.render("{{#unclosed}}", log_level="DEBUG")


def test_logger_adapter_is_supported() -> None:
    logger, handler = _logger("test.adapter", logging.WARNING)
    adapter = logging.LoggerAdapter(logger, {})

    assert chevron.render("{{missing}}", {}, logger=adapter) == ""

    assert _events(handler) == [(logging.WARNING, "Could not find key 'missing'")]


def test_log_level_filters_application_logger_events() -> None:
    logger, handler = _logger("test.level")

    assert (
        chevron.render("{{missing}}", {}, logger=logger, log_level=logging.ERROR) == ""
    )

    assert _events(handler) == []


def test_all_existing_warning_conditions_use_the_selected_logger() -> None:
    logger, handler = _logger("test.warnings", logging.WARNING)

    @chevron.func
    def none_result() -> None:
        return None

    class Build:
        version = "0.15.0"

    def rejected_callback(text: str, render) -> str:
        return render(text)

    cases = [
        ("{{missing}}", {}, None, "Could not find key 'missing'"),
        (
            "{{rejected}}",
            {"rejected": rejected_callback},
            {},
            "Callable template data 'rejected' is rejected when lambdas= is supplied",
        ),
        (
            "{{build.version}}",
            {"build": Build},
            {},
            "Could not resolve 'build.version': callable values cannot be traversed when lambdas= is supplied",
        ),
        (
            "{{none_result}}",
            {},
            {"none_result": none_result},
            "Lambda 'none_result' returned None; rendering an empty value",
        ),
    ]

    for template, data, lambdas, expected in cases:
        assert chevron.render(template, data, lambdas=lambdas, logger=logger) == ""
        assert _events(handler).pop() == (logging.WARNING, expected)


def test_debug_messages_describe_lambda_dispatch_and_partial_resolution() -> None:
    logger, handler = _logger("test.debug")

    @chevron.func
    def value() -> str:
        return "result"

    assert (
        chevron.render(
            "{{value}}{{>part}}",
            lambdas={"value": value},
            partials_dict={"part": "rendered-content"},
            logger=logger,
            log_level=logging.DEBUG,
        )
        == "resultrendered-content"
    )

    debug_messages = [
        message for level, message in _events(handler) if level == logging.DEBUG
    ]
    assert any("lambda mapping" in message for message in debug_messages)
    assert any("function lambda protocol" in message for message in debug_messages)
    assert any("configured partials" in message for message in debug_messages)
    assert all(
        "result" not in message and "rendered-content" not in message
        for message in debug_messages
    )


def test_filesystem_partial_debug_outcomes(tmp_path) -> None:
    logger, handler = _logger("test.partials")
    (tmp_path / "part.mustache").write_text("content", encoding="utf-8")

    assert (
        chevron.render(
            "{{>part}}{{>missing}}",
            partials_path=tmp_path,
            logger=logger,
            log_level=logging.DEBUG,
        )
        == "content"
    )

    messages = [message for _, message in _events(handler)]
    assert "Resolved partial 'part' from the configured path" in messages
    assert "Partial 'missing' was unavailable" in messages


@pytest.mark.parametrize(
    ("partial", "reason"),
    [("/etc/passwd", "absolute path"), ("../secret", "parent traversal")],
)
def test_rejected_filesystem_partial_diagnostics_retain_safe_context(
    tmp_path, partial: str, reason: str
) -> None:
    logger, handler = _logger("test.rejected-partials")

    assert (
        chevron.render(
            "{{> " + partial + "}}",
            partials_path=tmp_path,
            logger=logger,
            log_level=logging.DEBUG,
        )
        == ""
    )

    messages = [message for _, message in _events(handler)]
    assert f"Rejected partial reference '{partial}': {reason}" in messages
    assert str(tmp_path) not in "\n".join(messages)


def test_nested_operations_retain_the_enclosing_logger(capsys) -> None:
    logger, handler = _logger("test.nested", logging.WARNING)

    @chevron.compat
    def callback(text: str, render):
        return render(text)

    assert (
        chevron.render(
            "{{missing_outer}}{{#callback}}{{missing_callback}}{{/callback}}{{>part}}",
            {"callback": callback},
            partials_dict={"part": "{{missing_partial}}"},
            logger=logger,
        )
        == ""
    )

    assert _events(handler) == [
        (logging.WARNING, "Could not find key 'missing_outer'"),
        (logging.WARNING, "Could not find key 'missing_callback'"),
        (logging.WARNING, "Could not find key 'missing_partial'"),
    ]
    assert capsys.readouterr().err == ""


def test_iterable_and_lambda_returned_templates_retain_logger() -> None:
    logger, handler = _logger("test.recursive", logging.WARNING)

    @chevron.func
    def returned_template() -> str:
        return "{{missing_from_lambda}}"

    assert (
        chevron.render(
            "{{#items}}{{missing_from_iterable}}{{/items}}{{returned_template}}",
            {"items": [1, 2]},
            lambdas={"returned_template": returned_template},
            logger=logger,
        )
        == ""
    )

    assert _events(handler) == [
        (logging.WARNING, "Could not find key 'missing_from_iterable'"),
        (logging.WARNING, "Could not find key 'missing_from_iterable'"),
        (logging.WARNING, "Could not find key 'missing_from_lambda'"),
    ]


def test_reentrant_public_render_uses_its_own_logger() -> None:
    outer_logger, outer_handler = _logger("test.outer", logging.WARNING)
    inner_logger, inner_handler = _logger("test.inner", logging.WARNING)

    @chevron.func
    def nested() -> str:
        return chevron.render("{{inner_missing}}", logger=inner_logger)

    assert (
        chevron.render(
            "{{outer_missing}}{{nested}}",
            lambdas={"nested": nested},
            logger=outer_logger,
        )
        == ""
    )

    assert _events(outer_handler) == [
        (logging.WARNING, "Could not find key 'outer_missing'")
    ]
    assert _events(inner_handler) == [
        (logging.WARNING, "Could not find key 'inner_missing'")
    ]


def test_concurrent_public_renders_keep_logger_configuration_isolated() -> None:
    first_logger, first_handler = _logger("test.first", logging.WARNING)
    second_logger, second_handler = _logger("test.second")

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda options: chevron.render("{{missing}}", {}, **options),
                [
                    {"logger": first_logger, "log_level": logging.WARNING},
                    {"logger": second_logger, "log_level": logging.ERROR},
                ],
            )
        )

    assert results == ["", ""]
    assert _events(first_handler) == [(logging.WARNING, "Could not find key 'missing'")]
    assert _events(second_handler) == []


def test_unhandled_template_error_is_reported_once_and_reraised() -> None:
    logger, handler = _logger("test.error", logging.ERROR)

    with pytest.raises(chevron.ChevronError, match='tag "unclosed" was never closed'):
        chevron.render("{{#unclosed}}", logger=logger)

    assert len(handler.records) == 1
    assert handler.records[0].levelno == logging.ERROR
    assert 'tag "unclosed" was never closed' in handler.records[0].getMessage()


@pytest.mark.parametrize(
    ("template", "lambdas", "partials_dict"),
    [
        ("{{>part}}", None, {"part": "{{#unclosed}}"}),
        (
            "{{returned_template}}",
            {"returned_template": chevron.func(lambda: "{{#unclosed}}")},
            {},
        ),
    ],
    ids=["partial", "lambda-result"],
)
def test_nested_template_errors_report_once_at_the_public_boundary(
    template: str, lambdas, partials_dict
) -> None:
    logger, handler = _logger("test.nested-error", logging.ERROR)

    with pytest.raises(chevron.ChevronError):
        chevron.render(
            template,
            lambdas=lambdas,
            partials_dict=partials_dict,
            logger=logger,
        )

    assert len(handler.records) == 1
    assert handler.records[0].levelno == logging.ERROR


def test_failed_render_does_not_emit_a_successful_completion_event() -> None:
    logger, handler = _logger("test.completion", logging.INFO)

    with pytest.raises(chevron.ChevronError):
        chevron.render("{{#unclosed}}", logger=logger, log_level=logging.INFO)

    assert [level for level, _ in _events(handler)] == [
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
    ]
    assert "Render completed successfully" not in [
        message for _, message in _events(handler)
    ]


def test_warn_false_remains_silent_when_a_template_error_escapes(capsys) -> None:
    with pytest.raises(chevron.ChevronError):
        chevron.render("{{#unclosed}}")

    assert capsys.readouterr().err == ""


def test_handled_nested_template_error_is_not_reported_as_fatal() -> None:
    logger, handler = _logger("test.handled", logging.ERROR)

    @chevron.compat
    def recover(text: str, render) -> str:
        try:
            render("{{#unclosed}}")
        except chevron.ChevronError:
            return "recovered"
        raise AssertionError("expected the nested render to fail")

    assert (
        chevron.render("{{#recover}}x{{/recover}}", {"recover": recover}, logger=logger)
        == "recovered"
    )

    assert not [record for record in handler.records if record.levelno == logging.ERROR]


def test_direct_tokenisation_stays_output_free(capsys) -> None:
    with pytest.raises(chevron.ChevronError):
        list(tokenize("{{#unclosed}}"))

    assert capsys.readouterr().err == ""


def test_main_forwards_application_logger(tmp_path) -> None:
    logger, handler = _logger("test.main", logging.WARNING)
    template = tmp_path / "template.mustache"
    template.write_text("{{missing}}", encoding="utf-8")

    assert chevron.main(template, logger=logger) == ""

    assert _events(handler) == [(logging.WARNING, "Could not find key 'missing'")]


def test_cli_warn_routes_nonfatal_diagnostics(
    tmp_path, monkeypatch, caplog, capsys
) -> None:
    template = tmp_path / "template.mustache"
    template.write_text("{{missing}}", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["chevron", "--warn", str(template)])

    chevron.cli_main()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert caplog.messages == ["Could not find key 'missing'"]


def test_cli_warn_retains_its_syntax_error_presentation(
    tmp_path, monkeypatch, caplog, capsys
) -> None:
    template = tmp_path / "template.mustache"
    template.write_text("{{#unclosed}}", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["chevron", "--warn", str(template)])

    with pytest.raises(SystemExit, match='tag "unclosed" was never closed'):
        chevron.cli_main()

    captured = capsys.readouterr()
    assert captured.out == "Chevron: syntax error\n"
    assert caplog.messages[0] == "Could not find key 'unclosed'"
    assert caplog.messages[1].startswith("Template rendering failed: Unexpected EOF")
