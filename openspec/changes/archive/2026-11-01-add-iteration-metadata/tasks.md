# Tasks

## 1. Expose positional section metadata

- [x] 1.1 Rename `Extension.INVERTED_ITERATORS` to `Extension.ENHANCED_ITERATORS` and update its public documentation, compatibility notes, and extension configuration specification before release.
- [x] 1.2 Extend the private synchronous repeated-section state used by `Extension.ENHANCED_ITERATORS` to provide render-frame metadata for `.first`, `.last`, `.index`, and `.ordinal`, calculating sized-source length only when needed and using bounded lookahead otherwise; verify scalar and mapping list items retain their existing `{{.}}` and named-field behaviour.
- [x] 1.3 Add `.0`, `.1`, and other non-negative numeric metadata lookup for non-mapping sources supporting both `__len__` and `__getitem__`; return `None` for unsupported and out-of-range indexes without consuming streams.
- [x] 1.4 Add the equivalent asynchronous repeated-section metadata state; verify positional values remain correct for async generators under both supported AnyIO backends.
- [x] 1.5 Route reserved dot-prefixed metadata lookup through the nearest active repeated-section frame without exposing it outside that iteration; verify nested repeated sections use their own metadata.

## 2. Provide optional item counts and public guidance

- [x] 2.1 Resolve `.length` only from non-mapping repeated sources with `__len__`; verify sized sequences and iterators expose a count without consuming iteration while synchronous and asynchronous generators remain streaming with `.length` resolving to `None`.
- [x] 2.2 Add fixture-based public rendering cases for extension-enabled prefix/separator formatting, zero-based `.index`, one-based `.ordinal`, known counts, unavailable generator counts, nested sections, and unchanged mapping contexts; verify the applicable sync and async render suites.
- [x] 2.3 Document the reserved iteration metadata, count availability, generator streaming boundary, and mapping-context compatibility in the Sections guide; verify the strict MkDocs build.
