# Mustache and conformance

Chevron follows the [upstream Mustache manual at commit `115baf2`](https://github.com/mustache/mustache.github.com/blob/115baf277db1adc09354871271a7ec8dd7b73a5a/mustache.5.html). That pinned revision is the normative language reference for tags, sections, partials, delimiter changes, lambdas, dynamic names, and inheritance.

The repository vendors the upstream specification fixtures under `tests/fixtures/mustache-spec/`. They are test inputs, not another user guide. Chevron marks them as `conformance` tests and records their upstream provenance in [the fixture attribution](https://github.com/deeprave/chevron/tree/main/tests/fixtures/mustache-spec).

The guide explains the practical subset an application developer needs to use Chevron successfully. When wording differs in level of detail, the upstream manual defines the language and Chevron's [extensions](extensions.md) and [compatibility notes](compatibility.md) define the renderer-specific contract.
