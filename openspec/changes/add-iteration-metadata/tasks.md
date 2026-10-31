# Tasks

## 1. Expose positional section metadata

- [ ] 1.1 Extend the private synchronous repeated-section state from `fix-section-empty-iterator` to provide bounded lookahead and render-frame metadata for `.first`, `.last`, `.index`, and `.ordinal`; verify scalar and mapping list items retain their existing `{{.}}` and named-field behaviour.
- [ ] 1.2 Add the equivalent asynchronous repeated-section metadata state; verify positional values remain correct for async generators under both supported AnyIO backends.
- [ ] 1.3 Route reserved dot-prefixed metadata lookup through the nearest active repeated-section frame without exposing it outside that iteration; verify nested repeated sections use their own metadata.

## 2. Provide optional item counts and public guidance

- [ ] 2.1 Capture `.items` only from repeated sources with a non-consuming size, excluding mapping contexts; verify lists and tuples expose a stable count while synchronous and asynchronous generators remain streaming with `.items` unavailable.
- [ ] 2.2 Add fixture-based public rendering cases for prefix/separator formatting, zero-based `.index`, one-based `.ordinal`, known counts, unavailable generator counts, nested sections, and unchanged mapping contexts; verify the applicable sync and async render suites.
- [ ] 2.3 Document the reserved iteration metadata, count availability, generator streaming boundary, and mapping-context compatibility in the Sections guide; verify the strict MkDocs build.
