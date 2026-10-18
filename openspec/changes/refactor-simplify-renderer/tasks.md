# Tasks

## 1. Establish behavioural and performance comparisons

- [x] 1.1 Add only missing parametrised public-API characterisation cases for the policy/protocol combinations in the design, including undecorated interpolation and incompatible decorated tags; verify expected output and invocation counts against the existing engine.
- [x] 1.2 Extend `scripts/benchmark.py` with ordinary, explicit-empty, callable, nested callback and partial workloads, each checking expected output; record repeated baseline timings using identical inputs for later comparison.

## 2. Introduce the composed engine and state ownership

- [x] 2.0 Move file-like template reads into the renderer and remove tokenizer reader support without a wrapper; update tokenizer documentation and relocate read-failure coverage to the renderer, verifying text/file rendering equivalence and caller-owned reader preservation.
- [x] 2.1 Move execution into the composed ChevronRender class, without a leading underscore or package-level re-export, while retaining chevron.render as the primary entry point and preserving its signature and existing exports; consolidate render configuration and verify public API and CLI tests remain unchanged.
- [x] 2.2 Separate invocation state from local frames and bind recursive entry points; retain scope restoration and temporary-data semantics, documenting ownership beside the private types and verifying nested failure recovery and independent concurrent render output.

## 3. Extract callable-source policies

- [x] 3.1 Define a private resolution Protocol and explicit/permissive implementations selected once at public entry; consolidate repeated name lookup while preserving mapping provenance, validation, snapshotting, rejection diagnostics and lazy traversal, verified by lambda-mapping tests.
- [x] 3.2 Retain normalisation within the existing lookup exception boundary and current inverted-section behaviour; verify falsey callable, coercion-error fallback, missing-value and callable-traversal regression cases.

## 4. Consolidate bodies and lambda dispatch

- [x] 4.1 Extract one collector for callable and iterable section bodies, with opening/ending delimiters and protocol-specific source reconstruction; verify nested same-name sections, comments, standalone whitespace and both token tuple formats.
- [x] 4.2 Extract interpolation, standard-section and compatibility handlers selected by tag and declared metadata; verify invocation counts, binding, None diagnostics, result conversions, delimiter selection and padding with the existing protocol tests and any missing public-API cases.
- [x] 4.3 Restrict compatibility cache lookup to the bound compatibility callback entry point and remove the general rendering cache-mode flag; verify callback replay and standard/interpolation result rendering retain existing output.

## 5. Complete engine simplification

- [x] 5.1 Consolidate recursive partial and iterable rendering through the engine, retaining the existing partial loader policy; verify mapped, filesystem, containment, delimiter and indentation tests.
- [x] 5.2 Remove unreachable Python 2 branches and obsolete forwarding helpers, retaining supported string conversions and import locations; verify the current behavioural and pinned conformance suites pass and compare the benchmark scenarios with their recorded baseline.
- [x] 5.3 Preserve falsey non-text public template inputs as empty output, explicitly reject malformed direct token tuples, and remove residual state-owned tokenizer forwarding; update behavioural coverage and design ownership notes.

Routine repository checks, OpenSpec verification, review and Git delivery remain workflow hygiene rather than tracked implementation tasks. The subsequent Mustache conformance change retains responsibility for new syntax and the dotted-name behaviour correction.
