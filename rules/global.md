# User-level instructions

## Branches

Name a branch `<issue_number>-<slug>` (`45-snapshots`), or `<slug>` for work without an issue. Before creating or pushing one, run `git fetch origin` and confirm the name is free: `git ls-remote --heads origin <name>`, `gh pr list --head <name> --state all` and `git branch --list <name>` all print nothing. Branch from `origin/<default branch>`, not the local copy.

## Worktrees

Do each branch in its own worktree under `.claude/worktrees/`, inside the repo. Before each `git worktree add` or `git worktree remove`, and after each `gh pr merge` (it triggers a cleanup sweep), read `~/.claude/docs/worktrees.md`.

## Subagents

Hand each independent finding or fix, a review's findings included, to a Sonnet subagent (`model: "sonnet"`). Items that touch the same file (tickets in a batch, tracks in a build, findings in a review) go to one agent or run one after another. An agent that edits files gets its own scratch branch and worktree; a read-only investigator runs in your checkout. Keep the orchestrator for briefing, review and integration. A fix you can make in a call or two stays inline, and so do edits to skill, doc or rule prose whose wording you settled with the user in this session.

Before writing a brief, launching an agent, or integrating a scratch branch (its first `git rebase <your branch>`), read `~/.claude/docs/subagents.md`.

Before you build a feature or fix a bug, read `~/.claude/docs/track-builds.md`. Once the design is settled (for a bug, once a red command reproduces it), hand the TDD loop to Sonnet agents: one per independent track (backend and viewer, say), and one for a build that doesn't split.

## Long runs

- CI: before the first `gh` call that reads CI status, read the CI bullet of `~/.claude/docs/issue-tracker.md`, and wait on runs with its polling loop in the background.
- Waits: in a wait command (a poll, a watch, a sleep loop), keep stderr in its output, so an early exit names its reason.
- Context: suggest `/compact` at the first boundary (a PR opened or merged, a ticket done, a batch integrated) after about 150k tokens, and by 250k at the latest.

## Memory

Never use the auto-memory directory: don't read, write or update memory files. Put anything worth keeping in the repo's CLAUDE.md or docs instead.

## Agent skills

The engineering skills assume these:

- Issue tracker: the repo's GitHub Issues, with triage labels named after their roles. Read `~/.claude/docs/issue-tracker.md` (its operations) before reading or writing the tracker.
- Domain docs: `GLOSSARY.md` (or `GLOSSARY-MAP.md`) and `docs/adr/`. Read `~/.claude/docs/domain.md` before exploring a repo that has them.
