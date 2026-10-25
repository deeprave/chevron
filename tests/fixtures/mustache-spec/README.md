# Mustache specification fixtures

These JSON fixtures are copied from the [Mustache specification repository](https://github.com/mustache/spec)
at revision [`e8ec001db7f594521e773c34866aca2b5d6b0037`](https://github.com/mustache/spec/tree/e8ec001db7f594521e773c34866aca2b5d6b0037).

They replace the former Git submodule so the Chevron test suite is
self-contained. The fixture set includes lambda, dynamic-name, and inheritance
modules. Chevron passes lambda, dynamic-name, and inheritance conformance for
this pinned revision.

Each case has a pytest marker derived from its source JSON module. For example,
`~inheritance.json` cases are marked `mustache_inheritance`. The full
`conformance` marker continues to select every fixture. Individual modules can
also be selected with an expression such as `pytest -m mustache_inheritance`.

The upstream Mustache specification is MIT licensed. This repository's
[`LICENSE`](../../../LICENSE) applies to Chevron itself; retain this attribution
when updating the vendored fixtures.
