# Spec Delta

## Purpose

Define current Mustache optional-module rendering behaviour for dynamic partial names and template inheritance so the complete vendored upstream conformance suite passes.

## ADDED Requirements

### Requirement: Dynamic partial names resolve through the active context
Chevron SHALL support a partial name prefixed with `*` by resolving the remaining name through the active template context, then loading the resulting partial using the ordinary partial lookup rules. Dynamic partial lookup SHALL retain ordinary partial context, recursion, whitespace, and indentation behaviour.

#### Scenario: Dynamic partial name selects a configured partial
- **WHEN** a template contains a dynamic partial tag whose resolved name exists in the configured partial mapping
- **THEN** Chevron renders that partial using the active context

#### Scenario: Dynamic partial name resolves a dotted value
- **WHEN** a dynamic partial name contains a dotted context path
- **THEN** Chevron resolves the path using ordinary dotted-name semantics before selecting the partial

#### Scenario: Missing dynamic partial name is empty
- **WHEN** a dynamic partial name cannot be resolved or selects no available partial
- **THEN** Chevron renders the tag as an empty value without loading an unintended partial

### Requirement: Parent partials support named block overrides
Chevron SHALL support parent partials and named blocks so a child template can render a parent while overriding the parent's declared blocks. The parent SHALL use its default block content when the child supplies no override.

#### Scenario: Child overrides a parent block
- **WHEN** a child template renders a parent and supplies content for one of the parent's named blocks
- **THEN** the parent output contains the child block content in place of that block's default content

#### Scenario: Parent uses its default block
- **WHEN** a parent template's named block has no child override
- **THEN** Chevron renders the block's default content

#### Scenario: Nested inheritance preserves block scope
- **WHEN** parent templates inherit through multiple levels with nested block overrides
- **THEN** each block resolves according to the nearest applicable override without changing ordinary template-data scope

### Requirement: Inherited partial output preserves standalone and indentation rules
Chevron SHALL apply ordinary Mustache standalone-line and partial-indentation behaviour while rendering dynamic partials, parent partials, and block overrides.

#### Scenario: Indented inherited partial
- **WHEN** a dynamic or inherited partial appears on an indented standalone line
- **THEN** Chevron applies the same indentation behaviour as an ordinary partial
