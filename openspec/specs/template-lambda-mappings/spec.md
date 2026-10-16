# Template Lambda Mappings Specification

## Purpose

Chevron supplies executable template lambdas through a per-render mapping while preserving legacy section-lambda behaviour when a caller does not opt into explicit mode.

## Requirements

### Requirement: Explicit lambda mappings take precedence for callable sections

Chevron SHALL accept an optional `lambdas` mapping for a render. When supplied, the mapping SHALL be the sole source of executable template lambdas and SHALL be checked before template data for a callable-capable section name. A configured lambda name SHALL shadow template data with the same name.

#### Scenario: Configured lambda executes without template data

- **WHEN** a template section name is present in an explicit lambda mapping and absent from template data
- **THEN** Chevron executes the mapped callable through the supported legacy section-lambda protocol

#### Scenario: Configured lambda shadows template data

- **WHEN** a template section name is present in an explicit lambda mapping and template data contains the same name
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

When supplied, `lambdas` SHALL be a mapping of string template names to callable values. Chevron SHALL reject invalid mappings with a descriptive `TypeError`.

#### Scenario: Invalid lambda mapping is rejected

- **WHEN** a caller supplies a non-mapping, a non-string name, or a non-callable mapped value
- **THEN** Chevron raises `TypeError` before rendering

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

Chevron SHALL apply the active lambda-mapping or legacy behaviour consistently while rendering nested sections, iterable items, partials, and templates rendered through a legacy lambda callback. Complete dotted configured names SHALL resolve directly from the explicit mapping.

#### Scenario: Configured lambda remains available in a partial

- **WHEN** a partial contains a section whose complete name is present in an explicit lambda mapping
- **THEN** Chevron executes the mapped callable while rendering that partial

#### Scenario: Dotted configured lambda executes

- **WHEN** a section uses a dotted template name present in the explicit lambda mapping
- **THEN** Chevron executes the callable mapped to that complete name

#### Scenario: Legacy callback inherits its lambda behaviour

- **WHEN** a legacy section lambda renders a template through its rendering callback
- **THEN** the nested render retains the active explicit or compatibility behaviour

### Requirement: Lambda callback token reuse is render-scoped

Chevron SHALL keep any token reuse needed by a section lambda's supplied rendering callback within the active top-level render context. This internal reuse SHALL not change the public API or rendered output.

#### Scenario: Section-lambda callback retains rendered output

- **WHEN** a section lambda passes its received section text to the supplied rendering callback
- **THEN** Chevron produces the same rendered output while keeping any reused parsed tokens scoped to that active render

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
