---
name: agent-prose
description: Writing for agents: use when creating or editing a skill, an AGENTS.md or CLAUDE.md, a rule, or a doc a pointer reaches.
---

Reference for writing any document an agent consumes: a skill, an `AGENTS.md` / `CLAUDE.md`, a rule, a doc reached by a pointer. The aim is predictability: the agent takes the same _process_ every run, whatever the output; anything that lets runs diverge is _variance_. A document you write or edit is done when every rule here has met every line of it.

## Context pointers

A **context pointer** is a reference held in the agent's context that names some out-of-context material and encodes the condition for reaching it. A skill's description is one; a line in `AGENTS.md` naming a doc is the same object. The pointer's _wording_, not its target, decides when the agent reaches the material, and how reliably. A must-have target behind a weakly worded pointer is a variance bug: sharpen the wording first, and inline the material only if sharpening fails.

A pointer does two jobs: state what the material is, and list the **branches** that should trigger reaching it (a branch is a distinct case the document handles, so different runs take different paths through it). Every word of an always-loaded pointer spends context load, so it earns even harder pruning than the body:

- **Front-load the leading word**: the pointer is where it does its triggering work.
- **One trigger per branch.** Synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches.
- **Cut identity the body already carries.**

## The two loads

Every document and pointer you add spends one of two budgets:

- **Context load**: always-loaded material (an `AGENTS.md` line, a skill description) spends the agent's tokens and attention every turn, whether or not it fires.
- **Cognitive load**: the human is the index, remembering which documents exist and when to reach for each. It is the price of human agency: spend it where human judgement matters, remove it where it does not.

Material behind a pointer costs only the pointer's line of context load; material with no pointer at all rides entirely on cognitive load.

## Information hierarchy

A document is built from **steps** (the ordered actions the agent performs) and **reference** (definitions, rules, facts consulted on demand), mixed freely. The core decision is where each piece sits on the **information hierarchy**, a ladder ranked by how immediately the agent needs the material:

1. **In-file step**: what the agent does, in order.
2. **In-file reference**, consulted on demand. A flat peer-set (every rule of a review on one rung) is a fine arrangement.
3. **Disclosed reference**: a separate file, sibling or external, reached by a context pointer and loaded only when it fires.

Push too little down and the top bloats; push too much and you hide material the agent needs.

**Progressive disclosure** is the move down the ladder, behind a pointer, so the top stays legible. Branching is the cleanest test: inline what every branch needs, and push behind a pointer what only some branches reach. In-file reference that should be disclosed buries the steps and turns attending to them into a coin-flip: a variance lever.

**Co-location** decides _what sits beside_ a piece once the ladder has placed it: keep a concept's definition, rules and caveats under one heading, so reading one part brings its neighbours with it.

**Sprawl** is the failure mode here: a document simply too long, even when every line is live and unique. Attention thins across the excess. The cure is the ladder: disclose reference behind pointers, and split by branch or sequence so each path carries only what it needs.

## Steps and completion criteria

Every step ends on a **completion criterion**, the condition that tells the agent the work is done. Two properties make it a lever:

- **Clarity**: can the agent tell done from not-done? A vague bound ("understanding reached") invites **premature completion**: attention slipping to _being done_, pulled by the visible steps still ahead. Defend in order: **sharpen the bound first**; only if it is irreducibly fuzzy _and_ you observe the rush, split the sequence so the later steps sit across a real context boundary (a hand-off or a subagent dispatch; an inline call clears nothing). Merging sequences does the reverse: each step's later steps come into view.
- **Demand**: how much it requires. "Every modified model accounted for" forces thorough work where "produce a change list" does not. Demand drives **legwork** (the digging latent in the wording rather than written as its own step), and binds reference as well as steps: "every rule applied" gives an all-reference document its exhaustiveness bar.

The strongest criteria are both checkable and exhaustive.

## Leading words

A **leading word** is a compact concept already living in the model's pretraining that the agent thinks with while running the document (_lesson_, _fog of war_, _tracer bullets_). Repeated as a token, never as a sentence, it accumulates a distributed definition and anchors a whole region of behaviour in the fewest tokens. A coined word recruits no priors, so you pay in definition tokens what a pretrained word gives free: reach for an existing word first.

It anchors twice. In the body, _execution_: the agent reaches for the same behaviour every time the word appears, and inside flat reference it focuses attention on a class of thing to look for. In a pointer, _invocation_: when the same word lives in your prompts, your docs and your codebase, the agent links that shared language to the material and reaches it more reliably.

Hunt restatements a leading word retires: a triad spelled out at three sites, a pointer spending a sentence to gesture at one idea. Assume every document carries some.

- "fast, deterministic, low-overhead" → _tight_ (a _tight_ loop).
- "a loop you believe in" → _red_, turning a fuzzy gate into a binary observable state (the loop goes _red_ on the bug, or it doesn't).

**Negation** is the failure mode beside this lever: steering by prohibition drags the forbidden behaviour into context and makes it _more_ available. _Don't think of an elephant_, and the elephant is all there is. Prompt the **positive**: state the target behaviour ("write one-line comments") so the banned one is never spoken. A positive rewrite tends to keep the banned behaviour as a contrast ("read the config from the environment, not from the database"): reread each rewrite until it states only the target. A prohibition earns its place only as a hard guardrail you cannot phrase positively, paired with the positive target.

When a skill that acts contains banned patterns (negations, prohibitions, lists of what to avoid), rewrite each as its positive target, and move the banned pattern to a skill that reviews that work, as a red flag to look for. When no such reviewer exists, suggest one to the user if the work gets reviewed often enough to earn it; otherwise keep only the positive target.

## Pruning

- Keep each meaning in a **single source of truth**, so changing the behaviour is a one-place edit. **Duplication** (the same meaning in more than one place) costs maintenance and tokens, and inflates a meaning's prominence past its real rank.
- The **environment** is a source of truth too (`package.json` scripts, config files, the directory layout, `--help` output), and a document that restates it is a **cache**, earning its load only when the lookup is expensive. Cache what the agent cannot find by looking: the unwritten convention, the reason behind a choice, the gotcha no config confesses.
- State a reason as its **cause**, the mechanism that makes the rule hold (_separate target dirs link several copies at once_): numbers and setting from one run tie the rule to that run and leave the reader to guess what generalizes.
- A trim keeps every instruction's **force**: each `must`, `never`, `may` and condition, each step's action, and each list's required or optional status.
- Check every line for **relevance**: a line loses it by never bearing on the task (mere exposition, or a branch that should be disclosed) or by going stale. Without a pruning discipline the default fate is **sediment**: stale layers that settle because adding feels safe and removing feels risky.
- Hunt **no-ops** sentence by sentence: an instruction the model already obeys by default pays load to say nothing. The test (does it change behaviour versus the default?) is model-relative, and a guardrail the default would not hold under pressure (a rule the harness's own prompt pushes against) is not a no-op: settle a disagreement by running the document. When a sentence fails, delete the whole sentence. The test also grades leading words: a word too weak to beat the default (_be thorough_) is a no-op, and the fix is a stronger word (_relentless_).

## Running a skill

Pruning settles disputes by running the document. For a skill, that means running test prompts with and without it side by side; for its description, should-trigger and near-miss queries. Write trigger queries as substantive tasks: the agent consults a skill only for work it can't easily do alone, so a one-step prompt fires nothing whatever the description says.

Carry these from the runs back into the writing:

- **Read the transcripts, not just the outputs.** The process is what the document steers; a passage that sends runs down a wasted path is a line to prune.
- **Load timing is observed in the transcripts.** When a rule, skill or reminder enters context is harness behaviour, so a passage that looks like a no-op because "the rule is loaded anyway" is settled in the transcripts. In Claude Code a rule file with `paths:` frontmatter arrives mid-session, after a Read, Edit or Write of a matching file or a single-command Bash read of it such as `cat -n`, `head` or `sed -n` (a read inside a compound command, a pipe included, doesn't count, nor did a Bash read of a file under `/tmp`; a Read of a file outside the project is untested), and is absent until then.
- **Repeated legwork is a missing script.** When every run writes the same helper, bundle it in the skill's `scripts/` and point at it, so the environment carries it instead of the prose.

## Skills

Make a skill **user-invoked** (`disable-model-invocation: true`, with a one-line human-facing description) unless the agent or another skill must reach it on its own: it then costs no context load, but nothing except the human typing its name can fire it, other skills included. Reference two user-invoked skills both need therefore lives in a plain file outside the skills (a `docs/` file) that each points at. When user-invoked skills multiply past what the human remembers, add a **router skill**: one user-invoked skill naming the others and when to reach for each.

## Portable skills

Write skills _portable_: a skill loads in sessions its author never sees, so name each condition the agent can check ("when the session has no browser", "when the skill is generated from another source") and let the agent find the place. An install path behind a condition the agent can check (`~/.claude/rules/x.md`, when it exists) is portable. Facts true of one repo belong in that repo's `AGENTS.md` / `CLAUDE.md`.
