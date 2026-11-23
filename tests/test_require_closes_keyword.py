#!/usr/bin/env python3
"""Feeds commands to the Closes-keyword hook; prints a line per wrong verdict and exits 1 when any is wrong.

Usage: tests/test_require_closes_keyword.py [hook]  (default hooks/require-closes-keyword.sh; pass another
copy to test it without touching the worktree).

Each case: w when the hook should warn, - when it should stay quiet, tab, command, where \\n stands for a newline.
"""
import os
import sys
import tempfile

import lib
from lib import ROOT, cases, git, hook_run, report


# Closes-keyword hook: w when it should warn, - when it should stay quiet. A body file is read from
# the cwd the hook gets, which is not a repository, so its branch is unknown.
CLOSES = r"""w	gh pr create -t x --body "Refs #4"
w	gh pr create -t x --body "the unfixed #5 bug"
w	gh pr create -t x --body "prefix #4"
-	gh pr create -t x --body "Closes #4"
-	gh pr create -t x -b "fixes #4"
-	gh pr create -t x --body "Resolved: #4"
-	gh pr edit 4 --title x
-	gh pr create -t x --body-file closes.md
-	gh pr create -t x --body-file "my closes.md"
w	gh pr create -t x --body-file refs.md
w	gh pr create -t x -F missing.md
-	gh pr create -t x --body-file - <<'EOF'\nCloses #4\nEOF
w	gh pr create -t x --body-file - <<'EOF'\nRefs #4\nEOF
w	cd issue && gh pr create -t x --body "Refs #4"
-	cd plain && gh pr create -t x --body "Refs #4"
-	cd "plain" && gh pr create -t x --body "Refs #4"
w	cd plain && gh pr create -t x --head 7-x --body "Refs #4"
w	gh pr create -t x -H 7-x --body "Refs #4"
-	gh pr create -t x --head=docs-fix --body "Refs #4"
-	cd issue && gh pr create -t x -H docs-fix --body "Refs #4"
"""


def main():
    hook = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "hooks/require-closes-keyword.sh")

    with tempfile.TemporaryDirectory() as tmp:
        for name in ("issue", "plain"):
            git("init", "-q", os.path.join(tmp, name), cwd=ROOT)
        git("symbolic-ref", "HEAD", "refs/heads/7-x", cwd=os.path.join(tmp, "issue"))
        git("symbolic-ref", "HEAD", "refs/heads/docs-fix", cwd=os.path.join(tmp, "plain"))
        for name, text in (("closes.md", "Closes #4"), ("refs.md", "Refs #4"),
                           ("my closes.md", "Closes #4")):
            with open(os.path.join(tmp, name), "w") as f:
                f.write(text + "\n")
        for want, cmd in cases(CLOSES, comments=False, unescape=False):
            cmd = cmd.replace("\\n", "\n")
            _, out, _ = hook_run(hook, cmd, cwd=tmp)
            got = "w" if out else "-"
            if got != want:
                report("require-closes-keyword: '%s' gave %s, want %s" % (cmd, got, want))
    return lib.finish()


if __name__ == "__main__":
    sys.exit(main())
