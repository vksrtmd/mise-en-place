---
paths:
  - "**/README.md"
  - "**/AGENTS.md"
  - "**/CLAUDE.md"
---

# Docs

Each root doc has one reader:

- `README.md` is for humans: what the project is, how to set up, use and run it, and what they run into.
- `AGENTS.md` / `CLAUDE.md` is for agents: what an agent needs to work in the repo.

Put what both readers need in its own doc and link it from both. A README in a subdirectory can serve humans and agents together, as long as it stays short.

## README

How the project works (internals, log formats, how a component is isolated) goes in a design doc, such as an ADR or a threat model, and the README links to it.

Document each failure whose message gives the person no hint at the fix, such as a bare 403 from an API.

A heading that code cites (`README > Setup`) is an interface: when you rename one, update every citation in the same change. A repo whose code cites headings has a test that checks each cited heading exists.
