# Design

## Context

`_get_key()` currently walks template scopes and then applies falsey-value coercion before returning. Variable tags, unescaped tags, normal sections, inverted sections, and callable sections all consume that coerced result. See `proposal.md` for the motivation and `specs/template-value-resolution/spec.md` for the behavioural contract.

## Goals / Non-Goals

**Goals:**

- Separate name resolution from tag-specific handling without changing public API signatures.
- Ensure callable-section dispatch receives the resolved callable object even when the object evaluates as falsey.
- Preserve all established ordinary-value behaviour with explicit regression coverage.

**Non-Goals:**

- Adding new callable forms, changing lambda precedence, or completing Mustache lambda conformance.
- Replacing Chevron's context-stack lookup rules or changing callable traversal policy.
- Altering the `lambdas=` compatibility model introduced by `registered-template-lambdas`.

## Decisions

### Return a raw value or private missing sentinel from lookup

Lookup will resolve a name without applying generic falsey coercion. A private sentinel will distinguish an unresolved name from values such as `None`, an empty mapping, or an empty sequence. This lets callers retain their own semantics while preserving warning behaviour at the lookup boundary.

An alternative is a `preserve_callable` flag on the existing lookup function. That is smaller, but keeps tag-specific behaviour hidden inside lookup and creates another special-case path as future callable forms are added.

### Normalise values at tag-dispatch boundaries

Interpolation and unescaped interpolation will apply the existing empty-value and string-conversion behaviour after lookup. Normal and inverted sections will apply their existing truthiness behaviour after lookup. Callable-capable section dispatch will inspect the raw value first, then apply existing legacy or explicit lambda rules.

An alternative is to remove normalisation entirely. That would expose Python representations such as `None` and empty containers in interpolations, breaking established Chevron behaviour.

### Preserve compatibility through behavioural tests

Tests will cover missing names and diagnostics, `0`, `False`, empty strings and collections, custom falsey values, `_CHEVRON_return_scope_when_falsy`, nested scopes, normal sections, inverted sections, escaped and unescaped interpolation, and both legacy and explicit falsey callable instances. Tests will assert output and warnings rather than private lookup helpers.

## Risks / Trade-offs

- [Normalisation behaviour moves across callers] → Characterise current output and warning behaviour before and after the refactor, then run the full test suite.
- [Missing values become confused with resolved falsey values] → Use a private sentinel and cover missing interpolation and section cases explicitly.
- [Callable dispatch changes legacy behaviour] → Limit intentional change to falsey callable sections and test legacy and explicit modes separately.
- [Existing lambda conformance failures obscure regressions] → Keep the known issue #4 failures visible, compare the remaining suite against its current baseline, and add focused regressions for this change.

## Migration Plan

No caller migration is required. The library continues to accept the same render inputs; falsey callable sections begin executing as intended. Revert the implementation commit if an uncharacterised compatibility regression is found.
