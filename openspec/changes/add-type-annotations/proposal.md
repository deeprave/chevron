# Proposal

## Why

Chevron now supports Python 3.11 and later, but its public entry points and
much of its implementation remain unannotated. Clear annotations and routine
checking of both source and tests will make the synchronous and asynchronous
contracts easier to maintain without pretending that dynamically resolved
Mustache data is statically knowable.

## What Changes

- Annotate Chevron's supported public functions, decorators, exceptions, and
  CLI-facing helpers, allowing `Any` at genuinely dynamic template-data
  boundaries until a narrower contract is established.
- Introduce shared aliases and protocols for stable concepts such as render
  inputs, token streams, template readers, lambda callbacks, logging, and
  render scopes; use them where they improve the internal renderer contract.
- Add practical annotations to remaining source and test code, including async
  fixtures and test doubles, without enabling a strict type-checking mode or
  redesigning dynamic Mustache resolution for the type checker.
- Expand the existing Ty quality check from `src/` to `src/` and `tests/`, and
  make passing that non-strict check part of routine validation.
- Do not add a `py.typed` marker or change runtime rendering behaviour.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is a source-maintenance and quality-validation change with no
runtime contract change.

## Impact

- Affected code: public package exports, renderer modules, tokenizer, CLI
  helpers, tests, and type-checker quality configuration.
- Public API: runtime behaviour and supported call signatures remain unchanged;
  annotations are available to source readers but are not published as a typed
  distribution marker.
- Dependencies: no new runtime dependency; reuse the existing development Ty
  tool.
