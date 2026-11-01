# Spec Delta

## ADDED Requirements

### Requirement: Conditional sections use an independent extension

Chevron SHALL expose `Extension.CONDITIONAL_SECTIONS` as an independently selectable extension. Enabling it SHALL apply conditional-section syntax without requiring `Extension.ENHANCED_ITERATORS`; `Extension.ALL` SHALL include it.

#### Scenario: Application enables conditional sections alone

- **WHEN** an application calls `Extension.enable(Extension.CONDITIONAL_SECTIONS)` before rendering
- **THEN** conditional sections are enabled and enhanced iterator metadata remains disabled

#### Scenario: Application enables every extension

- **WHEN** an application calls `Extension.enable(Extension.ALL)` before rendering
- **THEN** conditional sections and every other implemented extension are enabled
