# Spec Delta

## MODIFIED Requirements

### Requirement: Interpolation lambdas follow the Mustache protocol

Chevron SHALL invoke a `@chevron.func` zero-argument callable resolved for an interpolation tag once for each occurrence. It SHALL render the callable's returned text as Mustache source against the active context using the configured render-default delimiters, then apply the escaped or unescaped interpolation semantics requested by the original tag. This behaviour SHALL be available in compatibility mode and for a lambda supplied through an explicit mapping. An invoked conditional section uses the same explicit zero-argument function protocol but applies its result as a truthiness value rather than interpolation text.

#### Scenario: Escaped interpolation lambda renders returned template text

- **WHEN** an escaped interpolation tag resolves to a zero-argument lambda that returns Mustache template text
- **THEN** Chevron recursively renders that text and HTML-escapes the resulting interpolation value

#### Scenario: Unescaped interpolation lambda preserves returned markup

- **WHEN** an unescaped interpolation tag resolves to a zero-argument lambda that returns Mustache template text
- **THEN** Chevron recursively renders that text without HTML escaping the resulting interpolation value

#### Scenario: Interpolation lambda is invoked for each occurrence

- **WHEN** a template contains the same zero-argument interpolation lambda tag more than once
- **THEN** Chevron invokes the lambda separately for every occurrence

#### Scenario: Interpolation lambda resets delimiters for returned text

- **WHEN** an interpolation lambda appears while alternate delimiters are active
- **THEN** Chevron parses the lambda's returned text using Mustache's default delimiters

#### Scenario: Section tag does not invoke an interpolation lambda

- **WHEN** a section tag resolves to a lambda that supports interpolation only
- **THEN** Chevron does not invoke that callable through the interpolation-lambda protocol

#### Scenario: Invoked conditional uses the function protocol

- **WHEN** an enabled invoked conditional section resolves `name` from a `lambdas` mapping or compatibility-mode template data to a `@chevron.func` callback
- **THEN** Chevron invokes that callback through its zero-argument function protocol and does not require a new decorator
