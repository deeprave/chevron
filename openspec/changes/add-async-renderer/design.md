# Design

## Context

This design targets the completed `refactor-simplify-renderer` architecture, which is presently proposed rather than implemented. The current renderer calls file-like `read()` through tokenisation, performs `Path.resolve`, file open/read/close in `_get_partial`, and writes warnings directly to stderr. Lambdas, iterable sections and recursive calls all execute synchronously. The refactor supplies a private engine, separate source policies and invocation handlers, common section collection, and explicit configuration/state/frame ownership.

## Goals / Non-Goals

Provide a genuine awaitable execution path with shared pure semantics, async recursion and I/O, and independent asyncio/Trio testing. Preserve synchronous rendering and the existing public decorators.

No library-owned loop, blocking portal, automatic parallel template evaluation, async CLI, network fetching, streaming output, or automatic awaiting of arbitrary template-data values. Runtime portability means AnyIO-supported asyncio and Trio backends; backend-specific callbacks remain the application's responsibility.

## Decisions

### Two execution engines sharing pure operations

The prerequisite refactor makes the tokenizer text-only and removes its file-like input support without a wrapper. Both engines own input reading and pass the resulting content directly to that same tokenizer; this change adds async reading at the renderer boundary only.

Add a private async engine beside the refactored synchronous engine. Both consume the same configuration, source policies, token representation, body collector, normalisation and escaping helpers. Async recursion awaits interpolation results, sections, partials and callbacks explicitly. Do not override synchronous methods with awaitable methods behind a misleading common return type or add an `is_async` flag to the synchronous loop. Accept small duplication of control flow where `await` changes execution, and enforce parity with shared behavioural cases.

Public `async_render` mirrors the parameters of `render`, returning a complete string. Source and token input preparation happens before shared pure tokenisation; the tokenizer never receives an unread file in the async path. Preserve current semantics for direct token sequences. New syntax from `update-to-latest-mustache`, if already implemented, must participate in async recursion too. The refactor is the hard prerequisite; conformance can land before or after this change, with parity maintained by whichever lands second.

### AnyIO dependency and runtime ownership

Offer an `async` extra containing AnyIO, and include that extra plus Trio in the development environment. Export `async_render` without importing AnyIO eagerly; awaiting it without the extra raises a clear installation error. Select a tested compatible AnyIO range during implementation, rather than pinning a transient version in this design. Keep the synchronous dependency footprint unchanged.

Use AnyIO operations inside the caller's running backend. Never call `asyncio.run`, `anyio.run`, construct a loop, or create a portal. AnyIO supplies portable file/thread operations, cancellation scopes and checkpoints. Its file APIs offload blocking OS operations to worker threads; this is non-blocking for the event loop, not a claim of native async filesystem syscalls.

### Await selected callable results, not template data

Resolve names and reject callable template data through the same source policy before invoking anything. Retain `func`, `section`, `compat` and undecorated compatibility section selection. Invoke once; use `inspect.isawaitable` on the returned value and await it once when appropriate. This checks an actual result, not `inspect.signature`, coroutine-function guesses or argument-count inference. It handles decorated async functions, async callable instances and ordinary functions returning awaitables.

Synchronous pure callbacks are supported directly; they must not perform blocking I/O. Automatically offloading every callback would change thread affinity and context access, so callers with blocking callbacks must adapt those operations explicitly using AnyIO. The same responsibility applies to custom mapping access, properties, string conversion and synchronous iterators. Renderer-owned I/O is always adapted. An async function that blocks internally cannot be made non-blocking by the renderer.

After awaiting, preserve each protocol's established result rules: interpolation and standard-section text is rendered recursively, compatibility output is appended directly, and None produces empty output plus the configured diagnostic. Inverted sections do not invoke a callable or await template data. Errors propagate without reinvocation or fallback to a different signature.

### Compatibility rendering callbacks are async

An async compatibility lambda receives `async_render_callback(template, data=None)`, normally used as `return await render(text, temporary_data)`. It preserves the active source policy, configuration, compatibility token cache, defaults and padding. A synchronous callback that simply returns `render(text)` also works because its returned awaitable is awaited; code that concatenates or otherwise consumes that coroutine as a string must migrate. Do not transparently bridge an old blocking callback into a loop. Document this distinction with examples while keeping the existing sync API intact.

Frames used for recursive async calls have independent scope-list containers, sharing underlying application data and the deliberate per-invocation cache. Diagnostic state must be scoped to the recursive branch, not one mutable stack shared across sibling tasks. This prevents awaits and callback-initiated concurrent nested renders from corrupting scope/tokenisation state. Capture the callback's invocation frame rather than an engine-wide current-frame pointer; preserve falsey temporary-data behaviour. No concurrent mutation guarantee is made for caller-owned data objects.

### All renderer-owned I/O has an async boundary

| Operation | Async path |
| --- | --- |
| Native async text reader | Await `read()`; require text and retain caller ownership |
| Ordinary file-like reader | Run blocking `read()` in an AnyIO worker; await an awaitable result if a regular method returns one |
| Filesystem partial | Await root/candidate resolution and UTF-8 read through AnyIO, or offload the complete existing contained file operation as one worker call |
| Missing/rejected/None diagnostics | Produce messages in shared pure logic and await ordered stderr writes through an AnyIO worker |
| Tokenisation and escaping | Shared synchronous CPU work over already-read text |

For reader adaptation, coroutine-method detection is an optimisation: unrecognised synchronous `read` methods are safely invoked in a worker and their result checked for awaitability. Do not pass async readers into the synchronous tokenizer. Read ordinary mapped partial text directly from memory; this change does not expand `partials_dict` into a provider/callback API.

The filesystem adapter retains mapping precedence, `partials_path=None`, suffix handling, relative-name restrictions and resolved containment, including a symlinked configured root. Offloading the complete existing filesystem operation is preferred initially because it preserves one resource ownership boundary and exception behaviour. It does not strengthen the existing path checks against concurrent filesystem replacement.

Synchronous source policies currently emit warnings inline. For async reuse, extract warning production behind a per-operation collector or sink so resolution stays pure; the synchronous engine immediately writes through its sink and the async engine drains through awaited writes at semantic boundaries. Preserve warning text, order and occurrence count. Avoid buffering all warnings until successful completion, which would lose diagnostics on failure.

### Async iteration, checkpoints and cancellation

Support `AsyncIterable` normal sections using `async for`, sequentially rendering each yielded item. Callable dispatch remains first; if an object supports both iteration forms, use asynchronous iteration in the async engine. Inverted sections retain ordinary object truthiness without destructive peeking. Caller-supplied iterators/readers remain caller-owned, including on cancellation; close only resources created by Chevron. Document this so applications can use their own async context managers for generator cleanup.

Add cooperative checkpoints at render entry and bounded token/iteration intervals, including section-body collection, so CPU-only templates permit cancellation and other tasks to progress. Keep the tokenizer synchronous; a single long parsing step or caller computation remains non-pre-emptible. Avoid one await per character and benchmark checkpoint overhead.

Use `finally` for frame and diagnostic cleanup. Propagate cancellation instead of turning it into a missing partial or empty lambda result. Worker-backed reads use non-abandoning cancellation behaviour so opened resources are deterministically closed; cancellation may therefore wait for an OS operation to return, although the event loop stays responsive. Any awaited cleanup requiring protection uses a narrow shield, never a shield around the whole render.

### Behavioural verification across backends

Use AnyIO's pytest plugin with explicit asyncio and Trio backend parametrisation. Run shared renderer cases and all vendored conformance fixtures through both engines; adapt fixture lambda declarations only as necessary, preserving upstream data. Use small async callback tests for every protocol under both source policies, including callables returning awaitables and falsey callable instances.

Use events and task groups to verify ordering, concurrent isolation and suspension rather than timing sleeps. Tests cover file and reader ownership, blocked filesystem work with a progressing sibling task, containment, warning writes, cancellation during readers/lambdas/iteration, recovered recursive errors and sequential output. Exercise pure-text cancellation checkpoints. Preserve the synchronous suite and add an isolated installation/import check without the async extra. Measure representative async workloads without making wall-clock timings a test gate.

## Risks / Trade-offs

- Duplicated execution loops can drift → share semantic helpers and parametrise the same acceptance cases across engines.
- Sync callbacks or custom objects can block → document the non-blocking callback contract and explicit worker adaptation; do not promise to police arbitrary application code.
- Optional imports can break synchronous users → lazy-load the async dependency and verify base installations independently.
- Shared recursive stacks are unsafe across awaits → use branch-owned frames and diagnostic state, with deterministic concurrent tests.
- Filesystem cancellation is not instant → retain resource-safe worker completion and document cancellation latency.

## Migration Plan

Implement after the refactor. Existing consumers continue using `render`; async consumers install the extra, await `async_render`, and migrate compatibility callbacks to await their supplied render operation. Add user-facing examples for all three decorators and both backends without publishing private engine classes. Implementation tasks contain code, tests and their necessary documentation only.

## References

- [AnyIO file I/O](https://anyio.readthedocs.io/en/stable/fileio.html): worker-backed file and path operations.
- [AnyIO testing](https://anyio.readthedocs.io/en/stable/testing.html): pytest plugin and backend fixtures.
- [AnyIO threads](https://anyio.readthedocs.io/en/stable/threads.html): worker execution and cancellation constraints.
