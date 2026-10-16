# Proposal

## Why

Chevron currently treats any callable reached through template data as executable in a section. Applications that render untrusted templates need an explicit callable source without breaking existing legacy two-argument section lambdas.

## What Changes

- Add an optional per-render `lambdas` mapping, separate from template data and scopes.
- In explicit-mapping mode, resolve configured lambda names before template data and execute those configured callables.
- Reject callable values found in template data during explicit-mode rendering; they render as empty and can emit a warning.
- Treat an explicit empty mapping as strict mode with no executable lambdas.
- Preserve existing callers that omit `lambdas` by retaining legacy section-lambda execution through mapping and sequence paths.
- In explicit mode, treat template-data callable values as rejected lookup
  leaves, with an optional warning.
- Make explicit mode's broad callable opacity an intentional, documented
  contract; callers expose plain data through authorised section lambdas.
- Change the library `render()` default from `partials_path="."` to
  `partials_path=None`, so filesystem partial loading is an explicit opt-in.
  Preserve the CLI `--path` default of `"."`.
- Carry scope and lambda-definition state together through nested sections, iterable items, partials, and legacy callback rendering.
- Document the explicit-mapping security boundary and compatibility behaviour.
- Defer Mustache-standard interpolation and one-argument section-lambda protocols to #4.

## Capabilities

### New Capabilities

- `template-lambda-mappings`: Supply template lambda execution with a per-render mapping while retaining legacy section-lambda compatibility when no mapping is supplied.

### Modified Capabilities

- None.

## Impact

- `src/chevron/renderer.py`: optional `lambdas` argument, composite render context, section-callable dispatch, and safe library partial default.
- Public Python API: additive `lambdas` keyword on `chevron.render()` and a breaking default for `partials_path` (`None` rather than `"."`).
- Documentation and pytest-style behavioural coverage.
- No runtime dependencies or changes to the CLI data-file contract. The
  `uv_build` compatibility range is updated so the current build tooling can
  build the modernised package.
