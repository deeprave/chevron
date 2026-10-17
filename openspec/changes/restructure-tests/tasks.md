# Tasks

## 1. Audit and test layout

- [x] 1.1 Create a legacy-test inventory mapping every `TestRegressions` behaviour to its pytest destination, marking only strict duplicates for removal; verify the inventory has no unassigned legacy test.
- [x] 1.2 Establish pytest-native module and plain-class groupings for renderer values/scopes, partials, tokenizer diagnostics, compatibility lambdas, and CLI/file behaviour; verify test names describe observable outcomes and no `unittest.TestCase` inheritance remains.
- [x] 1.3 Keep `test_specifications.py` and the vendored upstream Mustache fixtures byte-for-byte unchanged as a separate deterministic conformance harness; verify Chevron-owned tests neither rely on fixture-case names nor modify fixture content.

## 2. Convert legacy behavioural coverage

- [x] 2.1 Convert value, scope, Unicode, dotted lookup, falsey, and iterable legacy regressions to pytest assertions and appropriate readable parametrisation; verify the focused renderer/value test modules pass.
- [x] 2.2 Convert partial, indentation, disabled-partial, and file-entry regressions using pytest filesystem fixtures where appropriate; verify focused partial and CLI/file tests pass without mocks.
- [x] 2.3 Convert syntax-error, nesting, callable compatibility, temporary-scope, and historical issue regressions while preserving their externally observable assertions; verify focused tokenizer and lambda tests pass.

## 3. Consolidate and remove duplication

- [x] 3.1 Replace only structurally identical legacy cases with parameter tables and meaningful IDs, retaining separate cases where setup or observable behaviour differs; verify each retained parameter case reports independently under pytest.
- [x] 3.2 Remove superseded incremental or framework-only tests only after equivalent behavioural coverage exists; verify no production module has lost an observable behaviour assertion.
- [x] 3.3 Review test imports, helpers, fixtures, and module boundaries after conversion; verify Ruff and Ty pass without test-only production hooks.

## 4. Evaluate property-based coverage

- [x] 4.1 Identify and document grammar-constrained stable renderer/tokenizer invariants, then run a focused Hypothesis spike against at least one invariant; verify generated cases are bounded, reproducible, and complement rather than replace named regressions and Mustache fixtures.
- [x] 4.2 Add Hypothesis to development dependencies when the spike provides durable additional assurance, configure reproducible failure reporting and practical runtime, and use `pytest.mark.parametrize` around any shared property-test cycle. Verify `uv sync` and focused tests pass.

## 5. Continuous integration and publishing

- [x] 5.1 Add `.github/workflows/ci.yml` for pull requests and pushes to `main`, using uv and a Python 3.11–3.15 matrix; pin third-party Actions to immutable commits, configure Dependabot to monitor GitHub Actions and uv dependencies, and verify it runs pytest with a coverage XML report, Ruff check and format verification, Ty, Bandit, Vulture, OSV checking, and `uv build`.
- [x] 5.3 Add a manually dispatched `.github/workflows/publish.yml`; verify it derives the version from `pyproject.toml`, requires successful complete CI for the exact release commit, builds with uv, uses the configured PyPI trusted publisher through OIDC without a stored PyPI token, and creates the matching GitHub release and `v<version>` tag only after publishing succeeds, using matching changelog notes when available or GitHub-generated notes otherwise.

## 6. Integration verification and documentation

- [x] 6.1 Document the test-suite ownership boundary and retained property-test invariants for contributors; verify the examples and commands match the project configuration.
- [x] 6.2 Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check src/`, the relevant security/dead-code checks, and `uv build`; verify the full suite and package build succeed.

## Workflow follow-up

- Review the completed test-only refactor before archiving this change.
