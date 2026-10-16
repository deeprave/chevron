# Tasks

## 1. Lambda protocol representation

- [ ] 1.1 Add the internal lambda-definition wrapper and public standard-section decorator, then verify registered standard and unannotated legacy callbacks select their intended protocols through focused pytest cases.
- [ ] 1.2 Validate wrapped and unwrapped explicit mapping values without changing mapping-first lookup or callable template-data rejection, then verify shadowing and invalid mapping regression tests pass.

## 2. Renderer dispatch and recursive output

- [ ] 2.1 Implement zero-argument interpolation lambda dispatch for compatibility and explicit modes, recursively render returned source with default delimiters, and verify escaped, unescaped, repeated-call, and alternate-delimiter cases with pytest.
- [ ] 2.2 Implement Mustache-standard one-argument section dispatch and recursively render its returned source with the active delimiters, then verify raw section input, expansion, repeated-call, and alternate-delimiter cases with pytest.
- [ ] 2.3 Preserve the existing two-argument legacy section callback and temporary-data rendering helper, then verify existing legacy lambda regression tests continue to pass.
- [ ] 2.4 Carry protocol metadata and explicit-mapping isolation through nested renders and partials, then verify recursive and partial lambda cases with pytest.

## 3. Compatibility-mode classification

- [ ] 3.1 Classify compatibility-mode zero- and one-argument callables with safe signature inspection rather than runtime `TypeError` dispatch, then verify all pinned Mustache lambda fixtures pass unchanged.
- [ ] 3.2 Preserve existing handling for uninspectable compatibility-mode callables, then verify interpolation does not introduce a new call and legacy sections retain the two-argument path.

## 4. Documentation and integration verification

- [ ] 4.1 Document the standard section-lambda decorator, zero-argument interpolation behaviour, delimiter distinction, and retained legacy callback contract in the public API documentation; verify the examples match executable pytest coverage.
- [ ] 4.2 Add a technical changelog entry for Mustache lambda conformance and the explicit protocol opt-in, then verify its stated compatibility boundary matches the regression tests.
- [ ] 4.3 Run the full project checks—`uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check src/`, and `uv build`—and record any remaining failures outside this change's scope.
