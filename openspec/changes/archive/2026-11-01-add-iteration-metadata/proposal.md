# Proposal

## Why

Template authors currently need to preprocess repeated values into mapping objects to format the first, middle, and last item differently. Chevron can provide this information directly while preserving the current item as `{{.}}` and keeping generator rendering streaming.

## What Changes

- Rename `Extension.INVERTED_ITERATORS` to `Extension.ENHANCED_ITERATORS`, reflecting that it enables empty-iterator inversion and section iteration metadata.
- Add reserved, section-scoped iteration values: `.first`, `.last`, zero-based `.index`, one-based `.ordinal`, and `.length`.
- Add `.length` as the non-consuming item count when the repeated source exposes `__len__`; otherwise it resolves to `None`.
- Add `.0`, `.1`, and other non-negative decimal index names for non-mapping values that expose both `__len__` and `__getitem__`; unsupported or out-of-range indexes resolve to `None`.
- Make metadata available only when `Extension.ENHANCED_ITERATORS` is enabled, extending the existing opt-in streaming-iterator behaviour rather than adding a second extension flag.
- Support the metadata for repeated sequences, synchronous iterators, and asynchronous iterators without mutating item mappings or caller-owned sources.
- Preserve mappings as one Mustache context rather than iterating their keys, values, or entries.
- Document conditional separator and prefix patterns using the reserved values.

## Capabilities

### New Capabilities

- `section-iteration-metadata`: reserved contextual values for formatting individual iterations of a repeated Mustache section.

### Modified Capabilities

- `extension-configuration`: rename the iterator opt-in and expand its documented behaviour.

## Impact

- Extends the template language with reserved dot-prefixed names that were previously unresolved.
- Builds on the bounded iterator state introduced by `fix-section-empty-iterator` for synchronous and asynchronous single-pass sources.
- Affects private render-frame lookup, iterator adapters, shared behavioural cases, async cases, and section documentation.
