# Mustache specification fixtures

These JSON fixtures are copied from the [Mustache specification repository](https://github.com/mustache/spec)
at revision [`e8ec001db7f594521e773c34866aca2b5d6b0037`](https://github.com/mustache/spec/tree/e8ec001db7f594521e773c34866aca2b5d6b0037).

They replace the former Git submodule so the Chevron test suite is
self-contained. The fixture set includes lambda, dynamic-name, and inheritance
modules. Lambda and dynamic-name conformance currently pass. Inheritance
remains experimental compatibility work pending the iterative-renderer
refactor.

The upstream Mustache specification is MIT licensed. This repository's
[`LICENSE`](../../../LICENSE) applies to Chevron itself; retain this attribution
when updating the vendored fixtures.
