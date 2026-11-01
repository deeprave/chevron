# Design

## Context

See [proposal.md](proposal.md) for motivation and the conditional-section contract. Chevron already has process-wide extension configuration and private render-frame iterator state for enhanced iterator behaviour. A conditional section needs the same non-consuming observation for streaming sources, but it must not inherit positional metadata or ordinary-section scope changes.

## Goals / Non-Goals

**Goals:**

- Add one opt-in truthiness-only section form with equivalent synchronous and asynchronous behaviour.
- Preserve a generator item observed while testing its emptiness for a later ordinary section in the same render frame.
- Keep the conditional extension independent from enhanced iterator metadata and avoid render-call configuration.

**Non-Goals:**

- Add `else` syntax, negated conditional tags, predicates, comparisons, or expression evaluation.
- Make conditional sections standard Mustache syntax.
- Materialise, copy, or decorate application collections.
- Change ordinary section, inverted section, or lambda semantics.

## Decisions

### Reserve the conditional-section token only when enabled

The tokenizer recognises an opening `?` section only when `Extension.CONDITIONAL_SECTIONS` is enabled. Otherwise, `?` remains part of an ordinary variable name. When an apparent paired conditional section reaches an unmatched or mismatched closing tag, Chevron logs a warning that identifies the opt-in before raising its ordinary structural `ChevronError`.

### Evaluate truthiness without adopting the value as context

Conditional dispatch resolves its name once and selects or skips the collected body. It does not create a child scope from the resolved value, does not repeat the body, and does not run callables. This makes `{{?value}}` a direct test of a supplied value rather than another variant of `{{#value}}`.

### Reuse frame-local iterator observation only when a stream is tested

For synchronous iterators, conditional dispatch uses the existing private state held on the supplying render frame to observe at most one item. For asynchronous iterables, `async_render()` performs the equivalent awaited observation. Ordinary section dispatch must reuse a pending state created by a conditional check even if enhanced iterator metadata is disabled, so a later `{{#value}}` receives the observed first item. This remains local to the supplying frame and does not introduce a registry or cross-frame sharing.

The conditional path follows the enhanced-iterator truthiness policy: ordinary and sized values use their normal truthiness and do not need a probe, while unsized streams use one buffered observation. Synchronous rendering retains its existing error for asynchronous iterables; `async_render()` owns their observation.

### Keep conditional configuration independent

Add `CONDITIONAL_SECTIONS` as a distinct `Extension` member. It participates in `ALL` and the existing startup-only immutable configuration, but it does not implicitly enable `ENHANCED_ITERATORS`. Applications choose each extension according to template compatibility requirements.

## Risks / Trade-offs

- [A conditional test advances a one-shot iterator] → Retain its one observed item in the existing frame-local state for normal later iteration.
- [A template uses paired `?` syntax while the extension is disabled] → Keep `?` as an ordinary variable prefix, log a configuration warning when its closing tag proves structurally unmatched, then raise the ordinary structural error.
- [A callable's boolean value is surprising] → Do not invoke it; conditional sections intentionally test the callable object itself.
- [Async source observation introduces a suspension point] → Await only the one-item observation and do not parallelise rendering.

## Migration Plan

No migration is required. Applications must explicitly include `Extension.CONDITIONAL_SECTIONS` in their one-time startup configuration before templates use conditional-section syntax. Without it, `?` remains available in ordinary variable names.
