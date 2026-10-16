# Design

## Context

`render()` carries a mutable list of template scopes through recursive rendering. Legacy Chevron invokes a callable section value reached through those scopes. Explicit mappings introduce a separate, trusted callable namespace for applications rendering untrusted templates. See `proposal.md` and the `template-lambda-mappings` specification for the required public behaviour.

## Goals / Non-Goals

**Goals:**

- Keep ordinary template data separate from configured executable lambdas.
- Resolve configured lambda names before template data in explicit mode.
- Reject callable template-data values in explicit mode while retaining legacy compatibility when no mapping is supplied.
- Carry the same rendering state through every recursive render path.

**Non-Goals:**

- Add Mustache-standard interpolation or one-argument section lambdas.
- Add asynchronous rendering or callable protocol selection.
- Change callable attribute lookup rules established by upstream #118.
- Add dependencies or alter the CLI's data-file format.
- Change the CLI's established default partial directory.

## Decisions

### Use a private composite render context

Introduce a private render context that owns the mutable scope stack, configured lambda mapping, and render-scoped token cache. Recursive rendering receives this context rather than independently reconstructing scope and lambda state.

**Alternative considered:** Passing `lambdas` separately through every recursive call. This duplicates state propagation and risks omissions in partial or callback rendering.

### Resolve explicit lambdas before template data

`render(..., lambdas=mapping)` enters explicit mode, including when `mapping` is empty. For a callable-capable section, the complete template name is looked up in the mapping first. A mapped value executes without querying template data, so configured lambdas intentionally shadow same-named template values.

When the mapping lacks a name, ordinary template data supplies non-callable values. A callable obtained from data is rejected, rendered as empty, and produces a warning when requested. This makes the mapping the sole executable-code source in explicit mode and removes identity matching and bound-method special cases.

`lambdas` omitted or `None` selects compatibility mode. Compatibility mode retains existing legacy section-callable behaviour and makes no explicit-mode security guarantee.

### Preserve ordinary lookup behaviour and callable opacity

In explicit mode, template data remains available for ordinary values. Callable data is rejected rather than rendered, invoked, or traversed; dotted traversal through callable data remains unavailable. Compatibility mode retains historic callable-object traversal and legacy section execution.

### Disable implicit filesystem partial loading for the library API

The `render()` library API defaults `partials_path` to `None`. A caller that needs filesystem partials supplies an explicit trusted directory, including `partials_path="."` to restore historic library behaviour. The command-line interface retains its `--path` default of `"."`.

### Preserve state across recursive renders

Nested sections, iterable items, partials, and the legacy callback's `render(template, data)` path use the active composite context. The callback adds temporary data at the front of the scope stack while retaining the enclosing explicit or compatibility mode and configured mapping.

### Scope lambda-section token reuse to the render context

Section-lambda callback rendering may reuse the token sequence already parsed from the callback's reconstructed section text. That cache belongs to the private render context and is shared only by recursive renders within the same top-level `render()` call.

## Risks / Trade-offs

- [A configured lambda shadows template data] → Document this deliberate precedence and cover same-name template values in tests.
- [Callable data is no longer silently rendered in explicit mode] → Reject it predictably as empty with an optional warning; callers that require legacy execution omit `lambdas`.
- [A recursive path could lose explicit mode] → Route every recursive render call through the composite context and cover partials and legacy callbacks.
- [Existing lambda conformance failures obscure regressions] → Keep issue #4 failures visible and compare remaining full-suite output with the current baseline.
- [Implicit partial lookup could disclose process-relative files] → Disable it by default for `render()` and require an explicit trusted partial directory.

## Migration Plan

1. Callers requiring executable template extensions pass them only through `lambdas`.
2. Callers relying on callable values in template data omit `lambdas` to retain legacy behaviour.
3. Explicit-mode callers remove callable values from template data or accept their intentional empty rendering.
