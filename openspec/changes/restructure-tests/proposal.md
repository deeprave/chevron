# Proposal

## Why

Chevron's test suite mixes a large legacy `unittest.TestCase` module with newer pytest modules. This makes related behaviours difficult to find, repeats setup and assertions, and obscures the boundary between Chevron's own behavioural contract and vendored Mustache conformance fixtures.

## What Changes

- Convert the remaining legacy unittest coverage to plain pytest tests without changing the behaviours it protects.
- Reorganise tests by externally observable renderer, tokenizer, public-API, lambda, partial, and regression behaviour.
- Combine structurally identical cases with readable `pytest.mark.parametrize` tables while retaining distinct behaviour where setup or assertions differ.
- Separate Chevron behavioural regressions from the vendored Mustache specification harness and retain the fixture suite as an independent compatibility signal.
- Add targeted Hypothesis property tests only where generated inputs can assert stable renderer/tokenizer invariants; do not use generated testing as a substitute for named regressions or specification fixtures.
- Remove redundant incremental and framework-only tests discovered during the migration, preserving coverage for observable production behaviour.

## Capabilities

### New Capabilities

None. This is a test-only refactor with no intended production behaviour change.

### Modified Capabilities

None. Existing OpenSpec requirements remain the behavioural oracle; no requirement changes are proposed.

## Impact

Affected areas are the `tests/` suite, development dependencies, pytest configuration, and test documentation. The renderer, tokenizer, public API, vendored Mustache fixture contents, package runtime dependencies, and published behaviour are out of scope.
