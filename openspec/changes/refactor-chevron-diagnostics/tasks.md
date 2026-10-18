# Tasks

## 1. Diagnostic interface and compatibility

- [ ] 1.1 Add keyword-only logger and log_level options, per-render diagnostic configuration and a default stderr callback; verify through public render tests that positional callers remain compatible, callback arguments use numeric levels, stderr retains existing warning text/newlines and invalid configuration raises clearly.
- [ ] 1.2 Implement the warn master switch and severity threshold before delivery; parametrise tests over enabled/disabled diagnostics, default/custom sinks and DEBUG through ERROR thresholds, including a callback that must never run with warn=False. Document the gate and logger.log integration in the render docstring and README.

## 2. Recursive routing and event production

- [ ] 2.1 Route existing missing-key, blocked-traversal, callable-data and None-result warnings through the diagnostic interface without changing lookup fallback/coercion or rendering semantics; parametrise observable output and warning assertions across explicit/permissive modes and default/custom sinks.
- [ ] 2.2 Preserve diagnostic configuration through sections, iterable items, partials, lambda-returned templates and supplied callbacks; add behavioural tests for ordered nested delivery, re-entrant public calls and independent concurrent renders without shared configuration leakage.
- [ ] 2.3 Add INFO lifecycle and DEBUG resolution/dispatch/partial events with early filtering and bounded identifiers; verify event severity, absence of completion on failure, control-character handling and exclusion of template bodies/data values. Document event categories and privacy limitations alongside the debugging example.

## 3. Fatal errors and output boundaries

- [ ] 3.1 Report unhandled ChevronError once at the public rendering boundary while preserving its type, message and traceback; extend malformed-template cases for nested partials and lambda renders, warn=False silence and application-recovered nested errors, keeping direct tokenisation output-free.
- [ ] 3.2 Prevent callback retries, recursive failure reporting and stderr fallback; add tests for warning-sink failures, a sink raising ChevronError, and a sink failing during fatal reporting, confirming the original template error remains primary in the latter case. Document callback failure behaviour.
- [ ] 3.3 Integrate CLI diagnostic routing without duplicate fatal output or changes to exit status/rendered stdout; verify CLI syntax-error cases with and without --warn and programmatic main() forwarding of custom logging options. Update user-facing API change notes with the new diagnostic options and enabled ERROR reporting.
