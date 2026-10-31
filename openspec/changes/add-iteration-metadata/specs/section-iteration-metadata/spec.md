# Spec Delta

## Purpose

Provide stable, section-scoped metadata for formatting repeated Mustache values without requiring callers to copy or decorate every item before rendering.

## ADDED Requirements

### Requirement: Repeated sections expose positional metadata

Chevron SHALL reserve `.first`, `.last`, `.index`, and `.ordinal` within each iteration of a repeated section. They SHALL describe the current iteration, retain the original item as `{{.}}`, and take precedence over no application mapping field because their dot-prefixed names are reserved metadata.

#### Scenario: First and last values control formatting

- **WHEN** a section iterates `['one', 'two', 'three', 'four']`
- **THEN** `{{#values}}{{#.first}}- {{/.first}}{{.}}{{^.last}}, {{/.last}}{{/values}}` renders `- one, two, three, four`

#### Scenario: Index and ordinal identify the current iteration

- **WHEN** a section iterates three values
- **THEN** `.index` resolves to `0`, `1`, and `2`, while `.ordinal` resolves to `1`, `2`, and `3`, in iteration order

#### Scenario: Scalar item remains current context

- **WHEN** a section iterates scalar values while positional metadata is available
- **THEN** `{{.}}` continues to resolve to the current scalar item

#### Scenario: Nested repeated sections use nearest metadata

- **WHEN** a repeated section contains another repeated section
- **THEN** each `.first`, `.last`, `.index`, and `.ordinal` reference resolves from the nearest active repeated section

### Requirement: Item count is available only without source consumption

Chevron SHALL expose `.items` as the total number of values only when the repeated source provides a non-consuming size. For a source without such a size, `.items` SHALL resolve as unavailable and Chevron SHALL not consume remaining values merely to calculate it.

#### Scenario: Sized sequence exposes item count

- **WHEN** a section iterates a four-item list or tuple
- **THEN** `.items` resolves to `4` in every iteration

#### Scenario: Generator does not expose item count

- **WHEN** a section iterates a generator with no non-consuming size
- **THEN** `.items` resolves as unavailable while all generator items still render in order

#### Scenario: Async generator does not expose item count

- **WHEN** `async_render()` iterates an asynchronous generator with no non-consuming size
- **THEN** `.items` resolves as unavailable without exhausting the generator ahead of rendering

### Requirement: Mapping sections retain context semantics

Chevron SHALL continue to render a mapping section once as a nested context and SHALL not implicitly iterate its keys, values, or entries to provide iteration metadata.

#### Scenario: Mapping section remains a single context

- **WHEN** a section resolves to a mapping containing named values
- **THEN** its body resolves those values once through the mapping context rather than iterating mapping entries
