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

- Establish an evidence-based inventory of rendering behavior coverage,
  duplication, implementation-coupled tests, coherent behavioral groups, and
  collection/execution cost.
- Make shared template behavior readable as named, declarative Python cases
  executed through public synchronous and asynchronous entry points.
- Keep failures local and intelligible while retaining asyncio and Trio
  coverage where asynchronous behavior is relevant.
- Produce complete, maintainable regression evidence for the rendering engine.

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

### Coverage is primary; timing is diagnostic

The refactor's purpose is complete, readable behavioral coverage, not a speed
target. Collection and execution measurements provide context for decisions and
help identify accidental expansion, but a measured slowdown is acceptable when
the resulting cases protect distinct rendering behavior. Conversely, a speedup
does not justify losing a meaningful behavior assertion.

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

### Start with partial, inheritance, and whitespace behavior

The first consolidation group is partial lookup and inheritance together with
whitespace and standalone-line behavior. Its shared cases SHALL run through
the public synchronous API and the public asynchronous API under both asyncio
and Trio. This establishes the case format and runners before other groups are
considered.

### Group by durable behavior and retain public-contract exceptions

Move or consolidate only after identifying the behavior each test protects.
Group behavior around rendering values and scopes, sections, partial lookup and
inheritance, whitespace/standalone rules, lambda protocols, diagnostics,
filesystem and reader handling, public API, and async-only execution.

Do not create a generic `regressions` grouping: the underlying behavior is the
test's home. Preserve focused tests for supported non-source template input,
including token sequences, since a source-template case cannot exercise that
public contract.

### Expand only source-template input/output scenarios after the pilot

The pilot demonstrates that a named case is a useful rendering-behavior
regression test: it gives a template, ordinary rendering inputs, and the
expected output, then runs through each public renderer. The next
consolidation group is selected from the existing Chevron-owned tests using
that same boundary. The maintained inventory is `rendering-case-audit.md` in
this change.

It includes value and scope resolution, ordinary and inverted sections, and
source-level whitespace and delimiter behavior. It does not force tests into
the case format merely because they ultimately call `render()`: errors,
diagnostics, readers, filesystem access, cancellation, concurrency,
token-sequence input, and lambda protocol dispatch need observable resource,
lifecycle, or callback assertions beyond a template/output pair.

Do not extend `RenderCase` into a general-purpose test DSL. In particular,
callable and resource factories remain in focused tests unless a later
selection identifies a small, clearly shared source-output contract that can
be represented without obscuring its behavior.

### Use a narrow lambda-case variant for output-only callable behavior

`LambdaRenderCase` extends the ordinary case record only with a
`lambdas_factory`. The factory creates a fresh mapping of declared callables
for every render and is held as a private static method on the case module's
namespace class. This keeps multiple related callables and any shared closure
state contained within the individual case without adding a general setup
hook.

Synchronous lambda cases join both renderers. Async-only lambda cases join
only the async collection, so they run under asyncio and Trio but are never
passed to `render()`. Tests whose contract includes callback arguments,
invocation counts, warnings, exception propagation, or explicit rejection
remain focused tests.

### Model initial delimiters as an ordinary rendering input

`RenderCase` carries an explicit `initial_delimiters` pair. The runners pass
it directly as `def_ldel` and `def_rdel`, allowing a single case to express
initial custom-delimiter rendering through direct interpolation, partials, and
declared lambda expansion. Do not introduce a generic render-options mapping.

### Reuse lambda cases for explicit mapping output behavior

The existing lambda-case variant also represents explicit `lambdas=` mapping
behavior when output alone establishes the contract: supplied sections,
dotted names within partials, iterable and scope precedence, registered
callable truthiness, bound methods, and mapping implementations. Keep legacy
implicit callbacks focused because `LambdaRenderCase` deliberately always
supplies a mapping. Keep tests that observe exact invocation, rejection,
warnings, mapping snapshots, or failures focused.

### Use a filesystem-partial case only for ordinary file lookup

`FilesystemPartialRenderCase` supplies a small relative file tree and an
optional partial extension. Its dedicated runners materialise the tree in
pytest's temporary directory and pass that directory as `partials_path`.
This covers ordinary lookup, nested names, extension selection, mapping
precedence, and missing files through each renderer.

Containment, absolute or traversal paths, symlinks, file ownership,
cancellation, blocking-I/O behavior, and diagnostics remain focused resource
or security tests. The case variant must not attempt to model those concerns.

### Reuse ordinary cases for async-iterable output

`RenderCase.data_factory` already creates fresh consumable values, including
async iterables. Keep ordinary async-iterable section output in the
async-only collection, where it runs under asyncio and Trio. Do not create a
new variant for iterator errors, consumption guarantees, cancellation, or
ownership; those are lifecycle contracts and remain focused tests.

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
  only when each combination protects distinct behavior; use duration data as
  context rather than a replacement for coverage.
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
4. Repeat for only the groups justified by the inventory, using collection and
   duration data to understand each migration's impact.
5. Roll back any group migration by restoring its prior focused tests; no
   production data or runtime migration is involved.
