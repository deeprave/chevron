# Spec Delta

## MODIFIED Requirements

### Requirement: Explicit lambda mappings take precedence for callable sections

Chevron SHALL accept an optional `lambdas` mapping for a render. When supplied, the mapping SHALL be the sole source of executable template lambdas and SHALL be checked before template data for a callable tag name. A configured lambda name SHALL shadow template data with the same name. This applies to interpolation and section tags according to the configured lambda's supported protocol.

#### Scenario: Configured lambda executes without template data

- **WHEN** a template lambda tag name is present in an explicit lambda mapping and absent from template data
- **THEN** Chevron executes the mapped callable through its supported lambda protocol

#### Scenario: Configured lambda shadows template data

- **WHEN** a template lambda tag name is present in an explicit lambda mapping and template data contains the same name
- **THEN** Chevron executes the mapped callable without resolving that name from template data

#### Scenario: Explicit empty mapping configures no callables

- **WHEN** a render supplies `lambdas={}`
- **THEN** Chevron executes no template callable from the mapping

### Requirement: Lambda mapping validation

When supplied, `lambdas` SHALL be a mapping of string template names to callable values. Chevron SHALL reject invalid mappings with a descriptive `TypeError`. Chevron SHALL provide `@chevron.func`, `@chevron.section`, and `@chevron.compat` to declare zero-argument interpolation, Mustache-standard section, and Chevron legacy section protocols respectively. The new function and standard-section protocols SHALL require their decorators in both explicit and compatibility modes. Existing unannotated two-argument registered section lambdas SHALL retain the legacy protocol for backwards compatibility.

#### Scenario: Invalid lambda mapping is rejected

- **WHEN** a caller supplies a non-mapping, a non-string name, or a non-callable mapped value
- **THEN** Chevron raises `TypeError` before rendering

#### Scenario: Registered standard section lambda declares its protocol

- **WHEN** a caller registers a callable decorated with `@chevron.section`
- **THEN** Chevron invokes it as a standard section lambda rather than as a legacy two-argument callback

#### Scenario: Registered interpolation lambda declares its protocol

- **WHEN** a caller registers a zero-argument callable decorated with `@chevron.func`
- **THEN** Chevron invokes it through the interpolation-lambda protocol

#### Scenario: Registered compatibility lambda declares its protocol

- **WHEN** a caller registers a two-argument callable decorated with `@chevron.compat`
- **THEN** Chevron invokes it through the Chevron legacy section-lambda protocol

#### Scenario: Unannotated registered legacy section lambda remains compatible

- **WHEN** a caller registers an existing unannotated two-argument section lambda
- **THEN** Chevron invokes it through the legacy section-lambda protocol

### Requirement: Lambda context follows recursive rendering

Chevron SHALL apply the active lambda mapping or compatibility behaviour consistently while rendering nested sections, iterable items, partials, and text recursively rendered from a lambda. Complete dotted configured names SHALL resolve directly from the explicit mapping.

#### Scenario: Configured lambda remains available in a partial

- **WHEN** a partial contains a lambda tag whose complete name is present in an explicit lambda mapping
- **THEN** Chevron executes the mapped callable while rendering that partial

#### Scenario: Dotted configured lambda executes

- **WHEN** a tag uses a dotted template name present in the explicit lambda mapping
- **THEN** Chevron executes the callable mapped to that complete name

#### Scenario: Legacy callback inherits its lambda behaviour

- **WHEN** a legacy section lambda renders a template through its rendering callback
- **THEN** the nested render retains the active explicit or compatibility behaviour

#### Scenario: Recursively rendered lambda text inherits lambda behaviour

- **WHEN** a lambda returns template text that contains another lambda tag
- **THEN** the nested render retains the active explicit or compatibility behaviour

#### Scenario: Compatibility mode remains permissive

- **WHEN** `lambdas` is omitted and a callable is reached through ordinary template data in a section
- **THEN** Chevron retains its existing two-argument compatibility callback behaviour

### Requirement: Lambda callback token reuse is render-scoped

Chevron SHALL keep token reuse needed by a legacy section lambda's supplied rendering callback within the active top-level render context, without changing the public API or rendered output. Chevron SHALL retain immutable configured render-default delimiters separately from active parser delimiters. Interpolation lambda results and partials SHALL start with the configured render-default delimiters. Standard section lambda results SHALL start with the delimiter pair active when their section opens. Chevron SHALL not share tokenizer diagnostic state between renders, and SHALL use cached tokens only for legacy compatibility callback replay.

#### Scenario: Section-lambda callback retains rendered output

- **WHEN** a section lambda passes its received section text to the supplied rendering callback
- **THEN** Chevron produces the same rendered output while keeping any reused parsed tokens scoped to that active render

#### Scenario: Skipped section preserves lexical delimiter change

- **WHEN** a false section contains a delimiter-change tag
- **THEN** its enclosing render continues with the changed active delimiters without changing its configured render defaults

#### Scenario: Lambda returns no value

- **WHEN** an invoked lambda returns `None`
- **THEN** Chevron renders an empty value and emits a diagnostic when `warn=True`

## ADDED Requirements

### Requirement: Interpolation lambdas follow the Mustache protocol

Chevron SHALL invoke a `@chevron.func` zero-argument callable resolved for an interpolation tag once for each occurrence. It SHALL render the callable's returned text as Mustache source against the active context using the configured render-default delimiters, then apply the escaped or unescaped interpolation semantics requested by the original tag. This behaviour SHALL be available in compatibility mode and for a lambda supplied through an explicit mapping.

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

### Requirement: Standard section lambdas follow the Mustache protocol

Chevron SHALL invoke a `@chevron.section` standard section lambda with the unrendered source enclosed by its section tags. It SHALL recursively render the lambda's returned text against the active context and delimiter pair active at the section opening. Compatibility mode SHALL select the standard protocol from its decorator, while preserving existing undecorated two-argument legacy section lambdas.

#### Scenario: Standard section lambda receives literal source

- **WHEN** a section resolves to a standard one-argument lambda
- **THEN** Chevron passes the literal source between the opening and closing section tags, including comments and whitespace removed from rendered output by standalone processing

#### Scenario: Standard section lambda return value is recursively rendered

- **WHEN** a standard section lambda returns text containing a template tag
- **THEN** Chevron renders that returned text using the active context

#### Scenario: Alternate delimiters remain active for returned section text

- **WHEN** a standard section lambda appears under alternate delimiters and returns text using those delimiters
- **THEN** Chevron recursively renders the returned text with the active delimiters

#### Scenario: Legacy section callback remains available

- **WHEN** a compatibility-mode section resolves to an existing two-argument callable
- **THEN** Chevron continues to pass raw source and a rendering callback that accepts temporary data
