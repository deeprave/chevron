# Design

## Context

Chevron already gates `{{?name}}…{{/name}}` behind `Extension.CONDITIONAL_SECTIONS`. That form deliberately tests a callable object without invoking it. `@chevron.func` already declares an explicit zero-argument callable protocol for interpolation, while `@chevron.section` and `@chevron.compat` have distinct section contracts. See `proposal.md` for the motivation and the delta specs for externally observable behaviour.

## Goals / Non-Goals

**Goals:**

- Add an unambiguous conditional syntax that opts into invoking an existing zero-argument function lambda.
- Reuse the existing conditional-section setting and `@chevron.func` declaration.
- Preserve sync/async parity while retaining existing awaitable-result errors in synchronous rendering.
- Keep the conditional body in its existing active context.

**Non-Goals:**

- Adding a decorator, render argument, extension flag, or lambda protocol.
- Passing section source, rendered content, or a render callback to the invoked function.
- Rendering the function result, adding it to context, or treating it as an iterator source.
- Invoking undecorated, standard-section, or compatibility callbacks through the new syntax.
- Defining or endorsing callback side effects on application-owned template data.

## Decisions

### Use a distinct `?*` token form with the ordinary closing name

When conditional sections are enabled, the tokenizer will recognise `{{?*name}}` as a distinct invoked-conditional opener whose lookup and matching closing name are `name`. This lets `{{/name}}` close the construct without teaching body collection a special name translation. With the extension disabled, tokenizer behaviour remains unchanged: `?*name` is an ordinary variable name.

Alternative considered: represent `?*name` as an ordinary conditional token with a decorated key. That would make matching the existing `{{/name}}` close tag require special-case key rewriting during section collection.

### Reuse `@chevron.func` and dispatch by tag syntax

The decorator declares invocation arity and permission, not how every tag consumes a result. An interpolation tag renders a `@chevron.func` result as Mustache source; an invoked conditional calls the same protocol and applies `bool(result)` without emitting it. The renderer will skip an invoked conditional when lookup does not resolve to that declared protocol.

Alternative considered: add `@chevron.predicate`. It would duplicate the existing zero-argument protocol solely to distinguish result handling already expressed by `?*` syntax.

### Treat a predicate result as an ordinary value

The result is tested directly for Python truthiness. It is not recursively rendered, normalised for interpolation, or probed as a streaming iterator. This keeps the callback result local to the condition and avoids cursor state that cannot be meaningfully reused through a template lookup.

Alternative considered: apply conditional-section iterator probing to a returned iterator. That would consume application data without a stable template name through which to preserve the observed item.

### Reuse existing lambda-result handling per renderer

The synchronous path will use the established awaitable-result rejection path. The asynchronous path will await the callback result through its existing lambda await helper before testing truthiness. Neither path changes callback exception propagation or logging policy.

## Risks / Trade-offs

- [A callback can have application side effects] → Document that it runs once per encountered invoked conditional and avoid treating mutation as a Chevron context feature.
- [The new reserved syntax can conflict with literal `?*name` variables] → Reserve it only while `CONDITIONAL_SECTIONS` is enabled, matching the existing opt-in model.
- [Function and interpolation result semantics differ by tag] → Document that the decorator identifies a callable protocol while tag syntax determines whether the result is rendered or tested.

## Migration Plan

The feature is disabled by default. Applications enable the existing conditional-section extension at startup, register a function with `@chevron.func`, and adopt `{{?*name}}…{{/name}}` only where invocation is intended. No migration is required for existing templates.
