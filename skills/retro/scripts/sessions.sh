#!/usr/bin/env bash
# List a project's Claude Code sessions, newest first, so a retro can match "the /implement 20 run" or "the two
# sessions before this one" to log files in one call. Reads only; prints to stdout.
# Usage: sessions.sh [-n N] [start dir ...]   default: the dir of $PWD; N (default 20) caps the merged list
#        sessions.sh --help | -h
#   A start dir maps to ~/.claude/projects/<dir with every non-alphanumeric char as ->; give several (a repo and
#   its worktrees) to merge them. $CLAUDE_PROJECTS overrides ~/.claude/projects.
# Output: a `# <project dir>` header per dir (the logs are <project dir>/<session id>.jsonl), then per session:
#   9d30a9a2-a740-4824-9a55-65857ba1ce40  11-16 16:11–16:14  main  out 12k  agents 0  ⟲ "retro on retro. was it..."
#   session id · start MM-DD and start–end HH:MM in UTC (an end on another day prints MM-DD HH:MM) ·
#   branch (`a→b` when it changed) · output tokens · subagent transcripts in <id>/subagents · first prompt, cut
#   to 80 chars (`/cmd args` for a slash command; `-` when there is none), after `⟲` when the session opened with
#   /clear, as `⟲ 42a665db "..."`: the first 8 id chars of the session it cleared, the one in the same project dir
#   whose last timestamp is the latest at or before this session's first (a session still live then is skipped;
#   `⟲ ?` when none). With several start dirs, each header and row opens with
#   the dir's [k]. Exits 1 when no start dir has logs.
set -u

if [ "${1:-}" = --help ] || [ "${1:-}" = -h ]; then
  sed -n '2,/^set -u/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'
  exit
fi

n=20
if [ "${1:-}" = -n ]; then n=${2:?usage: sessions.sh [-n N] [start dir ...]}; shift 2; fi
case $n in ''|*[!0-9]*) echo "sessions.sh: -n wants a number" >&2; exit 2;; esac
[ $# -gt 0 ] || set -- "$PWD"
base=${CLAUDE_PROJECTS:-$HOME/.claude/projects}

rows=$(mktemp) || exit 2
trap 'rm -f "$rows"' EXIT
k=0; found=0
for a in "$@"; do
  case $a in "$base"/*) p=$a;; *) p=$base/$(printf '%s' "$a" | sed 's/[^A-Za-z0-9]/-/g');; esac
  [ -d "$p" ] || { echo "sessions.sh: no logs at $p" >&2; continue; }
  k=$((k + 1)); found=1; tag=""; [ $# -gt 1 ] && tag="[$k] "
  echo "# $tag$p"
  for f in "$p"/*.jsonl; do
    [ -f "$f" ] || continue
    id=$(basename "$f" .jsonl)
    agents=$(ls "$p/$id/subagents"/agent-*.jsonl 2>/dev/null | wc -l | tr -d ' ')
    jq -Rrs --arg p0 "$p" --arg id "$id" --arg agents "$agents" --arg tag "$tag" '
      [split("\n")[] | fromjson? | objects] as $e
      | [$e[] | select(.timestamp != null)] as $t
      | ($t | map(.timestamp)) as $ts
      | ([$t[].gitBranch | select(. != null and . != "")]) as $b
      | ([$e[] | select(.type == "assistant") | .message.usage.output_tokens // 0] | add // 0) as $o
      | [$e[] | select(.type == "user" and .isMeta != true and (.message.content | type) == "string")
           | .message.content | select(test("^\\s*<local-command") | not)] as $us
      | (($us[0] // "") | test("^\\s*<command-name>/clear</command-name>")) as $cleared
      | ([$us[] | select(test("^\\s*<command-name>/clear</command-name>") | not)][0] // "") as $c
      | ($c | if test("<command-name>") then
            ((capture("<command-name>(?<n>[^<]*)</command-name>").n)
             + ((capture("<command-args>(?<a>[^<]*)</command-args>").a // "") | if . == "" then "" else " " + . end))
          else . end
          | sub("^❯ "; "") | gsub("\\s+"; " ") | sub("^ "; "") | sub(" $"; "")) as $p
      | ($ts[0] // "") as $s | ($ts[-1] // $s) as $en
      | (if $s == "" then "-" else $s[5:10] + " " + $s[11:16] + "–"
           + (if $en[0:10] == $s[0:10] then "" else $en[5:10] + " " end) + $en[11:16] end) as $when
      | (if ($b | length) == 0 then "-" elif $b[0] == $b[-1] then $b[0] else $b[0] + "→" + $b[-1] end) as $br
      | ($tag + $id + "  " + $when + "  " + $br + "  out "
         + (if $o >= 1000 then "\(($o / 1000 + 0.5) | floor)k" else "\($o)" end)
         + "  agents " + $agents + (if $cleared then "  ⟲ @@CLR@@ \"" else "  \"" end)
         + (if $p == "" then "-" elif ($p | length) > 80 then $p[0:80] + "..." else $p end) + "\"") as $line
      | "\($s)\t\($en)\t\($p0)\t\($id)\t\($line)"' "$f" >> "$rows"
  done
done
# rows: start, end, project dir, id, line. A ⟲ row's @@CLR@@ becomes the id of the latest-ending session of its dir
# that ended at or before its start (itself excluded).
awk -F'\t' -v OFS='\t' '
  NR == FNR { n++; s[n] = $1; e[n] = $2; d[n] = $3; i[n] = $4; next }
  { m = ""; if ($1 != "") for (k = 1; k <= n; k++)
      if (d[k] == $3 && i[k] != $4 && e[k] != "" && e[k] <= $1 && (m == "" || e[k] > e[m])) m = k
    c = (m == "" ? "?" : substr(i[m], 1, 8)); x = index($5, "@@CLR@@")
    if (x) $5 = substr($5, 1, x - 1) c substr($5, x + 7)
    print $1, $5 }' "$rows" "$rows" | sort -r | head -n "$n" | cut -f2-
[ $found = 1 ]
