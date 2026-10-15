# Spec Delta

## Purpose

Chevron authorises template lambda execution per render while preserving existing legacy section-lambda behaviour for callers that do not opt into explicit authorisation.

## ADDED Requirements

### Requirement: Explicit lambda authorisation

Chevron SHALL accept an optional `lambdas` mapping for a render. When that mapping is supplied, Chevron SHALL execute a section callable only when normal template lookup resolves the exact callable mapped to the complete template name. The mapping SHALL not provide template values or change normal template scope precedence.

#### Scenario: Explicitly authorised callable executes

- **WHEN** a template section resolves a callable that is the exact callable mapped to its complete template name
- **THEN** Chevron executes that callable through the supported legacy section-lambda protocol

#### Scenario: Unauthorised callable is not invoked

- **WHEN** a template section resolves a callable absent from an explicitly supplied lambda mapping
- **THEN** Chevron does not invoke that callable

#### Scenario: Shadowed callable is not authorised by name alone

- **WHEN** an inner template scope resolves a different callable under a name mapped to an outer callable
- **THEN** Chevron does not invoke the inner callable

#### Scenario: Explicit empty mapping authorises no callables

- **WHEN** a render supplies `lambdas={}`
- **THEN** Chevron invokes no callable values as template lambdas

#### Scenario: Unregistered callable section behaves as missing

- **WHEN** a section resolves a callable absent from an explicitly supplied
  mapping
- **THEN** Chevron skips the normal section, renders its inverted section, and
  writes a diagnostic to standard error when `warn=True`

#### Scenario: Explicit mode does not traverse callable internals

- **WHEN** a template performs a dotted lookup from a callable while an
  explicit mapping is supplied
- **THEN** Chevron treats that lookup as missing rather than traversing the
  callable object

#### Scenario: Explicit mode treats callable data as opaque

- **WHEN** a dotted lookup would traverse a callable instance or class while
  an explicit mapping is supplied
- **THEN** Chevron treats that lookup as missing

#### Scenario: Identity mismatch explains the rejection

- **WHEN** a callable section name exists in the supplied mapping but normal
  lookup resolves a different callable and `warn=True`
- **THEN** Chevron emits a diagnostic that identifies the resolved callable as
  different from the callable mapped for that name

#### Scenario: Bound method registrations identify the same receiver and function

- **WHEN** normal lookup and the supplied mapping resolve separately accessed
  Python bound methods with identical `__self__` and `__func__`
- **THEN** Chevron permits the matching section callable

### Requirement: Lambda mapping validation

When supplied, `lambdas` SHALL be a mapping of string section names to
callable values. Chevron SHALL reject invalid mappings with a descriptive
`TypeError`.

#### Scenario: Invalid lambda mapping is rejected

- **WHEN** a caller supplies a non-mapping, a non-string name, or a
  non-callable mapped value
- **THEN** Chevron raises `TypeError` before rendering

### Requirement: Legacy section-lambda compatibility

When a caller omits `lambdas`, Chevron SHALL preserve the existing legacy behaviour for callable section values found through template scopes. Existing two-argument section lambdas SHALL continue to receive the raw section text and a rendering callback, including the callback's temporary-data capability.

#### Scenario: Existing callable section remains executable

- **WHEN** a caller renders a section whose resolved scope value is a callable and omits `lambdas`
- **THEN** Chevron invokes the callable with raw section text and a rendering callback

#### Scenario: Callable reached after a non-callable object attribute remains executable

- **WHEN** compatibility-mode lookup crosses a non-callable object attribute
  and then resolves a callable from a mapping or sequence
- **THEN** Chevron invokes that callable as a legacy section lambda

#### Scenario: Legacy callback can render with temporary data

- **WHEN** a legacy section lambda calls its rendering callback with temporary data
- **THEN** the callback renders that template with the temporary data taking precedence over the active template scopes

### Requirement: Lambda context follows recursive rendering

Chevron SHALL apply the active lambda-authorisation behaviour consistently while rendering nested sections, iterable items, partials, and templates rendered through a legacy lambda callback. Complete dotted template names SHALL be evaluated according to the same mapping and list traversal semantics as normal template lookup.

#### Scenario: Explicit authorisation remains active in a partial

- **WHEN** a partial contains a section that resolves a callable during a render with an explicit lambda mapping
- **THEN** Chevron applies the same mapping and identity check to that partial section

#### Scenario: Dotted callable lookup requires the matching mapped callable

- **WHEN** a section uses a dotted template name that resolves a callable from a nested mapping
- **THEN** Chevron invokes it only when the explicit lambda mapping contains that complete dotted name and the exact callable

#### Scenario: Legacy callback inherits its lambda behaviour

- **WHEN** a legacy section lambda renders a template through its rendering callback
- **THEN** the nested render retains the active authorisation or compatibility behaviour

### Requirement: Lambda callback token reuse is render-scoped

Chevron SHALL keep any token reuse needed by a section lambda's supplied
rendering callback within the active top-level render context. This internal
reuse SHALL not change the public API or rendered output.

#### Scenario: Section-lambda callback retains rendered output

- **WHEN** a section lambda passes its received section text to the supplied
  rendering callback
- **THEN** Chevron produces the same rendered output while keeping any reused
  parsed tokens scoped to that active render

### Requirement: Library partial loading is opt-in

The `render()` library API SHALL default `partials_path` to `None`. A caller
SHALL supply a partial path explicitly to enable filesystem partial loading.
This requirement does not alter the CLI `--path` default.

#### Scenario: Missing mapped partial does not load from the working directory

- **WHEN** a library render supplies no `partials_path` and a partial is absent
  from `partials_dict`
- **THEN** Chevron renders that partial as empty without reading from the
  process working directory

#### Scenario: Explicit partial path restores filesystem lookup

- **WHEN** a library render supplies an explicit `partials_path`
- **THEN** Chevron resolves an otherwise missing partial from that path
