# Spec Delta

## Purpose

Allow applications to route Chevron rendering diagnostics to their own output while retaining stderr defaults, explicit suppression and predictable error behaviour.

## ADDED Requirements

### Requirement: Per-render Python logger

The renderer SHALL accept a keyword-only `logger` option containing a `logging.Logger` or `logging.LoggerAdapter`. Eligible diagnostics SHALL use native Python logging methods and deferred format arguments. Chevron SHALL NOT configure a supplied logger's handlers, propagation or levels.

#### Scenario: Default warning destination

- **WHEN** a missing key is rendered with `warn=True` and no logger
- **THEN** its existing warning text is written once to stderr with the existing newline convention

### Requirement: Logger selection

With `logger=None` and a truthy `warn`, Chevron SHALL deliver eligible diagnostics to its shared `chevron` logger at WARNING level, preserving existing warning wording and newline behaviour through standard Python logging. Chevron SHALL NOT add handlers or configure global logging from the library. A supplied logger SHALL replace the default destination and receive eligible diagnostics according to the application's logging configuration, regardless of `warn`.

#### Scenario: Application selects a destination

- **WHEN** a render supplies an application logger
- **THEN** each eligible diagnostic is delivered to that logger instead of stderr
- **AND** the application's logger configuration determines which levels are emitted

### Requirement: Default logger selection and severity filtering

When no logger is supplied, falsey `warn` values SHALL suppress Chevron's default delivery and truthy values SHALL select it at `logging.WARNING`. A supplied logger SHALL be selected independently of `warn`; keyword-only `log_level` SHALL select Chevron's diagnostic delivery threshold, while the application's own configuration SHALL continue to filter delivery. Logger selection and filtering SHALL NOT suppress exceptions or change template output.

#### Scenario: Custom logger is independent of the default sink switch

- **WHEN** `warn=False` and an enabled application logger is supplied
- **THEN** eligible diagnostics are delivered to that logger and none are written to stderr
- **AND** a fatal template error still raises

#### Scenario: Default enabled verbosity

- **WHEN** `warn=True` and no logger is supplied
- **THEN** WARNING and ERROR events are eligible and INFO and DEBUG events are suppressed

#### Scenario: Application threshold

- **WHEN** an application logger is supplied with `log_level=logging.ERROR`
- **THEN** recoverable warnings are suppressed while fatal template error diagnostics remain eligible

### Requirement: Diagnostic severity describes the event

Chevron SHALL classify fatal template syntax errors as ERROR, existing recoverable warning conditions as WARNING, top-level render start and successful completion as INFO, and selected lookup, lambda dispatch and partial resolution decisions as DEBUG. DEBUG messages SHALL NOT dump template data, template source, callable representations or rendered values.

#### Scenario: Recoverable lambda condition

- **WHEN** a selected lambda returns None and warnings are enabled at the default threshold
- **THEN** Chevron emits WARNING and renders the established empty value

#### Scenario: Detailed diagnostics

- **WHEN** diagnostics are enabled at DEBUG during a render containing a missing key, a lambda and a partial
- **THEN** diagnostic output includes relevant resolution and dispatch decisions, with lifecycle events at INFO
- **AND** application data values and full template content are not included in those debug messages

### Requirement: Recursive rendering inherits diagnostics

Sections, iterable items, partials, lambda-returned templates and supplied rendering callbacks SHALL retain the enclosing render's selected logger. Independent public render calls SHALL NOT inherit logger settings implicitly or interfere with one another.

#### Scenario: Partial uses the enclosing callback

- **WHEN** a partial encounters a missing key in an enabled render with an application logger
- **THEN** its warning reaches that logger in rendering order, without a stderr fallback

#### Scenario: Re-entrant render selects its own destination

- **WHEN** application code starts another public render with different diagnostic options during an outer render
- **THEN** each render uses its own options, and the outer options remain intact afterwards

### Requirement: Fatal reporting preserves the rendering failure

An unhandled template syntax error SHALL produce one eligible ERROR event as it escapes a public render call, not one per recursive frame. The original exception type, message and traceback SHALL be preserved. Diagnostics SHALL NOT convert a failed render into a successful or empty result.

#### Scenario: Malformed nested partial

- **WHEN** an enabled render fails on malformed syntax inside a nested partial
- **THEN** one ERROR event describes the template failure, including available line information
- **AND** the original syntax exception propagates

#### Scenario: Application catches a nested error

- **WHEN** a lambda catches a syntax error from its supplied rendering callback and returns valid output
- **THEN** the enclosing render does not report an unhandled fatal template error

### Requirement: Logger delivery uses standard Python logging behaviour

Chevron SHALL NOT wrap, retry or redirect application logger delivery. Logger handler behaviour and failures SHALL follow Python logging's normal semantics. Chevron SHALL NOT fall back to stderr when an application logger is supplied.

#### Scenario: Application logger replaces stderr

- **WHEN** an application logger handles a warning
- **THEN** Chevron delegates delivery only through that logger without another attempt or stderr write

### Requirement: CLI diagnostics use standard logging

The CLI SHALL configure ordinary process-level logging with Chevron's historic message-only stderr format before invoking the renderer. `--warn` SHALL select WARNING diagnostics. The CLI SHALL NOT provide a `--log-level` option or a CLI-specific diagnostic logger.

#### Scenario: CLI warnings use standard logging

- **WHEN** the CLI is invoked with `--warn` and encounters a missing key
- **THEN** it emits the established warning text on stderr
- **AND** rendered template content remains on stdout
