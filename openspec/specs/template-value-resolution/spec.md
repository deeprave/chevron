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

The renderer SHALL retain established behaviour for `0`, `False`, empty strings, empty collections, custom falsey values, and values opting into `_CHEVRON_return_scope_when_falsy` across interpolation, unescaped interpolation, normal sections, and inverted sections.

#### Scenario: Numeric zero and false interpolate unchanged

- **WHEN** an interpolation resolves to `0` or `False`
- **THEN** it renders using Chevron's existing string conversion behaviour

#### Scenario: Custom falsey value opts into scope preservation

- **WHEN** a falsey value sets `_CHEVRON_return_scope_when_falsy`
- **THEN** Chevron preserves that value according to the established compatibility behaviour

#### Scenario: Empty value controls an inverted section

- **WHEN** an inverted section resolves to an empty value
- **THEN** its body renders according to existing inverted-section semantics
