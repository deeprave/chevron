# Test suite guide

Chevron's tests are organised by the observable behavior they protect. Tests
exercise public entry points unless a resource boundary must be controlled to
create the caller-visible condition under test.

## Behavioral source-template cases

`rendering_cases.py` defines the small immutable `RenderCase` record used for
ordinary source-template rendering. Topic modules provide named scenarios:

- `value_cases.py` covers basic interpolation and text rendering.
- `scope_cases.py` covers context, scope precedence, value normalisation, and
  dotted lookup.
- `section_cases.py` covers ordinary and inverted section behavior.
- `partial_cases.py` covers partial lookup, dynamic names, parent templates,
  and block overrides.
- `inheritance_cases.py` covers inheritance, standalone handling, indentation,
  and line endings.
- `whitespace_cases.py` covers delimiter state that affects subsequent
  rendering and partial expansion.
- `lambda_cases.py` covers declared lambda scenarios whose complete contract
  is the rendered result. It uses fresh case-local callable mappings and keeps
  callback protocol and lifecycle assertions in focused tests.
- `filesystem_partial_cases.py` covers ordinary temporary file-tree partial
  lookup. Security, ownership, cancellation, and I/O scheduling behavior
  remain focused resource tests.
- `async_cases.py` covers ordinary async-only source inputs, including fresh
  async iterables. Iterator lifecycle and cancellation behavior remain focused
  tests.

`test_rendering_cases.py` runs the synchronous collection through
`chevron.render`. `async/test_rendering.py` begins with every sync-compatible
case, adds async-only cases, and runs the result through `chevron.async_render`
on every supported AnyIO backend. A case name is therefore visible together
with the renderer mode in a failure.

Case collections are suitable only when a scenario is ordinary source-template
rendering with shared inputs and expected output. Keep them small and grouped
by durable behavior; do not turn them into a general testing DSL or force
resource-driven behavior into their shape.

Cases may explicitly supply an initial delimiter pair when that is the
behavior under test. This is passed through as `def_ldel` and `def_rdel`; it
is not a general collection of render options.

## Focused public-contract tests

Keep dedicated tests where the public contract needs resources or lifecycle
control that a source-template case cannot represent. These include template
readers, filesystem partial lookup, logging and diagnostics, lambda protocols,
token-sequence input, cancellation, concurrency, and optional async imports.
Place each test with the behavior it protects, rather than in a generic
regression or implementation-named module.

## Vendored conformance

`fixtures/mustache-spec/` contains the immutable upstream Mustache JSON
fixtures. `test_specifications.py` and `async/test_specifications.py` execute
them and retain the `conformance` marker and upstream-module markers. Chevron's
own behavior cases are not conformance fixtures and must not be added to that
directory or marked as conformance.

## Test resources

Use pytest fixtures for resource lifecycle and backend selection. The shared
AnyIO backend fixture lives in `async_support.py`; async tests remain
collectable only when the optional runtime is installed. Filesystem and other
resource tests create their own temporary resources with pytest fixtures.
