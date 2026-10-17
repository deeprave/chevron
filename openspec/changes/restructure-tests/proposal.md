# Proposal

## Why

Chevron's test suite mixes a large legacy `unittest.TestCase` module with newer pytest modules. This makes related behaviours difficult to find, repeats setup and assertions, and obscures the boundary between Chevron's own behavioural contract and vendored Mustache conformance fixtures.

## What Changes

- Convert the remaining legacy unittest coverage to plain pytest tests without changing the behaviours it protects.
- Reorganise tests by externally observable renderer, tokenizer, public-API, lambda, partial, and regression behaviour.
- Combine structurally identical cases with readable `pytest.mark.parametrize` tables while retaining distinct behaviour where setup or assertions differ.
- Separate Chevron behavioural regressions from the vendored Mustache specification harness and retain the fixture suite as an independent compatibility signal.
- Retain the vendored upstream Mustache specification cases byte-for-byte as the deterministic, named conformance oracle. Add bounded Hypothesis property tests only in Chevron-owned coverage where generated inputs can assert stable renderer/tokenizer invariants; do not replace or rewrite specification fixtures or named regressions with generated testing.
- Remove redundant incremental and framework-only tests discovered during the migration, preserving coverage for observable production behaviour.
- Add a `ci.yml` workflow for pull requests and pushes to `main`, covering the supported Python 3.11–3.15 range, the project’s test/static-analysis/build checks, and CI-based SonarCloud analysis with explicit source and test scopes. Pin third-party Actions to immutable commits and use Dependabot to track Action and uv dependency updates.
- Add a manually dispatched `publish.yml` trusted-publisher workflow which derives the release version from `pyproject.toml`, verifies CI for the selected commit, publishes its build to PyPI using the already configured OIDC publisher, then creates the matching GitHub release and tag with version-specific changelog notes when available.

## Capabilities

### New Capabilities

None. This is a test-only refactor with no intended production behaviour change.

### Modified Capabilities

None. Existing OpenSpec requirements remain the behavioural oracle; no requirement changes are proposed.

## Impact

Affected areas are the `tests/` suite, development dependencies, pytest configuration, test documentation, and GitHub workflows. The renderer, tokenizer, public API, vendored Mustache fixture contents, package runtime dependencies, and published behaviour are out of scope.
