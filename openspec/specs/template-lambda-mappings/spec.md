# Template Lambda Mappings Specification

## Purpose

Chevron supplies executable template lambdas through a per-render mapping while preserving legacy section-lambda behaviour when a caller does not opt into explicit mode.

## Requirements

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

### Requirement: Explicit mode rejects callable template data

When an explicit lambda mapping is supplied, template data SHALL not be an executable callable source. A callable resolved from template data where no configured lambda name takes precedence SHALL render as an empty value and SHALL emit a diagnostic when `warn=True`.

#### Scenario: Callable data in a section is rejected

- **WHEN** an explicit mapping lacks a section name that resolves to a callable in template data
- **THEN** Chevron does not invoke the callable and treats the section as falsey

#### Scenario: Callable data in interpolation is rejected

- **WHEN** an explicit mapping is supplied and an interpolation resolves to a callable in template data
- **THEN** Chevron renders an empty value and emits a diagnostic when `warn=True`

#### Scenario: Non-callable template data remains available

- **WHEN** an explicit mapping lacks a template name that resolves to a non-callable value
- **THEN** Chevron renders that value according to the tag's ordinary semantics

#### Scenario: Explicit mode does not traverse callable data

- **WHEN** a template performs a dotted lookup from a callable in template data while an explicit mapping is supplied
- **THEN** Chevron treats that lookup as missing rather than traversing the callable object

### Requirement: Lambda mapping validation

When supplied, `lambdas` SHALL map string template names to callable values, rejecting invalid mappings with `TypeError`. Chevron SHALL provide `@chevron.func`, `@chevron.section`, and `@chevron.compat` for interpolation, standard-section, and legacy-section protocols. New protocols require their decorators; unannotated registered two-argument section lambdas retain the legacy protocol.

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

### Requirement: Legacy section-lambda compatibility

When a caller omits `lambdas` or passes `None`, Chevron SHALL preserve the existing legacy behaviour for callable section values found through template scopes. Existing two-argument section lambdas SHALL continue to receive the raw section text and a rendering callback, including the callback's temporary-data capability.

#### Scenario: Existing callable section remains executable

- **WHEN** a caller renders a section whose resolved scope value is a callable and omits `lambdas`
- **THEN** Chevron invokes the callable with raw section text and a rendering callback

#### Scenario: Callable reached after a non-callable object attribute remains executable

- **WHEN** compatibility-mode lookup crosses a non-callable object attribute and then resolves a callable from a mapping or sequence
- **THEN** Chevron invokes that callable as a legacy section lambda

#### Scenario: Legacy callback can render with temporary data

- **WHEN** a legacy section lambda calls its rendering callback with temporary data
- **THEN** the callback renders that template with the temporary data taking precedence over the active template scopes

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

Chevron SHALL keep legacy callback token reuse within the active top-level render context without changing public output. It SHALL retain configured render-default delimiters separately from active parser delimiters. Interpolation results and partials start with configured defaults; standard-section results start with their opening delimiters. Tokenizer state is per render, and cached tokens are only for legacy callback replay.

#### Scenario: Section-lambda callback retains rendered output

- **WHEN** a section lambda passes its received section text to the supplied rendering callback
- **THEN** Chevron produces the same rendered output while keeping any reused parsed tokens scoped to that active render

#### Scenario: Skipped section preserves lexical delimiter change

- **WHEN** a false section contains a delimiter-change tag
- **THEN** its enclosing render continues with the changed active delimiters without changing its configured render defaults

#### Scenario: Lambda returns no value

- **WHEN** an invoked lambda returns `None`
- **THEN** Chevron renders an empty value and emits a diagnostic when `warn=True`

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

### Requirement: Library partial loading is opt-in

The `render()` library API SHALL default `partials_path` to `None`. A caller SHALL supply `partials_path` explicitly to enable filesystem partial loading. This requirement does not alter the CLI `--path` default.

#### Scenario: Missing mapped partial does not load from the working directory

- **WHEN** a library render supplies no `partials_path` and a partial is absent from `partials_dict`
- **THEN** Chevron renders that partial as empty without reading from the process working directory

#### Scenario: Explicit partial path restores filesystem lookup

- **WHEN** a library render supplies an explicit `partials_path`
- **THEN** Chevron resolves an otherwise missing partial from that path

### Requirement: Filesystem partial fallback remains within its configured root

Chevron SHALL consult `partials_dict` before filesystem lookup. When a partial has no `partials_dict` match and filesystem partial loading is enabled, Chevron SHALL read only relative partial names without parent-directory traversal whose resolved targets remain at or below `partials_path`. Chevron MAY follow a symlink used for `partials_path` itself, but SHALL reject an absolute partial name or a nested symlink that escapes that root.

#### Scenario: Mapped partial bypasses filesystem fallback

- **WHEN** `partials_dict` contains a named partial and `partials_path` is also supplied
- **THEN** Chevron renders the mapped partial without reading the filesystem

#### Scenario: Partial traversal is rejected

- **WHEN** a template names an absolute partial, a parent-directory traversal, or a nested symlink whose resolved target is outside the configured partial root
- **THEN** Chevron treats that partial as missing and renders it as empty

#### Scenario: Symlinked partial root remains available

- **WHEN** the configured partial root is itself a symlink and a relative partial resolves beneath that root's target
- **THEN** Chevron loads and renders the partial
