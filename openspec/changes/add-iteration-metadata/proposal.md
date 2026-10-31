# Proposal

## Why

Template authors currently need to preprocess repeated values into mapping objects to format the first, middle, and last item differently. Chevron can provide this information directly while preserving the current item as `{{.}}` and keeping generator rendering streaming.

## What Changes

- Add reserved, section-scoped iteration values: `.first`, `.last`, zero-based `.index`, and one-based `.ordinal`.
- Add `.items` as the total item count only when the repeated source exposes a non-consuming size; otherwise it resolves as unavailable.
- Support the metadata for repeated sequences, synchronous iterators, and asynchronous iterators without mutating item mappings or caller-owned sources.
- Preserve mappings as one Mustache context rather than iterating their keys, values, or entries.
- Document conditional separator and prefix patterns using the reserved values.

## Capabilities

### New Capabilities

- `section-iteration-metadata`: reserved contextual values for formatting individual iterations of a repeated Mustache section.

### Modified Capabilities

- None.

## Impact

- Extends the template language with reserved dot-prefixed names that were previously unresolved.
- Builds on the bounded iterator state introduced by `fix-section-empty-iterator` for synchronous and asynchronous single-pass sources.
- Affects private render-frame lookup, iterator adapters, shared behavioural cases, async cases, and section documentation.
