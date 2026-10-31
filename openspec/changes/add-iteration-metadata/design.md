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

Each repeated item will carry minimal private iteration context on its render frame: the source, its invocation-local index, and a bounded-last verdict where one is required. Resolution calculates `.first`, `.index`, `.ordinal`, `.length`, and numeric access only when the corresponding leading-dot name is resolved. It recognises reserved names from the nearest active iteration frame before ordinary application lookup. The context leaves mapping items, scalar items, caller scopes, and `{{.}}` untouched.

This is preferable to injecting keys into mapping items: it works for scalars, avoids copying user values, prevents mutation, and makes nested iteration scope naturally follow the existing render-frame chain.

### Extend the existing iterator extension

`Extension.ENHANCED_ITERATORS` is the single opt-in for iteration metadata as well as empty-iterator inversion. It replaces the narrower `INVERTED_ITERATORS` name before release. When disabled, Chevron does not provide reserved metadata values and their names retain ordinary unresolved-name behaviour. This keeps iterator adaptation under one configuration boundary and avoids multiple combinations of related streaming behaviour.

### Use a captured length or bounded lookahead to determine `last`

For any non-mapping source with `__len__`, Chevron calculates `.last` from the current `.index` only when `.last` is resolved, without lookahead. Other iterator adapters buffer at most one upcoming item before rendering an item. This bounded lookahead remains eager for unsized sources so `.last` works consistently for synchronous and asynchronous rendering without making all async lookup awaitable.

Computing `last` after rendering would be too late for template conditionals; collecting every item first would defeat streaming.

### Capture a count only from a non-consuming sized source

When `.length` is resolved, obtain it only from a non-mapping repeated source that implements `__len__`. A source that has no such operation resolves `.length` to `None`; Chevron does not drain it to manufacture a count. Mappings remain excluded even though they are sized because Chevron does not repeat their entries.

Returning `None` rather than raising leaves unsized sources falsey in templates, prevents outer-context fallback for the reserved name, and preserves generator streaming.

### Resolve numeric names only from sized, indexable sources

Reserved names of the form `.0`, `.1`, and so on address a repeated source by its zero-based index. Chevron exposes them only when the non-mapping source supports both `__len__` and `__getitem__`; `__len__` alone cannot provide non-consuming random access. Within an enhanced iteration frame, every leading-dot name other than `.` is reserved: a negative, unsupported, out-of-range, or oversized numeric name resolves to `None`. This avoids materialising, advancing a streaming iterator, or falling back to application data for a random lookup.

### Keep synchronous and asynchronous adapters separate

Synchronous and asynchronous protocols require distinct next-item and cancellation behaviour. They will use small parallel adapters with equivalent observable metadata rather than a universal wrapper that mixes `next()` and `anext()`.

## Risks / Trade-offs

- [Lookahead changes source timing] → Buffer no more than one item and release it through the normal iteration path.
- [A source mutates after its size is resolved] → `.length` represents the non-consuming size reported by the source for that resolution.
- [Reserved names might collide with template data] → Use dot-prefixed names that Chevron currently resolves as missing rather than ordinary mapping fields.
- [Async lookahead introduces an await point] → Await only source observation and retain the buffered value; do not parallelise or prefetch beyond one item.

## Migration Plan

No migration is required. Existing templates retain their current values; templates may opt in to the reserved metadata names. If rollback is necessary, removing the metadata overlay restores the prior unresolved dot-prefixed names without altering caller data.
