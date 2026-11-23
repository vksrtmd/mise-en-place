#!/usr/bin/env python3
"""Runs skills/review-skill/scripts/timeline.sh on a transcript built in a temp dir; prints a line per
failed expectation and exits 1 when any fails.

Usage: tests/test_review_skill_timeline.py [scripts dir]  (default skills/review-skill/scripts; pass another
copy, e.g. one extracted with `git archive main skills/review-skill/scripts`, to test it without touching
the worktree).
"""
import os
import sys
import tempfile

import lib
from lib import check, has, jl, lacks, res, run, use, user, write

os.chdir(lib.ROOT)
TL = lib.script_dir("skills/review-skill/scripts") + "/timeline.sh"


tmpd = tempfile.TemporaryDirectory()
tmp = tmpd.name

# A rule's text reaches the agent in an attachment after a tool call; an api-request-blob replay, hook
# output, or a toolUseResult holding the agent's own edit, is not an arrival.
t = tmp + "/timeline.jsonl"
write(t, [
    user("Review the tdd skill."),
    jl({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "/r/a.sh"}}]}}), res("t1", False, "skill text"),
    jl({"type": "attachment", "attachment": {"type": "nested_memory", "content": "# Lean code\nKeep it short."}}),
    "not json",
    use("t2", "Bash", "ls skills -x"), res("t2", False, "# Lean code again\nls: invalid option -x"),
    jl({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t3", "content": "edited"}]}, "toolUseResult": {"newString": "# Agent wrote this", "originalFile": "# Never shown"}}),
    jl({"type": "attachment", "attachment": {"type": "nested_memory", "content": "Write \"one-line\" comments.\n\tTabbed"}}),
    jl({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t4", "name": "Edit", "input": {"file_path": "/a/very/long/worktree/head/that/every/call/shares/before/the/part/that/matters/src/cart.test.js"}}]}}),
    jl({"type": "attachment", "attachment": {"type": "hook_success", "command": "hook # Hooked", "stdout": "# Hooked"}}),
    jl({"type": "attachment", "attachment": {"type": "hook_additional_context", "content": ["# From hook"]}}),
    jl({"type": "attachment", "attachment": {"type": "nested_memory", "path": "/r/rules/lean.md", "content": "# Lean code"}}),
    jl({"type": "attachment", "attachment": {"type": "prompt_snapshot", "systemPrompt": "# System rule"}}),
    jl({"type": "attachment", "attachment": {"type": "deferred_tools_record", "tools": [{"description": "# Deferred"}]}}),
    jl({"type": "attachment", "attachment": {"type": "hook_success", "hookEvent": "SessionStart", "content": "# Session hook", "stdout": "# Session hook"}}),
    jl({"type": "api-request-blob", "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Bash", "input": {"command": "ls skills -x"}}]}}),
    jl({"type": "attachment", "attachment": {"type": "prompt_snapshot", "systemPrompt": "# System rule", "tools": [{"description": "# Tooled"}]}}),
])
out, st = run(["bash", TL, t, "# System rule", "# Deferred", "# Session hook", "# Tooled", "# From hook", "# Hooked", "# Lean code", "# Absent", "-x", "-n", "# Agent wrote this", "# Never shown", 'Write "one-line" comments.\n\tTabbed'])
check(not st, "timeline.sh: exited %d: %s" % (st, out))
has("timeline.sh", out, "2 Read: /r/a.sh")
has("timeline.sh", out, '4 MARK "# Lean code" in nested_memory entry')
has("timeline.sh", out, "6 Bash: ls skills -x")
has("timeline.sh", out, '7 MARK "-x" in user entry')
has("timeline.sh", out, 'never MARK "# Absent"')
has("timeline.sh", out, 'never MARK "-n"')
has("timeline.sh", out, 'never MARK "# Agent wrote this"')
has("timeline.sh", out, 'never MARK "# Never shown"')
has("timeline.sh", out, 'never MARK "# Hooked"')
has("timeline.sh", out, 'never MARK "# Tooled"')
has("timeline.sh", out, 'never MARK "# Deferred"')
has("timeline.sh", out, '14 MARK "# System rule" in prompt_snapshot entry (from the start)')
has("timeline.sh", out, 'MARK "# Session hook" in hook_success entry')
has("timeline.sh", out, '9 MARK "Write \\"one-line\\" comments.\\n\\tTabbed" in nested_memory entry')
has("timeline.sh", out, "src/cart.test.js")
has("timeline.sh", out, '12 MARK "# From hook" in hook_additional_context entry')
has("timeline.sh", out, '7 MARK "# Lean code" in user entry')
lacks("timeline.sh", out, "13 MARK")
lacks("timeline.sh", out, "api-request")
check(sum("MARK" in l for l in out.split("\n")) == 14, "timeline.sh: want one MARK per marker and kind: %s" % out)
out, st = run(["bash", TL, t])
check(not st, "timeline.sh: no markers exited %d: %s" % (st, out))
has("timeline.sh", out, "6 Bash: ls skills -x")
_, st = run(["bash", TL, tmp + "/missing.jsonl"])
check(st == 2, "timeline.sh: missing transcript exited %d, want 2" % st)

tmpd.cleanup()

sys.exit(lib.finish())
