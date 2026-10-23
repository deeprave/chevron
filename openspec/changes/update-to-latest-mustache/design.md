# Design

## Context

See `proposal.md` for the motivation. Chevron currently vendors seven JSON modules from Mustache revision `934db98` and executes every JSON file it finds. The current upstream revision is `e8ec001db7f594521e773c34866aca2b5d6b0037`; it contains the seven existing modules plus optional `~dynamic-names.json` and `~inheritance.json`.

The initial experimental step refreshes the fixtures and runs the complete
conformance group against the current renderer. Its recorded per-module result
is the implementation map; it replaces any earlier aggregate count. The map
will identify the core dotted-name defect and the dynamic-name/inheritance
requirements that must constrain the iterative-renderer refactor.

## Experimental Baseline

On 2026-10-22, upstream `mustache/spec` HEAD resolved to
`e8ec001db7f594521e773c34866aca2b5d6b0037`. All nine JSON modules were
copied into the uncommitted worktree and verified byte-for-byte against that
revision. The `conformance` marker selects both synchronous and asynchronous
fixture executions.

Each renderer mode has the same 194-case result: 150 passing and 44 failing.
The asynchronous test runs once under asyncio and once under Trio, producing
the combined 582-case baseline of 450 passing and 132 failing executions.

| Module | Passing per mode | Failing per mode |
| --- | ---: | ---: |
| `comments`, `delimiters`, `inverted`, `partials`, `sections`, `~lambdas` | 104 | 0 |
| `interpolation` | 41 | 1 |
| `~dynamic-names` | 5 | 16 |
| `~inheritance` | 0 | 27 |

The interpolation failure is `Dotted Names - Context Precedence`. The dynamic
and inheritance failures cover their current upstream extension requirements;
this map is input to, not an exception from, the eventual all-passing gate.

## Current implementation status

After the isolated dotted-name and dynamic-partial corrections, every dynamic
name case passes in the synchronous, asyncio, and Trio renderers. Each mode
now has 167 passing and 27 failing cases; the remaining failures are all from
the inheritance module. Dynamic partial names resolve exactly one leading
asterisk name through the active frame, then reuse the established partial
lookup and rendering path without adding a scope frame.

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

### Establish a separately runnable conformance group before implementation

Mark both synchronous and asynchronous tests that execute vendored upstream
fixtures with pytest's `conformance` marker. This provides a bounded command
for the initial baseline and for later compatibility verification without
mixing it with Chevron-owned behavioural tests.

### Map compatibility first, then suspend for the iterative renderer refactor

Refresh and execute the full fixture set before changing renderer behaviour.
Record the upstream pin and per-module outcomes as the compatibility map, then
pause this change without committing the experimental fixture refresh. Complete
`refactor-iterative-renderer` first, using that map to ensure its frame and
control-flow design can accommodate the required current-Mustache behaviour.
Resume this change only after the refactor is ready for the implementation work.

### Defer public API shape until implementation is understood

Dynamic partial names and inheritance should initially reuse the established
rendering and partial-lookup contracts. Do not decide that this is a permanent
public-API constraint before the implementation shape is known. If a new
argument becomes necessary, make it keyword-only, preserve existing callers
where possible, and retain compatibility mode when direct preservation is not
possible.

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

1. Pin the current upstream head, refresh the fixture worktree, and record the complete conformance baseline without committing it.
2. Use the mapped failures to shape and complete `refactor-iterative-renderer`; suspend this change while that refactor is underway.
3. Resume this change, review and commit the vendor refresh, then update the harness classification and dotted-name lookup with regression coverage.
4. Implement dynamic-name and inheritance behaviour, then run the conformance group and full repository checks.
5. Roll back by restoring the prior vendored revision and lookup behaviour if the update reveals an unintended compatibility regression.
