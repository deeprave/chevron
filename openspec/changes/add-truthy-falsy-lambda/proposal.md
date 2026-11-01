# Proposal

Issue: [#39](https://github.com/deeprave/chevron/issues/39)

## Why

Conditional sections can test a callable object but intentionally do not invoke it, so templates cannot use application logic to decide whether a context-preserving conditional body should render. An explicit invoked form can provide that decision without adding another decorator or changing ordinary Mustache section-lambda semantics.

## What Changes

- Add `{{?*name}}…{{/name}}` as an opt-in conditional-section form that invokes an explicitly declared `@chevron.func` callback and tests the callback result with ordinary Python truthiness.
- Preserve the active template context and render the body once when the result is truthy; do not interpolate, render, or otherwise emit the callback result.
- Support synchronous `@chevron.func` callbacks in `render()` and synchronous or asynchronous `@chevron.func` callbacks in `async_render()`.
- Require the existing `Extension.CONDITIONAL_SECTIONS` setting; do not add a decorator, render option, or additional extension flag.
- Retain existing behaviour for `{{?name}}`, ordinary `{{name}}` interpolation lambdas, section lambdas, compatibility lambdas, and templates where conditional sections are disabled.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditional-section-evaluation`: Extend opt-in conditional syntax with explicit function invocation while preserving the ordinary non-invoking form.
- `template-lambda-mappings`: Define the `@chevron.func` protocol when used by an invoked conditional section.
- `async-template-rendering`: Define awaiting and error handling for invoked conditional callbacks in asynchronous rendering.

## Impact

- Affected code: tokenizer, synchronous and asynchronous renderers, lambda-protocol dispatch, public documentation, and behaviour-focused sync/async tests.
- Public API: no new decorator or render argument; `@chevron.func` gains a second, syntax-selected use.
- Compatibility: the `?*` prefix is reserved only when `Extension.CONDITIONAL_SECTIONS` is enabled. With the extension disabled, it remains an ordinary name prefix, consistent with `?` today.
