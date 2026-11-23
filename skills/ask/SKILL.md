---
name: ask
description: Ask which skill or flow fits your situation. A router over the installed skills.
disable-model-invocation: true
---

# Ask

Before stating what a skill does or recommending a step be skipped, read that skill's SKILL.md: the summaries here are for orientation only.

A **flow** is a path through the skills: one **main flow**, **on-ramps** that merge onto it, and standalone skills.

## The main flow: idea → ship

1. **`/discuss`** sharpens the idea into settled decisions, asking you only what it can't decide. In a repo with a `GLOSSARY.md` (or `GLOSSARY-MAP.md`) it also runs `/domain-modeling`, to keep that glossary clean.
2. **Branch: can you settle every question in conversation?** If a question needs a runnable answer (state, business logic, a UI you have to see), detour through a prototype, bridged by **`/handoff`** in both directions:
   - **`/handoff`** out, then open a fresh session against that file,
   - **`/prototype`** to answer the question with throwaway code,
   - **`/handoff`** back what you learned, and reference it from the original idea thread.
3. **Branch: is this a multi-session build?**
   - **Yes** → **`/to-tickets`**, which writes a spec first when the build needs one, then splits the thread into tracer-bullet tickets, each declaring its **blocking edges**. Then run **`/implement`** one of two ways:
     - One ticket per run, **`/clear`ing context between each one**. Take any ticket whose blockers are done; each is self-contained, so the last one's context is disposable.
     - One run for the parent, a list of ticket refs, or a group you describe. It runs implementer subagents in parallel on one integration branch. Reach for it when you'd rather hand the build to subagents.
   - **No** → **`/implement`** right here, in the same context window.

   Either way, the build drives **`/tdd`** and closes with **`/code-review`** of the diff. Reach for **`/tdd`** on its own when you just want to build a concrete behaviour test-first without a full spec, and **`/code-review`** on its own whenever you want to review a branch or PR against a fixed point.

   When the work goes up as a pull request, model-invoked **`/pr`** writes its title and body.

4. **`/retro`** closes the loop. After a build, and especially one that went sideways, it looks back over the session and suggests changes to the agent's **environment** (checks, steering files, pointers, tooling). You apply the suggestions you keep yourself, in a fresh session (after `/clear`) in the repository each one names. The next build then starts from a better environment.

### Context hygiene

Keep steps 1–3, through `/to-tickets`, in **one unbroken context window**. Then `/clear`: `/implement` starts fresh, working from the tickets. Run `/retro` in the build session before you clear; after clearing, point it at that session's log instead.

The limit is the **smart zone**, where the model still reasons sharply. If a session nears it before `/to-tickets`, `/compact` at the nearest phase boundary (see Phase boundaries).

## On-ramps

A starting situation that generates work, then merges onto the main flow.

- **Bugs and requests piling up** → **`/triage-tickets`**. It moves issues through triage roles and produces agent-ready issues, which **`/implement`** later picks up.

  Triage is for raw incoming issues; tickets from `/to-tickets` are already agent-ready and go straight to `/implement`.

- **Something's broken** → **`/tdd`**. It starts from one command that goes **red** on this bug. Once the fix is in, run **`/retro`** in the same session to ask what would have prevented the bug; where the real finding is that there's no good seam to lock it down, that's a job for **`/deepen-modules`**.

- **A huge, foggy effort: a greenfield project or a huge feature build, too big for one session** → **`/wayfinder`**, the most cognitively demanding flow here. When the way from here to the destination isn't visible yet, it charts a **shared map** of **decision tickets** on the issue tracker and resolves them one at a time, producing **decisions, not deliverables**, until the fog is pushed back and the way is clear. Where **`/discuss`** sharpens an idea you can hold in one session, wayfinder is for the one you can't; it's slower and denser.

  When the map clears, take it to **`/to-tickets`** and then `/implement` as usual; go straight to `/implement` only when the effort turned out genuinely small.

## Codebase health

- **`/code-review`** reviews one change. **`/audit-repo`** is its Correctness lens over a repo or part of it: a one-shot, ranked report that changes nothing.

- **`/deepen-modules`** runs whenever you have a spare moment to keep the codebase good for agents to operate in. It surfaces **deepening opportunities**; each pick goes on to `/to-tickets`.

## Vocabulary underneath

**`/domain-modeling`** is the model-invoked reference for the domain vocabulary: challenging a fuzzy term, recording an ADR. Reach for it when the **words**, not the process, are the problem.

## Phase boundaries

At the **boundary** between two phases of a session, pick between continuing, `/clear`, `/handoff`, a subagent and `/compact`. Read [PHASE-BOUNDARIES.md](PHASE-BOUNDARIES.md) for the ordered tree that picks between them.

## Standalone

- **`/prototype`** is a small, throwaway program that answers one design question: does this state model feel right, or what should this UI look like. The prototype is kept on a throwaway branch as a **primary source** while the answer folds into the real code. It's the detour in step 2 of the main flow, and fits any design question hard to settle on paper.
- **`/research`**: delegate reading legwork to a **background agent**: it investigates a question against **primary sources**, then leaves a cited Markdown file where the repo keeps such notes. The file it produces is something to take *into* the main flow at `/discuss`, since research feeds the thinking rather than replacing it.
- **`/agent-prose`** is the reference for writing documents agents consume: skills, AGENTS.md/CLAUDE.md, rules and pointed-at docs. **`/review-skill`** reviews a skill against it, then runs the skill to settle what reading can't.
