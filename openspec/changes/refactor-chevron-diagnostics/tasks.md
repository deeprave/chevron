# Tasks

## 1. Diagnostic interface and compatibility

- [x] 1.1 Replace the generic callback interface with keyword-only `logging.Logger`, `logging.LoggerAdapter` and `log_level` options, per-render configuration and the shared default `chevron` logger; verify through public render tests that positional callers remain compatible, stderr retains existing warning text/newlines and invalid configuration raises clearly.
- [x] 1.2 Retain `warn` truthiness for default warning output: truthy values select `logging.WARNING` and falsey values remain silent. Verify supplied loggers replace the default destination, use `log_level` for Chevron delivery filtering and retain application-owned configuration. Document the interface in the render docstring and README.

## 2. Recursive routing and event production

- [x] 2.1 Route existing missing-key, blocked-traversal, callable-data and None-result warnings through native logging without changing lookup fallback/coercion or rendering semantics; parametrise observable output and warning assertions across explicit/permissive modes and default/application loggers.
- [x] 2.2 Preserve the selected logger through sections, iterable items, partials, lambda-returned templates and supplied callbacks; add behavioural tests for ordered nested delivery, re-entrant public calls and independent concurrent renders without shared configuration leakage.
- [x] 2.3 Add INFO lifecycle and DEBUG resolution/dispatch/partial events with deferred logging arguments; verify event severity, absence of completion on failure, filesystem partial branches and exclusion of template bodies/data values. Document event categories and privacy limitations alongside the debugging example.

## 3. Fatal errors and output boundaries

- [x] 3.1 Report unhandled ChevronError once at the public rendering boundary while preserving its type, message and traceback; extend malformed-template cases for nested partials and lambda renders, warn=False silence and application-recovered nested errors, keeping direct tokenisation output-free.
- [x] 3.2 Remove callback-specific wrappers, retries and fallback policy. Delegate logger handler delivery and failure semantics to Python logging without a stderr fallback; update behavioural tests and documentation accordingly.
- [x] 3.3 Integrate CLI diagnostic logging through ordinary message-only standard logging, without a CLI-specific logger or `--log-level`, while retaining exit status, rendered stdout and programmatic `main()` forwarding. Update user-facing API change notes with the new diagnostics options and enabled ERROR reporting.
