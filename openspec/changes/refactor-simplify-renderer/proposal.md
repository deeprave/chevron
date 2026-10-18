# Proposal

## Why

Renderer complexity has grown through independent additions for explicit lambda mappings, three callable protocols, recursive token reuse, and source-preserving tokenisation. Refactor these responsibilities before implementing `update-to-latest-mustache`, so inheritance and dynamic partials can build on one coherent rendering engine.

## What Changes

- Keep the public `render()` signature and decorator APIs while moving execution into a composed `ChevronRender` class with bound recursive operations. Use no leading underscore on the class, but do not re-export it from `chevron/__init__.py`; `chevron.render()` remains the primary entry point.
- Select a callable-source policy once per public render: explicit mapping or permissive template-data lookup.
- Separate that policy from interpolation, standard-section, and compatibility-section invocation handlers.
- Consolidate section-body collection, recursive configuration propagation, and scope restoration.
- Move template reading into the renderer and make the tokenizer text-only, removing its file-like input handling without a compatibility wrapper.
- Separate render configuration, shared invocation state, and local rendering frames; remove unreachable Python 2 branches on the supported Python 3.11+ platform.
- Preserve observable output, lookup exceptions, warnings, callback behaviour, token inputs, and partial restrictions; add focused behavioural coverage where extraction exposes missing regression coverage.

## Capabilities

### New Capabilities

None. This is an internal refactor with `skip_specs: true`.

### Modified Capabilities

None. Existing `template-lambda-mappings` and `template-value-resolution` requirements remain the contract. The dotted-name correction and new Mustache modules remain in `update-to-latest-mustache`, which follows this refactor.

## Impact

Primary changes will affect `src/chevron/renderer.py`, small private modules where separation helps, relevant behavioural tests, and benchmark scenarios. Existing public imports and runtime dependencies remain unchanged. `ChevronRender` has a public-style name for potential direct use, but is not advertised or re-exported at package level. No async rendering API or new template syntax is introduced.
