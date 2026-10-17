# Proposal

## Why

The pinned Mustache lambda fixtures expose nine conformance failures because Chevron stringifies interpolation callables and supports only its legacy two-argument section-lambda extension. Chevron needs the standard lambda behaviours while preserving existing consumer callbacks unchanged.

## What Changes

- Invoke zero-argument interpolation lambdas for escaped and unescaped interpolation tags, then render their returned text as Mustache source before applying the tag's escaping rule.
- Invoke standard one-argument section lambdas with unrendered section source and recursively render their returned text with the active context and delimiters.
- Preserve two-argument legacy section lambdas, including their temporary-data rendering callback, as the backwards-compatible section behaviour.
- Define lambda protocol metadata for explicitly registered lambdas through `@chevron.func`, `@chevron.section`, and `@chevron.compat`, and retain the existing explicit-mapping identity and callable-data restrictions across recursive rendering and partials.
- Require protocol decorators for new zero-argument interpolation and one-argument standard section lambdas in both explicit and compatibility modes. Undecorated section callables retain Chevron's two-argument compatibility protocol.
- Isolate tokenisation state, delimiter defaults, and legacy token-cache replay per render so nested rendering is re-entrant and independent renders do not share mutable state.
- Extend the conformance and regression suite to cover escaped and unescaped interpolation, expansion, alternate delimiters, repeated calls, standard sections, and legacy callback compatibility.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `template-lambda-mappings`: Extend callable resolution and execution rules with Mustache-standard interpolation and section-lambda protocols while preserving explicit mapping hardening and legacy section behaviour.

## Impact

The renderer, public lambda documentation, the pinned Mustache fixture harness, and lambda regression tests will change. `render()` retains its existing signature; existing two-argument section lambdas remain supported. The change adds observable invocation semantics for decorated zero-argument interpolation callables and decorated standard one-argument section lambdas in compatibility and explicit modes.
