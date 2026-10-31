# Spec Delta

## MODIFIED Requirements

### Requirement: Existing falsey-value rendering remains compatible

The renderer SHALL retain established behaviour for `0`, `False`, empty strings, empty collections, and custom falsey values across interpolation, unescaped interpolation, normal sections, and inverted sections. A callable SHALL retain its existing lambda treatment before iterator handling, and Chevron SHALL not invoke it merely to decide inverted-section selection. When `Extension.INVERTED_ITERATORS` is enabled, a recognised synchronous iterator SHALL be a streaming section source within its active render frame. An empty source SHALL select an inverted section, and a first item observed by that check SHALL remain available to a later ordinary section in the same frame. A source SHALL not be traversed again after an ordinary section exhausts it. When the extension is disabled, Chevron SHALL retain its existing iterator section behaviour.

#### Scenario: Numeric zero and false interpolate unchanged

- **WHEN** an interpolation resolves to `0` or `False`
- **THEN** it renders using Chevron's existing string conversion behaviour

#### Scenario: Private falsey-value attributes are ignored

- **WHEN** a custom falsey value exposes `_CHEVRON_return_scope_when_falsy`
- **THEN** Chevron does not inspect or honour that attribute and applies ordinary falsey rendering behaviour

#### Scenario: Callable iterator retains lambda treatment

- **WHEN** an inverted section resolves to a callable that also implements `Iterator`
- **THEN** Chevron does not invoke or probe it for inverted selection, and a following ordinary section retains its established lambda behaviour

#### Scenario: Empty value controls an inverted section

- **WHEN** an inverted section resolves to an empty value
- **THEN** its body renders according to existing inverted-section semantics

#### Scenario: Empty iterator controls an inverted section

- **WHEN** `Extension.INVERTED_ITERATORS` is enabled and an ordinary section and its inverted section resolve to a synchronous iterator with no yielded items
- **THEN** the ordinary section renders no body and the inverted section renders its body

#### Scenario: Iterator peek preserves an ordinary section item

- **WHEN** `Extension.INVERTED_ITERATORS` is enabled and an inverted section checks a synchronous iterator that later supplies an item to an ordinary section
- **THEN** the inverted section is skipped and the ordinary section renders that first item

#### Scenario: Exhausted iterator does not restart

- **WHEN** `Extension.INVERTED_ITERATORS` is enabled and an ordinary section exhausts a recognised synchronous iterator and a later ordinary section resolves it
- **THEN** the later ordinary section renders no body

#### Scenario: Repeated inverted sections retain the initial iterator result

- **WHEN** `Extension.INVERTED_ITERATORS` is enabled and repeated inverted sections resolve the same synchronous iterator name in one frame before an ordinary section
- **THEN** they use the initial empty or non-empty result and the ordinary section retains every item from the initially examined source

#### Scenario: Exhausted non-empty iterator does not select an inverted section

- **WHEN** `Extension.INVERTED_ITERATORS` is enabled and an ordinary section exhausts a synchronous iterator that yielded one or more items and a later inverted section resolves the same iterator
- **THEN** the inverted section skips its body

#### Scenario: Async rendering handles a synchronous empty iterator

- **WHEN** `Extension.INVERTED_ITERATORS` is enabled and `async_render()` resolves an ordinary section and its inverted section to a synchronous iterator with no yielded items
- **THEN** it renders the inverted section body using the same behaviour as `render()`
