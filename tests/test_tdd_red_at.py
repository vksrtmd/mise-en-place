#!/usr/bin/env python3
"""Runs skills/tdd/scripts/red-at.sh on a fixture repo built in a temp dir; prints a line per failed
expectation and exits 1 when any fails.

Usage: tests/test_tdd_red_at.py [scripts dir]  (default skills/tdd/scripts; pass another copy, e.g. one
extracted with `git archive main skills/tdd/scripts`, to test it without touching the worktree).
Needs git.
"""
import os
import sys
import tempfile

import lib
from lib import check, has, run

os.chdir(lib.ROOT)
RED_AT = lib.script_dir("skills/tdd/scripts") + "/red-at.sh"


tmpd = tempfile.TemporaryDirectory()
tmp = tmpd.name

# A repo whose first commit has the bug and second the fix; the check exists only untracked.
r = tmp + "/repo"
os.makedirs(r)


def git(*args):
    return run(["git", "-C", r] + list(args))


def gc(*args):
    return git("-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "--no-verify", *args)


def put(name, text):
    with open(r + "/" + name, "w") as f:
        f.write(text)


git("init", "-q")
put("lib.sh", "echo wrong\n")
git("add", "lib.sh")
gc("-m", "bug")
put("lib.sh", "echo right\n")
gc("-am", "fix")
put("check.sh", '[ "$(bash lib.sh)" = right ] && echo PASS || { echo FAIL; exit 1; }\n')


def redat(*args):
    return run(["bash", RED_AT] + list(args), cwd=r)


out, st = redat("HEAD~1", "--setup", "touch scratch.tmp", "--copy", "check.sh", "--", "bash", "check.sh")
check(st == 1, "red-at.sh: on the bug commit exited %d, want 1: %s" % (st, out))
has("red-at.sh", out, "FAIL")
out, st = redat("HEAD", "--copy", "check.sh", "--", "bash", "check.sh")
check(st == 0, "red-at.sh: on the fix commit exited %d, want 0: %s" % (st, out))
has("red-at.sh", out, "PASS")
wl = git("worktree", "list")[0]
check(len(wl.split("\n")) == 1, "red-at.sh: left a worktree: %s" % wl)
sp_ = git("status", "--porcelain")[0]
check(sp_ == "?? check.sh", "red-at.sh: changed the worktree: %s" % sp_)
_, st = redat("nope", "--copy", "check.sh", "--", "true")
check(st == 2, "red-at.sh: unknown rev exited %d, want 2" % st)
_, st = redat("HEAD", "--", "true")
check(st == 2, "red-at.sh: no --copy exited %d, want 2" % st)
out, st = redat("HEAD~1", "--setup", "false", "--copy", "check.sh", "--", "bash", "check.sh")
check(st == 125, "red-at.sh: failing setup exited %d, want 125: %s" % (st, out))
has("red-at.sh", out, "setup failed")
out, st = redat("HEAD", "--copy", "check.sh", "--copy", "lib.sh", "--", "bash", "check.sh")
check(st == 0, "red-at.sh: repeated --copy exited %d, want 0: %s" % (st, out))

tmpd.cleanup()

sys.exit(lib.finish())
