# Spec Delta

## MODIFIED Requirements

### Requirement: Async section iteration preserves order

Async rendering SHALL support asynchronous iterables as section values, awaiting each item and rendering it in source order. It SHALL not implicitly parallelise lambdas, partials or section items. Plain awaitables in template data SHALL not be implicitly awaited as lambdas. A callable SHALL retain its existing lambda treatment before asynchronous-iterable handling, and Chevron SHALL not invoke it merely to decide inverted-section selection. When `Extension.INVERTED_ITERATORS` is enabled, an asynchronous iterable SHALL be a streaming section source within its active render frame. An empty source SHALL select an inverted section, and a first item observed by that check SHALL remain available to a later ordinary section in the same frame. A source SHALL not be traversed again after an ordinary section exhausts it. When the extension is disabled, async rendering SHALL retain its existing asynchronous-iterable section behaviour.

#### Scenario: Async iterable section

- **WHEN** a section value yields items asynchronously
- **THEN** its body renders once per item in yield order, including zero times for an empty iterable

#### Scenario: Async iterable in an inverted section

- **WHEN** `Extension.INVERTED_ITERATORS` is enabled and an inverted section references an asynchronous iterator
- **THEN** Chevron awaits at most one item to establish whether it is empty, renders the inverted body when it is empty, and preserves a non-empty first item for ordinary rendering

#### Scenario: Callable async iterable retains lambda treatment

- **WHEN** an inverted section resolves to a callable that also implements `AsyncIterable`
- **THEN** Chevron does not invoke or probe it for inverted selection, and a following ordinary section retains its established lambda behaviour

#### Scenario: Async iterator peek preserves an ordinary section item

- **WHEN** `Extension.INVERTED_ITERATORS` is enabled and an inverted section checks an asynchronous iterator that later supplies an item to an ordinary section
- **THEN** the inverted section is skipped and the ordinary section renders that first item

#### Scenario: Exhausted non-empty async iterator does not restart or select an inverted section

- **WHEN** `Extension.INVERTED_ITERATORS` is enabled and an ordinary section exhausts an asynchronous iterable and a later ordinary or inverted section resolves it
- **THEN** the ordinary section renders no body and the inverted section skips its body

#### Scenario: Async iterator cancellation remains application-owned

- **WHEN** cancellation interrupts an awaited caller-owned asynchronous iterator
- **THEN** Chevron does not close it itself, but the application SHALL not assume the iterator remains reusable

#### Scenario: Async rendering preserves a synchronous iterator cursor

- **WHEN** `Extension.INVERTED_ITERATORS` is enabled and `async_render()` has buffered a synchronous iterator after an inverted section check
- **THEN** its following ordinary section renders the buffered source item before the remaining source items
