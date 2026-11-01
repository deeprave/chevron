# Spec Delta

## Purpose

Provide stable, section-scoped metadata for formatting repeated Mustache values without requiring callers to copy or decorate every item before rendering.

## ADDED Requirements

### Requirement: Repeated sections expose positional metadata

When `Extension.ENHANCED_ITERATORS` is enabled, Chevron SHALL reserve every leading-dot name other than `.` within each iteration of a repeated section. It SHALL resolve `.first`, `.last`, `.index`, `.ordinal`, and `.length` from the current iteration, retain the original item as `{{.}}`, and resolve unsupported reserved names to `None` without application-data fallback. When the extension is disabled, those names SHALL retain ordinary unresolved-name behaviour.

#### Scenario: First and last values control formatting

- **WHEN** `Extension.ENHANCED_ITERATORS` is enabled and a section iterates `['one', 'two', 'three', 'four']`
- **THEN** `{{#values}}{{#.first}}- {{/.first}}{{.}}{{^.last}}, {{/.last}}{{/values}}` renders `- one, two, three, four`

#### Scenario: Index and ordinal identify the current iteration

- **WHEN** `Extension.ENHANCED_ITERATORS` is enabled and a section iterates three values
- **THEN** `.index` resolves to `0`, `1`, and `2`, while `.ordinal` resolves to `1`, `2`, and `3`, in iteration order

#### Scenario: Scalar item remains current context

- **WHEN** `Extension.ENHANCED_ITERATORS` is enabled and a section iterates scalar values while positional metadata is available
- **THEN** `{{.}}` continues to resolve to the current scalar item

#### Scenario: Nested repeated sections use nearest metadata

- **WHEN** `Extension.ENHANCED_ITERATORS` is enabled and a repeated section contains another repeated section
- **THEN** each `.first`, `.last`, `.index`, and `.ordinal` reference resolves from the nearest active repeated section

### Requirement: Length is available only without source consumption

When `Extension.ENHANCED_ITERATORS` is enabled, Chevron SHALL expose `.length` as the number of values only when a non-mapping repeated source provides `__len__`. For a source without such a size, `.length` SHALL resolve to `None` and Chevron SHALL not consume remaining values merely to calculate it.

#### Scenario: Sized source exposes length

- **WHEN** `Extension.ENHANCED_ITERATORS` is enabled and a section iterates a four-item list or tuple
- **THEN** `.length` resolves to `4` in every iteration

#### Scenario: Generator does not expose length

- **WHEN** `Extension.ENHANCED_ITERATORS` is enabled and a section iterates a generator with no non-consuming size
- **THEN** `.length` resolves to `None` while all generator items still render in order

#### Scenario: Async generator does not expose length

- **WHEN** `Extension.ENHANCED_ITERATORS` is enabled and `async_render()` iterates an asynchronous generator with no non-consuming size
- **THEN** `.length` resolves to `None` without exhausting the generator ahead of rendering

### Requirement: Numeric metadata addresses indexable sources

When `Extension.ENHANCED_ITERATORS` is enabled, Chevron SHALL resolve `.0`, `.1`, and other non-negative decimal names from a non-mapping source that supports both `__len__` and `__getitem__`. It SHALL resolve a negative, unsupported, or out-of-range numeric name to `None` without consuming a streaming source.

#### Scenario: Numeric metadata resolves an item

- **WHEN** an enhanced repeated section iterates `['one', 'two', 'three']`
- **THEN** `.0`, `.1`, and `.2` resolve to `one`, `two`, and `three` in every iteration

#### Scenario: Numeric metadata is unavailable for a generator

- **WHEN** an enhanced repeated section iterates a generator without random access
- **THEN** `.0` resolves to `None` without advancing the generator

#### Scenario: Numeric metadata is out of range

- **WHEN** an enhanced repeated section iterates a two-item indexable source
- **THEN** `.2` resolves to `None`

### Requirement: Mapping sections retain context semantics

Chevron SHALL continue to render a mapping section once as a nested context and SHALL not implicitly iterate its keys, values, or entries to provide iteration metadata.

#### Scenario: Mapping section remains a single context

- **WHEN** a section resolves to a mapping containing named values
- **THEN** its body resolves those values once through the mapping context rather than iterating mapping entries
