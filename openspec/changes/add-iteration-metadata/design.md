# Design

## Context

See [proposal.md](proposal.md) for motivation and the new specification for externally visible behaviour. Chevron currently creates a private frame for every repeated item, but exposes only the item itself. mcp-guide works around this by copying list items into mappings carrying `first` and `last`; Chevron can provide equivalent information without caller preprocessing.

This change depends on `fix-section-empty-iterator`. That change supplies bounded synchronous and asynchronous source state, including a buffered item when an iterator must be observed before normal rendering continues.

## Goals / Non-Goals

**Goals:**

- Make positional metadata available without changing caller-owned items or source collections.
- Preserve streaming for synchronous and asynchronous generators.
- Keep nested iteration metadata scoped to the nearest repeated section.
- Retain ordinary mapping section semantics.

**Non-Goals:**

- Add implicit mapping-entry iteration or key/value decomposition.
- Materialise or pre-scan a source solely to determine its count or last item.
- Expose positional metadata as ordinary unprefixed item fields.
- Add a public iterator-wrapper API.

## Decisions

### Store metadata in a private iteration frame overlay

Each repeated item will receive a private frame overlay containing the reserved dot-prefixed values. Resolution will recognise `.first`, `.last`, `.index`, `.ordinal`, and `.items` from the nearest active iteration overlay before ordinary application lookup. The overlay leaves mapping items, scalar items, caller scopes, and `{{.}}` untouched.

This is preferable to injecting keys into mapping items: it works for scalars, avoids copying user values, prevents mutation, and makes nested iteration scope naturally follow the existing render-frame chain.

### Use bounded lookahead to determine `last`

The iterator adapters established by `fix-section-empty-iterator` will be extended to buffer at most one upcoming item. Before rendering an item, the adapter determines whether another item exists. This makes `.last` accurate without materialising a generator. The async counterpart awaits only the required next-item operation and preserves its buffer across suspension and cancellation.

Computing `last` after rendering would be too late for template conditionals; collecting every item first would defeat streaming.

### Capture a count only from a non-consuming sized source

At section entry, obtain `.items` only from a repeated source that implements a non-consuming size operation. Store that captured total in the iteration metadata. A source that has no such operation exposes no `.items` value; Chevron does not drain it to manufacture a count. Mappings remain excluded even though they are sized because Chevron does not repeat their entries.

Returning an unavailable value rather than raising lets templates use normal Mustache fallback behaviour and preserves generator streaming.

### Keep synchronous and asynchronous adapters separate

Synchronous and asynchronous protocols require distinct next-item and cancellation behaviour. They will use small parallel adapters with equivalent observable metadata rather than a universal wrapper that mixes `next()` and `anext()`.

## Risks / Trade-offs

- [Lookahead changes source timing] → Buffer no more than one item and release it through the normal iteration path.
- [A source mutates after its size is captured] → `.items` represents the non-consuming size observed when section iteration begins.
- [Reserved names might collide with template data] → Use dot-prefixed names that Chevron currently resolves as missing rather than ordinary mapping fields.
- [Async lookahead introduces an await point] → Await only source observation and retain the buffered value; do not parallelise or prefetch beyond one item.

## Migration Plan

No migration is required. Existing templates retain their current values; templates may opt in to the reserved metadata names. If rollback is necessary, removing the metadata overlay restores the prior unresolved dot-prefixed names without altering caller data.
