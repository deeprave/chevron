# Tasks

## 1. MkDocs and publication foundation

- [x] 1.1 Add a `docs` optional extra for MkDocs, MkDocs Material, and Mike, then create `mkdocs.yml` with Material navigation, repository links, version selection, and strict-build configuration; verify `uv sync --extra docs` and `uv run mkdocs build --strict` produce the site.
- [x] 1.2 Add a pinned workflow that strictly builds documentation on relevant pull requests and, on `main` or manual dispatch, publishes the current `pyproject.toml` version plus the `latest` alias using Mike; use UV, full Git history, and `tomllib` version extraction, and validate its YAML and permissions locally.

## 2. Template-authoring guide

- [x] 2.1 Create the getting-started and template-language introduction chapters with a complete, realistic rendering example; verify they appear in the site navigation and link to the relevant API chapters.
- [x] 2.2 Document interpolation, escaping, comments, context lookup, dotted names, current context, sections, and inverted sections with progressively richer examples; verify each example's expected output against Chevron's public rendering behavior.
- [x] 2.3 Document standalone whitespace, delimiter changes, in-memory and filesystem partials, dynamic names, and inheritance with multi-file layout/component examples; verify the examples reflect current partial lookup and containment behavior.
- [x] 2.4 Document declared interpolation, standard-section, and compatibility lambdas, including their sync and async contracts and cross-links to rendering API guidance; verify the async compatibility examples distinguish forwarding an awaitable from awaiting and using its result.

## 3. API reference

- [x] 3.1 Migrate synchronous `render()` API material into a focused API chapter covering accepted template inputs, options, result behavior, partial policy, and diagnostics; verify every documented signature and option matches the public entry point.
- [x] 3.2 Create an `async_render()` chapter covering AnyIO runtime ownership, supported async inputs, callback behavior, cancellation boundaries, and synchronous compatibility-callback forwarding; verify its examples run on the supported async API.
- [x] 3.3 Create a `chevron.tokenizer` chapter documenting `from chevron.tokenizer import tokenize`, materialised stream reuse with both renderers, default and raw token shapes, and validation boundaries; verify its examples use the supported submodule import rather than a root-level export.
- [x] 3.4 Add reference chapters for Chevron extensions, compatibility differences, vendored fixture provenance, and the pinned upstream Mustache manual; verify standard-language claims link to the pinned upstream source rather than duplicate it.

## 4. Documentation migration

- [x] 4.1 Remove the root-level `API.md` after its content has been migrated into the documentation tree, and update README links to the published site and source documentation; verify no tracked repository link still targets the removed file.
- [x] 4.2 Keep the README as a concise package landing page with badges, package prerequisites, one minimal example, and clear documentation links; verify the rendered README does not duplicate the chaptered reference.
