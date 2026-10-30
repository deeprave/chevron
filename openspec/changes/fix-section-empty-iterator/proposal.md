# Proposal

## Why

Chevron deliberately accepts Python `Iterator` values in ordinary sections, but an empty iterator is truthy as a Python object. As a result, an ordinary section renders no items and its paired inverted section also skips, instead of treating the iterator like an empty list. Treating that case as falsey is useful, but it is an extension to Mustache rather than a requirement of the specification. Applications therefore need an explicit, process-wide way to opt into it without changing individual render calls.

## What Changes

- Add a public `Extension` bitmask with `enable()`, `disable()`, and `ALL`, providing one process-wide configuration surface for Chevron extensions.
- Add `Extension.INVERTED_ITERATORS`, disabled by default, to opt into empty synchronous and asynchronous iterators selecting inverted sections.
- When that extension is enabled, use one canonical cursor for each recognised iterator or asynchronous-iterable section binding within a render. Its initial emptiness is unknown until examined, then remains known as empty or non-empty.
- Preserve a recognised iterator's first yielded item when emptiness is checked, so a later ordinary section still renders it.
- Apply synchronous iterator semantics through both `render()` and `async_render()`, and asynchronous iterator semantics through `async_render()`.
- Add public behavioural regression cases for an empty iterator and document the precise iterator behaviour for section authors.

## Capabilities

### New Capabilities

- `extension-configuration`: applications can enable and disable individual non-standard Chevron extensions through a process-wide bitmask.

### Modified Capabilities

- `template-value-resolution`: `INVERTED_ITERATORS` makes recognised empty synchronous iterators control inverted sections while preserving their single-pass contents for ordinary sections.
- `async-template-rendering`: `INVERTED_ITERATORS` gives the corresponding behaviour to asynchronous iterators.

## Impact

- Affects private iterator handling in the shared renderer state and the sync and async section dispatch paths.
- Adds behavioural cases shared by the synchronous renderer and both async backends.
- Updates section-language documentation and adds a small public configuration API without adding parameters to `render()` or `async_render()`.
- With `INVERTED_ITERATORS` enabled, changes the incidental historic behaviour of repeatable `Iterator` and `AsyncIterable` implementations: a recognised streaming value can be traversed only once per render. Once Chevron has exhausted its canonical binding cursor, later ordinary sections render no items rather than restarting it. Inverted sections retain the cursor's recorded initial empty or non-empty result.
