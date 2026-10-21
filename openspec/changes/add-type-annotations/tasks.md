# Tasks

## 1. Establish public annotation contracts

- [ ] 1.1 Inventory package exports and annotate `render`, `async_render`, lambda decorators, CLI helpers, tokenizer entry points, and public exception-facing APIs without changing their runtime signatures; verify representative sync and async public calls type-check.
- [ ] 1.2 Define only the shared aliases and protocols needed by those public contracts—template/token inputs, readers, render callbacks, lambda registries, logging, and scope sequences—while retaining `Any` at dynamic Mustache lookup boundaries; verify Ty accepts the annotated source API.

## 2. Add practical implementation annotations

- [ ] 2.1 Annotate renderer, async-renderer, tokenizer, and CLI implementation control flow where their contracts are stable, including frames, configuration, token handling, filesystem helpers, and callback dispatch; verify existing rendering tests preserve identical runtime behaviour.
- [ ] 2.2 Annotate test fixtures, callback parameters, async test doubles, and specification data enough for Ty to check tests; resolve module lookup using the test search path and use only narrow local suppressions for deliberate invalid-call tests; verify `ty check src tests --extra-search-path tests` has no diagnostics.

## 3. Maintain the type-checking baseline

- [ ] 3.1 Extend the quality workflow's Ty command to check both source and tests using the established test module search path; verify the CI command and local quality command pass without enabling strict mode.
- [ ] 3.2 Confirm the package contains no `py.typed` marker and that annotations did not alter package contents or public runtime behaviour; verify the full test suite, Ruff checks, Ty baseline, and package build pass.
