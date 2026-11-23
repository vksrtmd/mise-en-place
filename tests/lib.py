"""Helpers shared by the tests/test_*.py files. Stdlib only, Python 3.9.

A failed expectation prints a line and sets `failed`; a test file ends with `sys.exit(finish())`.
"""
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASH = shutil.which("bash") or "/bin/bash"
failed = False


def report(msg):
    """Print a failure line and remember it."""
    global failed
    print(msg)
    failed = True


def finish():
    """Exit status for the test file: 1 when any expectation failed."""
    return 1 if failed else 0


def has(label, text, needle):
    if needle not in text:
        report("%s: output lacks: %s" % (label, needle))


def lacks(label, text, needle):
    if needle in text:
        report("%s: output has: %s" % (label, needle))


def check(ok, msg):
    if not ok:
        report(msg)


def script_dir(default):
    """The scripts dir to test: argv[1] or ROOT/default, absolute; exits 2 when it is no directory."""
    d = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, default)
    if not os.path.isdir(d):
        print("not a directory: %s" % d)
        sys.exit(2)
    return d


def run(cmd, cwd=None, env=None, merge=True):  # merge: True 2>&1, None inherit, False discard
    """Like $(...): returns (stdout with trailing newlines stripped, exit status)."""
    e = dict(os.environ)
    e.update(env or {})
    p = subprocess.run(cmd, cwd=cwd or ROOT, env=e, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT if merge else (None if merge is None else subprocess.DEVNULL))
    return p.stdout.decode("utf-8", "replace").rstrip("\n"), p.returncode


def sed_range(text, start, end):
    """sed -n '/start/,/end/p'"""
    out, inside = [], False
    for line in text.split("\n"):
        if not inside:
            if re.search(start, line):
                inside = True
                out.append(line)
        else:
            out.append(line)
            if re.search(end, line):
                inside = False
    return "\n".join(out)


def jl(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def write(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


# A transcript line per call and per result: use(id, tool, command), res(id, is_error, text).
# ts overrides the timestamp: each call at 10:00 and its result at 10:05 by default.
def use(i, n, c, ts="2026-01-01T10:00:00.000Z"):
    return jl({"type": "assistant", "timestamp": ts, "message": {
        "content": [{"type": "tool_use", "id": i, "name": n, "input": {"command": c}}],
        "usage": {"output_tokens": 10}}})


def res(i, e, t, ts="2026-01-01T10:05:00.000Z"):
    return jl({"type": "user", "timestamp": ts, "message": {
        "content": [{"type": "tool_result", "tool_use_id": i, "is_error": e, "content": t}]}})


def handback(m):
    return jl({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "h", "name": "SubagentHandback", "input": {"message": m}}]}})


def user(content, **extra):
    d = {"type": "user"}
    d.update(extra)
    d["message"] = {"content": content}
    return jl(d)


# Hook tests.
def cases(table, comments=True, unescape=True):
    """Yield (want, cmd) from a tab-separated table; \\n and \\t become a newline and a tab."""
    for line in table.split("\n"):
        if comments and (line == "" or line.startswith("#")):
            continue
        if not line:
            continue
        want, cmd = line.split("\t", 1)
        if unescape:
            cmd = cmd.replace("\\n", "\n").replace("\\t", "\t")
        yield want, cmd


def hook_run(hook, command, cwd=None, raw=None, env=None):
    """Run `bash hook` on a PreToolUse payload; return (exit status, stdout, stderr)."""
    if raw is None:
        payload = {"tool_input": {"command": command}}
        if cwd is not None:
            payload["cwd"] = cwd
        raw = json.dumps(payload)
    p = subprocess.run([BASH, hook], input=raw, cwd=ROOT, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True)
    return p.returncode, p.stdout, p.stderr


def git(*args, cwd):
    subprocess.run(["git"] + list(args), cwd=cwd, check=True, stdout=subprocess.DEVNULL)
