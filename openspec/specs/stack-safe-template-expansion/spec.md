# stack-safe-template-expansion Specification

## Purpose

Define reliable expansion of finite nested templates independently of the host
runtime's recursive call-stack depth.

## Requirements

### Requirement: Finite nested expansion is stack-safe

Chevron SHALL render a finite chain of nested template expansions without
failing solely because its nesting exceeds the host runtime's recursive
call-stack depth. This applies to public synchronous and asynchronous renders
for engine-owned partial and lambda-result expansion. Recursion initiated by a
caller through a compatibility callback remains caller-controlled.

#### Scenario: Deep synchronous partial expansion

- **WHEN** a synchronous render expands a finite chain of nested partials deeper than the host runtime's normal recursion limit
- **THEN** it returns the same rendered text that the equivalent shallow expansion produces

#### Scenario: Deep asynchronous lambda expansion

- **WHEN** an asynchronous render expands a finite chain of templates returned by supported lambda protocols deeper than the host runtime's normal recursion limit
- **THEN** it returns the expected rendered text without a recursion-depth failure

#### Scenario: Cyclic engine-owned expansion fails with a bounded error

- **WHEN** a partial or lambda result recursively expands itself without a finite end
- **THEN** Chevron raises a bounded `RecursionError` rather than consuming unbounded memory

### Requirement: Nested expansion preserves rendering context

Chevron SHALL preserve the active scope chain, delimiter context, indentation,
and configured lambda behaviour as finite nested expansions resume their
parent template.

#### Scenario: Nested expansion resumes its parent context

- **WHEN** a partial or lambda-produced template completes inside a section that uses nested scopes and delimiter changes
- **THEN** the remaining parent template renders with the scope, delimiters, indentation, and lambda behaviour established before that nested expansion
