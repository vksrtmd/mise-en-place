# Domain Docs

## Before exploring, read these

- **`GLOSSARY.md`** at the repo root, or
- **`GLOSSARY-MAP.md`** at the repo root if it exists: it points at one `GLOSSARY.md` per context. Read each one relevant to the topic.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in. In multi-context repos, also check `src/<context>/docs/adr/`.

If any of these files don't exist, **proceed silently**: the `/domain-modeling` skill creates them lazily when terms or decisions get resolved.

## File structure

Single-context repo (most repos): `GLOSSARY.md` and `docs/adr/0001-event-sourced-orders.md` at the root.

Multi-context repo (a `GLOSSARY-MAP.md` at the root): root `docs/adr/` holds system-wide decisions; each context has its own `src/<context>/GLOSSARY.md` and `src/<context>/docs/adr/`.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `GLOSSARY.md`, not a synonym it avoids.

If the concept you need isn't in the glossary, either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders), but worth reopening because…_
