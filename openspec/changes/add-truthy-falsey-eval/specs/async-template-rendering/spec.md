# Spec Delta

## ADDED Requirements

### Requirement: Async conditional sections preserve asynchronous iterator items

When the conditional-section extension is enabled and `async_render()` resolves a conditional section to an unsized asynchronous iterable, Chevron SHALL await no more than one item to determine whether it is empty. Falsey values, callables, and sized asynchronous iterable values SHALL use their ordinary truthiness without probing. A first observed item SHALL remain available to a later ordinary section in the same active render frame.

#### Scenario: Empty async iterator skips a conditional section

- **WHEN** an async conditional section resolves to an empty asynchronous iterator
- **THEN** Chevron renders no conditional-section body

#### Scenario: Non-empty async iterator selects a conditional section and preserves its first item

- **WHEN** an async conditional section resolves to a non-empty asynchronous iterator and an ordinary section later references it in the same active render frame
- **THEN** the conditional body renders once and the ordinary section renders every source item in order

#### Scenario: Probed re-iterable async source continues through one cursor

- **WHEN** a conditional section probes a re-iterable asynchronous source
- **THEN** later ordinary sections using the same lookup name continue through the retained cursor rather than starting a fresh traversal
