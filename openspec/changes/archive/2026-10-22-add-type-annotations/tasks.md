# Tasks

## 1. Establish public annotation contracts

- [x] 1.1 Inventory package exports and annotate `render`, `async_render`, lambda decorators, CLI helpers, tokenizer entry points, and public exception-facing APIs without changing their runtime signatures; verify representative sync and async public calls type-check.
- [x] 1.2 Define only local aliases and protocols needed by those public contracts in their owning modules—including `TemplateData`, template/token inputs, readers, render callbacks, lambda registries, logging, and scope sequences—while retaining `Any` at dynamic Mustache lookup boundaries; use `TYPE_CHECKING` only for necessary annotation-only imports and verify Ty accepts the annotated source API.

## 2. Complete strict source annotations

- [x] 2.1 Annotate renderer, async-renderer, tokenizer, and CLI implementation control flow where their contracts are stable, including frames, configuration, token handling, filesystem helpers, and callback dispatch; make `src/` pass the strict-equivalent Ty and source-only Ruff annotation checks while preserving existing rendering behaviour.

## 3. Make the test suite pass Ty

- [x] 3.1 Annotate test fixtures, callback parameters, async test doubles, and specification data until Ty's pragmatic test check passes; resolve module lookup using the test search path and use only narrow local suppressions for deliberate invalid-call tests.

## 4. Maintain the type-checking baseline

- [x] 4.1 Configure Ty's documented strict-equivalent rules with a `src/` override, run one Ty check over `src/` and `tests/` using the established test module search path, and add source-only Ruff `ANN` and `PYI` preview checks; verify the CI and local quality commands pass.
- [x] 4.2 Confirm the package contains no `py.typed` marker and that annotations did not alter package contents or public runtime behaviour; verify the full test suite, source annotation checks, combined Ty check with strict-equivalent source rules and pragmatic test rules, and package build pass.
