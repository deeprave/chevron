# Tasks

## 0. Establish the experimental compatibility map

- [x] 0.1 Resolve the upstream Mustache head at the start of the experiment, pin its immutable commit, copy every JSON fixture into the uncommitted worktree, and verify their checksums against that commit.
- [x] 0.2 Define a `conformance` pytest marker and apply it to every synchronous and asynchronous test that executes vendored upstream fixtures, so the entire compatibility suite can run separately.
- [x] 0.3 Run the complete `conformance` group against the refreshed fixtures and record a per-module pass/fail baseline, including the exact upstream commit, as the compatibility map.
- [x] 0.4 Suspend this change without committing the experimental fixture refresh. Use the compatibility map to shape `refactor-iterative-renderer`, then resume this change after that refactor is ready for the required Mustache behaviours.

## 1. Commit the reviewed specification baseline after the renderer refactor

- [ ] 1.1 Reconfirm the upstream pin selected during the experimental baseline, commit every reviewed JSON fixture from that revision into `tests/fixtures/mustache-spec/`, including `~dynamic-names.json` and `~inheritance.json`, and verify their checksums match upstream.
- [ ] 1.2 Update the fixture attribution README with the immutable revision, upstream URL, licence attribution, and the current optional-module support status; verify the recorded revision resolves upstream.

## 2. Enable the complete conformance suite

- [ ] 2.1 Update the fixture harness so every vendored upstream JSON module, including dynamic names and inheritance, is enabled; verify the parametrised cases cover all nine modules.
- [ ] 2.2 Keep the harness adapter limited to upstream JSON tagged-lambda materialisation and add behaviour-focused coverage for complete fixture discovery; verify no vendored module is silently excluded and the `conformance` group remains complete.

## 3. Correct core dotted-name resolution

- [ ] 3.1 Change dotted-name lookup so only its first component searches active scopes and later components remain within the resolved value; verify the upstream context-precedence fixture passes.
- [ ] 3.2 Add Chevron-owned regression coverage for outer-scope fallback rejection and successful nested dotted lookup; verify the tests exercise the public render API.

## 4. Implement dynamic partial names

- [ ] 4.1 Extend tokenisation and rendering to resolve `{{>*name}}` tags through the active context before ordinary partial lookup; verify every dynamic-name fixture passes, including dotted resolution, recursion, whitespace, and indentation cases.
- [ ] 4.2 Add Chevron-owned public-API regression tests for dynamic-partial resolution and missing values; verify configured partial mappings and existing filesystem partial safeguards remain intact.

## 5. Implement template inheritance

- [ ] 5.1 Extend tokenisation to represent parent and named-block tags without interpreting their closing tags as ordinary unmatched sections; verify the inheritance fixture parser cases execute without tokenisation errors.
- [ ] 5.2 Implement render-local parent/block override handling using ordinary partial lookup and active scopes; verify every inheritance fixture passes, including defaults, nested inheritance, recursion, and scope cases.
- [ ] 5.3 Add Chevron-owned public-API regression tests for block override precedence and inherited indentation; verify ordinary partial rendering remains unchanged.

## 6. Verify complete current conformance

- [ ] 6.1 Run the complete vendored Mustache conformance suite and verify every core and optional-module case passes.
- [ ] 6.2 Run the repository check array (`pytest -Werror`, Ruff check and format, Ty, OSV, pyproject validation, Bandit, Vulture, and `uv build`) and verify all checks pass.
