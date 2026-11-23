# ADR Format

ADRs live in `docs/adr/` and use sequential numbering: `0001-slug.md`, `0002-slug.md`, etc.

## Template

```md
# {Short title of the decision}

{1-3 sentences: what's the context, what did we decide, and why.}
```

An ADR can be a single paragraph: it records *that* a decision was made and *why*. How it's enforced and tested lives in code, tests or the threat model, and the ADR points there; file paths, flags, test names and log or audit formats belong to those places.

## Optional sections

Most ADRs need none.

- **Status** frontmatter (see [Changing an ADR](#changing-an-adr)): useful when decisions are revisited
- **Considered Options**: only when the rejected alternatives are worth remembering
- **Consequences**: only when non-obvious downstream effects need to be called out. When a consequence is a gap that a threat model or another register of promises and gaps tracks, name the gap in one line and link to its entry: the register is the one list.

## Numbering

Scan `docs/adr/` for the highest existing number, stubs included, and increment by one. A number belongs to its file for good.

Refer to an ADR the way the repo already does, in prose, links and status lines alike. With no convention yet, write `ADR-0013`.

## Changing an ADR

The `status` frontmatter takes one of: `proposed`, `accepted`, `superseded by ADR-NNNN`, `merged into ADR-NNNN`, `withdrawn`.

- **Amend**: the decision stands and a part of it changes. Edit the body statements the amendment supersedes, so the ADR reads as the current decision, and add a dated line at the end saying what changed and why.
- **Supersede**: a new decision replaces it. Write the new ADR, linking back; set the old one's status to `superseded by ADR-NNNN` and leave its body as the record of what was decided then.
- **Merge**: two ADRs record one decision. Move the content into the one that stays, and reduce the other to a stub with status `merged into ADR-NNNN`.
- **Withdraw**: the decision no longer holds and nothing replaces it, or it never met the three tests in SKILL.md (*Offer ADRs sparingly*). Reduce it to a stub with status `withdrawn`.

A **stub** keeps the file, its number and title so links still resolve. Its body is one sentence: why it changed and where the decision lives now, if anywhere.

## What qualifies

An ADR passes the three tests in SKILL.md (*Offer ADRs sparingly*). Typical shapes:

- **Architectural shape.** "We're using a monorepo." "The write model is event-sourced, the read model is projected into Postgres."
- **Integration patterns between contexts.** "Ordering and Billing communicate via domain events, not synchronous HTTP."
- **Technology choices that carry lock-in.** Database, message bus, auth provider, deployment target. Only those that would take a quarter to swap out.
- **Boundary and scope decisions.** "Customer data is owned by the Customer context; other contexts reference it by ID only." The explicit no-s are as valuable as the yes-s.
- **Deliberate deviations from the obvious path.** "We're using manual SQL instead of an ORM because X." Anything where a reasonable reader would assume the opposite. These stop the next engineer from "fixing" something that was deliberate.
- **Constraints not visible in the code.** "We can't use AWS because of compliance requirements." "Response times must be under 200ms because of the partner API contract."
- **Rejected alternatives when the rejection is non-obvious.** If you considered GraphQL and picked REST for subtle reasons, record it; otherwise someone will suggest GraphQL again in six months.
