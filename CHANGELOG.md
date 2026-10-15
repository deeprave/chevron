# Changelog

All notable changes to Chevron are documented in this file.

## [Unreleased]

### Added

- `chevron.render()` accepts an optional `lambdas=` mapping that defines which
  section tags may invoke callables for a render. The mapping is separate from
  template data: it neither supplies template values nor changes ordinary
  scope precedence.
- Explicit mappings match complete template names and callable identity. Python
  bound methods also match when both their receiver and underlying function are
  identical.
- Supplying `lambdas={}` explicitly disables all callable section execution.
- Invalid `lambdas=` arguments now raise descriptive `TypeError` exceptions.
- `render()` now disables filesystem partial lookup by default
  (`partials_path=None`). Supply an explicit trusted directory to enable it;
  use `partials_path="."` to restore the historic library behaviour.

### Changed

- Existing callers that omit `lambdas` (or pass `None`) retain legacy
  two-argument section-lambda handling.
- In explicit mode, all callable values are lookup leaves. This prevents
  callable-object traversal but means templates should receive plain data;
  authorised section lambdas can provide a constrained temporary scope.
- Unregistered callable sections behave as missing and can emit a `warn=True`
  diagnostic that distinguishes an absent mapping name from an identity mismatch.

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
