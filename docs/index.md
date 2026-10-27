# Chevron

Chevron is a modern Python implementation of [Mustache](https://mustache.github.io/). It is a maintained fork of the original `chevron`, with current Python support, pinned Mustache conformance fixtures, safe opt-in filesystem partials, explicit lambda protocols, and optional AnyIO-based asynchronous rendering.

Start with [Getting started](getting-started.md) for a complete, small application example. The [template-language guide](language/index.md) explains what template authors can write; the [API reference](api/render.md) describes how an application supplies templates, data, partials, and diagnostics.

## Choose the right entry point

- Use [`render()`](api/render.md) for ordinary synchronous Python applications.
- Use [`async_render()`](api/async-render.md) inside an existing AnyIO runtime when template readers, iterables, or lambdas may await I/O.
- Use [`chevron.tokenizer.tokenize()`](api/tokenizer.md) when an application owns template compilation or caching and wants to reuse a validated token stream.

Chevron follows the [upstream Mustache manual](reference/mustache.md) for the language, then documents its supported extensions and compatibility details separately.
