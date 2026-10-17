# Design

## Context

See [proposal.md](proposal.md) for motivation. The suite currently contains a broad `tests/test_regressions.py` `unittest.TestCase` alongside pytest-native modules for public API, raw-value resolution, lambda mappings, lambda protocols, and vendored Mustache fixtures. The renderer and tokenizer have stable public behaviours but no shared pytest fixtures or collection layout.

## Goals / Non-Goals

**Goals:**

- Preserve each non-redundant observable behaviour while converting legacy unittest assertions and grouping tests by the production behaviour they exercise.
- Use parameterisation only when setup, action, and assertion structure are genuinely the same, with readable case IDs for non-obvious values.
- Keep the vendored Mustache suite isolated from Chevron-owned behavioural and regression tests.
- Introduce property-based testing only for small, deterministic invariants where generated input adds coverage beyond named examples.

**Non-Goals:**

- Changing renderer or tokenizer semantics, public APIs, fixture content, or Mustache conformance expectations.
- Adding broad generated-template fuzzing, a coverage gate, mocks, or test-only hooks in production code.
- Rewriting every test merely to make the suite stylistically uniform.

## Decisions

### Migrate by behavioural area, not by legacy class shape

Split the legacy regression class into pytest-native modules or classes grouped around rendering values and scopes, partials, syntax diagnostics, compatibility lambdas, and CLI/file entry points. Cross-reference each group with `renderer.py`, `tokenizer.py`, or `main.py` before moving it. This gives pytest output meaningful behaviour names and avoids retaining the arbitrary historical `TestRegressions` bucket.

Keeping one converted class would minimise file movement, but would preserve the navigation problem the change addresses.

### Treat named regressions as the baseline contract

Translate every legacy test to an outcome-oriented pytest test before removing duplication. Keep cases tied to historical issues, syntax error messages, Unicode, partial indentation, callable compatibility, and scope restoration as named regressions unless an equivalent parametrised case covers the same externally visible assertion.

Removing tests solely because the current Mustache fixtures cover nearby syntax is rejected: Chevron-specific compatibility behaviours are not owned by the vendored specification suite.

### Parameterise equivalent inputs without hiding distinct setup

Use `pytest.mark.parametrize` for cases such as equivalent missing-value forms, disabled partial-path values, similar interpolation variants, and syntax input/error pairs. Retain separate tests where temporary scope construction, callback effects, file-system setup, or diagnostic assertions differ. Use `tmp_path` and existing `capsys`/`monkeypatch` fixtures rather than mocks.

### Add Hypothesis only after selecting stable invariants

Evaluate a small, explicit Hypothesis dependency for invariants such as literal templates rendering unchanged, tokenisation/rendering preserving ordinary Unicode text, and generated safe scalar values following existing interpolation semantics. Pin no arbitrary strategies to implementation internals, set practical examples/deadlines only when evidence requires them, and keep named regression examples. If no invariant provides meaningful additional assurance after a short spike, do not add the dependency.

### Keep conformance execution physically and conceptually separate

Retain `tests/test_specifications.py` and its vendored fixtures as the specification harness. Chevron-owned tests must not depend on fixture-case names or mutate fixture content. Shared utilities, if justified, may live in a small pytest helper but must not obscure which suite proves local behaviour versus Mustache compatibility.

## Risks / Trade-offs

- [Accidental behavioural coverage loss during consolidation] → map each legacy test to its destination and compare the full suite before and after each behavioural group.
- [Over-parameterised, unreadable tests] → parameterise only identical structures and use individual tests for different setup or observations.
- [Hypothesis adds dependency and runtime cost without useful signal] → require a defined invariant and a passing focused spike before retaining it.
- [Specification and local regression tests blur again] → retain separate test modules and document their distinct ownership.

## Migration Plan

Implement in small behavioural groups, running the affected modules followed by the full suite after each group. Keep the change reversible through ordinary source control; no runtime or data migration is required.
