# Tasks

## 1. Audit and test layout

- [ ] 1.1 Create a legacy-test inventory mapping every `TestRegressions` behaviour to its pytest destination, marking only strict duplicates for removal; verify the inventory has no unassigned legacy test.
- [ ] 1.2 Establish pytest-native module and plain-class groupings for renderer values/scopes, partials, tokenizer diagnostics, compatibility lambdas, and CLI/file behaviour; verify test names describe observable outcomes and no `unittest.TestCase` inheritance remains.
- [ ] 1.3 Keep `test_specifications.py` and vendored Mustache fixtures as a separate conformance harness; verify Chevron-owned tests neither rely on fixture-case names nor modify fixture content.

## 2. Convert legacy behavioural coverage

- [ ] 2.1 Convert value, scope, Unicode, dotted lookup, falsey, and iterable legacy regressions to pytest assertions and appropriate readable parametrisation; verify the focused renderer/value test modules pass.
- [ ] 2.2 Convert partial, indentation, disabled-partial, and file-entry regressions using pytest filesystem fixtures where appropriate; verify focused partial and CLI/file tests pass without mocks.
- [ ] 2.3 Convert syntax-error, nesting, callable compatibility, temporary-scope, and historical issue regressions while preserving their externally observable assertions; verify focused tokenizer and lambda tests pass.

## 3. Consolidate and remove duplication

- [ ] 3.1 Replace only structurally identical legacy cases with parameter tables and meaningful IDs, retaining separate cases where setup or observable behaviour differs; verify each retained parameter case reports independently under pytest.
- [ ] 3.2 Remove superseded incremental or framework-only tests only after equivalent behavioural coverage exists; verify no production module has lost an observable behaviour assertion.
- [ ] 3.3 Review test imports, helpers, fixtures, and module boundaries after conversion; verify Ruff and Ty pass without test-only production hooks.

## 4. Evaluate property-based coverage

- [ ] 4.1 Identify and document candidate stable renderer/tokenizer invariants, then run a focused Hypothesis spike against at least one invariant; verify generated cases are deterministic, bounded, and complement named regressions.
- [ ] 4.2 Add Hypothesis to development dependencies only if the spike finds durable additional assurance; otherwise record the decision without adding the dependency. Verify `uv sync` and focused tests pass for the chosen outcome.

## 5. Integration verification and documentation

- [ ] 5.1 Document the test-suite ownership boundary and any retained property-test invariants for contributors; verify the examples and commands match the project configuration.
- [ ] 5.2 Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check src/`, and `uv build`; verify the full suite and package build succeed.

## Workflow follow-up

- Review the completed test-only refactor before archiving this change.
