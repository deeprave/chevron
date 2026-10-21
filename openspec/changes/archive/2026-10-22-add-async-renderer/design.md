# Design

## Context

This design targets the completed `refactor-simplify-renderer` architecture. The current renderer owns file-like template reads, performs `Path.resolve`, file open/read/close in `_get_partial`, and has a composed engine with separate source policies and invocation handlers, common section collection, and explicit configuration/state/frame ownership. Lambdas, iterable sections and recursive calls otherwise execute synchronously.

## Goals / Non-Goals

Provide a genuine awaitable execution path with shared pure semantics, async recursion and I/O, and independent asyncio/Trio testing. Preserve synchronous rendering and the existing public decorators.

No library-owned loop, blocking portal, automatic parallel template evaluation, async CLI, network fetching, streaming output, or automatic awaiting of arbitrary template-data values. Runtime portability means AnyIO-supported asyncio and Trio backends; backend-specific callbacks remain the application's responsibility.

The change does not expose renderer internals or add a general scheduler/context facade. Async lambdas already run in the caller's active AnyIO-compatible task and can use ordinary AnyIO APIs for application I/O, worker adaptation and cancellation-aware work. The compatibility lambda's supplied recursive-render callback is the only renderer-specific context API needed now. Existing `func` and `section` signatures remain unchanged.

## Decisions

### Two execution engines sharing pure operations

The prerequisite refactor makes the tokenizer text-only and removes its file-like input support without a wrapper. Both engines own input reading and pass the resulting content directly to that same tokenizer; this change adds async reading at the renderer boundary only.

Add a private async engine in `chevron.async_renderer`, separate from the refactored synchronous engine. The package-level `async_render` dispatcher imports that module only when it is awaited. Both engines consume the same configuration, source policies, token representation, body collector, normalisation and escaping helpers. Async recursion awaits interpolation results, sections, partials and callbacks explicitly. Do not override synchronous methods with awaitable methods behind a misleading common return type or add an `is_async` flag to the synchronous loop. Accept small duplication of control flow where `await` changes execution, and enforce parity with shared behavioural cases.

Public `async_render` mirrors the parameters of `render`, returning a complete string. Source and token input preparation happens before shared pure tokenisation; the tokenizer never receives an unread file in the async path. Preserve current semantics for direct token sequences. New syntax from `update-to-latest-mustache`, if already implemented, must participate in async recursion too. The refactor is the hard prerequisite; conformance can land before or after this change, with parity maintained by whichever lands second.

### AnyIO dependency and runtime ownership

Offer an `anyio` extra containing `anyio>=4.14.0` and a `trio` extra containing AnyIO plus Trio; include both in the development environment. Chevron supports Python 3.11 and later, and this floor covers Python 3.11 through 3.15 while providing the `abandon_on_cancel` spelling used for the resource-safe worker-I/O contract. Do not add a speculative upper bound. Export `async_render` through a lazy package dispatcher, so a synchronous import neither imports the async module nor AnyIO; awaiting it without the extra raises a clear installation error. Keep the synchronous dependency footprint unchanged.

Run a focused compatibility matrix at the declared floors on Python 3.11 and 3.15, separate from the broad current-dependency test matrix: AnyIO 4.14 on asyncio, and AnyIO 4.14 plus Trio 0.32 on Trio. Declare the matching Trio floor directly as well as through AnyIO's extra, so resolution cannot select a Trio release AnyIO does not support. Its compact behavioural suite verifies the public asynchronous contract without multiplying the complete suite.

Use AnyIO operations inside the caller's running backend. Never call `asyncio.run`, `anyio.run`, construct a loop, or create a portal. AnyIO supplies portable file/thread operations, cancellation scopes and checkpoints. Its file APIs offload blocking OS operations to worker threads; this is non-blocking for the event loop, not a claim of native async filesystem syscalls.

### Await selected callable results, not template data

Resolve names and reject callable template data through the same source policy before invoking anything. Retain `func`, `section`, `compat` and undecorated compatibility section selection. Both explicit lambda mappings and existing compatibility mode remain available; async rendering does not create a new authorisation model. Invoke a selected callable once; use `inspect.isawaitable` on the returned value and await it once when appropriate. This applies to every supported lambda protocol and checks an actual result, not `inspect.signature`, coroutine-function guesses or argument-count inference. It handles decorated async functions, async callable instances and ordinary functions returning awaitables.

Synchronous pure callbacks are supported directly; they must not perform blocking I/O. Automatically offloading every callback would change thread affinity and context access, so callers with blocking callbacks must adapt those operations explicitly using AnyIO. The same responsibility applies to custom mapping access, properties, string conversion and synchronous iterators. Renderer-owned I/O is always adapted. An async function that blocks internally cannot be made non-blocking by the renderer.

After awaiting, preserve each protocol's established result rules: interpolation and standard-section text is rendered recursively, compatibility output is appended directly, and None produces empty output plus the configured diagnostic. Inverted sections do not invoke a callable or await template data. Errors propagate without reinvocation or fallback to a different signature.

### Compatibility rendering callbacks are async

An async compatibility lambda receives `async_render_callback(template, data=None)`, normally used as `return await render(text, temporary_data)`. It preserves the active source policy, configuration, compatibility token cache, defaults and padding. A synchronous callback that simply returns `render(text)` also works because its returned awaitable is awaited; code that concatenates or otherwise consumes that coroutine as a string must migrate. Do not transparently bridge an old blocking callback into a loop. Document this distinction with examples while keeping the existing sync API intact.

Both renderers use immutable, parent-linked `_RenderFrame` scope chains. A frame owns one scope binding and points to its parent; section entry creates a child frame and section exit resumes the parent. Lookup walks the chain. The caller's outer `scopes` collection is input only and is never used as the renderer's live mutable stack; objects inside it remain shared. This removes list insertion, deletion and restoration, prevents awaits and callback-initiated concurrent nested renders from corrupting scope state, and gives sync and async identical scope ownership. Capture the callback's invocation frame rather than an engine-wide current-frame pointer; preserve falsey temporary-data behaviour. No concurrent mutation guarantee is made for caller-owned data objects.

Inverted sections use a distinct internal frame marker because they enter no
application scope. Current-context lookup treats every consecutive
inverted-section marker as transparent and continues through parent frames to
the nearest application scope. This keeps `{{.}}` and `{{#.}}` semantics
correct in nested inverted sections without a second scope stack or
renderer-local recovery.

### All renderer-owned I/O has an async boundary

| Operation | Async path |
| --- | --- |
| Native async text reader | Await `read()`; require text and retain caller ownership |
| Ordinary file-like reader | Run blocking `read()` in an AnyIO worker; await an awaitable result if a regular method returns one |
| Filesystem partial | Await a dedicated async filesystem helper using AnyIO path/file APIs for root/candidate resolution and UTF-8 reads |
| Missing/rejected/None diagnostics | Produce messages in shared pure logic and call the selected synchronous Python logger directly; the default `chevron` logger writes to stderr |
| Tokenisation and escaping | Shared synchronous CPU work over already-read text |

For reader adaptation, coroutine-method detection is an optimisation: unrecognised synchronous `read` methods are safely invoked in a worker and their result checked for awaitability. Do not pass async readers into the synchronous tokenizer. Read ordinary mapped partial text directly from memory; this change does not expand `partials_dict` into a provider/callback API.

The filesystem adapter retains mapping precedence, `partials_path=None`, suffix handling, relative-name restrictions and resolved containment, including a symlinked configured root. It lives in the async module as `_aget_filesystem_partial()` and delegates worker-pool mechanics to AnyIO's asynchronous path/file API rather than calling `to_thread` from Chevron's renderer logic. It does not strengthen the existing path checks against concurrent filesystem replacement.

Synchronous source policies produce messages through the shared per-render logging contract. For async reuse, keep message production separate from delivery so resolution stays pure; both engines call their selected synchronous logger at the semantic delivery point. This applies to the default stderr logger and application-provided loggers alike. `async_render()` documents that a supplied logger should remain minimal because it executes synchronously and blocks that render while it runs. Preserve warning text, order and occurrence count. Avoid buffering all warnings until successful completion, which would lose diagnostics on failure.

### Async iteration, checkpoints and cancellation

Support `AsyncIterable` normal sections using `async for`, sequentially rendering each yielded item. Callable dispatch remains first; if an object supports both iteration forms, use asynchronous iteration in the async engine. Inverted sections retain ordinary object truthiness without destructive peeking. Caller-supplied iterators/readers remain caller-owned, including on cancellation; close only resources created by Chevron. Document this so applications can use their own async context managers for generator cleanup.

Add cooperative checkpoints at render entry and bounded token/iteration intervals, including section-body collection, so CPU-only templates permit cancellation and other tasks to progress. Keep the tokenizer synchronous; a single long parsing step or caller computation remains non-pre-emptible. Avoid one await per character and benchmark checkpoint overhead.

Use `finally` for frame and diagnostic cleanup. Propagate cancellation instead of turning it into a missing partial or empty lambda result. When cancellation is delivered through an AnyIO cancellation scope, worker-backed reads use non-abandoning cancellation behaviour so opened resources are deterministically closed; cancellation may therefore wait for an OS operation to return, although the event loop stays responsive. This guarantee does not extend to raw `asyncio` timeout or task-cancellation APIs. Any awaited cleanup requiring protection uses a narrow shield, never a shield around the whole render.

### Behavioural verification across backends

Use AnyIO's pytest plugin with explicit asyncio and Trio backend parametrisation. Keep those tests and all async conformance fixtures in a separately collected async test directory, ignored when AnyIO is unavailable. Run shared renderer cases and all vendored conformance fixtures through both engines; adapt fixture lambda declarations only as necessary, preserving upstream data. Use small async callback tests for every protocol under both source policies, including callables returning awaitables and falsey callable instances. Share fixture loading and lambda adaptation where it is protocol-neutral; keep only engine execution in the separate suites.

Use events and task groups to verify ordering, concurrent isolation and suspension rather than timing sleeps. Tests cover file and reader ownership, blocked filesystem work with a progressing sibling task, containment, warning writes, cancellation during readers/lambdas/iteration, recovered recursive errors and sequential output. Exercise pure-text cancellation checkpoints. Preserve the synchronous suite and add an isolated installation/import check without the async extra. Measure representative async workloads without making wall-clock timings a test gate.

## Risks / Trade-offs

- Duplicated execution loops can drift → share semantic helpers and parametrise the same acceptance cases across engines.
- Sync callbacks or custom objects can block → document the non-blocking callback contract and explicit worker adaptation; do not promise to police arbitrary application code.
- Optional imports can break synchronous users → lazy-load the async dependency and verify base installations independently.
- Shared recursive stacks are unsafe across awaits → use branch-owned frames and diagnostic state, with deterministic concurrent tests.
- Filesystem cancellation is not instant → retain resource-safe worker completion and document cancellation latency.

## Migration Plan

Implement after the refactor. Existing consumers continue using `render`; async consumers install the extra, await `async_render`, and migrate compatibility callbacks to await their supplied render operation. Document complete sync and async API usage, logging and lambda protocols in `API.md`; retain only a concise package overview and navigation in `README.md`. Add user-facing examples for all three decorators and both backends without publishing private engine classes. Implementation tasks contain code, tests and their necessary documentation only.

## References

- [AnyIO file I/O](https://anyio.readthedocs.io/en/stable/fileio.html): worker-backed file and path operations.
- [AnyIO testing](https://anyio.readthedocs.io/en/stable/testing.html): pytest plugin and backend fixtures.
- [AnyIO threads](https://anyio.readthedocs.io/en/stable/threads.html): worker execution and cancellation constraints.
