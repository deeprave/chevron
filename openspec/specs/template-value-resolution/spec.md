# template-value-resolution Specification

## Purpose

Define stable value-resolution behaviour so template tags can apply their own semantics without lookup prematurely discarding resolved values.

## Requirements

### Requirement: Raw resolved values remain available to tag dispatch

The renderer SHALL preserve a resolved value until the consuming tag applies its own rendering semantics. A missing name SHALL remain distinguishable from a resolved falsey value while dispatch is in progress.

#### Scenario: Empty value is resolved for a section

- **WHEN** a section name resolves to an empty collection
- **THEN** the section applies ordinary falsey section behaviour rather than treating the name as unresolved

#### Scenario: Missing name is resolved for interpolation

- **WHEN** an interpolation name is absent from every template scope
- **THEN** the interpolation renders as an empty string and retains the configured missing-key diagnostic behaviour

### Requirement: Callable section values are dispatched before falsey coercion

The renderer SHALL dispatch a callable section value before applying generic falsey-value coercion. This SHALL apply to both legacy callable sections and callables permitted through an explicit lambda mapping.

#### Scenario: Falsey legacy callable instance

- **WHEN** a legacy section value is callable and evaluates as falsey
- **THEN** Chevron invokes the callable section

#### Scenario: Falsey explicitly permitted callable instance

- **WHEN** an explicitly permitted section value is callable and evaluates as falsey
- **THEN** Chevron invokes the callable section

### Requirement: Existing falsey-value rendering remains compatible

The renderer SHALL retain established behaviour for `0`, `False`, empty strings, empty collections, and custom falsey values across interpolation, unescaped interpolation, normal sections, and inverted sections.

#### Scenario: Numeric zero and false interpolate unchanged

- **WHEN** an interpolation resolves to `0` or `False`
- **THEN** it renders using Chevron's existing string conversion behaviour

#### Scenario: Private falsey-value attributes are ignored

- **WHEN** a custom falsey value exposes `_CHEVRON_return_scope_when_falsy`
- **THEN** Chevron does not inspect or honour that attribute and applies ordinary falsey rendering behaviour

#### Scenario: Empty value controls an inverted section

- **WHEN** an inverted section resolves to an empty value
- **THEN** its body renders according to existing inverted-section semantics

### Requirement: Dotted names retain their resolved scope

Chevron SHALL resolve the first component of a dotted name from the active template scopes. Each remaining component SHALL resolve only from the value produced by its preceding component and SHALL not fall back to another active scope.

#### Scenario: Outer scopes cannot satisfy a broken dotted chain

- **WHEN** a template resolves the first component in an inner scope but a later component is absent from that value and present in an outer scope
- **THEN** the dotted name renders as unresolved rather than using the outer-scope value

#### Scenario: Dotted names still resolve nested values

- **WHEN** every component of a dotted name exists on the value resolved by its preceding component
- **THEN** the interpolation renders the terminal nested value
