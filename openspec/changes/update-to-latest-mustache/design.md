# Design

## Context

See `proposal.md` for the motivation. Chevron currently vendors seven JSON modules from Mustache revision `934db98` and executes every JSON file it finds. The current upstream revision is `e8ec001db7f594521e773c34866aca2b5d6b0037`; it contains the seven existing modules plus optional `~dynamic-names.json` and `~inheritance.json`.

Running the current renderer against that full upstream set produces 150 passes and 44 failures. The only core failure is dotted-name context precedence. The remaining failures belong to the two newly added optional modules, which introduce dynamic partial names and template inheritance. Those modules are part of this change's implementation scope.

## Goals / Non-Goals

**Goals:**

- Vendor the complete current upstream JSON fixture set with immutable provenance.
- Preserve core and lambda fixtures as a passing, deterministic conformance gate.
- Fix the core dotted-name scoping defect exposed by the update.
- Implement dynamic-name and inheritance support so the complete vendored suite is a passing compatibility gate.

**Non-Goals:**

- Alter Chevron's explicit lambda protocols, filesystem partial policy, or public `render()` API.
- Rewrite or customise upstream fixture content.

## Decisions

### Vendor all upstream JSON modules at one immutable revision

Copy the JSON files from upstream `specs/` at `e8ec001` and retain a Chevron-owned attribution README that records the full commit hash, upstream URL, and licensing. JSON remains the input format because the existing harness materialises the upstream JSON representation of tagged lambda fixtures without adding a YAML dependency.

Using a full immutable revision rather than selectively copying new core files provides a reproducible baseline and lets future support work enable already-reviewed optional suites. Copying only supported fixtures would hide the current standard surface and require another vendor update before optional implementation work can begin.

### Execute the complete vendored suite

Keep fixture discovery comprehensive: every vendored JSON module is enabled and must pass. The tilde prefix denotes upstream optionality, not an opt-out from Chevron's conformance gate once Chevron chooses to vendor that module.

Excluding dynamic names and inheritance would create a baseline of known failures rather than a standards update. Vendoring the complete suite and implementing all its modules keeps the fixture set an honest release gate.

### Preserve dotted-name scope after the first component resolves

Adjust lookup so that outer-scope search applies only while resolving the first component of a dotted name. Once that component is found, resolve each remaining component exclusively against the preceding value. A failed later component therefore produces an unresolved value rather than restarting the whole dotted chain in an outer scope.

This matches the new upstream context-precedence fixture and keeps ordinary top-level name shadowing intact. It also avoids altering falsey-value handling, callable restrictions, or direct single-name lookup.

### Extend partial rendering rather than bypassing partial policy

Dynamic partial names resolve a context value first and then pass the resolved name through the established partial lookup path. Parent partials reuse ordinary partial lookup for their parent name, but carry a render-local block-override mapping through that parent render. This preserves `partials_dict` precedence, opt-in filesystem partial lookup, containment protections, and render re-entrancy.

The tokenizer must represent parent and block constructs distinctly from ordinary sections so it can pair and collect overrides without treating their closing tags as unmatched sections. The renderer then applies the nearest override while retaining the existing context stack and ordinary partial indentation path.

### Keep upstream fixtures independent from Chevron behavioural tests

The vendor suite remains a black-box conformance signal through the public render API. Add or adjust Chevron-owned regression tests only for the dotted-name behaviour and module classification; do not encode implementation structure or edit the upstream cases to make them pass.

## Risks / Trade-offs

- [Optional modules require parser and renderer extension] → Add support through render-local metadata and exercise the official dynamic-name and inheritance cases as black-box acceptance tests.
- [The fixture refresh changes current test cardinality] → Run the complete vendored suite so accidental omission is visible.
- [Dotted lookup changes historic outer-scope fallback] → Cover both the new precedence case and existing nested dotted-name behaviour with regression tests.
- [Future upstream fixture formats evolve] → Retain the existing JSON/tag materialisation boundary and keep provenance in the attribution README.

## Migration Plan

1. Replace fixture files and update provenance documentation in one reviewable change.
2. Update the harness classification and dotted-name lookup with regression coverage.
3. Run the enabled conformance suite and full repository checks.
4. Roll back by restoring the prior vendored revision and lookup behaviour if the update reveals an unintended compatibility regression.
