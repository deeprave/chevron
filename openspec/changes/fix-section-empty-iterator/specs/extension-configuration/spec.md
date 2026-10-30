# Spec Delta

## ADDED Requirements

### Requirement: Applications configure Chevron extensions globally

Chevron SHALL expose an `Extension` bitmask for optional, non-standard rendering behaviour. It SHALL provide `NONE`, an individually named value for every implemented extension, and `ALL` containing every implemented extension. Applications SHALL enable or disable one or more values through `Extension.enable()` and `Extension.disable()` without adding configuration to a render call or template context. Extensions SHALL be disabled by default.

#### Scenario: An application enables one extension

- **WHEN** an application calls `Extension.enable(Extension.INVERTED_ITERATORS)` before rendering
- **THEN** subsequent renders apply that extension

#### Scenario: An application configures all current extensions

- **WHEN** an application calls `Extension.enable(Extension.ALL)`
- **THEN** subsequent renders apply every extension currently represented by `ALL`

#### Scenario: An application disables a group of extensions

- **WHEN** an application calls `Extension.disable()` with one or more extension values, including `Extension.ALL`
- **THEN** subsequent renders do not apply those extensions

#### Scenario: An application supplies an unknown extension bit

- **WHEN** an application constructs `Extension` with a bit Chevron does not define
- **THEN** construction raises `ValueError`

#### Scenario: An application leaves extensions unconfigured

- **WHEN** an application renders without enabling an extension
- **THEN** Chevron retains the existing standard and compatibility behaviour for that extension

### Requirement: Renderer code can inspect enabled extensions

Chevron's renderer SHALL query an individual extension through `Extension.is_enabled()`.

#### Scenario: Renderer code checks one extension

- **WHEN** a renderer reaches behaviour controlled by an extension
- **THEN** it determines whether to apply that behaviour through `Extension.is_enabled()`

### Requirement: Extension settings are fixed at application startup

Extension configuration is process-wide application-startup configuration. An application that uses extensions SHALL configure them once before it begins using Chevron to render templates. Dynamic extension changes during later application runtime, including changes while rendering is in progress, are outside Chevron's supported contract. Chevron SHALL not provide synchronisation or runtime enforcement for such changes.

#### Scenario: An application configures extensions before rendering

- **WHEN** an application enables or disables extensions before it begins rendering
- **THEN** every renderer operation observes the configured extension values

#### Scenario: An application attempts to change extensions after startup

- **WHEN** an application enables or disables an extension after it has begun using Chevron to render templates
- **THEN** that dynamic configuration change is outside Chevron's supported contract, even though Chevron does not currently reject it
