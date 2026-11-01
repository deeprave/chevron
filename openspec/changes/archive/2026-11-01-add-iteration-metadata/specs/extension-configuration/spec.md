# Spec Delta

## MODIFIED Requirements

### Requirement: Applications configure Chevron extensions globally

Chevron SHALL expose an `Extension` bitmask for optional, non-standard rendering behaviour. It SHALL provide `NONE`, an individually named value for every implemented extension, and `ALL` containing every implemented extension. Applications SHALL select one or more values through one call to `Extension.enable()` without adding configuration to a render call or template context. Extensions SHALL be disabled by default.

#### Scenario: An application enables one extension

- **WHEN** an application calls `Extension.enable(Extension.ENHANCED_ITERATORS)` before rendering
- **THEN** subsequent renders apply empty-iterator inversion and section iteration metadata

#### Scenario: An application configures all current extensions

- **WHEN** an application calls `Extension.enable(Extension.ALL)`
- **THEN** subsequent renders apply every extension currently represented by `ALL`

#### Scenario: An application leaves extensions unconfigured

- **WHEN** an application renders without enabling an extension
- **THEN** Chevron retains the existing standard and compatibility behaviour for that extension
