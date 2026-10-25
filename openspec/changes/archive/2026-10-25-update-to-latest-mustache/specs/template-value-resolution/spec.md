# Spec Delta

## ADDED Requirements

### Requirement: Dotted names retain their resolved scope
Chevron SHALL resolve the first component of a dotted name from the active template scopes. Each remaining component SHALL resolve only from the value produced by its preceding component and SHALL not fall back to another active scope.

#### Scenario: Outer scopes cannot satisfy a broken dotted chain
- **WHEN** a template resolves the first component in an inner scope but a later component is absent from that value and present in an outer scope
- **THEN** the dotted name renders as unresolved rather than using the outer-scope value

#### Scenario: Dotted names still resolve nested values
- **WHEN** every component of a dotted name exists on the value resolved by its preceding component
- **THEN** the interpolation renders the terminal nested value
