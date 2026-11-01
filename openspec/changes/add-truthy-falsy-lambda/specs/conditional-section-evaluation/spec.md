# Spec Delta

## MODIFIED Requirements

### Requirement: Conditional sections preserve the active context

Chevron SHALL evaluate an ordinary conditional section without pushing the resolved value as a scope, iterating it, interpolating it, or invoking it as a lambda. Names inside its body SHALL resolve from the context active before the conditional section. An explicitly invoked conditional function is governed by the invoked-conditional requirement.

#### Scenario: Conditional mapping does not become current context

- **WHEN** a conditional section resolves to a truthy mapping and its body interpolates a key from that mapping
- **THEN** the key resolves only if it is available from the pre-existing active context

#### Scenario: Conditional collection does not repeat its body

- **WHEN** a conditional section resolves to a non-empty collection
- **THEN** Chevron renders its body once rather than once per collection item

#### Scenario: Callable is tested without invocation

- **WHEN** an ordinary conditional section resolves to a callable
- **THEN** Chevron uses the callable object's truthiness and does not invoke it

## ADDED Requirements

### Requirement: Conditional sections can invoke explicit function lambdas

When `Extension.CONDITIONAL_SECTIONS` is enabled, Chevron SHALL recognise `{{?*name}}…{{/name}}` as an invoked conditional section. It SHALL invoke a `@chevron.func` callback once, test its result using ordinary Python truthiness, and render the body once only when that result is truthy. It SHALL preserve the active context and SHALL not render or interpolate the callback result.

#### Scenario: Truthy function result selects the body

- **WHEN** an invoked conditional section resolves to a `@chevron.func` callback that returns a truthy value
- **THEN** Chevron invokes it once and renders the body once against the pre-existing active context

#### Scenario: Falsey function result skips the body

- **WHEN** an invoked conditional section resolves to a `@chevron.func` callback that returns `None`, `False`, `0`, an empty string, or an empty collection
- **THEN** Chevron invokes it once and renders no body

#### Scenario: Function result is not interpolation output

- **WHEN** an invoked conditional function returns text containing Mustache syntax
- **THEN** Chevron tests that text for truthiness without rendering or emitting it

#### Scenario: Unsupported callable protocol is not invoked

- **WHEN** an invoked conditional section resolves to an undecorated callable or a callback declared with `@chevron.section` or `@chevron.compat`
- **THEN** Chevron does not invoke that callback and renders no body

## MODIFIED Requirements

### Requirement: Conditional-section syntax is reserved only when enabled

When `Extension.CONDITIONAL_SECTIONS` is enabled, Chevron SHALL recognise `?` as a conditional-section opener and `?*` as an invoked conditional-section opener. When disabled, Chevron SHALL retain both prefixes as part of an ordinary variable name. If an apparent paired conditional section has an unmatched or mismatched closing tag, Chevron SHALL log a warning naming `Extension.CONDITIONAL_SECTIONS` before raising its ordinary structural `ChevronError`.

#### Scenario: Disabled prefix remains an ordinary variable

- **WHEN** a template contains `{{?name}}` and the conditional-section extension is disabled
- **THEN** Chevron resolves it as the ordinary variable name `?name`

#### Scenario: Disabled invoked prefix remains an ordinary variable

- **WHEN** a template contains `{{?*name}}` and the conditional-section extension is disabled
- **THEN** Chevron resolves it as the ordinary variable name `?*name`

#### Scenario: Disabled paired syntax reports the opt-in

- **WHEN** a template contains `{{?name}}…{{/name}}` and the conditional-section extension is disabled
- **THEN** Chevron logs a warning naming `Extension.CONDITIONAL_SECTIONS` before raising its ordinary structural error for the unmatched closing tag
