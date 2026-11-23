---
name: audit-repo
description: >
  Quality audit of a repo or a part of it (a package, a subsystem): bugs,
  security holes, what breaks under real load, risky code without tests, slow
  paths, and what to delete, merge or split. Use for "audit this codebase", "find bloat", "what can I delete".
---

Audit the repo through the Correctness lens of `code-review`, with the repo as the code in scope instead of a diff. Read these first:

- [`../code-review/correctness.md`](../code-review/correctness.md): what to look for. Step 1 here takes the place of its *Understand first*.
- [`../code-review/standards.md`](../code-review/standards.md): the smells, part of Lean.
- [`../code-review/findings.md`](../code-review/findings.md): checking and format.

The user asked for this report, so give it in full.

## 1. Map first

- Audit what the user names (a folder, a package); nothing named: the whole repo.
- Read the README, the deploy and build config, the dependency list, the entry points (main, routes, handlers, jobs, CLI commands) and the tests.
- Trace the main flows end to end: where data comes in, what is stored, what goes out. Read the *risky paths* fully: input from users, money, auth, data writes, background jobs, anything shared between processes.
- Write the *toolchain note*: which build and test commands run here (`cargo test`, `npm test`, ...), checked once, and the target or cache dir they use. When you will fan out and no run has filled one yet, build once now, so each fan-out agent runs the stated commands in that warm dir.

The map is done when every entry point and risky path is traced or named under `Not checked:`, and the toolchain note is written.

## 2. Look and check

Apply the lens's *Look for* to every flow you traced, and check each finding as findings.md says. One more Lean item for an audit:

- module shape: a shallow module, one concept spread over many files, a seam that leaks. List each as one line under `Architecture:` at the end, with the files, outside the numbering; `/deepen-modules` proposes deepenings.

The audit is done when the lens's done criterion holds over the traced flows, module shape included.

### Fan out

When the user asks for sub-agents, or the repo passes about 5,000 lines, run step 2 in fresh sub-agents, one per trust boundary or subsystem, briefed from step 1's map. Four at once at most, so one quota window carries the run. Trust boundaries run on the session's model, the rest (tests, docs against code, plain correctness) on a smaller one. Each brief gives:

- its files, and the doc sections stating the promises it checks;
- findings.md's shape;
- step 1's toolchain note;
- a cap on each call's output: where the harness saves big output to a file (Claude Code: from about 30 KB), stay under it, reading big files one per call with offset/limit, since saved output is read a second time;
- the handback: the report in a file under `/tmp`, its path returned with one line (the reason is under *Handback through `/tmp`* in findings.md).

## 3. Output

Write findings.md's format, with these additions.

Start with `What this repo does:` in two or three sentences, and the load you assumed.

Number findings across all groups, so the user can say "fix 2 and 5". When small findings would bury the ones that matter, leave them out and say how many.

End with:
- `Verdict:` one line: healthy, or what to fix first.
- `Lean: -<N> lines, -<M> dependencies possible.` when lean findings exist.
- `Architecture:` the module-shape lines, when there are any, ending with "run `/deepen-modules` to propose deepenings for these".
- `Not checked:` the parts you did not read or could not run.

Nothing found: `What this repo does:`, then `Healthy. Nothing to fix.` and one line on what you checked, in place of findings.md's `Looks good.`

Stop at the report.
