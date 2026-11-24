# Worktrees

## Create

Make each branch's worktree under `.claude/worktrees/`, inside the repo, so the host sees it and the user's checkout stays as it is:

```sh
git worktree add .claude/worktrees/<name> -b <name> --no-track origin/main
grep -qxF .claude/worktrees/ .git/info/exclude || echo .claude/worktrees/ >> .git/info/exclude
```

With no remote (`git remote` prints nothing), start from the local default branch in place of `origin/main`.

When the session already runs in .claude/worktrees/<name>, work there, and make further worktrees under that worktree's own .claude/worktrees/ when the main checkout's isn't writable.

## Clean up

Clean up when you drop a scratch branch, right after you merge one (see Integrate in `~/.claude/docs/subagents.md`) or your PR, before each `git worktree add` and after each `gh pr merge`. Those last two sweep every worktree under `.claude/worktrees/` whose branch has a merged PR (`gh pr list --head <branch> --state merged` prints one; the session that opens a PR usually ends before it merges), and each whose PR is closed unmerged once the user confirms (ask once per branch). With no remote, sweep each branch `git branch --merged <default branch>` lists instead.

cd to the repo root first, so the shell keeps a working directory. Remove a clean worktree by path (`git worktree remove <path>`), then `git branch -D <name>`, naming each branch and path literally. When the destructive-git hook blocks a step, its message names the way through.

## Recover

When git says `not a git repository: .../.git/worktrees/<name>`, the registration is gone: move the directory aside, `git worktree add <path> <branch>` again, then copy uncommitted files back.
