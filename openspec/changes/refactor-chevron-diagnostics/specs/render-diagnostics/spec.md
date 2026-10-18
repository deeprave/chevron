# Spec Delta

## Purpose

Allow applications to route Chevron rendering diagnostics to their own output while retaining stderr defaults, explicit suppression and predictable error behaviour.

## ADDED Requirements

### Requirement: Per-render diagnostic callback

The renderer SHALL accept keyword-only `logger` and `log_level` options. Enabled diagnostics SHALL call `logger(level, message)` with a numeric standard-library logging severity and a string without an added trailing newline. With `logger=None`, Chevron SHALL use stderr, appending the platform newline and preserving existing warning wording.

#### Scenario: Default warning destination

- **WHEN** a missing key is rendered with `warn=True` and no logger
- **THEN** its existing warning text is written once to stderr with the existing newline convention

#### Scenario: Application selects a destination

- **WHEN** a render supplies a callback and enables warnings
- **THEN** each eligible diagnostic is delivered to that callback instead of stderr
- **AND** a bound standard-library `Logger.log` method is a supported callback

### Requirement: Suppression precedes severity filtering

The renderer SHALL suppress all diagnostic delivery when `warn=False`, regardless of callback or threshold. With `warn=True`, it SHALL deliver only events at or above `log_level`, whose default is WARNING. Suppression SHALL NOT suppress exceptions or change template output.

#### Scenario: Custom logger does not override silence

- **WHEN** `warn=False`, a logger is supplied, and `log_level` is DEBUG
- **THEN** no callback is invoked and no diagnostics are written to stderr, including for a fatal template error
- **AND** a fatal template error still raises

#### Scenario: Default enabled verbosity

- **WHEN** `warn=True` and no threshold is supplied
- **THEN** WARNING and ERROR events are eligible and INFO and DEBUG events are suppressed

#### Scenario: Explicit threshold

- **WHEN** `warn=True` and the threshold is ERROR
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

Sections, iterable items, partials, lambda-returned templates and supplied rendering callbacks SHALL retain the enclosing render's diagnostic callback, suppression and threshold. Independent public render calls SHALL NOT inherit these settings implicitly or interfere with one another.

#### Scenario: Partial uses the enclosing callback

- **WHEN** a partial encounters a missing key in an enabled render with a custom logger
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

### Requirement: Diagnostic callback failures do not cause recursive reporting

Chevron SHALL NOT retry a failed diagnostic callback, report its failure through itself, or fall back to stderr. A callback failure during normal rendering SHALL propagate. If reporting an existing fatal template error fails, the original template error SHALL remain the primary exception.

#### Scenario: Callback fails on a warning

- **WHEN** a custom callback raises while handling a warning
- **THEN** that failure propagates without another callback attempt or stderr write

#### Scenario: Callback fails during fatal reporting

- **WHEN** a custom callback raises while reporting an unhandled template syntax error
- **THEN** the original template syntax error is re-raised rather than replaced by the callback error
