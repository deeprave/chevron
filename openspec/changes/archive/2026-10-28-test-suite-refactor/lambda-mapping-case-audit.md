# Explicit lambda-mapping case audit

## Convert to shared lambda cases

- explicit mapping supplies a section callable without template data;
- explicit dotted mapping remains available inside a partial;
- explicit mapping remains available in an iterable section scope;
- explicit mapping works with `scopes=`;
- an explicit mapping takes precedence over scope lookup;
- a registered callable is truthy in an inverted section;
- separately accessed bound methods are recognised as the same registered
  callable;
- an explicit mapping can supply a bound method without template data;
- an explicit mapping can supply a class-bound method;
- `ChainMap` and `MappingProxyType` lambda mappings are accepted.

## Keep focused

Keep tests which observe callable invocation or non-invocation, warnings,
invalid mappings, snapshot semantics, rejected values, callable-internal
traversal, and legacy implicit callback behaviour. `LambdaRenderCase` always
supplies an explicit mapping and must not grow a compatibility-mode switch.
