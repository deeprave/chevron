# Proposal

## Why

Chevron's API reference and template-language guidance are split between a concise README, a single large API document, and upstream links. Developers need a discoverable, approachable reference that explains both standard Mustache and Chevron's supported extensions without requiring them to infer behavior from source or tests.

## What Changes

- Replace the repository-root `API.md` with a MkDocs documentation source arranged as navigable chapters and deployed to GitHub Pages.
- Document practical template authoring from basic interpolation through context lookup, sections, partials, dynamic names, inheritance, whitespace, delimiters, and declared lambda protocols.
- Document the synchronous and asynchronous rendering APIs, diagnostics, and the supported `chevron.tokenizer` pre-parsing API.
- Use substantial, realistic examples and cross-references where concepts overlap, while linking the pinned upstream Mustache manual as the normative language reference.
- Update the README to direct readers to the published documentation rather than duplicating reference material.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

This is documentation and publishing work only; it does not change Chevron's production behavior or public API contracts.

## Impact

- Adds MkDocs Material configuration, documentation sources, and a versioned GitHub Pages deployment workflow.
- Replaces `API.md` with structured documentation and updates README links.
- Adds documentation-only development dependencies as needed for the site build.
