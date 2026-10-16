# Tasks

## 1. Separate resolution from interpolation coercion

- [x] 1.1 Refactor template-name lookup to return raw resolved values and a private missing sentinel while retaining missing-key warnings; verify focused tests cover missing escaped and unescaped interpolation.
- [x] 1.2 Move existing interpolation coercion to escaped and unescaped tag dispatch; verify `0`, `False`, empty strings, empty collections, custom falsey values, and `_CHEVRON_return_scope_when_falsy` preserve current rendered output.

## 2. Apply section-specific value handling

- [x] 2.1 Update normal and inverted section dispatch to consume raw resolved values while preserving context-stack and ordinary truthiness behaviour; verify nested, empty, and missing section cases.
- [x] 2.2 Dispatch callable section values before falsey coercion in legacy and explicit lambda modes; verify falsey callable instances execute and an unpermitted callable retains explicit-mode behaviour.

## 3. Verify renderer compatibility

- [x] 3.1 Run the full renderer test suite and compare against the known Mustache lambda conformance baseline; verify all non-deferred regressions pass and the known issue #4 failures remain visible.
