# Tasks

## 1. Behavioural Coverage

- [x] 1.1 Add pytest-style tests for explicit lambda mappings: exact authorised execution, unauthorised callable non-execution, shadowed callable identity mismatch, and `lambdas={}` strict mode; verify the focused test module fails before implementation and passes afterwards.
- [x] 1.2 Add pytest-style tests for dotted callable names and partial rendering under an explicit mapping; verify each path retains the same authorisation rule.
- [x] 1.3 Add pytest-style regression tests for omitted-`lambdas` compatibility, including legacy two-argument callbacks and temporary callback data; verify current legacy behaviour remains covered.

## 2. Render Context and Authorisation

- [x] 2.1 Add the optional public `lambdas` argument and private composite render context with normalised legacy lambda definitions; verify existing `data` and `scopes` calls still render unchanged.
- [x] 2.2 Propagate the composite context through nested sections, iterable items, partials, and legacy callback rendering; verify the focused recursive-render tests pass.
- [x] 2.3 Enforce exact name-and-identity authorisation for section callables in explicit-mapping mode while preserving omitted-`lambdas` compatibility derivation; verify all lambda-mapping tests pass.

## 3. Documentation and Validation

- [x] 3.1 Document `lambdas=` explicit mode, `lambdas={}` strict mode, and legacy compatibility in the README; verify the examples distinguish template data from lambda authorisation.

## 4. Review Follow-ups

- [x] 4.1 Replace eager compatibility extraction with lookup-time eligibility; cover aliases, tuple-backed paths, current-scope callables, literal dotted keys, cyclic data, and unused custom mappings with pytest.
- [x] 4.2 Keep recursive render-context threading private; prevent rejected callables from becoming section scopes and cover callback restriction propagation with pytest.

## 5. Accepted Implementation Follow-ups

- [x] 5.1 Add pytest-style behaviour coverage for compatibility lookup through object-held mappings and sequences; explicit-mode recursive rejection in partials, iterable items, and callback data; callable-leaf lookup; rejected-section output and warning; bound methods; invalid mappings; and legacy callback temporary callables.
- [x] 5.2 Implement compatibility and explicit-mode callable policies: `allows_context_callables`, callable-leaf lookup in explicit mode, missing-section handling and diagnostics for rejected callables, strict mapping validation, and narrow bound-method matching.

## 6. Security and Contract Follow-ups

- [x] 6.1 Add pytest-style contract coverage for explicit-mode callable opacity, `lambdas=None`, `scopes=`, class-bound methods, generic mappings, authorised inverted sections, scope precedence, mapping snapshot semantics, and both rejection warning reasons.
- [x] 6.2 Retain explicit-mode callable opacity, distinguish missing-name from identity-mismatch warnings, remove the unreachable ordinary-section callable conditional, and update the public `render()` docstring.
- [x] 6.3 Change the library `render()` default to `partials_path=None`, retain the CLI `--path` default of `.`, and add regressions for disabled default fallback and explicit filesystem lookup.
- [x] 6.4 Update README and CHANGELOG with the explicit-mode callable restriction, safe section-lambda pattern, non-sandbox boundary, and the breaking library partial default with explicit compatibility restoration.

## 7. Review Follow-ups

- [x] 7.1 Add behavioural regressions for same-receiver different bound-method rejection, rejected inverted-section warnings, and callable-instance opacity in explicit mode.
- [x] 7.2 Make `warn=True` distinguish blocked callable traversal from an absent key without treating registered callables as traversable.
- [x] 7.3 Move lambda-section token reuse from process-global state to the private render context, preserving existing rendering behaviour and public API.
- [x] 7.4 Correct the README partials default comment and replace developer-oriented direct Git installation guidance with supported end-user installation guidance.

## 8. Lambda-first Explicit Resolution

- [x] 8.1 Replace explicit-mode identity matching with lambda-first section resolution and template-data callable rejection; verify lambda entries shadow same-named template data and unconfigured data callables render empty with `warn=True`.
- [x] 8.2 Update pytest-style behaviour coverage for lambda-only sections, lambda precedence, rejected callable interpolation and sections, explicit empty mappings, and unchanged legacy callable execution; verify the focused suite passes.
- [x] 8.3 Revise README, CHANGELOG, and the lambda-mapping design/specification artefacts for lambda-first resolution and asynchronous partial handling; verify documented examples match the implementation.

## 9. Filesystem Partial Containment

- [x] 9.1 Restrict filesystem partial fallback to non-traversing relative names whose resolved files remain beneath the configured partial root; preserve a symlinked root while rejecting escaping nested symlinks, and cover each case with pytest.
