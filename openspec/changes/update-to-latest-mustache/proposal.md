# Proposal

## Why

Chevron vendors a reviewed copy of the Mustache specification fixtures so that conformance testing is deterministic and does not depend on a Git submodule. The current copy is pinned to `934db98`, while upstream `mustache/spec` now contains additional core cases and optional dynamic-name and inheritance modules at `e8ec001`.

Updating the vendor set makes the current standard's expectations visible and preserves a reproducible basis for bringing Chevron into full conformance with every module it vendors.

## What Changes

- Replace the vendored JSON fixtures with the complete current upstream JSON set pinned to `e8ec001db7f594521e773c34866aca2b5d6b0037`, retaining Chevron's attribution README.
- Mark every synchronous and asynchronous upstream-fixture test as `conformance`, so the full compatibility suite can run separately from other tests.
- Refresh the fixtures and measure a per-module baseline before renderer implementation begins; use that map to identify the requirements the iterative-renderer refactor must support.
- Use the compatibility map to distinguish isolated conformance corrections from requirements that need the iterative-renderer state model.
- Implement isolated shared semantic corrections while retaining the iterative refactor as the prerequisite for state-machine-dependent extensions.
- Correct dotted-name resolution so that, after the initial name resolves in a scope, later dotted segments resolve only from that value rather than falling back to an outer scope.
- Implement the upstream dynamic-name and inheritance modules, including their partial lookup, block override, scope, recursion, standalone whitespace, and indentation behaviours.
- Document the pinned upstream revision and implemented Mustache module support.

## Capabilities

### New Capabilities

- `mustache-spec-conformance`: Vendored upstream conformance fixtures, their revision provenance, and the supported-module execution contract.
- `mustache-template-extensions`: Dynamic partial-name resolution and parent/block inheritance rendering.

### Modified Capabilities

- `template-value-resolution`: Dotted-name resolution must retain the scope established by its first component.

## Impact

Affected areas include `tests/fixtures/mustache-spec/`, `tests/test_specifications.py`, renderer name resolution, and the fixture attribution documentation. There is no public API addition. The core dotted-name correction changes an incorrect outer-scope fallback to match the Mustache specification.

## Delivery Approach

This began as an experimental compatibility-mapping change. The initial stage
pinned the upstream head, refreshed the vendor files, and captured the complete
`conformance`-marked baseline before implementation began.

The reviewed fixture snapshot is now committed on the draft evaluation branch.
The compatibility map is used to implement small, shared semantic corrections
that do not require new rendering control flow, beginning with dotted-name
context precedence and dynamic partial names. Inheritance remains deferred to
the iterative-renderer state-machine work because its block-override state
requires nested expansion control flow.
