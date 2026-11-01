# Spec Delta

## ADDED Requirements

### Requirement: Conditional sections determine synchronous iterator emptiness without loss

When the conditional-section extension is enabled and a conditional section resolves to an unsized synchronous iterator, Chevron SHALL observe no more than one item to determine whether the iterator is empty. Falsey values, callables, and sized values SHALL use their ordinary truthiness without probing. A first observed item SHALL remain available to a later ordinary section in the same active render frame.

#### Scenario: Empty iterator skips a conditional section

- **WHEN** a conditional section resolves to an empty synchronous iterator
- **THEN** Chevron renders no conditional-section body

#### Scenario: Non-empty iterator selects a conditional section and preserves its first item

- **WHEN** a conditional section resolves to a non-empty synchronous iterator and an ordinary section later references it in the same active render frame
- **THEN** the conditional body renders once and the ordinary section renders every source item in order

#### Scenario: Later iteration uses the same lookup name

- **WHEN** a conditional section probes an iterator through a dotted lookup name
- **THEN** a later ordinary section using that identical dotted lookup name receives the retained first item
