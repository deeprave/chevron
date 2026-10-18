# Tasks

## 1. Lambda protocol representation

- [x] 1.1 Add the internal lambda-definition wrapper and public `@chevron.func`, `@chevron.section`, and `@chevron.compat` decorators, then verify decorated and unannotated callbacks select their intended protocols through focused pytest cases.
- [x] 1.2 Validate wrapped and unwrapped explicit mapping values without changing mapping-first lookup or callable template-data rejection, then verify shadowing and invalid mapping regression tests pass.

## 2. Renderer dispatch and recursive output

- [x] 2.1 Implement zero-argument interpolation lambda dispatch for compatibility and explicit modes, recursively render returned source with default delimiters, and verify escaped, unescaped, repeated-call, and alternate-delimiter cases with pytest.
- [x] 2.2 Implement Mustache-standard one-argument section dispatch with literal source input, including comments and standalone whitespace, and recursively render its returned source with the active delimiters; verify source preservation, expansion, repeated-call, and alternate-delimiter cases with pytest.
- [x] 2.3 Preserve the existing two-argument legacy section callback and temporary-data rendering helper, then verify existing legacy lambda regression tests continue to pass.
- [x] 2.4 Carry protocol metadata and explicit-mapping isolation through nested renders and partials, then verify recursive and partial lambda cases with pytest.

## 3. Compatibility-mode protocol selection

- [x] 3.1 Require the declared decorators for the new zero- and one-argument protocols in compatibility mode, without signature inspection or `TypeError` dispatch, then adapt the reviewed fixture harness.
- [x] 3.2 Preserve undecorated interpolation stringification and two-argument legacy section behaviour.

## 4. Documentation and integration verification

- [x] 4.1 Document `@chevron.func`, `@chevron.section`, and `@chevron.compat`, zero-argument interpolation behaviour, delimiter distinction, and the retained unannotated legacy callback contract in the public API documentation; verify the examples match executable pytest coverage.
- [x] 4.2 Add a technical changelog entry for Mustache lambda conformance and the explicit protocol opt-in, then verify its stated compatibility boundary matches the regression tests.
- [x] 4.3 Run the full project checks—`uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check src/`, and `uv build`—and record any remaining failures outside this change's scope.

## 5. Review remediation

- [x] 5.1 Isolate tokenizer state and immutable configured delimiter defaults in `_RenderContext`; preserve lexical delimiter propagation through skipped and iterated sections, partials, and nested rendering.
- [x] 5.2 Restrict token-cache replay to legacy compatibility callbacks; restore falsy temporary-data behaviour; normalise `None` callback results to an optional warning and empty output.
- [x] 5.3 Preserve decorated callable metadata and descriptor behaviour, clarify diagnostics and documentation, and add focused behavioural regression tests for the accepted review cases.
