#!/usr/bin/env python3
"""Runs skills/retro/scripts/sessions.sh on fixture logs built in a temp dir; prints a line per failed
expectation and exits 1 when any fails.

Usage: tests/test_retro_sessions.py [scripts dir]  (default skills/retro/scripts; pass another copy, e.g. one
extracted with `git archive main skills/retro/scripts`, to test it without touching the worktree).
"""
import os
import sys
import tempfile

import lib
from lib import check, has, jl, lacks, run, write

os.chdir(lib.ROOT)
DIR = lib.script_dir("skills/retro/scripts")


tmpd = tempfile.TemporaryDirectory()
tmp = tmpd.name

# Fixture logs under $tmp/proj: one project dir per start dir, a log per session.
sp = tmp + "/proj"
for d in ["/-w-repo", "/-w-repo-wt/", "/-w-repo/bbbbbbbb1111/subagents"]:
    os.makedirs(sp + d, exist_ok=True)


def ent(ts, ty, b, c, o):
    return {"type": ty, "timestamp": ts, "gitBranch": b, "message": {"content": c, "usage": {"output_tokens": o}}}


write(sp + "/-w-repo/aaaaaaaa1111.jsonl", [
    '{"type":"mode","mode":"x"}',
    jl(ent("2026-11-16T09:00:00.000Z", "user", "main", "❯ first   prompt\nover lines", 0)),
    jl(ent("2026-11-16T09:05:00.000Z", "assistant", "main", [], 1500)),
])
write(sp + "/-w-repo/bbbbbbbb1111.jsonl", [
    jl(ent("2026-11-16T10:00:00.000Z", "user", "main", [{"type": "tool_result", "content": "skip me"}], 0)),
    jl(ent("2026-11-16T10:01:00.000Z", "user", "main", "<command-name>/implement</command-name><command-args>20</command-args>", 0)),
    jl(ent("2026-11-16T10:02:00.000Z", "assistant", "feat", [], 400)),
    jl(ent("2026-11-17T00:30:00.000Z", "assistant", "feat", [], 100)),
])
write(sp + "/-w-repo/bbbbbbbb1111/subagents/agent-1.jsonl", ["x"])
write(sp + "/-w-repo/bbbbbbbb1111/subagents/agent-2.jsonl", ["x"])
write(sp + "/-w-repo/cccccccc1111.jsonl", [jl(ent("2026-11-16T11:00:00.000Z", "assistant", "wt", [], 5))])
write(sp + "/-w-repo-wt/dddddddd1111.jsonl", [jl(ent("2026-11-16T12:00:00.000Z", "user", "wt", "in worktree", 0))])
# Opened with /clear: the caveat (isMeta) and the /clear command come before the first real prompt.
caveat = ent("2026-11-16T08:00:00.000Z", "user", "wt", "<local-command-caveat>The command below was run</local-command-caveat>", 0)
caveat["isMeta"] = True
write(sp + "/-w-repo-wt/eeeeeeee1111.jsonl", [
    jl(caveat),
    jl(ent("2026-11-16T08:00:01.000Z", "user", "wt", "<command-name>/clear</command-name><command-args></command-args>", 0)),
    jl(ent("2026-11-16T08:00:02.000Z", "user", "wt", "<local-command-stdout></local-command-stdout>", 0)),
    jl(ent("2026-11-16T08:01:00.000Z", "user", "wt", "after the clear", 0)),
])


def sess(*args, quiet=None):
    return run([DIR + "/sessions.sh"] + list(args), env={"CLAUDE_PROJECTS": sp}, merge=quiet)


def body(out):
    return [l for l in out.split("\n") if not l.startswith("#")]


out, _ = sess("/w/repo")
has("sessions.sh", out, "# %s/-w-repo" % sp)
has("sessions.sh", out, 'aaaaaaaa1111  11-16 09:00–09:05  main  out 2k  agents 0  "first prompt over lines"')
has("sessions.sh", out, 'bbbbbbbb1111  11-16 10:00–11-17 00:30  main→feat  out 500  agents 2  "/implement 20"')
lacks("sessions.sh", out, "skip me")
has("sessions.sh", out, 'cccccccc1111  11-16 11:00–11:00  wt  out 5  agents 0  "-"')
check("".join(l[:8] + " " for l in body(out)) == "cccccccc bbbbbbbb aaaaaaaa ", "sessions.sh: order is not newest first")
out, _ = sess("/w/repo", "/w/repo/wt")
has("sessions.sh", out, "# [2] %s/-w-repo-wt" % sp)
has("sessions.sh", out, '[2] eeeeeeee1111  11-16 08:00–08:01  wt  out 0  agents 0  ⟲ ? "after the clear"')
has("sessions.sh", out, "[1] aaaaaaaa1111  ")
lacks("sessions.sh", out, "caveat")
check(body(out)[0][4:12] == "dddddddd", "sessions.sh: merged list not newest first")
out, _ = sess("-n", "1", "/w/repo", "/w/repo/wt")
has("sessions.sh", out, "dddddddd")
lacks("sessions.sh", out, "cccccccc")
# A ⟲ row names the session it cleared: the latest-ending one in its dir that ended at or before its start; a session
# still live then is skipped.
os.makedirs(sp + "/-w-clr", exist_ok=True)
write(sp + "/-w-clr/oldoldol1111.jsonl", [jl(ent("2026-11-16T09:00:00.000Z", "user", "m", "old", 0)), jl(ent("2026-11-16T09:05:00.000Z", "assistant", "m", [], 1))])
write(sp + "/-w-clr/endedend1111.jsonl", [jl(ent("2026-11-16T10:00:00.000Z", "user", "m", "ended", 0)), jl(ent("2026-11-16T10:30:00.000Z", "assistant", "m", [], 1))])
write(sp + "/-w-clr/livelive1111.jsonl", [jl(ent("2026-11-16T10:10:00.000Z", "user", "m", "live", 0)), jl(ent("2026-11-16T12:00:00.000Z", "assistant", "m", [], 1))])
write(sp + "/-w-clr/clearclr1111.jsonl", [
    jl(ent("2026-11-16T11:00:00.000Z", "user", "m", "<command-name>/clear</command-name><command-args></command-args>", 0)),
    jl(ent("2026-11-16T11:01:00.000Z", "user", "m", "after clear", 0))])
out, _ = sess("/w/clr")
has("sessions.sh clear", out, 'clearclr1111  11-16 11:00–11:01  m  out 0  agents 0  ⟲ endedend "after clear"')
has("sessions.sh", sess("--help")[0], "Usage: sessions.sh")
check(sess("/w/none", quiet=False)[1] != 0, "sessions.sh: a start dir with no logs exited 0")


tmpd.cleanup()

sys.exit(lib.finish())
