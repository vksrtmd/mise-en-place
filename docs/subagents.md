# Subagents

Read before writing a brief, launching an agent, or integrating a scratch branch. The policy (who gets an agent, which model) is in `~/.claude/rules/global.md`.

## Brief

- List only files you have confirmed exist (`ls` them in the agent's worktree, or your checkout for a read-only agent): a template's "read the repo's CLAUDE.md" sends each agent after a file that may not be there.
- Copy the wait block from `~/.claude/docs/track-builds.md` step 3 into the brief of every agent that runs the repo's check, a build or a test suite.
- An agent that deletes or moves text greps the repo for references into each passage it touches (`below`, `above`, step numbers, section names), in files it doesn't own too, and lists them in its report. It keeps each rule's force as it was: a `Never`, `must` or condition it rewrites stays a `Never`, `must` or condition.
- A review brief lists the edits the user made in the change under review, deletions included, as intended: the reviewer takes them as the baseline.

## Launch an agent that edits files

- Worktree: make it yourself (`~/.claude/docs/worktrees.md`) and launch the agent without `isolation`: an isolated agent works only inside the worktree the harness gives it.
- When an agent does run isolated, have it bring its worktree up to date with `git merge --ff-only <base>`.
- Brief: give the worktree's absolute path exactly as `git worktree list` prints it.

## Integrate

Integrate one scratch branch at a time: in its worktree, `git rebase <your branch>`; then, in yours, `git merge --ff-only <scratch branch>`.

Once merged, remove the scratch worktree and branch (`git worktree remove <path>`, then `git branch -D <name>`) while its commits still sit on your branch: your own later rebase gives them new SHAs. Run the removal in a later message than the merge, once the merge's output shows the branch landed, naming each branch and path literally.

When a rebase stops on `Your local changes ... would be overwritten` and `git -C <worktree> status --short` prints nothing, run `git rebase --continue`, then compare the replayed commits with `git range-diff`. The stop is a false positive, likely stale index stat data on a bind mount (a container's checkout): repeated rebases there stopped 2 times in 40, and none in 80 on a local disk.
