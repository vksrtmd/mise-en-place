# mise-en-place

This repo is the source of what is installed under `~/.claude` (see `README.md`). Edit the repo copy; the installed copy is read-only. When the main checkout isn't writable (in a container that mounts it read-only), write everything, `.scratch/` included, inside a worktree.

Put a fact about one tool where only sessions using that tool load it: a language's or build tool's (Cargo, vitest, a package manager) in `rules/<language>.md` behind `paths:`, `gh`'s in `docs/issue-tracker.md`, a hook's way around what it blocks in that block's message. Skills, the other docs and `rules/global.md` point at it with the condition that reaches it. A retro fix lands in that home first.

Before opening a PR, and before each push to an open one, when the commits no review has seen touch `skills/`, hand a review of those commits to a fresh subagent:

- Prose: the static pass of `skills/review-skill/SKILL.md`. Add the passages it calls **dropped** to the PR body for the user to confirm.
- A script: a reviewer that writes cases against the script and runs them, hunting inputs where it gives a wrong result.

After applying a review's findings, review again only the fixes that change behaviour, on their own diff; wording taken verbatim from a review needs none.

Write each Markdown paragraph and list item on one line; the reader's editor wraps it.

Run `tests/check.sh` before committing: it is the full check.

Scripts under `skills/*/scripts/` are tested in `tests/test_<skill>_<script>.py`, hooks in `tests/test_<hook>.py` (hyphens as underscores), each an executable run directly (`tests/test_retro_digest.py`), silent on pass; a change adds its case there (pass an old copy's path, from `git archive`, to see a red). A script that reads transcripts is also run on a real log under `~/.claude/projects` and its output read before the change is called done; fixtures hold only the shapes you thought of.
