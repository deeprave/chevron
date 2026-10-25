# Proposal

## Why

Chevron's test suite has grown organically around individual regressions and
separate synchronous and asynchronous implementations. Before the next release,
it needs a measured refactor that shortens feedback where evidence supports it,
removes redundancy, and makes behavioral coverage easier to understand and
maintain without weakening the release gate.

## What Changes

- Audit collection and execution cost, duplicated coverage, implementation-coupled
  tests, and natural behavior groupings before moving tests.
- Organise Chevron-owned rendering tests by observable behavior, including value
  resolution, sections, partials and inheritance, whitespace and standalone
  handling, lambda protocols, filesystem lookup, and async-specific behavior.
- Introduce typed, Python-declared behavioral case collections for template
  rendering scenarios. A named case supplies template input, data, partials,
  and expected output; synchronous and asynchronous public APIs run the same
  case set, with async retaining asyncio and Trio coverage.
- Retain small focused tests only where a distinct supported public contract
  requires them, such as token-sequence template input; remove tests that
  assert private renderer structure rather than observable behavior.
- Preserve the vendored Mustache specification JSON modules as immutable,
  independently marked conformance evidence. Chevron-owned case collections
  must not be presented as upstream conformance fixtures.
- Prefer clear parameterisation over repeated near-identical tests while
  avoiding broad Cartesian products that obscure failures or increase runtime.

## Capabilities

### New Capabilities

None. This is a test-suite refactor with no new production behavior.

### Modified Capabilities

None. Production requirements and public behavior do not change.

## Impact

- Affects test layout, shared test support, pytest parameterisation, and
  developer feedback workflows under `tests/`.
- May simplify test-only configuration or markers where the audit shows it is
  needed.
- Does not alter production modules, public APIs, vendored Mustache fixtures,
  dependency requirements, or release behavior.
