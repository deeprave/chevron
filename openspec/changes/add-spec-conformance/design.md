# Design

## Context

See [proposal.md](proposal.md) for the motivation and the accompanying `template-lambda-mappings` delta for the behavioural contract. The renderer currently recognises callable values only in section dispatch, where it unconditionally calls them with `(raw_text, render)`. Interpolation tags normalise and stringify every resolved value. The vendored fixture harness deliberately materialises its callable examples as ordinary template-data values, so it exercises compatibility mode rather than `lambdas=`.

`_RenderContext` already carries rendering scopes, the optional explicit lambda mapping, and the token cache through recursive renders. Explicit mappings are an identity-based source of trusted executable values: they are checked before template data and template-data callables are rejected.

## Goals / Non-Goals

**Goals:**

- Implement the pinned Mustache lambda fixtures without weakening explicit-mapping callable isolation.
- Make the standard and Chevron-specific section protocols unambiguous for new explicit registrations.
- Keep current two-argument section callbacks working without source changes.
- Preserve lambda behaviour through recursive renders, partials, and the existing render-context restoration rules.

**Non-Goals:**

- Redesigning rendering around a public renderer class or changing the `render()` signature.
- Adding asynchronous rendering, changing callable warning transport, or changing filesystem partial handling.
- Updating the vendored Mustache fixture revision beyond the currently pinned known-working revision.

## Decisions

### Represent declared section protocols with a callable wrapper

Introduce an internal `_LambdaDefinition` that retains the wrapped callable and a section protocol marker. Provide a public decorator for the standard one-argument section protocol; its result is accepted wherever a callable is accepted and supplies the marker to the render context. An undecorated callable in an explicit mapping retains Chevron's existing two-argument legacy section interpretation. A separate legacy decorator is unnecessary because the legacy form remains the explicit default.

This makes the choice visible where the function is declared, rather than inferring it at invocation time. It also gives later async work a single place to add protocol metadata. The alternative—always inspecting signatures—would make callable implementation details an execution contract and behaves poorly for wrappers, partials, and non-introspectable callables. Catching `TypeError` after invoking a callable is rejected because an application-raised `TypeError` is indistinguishable from an arity mismatch.

### Choose protocol from tag type before calling a registered lambda

For an interpolation tag, an explicit callable is invoked with zero arguments. Its return value is recursively rendered with the same context but Mustache's default `{{` and `}}` delimiters, then escaped only for the original escaped interpolation tag. A callable that is explicitly marked as a section-only standard lambda is not invoked through an interpolation tag.

For a section tag, a wrapper marked as standard receives the unrendered section source and its return value is recursively rendered using the delimiters active at the section. An unannotated explicit callable remains a legacy two-argument section callback and receives the current temporary-data render helper. This preserves Chevron’s established API while allowing new registrations to opt into Mustache’s protocol deliberately.

The alternative of treating an undecorated explicit one-argument callable as standard would be convenient but would make migration ambiguous and could silently alter a legacy callback's invocation.

### Use signature inspection only for compatibility-mode fixture bridging

Compatibility mode has no protocol metadata because callables originate in ordinary template scopes. Use `inspect.signature` to recognise zero-argument values for interpolation and one-argument values for standard sections. Treat values which cannot be safely classified as their existing behaviour: interpolation does not invoke them, while sections retain the two-argument legacy callback path.

Inspection is deliberately confined to compatibility ergonomics. It is neither an authorisation check nor a way to discover executable values in explicit mode; explicit execution continues to require lookup in the supplied `lambdas` mapping. This avoids a runtime-`TypeError` fallback while allowing the pinned fixture data to stay unchanged.

### Keep recursive rendering context-specific delimiter behaviour

Lambda return values reuse the active `_RenderContext`, so scopes, explicit mappings, partial configuration, warnings, and the token cache remain available. Interpolation return values reset delimiters to Mustache defaults; standard section return values preserve the section's active delimiters. Legacy callbacks keep the current helper semantics, including optional temporary scope data.

This distinction is required by the pinned fixture suite. Reusing one delimiter policy for both protocols would fail alternate-delimiter cases.

### Test behaviour at both the fixture and public API boundaries

Keep the vendored lambda fixture cases as the conformance proof. Add focused pytest cases for explicit registrations, shadowing, rejected callable template data, decorator protocol selection, repeated invocation, delimiter behaviour, and preservation of legacy callback rendering. Tests should exercise `chevron.render()` rather than internal helpers except where a narrow regression demands it.

## Risks / Trade-offs

- [Signature inspection cannot classify every Python callable] → Preserve prior compatibility behaviour for uninspectable values and require an explicit protocol decorator for newly registered standard section lambdas.
- [A decorator introduces a small public API surface] → Export and document only the standard-section marker; retain unannotated legacy callbacks as the default.
- [Recursive return-value rendering can expose delimiter mistakes] → Cover interpolation-default and section-active delimiter cases directly with the pinned fixtures and focused regressions.
- [Changes near callable dispatch can weaken explicit-mode hardening] → Retain mapping-first lookup and template-data callable rejection in every nested render path, with regression tests for shadowing and recursion.

## Migration Plan

No data migration is required. Existing callers can retain two-argument section callbacks. Callers adopting a Mustache-standard section lambda register it with the standard-section decorator in `lambdas=`. Compatibility-mode templates gain support for the pinned zero- and one-argument callable forms without requiring fixture or application rewrites. If a regression is discovered, revert the change as a single renderer and public-export release change; the previous legacy protocol remains independently available.
