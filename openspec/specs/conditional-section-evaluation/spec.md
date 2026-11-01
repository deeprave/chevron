# conditional-section-evaluation Specification

## Purpose

Provide an opt-in template section that evaluates truthiness without changing the active context or repeating its body.

## Requirements

### Requirement: Conditional sections render a truthy value once

When `Extension.CONDITIONAL_SECTIONS` is enabled, Chevron SHALL recognise `{{?name}}…{{/name}}` as a conditional section. It SHALL render its body once when `name` resolves to a truthy value and SHALL render nothing when the value is falsey or missing.

#### Scenario: Truthy scalar selects its body

- **WHEN** a conditional section resolves to a truthy scalar
- **THEN** Chevron renders its body once

#### Scenario: Falsey or missing value skips its body

- **WHEN** a conditional section resolves to `False`, `0`, an empty string, an empty collection, or a missing name
- **THEN** Chevron renders no conditional-section body

### Requirement: Conditional sections preserve the active context

Chevron SHALL evaluate a conditional section without pushing the resolved value as a scope, iterating it, interpolating it, or invoking it as a lambda. Names inside its body SHALL resolve from the context active before the conditional section.

#### Scenario: Conditional mapping does not become current context

- **WHEN** a conditional section resolves to a truthy mapping and its body interpolates a key from that mapping
- **THEN** the key resolves only if it is available from the pre-existing active context

#### Scenario: Conditional collection does not repeat its body

- **WHEN** a conditional section resolves to a non-empty collection
- **THEN** Chevron renders its body once rather than once per collection item

#### Scenario: Callable is tested without invocation

- **WHEN** a conditional section resolves to a callable
- **THEN** Chevron uses the callable object's truthiness and does not invoke it

### Requirement: Conditional-section syntax is reserved only when enabled

When `Extension.CONDITIONAL_SECTIONS` is enabled, Chevron SHALL recognise `?` as a conditional-section opener. When disabled, Chevron SHALL retain `?` as part of an ordinary variable name. If an apparent paired conditional section has an unmatched or mismatched closing tag, Chevron SHALL log a warning naming `Extension.CONDITIONAL_SECTIONS` before raising its ordinary structural `ChevronError`.

#### Scenario: Disabled prefix remains an ordinary variable

- **WHEN** a template contains `{{?name}}` and the conditional-section extension is disabled
- **THEN** Chevron resolves it as the ordinary variable name `?name`

#### Scenario: Disabled paired syntax reports the opt-in

- **WHEN** a template contains `{{?name}}…{{/name}}` and the conditional-section extension is disabled
- **THEN** Chevron logs a warning naming `Extension.CONDITIONAL_SECTIONS` before raising its ordinary structural error for the unmatched closing tag
