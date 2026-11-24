#!/usr/bin/env python3
"""Feeds commands to the destructive-git hook; prints a line per wrong verdict and exits 1 when any is wrong.

Usage: tests/test_block_destructive_git.py [hook]  (default hooks/block-destructive-git.sh; pass another
copy, e.g. one from `git show main:hooks/block-destructive-git.sh`, to test it without touching the worktree).

Each case: expected exit (0 allow, 2 block), tab, command, where \\n and \\t stand for a newline
and a tab. Lines starting with # are comments.
"""
import os
import subprocess
import sys
import tempfile

import lib
from lib import ROOT, cases, git, hook_run, report


MAIN = r"""2	git reset --hard
2	git reset HEAD~1 --hard
0	git reset --soft HEAD~1
0	git reset HEAD file
0	git reset
2	git clean -fd
2	git clean --force
0	git clean -n
2	git checkout .
2	git checkout -f main
0	git checkout main
2	git checkout -- file
2	git checkout HEAD -- src/a.go
2	git checkout -qf main
0	git checkout main --
0	git checkout -b feature origin/main
0	git -C . checkout main
2	git checkout HEAD src/a.go
2	git -C /x checkout main~1 a b
0	git checkout -B feature origin/main
0	git checkout --orphan gh-pages main
0	git checkout --detach origin/main
0	git checkout main >/dev/null 2>&1
0	git checkout main 2> err.log
2	git -C . checkout .
2	git -C . checkout -- src/app.ts
2	git switch --discard-changes main
0	git switch main
2	git switch -fq main
0	git switch -c feature
2	git restore file
2	git restore --staged --worktree file
0	git restore --staged file
0	git restore -S file
0	git restore -qS file
2	git restore -SW file
2	git restore -S -W file
2	git restore -s HEAD file
0	git branch -d done
0	git branch --delete done
2	git branch -D done
2	git branch -d -f done
2	git branch --delete --force done
2	git branch -df done
0	git branch -f feature origin/main
0	git branch -a
0	git stash branch fix
2	git stash
2	git stash -u
2	git stash push -m wip
2	git stash save wip
2	git stash pop
2	git stash drop stash@{0}
2	git stash clear
2	git stash store abc123
0	git stash show -p stash@{0}
0	git stash apply e30e001a
0	git stash create
0	git stash branch fix stash@{0}
2	git worktree prune
2	git -C /x worktree prune -v
2	git --git-dir=/x/.git worktree prune
2	cd /x && git worktree prune
2	/usr/bin/git worktree prune
2	git worktree  prune
2	git	worktree prune
0	git worktree prune --dry-run
0	git worktree prune -n
0	git worktree remove .claude/worktrees/x
2	git worktree remove --force ../other
2	git worktree remove -f ../other
2	git worktree remove -ff ../other
2	git worktree remove ../other --force
0	git push
0	git push -u origin feature
0	git push origin HEAD:feature
0	git push --no-force-with-lease origin feature
0	git -C /x push origin feature
2	git push --force
2	git push -f origin feature
2	git push -uf origin feature
2	git push origin feature -f
2	git push --force-with-lease origin feature
2	git push --force-with-lease=feature:abc123 origin feature
2	git push --force-if-includes --force-with-lease origin feature
2	git push origin +feature
2	git push origin +HEAD:feature
2	git push --mirror backup
2	git fetch origin && git push --force origin feature
0	git worktree list
0	echo 'git worktree prune'
0	git commit -m "git reset --hard"
0	git commit -m "run bash -c 'git reset --hard'"
2	bash -c "git reset --hard"
2	sh -c 'git clean -fdx'
2	/bin/bash -lc 'git stash'
2	eval "git checkout ."
2	bash -c "cd /x && git reset --hard"
0	bash -c 'git status'
2	(git reset --hard)
2	echo $(git reset --hard)
2	echo `git reset --hard`
2	x=$(git reset --hard)
0	git status
2	git rm -f a.go
2	git rm -rf dir
2	git rm --force a.go
0	git rm a.go
0	git rm -r --cached dir
0	git rm --cached -rf dir
0	git rm -n -f a.go
0	git rm -rf --dry-run dir
# A trailing backslash continues the command on the next line.
2	git reset \\n  --hard origin/main
2	git \\n  stash
2	git -C /x \\n  worktree prune
0	git log \\n  --oneline
# A backslash ending a heredoc body line does not continue it.
2	cat <<'EOF' > f\nC:\\dir\\\nEOF\ngit reset --hard
# Heredoc bodies are text, unless a shell runs them.
0	git commit -qam "Retro: restore x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
0	git commit -qam "Retro: reset --hard x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
2	git commit -qam "Retro: restore x\n\nCo-Authored-By: Claude <noreply@anthropic.com>" && git reset --hard
0	git commit -F - <<'EOF'\nNever run git stash here\nEOF
# An apostrophe pairs only within its line, so the lines after it are still checked.
2	echo it's done\ngit reset --hard\necho 'x'
0	git commit -m "$(cat <<'EOF'\nUse git restore --staged, not git restore\nEOF\n)"
0	gh pr create --body-file - <<EOF\nwhy (git clean -fd) bites\nEOF
0	cat > a.md <<-EOF\n\tgit reset --hard\n\tEOF
0	cat <<A <<"B"\ngit stash\nA\ngit stash\nB
2	git commit -F - <<'EOF'\ngit stash here\nEOF\ngit reset --hard
2	cat <<A <<B\nx\nA\ny\nB\ngit stash
2	bash <<'EOF'\ngit reset --hard\nEOF
2	cat <<EOF | sh\ngit clean -fd\nEOF
2	/bin/zsh -s <<EOF\ngit stash\nEOF
2	git <<<x stash
# Known issues: verdicts pinned at their current, wrong value so a fix or a regression shows up.
# Fix one, then flip its expectation and drop it from the list in the hook's header.
0	g=git; $g reset --hard
0	git commit -m "Fix hook\n\nNever run git stash here"
0	echo it's; git reset --hard; echo 'x'
2	git commit -m 'Fix hook\n\nNever run git stash here'
0	echo "<<EOF"\ngit reset --hard
0	git checkout src/a.go
"""

# git branch -D, run from tmp: allowed only when every named branch's commits are on another
# ref or squash-merged into origin/main. repo/: old is behind main, squashed landed as one
# commit, pushed is on origin only, local is nowhere else, copy is a second name for local.
BRANCH_D = r"""0	git -C repo branch -D squashed
0	git -C repo branch -D old
0	git -C repo branch -D pushed
0	git -C repo branch -D copy
0	git -C repo branch -d -f squashed
0	cd repo && git branch -D squashed 2>/dev/null
0	git -C repo branch -D old squashed
0	git -C repo branch -D local
2	git -C repo branch -D local copy
2	git -C repo branch -D squashed local copy
2	git -C repo branch -D missing
2	git branch -D squashed
2	cd plain && git branch -D squashed
2	cd "repo" && git branch -D squashed
# Known issue, pinned: the cd stays in force after its subshell.
0	(cd repo) ; git branch -D squashed
"""

# The block reason for a branch named through an expansion, which the hook can't resolve.
LITERAL = r"""for n in 9 10; do git -C repo branch -D research/$n; done
git -C repo branch -D "research/$n"
git -C repo branch -D research/`echo x`
git -C repo branch -D $(echo local)
"""

# A literal branch name keeps the unmerged reason when a $ or backtick sits in heredoc text or on another line.
NO_OTHER_REF = r"""git -C repo branch -D local copy && python3 - <<'X'\nnote = "a branch `named` $here"\nX
git -C repo branch -D local copy\necho $HOME
"""


# Each block that discards edits names the alternative: (command, text its message must contain).
WAY_OUT = [
    ("git reset --hard", "git commit -am wip"),
    ("git checkout .", "git show HEAD:<file>"),
    ("git checkout HEAD src/a.go", "git show <ref>:<file>"),
    ("git restore file", "git show HEAD:<file>"),
    ("git worktree remove --force wt", "git -C <path> status --short"),
]


def main():
    hook = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "hooks/block-destructive-git.sh")

    for want, cmd in cases(MAIN):
        got = hook_run(hook, cmd)[0]
        if str(got) != want:
            report("%s: '%s' exited %s, want %s" % (hook, cmd, got, want))

    for cmd, want in WAY_OUT:
        err = hook_run(hook, cmd)[2]
        if want not in err:
            report("%s: '%s' message lacks '%s': %s" % (hook, cmd, want, err.strip()))

    # Fail closed: unparseable input, or no jq on PATH.
    got = hook_run(hook, None, raw="not json\n")[0]
    if got != 2:
        report("%s: invalid JSON exited %s, want 2" % (hook, got))
    env = dict(os.environ, PATH="/nonexistent")
    got = hook_run(hook, None, raw="{}\n", env=env)[0]
    if got != 2:
        report("%s: no jq on PATH exited %s, want 2" % (hook, got))

    with tempfile.TemporaryDirectory() as tmp:
        # `cd plain && ...` runs in a repo that has no such branch (copied from the Closes-keyword fixture).
        git("init", "-q", os.path.join(tmp, "plain"), cwd=ROOT)
        # Fixture for the branch -D cases.
        os.environ.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                          GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        r = os.path.join(tmp, "repo")

        def c(msg):
            with open(os.path.join(r, "f"), "a") as f:
                f.write(msg + "\n")
            git("add", "f", cwd=r)
            git("-c", "commit.gpgsign=false", "commit", "-qm", msg, cwd=r)

        try:
            git("init", "-q", "--bare", os.path.join(tmp, "origin.git"), cwd=ROOT)
            git("init", "-q", "-b", "main", r, cwd=ROOT)
            git("remote", "add", "origin", os.path.join(tmp, "origin.git"), cwd=r)
            c("base")
            git("branch", "old", cwd=r)
            c("second")
            git("switch", "-qc", "squashed", cwd=r)
            c("s1")
            c("s2")
            git("switch", "-q", "main", cwd=r)
            git("merge", "-q", "--squash", "squashed", cwd=r)
            git("-c", "commit.gpgsign=false", "commit", "-qm", "squash", cwd=r)
            git("switch", "-qc", "pushed", cwd=r)
            c("p")
            git("push", "-q", "origin", "main", "pushed", cwd=r)
            git("switch", "-qc", "local", "main", cwd=r)
            c("l")
            git("branch", "copy", cwd=r)
            git("switch", "-q", "main", cwd=r)
            git("fetch", "-q", "origin", cwd=r)
        except subprocess.CalledProcessError:
            print("branch -D fixture failed")
            return 2

        for want, cmd in cases(BRANCH_D):
            got = hook_run(hook, cmd, cwd=tmp)[0]
            if str(got) != want:
                report("%s: '%s' in %s exited %s, want %s" % (hook, cmd, tmp, got, want))

        # No remote: the squash check falls back to the local main, and git's own errors stay out of the reason.
        n = os.path.join(tmp, "noremote")
        try:
            git("init", "-q", "-b", "main", n, cwd=ROOT)
            r = n
            c("base")
            git("switch", "-qc", "squashed", cwd=n)
            c("s1")
            git("switch", "-q", "main", cwd=n)
            git("merge", "-q", "--squash", "squashed", cwd=n)
            git("-c", "commit.gpgsign=false", "commit", "-qm", "squash", cwd=n)
            git("switch", "-qc", "local", cwd=n)
            c("l")
            git("switch", "-q", "main", cwd=n)
        except subprocess.CalledProcessError:
            print("no-remote fixture failed")
            return 2
        got = hook_run(hook, "git -C noremote branch -D squashed", cwd=tmp)[0]
        if got != 0:
            report("%s: squash-merged branch in a repo without a remote exited %s, want 0" % (hook, got))
        err = hook_run(hook, "git -C noremote branch -D local", cwd=tmp)[2]
        if not err.startswith("BLOCKED") or "git branch -d" not in err:
            report("%s: unmerged branch without a remote: want a BLOCKED reason naming git branch -d, got: %s" % (hook, err.strip()))

        for cmd in LITERAL.split("\n"):
            if not cmd:
                continue
            if "literally" not in hook_run(hook, cmd, cwd=tmp)[2]:
                report("%s: '%s' blocks without the pass-literally reason" % (hook, cmd))

        for cmd in NO_OTHER_REF.split("\n"):
            if not cmd:
                continue
            cmd = cmd.replace("\\n", "\n")
            err = hook_run(hook, cmd, cwd=tmp)[2]
            if "no other ref" not in err:
                report("%s: '%s' blocks without the unmerged reason: %s" % (hook, cmd, err))
    return lib.finish()


if __name__ == "__main__":
    sys.exit(main())
