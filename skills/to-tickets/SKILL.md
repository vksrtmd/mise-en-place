---
name: to-tickets
description: Break a plan, spec, or the current conversation into tracer-bullet tickets with blocking edges, published as GitHub issues; writes a spec first when the work needs one.
disable-model-invocation: true
---

# To Tickets

Break a plan, spec, or conversation into **tickets**: tracer-bullet vertical slices, each declaring the tickets that **block** it.

Read the issue tracker doc your instructions point at for its operations and triage labels.

## Process

### 1. Gather context

Work from the conversation. When the user passes a reference (a spec path, an issue number or URL) as an argument, fetch it and read its full body and comments. Any other argument text is an instruction on the breakdown ("group aggressively", "one ticket per service"): apply it in the first draft (see step 5).

Use the domain glossary's vocabulary in specs, titles and descriptions, and respect ADRs in the area, when the repo has them.

### 2. Explore the codebase (optional)

When you haven't already, explore the current state of the code.

Look for prefactoring that makes the implementation easier: "Make the change easy, then make the easy change."

### 3. Decide whether a spec comes first

Write a spec, following [spec.md](spec.md), when the source isn't already a spec in the tracker (a spec file is source material for one) and the work holds decisions several tickets will depend on (an interface, the seams to test at, which tests survive). Work that fits in one ticket skips the spec: the ticket holds the decision.

A spec you write becomes the source: its tickets are its sub-issues (step 6).

State the decision to the user in one line; ask when the work could fit one ticket or several. Done when the spec is published, or the user has heard that the work needs none.

### 4. Draft vertical slices

Break the work into **tracer bullet** tickets.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests): vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Each slice is sized to fit in a single fresh context window
- Any prefactoring should be done first

</vertical-slice-rules>

Give each ticket its **blocking edges**: the tickets that must complete before it can start. A ticket with no blockers can start immediately.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change (rename a column, retype a shared symbol) whose **blast radius** fans across the codebase, so a single edit breaks thousands of call sites and no vertical slice can land green. Sequence it as **expand–contract**: first expand, adding the new form beside the old so nothing breaks; then migrate call sites in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, CI green throughout because the old form still exists; finally contract, deleting the old form in a ticket blocked by every migrate batch. When even the batches can't stay green alone, let them share an integration branch that all block a final integrate-and-verify ticket; green is promised only there.

**Moved checks.** When a ticket moves a check or lookup to another point (into another module, after other validation), list in **What to build** the checks that ran before it at the old point and at the new one, and say whether the order of errors a caller sees may change. A ticket that claims identical behaviour must name an acceptance criterion that tests that order.

### 5. Quiz the user

When the argument gave an instruction on the breakdown, check the draft against it and revise until it holds; then open the quiz with how you read it ("group aggressively": 13 tickets merged to 6).

Present a numbered list; for each ticket:

- **Title**: short descriptive name
- **Blocked by**: tickets that must complete first
- **What it delivers**: the end-to-end behaviour it makes work

Ask whether the granularity is right (too coarse / too fine), whether each ticket depends only on tickets that genuinely gate it, and whether any should be merged or split.

When you offer options, recommend the one that follows the argument's instruction.

Iterate until the user approves the breakdown.

### 6. Publish the tickets

Publish one issue per ticket in dependency order (blockers first) so blocking edges reference real issue numbers. Add edges per the tracker doc's **Blocking**. When the source was an existing issue, make each ticket its sub-issue (tracker doc). Apply `ready-for-agent` unless instructed otherwise; the tickets are agent-grabbable by construction.

Work the **frontier**: any ticket whose blockers are all done (top to bottom for a linear chain).

Do NOT close or modify any parent issue.

<issue-template>

## Parent

A reference to the parent issue (omit when the source wasn't an existing issue).

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not layer-by-layer implementation.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Blocked by

- A reference to each blocking ticket, or "None (can start immediately)". Omit when blockers were set as native edges.

</issue-template>

Describe behaviour and decisions in prose; file paths and code snippets go stale. The prototype-snippet exception in [spec.md](spec.md) (Implementation Decisions) applies here too.
