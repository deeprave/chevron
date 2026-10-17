# Design

## Context

See [proposal.md](proposal.md) for motivation. The suite currently contains a broad `tests/test_regressions.py` `unittest.TestCase` alongside pytest-native modules for public API, raw-value resolution, lambda mappings, lambda protocols, and vendored Mustache fixtures. The renderer and tokenizer have stable public behaviours but no shared pytest fixtures or collection layout.

## Goals / Non-Goals

**Goals:**

- Preserve each non-redundant observable behaviour while converting legacy unittest assertions and grouping tests by the production behaviour they exercise.
- Use parameterisation whenever cases share the same setup, action, and assertion cycle, with readable case IDs for non-obvious values. This applies independently of whether a property test is also useful.
- Keep the vendored Mustache suite isolated from Chevron-owned behavioural and regression tests.
- Retain every vendored upstream Mustache fixture byte-for-byte as a deterministic named conformance case. Introduce property-based testing only in Chevron-owned tests for small, bounded invariants where generated input adds coverage beyond named examples.
- Run the supported Python 3.11–3.15 matrix, the project’s test/static-analysis checks, and a package build for pull requests and pushes to `main`.
- Publish release builds through a manually dispatched, CI-gated workflow using the preconfigured PyPI trusted publisher, then create the GitHub release and tag.

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

### Preserve fixture conformance and add bounded properties

The upstream fixture cases provide traceability to the Mustache specification: each has a stable name, reviewed input, and exact output. They are vendored inputs, not Chevron tests to rewrite, and must remain byte-for-byte unchanged. Replacing them wholesale with generated data would lose that audit trail and make gaps harder to diagnose. Retain them as a separate parametrised conformance harness.

Use Hypothesis alongside the fixture suite for grammar-constrained, bounded properties that exercise relationships rather than a catalogue of examples. Candidate properties include literal text rendering unchanged, safe scalar interpolation matching the existing escaping contract, and tokenisation preserving literal source text. Parameterise protocol, delimiter, and mode variants around a property when they share its test cycle. Avoid unconstrained template fuzzing, implementation-shaped strategies, global random state, and properties whose oracle simply repeats renderer logic. Configure the resulting suite for reproducible failures and practical runtime.

### Make CI and publishing explicit repository contracts

`ci.yml` should run on `pull_request` and `push` to `main`. It should use uv and a 3.11–3.15 matrix, run pytest, Ruff check and format verification, Ty, Bandit, Vulture, OSV checking, and `uv build`. Third-party Actions must be pinned to immutable commit identifiers, with Dependabot configured to propose their updates and updates to the uv lockfile. Local pre-commit remains the fast developer gate; CI independently proves the repository state.

`publish.yml` should run only when manually dispatched for a selected commit. `pyproject.toml` is the authoritative version source. Before building or publishing, it must use the GitHub Actions API to require a successful push-triggered CI run and every expected CI job for that exact commit, and reject an existing matching release or tag. It should build with uv, publish with `uv publish --trusted-publishing always` to the preconfigured PyPI trusted publisher, then create the GitHub release and `v<version>` tag only after publishing succeeds. If `CHANGELOG.md` contains a non-empty matching `## [<version>]` section, it becomes the release notes; otherwise, GitHub generates notes from the commits. Each job must have only the permissions it needs. It must not publish on arbitrary branch pushes or tags.

### Keep conformance execution physically and conceptually separate

Retain `tests/test_specifications.py` and its vendored fixtures as the specification harness. Chevron-owned tests must not depend on fixture-case names or mutate fixture content. Shared utilities, if justified, may live in a small pytest helper but must not obscure which suite proves local behaviour versus Mustache compatibility.

## Risks / Trade-offs

- [Accidental behavioural coverage loss during consolidation] → map each legacy test to its destination and compare the full suite before and after each behavioural group.
- [Over-parameterised, unreadable tests] → parameterise only identical structures and use individual tests for different setup or observations.
- [Hypothesis adds dependency and runtime cost without useful signal] → require a defined invariant and a passing focused spike before retaining it.
- [Generated properties become flaky or opaque] → bound strategies, preserve exact fixture examples, and ensure failing examples reproduce under the committed configuration.
- [Specification and local regression tests blur again] → retain separate test modules and document their distinct ownership.
- [A workflow gives a false signal of support] → make the matrix match the declared 3.11–3.15 support range and run the same named checks which developers use locally.
- [A release event publishes an unverified artefact] → build from the release revision and keep publication limited to the configured trusted publisher.

## Migration Plan

Implement in small behavioural groups, running the affected modules followed by the full suite after each group. Keep the change reversible through ordinary source control; no runtime or data migration is required.
