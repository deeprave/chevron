# Design

## Context

`render()` currently carries a mutable list of template scopes through all recursive rendering paths. Callable section values are invoked solely because they are callable. See [proposal.md](proposal.md) and the `template-lambda-mappings` specification for the required public behaviour.

## Goals / Non-Goals

**Goals:**

- Keep template lookup data separate from callable authorisation state.
- Preserve existing callers that provide legacy section lambdas in `data` or `scopes`.
- Make explicit lambda mappings authoritative for applications that render untrusted templates.
- Carry the same rendering state through every recursive render path.

**Non-Goals:**

- Add Mustache-standard interpolation or one-argument section lambdas.
- Add asynchronous rendering or callable protocol selection.
- Change callable attribute lookup rules established by upstream #118.
- Add dependencies or alter the CLI's data-file format.
- Change the CLI's established default partial directory.

## Decisions

### Use a private composite render context

Introduce a private render-context value that owns the mutable scope stack and lambda-definition state. Recursive rendering receives this context rather than independently reconstructing scope and lambda state.

This centralises the distinction between normal value lookup and callable authorisation while retaining the existing `data` and `scopes` inputs. A public context class is not needed for this change.

**Alternative considered:** Passing `lambdas` separately through every recursive call. This duplicates state propagation and risks omissions in partial or callback rendering.

### Treat an explicit mapping as strict mode

`render(..., lambdas=mapping)` enters explicit mode, including when `mapping` is empty. In this mode, a section callable executes only if `mapping[complete_template_name] is resolved_value`.

`lambdas` omitted or `None` selects compatibility mode. Compatibility mode retains existing legacy section-callable behaviour and must not claim the explicit-mode security guarantee.

**Alternative considered:** Inferring strict mode from whether a mapping is empty. This makes `lambdas={}` ambiguous and prevents callers from explicitly authorising no extensions.

### Normalise public mapping values privately

The public mapping continues to contain plain callables. Internally, each is normalised into a private definition carrying callable identity and the existing legacy section protocol. Issue #4 can extend that definition with explicit protocol and async metadata without changing the render-context boundary.

**Alternative considered:** Requiring public wrapper objects now. That would add API complexity before the additional protocols exist.

### Decide compatibility eligibility at section lookup

Compatibility mode retains Chevron's existing callable-section behaviour for values resolved through mapping and sequence lookup, including the current scope (`.`). The original scope entries continue to determine ordinary template lookup and precedence; no compatibility map is precomputed.

`_RenderContext.allows_callable_traversal` makes the lookup policy explicit:
when no mapping is supplied, dotted lookup may traverse callable values and a
callable section value that normal lookup resolves is eligible. The existing
lookup rule still skips a callable obtained directly by object attribute
access; a callable subsequently obtained from a mapping or sequence remains
compatible with existing renders.

**Alternative considered:** Pre-walking arbitrary object graphs. This risks cycles, side effects, and divergence from Chevron's existing lookup semantics.

### Keep explicit mode strict and diagnosable

When a mapping is supplied, a callable is a leaf for dotted lookup. This keeps
templates from traversing callable internals while still allowing the callable
itself to be resolved for section matching. A callable section absent from the
supplied mapping behaves as missing: a normal section is skipped and an
inverted section renders. With `warn=True`, Chevron writes a diagnostic to
standard error saying that the callable section is not in the supplied lambdas
mapping.

Exact object identity remains the default mapping check. Python bound methods
are the narrow exception: two `MethodType` values match when both `__self__`
and `__func__` are identical. This supports normal instance and class method
use without broad equality-based matching.

This broad leaf rule deliberately includes callable instances and classes, not
only functions and methods. In explicit mode, callers should expose plain data
directly or use an authorised section lambda to provide a small temporary data
scope. Compatibility mode retains historic callable-object traversal.

### Disable implicit filesystem partial loading for the library API

The `render()` library API defaults `partials_path` to `None`. A caller that
needs filesystem partials supplies an explicit trusted directory, including
`partials_path="."` to restore historic library behaviour. This prevents an
untrusted template from turning a missing `partials_dict` entry into a read
relative to the renderer process's working directory.

The command-line interface intentionally retains its `--path` default of
`"."`; it is an explicit filesystem-oriented interface with an existing
compatibility contract.

### Preserve state across recursive renders

Nested sections, iterable items, partials, and the legacy callback's `render(template, data)` path must use the active composite context. The callback adds its temporary data at the front of the scope stack while retaining the enclosing mode and lambda definitions.

**Alternative considered:** Letting each recursive `render()` create a fresh context. That would bypass strict authorisation in nested templates.

### Scope lambda-section token reuse to the render context

Section-lambda callback rendering may reuse the token sequence already parsed
from the callback's reconstructed section text. That cache belongs to the
private render context and is shared only by recursive renders within the same
top-level `render()` call. It is not a process-global template cache and does
not alter the public rendering API or output contract.

**Alternative considered:** Retaining a process-global cache. That keeps
template-controlled section bodies alive indefinitely and lets independent
renders share parser state without a public requirement to do so.

## Risks / Trade-offs

- [A custom mapping or `ChainMap` can have unusual lookup behaviour] → Use
  normal lookup at section resolution rather than pre-walking data, and cover
  compatibility paths in tests.
- [A shadowed callable could be authorised by name alone] → Compare object identity after normal scope resolution.
- [A recursive path could lose strict mode] → Route every recursive render call through the composite context and add focused tests for partials and legacy callbacks.
- [Compatibility extraction could be mistaken for the security boundary] → Document that applications rendering untrusted templates must provide an explicit mapping, including `{}` when no lambdas are allowed.
- [Implicit partial lookup could disclose process-relative files] → Disable it
  by default for `render()` and require an explicit trusted partial directory.

## Migration Plan

1. Add the optional public `lambdas` argument and internal context without changing calls that omit it.
2. Add strict explicit-mapping checks and regression coverage for legacy section lambdas.
3. Document explicit mode for untrusted-template renderers.
4. Retain compatibility mode until a separately approved major-version policy changes it.
