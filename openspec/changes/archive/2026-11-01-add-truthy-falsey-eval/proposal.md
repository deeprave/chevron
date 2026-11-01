# Proposal

## Why

Mustache sections combine a truthiness check with context selection or repeated rendering. Template authors sometimes need only the first operation: conditionally include a larger fragment without changing the active context or traversing a collection. `{{?name}}` makes that intent explicit and lets a generator be checked without caller-provided duplicate boolean data.

## What Changes

- Add the non-standard `{{?name}}…{{/name}}` conditional-section tag, which renders its body once only when `name` resolves to a truthy value.
- Add `Extension.CONDITIONAL_SECTIONS` as an independent, process-wide opt-in; enabling it must not require `Extension.ENHANCED_ITERATORS`.
- Preserve the active render context inside a conditional section: the resolved value is not pushed as a scope, iterated, interpolated, or invoked as a lambda.
- Evaluate collections using the enhanced-iterator truthiness policy: ordinary and sized values use their own truthiness, while unsized synchronous or asynchronous iterator sources are observed once when needed and preserve a probed item for later ordinary section rendering.
- Reserve `?` as conditional-section syntax only when the extension is enabled. When disabled it remains part of an ordinary variable name; an apparent paired conditional section logs a configuration warning before its ordinary structural template error.

## Capabilities

### New Capabilities

- `conditional-section-evaluation`: opt-in conditional template sections that select their bodies by value truthiness without changing context or repeating content.

### Modified Capabilities

- `extension-configuration`: add the independent conditional-section extension to the global extension mask.
- `template-value-resolution`: define synchronous conditional lookup and iterator-observation behaviour.
- `async-template-rendering`: define conditional handling for asynchronous iterables within `async_render()`.

## Impact

- Affects tokenizer tag recognition, synchronous and asynchronous section dispatch, private iterator state, extension configuration, behavioural fixtures, and language/API documentation.
- Adds no render-call options or dependencies.
- Introduces an opt-in template-language extension; standard Mustache templates and applications that leave extensions disabled retain their current behaviour.
