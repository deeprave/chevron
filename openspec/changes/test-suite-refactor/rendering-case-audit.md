# Rendering-case audit

## Selection rule

A scenario belongs in a shared rendering-case collection when it is fully
described by source template text, ordinary render data and partial mappings,
and expected output. The same named scenario can then run through
`chevron.render()` and `chevron.async_render()` under each enabled AnyIO
backend.

This is not a claim that every test which calls `render()` should become a
case. A focused test remains the clearer regression guard where it verifies
an exception, log record, resource ownership, callback invocation or
arguments, scheduling, cancellation, or an alternate public input type.

## Convert to shared source-template cases

### Values, scopes, and lookup

Create a small `scope_cases.py` collection from these observable output
scenarios:

- `test_top_level_sequence_uses_the_current_context_name`
- `test_nested_dotted_sections_restore_the_parent_scope`
- `test_unicode_sequence_items_render_through_the_current_context_name`
- `test_dotted_lookup_resolves_public_attributes_without_traversing_scalars`
- `test_nested_sections_with_the_same_name_restore_the_outer_scope`
- `test_empty_scopes_are_a_valid_empty_context`
- `test_unescaped_current_scope_in_inverted_section_uses_the_parent_scope`
- `test_true_current_scope_is_not_an_inverted_section_marker`
- `test_nested_inverted_sections_resolve_current_scope`
- `test_nested_inverted_sections_resolve_current_scope_sections`
- `test_dotted_sequence_lookup_resolves_indices_or_renders_empty`
- `test_dotted_lookup_does_not_fall_back_after_its_first_name_resolves`
- `test_missing_later_dotted_name_does_not_render_its_resolved_prefix`
- `test_missing_later_dotted_name_does_not_select_a_dynamic_partial`
- `test_numeric_lookup_falls_back_past_a_scalar_section_frame`
- `test_numeric_lookup_falls_back_past_an_inverted_section_marker`
- `test_namedtuple_fields_are_template_values`
- `test_public_class_attributes_are_template_values`
- `test_builtin_callable_attributes_are_not_template_values`
- `test_custom_falsey_values_can_opt_into_rendering`
- `test_ordinary_falsey_values_retain_tag_behaviour`
- `test_missing_and_empty_sections_use_ordinary_falsey_behaviour`
- `test_coercion_errors_fall_back_to_later_scope`
- `test_dotted_lookup_does_not_fall_back_after_value_normalisation_fails`

The two coercion-normalisation scenarios use small local value classes. Keep
those classes adjacent to this collection rather than adding an arbitrary
object-construction hook to `RenderCase`.

### Ordinary and inverted sections

Create `section_cases.py` for output-only section behavior:

- `test_inverted_sections_evaluate_mixed_sequence_items_independently`
- `test_iterable_section_collects_nested_inverted_sections_with_the_same_name`
- `test_skipped_and_iterated_sections_propagate_delimiter_changes`

The first two groups intentionally overlap where a scenario protects both
lookup and section behavior; each case should have one durable home, chosen by
its dominant behavior. Avoid duplicating the same case across collections.

### Whitespace, standalone tags, delimiters, and line endings

The inheritance collection already covers most parent/block indentation and
LF, CRLF, and CR behavior. Add the remaining Chevron-owned source cases to
that collection or a narrowly named whitespace collection:

- `test_partial_resets_to_render_default_delimiters_after_a_change`
- the output-only portions of `test_skipped_and_iterated_sections_propagate_delimiter_changes`

Keep the existing inheritance cases as the canonical place for inheritance
indentation, block whitespace, and parent line-context behavior. Do not copy
vendored Mustache examples into Chevron-owned cases merely to increase count.

### Existing async examples that should use the shared collections

Where their inputs are ordinary source/data/partials/output, replace parallel
async examples with the shared sync/async case runners. Initial candidates
are the async counterparts of the selected scope and section cases, including
empty scopes, current-context interpolation, inverted sections, dotted and
numeric lookup fallback, and missing dynamic partial selection. The runner
already provides asyncio and Trio coverage, so no async-only duplicate is
needed for these cases.

## Keep as focused public-contract tests

### Template inputs, errors, and diagnostics

Keep tokenizer errors, malformed token sequences, binary/readable templates,
CLI entry points, warnings, logger routing, log level filtering, and error
location checks focused. Their result is not represented by rendered output
alone.

### Readers, filesystem, and task lifecycle

Keep filesystem partial precedence/containment, symlink handling, reader
ownership, blocking-I/O behavior, iterator failures, cancellation, task
scheduling, and concurrent-render isolation focused. These tests need a
controlled resource or lifecycle observation.

### Lambda and callback protocols

Keep decorator metadata, protocol selection, mapping authorisation, callback
arguments, invocation counts, returned-awaitable behavior, warning behavior,
and compatibility callbacks focused. Some lambda scenarios produce text, but
their durable contract includes how the callable is selected or invoked; a
generic lambda factory in `RenderCase` would hide that contract and broaden
the case framework without enough benefit.

### Generative properties and depth bounds

Keep Hypothesis properties and deep/cyclic expansion tests focused. Their
coverage depends on generated input or a deliberately large construction,
neither of which is a readable fixed rendering fixture.
