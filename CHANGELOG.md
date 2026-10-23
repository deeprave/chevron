# Changelog

All notable changes to Chevron are documented in this file.

## [Unreleased]

### Added

- `async_render()` provides runtime-neutral async rendering for applications using asyncio or Trio. The optional `anyio` or `trio` extra enables it; async lambdas, readers, iterables, and filesystem partials are supported without a library-owned event loop.
- Added `API.md` with complete synchronous and asynchronous API, lambda, partial, and logging guidance.
- Mustache dynamic partial names allow `{{>*name}}` to select one partial from
  the active context while retaining the caller's scope, partial indentation,
  and partial lookup policy.

### Changed

- A partial name beginning with `*` is now a dynamic selector; Chevron no
  longer treats `{{>*name}}` as a literal partial named `*name`.
- Renderer scope traversal now uses private immutable frames, so sections and
  nested renders never structurally mutate a caller-provided `scopes` sequence.
- The internal tokenizer now accepts source text only. Direct callers that supply file-like objects receive a `TypeError`; `chevron.render()` continues to accept file-like templates. Moving input I/O to the renderer boundary prepares the package for async rendering.
- `chevron.render()` now accepts keyword-only standard-library `logger=` and `log_level=` options for per-render diagnostics. A supplied `logging.Logger` or `logging.LoggerAdapter` remains under application configuration, while `warn` retains its established truthiness-based opt-in behaviour for Chevron's default warning output.

### Fixed

- Rejected filesystem partial diagnostics identify the requested reference and whether it was an absolute path or parent traversal, without disclosing configured or resolved filesystem paths.
- Inverted-section bookkeeping no longer confuses an application value of
  `True` with Chevron's internal context state, including current-scope
  interpolation.
- Synchronous rendering rejects awaitable template-reader and lambda results
  with guidance to use `async_render()` rather than leaking unawaited
  coroutines.

## [0.15.0] - 2026-10-18

### Added

- Mustache-standard zero-argument interpolation lambdas and one-argument section lambdas now pass the pinned Mustache lambda fixtures when declared with `@chevron.func` and `@chevron.section`. Interpolation results are rendered with the configured render-default delimiters; section results start with their section's opening delimiters.
- `@chevron.func`, `@chevron.section`, and `@chevron.compat` declare interpolation, Mustache-standard section, and Chevron two-argument compatibility protocols respectively. Undecorated registered two-argument callbacks remain compatible.
- `chevron.render()` accepts an optional `lambdas=` mapping that supplies
  callable section tags for a render. In explicit mode, configured lambda names
  take precedence over template data.
- Callable values found in template data are rejected in explicit mode rather
  than invoked or rendered. Omit `lambdas` or pass `None` to retain legacy
  callable template-data behaviour.
- Supplying `lambdas={}` explicitly disables all callable section execution.
- Invalid `lambdas=` arguments now raise descriptive `TypeError` exceptions.
- `render()` now disables filesystem partial lookup by default
  (`partials_path=None`). Supply an explicit trusted directory to enable it;
  use `partials_path="."` to restore the historic library behaviour.

### Changed

- Filesystem partial lookup now rejects absolute partial names, lexical parent
  traversal, and symlinks that escape the configured partial directory. A
  symlinked partial directory remains a supported root.
- Existing callers that omit `lambdas` (or pass `None`) retain legacy
  two-argument section-lambda handling.
- In explicit mode, callable template-data values are lookup leaves. This
  prevents callable-object traversal and means templates should receive plain
  data; configured section lambdas can provide a constrained temporary scope.
- Rejected callable template data behaves as missing and can emit a `warn=True`
  diagnostic.
- Lambda callbacks that return `None` now render as empty output and can emit a `warn=True` diagnostic instead of raising a later type error.
- Tokenisation diagnostics are now per render and nested rendering no longer shares module-level tokenizer state. Token-cache replay is limited to the legacy `@chevron.compat` callback helper.

### Modernised

- Replaced the legacy packaging configuration with a PEP 621 `pyproject.toml`
  built by `uv_build`; package and CLI versions now derive from installed
  project metadata.
- Moved the package to the `src/` layout while preserving the established
  `chevron` import and command-line interfaces.
- Began converting the test suite to pytest-compatible, behaviour-focused
  tests while retaining the existing unittest coverage during the transition.
- Added informational pytest-cov reporting without an enforced coverage
  threshold.
- Replaced the Mustache specification submodule with a pinned, attributed copy
  of its fixtures in the test suite.
- Added Ruff formatting and linting, plus Ty type checking, as development
  checks.

### Compatibility notes

- Applications rendering untrusted templates should always supply an explicit
  `lambdas` mapping, including `lambdas={}` when no callable sections are
  permitted. This controls callable sections only; it is not a general template
  sandbox.
- The command-line interface keeps its existing `--path .` default. The safer
  partial default applies only to the library API.
