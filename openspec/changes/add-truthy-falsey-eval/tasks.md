# Tasks

## 1. Configure and recognise conditional sections

- [x] 1.1 Add `Extension.CONDITIONAL_SECTIONS` to the immutable global extension mask and `ALL`; verify conditional sections can be enabled without enhanced iterator metadata.
- [x] 1.2 Reserve `{{?name}}…{{/name}}` when enabled and retain `?name` as an ordinary variable when disabled; warn before an apparent paired form reaches its ordinary structural error.
- [x] 1.3 Implement synchronous truthiness-only conditional dispatch without changing scope, repeating collections, or invoking callables; verify behavioural fixtures cover scalar, mapping, collection, missing, and callable values.
- [x] 1.4 Document conditional-section syntax, startup-only opt-in configuration, context preservation, and its compatibility boundary; verify the strict documentation build.

## 2. Preserve streaming source behaviour

- [x] 2.1 Reuse frame-local synchronous iterator observation for conditional and inverted checks and later ordinary sections; verify empty and non-empty generator fixtures retain every yielded item, including nested and partial bodies.
- [x] 2.2 Implement equivalent asynchronous conditional dispatch and source observation under supported AnyIO backends; verify async generator fixtures preserve item order and empty handling.
