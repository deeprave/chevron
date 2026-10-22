# Design

## Context

See [proposal.md](proposal.md) for motivation. Chevron already requires Python
3.11 and runs `ty check src/`, but its public entry points and many internal
helpers are unannotated. A current baseline `ty check src tests` reports test
module-resolution failures and 21 diagnostics, principally missing callback
types, deliberately non-returning async test doubles, and fixture data that is
still typed as `object`.

The renderer intentionally accepts dynamic Mustache data: arbitrary scopes,
mapping-like values, object attributes, callables, readers, and iterables. Its
types must preserve that contract rather than invent a closed template-data
model.

## Goals / Non-Goals

**Goals:**

- Give every supported public entry point an explicit annotation and make
  stable renderer relationships legible to Ty.
- Narrow internal types where the runtime contract is stable, particularly
  scope containers, token data, configuration, readers, lambda protocols, and
  callback rendering functions.
- Type and check tests with the existing non-strict Ty defaults.

**Non-Goals:**

- Publishing a PEP 561 `py.typed` marker or promising a consumer-facing typed
  distribution.
- Removing every `Any`, treating arbitrary template values as a closed schema,
  or applying strict-equivalent annotation checks to the test suite.
- Changing renderer behaviour, accepted inputs, callback dispatch, or the
  public runtime signature in order to make annotations narrower.

## Decisions

### Annotate the public surface before refining internals

Annotate package exports (`render`, `async_render`, the lambda decorators,
`main`, `cli_main`, and public exceptions) first. Keep the established
parameter order, default values, and keyword-only logging arguments exactly as
they are. Use permissive types such as `Any` or `object` initially where the
API deliberately accepts unconstrained template data.

This delivers useful source documentation without the false claim implied by a
packaged typing marker. It also gives internal work a stable target. Deferring
public annotations until every helper is exact would provide neither benefit.

### Model stable shapes; preserve a dynamic data boundary

Add local aliases and small `Protocol` definitions only for repeated stable
shapes: token tuples/streams, readable template objects, async readable
objects, rendering callbacks, lambda registries, logger inputs, and scope
sequences. Define each alias in the module that owns the corresponding runtime
abstraction; do not add a shared types module. Use `collections.abc` generic
interfaces and modern Python 3.11 syntax. Use `TYPE_CHECKING` only when an
annotation-only import would create a runtime dependency or import cycle.

For render contexts, distinguish the caller-facing `ScopeSequence` from the
immutable `NormalisedScopes` snapshot used internally. `ScopeSequence` remains
a sequence of dynamic scope values; individual scopes may themselves be
sequences, mappings, or attribute-bearing objects. `NormalisedScopes` is the
tuple created after the existing outer-container validation and empty-scope
normalisation. Do not introduce a wrapper collection: frame construction
already gives empty input a predictable empty-mapping root and existing lookup
behaviour handles individual sequence bounds.

Define `TemplateData` as a semantic `Any` alias for template values and dynamic
lookup results. This preserves the renderer's permissive data boundary while
making that boundary visible in annotations. Use `object` when a value is only
passed or compared, and narrow it only after the implementation has established
a concrete type. Do not add an abstraction solely to avoid an `Any`, and do not
attempt to statically represent every legacy lambda calling convention.

### Enforce strict-equivalent source checking and pragmatic test checking

Apply Ty's documented strict-equivalent rules to `src/` only:
`dynamic-function-decorator-return`, `missing-type-argument`,
`possibly-unresolved-reference`, and `unsound-return-statement`. Run Ruff's
`ANN` and `PYI` rules in preview mode against `src/` as a separate quality
command. This makes missing source annotations fail validation without imposing
the same standard on test fixtures.

Check `tests/` with Ty's default diagnostics and an explicit additional
test-module search path matching pytest's `pythonpath` setup. Fix diagnostics
by annotating fixtures, callback parameters, and test doubles truthfully. For
tests that intentionally exercise an invalid public call, use the smallest
local suppression or call shape that preserves the runtime assertion; do not
weaken the production signature.

### Verify annotations through existing quality tooling

Retain the existing Ty development dependency and run one Ty command over
`src/` and `tests/`, with source-only strict-equivalent rules supplied by the
`src/` override. Add source-only Ruff annotation checks as the separate quality
command. Tests continue to validate runtime semantics separately; typing tests
focus on the maintained checker baseline and representative public signature
use.

## Risks / Trade-offs

- Dynamic renderer semantics can tempt over-specific annotations → retain
  `Any` at explicit lookup and callable-result boundaries, with explanatory
  aliases where helpful.
- Test checking can expose intentionally invalid test calls → use narrow local
  suppressions only at those assertions, never broad file-level ignores.
- Source strict-equivalent checks may reveal limitations in Ty's evolving
  inference → resolve concrete diagnostics and use a narrow local suppression
  only when necessary to preserve correct runtime behaviour.
- Public annotations may be mistaken for a packaged typing guarantee → do not
  add `py.typed` and state that boundary in developer documentation if needed.

## Migration Plan

1. Annotate the public surface and implementation, then make `src/` pass the
   strict-equivalent Ty and source-only Ruff annotation checks.
2. Annotate and correct the test suite until its pragmatic Ty check passes.
3. Add the source and test commands to the quality workflow, then run tests,
   formatting, and the normal quality suite.
4. If an annotation proves incompatible with a supported dynamic input, widen
   that annotation without changing runtime behaviour; reverting is a
   source-only change.
