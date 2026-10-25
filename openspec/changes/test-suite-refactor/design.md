# Design

## Context

See `proposal.md` for motivation. The repository already separates vendored
Mustache conformance execution in `test_specifications.py` and
`async/test_specifications.py`, while Chevron-owned coverage is distributed
across topical modules and a large async rendering module. The latter contains
many parallel synchronous/asynchronous behavioral examples, including recent
inheritance and whitespace regressions.

This change is test-only. The vendored upstream JSON modules remain immutable
external evidence; their loader, markers, and discovery are not a general
fixture framework for Chevron-owned cases.

## Goals / Non-Goals

**Goals:**

- Establish an evidence-based inventory of collection/execution cost,
  duplication, implementation-coupled tests, and coherent behavioral groups.
- Make shared template behavior readable as named, declarative Python cases
  executed through public synchronous and asynchronous entry points.
- Keep failures local and intelligible while retaining asyncio and Trio
  coverage where asynchronous behavior is relevant.
- Leave the suite at least as strong and no slower without an evidence-backed
  reason.

**Non-Goals:**

- Changing renderer, tokenizer, CLI, or public API behavior.
- Reformatting or relocating tests solely for visual consistency.
- Replacing vendored Mustache fixtures, modifying their content, or relabeling
  Chevron-owned tests as conformance.
- Creating a universal testing DSL, a second fixture-file format, or broad
  parameter Cartesian products.

## Decisions

### Audit before consolidation

Capture collection and execution measurements, module/test counts, repeated
sync/async behavior, and uses of private implementation details before moving
tests. Review candidates individually: a test that touches implementation
internals is retained when it verifies a supported public contract, otherwise
it is replaced by a public behavior assertion or removed if redundant.

This prevents a mechanically smaller suite from losing regression coverage.
Running broad test moves before the inventory would make performance and
coverage changes impossible to attribute.

### Use typed Python case collections for Chevron-owned template behavior

Introduce small, topic-specific case modules under `tests/` with immutable,
named case records. A record may express template source, data, partial
mappings, expected output, and only the configuration required by that topic.
Python is chosen over JSON because multiline template whitespace remains
readable, typing is available, and no local fixture schema/loader is needed.

The case records are test support, not pytest resource fixtures. Continue to
use pytest fixtures for resources and lifecycle concerns such as temporary
directories, readers, logging capture, and async backend selection.

### Share behavioral cases, not test execution machinery

Synchronous and asynchronous test modules import the same case collection and
call `chevron.render()` or `chevron.async_render()` respectively. Async tests
retain the existing AnyIO backend parameterisation. Keep the two small runners
explicit rather than introducing a generic sync/async execution abstraction;
their public API calls and failure traces should remain obvious.

Case collections are appropriate when the same source-level scenario applies
to more than one renderer. Resource-heavy, timing-sensitive, filesystem,
concurrency, or callback-protocol tests remain focused topical tests unless an
audit identifies meaningful common behavior.

### Group by durable behavior and retain public-contract exceptions

Move or consolidate only after identifying the behavior each test protects.
Group behavior around rendering values and scopes, sections, partial lookup and
inheritance, whitespace/standalone rules, lambda protocols, diagnostics,
filesystem and reader handling, public API, and async-only execution.

Do not create a generic `regressions` grouping: the underlying behavior is the
test's home. Preserve focused tests for supported non-source template input,
including token sequences, since a source-template case cannot exercise that
public contract.

### Preserve conformance isolation and marker semantics

Keep vendored fixture discovery in `specification_fixtures.py`, its existing
`conformance` marker, and its upstream module markers. Chevron-owned case
collections receive no conformance marker and do not enter the vendored fixture
directory. This keeps `pytest -m conformance` a stable upstream compatibility
gate and lets ordinary behavioral coverage evolve independently.

## Risks / Trade-offs

- [A shared case table conceals scenario purpose] → Require descriptive stable
  case names and keep topic-specific collections small.
- [Parameterisation multiplies runtime] → Parameterize independent dimensions
  only when each combination protects distinct behavior; use duration data to
  verify the result.
- [Consolidation removes edge coverage] → Preserve or replace every affected
  assertion with a public behavior case before deletion, then run focused and
  full suites.
- [Large file moves create noisy reviews] → Refactor one behavioral group at a
  time and avoid unrelated renames or formatting.

## Migration Plan

1. Record the audit inventory and select the first high-value behavioral group,
   beginning with template partial/inheritance and whitespace cases.
2. Add the typed shared case collection and explicit sync/async public runners.
3. Migrate equivalent cases, retaining focused public-contract exceptions.
4. Repeat for only the groups justified by the inventory, validating duration,
   collection, conformance, and full-suite results after each group.
5. Roll back any group migration by restoring its prior focused tests; no
   production data or runtime migration is involved.
