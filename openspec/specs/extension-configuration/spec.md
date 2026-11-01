# extension-configuration Specification

## Purpose

Define the process-wide opt-in configuration for Chevron extensions without changing render-call or template APIs.

## Requirements

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

### Requirement: Renderer code can inspect enabled extensions

Chevron's renderer SHALL query an individual extension through `Extension.is_enabled()`.

#### Scenario: Renderer code checks one extension

- **WHEN** a renderer reaches behaviour controlled by an extension
- **THEN** it determines whether to apply that behaviour through `Extension.is_enabled()`

### Requirement: Extension settings are fixed at application startup

Extension configuration is process-wide application-startup configuration. An application that uses extensions SHALL configure them once before it begins using Chevron to render templates. Chevron SHALL freeze the selected mask after that configuration. Chevron SHALL not provide synchronisation for configuration calls.

#### Scenario: An application configures extensions before rendering

- **WHEN** an application enables extensions before it begins rendering
- **THEN** every renderer operation observes the configured extension values

#### Scenario: An application attempts a second configuration

- **WHEN** an application calls `Extension.enable()` after the extension mask has been configured
- **THEN** Chevron raises `RuntimeError`

### Requirement: Conditional sections use an independent extension

Chevron SHALL expose `Extension.CONDITIONAL_SECTIONS` as an independently selectable extension. Enabling it SHALL apply conditional-section syntax without requiring `Extension.ENHANCED_ITERATORS`; `Extension.ALL` SHALL include it.

#### Scenario: Application enables conditional sections alone

- **WHEN** an application calls `Extension.enable(Extension.CONDITIONAL_SECTIONS)` before rendering
- **THEN** conditional sections are enabled and enhanced iterator metadata remains disabled

#### Scenario: Application enables every extension

- **WHEN** an application calls `Extension.enable(Extension.ALL)` before rendering
- **THEN** conditional sections and every other implemented extension are enabled
