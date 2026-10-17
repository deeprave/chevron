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

Introduce an internal `_LambdaDefinition` that retains the wrapped callable and a protocol marker. Provide `@chevron.func` for the zero-argument interpolation protocol, `@chevron.section` for the Mustache-standard one-argument section protocol, and `@chevron.compat` for Chevron's legacy two-argument section protocol. Each decorator result is accepted wherever a callable is accepted and supplies the marker to the render context. An undecorated callable in an explicit mapping retains Chevron's existing two-argument legacy section interpretation.

This makes the choice visible where the function is declared, rather than inferring it at invocation time. It also gives later async work a single place to add protocol metadata. The alternative—always inspecting signatures—would make callable implementation details an execution contract and behaves poorly for wrappers, partials, and non-introspectable callables. Catching `TypeError` after invoking a callable is rejected because an application-raised `TypeError` is indistinguishable from an arity mismatch.

### Choose protocol from tag type before calling a registered lambda

For an interpolation tag, an explicit callable is invoked with zero arguments. Its return value is recursively rendered with the same context but Mustache's default `{{` and `}}` delimiters, then escaped only for the original escaped interpolation tag. A callable that is explicitly marked as a section-only standard lambda is not invoked through an interpolation tag.

For a section tag, a wrapper marked as standard receives the literal, unprocessed source enclosed by its section tags, including comments and whitespace removed from rendered output by standalone processing. Its return value is recursively rendered using the delimiters active at the section. An unannotated explicit callable remains a legacy two-argument section callback and receives the current temporary-data render helper. This preserves Chevron’s established API while allowing new registrations to opt into Mustache’s protocol deliberately.

The alternative of treating an undecorated explicit one-argument callable as standard would be convenient but would make migration ambiguous and could silently alter a legacy callback's invocation.

### Make protocol selection declarative in every mode

Do not inspect callable signatures or use a `TypeError` fallback to select a protocol. `@chevron.func` and `@chevron.section` are required for the new zero- and one-argument protocols whether their values are supplied through `lambdas=` or ordinary compatibility-mode template data. An undecorated section callable retains Chevron's two-argument compatibility protocol; undecorated interpolation callables retain their historic stringification behaviour. The pinned fixture harness adapts its reviewed fixture callables into the declared protocols.

This keeps invocation a developer-declared contract, avoids treating application-raised `TypeError` as dispatch metadata, and preserves legacy applications without guessing their callable shape.

### Keep recursive rendering context-specific delimiter behaviour

Lambda return values reuse the active `_RenderContext`, so scopes, explicit mappings, partial configuration, warnings, and the token cache remain available. Interpolation return values reset to the immutable render defaults configured by `def_ldel` and `def_rdel`; standard section return values start with the delimiter pair active at the section opening. A legacy callback helper always starts with the immutable render defaults, including optional temporary scope data. Partials likewise start with the immutable render defaults rather than the delimiter pair active at their call site.

This distinction is required by the pinned fixture suite. Delimiter state inside a skipped or collected section still changes the outer parser state lexically, without changing the immutable per-render defaults.

### Keep tokenisation state in the render context

Replace tokenizer module globals with a per-tokenisation state object. `_RenderContext` owns a stack of these state objects for the lifetime of nested tokenisation; each tokenizer receives and directly updates its own state. The render context pushes when iteration starts and pops in a `finally` block. This preserves syntax line diagnostics across nested render calls without shared mutable module state.

The token cache remains solely for Chevron's legacy callback replay. Standard function and section lambda return values always tokenise their source independently, preventing cache state or delimiter policy from leaking between protocols.

### Test behaviour at both the fixture and public API boundaries

Keep the vendored lambda fixture cases as the conformance proof. Add focused pytest cases for explicit registrations, shadowing, rejected callable template data, decorator protocol selection, repeated invocation, delimiter behaviour, and preservation of legacy callback rendering. Tests should exercise `chevron.render()` rather than internal helpers except where a narrow regression demands it.

## Risks / Trade-offs

- [New protocols require explicit declaration] → Export and document the decorators, retain undecorated two-argument section callbacks, and adapt the reviewed fixture harness rather than guessing callable signatures.
- [Decorators introduce a small public API surface] → Export and document the three protocol markers; retain unannotated legacy callbacks as the default.
- [Recursive return-value rendering can expose delimiter mistakes] → Cover interpolation-default and section-active delimiter cases directly with the pinned fixtures and focused regressions.
- [Changes near callable dispatch can weaken explicit-mode hardening] → Retain mapping-first lookup and template-data callable rejection in every nested render path, with regression tests for shadowing and recursion.

## Migration Plan

No data migration is required. Existing callers can retain two-argument section callbacks. New registrations use `@chevron.func`, `@chevron.section`, or `@chevron.compat` to make their protocol visible; callers are encouraged to annotate legacy callbacks with `@chevron.compat`, although unannotated callbacks retain that default. Compatibility-mode templates gain the new protocols when applications opt in with decorators. If a regression is discovered, revert the change as a single renderer and public-export release change; the previous legacy protocol remains independently available.
