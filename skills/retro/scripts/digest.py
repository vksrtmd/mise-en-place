#!/usr/bin/env python3
"""Digest a Claude Code session for a retro: the agents ranked by output tokens, the hedges in their reports and the
commands repeated across agents, then a block per transcript (stats, pauses, prompt, friction, report; a
main block adds the prompt and user turns).
Reads only; prints to stdout.
Usage: [MIN_AGENTS=2] [EXPECTED_RED=<regex>] digest.py <session-dir | session.jsonl> [width]
       digest.py --around <transcript.jsonl> <line> [radius [width]]   the entries within radius (default 3) of a
         flagged @line, width default 400, without entries that only carry harness context (isMeta, <system-reminder>,
         # Environment update)
       digest.py --to-read <session-dir | session.jsonl> [radius [width]]   a `widen:` line (the --around command as
         a template), a `note:` line when EXPECTED_RED is unset and agents whose prompt mentions tdd,
         red-first, red tests or a mutation test/run have ! windows on Bash calls (`note: agents briefed for red tests have
         ! windows (<id8>, ...): when their reds were meant, rewrite with EXPECTED_RED='<regex of their commands>'`), and a `<who> <path>` line per transcript
         with a group, once; then each ! and ? group (~ stays
         out), main log first, as `<mark> <main | id8> @<line>[ ×N]` and its --around window at the group's first
         @line, radius default 1, width default 400, with its call's line above it when the window leaves it out.
         A friction key (tool, text) in at least MIN_AGENTS agents prints its first agent group's window, then
         `also: <id8> @<line>[ ×N], ...` for the others; the main log's groups are never collapsed.
       digest.py --text <transcript.jsonl> [width]   the agent's prose, a line per text block, width default 400
       digest.py --calls <transcript.jsonl> [width]   the tool calls, a line each as `@line Name: input`, width default 400
       digest.py --prompt <transcript.jsonl>   the first string prompt, whole: not squashed, not cut
       digest.py --help | -h
  <session-dir> is ~/.claude/projects/<project>/<session-id>; the .jsonl beside it is the main log.
  The main log is read only up to the first digest.py call naming this session, so the retro's calls stay out of it.
  EXPECTED_RED matches the commands whose failures were meant (a before-state script, a mutation run); a red-at.sh
  run whose setup succeeded is. A meant red that matches none of the ~ rules below still shows as `!`.
Exit status: 0, or 1 on bad usage (a missing argument, a non-numeric line, radius or width), 2 on a session or
  transcript it can't find, read or parse, 5 on a timestamp that isn't %Y-%m-%dT%H:%M:%SZ.
Stats line: `results N KB, largest N KB` counts a result the harness persisted (the log holds a preview that starts
  `<persisted-output>`) at the size its `Output too large (83.3KB)` header names, not the preview's.
  An AskUserQuestion call prints as `AskUserQuestion: [<label> | <label> ...] <question>` per question, cut to width:
  the labels lead so the default width keeps them.
Symbols:
  ⏸ a usage-limit pause (active minutes leave the pauses out), with its start as `at MM-DD HH:MM UTC` (the form
    sessions.sh prints), split into `limit N, then waiting to be resumed M`
    when the run sat on after another transcript's reply showed the limit had lifted; the output tokens each model
    spent across the session since the previous pause (`since the start` for the first) follow, `none` when no
    model spent any: the quota went to other sessions. Back-to-back stops
    of one transcript with the same message text and no successful reply of it between print as one line,
    `⏸ <error> ×N @a,@b,...: <text> · at ... · paused M min (...)`, paused from the first stop to the last one's end.
  ⌛ a call that sat over 5 min before the next entry (no ⏸ in the gap), `N min after`, or a Bash the harness moved to
    the background after its timeout, `moved to background`.
  @line a line in the transcript; --around takes one (a group's first).
  ! an error result (a nonzero exit, a tool error).  ? a friction line in a result that exited 0 (a piped test run,
    or quoted text: judge it from the line shown; the +, - and space lines and the `@@` lines of a `diff --git` hunk,
    and the numbered lines of a `cat -n` or `nl` that takes no piped input, don't count).  ~ a failure that later clears or was meant: its call, leading
    VAR=value assignments aside, later succeeds, the test it failed passes under the same name, or the call is a
    red-at.sh run whose setup succeeded or matches EXPECTED_RED.
  Each flagged line prints `@a: <first friction line> · <call, leading VAR=value aside, cut to width>`; N identical
    ones (same mark, tool, call and text in one transcript) print `×N @a,@b,...`.
Summary sections of a session dir with subagents, before the blocks:
  ## friction repeated across agents  `A agents × L lines · <tool>: <text> · <id8> n, ...`: a friction line (mark and
    call ignored; a ×N line counts N) found in at least MIN_AGENTS agents, top 20, with each agent's line count.
  ## hedges in reports  the sentences of an agent's report, and of the main log's prose (`main:` lines, which also
    print for a session without agents), that admit a gap (assumed, estimated, did not, nobody...). Left out: a "did
    not <verb>" the agent's prompt also forbids ("don't <verb>"), table rows and lines of only numbers and units.
    A brief sentence (one that limits the agent's work) shared by 2 or more of the agents printed there prints once at
    the top, `all agents brief:` or `N agents brief:`; an agent's own lines keep the rest.
  ## brief template (lines in every agent's prompt)  with 2 or more agents: the non-blank prompt lines (trailing
    whitespace ignored) present in every agent's prompt, whole, in the first agent's order; omitted when none is
    shared. Each agent's `prompt:` then shows only its lines outside the template, or `(template only)`.
"""

import calendar
import json
import os
import re
import shlex
import sys
from collections import Counter

# \s without \x1c-\x1f, as Oniguruma reads it (Python's \s takes them): output stays identical to the jq version's.
WS = r"\t\n\v\f\r \x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000"


def rx(pattern, flags=0):
    """re.compile with \\s and \\S meaning WS."""
    out, i, in_class = [], 0, False
    while i < len(pattern):
        c = pattern[i]
        if c == "\\" and i + 1 < len(pattern):
            n = pattern[i + 1]
            if n == "s":
                out.append(WS if in_class else "[" + WS + "]")
            elif n == "S":
                out.append(c + n if in_class else "[^" + WS + "]")
            else:
                out.append(c + n)
            i += 2
            continue
        if c == "[" and not in_class:
            in_class = True
        elif c == "]" and in_class:
            in_class = False
        out.append(c)
        i += 1
    return re.compile("".join(out), flags)


# Result lines that signal friction: failing tests and commands, refusals, timeouts. Matched line by line, and only in
# the results of commands other than file readers, so a word inside ordinary output (a branch name, a file listing,
# printed source) passes; any result marked as an error counts too. A reader is a command whose every part (split on
# && || | ; and newlines) starts with a reader word (cat, sed, grep, ...), so `cat x | head` is one; a subshell, an
# if/then/else and a for loop are read through, and a segment of only NAME=value assignments is one. A command with any
# command substitution ($(, a backtick, <() is no reader, whatever its parts are. Lines that only quote a failure pass
# as well: a digest line (`! Bash @3: ...`) and a one-line JSON object (`gh ... --json`), a path in printed source
# (`    error::Result,` in a Rust use list), the +, - and space lines inside a hunk of a `diff --git` section (any Bash
# result), the `@@` lines themselves, and the numbered lines of a call with a `cat -n` or `nl` segment that takes no
# piped input (the first segment, or one after && || ; or a newline). A hunk lasts while the counts of its
# `@@ -a[,b] +c[,d] @@` header do; once both reach 0 only another `@@` or a file header line continues the section, and
# any other line ends it; a body line whose count is already 0 ends the hunk and is judged as outside it. Limits: a
# hunk cut short (`git diff | head`) still counts as open, so a runner's indented output right after it reads as diff
# text (it matters only for a call that exits 0, as a nonzero exit flags `!` anyway); only `diff --git` sections are
# read, not combined diffs (`diff --cc`).
FRICTION = rx(r"^\s*(?:fatal|error|Error|ERROR):(?!:|\s*[{\[])|^\s*(?:FAIL|not ok)\b|--- FAIL|✖|[Pp]ermission denied"
              r"|timed out|\[(?:remote )?rejected\]|command not found|No such file or directory|EADDRINUSE"
              r"|^Traceback \(most recent")
QUOTED_FAILURE = rx(r"^\s*(?:[!?~] \S+(?: ×[0-9]+)? @[0-9]+(?:,@[0-9]+)*:|\{\")")

# Report sentences that admit a gap: what the agent assumed, skipped or could not check.
HEDGE = rx(r"assum|estimat|did(?:n.t| not) \w+|without (?:checking|verifying|running)|could(?:n.t| not)"
           r"|unable to|unverified|not verified|not confirmed|untested|not tested|no (?:automated )?tests?\b|by hand"
           r"|unclear|\b(?:I|we) guess|\bnobody\b|\bno one\b", re.I)
# A report line that only tallies: a table row, or no word of 3 letters once hedge words and units are set aside.
SIZE_UNITS = rx(r"\b(?:[kmg]?b|ms|sec|min|tokens?)\b", re.I)
TALLY_ROW = rx(r"^\s*\|")
# "did not <verb>" / "don't <verb>" / "never <verb>": the verb is what a limit forbids or a report admits skipping.
NEGATED = rx(r"\b(?:did(?:n.t| not)|do(?:n.t| not)|never|must not|should not)\s+(\w+)", re.I)
# Report lines and sentences that describe a finding (a reviewer's bold title, "What this is:", "Problem:", "If we skip
# it:"), not a gap in the agent's work.
FINDING = rx(r"^[\s>-]*(?:\*\*|(?:If we skip it|What this is|Problem)\b)")
# A line opening a section of gaps. A report with one gets only its gap sections read, every sentence a gap.
GAPS = rx(r"^[\s#*>-]*(?:Unconfirmed|Not (?:checked|confirmed|verified))\b", re.I)
GAPS_ONLY = rx(r"^[\s#*>-]*(?:Unconfirmed|Not (?:checked|confirmed|verified))\b[\s:*]*$", re.I)
QUOTED_SPAN = rx(r"`[^`]*`|\"[^\"]*\"|“[^”]*”|(?<!\w)'[^']*'(?!\w)")
SENTENCE_END = rx(r"(?<=[.!?;])\s+")
FENCE_OPEN = rx(r"[ \t]*(`{3,}|~{3,})")
SENTENCE_BREAK = rx(r"(?<=[.!?;])\s+|\s(?=- \*\*)")

WS_RUN = rx(r"\s+")
REMINDER = rx(r"<system-reminder>[\s\S]*?</system-reminder>")
CODE_SUBST = re.compile(r"\$\((?!\()|`|<\(")
SEGMENT_SPLIT = rx(r"\s*(?:&&|\|\|?|;|\n)\s*")
SEGMENT_SEP = rx(r"\s*(&&|\|\|?|;|\n)\s*")
SEGMENT_HEAD = rx(r"^[\s(]*(?:(?:do|if|then|else|elif)\s+)?")
READER_WORD = rx(r"^(?:cd|echo|printf|ls|wc|sort|uniq|cut|tr|cat|head|tail|sed|nl|less|bat|grep|rg|jq|true|test|for"
                 r"|done|fi|git (?:show|diff|log|grep))(?:\s|$|\))|^\[\[?\s|^(?:do|then|else)?[\s)]*$")
ASSIGNMENT_ONLY = rx(r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=(?:\"[^\"]*\"|\S*)\s*)+$")
DIFF_HEAD = rx(r"^diff --git ")
DIFF_FILE = rx(r"^(?:diff --git|index |--- |\+\+\+ |new file|deleted file|similarity|rename|old mode|new mode"
               r"|Binary files)")
NUMBERED = rx(r"^\s*[0-9]+\t")
HUNK_HEAD = rx(r"^@@ -[0-9]+(?:,([0-9]+))? \+[0-9]+(?:,([0-9]+))? @@")
NUMBERING_HEAD = rx(r"^(?:cat -n|nl)(?:\s|$)")
ASSIGNMENTS = rx(r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=(?:\"[^\"]*\"|\S*)\s+)+")
FAILED_NAME = rx(r"^\s*(?:✖|not ok [0-9]+ -|--- FAIL:)\s*(?P<n>.+?)(?:\s+\([0-9.]+m?s\))?\s*$")
PASSED_NAME = rx(r"^\s*(?:✔|ok [0-9]+ -|--- PASS:)\s*(?P<n>.+?)(?:\s+\([0-9.]+m?s\))?\s*$")
BACKGROUNDED = rx(r"^\s*Command\b.*(?:moved to (?:the )?background|automatically backgrounded|backgrounded after)", re.I)
BRIEF_LIMIT = rx(r"^(?:skip|leave)\b|\b(?:do(?:n.t| not)|never|only|without|no need)\b", re.I)
NOT_HUMAN = rx(r"^\s*(?:<(?:local-command-(?:caveat|stdout|stderr)|task-notification)>|Another Claude session sent a message)")
SLASH_TAGS = rx(r"<command-(?:name|message|args)>[\s\S]*?</command-(?:name|message|args)>")
HARNESS_TEXT = rx(r"^\s*(?:<system-reminder>[\s\S]*</system-reminder>\s*$|# Environment update)")
HEADING = rx(r"^\s*(?:#|\*\*)")
NON_SPACE = rx(r"\S")


# --- JSON as jq prints it (escapes, number format): width cuts and printed strings depend on it.

_ESC = re.compile('["\\\\\x00-\x1f\x7f]')
_ESC_MAP = {'"': '\\"', "\\": "\\\\", "\n": "\\n", "\t": "\\t", "\r": "\\r", "\b": "\\b", "\f": "\\f"}


def jq_str(s):
    return '"' + _ESC.sub(lambda m: _ESC_MAP.get(m.group(), "\\u%04x" % ord(m.group())), s) + '"'


def jq_num(x):
    if isinstance(x, int) and abs(x) < 2 ** 53:
        return str(x)
    f = float(x)
    if f != f or f in (float("inf"), float("-inf")):
        return "null"
    sign = "-" if str(f).startswith("-") else ""
    mant, _, exp = repr(abs(f)).partition("e")
    whole, _, frac = mant.partition(".")
    digits = (whole + frac).lstrip("0")
    decpt = len(whole) + int(exp or 0) - (len(whole + frac) - len((whole + frac).lstrip("0")))
    digits = digits.rstrip("0")
    if not digits:
        return sign + "0"
    n = len(digits)
    if decpt <= -4 or decpt > n + 15:
        e = decpt - 1
        body = digits[0] + ("." + digits[1:] if n > 1 else "")
        return "%s%se%s%02d" % (sign, body, "-" if e < 0 else "+", abs(e))
    if decpt <= 0:
        return sign + "0." + "0" * -decpt + digits
    if decpt >= n:
        return sign + digits + "0" * (decpt - n)
    return sign + digits[:decpt] + "." + digits[decpt:]


def tojson(v):
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, str):
        return jq_str(v)
    if isinstance(v, (int, float)):
        return jq_num(v)
    if isinstance(v, list):
        return "[" + ",".join(tojson(x) for x in v) + "]"
    return "{" + ",".join(jq_str(k) + ":" + tojson(x) for k, x in v.items()) + "}"


def tostring(v):
    return v if isinstance(v, str) else tojson(v)


# --- Reading a transcript

def fail(msg, code=2):
    sys.stderr.write("digest.py: %s\n" % msg)
    sys.exit(code)


def read_lines(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        fail("cannot read %s: %s" % (path, e.strerror))
    return data.decode("utf-8", "replace").split("\n")


def parse_line(line, path, n):
    try:
        return json.loads(line)
    except ValueError:
        fail("%s:%d: parse error" % (path, n))


def read_entries(path):
    """The parsed JSON value of each non-blank line, in order. An entry's number is its index + 1."""
    out = []
    for n, line in enumerate(read_lines(path), 1):
        if line.strip():
            out.append(parse_line(line, path, n))
    return out


def truthy(v):  # jq's: only null and false are false
    return v is not None and v is not False


def first_truthy(*vals):  # jq's a // b // c
    for v in vals:
        if truthy(v):
            return v
    return None


def get(v, *path):
    for k in path:
        if not isinstance(v, dict):
            return None
        v = v.get(k)
    return v


def iterate(v):  # jq's .[]?
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        return list(v.values())
    return []


def blocks(entry):
    """The objects of .message.content[]?"""
    return [b for b in iterate(get(entry, "message", "content")) if isinstance(b, dict)]


def is_type(entry, t):
    return isinstance(entry, dict) and entry.get("type") == t


def key_of(v):  # the object key jq's from_entries makes of an id
    return v if isinstance(v, str) else tojson(v)


def squash(s):
    return WS_RUN.sub(" ", s)


def piece(c):  # .text? // ""
    t = c.get("text") if isinstance(c, dict) else None
    return tostring(t) if truthy(t) else ""


def result_text(content, sep):
    """A tool_result's content as text: an array's text blocks joined by sep, anything else as a string."""
    if isinstance(content, list):
        return sep.join(piece(c) for c in content)
    return tostring(content)


def split_lines(s):
    return s.split("\n") if s else []


def call_text(inp_owner, *fields):
    """The input field that says what a call did (the first present of fields), as a string."""
    return tostring(first_truthy(*[get(inp_owner, "input", f) for f in fields]) or "")


def ts(s):
    m = re.match(r"^(\d+)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.[0-9]+)?Z$", s) if isinstance(s, str) else None
    if not m:
        fail("date %s does not match format \"%%Y-%%m-%%dT%%H:%%M:%%SZ\"" % tojson(s), 5)
    return calendar.timegm(tuple(int(g) for g in m.groups()) + (0, 0, 0))


def hhmm(s):
    return s[11:16] if truthy(s) else "??:??"


# --- Pauses: the stops after API errors (a usage limit)

def stops(entries):
    """From each API error to the next user or assistant entry, when the run went on. Each as {l: line, v: entry,
    t: start, end: seconds or None}."""
    stamped = [(i + 1, e) for i, e in enumerate(entries) if truthy(get(e, "timestamp"))]
    times = [ts(e["timestamp"]) for _, e in stamped]
    out = []
    for i, (l, e) in enumerate(stamped):
        if e.get("isApiErrorMessage") is True:
            end = None
            for j in range(i + 1, len(stamped)):
                if is_type(stamped[j][1], "user") or is_type(stamped[j][1], "assistant"):
                    end = times[j]
                    break
            out.append({"l": l, "v": e, "t": times[i], "end": end})
    return out


def alive_of(all_entries):
    """Every successful assistant entry's time t, model m and output tokens o, across the whole session: the limit
    lifted by the first reply anywhere, not just the first in this transcript."""
    out = []
    for e in all_entries:
        if is_type(e, "assistant") and truthy(e.get("timestamp")) and e.get("isApiErrorMessage") is not True:
            model = first_truthy(get(e, "message", "model")) or "?"
            if isinstance(model, str) and model.startswith("claude-"):
                model = model[len("claude-"):]
            out.append({"t": ts(e["timestamp"]), "m": tostring(model),
                        "o": first_truthy(get(e, "message", "usage", "output_tokens")) or 0})
    return out


def lifted(stop, alive):
    """When the limit lifted: the first later reply, or the stop's end when none came sooner."""
    later = [a["t"] for a in alive if a["t"] > stop["t"]]
    up = min(later) if later else stop["end"]
    return min(up, stop["end"])


def compact(n):
    return "%dk" % (n // 1000) if n >= 1000 else tojson(n)


def pauses(entries, alive, w):
    """Each stop line, with the time until the run went on, split when the run waited on past the limit, and the output
    tokens each model spent across the session since the previous pause. Back-to-back stops (the same message text, no
    successful assistant entry of this transcript between) are one line, spanning from the first start to the last end."""
    runs = []
    for s in stops(entries):
        content = get(s["v"], "message", "content")
        full = squash(result_text(content, " ") if isinstance(content, list) else tostring(content))
        if runs and runs[-1]["full"] == full and not any(
                is_type(e, "assistant") and e.get("isApiErrorMessage") is not True
                for e in entries[runs[-1]["stops"][-1]["l"]:s["l"] - 1]):
            runs[-1]["stops"].append(s)
        else:
            runs.append({"full": full, "stops": [s]})
    out, prev = [], None
    for r in runs:
        first, last = r["stops"][0], r["stops"][-1]
        by_model = {}
        for a in alive:
            if (prev is None or a["t"] > prev) and a["t"] <= last["t"]:
                by_model[a["m"]] = by_model.get(a["m"], 0) + a["o"]
        spent = ", ".join("%s %s" % (m, compact(by_model[m])) for m in sorted(by_model)) or "none"
        n = len(r["stops"])
        line = "  ⏸ %s%s %s: %s" % (tostring(first_truthy(first["v"].get("error")) or "api error"),
                                   " ×%d" % n if n > 1 else "", ",".join("@%d" % s["l"] for s in r["stops"]),
                                   r["full"][:w])
        line += " · at %s UTC" % first["v"]["timestamp"][5:16].replace("T", " ")
        if last["end"] is not None:
            span = {"t": first["t"], "end": last["end"]}
            line += " · paused %d min" % ((span["end"] - span["t"]) // 60)
            up = lifted(span, alive)
            wait = (span["end"] - up) // 60
            if wait > 0:
                line += " (limit %d, then waiting to be resumed %d)" % ((up - span["t"]) // 60, wait)
        out.append(line + "\n    out tokens since " + ("the start" if prev is None else "the previous pause") + ": " + spent)
        prev = last["t"]
    return out


def waits(entries, w):
    """A call that sat over 5 min before the transcript's next entry (unless an API-error stop falls in the gap), and
    a Bash the harness moved to the background after its timeout (not one the agent asked to run there). Each is
    listed on its call's line. shortcut: the harness's real wording for the move is unknown, so BACKGROUNDED guesses at
    it and needs a first line opening with "Command", which keeps out quotes (test output, grep hits); pin it to the
    first real result seen."""
    def what(b):
        return squash(call_text(b, "command", "file_path", "pattern", "description"))[:w]

    stopped = stops(entries)
    done = {}
    for e in entries:
        t = get(e, "timestamp")
        for b in blocks(e):
            if b.get("type") == "tool_result" and truthy(t) and truthy(b.get("tool_use_id")):
                done[key_of(b["tool_use_id"])] = ts(t)
    next_ts = [None] * len(entries)
    nxt = None
    for i in range(len(entries) - 1, -1, -1):
        next_ts[i] = nxt
        if truthy(get(entries[i], "timestamp")):
            nxt = ts(entries[i]["timestamp"])

    found = []
    for i, e in enumerate(entries):
        if not (is_type(e, "assistant") and truthy(e.get("timestamp"))) or next_ts[i] is None:
            continue
        t0 = ts(e["timestamp"])
        for u in blocks(e):
            if u.get("type") != "tool_use":
                continue
            t1 = done.get(key_of(u.get("id")), next_ts[i])
            if t1 - t0 > 300 and all(s["t"] < t0 or s["t"] > t1 for s in stopped):
                found.append((i + 1, "  ⌛ @%d: %d min after · %s" % (i + 1, (t1 - t0) // 60, what(u))))

    foreground = {}
    for i, e in enumerate(entries):
        for b in blocks(e):
            if b.get("type") == "tool_use" and b.get("name") == "Bash" and get(b, "input", "run_in_background") is not True:
                foreground[key_of(b.get("id"))] = (i + 1, what(b))
    for e in entries:
        for b in blocks(e):
            if b.get("type") == "tool_result" and key_of(b.get("tool_use_id")) in foreground:
                first = result_text(b.get("content"), " ").split("\n")[0]
                if BACKGROUNDED.search(first):
                    l, wh = foreground[key_of(b["tool_use_id"])]
                    found.append((l, "  ⌛ @%d: moved to background · %s" % (l, wh)))
    return [s for _, s in sorted(found, key=lambda p: p[0])]


# --- Per-transcript sections

def output_tokens(entries):
    return sum(first_truthy(get(e, "message", "usage", "output_tokens")) or 0 for e in entries if is_type(e, "assistant"))


PERSISTED = re.compile(r"\A<persisted-output>\s*Output too large \(([0-9.]+) ?([KMG]?B)\)")
UNITS = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}


def result_size(content):
    """A result's size in bytes: the size a persisted-output header names (the log holds only a preview), else its length."""
    m = PERSISTED.match(result_text(content, "\n"))
    return int(float(m.group(1)) * UNITS[m.group(2)]) if m else len(tostring(content))


def stats(entries, paused_stops):
    """Tool calls, result bytes, active minutes (wall time less the pauses after API errors), output tokens."""
    calls = sum(1 for e in entries if is_type(e, "assistant") for b in blocks(e) if b.get("type") == "tool_use")
    sizes = [result_size(b.get("content")) for e in entries if is_type(e, "user") for b in blocks(e)
             if b.get("type") == "tool_result"]
    times = [ts(e["timestamp"]) for e in entries if truthy(get(e, "timestamp"))]
    paused = sum(s["end"] - s["t"] for s in paused_stops if s["end"] is not None)
    active = (max(times) - min(times) - paused) // 60 if len(times) > 1 else 0
    return "  calls %d · results %d KB, largest %d KB · %d min · out tokens %s" % (
        calls, sum(sizes) // 1024, (max(sizes) if sizes else 0) // 1024, active, tojson(output_tokens(entries)))


def ask_text(b):
    """An AskUserQuestion's questions, each after its option labels in brackets."""
    return " ".join("[%s] %s" % (" | ".join(tostring(o.get("label")) for o in iterate(q.get("options"))), tostring(q.get("question")))
                    for q in iterate(get(b, "input", "questions")) if isinstance(q, dict))


def calls(entries, w):
    """One line per tool call: @line Name: the input that says what it did."""
    return ["  @%d %s: %s" % (l, tostring(b.get("name")), squash(ask_text(b) if b.get("name") == "AskUserQuestion" else
                                                      call_text(b, "command", "file_path", "pattern", "skill", "description"))[:w])
            for l, e in enumerate(entries, 1) if is_type(e, "assistant") for b in blocks(e) if b.get("type") == "tool_use"]


def bare(call):
    return ASSIGNMENTS.sub("", call, count=1)


def is_reader(call):
    if CODE_SUBST.search(call):
        return False
    for part in SEGMENT_SPLIT.split(call):
        if not NON_SPACE.search(part):
            continue
        head = SEGMENT_HEAD.sub("", part, count=1)
        if not READER_WORD.search(head) and not ASSIGNMENT_ONLY.search(head):
            return False
    return True


def numbers_lines(call):
    """Whether a `cat -n` or `nl` segment takes no piped input: the first segment, or one after && || ; or a newline."""
    parts = SEGMENT_SEP.split(call)
    return any(NUMBERING_HEAD.search(SEGMENT_HEAD.sub("", part, count=1))
               for k, part in enumerate(parts[::2]) if k == 0 or parts[2 * k - 1] != "|")


def quoted_lines(call, lines):
    """The result lines that only quote text: the +, - and space lines and the `@@` lines of a `diff --git` hunk,
    and the numbered lines of a `cat -n` or `nl` segment that takes no piped input. A hunk lasts while its header's counts do; then only `@@` or a
    file header continues the section."""
    numbered = numbers_lines(call)
    quoted, in_diff, old, new = set(), False, 0, 0
    for i, x in enumerate(lines):
        if old or new:
            c = x[:1]
            body = True
            if c in ("", " ") and old and new:
                old, new = old - 1, new - 1
            elif c == "-" and old:
                old -= 1
            elif c == "+" and new:
                new -= 1
            elif not x.startswith("\\ No newline"):
                old = new = body = 0
            if body:
                quoted.add(i)
                continue
        if DIFF_HEAD.search(x):
            in_diff = True
        elif in_diff:
            m = HUNK_HEAD.search(x)
            if m:
                quoted.add(i)
                old, new = (int(g) if g is not None else 1 for g in m.groups())
            elif not DIFF_FILE.search(x):
                in_diff = False
            elif x.startswith(("--- ", "+++ ")):
                nxt = lines[i + 1:i + 3]
                if x[0] == "-" and len(nxt) == 2 and nxt[0].startswith("+++ ") and nxt[1].startswith("@@"):
                    quoted.add(i)
                elif x[0] == "+" and nxt[:1] and nxt[0].startswith("@@"):
                    quoted.add(i)
        if numbered and NUMBERED.search(x):
            quoted.add(i)
    return quoted


def friction_groups(entries, w, expected_red):
    """Error results and results with a friction line, each with its first friction line and @line in the transcript,
    marked by whether the call later succeeds, its failed test later passes, or the red pattern matches it. Identical
    ones are grouped: [(line dict, the @lines)]."""
    red = re.compile("red-at\\.sh" + ("|" + expected_red if expected_red else ""))
    uses = {}
    for l, e in enumerate(entries, 1):
        for b in blocks(e):
            if b.get("type") == "tool_use":
                uses[key_of(b.get("id"))] = {"name": b.get("name"), "line": l,
                                             "call": call_text(b, "command", "file_path", "description")}
    results = []
    for l, e in enumerate(entries, 1):
        for b in blocks(e):
            if b.get("type") != "tool_result":
                continue
            use = uses.get(key_of(b.get("tool_use_id")), {"name": "?", "call": "", "line": l})
            lines = split_lines(result_text(b.get("content"), "\n"))
            hits = []
            if use["name"] == "Bash" and not is_reader(use["call"]):
                skip = quoted_lines(use["call"], lines)
                hits = [x for i, x in enumerate(lines) if i not in skip and FRICTION.search(x) and not QUOTED_FAILURE.search(x)]
            err = b.get("is_error") is True or use["name"] == "TaskStop"
            results.append({
                "name": use["name"], "call": use["call"], "line": l, "use": use["line"],
                "text": hits[0] if hits else " ".join(lines),
                "failed": [m.group("n") for m in (FAILED_NAME.match(x) for x in hits) if m],
                "passed": [m.group("n") for m in (PASSED_NAME.match(x) for x in lines) if m],
                "err": err, "setup": any(x.startswith("red-at: setup failed") for x in lines),
                "bad": err or bool(hits)})

    # The last index at which a call succeeded and a test passed: "later" is then one comparison.
    last_ok, last_pass = {}, {}
    for i, r in enumerate(results):
        if not r["bad"]:
            last_ok[bare(r["call"])] = i
        for p in r["passed"]:
            last_pass[p] = i

    groups, order = {}, []
    for i, r in enumerate(results):
        if not r["bad"]:
            continue
        b = bare(r["call"])
        if ((r["call"] != "" and last_ok.get(b, -1) > i) or (red.search(r["call"]) and not r["setup"])
                or any(last_pass.get(f, -1) > i for f in r["failed"])):
            mark = "~"
        elif r["err"]:
            mark = "!"
        else:
            mark = "?"
        o = {"m": mark, "name": r["name"], "line": r["line"], "use": r["use"], "call": squash(b), "text": squash(r["text"])[:w]}
        g = tojson([mark, o["name"], o["call"], o["text"]])
        if g in groups:
            groups[g][1].append(o["line"])
        else:
            groups[g] = (o, [o["line"]])
            order.append(g)
    return [groups[g] for g in order]


def format_frictions(groups, w):
    out = []
    for o, lines in groups:
        out.append("  %s %s%s %s: %s%s" % (
            o["m"], tostring(o["name"]), " ×%d" % len(lines) if len(lines) > 1 else "",
            ",".join("@%d" % n for n in lines), o["text"], " · " + o["call"][:w] if o["call"] != "" else ""))
    return out


def handbacks(entries):
    """The messages of a subagent's SubagentHandback calls: its final report."""
    return [b["input"]["message"] for e in entries if is_type(e, "assistant") for b in blocks(e)
            if b.get("type") == "tool_use" and b.get("name") == "SubagentHandback"
            and isinstance(get(b, "input", "message"), str)]


def report(entries, w):
    return ["  > " + squash(m)[:w * 3] for m in handbacks(entries)]


def first_string_prompt(entries):
    """The text of the first user entry whose content is a plain string."""
    for e in entries:
        if is_type(e, "user") and isinstance(get(e, "message", "content"), str):
            return e["message"]["content"]
    return None


def agent_prompt(entries, w, template=None):
    """The agent's prompt line; with a template, only its lines outside it."""
    p = first_string_prompt(entries)
    if p is None:
        return []
    if template is not None:
        p = "\n".join(x for x in p.split("\n") if NON_SPACE.search(x) and x.rstrip() not in template)
        if not p:
            return ["  prompt: (template only)"]
    return ["  prompt: " + squash(p)[:w]]


# --- Agent labels, briefs, hedges

def agent_id(path):
    ident = os.path.basename(path)
    if ident.endswith(".jsonl"):
        ident = ident[:-len(".jsonl")]
    if ident.startswith("agent-"):
        ident = ident[len("agent-"):]
    return ident


def label(path, entries):
    """An agent's description, model, id and start time, so same-named agents stay apart."""
    meta = path[:-len(".jsonl")] + ".meta.json" if path.endswith(".jsonl") else path + ".meta.json"
    head = "agent"
    if os.path.isfile(meta):
        try:
            with open(meta, "rb") as f:
                m = json.loads(f.read().decode("utf-8", "replace"))
            head = "%s [%s]" % (tostring(get(m, "description")), tostring(first_truthy(get(m, "model")) or "inherit"))
        except ValueError:
            pass
    ident = agent_id(path)
    start = next((e["timestamp"] for e in entries if truthy(get(e, "timestamp"))), None)
    return "%s · %s%s" % (head, ident[:8], " · " + start[11:16] if start is not None else "")


def short_who(lab):
    """The label without its start time and model, for the lines that quote an agent."""
    lab = re.sub(r" · ..:..$", "", lab, flags=re.S)
    return re.sub(r" \[.*\]", "", lab, count=1, flags=re.S)


def brief(entries, who):
    """The sentences of an agent's prompt that limit its work, shown beside its hedges."""
    p = first_string_prompt(entries)
    if p is None:
        return []
    return ["  %s brief: %s" % (who, s) for s in SENTENCE_END.split(squash(p)) if BRIEF_LIMIT.search(s)]


def drop_fences(text):
    """The text without its fenced code blocks, each replaced by a newline; an unterminated fence stays."""
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i])
        end = None
        if m:
            f = m.group(1)
            close = rx(r"[ \t]*%s{%d,}[ \t]*$" % (re.escape(f[0]), len(f)))
            end = next((j for j in range(i + 1, len(lines)) if close.match(lines[j])), None)
        if end is None:
            out.append(lines[i])
            i += 1
        else:
            out.append("")
            i = end + 1
    return "\n".join(out)


def sentences(text):
    return [s for s in SENTENCE_BREAK.split(squash(drop_fences(text))) if re.search(r"\w", s)]


def is_tally(line):
    """A table row, or a line of numbers whose only words are hedge words and units ("~120 KB estimated")."""
    return bool(TALLY_ROW.search(line)) or (bool(re.search(r"\d", line))
                                            and not re.search(r"[A-Za-z]{3,}", SIZE_UNITS.sub("", re.sub(r"\w*(?:%s)\w*" % HEDGE.pattern, "", line))))


def echoes_limit(sentence, prompt):
    """A sentence whose only gap is a negated verb the prompt also negates ("I did not push." under "Don't push.")."""
    if prompt is None:
        return False
    s = QUOTED_SPAN.sub("", sentence)
    negated = {m.group(1).lower() for m in NEGATED.finditer(prompt)}
    echoed = [m.group(0) for m in NEGATED.finditer(s) if m.group(1).lower() in negated]
    for phrase in echoed:
        s = s.replace(phrase, "")
    return bool(echoed) and not HEDGE.search(s)


def hedge_sentences(text, prompt=None):
    """The sentences of a text matching HEDGE outside findings, tally lines and a prompt's own limits."""
    body = "\n".join(x for x in drop_fences(text).split("\n") if not FINDING.search(x) and not is_tally(x))
    return [s for s in sentences(body) if not FINDING.search(s) and HEDGE.search(QUOTED_SPAN.sub("", s))
            and not echoes_limit(s, prompt)]


def hedges(entries, who):
    """The sentences of a report's gap sections (from a GAPS line to the next heading or bold line), else its
    sentences matching HEDGE outside findings; prefixed with the agent."""
    out = []
    prompt = first_string_prompt(entries)
    for message in handbacks(entries):
        lines = drop_fences(message).split("\n")
        if any(GAPS.search(x) for x in lines):
            inside, kept = False, []
            for x in lines:
                if GAPS.search(x):
                    inside = True
                elif HEADING.search(x):
                    inside = False
                if inside:
                    kept.append(x)
            found = [s for x in kept if not GAPS_ONLY.search(x) and not is_tally(x) for s in sentences(x)
                     if not echoes_limit(s, prompt)]
        else:
            found = hedge_sentences(message, prompt)
        out.extend("  %s: %s" % (who, s) for s in found)
    return out


def prose_hedges(entries):
    """The hedges in the assistant's own prose (the main log): a line per sentence, prefixed `main`."""
    return ["  main: " + s for e in entries if is_type(e, "assistant") for b in blocks(e) if b.get("type") == "text"
            for s in hedge_sentences(tostring(b.get("text")))]


# --- The human's turns in a log

def human_turns(entries):
    """The human's turns, each {l: line, t: time, x: text}: user entries that are not isMeta, whose text (a string, or
    the joined text blocks of an array) is non-blank once the harness-made pieces are dropped: entries opening with a
    local-command or task-notification tag, a message from another session or an agent's hand-back (origin peer, or
    text opening "Another Claude session sent a message"), and <system-reminder> spans. A typed slash command
    (<command-name>) stays."""
    out = []
    for l, e in enumerate(entries, 1):
        if not is_type(e, "user") or e.get("isMeta") is True:
            continue
        origin = e.get("origin")
        if origin is not None and not isinstance(origin, dict):
            continue
        if get(origin, "kind") == "peer":
            continue
        content = get(e, "message", "content")
        if isinstance(content, str):
            x = content
        else:
            x = " ".join(tostring(b["text"]) if truthy(b.get("text")) else ""
                         for b in blocks(e) if b.get("type") == "text")
        x = REMINDER.sub("", x)
        if not NOT_HUMAN.search(x) and NON_SPACE.search(x):
            out.append({"l": l, "t": hhmm(e.get("timestamp")), "x": x})
    return out


def main_prompt_and_turns(entries, w):
    turns = human_turns(entries)
    if not turns:
        return []
    p = next((t for t in turns if NON_SPACE.search(SLASH_TAGS.sub("", t["x"]))), turns[0])
    out = ["  prompt: " + squash(p["x"])[:w], "  -- user turns"]
    out += ["  @%d %s: %s" % (t["l"], t["t"], squash(t["x"])[:w]) for t in turns if t["l"] != p["l"]]
    return out


# --- Sections of the output

def label_all(paths, cache):
    return {p: label(p, cache[p]) for p in paths}


def section_ranking(paths, cache, labels, main_tokens):
    """The agents ranked by output tokens. The main log stays out of the ranking: in a fan-out the orchestrator tops
    it by construction."""
    rows = ["%s %s" % (tojson(output_tokens(cache[p])), labels[p]) for p in paths]
    rows.sort(key=lambda r: (float(r.split(" ", 1)[0]), r), reverse=True)
    out = ["## agents by out tokens"] + ["  " + r for r in rows]
    if main_tokens is not None:
        out.append("  main log, unranked: %s" % tojson(main_tokens))
    return out + [""]


def section_hedges(paths, cache, labels, main_entries=None):
    """Gaps the agents admitted: each is information an agent lacked, and a lead the other signals miss. The brief's
    limits come first, so a gap the brief ordered shows as one; one sentence shared by 2 or more of the agents printed
    here is said once, at the top. The main log's prose hedges follow the agents' as `main:` lines."""
    printed = []
    for p in paths:
        who = short_who(labels[p])
        found = hedges(cache[p], who)
        if found:
            printed.append((who, brief(cache[p], who), found))
    count = {}  # sentence -> agents with it, in order of first appearance
    for who, bs, _ in printed:
        for s in dict.fromkeys(b[len("  %s brief: " % who):] for b in bs):
            count[s] = count.get(s, 0) + 1
    shared = [s for s, n in count.items() if n >= 2]
    out = ["## hedges in reports"]
    out += ["  %s brief: %s" % ("all agents" if count[s] == len(printed) else "%d agents" % count[s], s) for s in shared]
    for who, bs, found in printed:
        out += [b for b in bs if b[len("  %s brief: " % who):] not in shared] + found
    return out + (prose_hedges(main_entries) if main_entries else []) + [""]


def agent_prompts(paths, cache):
    return [first_string_prompt(cache[p]) for p in paths]


def template_lines(paths, cache):
    """The non-blank prompt lines (trailing whitespace stripped) in every agent's prompt, in the first agent's order;
    empty with fewer than 2 agents."""
    prompts = agent_prompts(paths, cache)
    if len(prompts) < 2 or None in prompts:
        return []
    sets = [{x.rstrip() for x in p.split("\n") if NON_SPACE.search(x)} for p in prompts]
    out = []
    for x in prompts[0].split("\n"):
        x = x.rstrip()
        if NON_SPACE.search(x) and x not in out and all(x in s for s in sets):
            out.append(x)
    return out


def section_template(lines):
    return ["## brief template (lines in every agent's prompt)"] + ["  " + x for x in lines] + [""] if lines else []


def section_friction(paths, cache, groups, min_agents):
    """The friction lines (tool and text; the mark and call ignored) found in several agents, with each agent's line
    count: a failure every agent hit the same way."""
    per = {}
    for p in paths:
        for o, lines in groups[p]:
            per.setdefault((tostring(o["name"]), o["text"]), Counter())[agent_id(p)[:8]] += len(lines)
    rows = sorted(((len(c), sum(c.values()), k, c) for k, c in per.items() if len(c) >= min_agents),
                  key=lambda r: (-r[0], -r[1], r[2]))[:20]
    return ["## friction repeated across agents"] + [
        "  %d agents × %d lines · %s: %s · %s" % (a, n, k[0], k[1], ", ".join("%s %d" % (i, m) for i, m in c.most_common()))
        for a, n, k, c in rows] + [""]


def section_repeated(paths, cache, min_agents):
    """Commands several agents ran: a missing script, doc or check. Takes each command's first line, splits it on
    && ; || and a spaced |, drops `cd` and everyday reading/editing tools, keeps three words, and counts agents, not
    runs."""
    skip = {"cd", "cat", "sed", "grep", "head", "tail", "ls", "echo", "git", "wc", "find", "awk", "python3", "cut", "sort",
            "tr", "printf", "EOF", "for", "do", "done", "if", "then", "fi", "}", ")"}
    splitter = re.compile(r"&&|;|\|\||[ \t]\|[ \t]")
    counts = Counter()
    for p in paths:
        seen = set()
        for e in cache[p]:
            if not is_type(e, "assistant"):
                continue
            for b in blocks(e):
                cmd = get(b, "input", "command")
                if b.get("type") != "tool_use" or b.get("name") != "Bash" or not isinstance(cmd, str):
                    continue
                first = cmd.split("\n")[0] if cmd else "null"  # an empty command prints as null
                for part in splitter.sub("\n", first).split("\n"):
                    fields = re.split(r"[ \t]+", re.sub(r"^[ \t\n\r\f\v(]*", "", part).strip(" \t"))
                    fields = [f for f in fields if f]
                    if fields and fields[0] not in skip:
                        seen.add(" ".join((fields + ["", ""])[:3]))
        counts.update(seen)
    rows = sorted(("%7d %s" % (n, line) for line, n in counts.items() if n >= min_agents),
                  key=lambda r: (int(r[:7]), r), reverse=True)[:20]
    return ["## repeated across agents (agents × command)"] + ["  " + r for r in rows] + [""]


def to_read(flagged, min_agents=2):
    """(heading, also line or None, path, first line, its call's line) per ! and ? group. A friction key (tool, text)
    found in at least min_agents agents prints only its first agent group; the later ones go on its also: line. The
    main log's groups are never collapsed."""
    agents = {}
    for who, path, groups in flagged:
        if who != "main":
            for o, lines in groups:
                agents.setdefault((tostring(o["name"]), o["text"]), set()).add(who)
    shared = {k for k, v in agents.items() if len(v) >= min_agents}
    rows, first = [], {}
    for who, path, groups in flagged:
        for o, lines in groups:
            if o["m"] == "~":
                continue
            key = (tostring(o["name"]), o["text"])
            tag = "%s @%d%s" % (who, lines[0], " ×%d" % len(lines) if len(lines) > 1 else "")
            if who != "main" and key in shared:
                if key in first:
                    first[key][1].append(tag)
                    continue
            row = ["%s %s" % (o["m"], tag), [], path, lines[0], o["use"]]
            rows.append(row)
            if who != "main" and key in shared:
                first[key] = row
    return [(r[0], "also: " + ", ".join(r[1]) if r[1] else None, r[2], r[3], r[4]) for r in rows]


def section_main(path, entries, alive, w, groups):
    paused = stops(entries)
    out = ["## main session " + os.path.basename(path), stats(entries, paused)]
    out += pauses(entries, alive, w) + waits(entries, w) + main_prompt_and_turns(entries, w)
    out += ["  -- friction"] + format_frictions(groups, w)
    return out + [""]


def section_agent(lab, entries, alive, w, groups, template=None):
    out = ["## " + lab, stats(entries, stops(entries))]
    out += pauses(entries, alive, w) + waits(entries, w) + agent_prompt(entries, w, template)
    out += ["  -- friction"] + format_frictions(groups, w)
    out += ["  -- report"] + report(entries, w)
    return out + [""]


def cut_main(entries, session_id):
    """Up to the first call running digest on this session: the retro's own work starts there, wherever the retro was
    invoked (a retro queued at the start comes after the work). A call that names the session by a variable doesn't
    match, which keeps in only the few calls the retro made before it. digest.sh counts too: sessions retro'd before
    the rename call it by that name."""
    for i, e in enumerate(entries):
        if not is_type(e, "assistant"):
            continue
        for b in blocks(e):
            cmd = first_truthy(get(b, "input", "command")) or ""
            if (b.get("type") == "tool_use" and b.get("name") == "Bash" and isinstance(cmd, str)
                    and re.search(r"digest\.(?:sh|py)", cmd) and session_id in cmd):
                return entries[:i]
    return entries


def load(target, w, env):
    """The session's transcripts and their friction groups, the main log cut by cut_main."""
    d = target[:-1] if target.endswith("/") else target
    if d.endswith(".jsonl"):
        d = d[:-len(".jsonl")]
    if not os.path.isdir(d):
        d = ""
    main = (d or (target[:-len(".jsonl")] if target.endswith(".jsonl") else target)) + ".jsonl"
    if not os.path.isfile(main):
        main = ""
    if not d and not main:
        fail("no session dir or log at %s" % target)
    agent_paths = sorted(p for p in glob_agents(d)) if d else []

    cache = {p: read_entries(p) for p in ([main] if main else []) + agent_paths}
    main_entries = cut_main(cache[main], os.path.basename(main)[:-len(".jsonl")]) if main else None
    red = env.get("EXPECTED_RED", "")
    groups = {p: friction_groups(cache[p], w, red) for p in agent_paths}
    if main:
        groups[main] = friction_groups(main_entries, w, red)
    flagged = ([("main", main, groups[main])] if main else []) + [(agent_id(p)[:8], p, groups[p]) for p in agent_paths]
    return main, main_entries, agent_paths, cache, groups, flagged


def digest(target, w, env):
    main, main_entries, agent_paths, cache, groups, flagged = load(target, w, env)
    alive = alive_of([e for p in cache for e in cache[p]])
    template = template_lines(agent_paths, cache)

    out = []
    if agent_paths:
        labels = label_all(agent_paths, cache)
        out += section_ranking(agent_paths, cache, labels, output_tokens(main_entries) if main else None)
        out += section_template(template)
        out += section_hedges(agent_paths, cache, labels, main_entries)
        min_agents = int(env.get("MIN_AGENTS") or 2)
        out += section_repeated(agent_paths, cache, min_agents)
        out += section_friction(agent_paths, cache, groups, min_agents)
    elif main and prose_hedges(main_entries):
        out += ["## hedges in reports"] + prose_hedges(main_entries) + [""]
    if main:
        out += section_main(main, main_entries, alive, w, groups[main])
    for p in agent_paths:
        out += section_agent(label(p, cache[p]), cache[p], alive, w, groups[p], set(template) if template else None)
    return out


RED_BRIEF = rx(r"\btdd\b|red[- ]first|red tests?\b|mutation (test|run)", re.I)


def red_nudge(flagged, cache, env):
    """A note line naming the agents briefed for red tests that have ! windows on Bash calls, when EXPECTED_RED is unset."""
    if env.get("EXPECTED_RED"):
        return []
    who = []
    for id8, path, groups in flagged:
        prompt = first_string_prompt(cache[path]) if id8 != "main" else None
        if prompt is not None and RED_BRIEF.search(prompt) and any(o["m"] == "!" and o["name"] == "Bash" for o, _ in groups):
            who.append(id8)
    if not who:
        return []
    return ["note: agents briefed for red tests have ! windows (%s): when their reds were meant, rewrite with "
            "EXPECTED_RED='<regex of their commands>'" % ", ".join(who)]


def to_read_windows(target, radius, w, env):
    """The widen command as a template and a `<who> <path>` line per transcript with a group, then each group's
    heading, its also: line and its --around window, a blank line between groups; a call outside the window (hook
    attachments sit between it and its result) prints above it."""
    _, _, _, cache, _, flagged = load(target, w, env)
    rows = to_read(flagged, int(env.get("MIN_AGENTS") or 2))
    if not rows:
        return []
    out = ["widen: %s --around <transcript> <line> <radius>" % shlex.quote(os.path.abspath(__file__))]
    out += red_nudge(flagged, cache, env)
    out += ["%s %s" % (who, shlex.quote(path)) for who, path, groups in flagged
             if any(o["m"] != "~" for o, _ in groups)] + [""]
    for i, (heading, also, path, n, u) in enumerate(rows):
        window = around(path, n, radius, w)
        call = [] if any(x.startswith("@%d " % u) for x in window) else around(path, u, 0, w)
        out += ([""] if i else []) + [heading] + ([also] if also else []) + call + window
    return out


def glob_agents(d):
    sub = os.path.join(d, "subagents")
    try:
        names = os.listdir(sub)
    except OSError:
        return []
    return [os.path.join(d, "subagents", n) for n in names if n.startswith("agent-") and n.endswith(".jsonl")]


# --- --around and --text

def around(path, n, r, w):
    """The r printed entries before line n, line n and the r printed entries after it; entries that only carry harness
    context are not printed and not counted."""
    found = []
    for l, line in enumerate(read_lines(path), 1):
        if not line.strip():
            continue
        e = parse_line(line, path, l)
        if not isinstance(e, dict) or e.get("isMeta") is True or e.get("type") == "attachment" \
                or not isinstance(e.get("message"), dict):
            continue
        content = e["message"].get("content")
        if not truthy(content):
            continue
        items = [{"type": "text", "text": content}] if isinstance(content, str) else \
            [b for b in iterate(content) if isinstance(b, dict)]
        shown = []
        for b in items:
            kind = b.get("type")
            if kind == "text" and HARNESS_TEXT.search(tostring(b.get("text"))):
                continue
            if kind == "text":
                s = tostring(b.get("text"))
            elif kind == "tool_use":
                s = "%s: %s" % (tostring(b.get("name")), tostring(b.get("input")))
            elif kind == "tool_result":
                s = "result%s: %s" % (" (error)" if truthy(b.get("is_error")) else "", result_text(b.get("content"), "\n"))
            else:
                continue
            shown.append("@%d %s" % (l, squash(REMINDER.sub("", s))[:w]))
        if shown:
            found.append((l, shown))
    before = ([f for f in found if f[0] < n][-r:] if r else [])
    after = [f for f in found if f[0] > n][:r]
    return [s for f in before + [f for f in found if f[0] == n] + after for s in f[1]]


def text_blocks(path, w):
    """The agent's prose, a line per text block."""
    out = []
    for n, line in enumerate(read_lines(path), 1):
        if not line.strip():
            continue
        e = parse_line(line, path, n)
        if is_type(e, "assistant"):
            out += ["@%d %s" % (n, squash(tostring(b.get("text")))[:w]) for b in blocks(e) if b.get("type") == "text"]
    return out


def usage(text):
    sys.stderr.write("digest.py: usage: %s\n" % text)
    sys.exit(1)


def number(s, what):
    try:
        return int(s)
    except ValueError:
        fail("%s must be a number: %s" % (what, s), 1)


def emit(lines):
    sys.stdout.buffer.write(("\n".join(lines) + "\n" if lines else "").encode("utf-8", "replace"))
    sys.stdout.buffer.flush()


def main(argv):
    first = argv[0] if argv else ""
    if first in ("--help", "-h"):
        emit(__doc__.rstrip("\n").split("\n"))
    elif first == "--around":
        if len(argv) < 2 or not argv[1]:
            usage("digest.py --around <transcript.jsonl> <line> [radius [width]]")
        if len(argv) < 3 or not argv[2]:
            usage("line")
        emit(around(argv[1], number(argv[2], "line"), number(argv[3] if len(argv) > 3 and argv[3] else "3", "radius"),
                    number(argv[4] if len(argv) > 4 and argv[4] else "400", "width")))
    elif first == "--to-read":
        if len(argv) < 2 or not argv[1]:
            usage("digest.py --to-read <session-dir | session.jsonl> [radius [width]]")
        emit(to_read_windows(argv[1], number(argv[2] if len(argv) > 2 and argv[2] else "1", "radius"),
                             number(argv[3] if len(argv) > 3 and argv[3] else "400", "width"), os.environ))
    elif first == "--prompt":
        if len(argv) < 2 or not argv[1]:
            usage("digest.py --prompt <transcript.jsonl>")
        p = first_string_prompt(read_entries(argv[1]))
        emit([] if p is None else p.split("\n"))
    elif first == "--calls":
        if len(argv) < 2 or not argv[1]:
            usage("digest.py --calls <transcript.jsonl> [width]")
        emit(calls(read_entries(argv[1]), number(argv[2] if len(argv) > 2 and argv[2] else "400", "width")))
    elif first == "--text":
        if len(argv) < 2 or not argv[1]:
            usage("digest.py --text <transcript.jsonl> [width]")
        emit(text_blocks(argv[1], number(argv[2] if len(argv) > 2 and argv[2] else "400", "width")))
    else:
        if not first:
            usage("digest.py <session-dir | session.jsonl> [width]")
        emit(digest(first, number(argv[1] if len(argv) > 1 and argv[1] else "160", "width"), os.environ))


if __name__ == "__main__":
    main(sys.argv[1:])
