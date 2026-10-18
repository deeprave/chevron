# Verification: refactor-simplify-renderer

## Summary

| Dimension | Result |
| --- | --- |
| Completeness | 12/12 implementation tasks complete |
| Correctness | 293 tests pass with warnings treated as errors; pinned conformance fixtures unchanged |
| Coherence | Composed engine, source policies, protocol handlers and state ownership match the agreed design |

No implementation findings remain from this verification. Delta-spec verification is intentionally omitted because this behaviour-preserving change declares `skip_specs: true`; the authorised tokenizer input narrowing is recorded in the design. Existing lambda-mapping and value-resolution requirements remain covered by their regression suites. This verification is not an independent code review.

## Evidence

- `src/chevron/renderer.py`: `ChevronRender` is composed with `_SourcePolicy`, with `_ExplicitSource` and `_PermissiveSource` selected once by public `render`. Package exports remain unchanged.
- `_RenderConfig`, `_RenderState` and `_RenderFrame` separate settings, shared invocation state and recursive scope/delimiter/padding inputs. Render-local token cursors and output are not stored as mutable engine-wide active state.
- `_collect_section` serves callable and iterable sections. `_SectionBody` builds source or compatibility text only when needed. Only `compatibility_render` reads the compatibility cache.
- `_get_key` retains normalisation inside its exception boundary. Existing coercion fallback, falsey callable, temporary-scope recovery and warning tests pass.
- Tokenizer reading was removed without a wrapper. `tests/test_file_entry_points.py` verifies renderer reader-error propagation, current-position reading and caller ownership. Tokenizer documentation now describes text input.
- `tests/test_render_isolation.py` verifies independent concurrent renders and both token representations through public behaviour. Existing lambda tests were parametrised for both source policies and incompatible tags rather than duplicated.
- A one-off baseline comparison covered 264 combinations of source policy, callable protocol, token representation, nested sections, partials and delimiter changes; outputs, callback inputs and warnings matched the pre-refactor renderer.
- Repeated benchmark evidence is recorded in benchmark.md. No timing gate was introduced.

## Checks

Pytest passes all 293 cases with `-Werror`; baseline was 280 cases. Overall branch-aware coverage is 97% (previously 94%). Ruff lint/format, Ty, Vulture, Bandit, OSVCheck and packaging validation pass. Both wheel and source distribution build. Strict OpenSpec validation and whitespace checks pass.

The complete pre-commit run is not wholly green: `no-commit-to-branch` rejects the current `main` checkout. This is a delivery-policy guard, not an implementation failure. No commit, push, branch change or archive was performed.
