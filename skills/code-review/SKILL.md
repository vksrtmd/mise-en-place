---
name: code-review
description: "Review a change for bugs, safety, load, untested risk and needless code, plus repo standards and spec fit. Use for \"review this\", \"code review\", \"review my PR\", \"review since X\", \"is this over-engineered\"."
---

Review a change along separate axes, each in its own **fresh sub-agent** (never a fork), so it reads the code unanchored on this session's view of it. Correctness always runs; the other axes join when the change calls for them.

## 1. Pin the change

Review what the user names: a fixed point (SHA, branch, tag, `main`, `HEAD~5`), a PR, files, or uncommitted work. A PR: `gh pr diff <n>` and `gh pr view <n> --json commits`. Files: `git diff HEAD -- <files>`. Named nothing: the uncommitted changes (`git diff HEAD` plus untracked files); none, then the branch since its merge-base with the default branch; on the default branch, the last commit.

For a fixed point the diff is `git diff <fixed-point>...HEAD` (three-dot: against the merge-base) and the commits are `git log <fixed-point>..HEAD --oneline`. Confirm the ref resolves (`git rev-parse`) and the diff is non-empty, so a bad target fails here, not inside the sub-agents. The step is done when you hold one diff command, its commit list (empty for uncommitted work), and a one-line statement of what you chose and why.

## 2. Find the spec

In this order, stopping at the first hit:

1. Issue references in the commit messages (`#123`, `Closes #45`), fetched per `~/.claude/docs/issue-tracker.md`, when it exists.
2. A path the user passed.
3. A spec file under `docs/` or `specs/` matching the branch name or feature.
4. The branch's open PR description (`gh pr view --json title,body`).

No hit: Spec sits out.

Then write the **settled list**: the spec's settled decisions and out-of-scope list, plus whatever the user or calling skill names as settled (a decision, a commit they made on purpose and why), plus what the user decided earlier in this session (findings they picked or declined, deletions they confirmed).

## 3. Spawn the sub-agents

When the diff changes fewer than about 50 lines (`git diff --shortstat`), run Correctness alone, with the documented standards and the spec added to its prompt, plus Security when the diff touches a trust boundary.

Issue every call in one batch, then wait for every report before step 4. Each prompt carries the diff command, the commit list, the absolute path of [`findings.md`](findings.md) with: "Read it first; report every finding in its format.", and the settled list, when not empty, with: "A finding that contradicts one of these is a note, not a finding."

- **Correctness**, always, on the session's model: the axis that catches what the others miss. Add the paths of [`correctness.md`](correctness.md) and [`standards.md`](standards.md). Brief: "Review exactly this diff through the lens in correctness.md. When the report runs long, cut Nice to have first, then Should fix."
- **Standards**, when the repo has files documenting how code is written (`CONTRIBUTING.md`, a style section in `AGENTS.md`/`CLAUDE.md`, a rules file such as `.claude/rules/*.md`, or a docs page), `model: "sonnet"`. Add their paths. Brief: "Report every place the diff breaks a documented standard: cite file and rule, mark it hard or a judgement call, quote the hunk. Skip anything tooling already enforces."
- **Spec**, when step 2 found a spec, `model: "sonnet"`. Add the spec's path or fetched contents. Brief: "Report (a) requirements missing or partial; (b) behaviour nobody asked for (scope creep); (c) requirements that look implemented but wrong; (d) places where following the spec's design changes behaviour the spec says stays unchanged. Quote the spec line for each."
- **Security**, when the diff touches a trust boundary (input from users or the network, auth or permissions, secrets, building shell commands, SQL, paths or URLs from input, deserialization, crypto, sandboxing), on the session's model. Add the path of `correctness.md`. Brief: "Trace every input this diff accepts from outside the process to where it is used. Report the security holes listed under Risk in correctness.md, each with the input that exploits it, marked `verified:` with the command you ran and its output, or `unverified`. Write the report to a file under `/tmp` and hand back its path with one line." Read the file (see findings.md).

## 4. Aggregate

Start with `What this change does:` in two or three sentences, then the target from step 1.

Then one section per axis that ran (`## Correctness`, `## Standards`, `## Spec`, `## Security`), each in its sub-agent's order, verbatim or lightly cleaned; a finding two axes report sits once, in the first. Number findings across all sections so the user can say "fix 2 and 5". Name each axis that sat out, and why, in one line. Drop a smell finding that a repo standard the Standards axis read endorses. Notes against the settled list go under `## Notes`, after the axes.

End with:

- `Verdict: Ship.` or `Verdict: fix 1 and 3 first.` (every must-fix).
- `Lean: -<N> lines possible.` when lean findings exist.
- `Not checked:` one line, when something mattered and no axis could check it.

End the review at the report; leave the code as it is.
