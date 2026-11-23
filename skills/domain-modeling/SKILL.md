---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when discussing codebase terminology, writing or editing a GLOSSARY.md, or recording, editing or reviewing ADRs.
---

# Domain Modeling

Actively build and sharpen the project's domain model as you design: challenge terms, invent edge-case scenarios, and write the glossary and decisions down the moment they crystallise. Merely reading `GLOSSARY.md` for vocabulary is not this skill; it is for changing the model.

## File structure

Layout (single context, or `GLOSSARY-MAP.md` plus per-context `GLOSSARY.md` and `docs/adr/`): `~/.claude/docs/domain.md`. Create files lazily: a `GLOSSARY.md` when the first term is resolved, `docs/adr/` when the first ADR is needed.

## During the session

### Challenge against the glossary

Check every term against `GLOSSARY.md`: the user's, the ones you write, and those in the docs and ADRs you read or edit. When the user's term conflicts with the glossary, call it out immediately: "Your glossary defines 'cancellation' as X, but you seem to mean Y. Which is it?" Write your own text in the glossary's terms. When an existing doc uses a term the glossary lists under _Avoid_ or defines differently, propose the fix.

### Sharpen fuzzy language

For vague or overloaded terms, propose a precise canonical term. "You're saying 'account': do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

Stress-test domain relationships with invented scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible. Which is right?"

### Update GLOSSARY.md inline

When a term is resolved, update `GLOSSARY.md` right there, not batched. Use the format in [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md). It holds terms only, with no implementation details, spec or scratch notes.

### Offer ADRs sparingly

Offer an ADR only when all three are true:

1. **Hard to reverse**: the cost of changing your mind later is meaningful
2. **Surprising without context**: a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off**: there were genuine alternatives and you picked one for specific reasons

Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md), and its *Changing an ADR* when revising one.

## Reviewing existing ADRs

When asked to check the ADRs already written, go through each one and record a finding per mismatch:

1. **The three tests** above. An ADR that fails one is a candidate to withdraw, or to merge into the ADR it belongs to.
2. **Form**, per [ADR-FORMAT.md](./ADR-FORMAT.md): the decision and why, with enforcement and tests pointed at rather than described; consequences that link to a register's gaps instead of restating them; status and stubs as *Changing an ADR* defines them; references in the repo's one ADR form.
3. **Terms**, checked against the glossary as in *Challenge against the glossary*.

The review is done when every ADR has met all three checks and is either named clean or has its findings. Report them, then apply the fixes the user picks, each as one of the changes in *Changing an ADR*.
