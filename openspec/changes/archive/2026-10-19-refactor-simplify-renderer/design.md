# Design

## Context

The inspected `renderer.py` combines decorators, lookup, filesystem loading, context state, protocol dispatch, section collection, and output assembly. `_render_inner` creates nested helpers on each invocation, repeats the lambda-first lookup in three tag paths, collects section bodies independently for callables and iterables, and forwards the same partial configuration through every recursive call. `_render` already restores scope-list contents in `finally`; this is valuable existing behaviour, not a missing feature.

The existing tests cover mapping precedence and rejection, falsey callables, decorator metadata and binding, delimiter changes, temporary callback data, and recovery after recursive failure. `scripts/benchmark.py` exercises only ordinary iterable sections. Python 2 output branches remain despite the Python 3.11 minimum.

## Goals / Non-Goals

Make mode-dependent decisions in a small policy selected once, centralise recursion and body collection, and make ownership of mutable state explicit. Preserve current public rendering results and error behaviour.

Do not fix dotted-name precedence here, update fixtures, add inheritance or dynamic names, advertise a package-level renderer-class API, infer callback signatures, add async execution, introduce a full template AST, or change warning delivery. These would obscure whether the refactor preserves behaviour.

## Decisions

### One composed renderer, rather than subclasses of the engine

Keep `chevron.render(...)` as the primary entry point. It constructs `ChevronRender`, configuration, invocation state, and an initial frame. The class deliberately has no leading underscore, allowing potential direct use from its defining module, but is not re-exported or advertised in `chevron/__init__.py` or added to package `__all__`. The engine owns bound operations for interpolation, sections, partials, and recursive rendering. Its explicit tag dispatch remains: tag kinds represent real language operations, and replacing every branch with a class would add indirection without removing semantic complexity.

Use composition for the two callable-source policies. A private structural `Protocol` describes their shared resolution operation; concrete explicit and permissive policies need no common implementation base class. Do not use runtime protocol checks. A whole-renderer subclass hierarchy would multiply combinations because each policy supports all three lambda protocols.

### Actual variants and their boundaries

| Variation | Selection | Responsibility |
| --- | --- | --- |
| Explicit callable source | `lambdas is not None`, including `{}` | Validate and snapshot mapping; resolve complete mapped names first; reject callable data and callable traversal with existing warnings |
| Permissive callable source | Omitted `lambdas` or `None` | Existing lazy scope lookup and callable traversal; no eager walk or extraction of template data |
| Interpolation lambda | `@func` in interpolation | Call with no arguments; render returned source using configured defaults, empty padding, no compatibility cache; then apply escaping |
| Standard section lambda | `@section` in a section | Call with exact enclosed source; render returned source with opening delimiters and current padding, without compatibility cache |
| Compatibility section lambda | `@compat` or undecorated callable in a section | Supply reconstructed compatibility text and render callback; replay compatibility tokens only through that callback; append returned text directly |
| Ordinary section value | Non-callable lookup result | Preserve scalar, falsey, sequence and iterator semantics; callable dispatch precedes iterable or truthiness handling |
| Input representation | Source/file-like input or existing token sequence | Adapt once at the input boundary; retain two-item public tokens and three-item source-bearing tokens |
| Partial source | Mapping first, optional filesystem fallback | One loader with current precedence and containment rules, not separate rendering modes |

Escaping, inverted sections, delimiters and padding are tag semantics or frame state, not additional policy variants. Inverted sections must not execute lambdas. Preserve current falsey callable behaviour there, even where it differs from normal callable sections.

### Resolution retains provenance and exception boundaries

Policies provide one `resolve(name, frame, value_handler)` operation returning the resolved value and whether it came directly from the supplied mapping. This provenance is necessary: an undecorated callable in permissive interpolation is stringified without invocation, while the same callable supplied explicitly produces empty interpolation. Decorated callables used with incompatible tags also retain their existing empty result.

Keep common scope traversal in `_get_key` initially. The consumer's normalisation handler must remain inside its existing exception boundary: `test_coercion_errors_fall_back_to_later_scope` requires equality/truthiness `ValueError` to permit later-scope lookup. Moving all conversion after lookup would regress that behaviour. Explicit mapping hits continue to bypass template-data traversal and data normalisation. Do not change callable-attribute filtering, missing-value warnings, literal dotted mapping keys, or the known whole-chain dotted fallback in this refactor.

### Lambda invocation handlers are independent of source policy

Select a handler from decorator metadata and tag kind, with undecorated section callables selecting the compatibility handler. Use a small dispatch table of handler functions or bound methods; separate classes for stateless handlers are unnecessary. Retain `_LambdaDefinition` metadata, descriptor binding and public decorator exports.

Share the None-result diagnostic, but preserve distinct conversion rules: standard lambda results stringify non-string values before recursive rendering; compatibility results are appended directly and retain existing errors for incompatible types. Never catch callback `TypeError` to infer arity or retry invocation.

### Separate configuration, invocation state and frames

- Configuration holds partial lookup settings, warning preference, and render-default delimiters. Select and retain the source policy alongside it. Preserve caller-owned mapping behaviour except for the already-snapshotted lambda mapping.
- Invocation state holds the compatibility token cache. Tokenizer diagnostics remain private to each tokenisation call. Each public render creates fresh state; recursion shares its compatibility cache deliberately. Compatibility callback input first follows the public falsey non-text empty-output contract, then uses the cache only for text source.
- A frame carries scopes, active delimiters and padding for one recursive rendering operation. Local output and token cursors remain invocation locals, not mutable renderer attributes.

Retain the existing scope restoration guard and child-scope construction semantics in the first extraction. Do not deep-copy data, freeze scopes, or assume a scope must be a dict. Compatibility callbacks capture their frame and the bound engine operation, not a module-level active context or a mutable engine-wide current-frame pointer. Truthy temporary callback data prepends a child scope; falsey temporary data retains the caller's scopes as today. Every recursive entry restores incoming scope-list contents after success or failure.

Independent public renders remain isolated for concurrent calls, including calls from inside a lambda. This does not promise simultaneous use of one captured compatibility callback across threads; introducing that guarantee would require a separate lifecycle contract.

### Centralise section collection and recursive entry points

The renderer owns template input reading and always supplies text to the tokenizer. Remove the tokenizer's file-like `.read()` support directly, without a wrapper or alternative compatibility entry point. Preserve file-like input support on `render()`, including caller ownership and read-error propagation. Preserve historic empty output for falsey non-text templates at the public render boundary. Move tests of reading failures to the renderer boundary. Existing direct tokens must be non-string sequences containing exactly two or three values; list and tuple tokens remain supported. This input-contract narrowing is explicitly authorised; the behaviour-preservation goal applies to rendering, not the removed tokenizer reader convenience.

Introduce one section-body collector returning the enclosed token sequence and opening/ending delimiter state. Callable and iterable paths share matching logic, including nested sections and inverted sections with the same name. Derive exact source and compatibility reconstruction from that body only when their respective handlers need them. Preserve fallback reconstruction for public two-item tokens and source-only comments/whitespace for standard lambdas. Compatibility reconstruction keeps its existing cache key and filtered token representation.

Keep scalar sections on their current streaming path initially. A full AST would change parsing timing, memory use and error timing unnecessarily. Partial and lambda handlers use bound recursive operations with explicit frame overrides, eliminating repeated configuration lists and the engine-wide `use_token_cache` switch. Only the compatibility callback entry point checks the compatibility cache.

Default delimiters remain distinct from current lexical delimiters. Partials and interpolation returns restart with configured defaults; standard section returns use opening delimiters. Consuming or skipping a body must still propagate lexical delimiter changes to its enclosing frame.

### Simplification and evidence

Remove unreachable Python 2 conversion branches and use Python 3 strings while preserving supported output conversion. Keep private helpers grouped by responsibility; split into private modules only when dependencies remain acyclic and the split makes ownership clearer. Retain public import locations and `__all__` order.

Use existing behavioural and pinned specification tests as the baseline. Add only missing public-API cases for extraction-sensitive combinations, preferably parametrised: both policies with each applicable lambda protocol, recursive exception recovery, diagnostics, token input forms and independent concurrent renders. Do not assert private class shapes or mock internal dispatch. Extend the benchmark with ordinary, explicit-empty, explicit/permissive callable, partial and nested-render scenarios; compare identical inputs before and after, reporting repeated timings rather than adding a fragile timing gate.

## Risks / Trade-offs

- Policy abstraction can move exception handling and change lookup results → retain `_get_key`'s conversion boundary and the existing coercion regression tests.
- Shared body collection can alter delimiters, cache reconstruction or whitespace → preserve exact protocol differences and exercise both token representations.
- Binding recursive methods can accidentally share active state → keep frame/output local and allocate invocation state per public call.
- New objects and dispatch calls can cost time on simple templates → select policies once, avoid per-token class allocation, and compare representative benchmarks.
- Existing specs sometimes call compatibility reconstruction “raw source” → retain tested behaviour and explain the distinction here; do not silently change it during extraction.

## Migration Plan

Land small extractions against the current pinned fixture baseline, keeping the existing public adapter throughout. Revert an extraction if behavioural comparison reveals a regression. Complete this refactor before applying `update-to-latest-mustache`; revisit that change's implementation design against the new internal structure without reducing its full-conformance objective.
