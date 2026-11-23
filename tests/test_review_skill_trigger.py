#!/usr/bin/env python3
"""Runs skills/review-skill/scripts/trigger.sh against a fake claude built in a temp dir; prints a line
per failed expectation and exits 1 when any fails.

Usage: tests/test_review_skill_trigger.py [scripts dir]  (default skills/review-skill/scripts; pass another
copy, e.g. one extracted with `git archive main skills/review-skill/scripts`, to test it without touching
the worktree). Needs jq.
"""
import json
import os
import sys
import tempfile

import lib
from lib import check, has, run

os.chdir(lib.ROOT)
TR = lib.script_dir("skills/review-skill/scripts") + "/trigger.sh"


tmpd = tempfile.TemporaryDirectory()
tmp = tmpd.name

# A fake claude whose first tool call is picked by the query's first word.
os.makedirs(tmp + "/bin")
os.makedirs(tmp + "/sk/demo")
with open(tmp + "/sk/demo/SKILL.md", "w") as f:
    f.write("---\nname: demo\ndescription: Demo.\n---\nBody.\n")
with open(tmp + "/bin/claude", "w") as f:
    f.write(r'''#!/usr/bin/env bash
[ -z "${CLAUDECODE:-}" ] || exit 1
q=$2; trial=$(basename "$PWD"/.claude/skills/*)
grep -q '^name: '"$trial"'$' ".claude/skills/$trial/SKILL.md" || exit 1
case "$*" in *"--max-turns 1"*) ;; *) exit 1 ;; esac
u() { jq -nc --arg n "$1" --argjson i "$2" '{type:"assistant",message:{content:[{type:"text",text:"x"},{type:"tool_use",name:$n,input:$i}]}}'; }
echo '{"type":"system","subtype":"init"}'
case $q in
  this*) u Skill "{\"skill\":\"$trial\"}" ;;
  slash*) u Skill "{\"skill\":\"/$trial\"}" ;;
  installed*) u Skill '{"skill":"demo"}' ;;
  read*) u Read "{\"file_path\":\"$PWD/.claude/skills/$trial/SKILL.md\"}" ;;
  other*) u Skill '{"skill":"code-review"}' ;;
  bash*) u Bash '{"command":"ls"}' ;;
  fail*) echo "Not logged in" >&2; exit 1 ;;
  text*) exit 0 ;;
esac
u Skill "{\"skill\":\"$trial\"}"
echo '{"type":"result"}'
''')
os.chmod(tmp + "/bin/claude", 0o755)


def trig():
    return run(["bash", TR, tmp + "/sk/demo", tmp + "/q.json", "2"],
               env={"PATH": tmp + "/bin:" + os.environ.get("PATH", ""), "CLAUDECODE": "1"})


def queries(qs):
    with open(tmp + "/q.json", "w") as f:
        f.write(json.dumps([{"query": q, "should_trigger": b} for q, b in qs], indent=2) + "\n")


queries([("this one", True), ("slash it", True), ("read it", True), ("installed copy", True),
         ("other skill", False), ("bash first", False), ("text only", False)])
out, st = trig()
check(st == 0, "trigger.sh: all-pass set exited %d: %s" % (st, out))
has("trigger.sh", out, "PASS  fire 2/2 (this 2, installed 0)  expect fire")
has("trigger.sh", out, "PASS  fire 2/2 (this 0, installed 2)  expect fire")
has("trigger.sh", out, "PASS  fire 0/2 (this 0, installed 0)  expect none  also: skill:code-review 2")
has("trigger.sh", out, "also: tool:Bash 2")
has("trigger.sh", out, "also: none 2")
has("trigger.sh", out, "      other skill")
has("trigger.sh", out, "passed 7/7 queries, 2 runs each, trial name demo-")
queries([("this one", False), ("fail now", True)])
out, st = trig()
check(st == 1, "trigger.sh: failing set exited %d, want 1" % st)
has("trigger.sh", out, "FAIL  fire 2/2 (this 2, installed 0)  expect none")
has("trigger.sh", out, "FAIL  fire 0/2 (this 0, installed 0)  expect fire  also: error 2")
has("trigger.sh", out, "2 runs errored")
queries([("fail now", True)])
out, st = trig()
check(st == 1, "trigger.sh: all-error set exited %d, want 1" % st)
has("trigger.sh", out, "every run failed; first error:")
has("trigger.sh", out, "Not logged in")
_, st = run(["bash", TR, tmp + "/sk", tmp + "/q.json"])
check(st == 2, "trigger.sh: dir without SKILL.md exited %d, want 2" % st)
for body, msg in (("", "has no queries"), ("[]", "has no queries"), ("{}", "is not a JSON array")):
    with open(tmp + "/q.json", "w") as f:
        f.write(body + "\n" if body else "")
    out, st = trig()
    check(st == 2, "trigger.sh: queries file %s exited %d, want 2" % (body, st))
    has("trigger.sh", out, msg)


tmpd.cleanup()

sys.exit(lib.finish())
