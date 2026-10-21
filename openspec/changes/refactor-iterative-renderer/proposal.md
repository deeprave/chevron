# Proposal

## Why

Both renderers currently call themselves for partials, iterable sections, and
lambda-produced templates. A finite but deeply nested template can therefore
fail because of Python's call-stack limit even though it has valid Chevron
semantics. Now that render context is represented by immutable frames, the
engines can make nested work explicit instead.

## What Changes

- Replace recursive nested-render dispatch in the synchronous and asynchronous
  renderers with explicit iterative render state.
- Keep active scope, delimiter, padding, output, and continuation state in
  private frames so nested partials, sections, and lambda results resume their
  parent render correctly.
- Preserve existing public APIs and observable Mustache, compatibility-lambda,
  partial, delimiter, diagnostic, and cancellation behaviour.
- Add regression coverage for finite deep expansion and compare equivalent
  synchronous and asynchronous rendering workloads while developing the
  refactor.

## Capabilities

### New Capabilities

- `stack-safe-template-expansion`: Render finite nested template expansion
  without relying on Python call-stack depth.

### Modified Capabilities

- None.

## Impact

The synchronous renderer, AnyIO-backed asynchronous renderer, and their
rendering tests will change internally. No public API, dependency, or template
syntax change is introduced.
