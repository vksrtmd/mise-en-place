#!/usr/bin/env python3
"""Runs skills/retro/scripts/digest.py on transcripts built in a temp dir; prints a line per failed
expectation and exits 1 when any fails.

Usage: tests/test_retro_digest.py [scripts dir]  (default skills/retro/scripts; pass another copy, e.g. one
extracted with `git archive main skills/retro/scripts`, to test it without touching the worktree; a copy
from before the port holds digest.sh instead of digest.py and runs through that).
"""
import os
import sys
import tempfile

import lib
from lib import check, handback, has, jl, lacks, res, run, sed_range, use, user, write

os.chdir(lib.ROOT)
DIR = lib.script_dir("skills/retro/scripts")


def digest(*args, env=None):
    # An old copy of the scripts (git archive of a commit before the port) still has digest.sh.
    if os.path.isfile(DIR + "/digest.py"):
        cmd = ["python3", DIR + "/digest.py"]
    else:
        cmd = ["bash", DIR + "/digest.sh"]
    return run(cmd + list(args), env=env)



tmpd = tempfile.TemporaryDirectory()
tmp = tmpd.name

s = tmp + "/session"
os.makedirs(s + "/subagents")
write(s + ".jsonl", [
    use("m1", "Bash", "git ls-remote --heads origin x"), res("m1", False, ""),
    use("m3", "Bash", "wc -l digest.sh && cat digest.sh | head -40"), res("m3", False, "friction='[Pp]ermission denied|timed out'"),
    user("<command-name>/retro</command-name>"),
    use("m2", "Bash", "bash digest.sh ~/.claude/projects/p/session"), res("m2", True, "error: the retro's own call"),
])
write(s + "/subagents/agent-1.jsonl", [
    user("Fix the skip reasons in the runner."),
    use("a1", "Bash", "npm test"), res("a1", True, "Exit code 1\nok 1 - loads\nnot ok 2 - parses skip reasons"),
    use("a2", "Bash", "git worktree list"), res("a2", False, "/r abc [main]\n/r/.claude/worktrees/timeout-fix def [timeout-fix] prunable"),
    use("a3", "Bash", "echo exit=1 free"), res("a3", False, "exit=1 free"),
    use("a4", "Bash", "npm test"), res("a4", False, "ok 1 - loads\nok 2 - parses skip reasons"),
    use("a5", "Bash", "npm run lint"), res("a5", False, "src/a.ts\n  3:1  error  no-console\n✖ 1 problem"),
    use("a6", "Bash", "cd src && cat server.js"), res("a6", False, "  if (e.code === 'EADDRINUSE') retry()"),
    use("a7", "Bash", "node dump.js"), res("a7", False, "error: { code: 1 }"),
    use("a8", "Bash", "node --test --test-name-pattern dates"), res("a8", True, "✖ parses dates (1.2ms)\n✖ failing tests:"),
    use("a9", "Bash", "node --test"), res("a9", False, "✔ loads (0.4ms)\n✔ parses dates (0.9ms)"),
    use("a10", "Bash", "true", ts="2026-01-01T11:00:00.000Z"), res("a10", False, ""),
    handback("Tests pass. I assumed the skips are the box's usual ones, without checking each. Only `unverified` findings were reproduced. The flag order was checked by hand; no automated test covers it. A guessed token is rejected. - **If we skip it:** accounting fixes them by hand."),
    jl({"type": "assistant", "timestamp": "2026-01-01T10:01:00.000Z", "message": {"model": "claude-opus-5-5", "content": [], "usage": {"output_tokens": 2000}}}),
])
write(s + "/subagents/agent-1.meta.json", ['{"description":"Fix skips"}'])
write(s + "/subagents/agent-3.jsonl", [handback("## Findings\n- **The Renovate fixture assumes v2**\n  What this is: the fixture assumes a v2 config.\n  Problem: no test covers v3.\n## Not checked\n- the pid reuse on restart\n**Unconfirmed:** the lock order.\n**Fixed**\n- I assumed bash 5.")])
write(s + "/subagents/agent-4.jsonl", [handback("- **The fixture assumes v2.** It could not load v3.\n  What this is: the fixture assumes v2.\nI assumed the host runs bash 5.")])
write(s + "/subagents/agent-2.jsonl", [
    user("Fix the timeout."),
    use("b1", "Bash", "npm test", ts="2026-01-01T10:00:00.000Z"),
    jl({"type": "assistant", "timestamp": "2026-01-01T10:10:00.000Z", "isApiErrorMessage": True, "error": "rate_limit", "message": {"content": [{"type": "text", "text": "You have hit your 5-hour limit"}]}}),
    res("b1", False, "ok 1 - loads", ts="2026-01-01T13:10:00.000Z"),
    use("b2", "Bash", "cd /r; git fetch; gh pr view 9 --json body"), res("b2", False, '{"body":"✖ 1 quoted problem"}'),
    use("b3", "Bash", 'f=$(ls -t | head -1); digest.sh "$f"'), res("b3", False, "  ! Bash @3: No such file or directory, quoted"),
    use("b4", "Bash", "node a.js"), res("b4", False, "  ! Bash ×2 @2,@6: Socket is closed · curl a"),
    use("b5", "Bash", "node a.js"), res("b5", False, "  ? Bash @11: ✖ 1 problem · npm run lint"),
    use("b6", "Bash", "echo $((1+2)) && sed -n 1,5p a.sh"), res("b6", False, "error: arith source"),
    handback("Done. All checks run. Not confirmed: the retry count. The sizes are estimates from the code. I did not import a big database."),
])
# A hedge the brief ordered, and hedge words inside quotes.
write(s + "/subagents/agent-5.jsonl", [
    user("Fix the dedupe. Skip check.sh: the orchestrator runs it."),
    handback("I didn't run check.sh. The header says \"could not reach\" and pr-push's one says 'unable to push'."),
])
# Source printed by reader shapes beyond a plain pipe: `|| true`, git grep, a for loop, a subshell, an if.
R = "2026-01-01T14:00:00.000Z"
write(s + "/subagents/agent-6.jsonl", [
    use("r1", "Bash", "grep -rn error src || true", ts=R), res("r1", False, "    error: String,", ts=R),
    use("r2", "Bash", "git grep -n Error", ts=R), res("r2", False, "error: io::Error", ts=R),
    use("r3", "Bash", 'for f in src/*.rs; do\n  grep -n error "$f"\ndone', ts=R), res("r3", False, "error: Box<dyn Error>", ts=R),
    use("r4", "Bash", "(cd src && cat main.rs)", ts=R), res("r4", False, "error: Subshell", ts=R),
    use("r5", "Bash", "if [ -f a.rs ]; then cat a.rs; else cat b.rs; fi", ts=R), res("r5", False, "error: IfElse", ts=R),
    # Loops and command substitutions that run a non-reader still flag.
    use("r6", "Bash", 'for f in $(cargo build 2>&1); do echo "$f"; done', ts=R), res("r6", False, "error: could not compile", ts=R),
    use("r7", "Bash", 'for t in a b; do\n  cargo test "$t"\ndone', ts=R), res("r7", False, "error: test failed", ts=R),
    # Command words end at whitespace: a name that only starts with one is no reader. Any command substitution flags; [[ reads.
    use("r8", "Bash", "test-runner --all", ts=R), res("r8", False, "error: runner failed", ts=R),
    use("r9", "Bash", "cat x && test.sh", ts=R), res("r9", False, "error: dotted failed", ts=R),
    use("r10", "Bash", "echo $(cargo build)", ts=R), res("r10", False, "error: echo subst", ts=R),
    use("r11", "Bash", "cat $(make 2>&1)", ts=R), res("r11", False, "error: cat subst", ts=R),
    use("r12", "Bash", "grep x <(cargo build 2>&1)", ts=R), res("r12", False, "error: process subst", ts=R),
    use("r13", "Bash", "echo `cargo build`", ts=R), res("r13", False, "error: backtick subst", ts=R),
    use("r14", "Bash", "[[ -f x ]] && cat x", ts=R), res("r14", False, "error: DoubleBracket", ts=R),
    # Rust paths in printed source (a nested use list) are no error lines.
    use("r15", "Bash", "cat src/lib.rs && cargo fmt --check", ts=R),
    res("r15", False, "use crate::{\n    error::Result,\n    Error::Io,\n};", ts=R),
    # A segment of only assignments reads; one with a substitution still flags.
    use("r16", "Bash", "O=e321f66^\ngrep -n x f\ncat -n f\ngit show $O:f | sed -n 1,22p", ts=R), res("r16", False, "error: assign reader", ts=R),
    use("r17", "Bash", "O=$(make 2>&1)\ncat f", ts=R), res("r17", False, "error: assign subst", ts=R),
    # Lines of a diff section are quoted; a plain line after it is not.
    use("r18", "Bash", "python3 - <<'EOF'\nprint(1)\nEOF\ngit diff", ts=R),
    res("r18", False, "diff --git a/f b/f\nindex 1..2 100644\n--- a/f\n+++ b/f\n@@ -1,3 +1,2 @@\n-diffminus timed out\n+diffplus timed out\n diffctx timed out\n--- diffdash timed out", ts=R),
    use("r19", "Bash", "python3 - <<'EOF'\nprint(1)\nEOF\ngit diff", ts=R),
    res("r19", False, "diff --git a/f b/f\n@@ -1 +1 @@\n-diffgone timed out\nplainafter timed out", ts=R),
    use("r20", "Bash", "python3 t.py", ts=R), res("r20", False, "-nodiff timed out", ts=R),
    # cat -n lines are quoted; a plain line in the same call is a hit.
    use("r21", "Bash", 'cat -n x.sh; for t in tests/*.py; do $t; done', ts=R), res("r21", False, '   153\t[ ... ] && echo "numbered timed out"', ts=R),
    use("r22", "Bash", 'nl x.sh; for t in tests/*.py; do $t; done', ts=R), res("r22", False, '   153\t[ ... ] && echo "nl timed out"\nown test timed out', ts=R),
    use("r23", "Bash", "git diff; npx jest", ts=R), res("r23", False, "diff --git a/f b/f\n@@ -1 +1 @@\n-a\n+b\n FAIL  src/a.test.js", ts=R),
    use("r24", "Bash", "git diff && go test ./...", ts=R), res("r24", False, "diff --git a/f b/f\n@@ -1 +1 @@\n-a\n+b\n--- FAIL: TestX (0.00s)", ts=R),
    use("r25", "Bash", "git diff; ./t.sh", ts=R), res("r25", False, "diff --git a/f b/f\n@@ -1 +1 @@\n-a\n+b\n error: something broke", ts=R),
    use("r26", "Bash", "git diff; npx jest", ts=R), res("r26", False, "diff --git a/f b/f\n@@ -1 +1 @@\n-a\n+b\n  ✖ t1", ts=R),
    use("r27", "Bash", "git diff HEAD~1; ./check.sh", ts=R), res("r27", False, "diff --git a/f b/f\n@@ -1 +1 @@\n-a\n+b\n- timed out waiting", ts=R),
    use("r30", "Bash", "git diff; ./t.sh", ts=R), res("r30", False, "diff --git a/f b/f\n@@ -1 +1 @@\n-a\n+b\n--- afterdash timed out", ts=R),
    use("r28", "Bash", "./run.sh --nl x", ts=R), res("r28", False, "   3\tnlflag timed out", ts=R),
    use("r29", "Bash", "go test ./... 2>&1 | nl", ts=R), res("r29", False, "     1\t--- FAIL: TestPipeNl", ts=R),
    use("r31", "Bash", "cd x && cat -n f", ts=R), res("r31", False, "   2\tafterand timed out", ts=R),
    use("r32", "Bash", "git diff; ./t.sh", ts=R), res("r32", False, 'diff --git a/f b/f\n@@ -1 +1 @@ it("hunkhead timed out")\n-a\n+b', ts=R),
    use("r33", "Bash", "git diff; ./t.sh", ts=R), res("r33", False, "diff --git a/f b/f\n@@ -0,0 +1 @@\n-negcount timed out", ts=R),
])

out, st = digest(s, "200")
check(not st, "digest.py: exited %d: %s" % (st, out))
has("digest.py", out, "## Fix skips [inherit] · 1 · 10:00")
rk = sed_range(out, r"^## agents by out tokens", r"^$")
has("digest.py ranking", rk.split("\n")[1], "2100 Fix skips [inherit] · 1 · 10:00")
has("digest.py ranking", rk, "  main log, unranked: 20")
has("digest.py", out.split("\n")[0], "## agents by out tokens")
has("digest.py", out, "prompt: Fix the skip reasons in the runner.")
has("digest.py", out, "  ~ Bash @3: not ok 2 - parses skip reasons · npm test")
has("digest.py", out, "  ? Bash @11: ✖ 1 problem · npm run lint")
lacks("digest.py", out, "EADDRINUSE")
lacks("digest.py", out, "error: {")
lacks("digest.py", out, "error: String")
lacks("digest.py", out, "assign reader")
has("digest.py", out, "error: assign subst")
lacks("digest.py", out, "diffminus")
lacks("digest.py", out, "diffplus")
lacks("digest.py", out, "diffctx")
lacks("digest.py", out, "diffdash")
lacks("digest.py", out, "diffgone")
has("digest.py", out, "plainafter timed out")
has("digest.py", out, "-nodiff timed out")
lacks("digest.py", out, "numbered timed out")
lacks("digest.py", out, "nl timed out")
has("digest.py", out, "own test timed out")
has("digest.py", out, "FAIL src/a.test.js")
has("digest.py", out, "--- FAIL: TestX")
has("digest.py", out, "error: something broke")
has("digest.py", out, "✖ t1")
has("digest.py", out, "- timed out waiting")
has("digest.py", out, "nlflag timed out")
has("digest.py", out, "TestPipeNl")
lacks("digest.py", out, "afterand")
lacks("digest.py", out, "hunkhead")
has("digest.py", out, "negcount timed out")
has("digest.py", out, "afterdash timed out")
lacks("digest.py", out, "error: io::Error")
lacks("digest.py", out, "error: Box")
lacks("digest.py", out, "error: Subshell")
lacks("digest.py", out, "error: IfElse")
lacks("digest.py", out, "error: DoubleBracket")
lacks("digest.py", out, "error::Result")
lacks("digest.py", out, "Error::Io")
for e in ["runner failed", "dotted failed", "echo subst", "cat subst", "process subst", "backtick subst"]:
    has("digest.py", out, ": error: " + e)
has("digest.py", out, "? Bash @12: error: could not compile")
has("digest.py", out, "? Bash @14: error: test failed")
has("digest.py", out, "  ~ Bash @17: ✖ parses dates (1.2ms)")
lacks("digest.py", out, "the retro's own call")
ml = sed_range(out, r"^## main session", r"^## ")
lacks("digest.py main block", ml, "-- calls")
lacks("digest.py main block", ml, "  Bash: git ls-remote --heads origin x")
lacks("digest.py default digest", out, "-- calls")
LS_LINE = [i for i, l in enumerate(open(s + ".jsonl"), 1) if "git ls-remote --heads origin x" in l and '"tool_use"' in l][0]
cout, _ = digest("--calls", s + ".jsonl")
has("digest.py --calls", cout, "  @%d Bash: git ls-remote --heads origin x" % LS_LINE)
lacks("digest.py --calls", cout, "-- calls")
cout, _ = digest("--calls", s + ".jsonl", "12")
has("digest.py --calls width", cout, "  @%d Bash: git ls-r" % LS_LINE)
lacks("digest.py --calls width", cout, "git ls-remote")
# The user turns of the log before the cut print whether or not a digest.sh call truncated it.
has("digest.py current session", ml, "  prompt: <command-name>/retro</command-name>")
has("digest.py current session", ml, "  -- user turns")
# A past session: the main block carries the prompt and the later user turns, each with its UTC time.
write(tmp + "/past.jsonl", [
    user("<local-command-caveat>Caveat: run directly.</local-command-caveat>"),
    user("<local-command-stdout>stdout noise</local-command-stdout>"),
    user("Plan   the\nmigration.", timestamp="2026-01-01T09:07:00.000Z"),
    user("<task-notification><task-id>x</task-id></task-notification>"),
    user([{"type": "text", "text": "<system-reminder>reminder noise</system-reminder>"}]),
    user("<command-name>/retro</command-name>"),
    user("Keep this. <system-reminder>\ninline\nnoise\n</system-reminder>"),
    user("Another Claude session sent a message:\n<agent-message from=\"a1\">\n[Subagent hand-back] report text</agent-message>"),
    user("peer words", origin={"kind": "peer", "from": "a1"}),
    use("p1", "Bash", "ls"), res("p1", False, "a.txt"),
    user("meta noise", isMeta=True),
    user([{"type": "text", "text": "Now  do\nthe second part."}], timestamp="2026-01-01T09:42:00.000Z"),
    user("Why does <agent-message from=x> get dropped?"),
])
pm, _ = digest(tmp + "/past.jsonl", "200")
has("digest.py past session", pm, "  prompt: Plan the migration.")
has("digest.py past session", pm, "  -- user turns")
has("digest.py past session", pm, "  @13 09:42: Now do the second part.")
has("digest.py past session", pm, "  @6 ??:??: <command-name>/retro</command-name>")
has("digest.py past session", pm, "  @7 ??:??: Keep this.")
has("digest.py past session", pm, "  prompt: Plan the migration.")
has("digest.py past session", pm, "Why does <agent-message from=x> get dropped?")
lacks("digest.py past session", pm, "hand-back")
lacks("digest.py past session", pm, "peer words")
lacks("digest.py past session", pm, "noise")
lacks("digest.py past session", pm, "Caveat")
lacks("digest.py past session", pm, "task-notification")
lacks("digest.py past session", pm, "a.txt")
lacks("digest.py past session", pm, "meta noise")
lacks("digest.py past session", pm, "@1:")
lacks("digest.py main calls", ml, "Bash: bash digest.sh")
has("digest.py", out, "  ⏸ rate_limit @3: You have hit your 5-hour limit · at 01-01 10:10 UTC · paused 180 min (limit 50, then waiting to be resumed 130)")
has("digest.py", out, "    out tokens since the start: ? 180, opus-5-5 2k")
lacks("digest.py", out, "ermission denied|timed out")
has("digest.py", out, "· 10 min ·")
hd = sed_range(out, r"^## hedges", r"^## repeated")
has("digest.py hedges", hd, "Fix skips · 1: The flag order was checked by hand;")
has("digest.py hedges", hd, "Fix skips · 1: no automated test covers it.")
has("digest.py hedges", hd, "agent · 2: Not confirmed: the retry count.")
# A hedge outside the usual verbs: an estimate, and a step the agent did not take.
has("digest.py hedges", hd, "agent · 2: The sizes are estimates from the code.")
has("digest.py hedges", hd, "agent · 2: I did not import a big database.")
lacks("digest.py hedges", hd, "All checks run")
lacks("digest.py hedges", hd, "A guessed token")
lacks("digest.py hedges", hd, "If we skip it")
has("digest.py hedges", hd, "agent · 3: - the pid reuse on restart")
has("digest.py hedges", hd, "agent · 3: **Unconfirmed:** the lock order.")
lacks("digest.py hedges", hd, "agent · 3: ## Not checked")
lacks("digest.py hedges", hd, "Renovate")
lacks("digest.py hedges", hd, "agent · 3: - I assumed bash 5.")
has("digest.py hedges", hd, "agent · 4: I assumed the host runs bash 5.")
lacks("digest.py hedges", hd, "agent · 4: - **The fixture")
lacks("digest.py hedges", hd, "could not load v3")
lacks("digest.py hedges", hd, "agent · 4: What this is")
lacks("digest.py", out, "timeout-fix def")
lacks("digest.py", out, "! Bash: exit=1")
has("digest.py", out, "## hedges in reports")
has("digest.py", out, "Fix skips · 1: I assumed the skips are the box's usual ones, without checking each.")
lacks("digest.py", out, ": Only `unverified` findings")
lacks("digest.py", out, "agent · 2: Done.")
lacks("digest.py", out, "quoted")
lacks("digest.py", out, "Socket is closed · node a.js")
lacks("digest.py", out, "· node a.js")
lacks("digest.py", out, "error: arith source")
has("digest.py", out, "2 npm test")
has("digest.py hedges", hd, "agent · 5 brief: Skip check.sh: the orchestrator runs it.")
has("digest.py hedges", hd, "agent · 5: I didn't run check.sh.")
lacks("digest.py hedges", hd, "could not reach")
lacks("digest.py hedges", hd, "agent · 4 brief")
# The prompt line skips a turn that is only a slash-command wrapper; the wrapper still prints under user turns.
write(tmp + "/slash.jsonl", [
    user("<command-name>/discuss</command-name>\n<command-message>discuss</command-message>\n<command-args>the plan</command-args>"),
    user("Settle the plan for caching."),
])
out, _ = digest(tmp + "/slash.jsonl", "200")
has("digest.py slash prompt", out, "  prompt: Settle the plan for caching.")
has("digest.py slash prompt", out, "  @1 ??:??: <command-name>/discuss</command-name>")
lacks("digest.py slash prompt", out, "  prompt: <command-name>")
# ⌛ lines: a call that sat over 5 min before the next entry, and a Bash moved to the background after its timeout; not a
# gap an API-error pause covers, nor a background run the agent asked for.
write(tmp + "/wait.jsonl", [
    user("Run the long build.", timestamp="2026-01-01T10:00:00.000Z"),
    use("w1", "Bash", "sleep   400", ts="2026-01-01T10:00:00.000Z"), res("w1", False, "done", ts="2026-01-01T10:07:00.000Z"),
    use("w2", "Bash", "ls", ts="2026-01-01T10:08:00.000Z"), res("w2", False, "a", ts="2026-01-01T10:09:00.000Z"),
    use("w3", "Bash", "npm run dev", ts="2026-01-01T10:10:00.000Z"),
    res("w3", False, "Command timed out after 120s and was moved to the background (ID: bg1).", ts="2026-01-01T10:10:30.000Z"),
    jl({"type": "assistant", "timestamp": "2026-01-01T10:11:00.000Z", "message": {"content": [{"type": "tool_use", "id": "w4", "name": "Bash", "input": {"command": "npm run watch", "run_in_background": True}}]}}),
    res("w4", False, "Command running in background with ID: bg2.", ts="2026-01-01T10:11:01.000Z"),
])
wm, _ = digest(tmp + "/wait.jsonl", "200")
has("digest.py waits", wm, "  ⌛ @2: 7 min after · sleep 400")
has("digest.py waits", wm, "  ⌛ @6: moved to background · npm run dev")
lacks("digest.py waits", wm, "⌛ @7")
lacks("digest.py waits", wm, "⌛ @4")
lacks("digest.py waits", wm, "npm run watch ·")
lacks("digest.py waits", wm, "⌛ @9")
out, _ = digest(s, "200")
lacks("digest.py waits", out, "⌛ @2:")
# A result that quotes the phrase, below its first line or after another opening, is no move to the background.
write(tmp + "/quote.jsonl", [
    use("q1", "Bash", "git log --oneline", ts="2026-01-01T10:00:00.000Z"),
    res("q1", False, "abc123 digest.sh: flag long waits\ndef456 flag Bash moved to the background", ts="2026-01-01T10:00:02.000Z"),
    use("q2", "Bash", "tests/test_retro_digest.py", ts="2026-01-01T10:00:00.000Z"),
    res("q2", False, "digest.sh waits: output lacks:   ⌛ @6: moved to background · npm run dev", ts="2026-01-01T10:00:02.000Z"),
])
out, _ = digest(tmp + "/quote.jsonl", "200")
lacks("digest.py waits quoted", out, "⌛")
# Parallel calls: one assistant entry per call, the results after; the slow call in the batch is flagged, on its own line.
write(tmp + "/par.jsonl", [
    use("pa", "Bash", "fast", ts="2026-01-01T10:00:00.000Z"), use("pb", "Bash", "slow build", ts="2026-01-01T10:00:00.000Z"),
    res("pa", False, "ok", ts="2026-01-01T10:00:01.000Z"), res("pb", False, "ok", ts="2026-01-01T10:08:00.000Z"),
])
out, _ = digest(tmp + "/par.jsonl", "200")
has("digest.py waits parallel", out, "  ⌛ @2: 8 min after · slow build")
lacks("digest.py waits parallel", out, "· fast")
# --text prints the assistant's prose; --around leaves out entries that only carry harness context and takes a width.
write(tmp + "/txt.jsonl", [
    user("Hello there"),
    user("meta ctx", isMeta=True),
    user([{"type": "text", "text": "<system-reminder>\nreminder noise\n</system-reminder>"}]),
    user([{"type": "text", "text": "# Environment update\n - cwd moved"}]),
    jl({"type": "attachment", "attachment": {"type": "environment"}, "message": {"content": "att noise"}}),
    jl({"type": "api-request-blob", "message": [{"type": "text", "text": "blob noise"}]}),
    jl({"type": "assistant", "message": {"content": [{"type": "text", "text": "I will   run\nthe tests."}, {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "npm test"}}]}}),
])
out, _ = digest("--around", tmp + "/txt.jsonl", "4", "4")
has("digest.py --around harness", out, "@1 Hello there")
has("digest.py --around harness", out, "@7 I will run the tests.")
for x in ["meta ctx", "reminder noise", "Environment update", "att noise", "blob noise"]:
    lacks("digest.py --around harness", out, x)
write(tmp + "/rem.jsonl", [
    user([{"type": "text", "text": "Run it. <system-reminder>\nmixed noise\n</system-reminder>"}]),
    user([{"type": "tool_result", "tool_use_id": "r", "content": "all passed\n<system-reminder>\nresult noise\n</system-reminder>"}]),
])
out, _ = digest("--around", tmp + "/rem.jsonl", "1", "1")
has("digest.py --around inline reminder", out, "@1 Run it.")
has("digest.py --around inline reminder", out, "@2 result: all passed")
lacks("digest.py --around inline reminder", out, "noise")
out, _ = digest("--around", tmp + "/txt.jsonl", "7", "0", "10")
has("digest.py --around width", out, "@7 I will run")
lacks("digest.py --around width", out, "the tests")
# --around counts its radius in printed entries: noise lines between a result and the next call do not use it up.
write(tmp + "/noisegap.jsonl", [
    jl({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "g1", "name": "Bash", "input": {"command": "first"}}]}}),
    user([{"type": "tool_result", "tool_use_id": "g1", "content": "done"}]),
    jl({"type": "attachment", "attachment": {"type": "x"}, "message": {"content": "n1"}}),
    jl({"type": "last-prompt", "lastPrompt": "n2"}),
    jl({"type": "permission-mode", "permissionMode": "default"}),
    user("meta noise", isMeta=True),
    jl({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "g2", "name": "Bash", "input": {"command": "second"}}]}}),
])
out, _ = digest("--around", tmp + "/noisegap.jsonl", "2", "1")
has("digest.py --around noise gap", out, "@7 Bash: ")
has("digest.py --around noise gap", out, "@1 Bash: ")
lacks("digest.py --around noise gap", out, "noise")
out, _ = digest("--text", tmp + "/txt.jsonl")
has("digest.py --text", out, "@7 I will run the tests.")
lacks("digest.py --text", out, "Hello there")
lacks("digest.py --text", out, "npm test")
out, _ = digest("--text", tmp + "/txt.jsonl", "10")
has("digest.py --text width", out, "@7 I will run")
lacks("digest.py --text width", out, "the tests")
out, st = digest("-h")
check(not st, "digest.py -h: exited %d" % st)
has("digest.py -h", out, "Symbols:")
# A mistyped session path fails loudly instead of printing an empty digest.
out, st = digest(tmp + "/no-such-session")
check(st == 2, "digest.py missing session: exited %d, want 2: %s" % (st, out))
has("digest.py missing session", out, "no session dir or log")
# A session dir with subagents and no main log beside it still digests.
os.makedirs(tmp + "/nomain/subagents")
write(tmp + "/nomain/subagents/agent-1.jsonl", [use("n1", "Bash", "npm test"), res("n1", False, "ok")])
out, st = digest(tmp + "/nomain")
check(st == 0, "digest.py no main log: exited %d, want 0: %s" % (st, out))
has("digest.py no main log", out, "## agents by out tokens")
out, _ = digest("--around", s + "/subagents/agent-1.jsonl", "16", "1")
has("digest.py --around", out, "@15 result: error: { code: 1 }")
has("digest.py --around", out, '@16 Bash: {"command":"node --test --test-name-pattern dates"}')
has("digest.py --around", out, "@17 result (error): ✖ parses dates (1.2ms) ✖ failing tests:")
lacks("digest.py --around", out, "@14")
# A retro queued at the session's start: the work before its digest.sh call on this session stays in, an edit of
# digest.sh included.
write(tmp + "/queued.jsonl", [
    user("<command-name>/retro</command-name>"),
    use("q1", "Bash", "npm run lint"), res("q1", False, "✖ 1 queued problem"),
    use("q3", "Bash", "bash skills/retro/scripts/digest.sh --around x.jsonl 3"), res("q3", True, "error: editing digest.sh"),
    use("q2", "Bash", "skills/retro/scripts/digest.sh /p/queued.jsonl"), res("q2", True, "error: the queued retro's own call"),
])
out, _ = digest(tmp + "/queued.jsonl")
has("digest.py queued", out, "  ? Bash @3: ✖ 1 queued problem")
lacks("digest.py queued", out, "the queued retro's own call")
has("digest.py queued", out, "editing digest.sh")
# The script's new name cuts the log too, as the old one did.
write(tmp + "/queuedpy.jsonl", [
    use("q1", "Bash", "npm run lint"), res("q1", False, "✖ 1 queued problem"),
    use("q2", "Bash", "skills/retro/scripts/digest.py /p/queuedpy.jsonl"), res("q2", True, "error: the py retro's own call"),
])
out, _ = digest(tmp + "/queuedpy.jsonl")
has("digest.py queued", out, "  ? Bash @2: ✖ 1 queued problem")
lacks("digest.py queued", out, "the py retro's own call")
# Failure marks: a mutation run under an env prefix, an expected red, red-at.sh, a quoted and a real traceback.
write(tmp + "/marks.jsonl", [
    use("r1", "Bash", "KIT_MUTANT=/tmp/mut tests/kit.sh"), res("r1", True, "Exit code 1\nFAIL kit"),
    use("r2", "Bash", "tests/kit.sh"), res("r2", False, "PASS"),
    use("r3", "Bash", "tests/on-base.sh"), res("r3", True, "Exit code 1\nnot ok 1 - fixed"),
    use("r4", "Bash", "skills/tdd/scripts/red-at.sh HEAD~1 --copy t.sh -- t.sh"), res("r4", True, "Exit code 1\nFAIL t"),
    use("r5", "Bash", "awk '/TRACEBACK/' harness.py"), res("r5", False, 'harness.py:3:TRACEBACK = "Traceback (most recent call last)"'),
    use("r6", "Bash", "python3 run.py"), res("r6", True, "Exit code 1\nTraceback (most recent call last):"),
    use("r7", "Bash", "red-at.sh HEAD --setup 'git apply m.diff' --copy t.sh -- t.sh"), res("r7", True, "Exit code 125\nred-at: setup failed"),
])
out, _ = digest(tmp + "/marks.jsonl")
has("digest.py marks", out, "  ~ Bash @2: FAIL kit · tests/kit.sh")
has("digest.py marks", out, "  ! Bash @6: not ok 1 - fixed")
has("digest.py marks", out, "  ~ Bash @8: FAIL t")
lacks("digest.py marks", out, "TRACEBACK =")
has("digest.py marks", out, "  ! Bash @12: Traceback (most recent call last):")
has("digest.py marks", out, "  ! Bash @14: Exit code 125 red-at: setup failed · red-at.sh HEAD")
out, _ = digest(tmp + "/marks.jsonl", env={"EXPECTED_RED": "on-base"})
has("digest.py EXPECTED_RED", out, "  ~ Bash @6: not ok 1 - fixed")

# Identical flagged lines of one transcript collapse into one line with a count and the @lines; --help prints the legend.
write(tmp + "/groups.jsonl", [
    use("g1", "Bash", "curl localhost:1"), res("g1", True, "Socket is closed"),
    use("g2", "Bash", "curl localhost:2"), res("g2", True, "Socket is closed"),
    use("g3", "Bash", "curl localhost:1"), res("g3", True, "Socket is closed"),
])
out, _ = digest(tmp + "/groups.jsonl")
has("digest.py groups", out, "  ! Bash ×2 @2,@6: Socket is closed · curl localhost:1")
has("digest.py groups", out, "  ! Bash @4: Socket is closed · curl localhost:2")
out, st = digest("--help")
check(st == 0, "digest.py --help exited %d: %s" % (st, out))
has("digest.py --help", out, "Usage:")
has("digest.py --help", out, "×N")
has("digest.py --help", out, "EXPECTED_RED")

# --- digest.py: friction repeated across agents, shared briefs, the brief template, --prompt, ⏸ merging.
def agent_dir(name, agents):
    d = "%s/%s/subagents" % (tmp, name)
    os.makedirs(d)
    for aid, lines in agents.items():
        write("%s/agent-%s.jsonl" % (d, aid), lines)
    return "%s/%s" % (tmp, name)


def bad(i, c, t):
    return [use(i, "Bash", c), res(i, True, t)]


fr = agent_dir("fr", {
    "aaaaaaaa11": bad("a1", "sleep 1", "Blocked: sleep") + bad("a2", "sleep 2", "Blocked: sleep") + bad("a3", "x", "Other: once"),
    "bbbbbbbb22": bad("b1", "sleep 5", "Blocked: sleep") + [use("b2", "Bash", "sleep 5"), res("b2", False, "ok")],
    "cccccccc33": bad("c1", "sleep 5", "Blocked: sleep") + bad("c2", "sleep 5", "Blocked: sleep"),
})
out, _ = digest(fr, "200")
fg = sed_range(out, r"^## friction repeated across agents", r"^$")
check("## friction repeated across agents" in out and out.index("## repeated across agents") < out.index("## friction repeated across agents"),
      "digest.py friction fanout: section is missing or not after the repeated-commands one")
has("digest.py friction fanout", fg, "  3 agents × 5 lines · Bash: Blocked: sleep · aaaaaaaa 2, cccccccc 2, bbbbbbbb 1")
lacks("digest.py friction fanout", fg, "Other: once")
# The digest has no ## to read section: --to-read carries those groups.
check("## to read" not in out, "digest.py: output still has a ## to read section")
out, _ = digest(s, "200")
check("## to read" not in out, "digest.py with an agent: output still has a ## to read section")
out, _ = digest("--help")
lacks("digest.py --help", out, "  ## to read")
# --to-read: the widen template and who -> path lines once at the top, short headings, then each group's window.
out, st = digest("--to-read", s)
check(st == 0, "digest.py --to-read exited %d: %s" % (st, out))
has("digest.py --to-read widen template", out, "widen: ")
has("digest.py --to-read widen template", out, "digest.py --around <transcript> <line> <radius>")
has("digest.py --to-read who path", out, "\n1 %s/subagents/agent-1.jsonl\n" % s)
check(out.count("--around") == 1, "digest.py --to-read: --around printed %d times" % out.count("--around"))
has("digest.py --to-read heading", out, "\n? 1 @11\n")
lacks("digest.py --to-read old heading", out, "  ? 1: ")
for n in (10, 11, 12):
    has("digest.py --to-read window", out, "\n@%d " % n)
lacks("digest.py --to-read radius", out, "\n@9 ")
lacks("digest.py --to-read ~ group", out, "@3 ")
out, _ = digest("--to-read", s, "2")
has("digest.py --to-read radius widens", out, "\n@9 ")
out, _ = digest("--to-read", fr)
# Blocked: sleep is in 3 agents: aaaaaaaa's window prints, the others are named on an also: line.
has("digest.py --to-read groups", out, "\n! aaaaaaaa @2\nalso: aaaaaaaa @4, cccccccc @2 \u00d72\n")
check("\n! bbbbbbbb" not in out and "\n! cccccccc" not in out, "digest.py --to-read: a collapsed agent prints its own window")
has("digest.py --to-read top", out, "\ncccccccc %s/subagents/agent-cccccccc33.jsonl\n" % fr)
has("digest.py --to-read blank between groups", out, "\n\n! ")
# Two agents with one key: one window plus an also: line.
two = agent_dir("two", {"aaaaaaaa11": bad("a1", "make", "E: boom"), "bbbbbbbb22": bad("b1", "make", "E: boom")})
out, _ = digest("--to-read", two)
has("digest.py --to-read also", out, "\n! aaaaaaaa @2\nalso: bbbbbbbb @2\n")
check(out.count("E: boom") == 1, "digest.py --to-read also: window printed %d times" % out.count("E: boom"))
# The main log's group keeps its own window, and is not named on an also: line.
os.makedirs(tmp + "/mainkey/m/subagents")
write(tmp + "/mainkey/m.jsonl", bad("m1", "make", "E: boom"))
write(tmp + "/mainkey/m/subagents/agent-aaaaaaaa11.jsonl", bad("a1", "make", "E: boom"))
write(tmp + "/mainkey/m/subagents/agent-bbbbbbbb22.jsonl", bad("b1", "make", "E: boom"))
out, _ = digest("--to-read", tmp + "/mainkey/m")
has("digest.py --to-read main kept", out, "\n! main @2\n")
has("digest.py --to-read main kept", out, "\n! aaaaaaaa @2\nalso: bbbbbbbb @2\n")
check(out.count("E: boom") == 2, "digest.py --to-read main kept: window printed %d times" % out.count("E: boom"))
# A call that hook attachments push out of the window prints above it.
write(tmp + "/gap.jsonl", [use("g1", "Bash", "git restore x"), jl({"type": "attachment"}), jl({"type": "attachment"}),
                           res("g1", True, "BLOCKED: discards work")])
out, _ = digest("--to-read", tmp + "/gap.jsonl")
has("digest.py --to-read call above window", out, "\n@1 Bash: ")
has("digest.py --to-read call above window", out, "\n@4 result (error): BLOCKED")
out, st = digest("--to-read", tmp + "/nonesuch")
check(st == 2, "digest.py --to-read missing session exited %d" % st)
out, st = digest("--to-read")
check(st == 1, "digest.py --to-read without target exited %d" % st)
out, st = digest("--to-read", s, "x")
check(st == 1, "digest.py --to-read bad radius exited %d" % st)
out, _ = digest(fr, "200", env={"MIN_AGENTS": "4"})
lacks("digest.py friction fanout", out, "Blocked: sleep · aaaaaaaa")

hd2 = agent_dir("hd2", {
    "aaaaaaaa": [user("Do the work. Skip check.sh. Never push."), handback("I assumed x.")],
    "bbbbbbbb": [user("Do the work. Skip check.sh. Only edit a.py."), handback("I assumed y.")],
    "cccccccc": [user("Do the work. Skip check.sh. Never push."), handback("I assumed z.")],
})
out, _ = digest(hd2, "200")
hd = sed_range(out, r"^## hedges", r"^$")
hl = hd.split("\n")
check(hl[1:3] == ["  all agents brief: Skip check.sh.", "  2 agents brief: Never push."],
      "digest.py shared brief: top lines are %r" % hl[1:3])
has("digest.py shared brief", hd, "  agent · bbbbbbbb brief: Only edit a.py.")
lacks("digest.py shared brief", hd, "agent · aaaaaaaa brief")
lacks("digest.py shared brief", hd, "agent · cccccccc brief")
has("digest.py shared brief", hd, "  agent · aaaaaaaa: I assumed x.")
lacks("digest.py shared brief template", out, "## brief template")

LONG = "L" * 300
tp = agent_dir("tp", {
    "aaaaaaaa": [user("Header line\n\nShared rule one   \nOnly A line\nShared rule two\n" + LONG), handback("done")],
    "bbbbbbbb": [user("Header line\nOnly B line\nShared rule two\nShared rule one\n" + LONG), handback("done")],
    "cccccccc": [user("Shared rule two\nHeader line\nShared rule one\n" + LONG), handback("done")],
})
out, _ = digest(tp, "200")
tl = sed_range(out, r"^## brief template", r"^$").split("\n")
check(tl[:5] == ["## brief template (lines in every agent's prompt)", "  Header line", "  Shared rule one",
                 "  Shared rule two", "  " + LONG], "digest.py brief template: section is %r" % tl[:5])
check("## brief template" in out and out.index("## agents by out tokens") < out.index("## brief template") < out.index("## hedges"),
      "digest.py brief template: not right after the ranking")
has("digest.py brief template", out, "  prompt: Only A line")
has("digest.py brief template", out, "  prompt: Only B line")
has("digest.py brief template", out, "  prompt: (template only)")
lacks("digest.py brief template", out, "  prompt: Header")
out, _ = digest("--prompt", tp + "/subagents/agent-aaaaaaaa.jsonl")
check(out == "Header line\n\nShared rule one   \nOnly A line\nShared rule two\n" + LONG,
      "digest.py --prompt: not the whole prompt: %r" % out)
out, _ = digest(hd2, "200")
lacks("digest.py brief template", out, "## brief template")
one = agent_dir("one", {"aaaaaaaa": [user("Header line"), handback("done")]})
out, _ = digest(one, "200")
lacks("digest.py brief template one agent", out, "## brief template")


# ⏸: tokens since the previous pause; back-to-back limit hits of one transcript print as one line.
def stop(t, text="You hit your limit"):
    return jl({"type": "assistant", "timestamp": "2026-01-01T%s:00.000Z" % t, "isApiErrorMessage": True,
               "error": "rate_limit", "message": {"content": [{"type": "text", "text": text}]}})


def ok(t, o, model="claude-opus-5-5"):
    return jl({"type": "assistant", "timestamp": "2026-01-01T%s:00.000Z" % t,
               "message": {"model": model, "content": [], "usage": {"output_tokens": o}}})


lim = agent_dir("lim", {
    "aaaaaaaa": [user("go", timestamp="2026-01-01T09:00:00.000Z"), ok("09:05", 100), stop("10:00"), stop("10:10"),
                 stop("10:20"), user("back", timestamp="2026-01-01T10:40:00.000Z"), ok("10:50", 50),
                 stop("11:00"), user("again", timestamp="2026-01-01T11:20:00.000Z")],
    "bbbbbbbb": [ok("10:15", 7, "claude-sonnet-5-5")],
})
out, _ = digest(lim, "200")
lm = sed_range(out, r"^## agent · aaaaaaaa", r"^$")
has("digest.py pauses", lm, "  ⏸ rate_limit ×3 @3,@4,@5: You hit your limit · at 01-01 10:00 UTC · paused 40 min (limit 15, then waiting to be resumed 25)")
has("digest.py pauses", lm, "    out tokens since the start: opus-5-5 100, sonnet-5-5 7")
has("digest.py pauses", lm, "  ⏸ rate_limit @8: You hit your limit · at 01-01 11:00 UTC · paused 20 min")
has("digest.py pauses", lm, "    out tokens since the previous pause: opus-5-5 50")
lacks("digest.py pauses", lm, "out tokens before it")
# A different message text between hits keeps them apart.
write(tmp + "/lim2.jsonl", [user("go", timestamp="2026-01-01T09:00:00.000Z"), stop("10:00"), stop("10:10", "Server busy"),
                            user("back", timestamp="2026-01-01T10:20:00.000Z")])
out, _ = digest(tmp + "/lim2.jsonl", "200")
has("digest.py pauses", out, "  ⏸ rate_limit @2: You hit your limit · at 01-01 10:00 UTC · paused 10 min")
has("digest.py pauses", out, "  ⏸ rate_limit @3: Server busy · at 01-01 10:10 UTC · paused 10 min")
# No model spent anything before the first stop: the quota went to other sessions.
has("digest.py pauses", out, "    out tokens since the start: none")

# An AskUserQuestion call shows each question and its option labels, cut to the width like other calls.
ask = {"questions": [{"question": "How should Cargo builds be limited?", "header": "Cargo", "multiSelect": False,
                      "options": [{"label": "Shared dir, cap 3 (Recommended)", "description": "d"},
                                  {"label": "Per-agent dirs + flock", "description": "d"},
                                  {"label": "Retro as written", "description": "d"}]}]}
write(tmp + "/ask.jsonl", [jl({"type": "assistant", "timestamp": "2026-01-01T10:00:00.000Z", "message": {
    "content": [{"type": "tool_use", "id": "q1", "name": "AskUserQuestion", "input": ask}], "usage": {"output_tokens": 1}}})])
out, _ = digest("--calls", tmp + "/ask.jsonl", "200")
has("digest.py --calls ask", out, "  @1 AskUserQuestion: [Shared dir, cap 3 (Recommended) | Per-agent dirs + flock | Retro as written] How should Cargo builds be limited?")
out, _ = digest("--calls", tmp + "/ask.jsonl", "20")
has("digest.py --calls ask width", out, "  @1 AskUserQuestion: [Shared dir, cap 3 (")

# A persisted result counts at the size its header names, in the total and the largest.
pre = "<persisted-output>\nOutput too large (%s). Full output saved to: /x/tool-results/a.txt\n\nPreview (first 2KB):\nabc"
for unit, text, want in [("KB", "83.3KB", "results 83 KB, largest 83 KB"), ("MB", "1.5MB", "results 1536 KB, largest 1536 KB")]:
    write(tmp + "/pers.jsonl", [use("p1", "Bash", "x"), res("p1", False, pre % text)])
    out, _ = digest(tmp + "/pers.jsonl", "200")
    has("digest.py persisted " + unit, out, want)
write(tmp + "/pers2.jsonl", [use("p1", "Bash", "x"), res("p1", False, "small"),
                             use("p2", "Bash", "y"), res("p2", False, [{"type": "text", "text": pre % "30KB"}])])
out, _ = digest(tmp + "/pers2.jsonl", "200")
has("digest.py persisted list", out, "results 30 KB, largest 30 KB")


# Hedges: a report line that only restates a limit the prompt set, and a row of numbers, are no gaps; the main log's
# prose is scanned too.
hn = agent_dir("hn", {
    "aaaaaaaa": [user("Fix the dedupe. Don't push. Never touch b.py."),
                 handback("I did not push. I didn't touch c.py.\n| step | estimated KB |\n| a | 12 |\n~120 KB estimated\n"
                          "I did not run the slow suite.")],
})
write(hn + ".jsonl", [
    user("Go."),
    jl({"type": "assistant", "message": {"content": [{"type": "text", "text": "Nobody re-reviewed the reworked step 1 after the merge. All green."}]}}),
])
out, _ = digest(hn, "200")
hd = sed_range(out, r"^## hedges", r"^$")
lacks("digest.py hedges echo", hd, "I did not push")
lacks("digest.py hedges echo", hd, "touch c.py")
has("digest.py hedges echo", hd, "agent · aaaaaaaa: I did not run the slow suite.")
lacks("digest.py hedges numbers", hd, "| step")
lacks("digest.py hedges numbers", hd, "| a |")
lacks("digest.py hedges numbers", hd, "~120 KB")
has("digest.py hedges main", hd, "main: Nobody re-reviewed the reworked step 1 after the merge.")
lacks("digest.py hedges main", hd, "All green")
write(tmp + "/solo.jsonl", [user("Go."), jl({"type": "assistant", "message": {"content": [{"type": "text", "text": "Nobody re-reviewed step 1."}]}})])
out, _ = digest(tmp + "/solo.jsonl", "200")
has("digest.py hedges main alone", out, "## hedges in reports\n  main: Nobody re-reviewed step 1.")

# --to-read: a hidden entry between a call and its result leaves the call inside the window; it prints once.
hid = agent_dir("hid", {"aaaaaaaa": [
    user("Go."),
    use("h1", "Bash", "make build"),
    jl({"type": "attachment", "attachment": {"type": "hook_success"}}),
    res("h1", True, "Exit code 2\nboom"),
    use("h2", "Bash", "true"), res("h2", False, ""),
]})
out, _ = digest("--to-read", hid)
check(out.count("@2 Bash: ") == 1, "digest.py --to-read hidden entry between call and result: call printed %d times: %s" % (out.count("@2 Bash: "), out))

# --to-read: EXPECTED_RED nudge for ! windows of agents briefed for red tests.
nr = agent_dir("nr", {
    "aaaaaaaa": [user("Do TDD: write the failing test first."), use("n1", "Bash", "npm test"), res("n1", True, "Exit code 1\nboom")],
    "bbbbbbbb": [user("Fix the thing."), use("n2", "Bash", "make"), res("n2", True, "Exit code 2\nfail")],
})
out, _ = digest("--to-read", nr)
has("digest.py --to-read red nudge", out, "\nnote: 1 ! windows in agents briefed for red tests (aaaaaaaa): when their reds were meant, rewrite with EXPECTED_RED='npm\\ test'\n")
has("digest.py --to-read red nudge after widen:", out, "<transcript> <line> <radius>\nnote: 1 ")
out, _ = digest("--to-read", nr, env={"EXPECTED_RED": "zzz"})
lacks("digest.py --to-read red nudge with EXPECTED_RED", out, "note:")
out, _ = digest("--to-read", fr)
lacks("digest.py --to-read red nudge without a red brief", out, "note:")

# Hedges: a fenced code block is no sentence, in a report, a gap section and the main log's prose.
fence = "```\ncurl -s https://x/y | jq .a; echo did not check\n```"
fh = agent_dir("fh", {
    "aaaaaaaa": [user("Go."), handback("Done.\n" + fence + "\nI assumed the host runs bash 5.")],
    "bbbbbbbb": [user("Go."), handback("**Unconfirmed:** the lock order.\n" + fence + "\n")],
})
write(fh + ".jsonl", [user("Go."), jl({"type": "assistant", "message": {"content": [{"type": "text", "text": "Ran:\n" + fence + "\nAll green."}]}})])
out, _ = digest(fh, "200")
hd = sed_range(out, r"^## hedges", r"^$")
lacks("digest.py hedges fence", hd, "curl")
has("digest.py hedges outside a fence", hd, "agent · aaaaaaaa: I assumed the host runs bash 5.")
has("digest.py hedges gap section with a fence", hd, "the lock order")
lacks("digest.py hedges main fence", hd, "main:")

tmpd.cleanup()

sys.exit(lib.finish())
