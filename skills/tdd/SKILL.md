---
name: tdd
description: "TDD: use when building a feature or fixing a bug test-first, or writing integration tests."
---

# Test-Driven Development

## The loop

1. Read the lean-code rule (`~/.claude/rules/lean-code.md`) when it exists and is not in context. It loads by itself only after a Read, Edit or Write of a code file, or a single-command shell read of one, so other shell work can leave it unloaded.
2. Explore the codebase until you can name the public interface the behaviour sits behind and the tests already around it. When the repo has a `GLOSSARY.md` or `docs/adr/`, read `~/.claude/docs/domain.md` first, so test names match the domain language and the code keeps within the ADRs.
3. Write down the seams under test (a **seam** is where a module's interface lives: the place callers and tests both cross, observing behaviour without reaching inside), each with a one-line note on what it catches and what it misses, so testing effort lands on critical paths and complex logic. Confirm them by where you got the task:
   - **A skill or agent called you with items** (the seams a spec agreed, a ticket's acceptance criteria, or review findings): every seam traces to one of those items.
   - **A user gave you the task**, a ticket included: confirm them with the user: "What's the public interface, and which seams should we test?"
   - **Neither** (you run as a background subagent handed no items): choose them yourself and list them in your report.
4. **Red**: read [tests.md](tests.md) (and [mocking.md](mocking.md) when the test needs a mock), then write one failing test at a confirmed seam, meeting the Test targets. For a bug, the first test follows *Bugs* below.
5. **Green**: write only the code that test needs.
6. Repeat from 4, one test, one minimal implementation per cycle.

**Conflicts**: when, at any step, a requirement (a handed item, the user's request) leaves a behaviour open or the code contradicts it (an ordering it doesn't fix, behaviour that looks like a bug), finish the seams no conflict touches, then stop and report every conflict at once: the requirement, what the code does, and the options. A suspected bug stays unpinned until the user answers, directly or through whoever briefed you.

**Red at the base**: to prove a test red against the old code (`<base>` is the base commit, or `HEAD` while your change is uncommitted), run [`scripts/red-at.sh`](scripts/red-at.sh) `<base> --copy <test files> -- <test cmd>`. It runs the tests in a scratch worktree, a bare checkout of `<base>`, and leaves yours as it is; when the tests need installed dependencies, add `--setup "<install cmd>"`. Read the failure output and confirm it shows the missing behaviour, with the dependencies in place.

Done when every confirmed seam, and every handed item a test can show, has a green test or is reported as a conflict, and, for a bug, its red command is green. Refactor in the review stage (the `code-review` skill), outside this loop.

## Test targets

- **Through the interface**: assert via the public interface, so a refactor that keeps behavior leaves the test green.
- **Named as a specification**: the name states a capability ("user can checkout with valid cart"), and the test makes one logical assertion about it.
- **Independent expected values**: take them from a known-good literal, a worked example, or the spec, so the assertion can disagree with the code.
- **Vertical slices**: each test is a **tracer bullet** that responds to what the last cycle taught you, so the test structure follows what you learn about the implementation.

## Bugs: red before theory

When the task is a bug, the first test reproduces it: it drives the real code path and asserts the user's exact symptom, so it goes **red** on this bug and green once fixed. Watch it go red before you form a theory of the cause; each hypothesis is then a prediction that the red command tests.

When no test seam reaches the bug yet, build another red command first: a curl against a dev server, a CLI run diffed against known-good output, a replayed captured payload, a `git bisect run` between two known states; once the cause is found, turn it into a red test at the seam that reaches the bug. Keep it **tight** (seconds, the same verdict every run; for a flaky bug, raise the reproduction rate until most runs go red). When nothing you try goes red, report what you tried and ask the user for an environment or a captured artifact that reproduces it.

When the only seam that reaches the bug is too shallow to replay how it happened, say so in your report: the architecture is what keeps it from being locked down.
