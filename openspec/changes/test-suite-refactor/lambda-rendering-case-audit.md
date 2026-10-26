# Lambda rendering-case audit

## Selection rule

A lambda scenario belongs in `LambdaRenderCase` when its complete contract is
a template, ordinary render data and partial mappings, a declared lambda
mapping, and expected output. The callable mapping is made fresh for each
render by a named private factory.

## Shared sync and async cases

- function expansion resumes parent delimiters;
- declared function escaped and unescaped interpolation;
- declared function rendering in an indented partial;
- declared section uses its opening delimiters after its body changes them;
- declared function takes precedence over template data;
- declared function remains available in a nested partial;
- declared section returning a partial uses render-default delimiters;
- declared functions remain available in recursively rendered text.

These use synchronous declared functions and run through the sync, asyncio,
and Trio runners.

## Async-only cases

- declared async interpolation, section, and compatibility protocols;
- async function expansion resumes parent delimiters;
- the async renderer awaits an awaitable returned by a synchronous declared
  function;
- async declared function rendering in an indented partial;
- async compatibility callback retains parent data when temporary data is
  falsey;
- a synchronous compatibility callback forwards the async render callback.

These join only the async collection. They run under asyncio and Trio and are
not passed to `chevron.render()`.

## Focused tests retained

Keep tests that observe callback source or arguments, call counts, warning
records, decorator metadata, protocol selection or rejection, explicit mapping
authorisation, synchronous rejection of awaitables, failure propagation, and
compatibility recovery from an inner failure. Those contracts require more
than final rendered output.
