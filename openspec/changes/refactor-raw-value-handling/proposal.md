# Proposal

## Why

Chevron currently combines name lookup with falsey-value normalisation. This hides a rare but valid falsey callable instance before callable-section dispatch can inspect it, and it couples every caller to lookup's interpolation-oriented coercion rules.

## What Changes

- Separate raw template-name resolution from tag-specific value handling.
- Preserve callable values for callable-capable tag dispatch even when the callable instance is falsey.
- Retain existing rendering behaviour for ordinary falsey values, including `0`, `False`, empty values, custom falsey values, missing names, warnings, and context-stack lookup.
- Add behavioural regression coverage for the special cases whose behaviour must remain stable while lookup is refactored.

## Capabilities

### New Capabilities

- `template-value-resolution`: Resolve template values without prematurely coercing them, then apply tag-specific rendering rules.

### Modified Capabilities

- None.

## Impact

- Affects `src/chevron/renderer.py` lookup and tag-dispatch boundaries.
- Affects renderer regression tests and the callable-mapping test suite.
- Changes the observable behaviour of falsey callable sections: they execute rather than being treated as missing or falsey.
- Does not add dependencies or change the public `render()` signature.
