# Tasks

## 1. Define the canonical iterator contract

- [x] 1.1 Provide focused synchronous and asynchronous canonical cursor state that reports unknown, non-empty, or empty initial state and retains at most one peeked item.
- [x] 1.2 Associate canonical state with each name in its supplying context so repeated resolution through partials consumes the same cursor, while a shadowed value or distinct name remains independent.

## 2. Route rendering through canonical cursors

- [x] 2.1 Route synchronous iterator sections in both public APIs through canonical state, preserving empty inverted selection and retaining a non-empty cursor's inverted result after it is exhausted.
- [x] 2.2 Route asynchronous iterable sections through the corresponding canonical state with the same ordering and exhaustion rules, while keeping iterator lifecycle application-owned.

## 3. Capture the public behaviour

- [x] 3.1 Add fixture-based sync and async cases for inverted-first buffering, ordinary-first exhaustion, repeated inverted checks, fresh wrappers through partials and child contexts, shadowed values, and falsey iterator values.
- [x] 3.2 Add cases showing that recognised repeatable iterator and async-iterable sources do not restart after their canonical cursor is exhausted, while retaining their initial inverted-section result.
- [x] 3.3 Update the language and async API documentation and changelog with the streaming-cursor contract and its repeatable-source compatibility difference.
- [x] 3.4 Preserve callable and explicitly marked falsey value precedence before iterator probing, and document and test that contract in both render modes.
- [x] 3.5 Remove the undocumented falsey-value escape hatch and its tests, specifications, and iterator-specific extensions.
- [x] 3.6 Add safe falsey-value and missing-state lookup short-circuits while preserving synchronous rejection of asynchronous iterable section values.
- [x] 3.7 Clarify that the async exhausted-iterator scenario applies to a non-empty cursor.

## 4. Make iterator inversion an explicit extension

- [x] 4.1 Add the process-wide public `Extension` bitmask, including `NONE`, `INVERTED_ITERATORS`, `ALL`, and explicit `enable()` and `disable()` operations.
- [x] 4.2 Provide `Extension.is_enabled()` for renderer code to query the process-wide extension mask without adding arguments to `render()` or `async_render()`.
- [x] 4.3 Apply canonical cursor probing and single-traversal behaviour only when `INVERTED_ITERATORS` is enabled; retain existing iterator behaviour when it is disabled.
- [x] 4.4 Cover default and enabled behaviour in synchronous, asyncio, and Trio rendering, including additive, subtractive, and `ALL` configuration.
- [x] 4.5 Document the extension configuration API and revise iterator documentation and changelog wording to distinguish default and opted-in behaviour.
