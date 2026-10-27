# Design

## Context

See [proposal.md](proposal.md) for motivation. Chevron currently has a root-level README and `API.md`, but no documentation build configuration, chapter navigation, or published reference. `API.md` already contains useful material, including current async compatibility-callback guidance, which must migrate without losing its corrections.

The repository's CI and release workflows use pinned GitHub Actions and UV. Documentation should follow those conventions and must not add runtime dependencies to the package.

## Goals / Non-Goals

**Goals:**

- Provide a technical but approachable GitHub Pages reference site built with MkDocs.
- Arrange the documentation as a progression that can also be used as a chapter-level reference.
- Explain standard Mustache behavior, Chevron-specific extensions, and public APIs with substantial examples that resemble realistic use.
- Cross-link related concepts instead of repeating explanations, and link the pinned upstream Mustache manual as the normative language source.
- Document `chevron.tokenizer.tokenize()` and rendering from materialised token sequences as the supported submodule-level API.

**Non-Goals:**

- Reproduce the upstream Mustache specification or publish an alternative language standard.
- Add production rendering behavior, a template compiler, or caching implementation.
- Turn the README into another full reference, or maintain duplicate API content in `API.md`.

## Decisions

### Use MkDocs Material with a documentation optional extra

Follow the proven mcp-guide pattern: add a `docs` optional extra containing MkDocs, MkDocs Material, and Mike, then configure `mkdocs.yml` at the repository root. Material supplies accessible navigation, search, a mobile-friendly table of contents, and durable cross-page anchors without custom site code. The extra keeps site tooling out of Chevron's runtime and normal development environment while making the local preview and build commands unambiguous: `uv sync --extra docs`, then `uv run mkdocs serve` or `uv run mkdocs build --strict`.

### Publish versioned documentation through GitHub Pages

Chevron's public API evolves between releases, so retain documentation for each published package version as well as a `latest` alias. Use Mike to publish the generated Material site to the repository's `gh-pages` branch from `main`, with a version derived from `pyproject.toml`. The workflow must use pinned actions, `uv sync --frozen --extra docs`, a full checkout for Mike, and standard-library `tomllib` for version extraction; parsing the entire project TOML with an auxiliary command has proven fragile when unrelated metadata contains TOML date values.

The workflow will validate strict documentation builds on pull requests that affect documentation inputs, and publish only from `main` (with manual dispatch available). Publication needs `contents: write` for the generated `gh-pages` commit; no package runtime credential or dependency is involved. Repository Pages activation and publication verification are operational deployment work outside this implementation change. This intentionally differs from an artifact-only Pages deployment because versioned documentation requires Mike's retained version tree.

### Replace `API.md` with a chaptered documentation tree

Move existing API material into `docs/api/` and remove the root-level `API.md`. Update README links to the published documentation site and the relevant source pages. Keep the README concise: badges, package purpose, a minimal example, dependency facts, and documentation links.

The navigation will contain these chapter groups:

- **Getting started:** overview, installation-independent package prerequisites, and a first complete render.
- **Template language:** syntax and escaping; contexts and lookup; sections and inverted sections; partials and whitespace; dynamic names and inheritance; lambda behavior.
- **API reference:** synchronous rendering, async rendering, tokenizer API, diagnostics and logging, and compatibility notes.
- **Reference:** the pinned upstream Mustache manual, fixture provenance, extensions, and compatibility differences.

### Teach concepts in order and cross-reference them

Each chapter introduces one primary idea, includes a non-trivial rendered example, and links forward or back to neighboring concepts. Examples should use realistic view data, layouts, components, notification variants, or page fragments rather than isolated placeholders. Explain enough renderer behavior to make a contract understandable, but keep internal frames, token scheduling, and implementation algorithms out of the guide.

The lambda chapters will explicitly establish that historical compatibility lambdas were section callbacks, then distinguish zero-argument interpolation lambdas, standard section lambdas, and compatibility callbacks. The async chapter will state that its compatibility `render` argument is an async callable whose calls return awaitables, including the limited synchronous forwarding case.

### Treat tokenizer documentation as an explicit submodule contract

Document `from chevron.tokenizer import tokenize`, not a nonexistent `chevron.tokenize` root export. Explain that a materialised token sequence can be supplied to `render()` or `async_render()` to avoid repeated tokenisation, while rendering, lookup, and expansion still occur per call. Describe the two-item default stream, the `include_raw=True` stream, source-text-only input, and the need to materialise the generator before reuse.

## Risks / Trade-offs

- [Examples can drift from implementation] → Keep examples scoped to supported public behavior and validate the MkDocs build in CI; use existing behavioral tests as the source of truth when writing examples.
- [Pages may not be enabled for the repository] → The repository maintainer enables Pages to serve `gh-pages` when the deployment workflow is ready; this operational step is outside the change implementation.
- [A documentation version could overwrite an earlier release's reference] → Publish immutable version directories through Mike and update only the `latest` alias for the current version.
- [Migrating `API.md` can break inbound links] → Replace README links in the same change and add a short repository-level migration note if a durable redirect is not available from GitHub Pages.
- [Too much implementation detail can obscure the guide] → Keep internal explanation limited to consequences visible to template authors and API users; link between chapters instead of duplicating detail.

## Migration Plan

1. Add the MkDocs Material configuration, source tree, and versioned Pages deployment workflow.
2. Migrate and expand API documentation into the chaptered tree, then remove `API.md` and update repository links.
3. Build the site locally and in CI. The repository maintainer can then activate Pages to serve the `gh-pages` branch.
4. If publishing must be rolled back, disable the Pages workflow or deployment environment; documentation sources remain ordinary repository files and do not affect package runtime behavior.
