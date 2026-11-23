#!/usr/bin/env bash
# Measure how often a skill's description makes Claude invoke it. Copies the skill into a temp project
# under a trial name (<name>-<id>), runs each query in a fresh `claude -p` session cut at one turn, and
# reads the run's first tool call: the Skill tool (or a Read of the SKILL.md) on the trial copy, on the
# installed copy of the same name, on another skill, another tool, or none. A fire counts either copy,
# since an installed one stays listed beside the trial one. The other skills a query can go to are the
# ones installed where the script runs, so near misses test only against those.
# A query passes when its fire rate is at least half (should_trigger true) or below half (false).
# Usage: trigger.sh <skill dir> <queries.json> [runs per query, default 3]
#   queries.json: [{"query": "...", "should_trigger": true}, ...]
#   Env: TRIGGER_JOBS parallel sessions (default 4), TRIGGER_TIMEOUT seconds per run (default 120),
#   TRIGGER_MODEL passed as --model. Exits 1 when a query fails or every run errors, 2 on bad usage.
# Each run is a full session and spends tokens. Needs a logged-in claude CLI and jq. Bash 3.2 compatible.
set -u

if [ "${1:-}" = --run ]; then
  # One run: --run <query index> <run index>, with TRIGGER_PROJ, TRIGGER_QUERIES, TRIGGER_TRIAL and
  # TRIGGER_NAME set by the parent. Prints "<query index> <outcome>".
  i=$2; r=$3; out=$TRIGGER_PROJ/runs/$i.$r
  q=$(jq -r ".[$i].query" "$TRIGGER_QUERIES")
  set -- -p "$q" --output-format stream-json --verbose --max-turns 1
  [ -n "${TRIGGER_MODEL:-}" ] && set -- "$@" --model "$TRIGGER_MODEL"
  (cd "$TRIGGER_PROJ" && exec env -u CLAUDECODE claude "$@") > "$out" 2> "$out.err" &
  pid=$!
  # The watchdog's sleep must die with it and hold no pipe, or the caller waits out the timeout.
  (trap 'kill $s 2>/dev/null; exit' TERM; sleep "${TRIGGER_TIMEOUT:-120}" & s=$!; wait $s; kill "$pid") \
    > /dev/null 2>&1 &
  dog=$!
  wait "$pid" 2>/dev/null; st=$?
  kill "$dog" 2>/dev/null
  # One write per line: parallel runs share the output.
  o=$(jq -nrR --arg t "$TRIGGER_TRIAL" --arg n "$TRIGGER_NAME" --argjson st "$st" '
    [inputs | fromjson? // empty | select(.type == "assistant") | .message.content[]? | select(.type == "tool_use")] as $u
    | if ($u | length) == 0 and $st != 0 then "error"
      elif ($u | length) == 0 then "none"
      else $u[0]
        | if .name == "Skill" then (.input.skill // "" | ltrimstr("/")) as $s
            | if $s == $t then "this" elif $s == $n then "installed" else "skill:" + $s end
          elif .name == "Read" and (.input.file_path // "" | endswith("/SKILL.md")) then
            (.input.file_path | split("/") | .[-2]) as $s
            | if $s == $t then "this" elif $s == $n then "installed" else "skill:" + $s end
          else "tool:" + .name end
      end' < "$out")
  echo "$i $o"
  exit 0
fi

[ $# -ge 2 ] && [ -f "$1/SKILL.md" ] && [ -f "$2" ] || {
  echo "usage: trigger.sh <skill dir> <queries.json> [runs per query]" >&2; exit 2; }
runs=${3:-3}
n=$(jq 'if type == "array" then length else error("") end' "$2" 2>/dev/null) || {
  echo "trigger.sh: $2 is not a JSON array" >&2; exit 2; }
[ "${n:-0}" -gt 0 ] || { echo "trigger.sh: $2 has no queries" >&2; exit 2; }
name=$(awk 'NR > 1 && /^---/ { exit } /^name:/ { sub(/^name:[ \t]*/, ""); print; exit }' "$1/SKILL.md")
[ -n "$name" ] || { echo "trigger.sh: $1/SKILL.md has no name" >&2; exit 2; }

TRIGGER_PROJ=$(mktemp -d) || exit 2
trap 'rm -rf "$TRIGGER_PROJ"' EXIT
TRIGGER_TRIAL=$name-$(LC_ALL=C tr -dc a-f0-9 < /dev/urandom | head -c 6)
TRIGGER_NAME=$name
TRIGGER_QUERIES=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
export TRIGGER_PROJ TRIGGER_TRIAL TRIGGER_NAME TRIGGER_QUERIES
copy=$TRIGGER_PROJ/.claude/skills/$TRIGGER_TRIAL
mkdir -p "$TRIGGER_PROJ/.claude/skills" "$TRIGGER_PROJ/runs"
cp -R "$1" "$copy"
awk -v t="$TRIGGER_TRIAL" '!done && /^name:/ { print "name: " t; done = 1; next } { print }' \
  "$1/SKILL.md" > "$copy/SKILL.md"

i=0
while [ "$i" -lt "$n" ]; do
  r=0; while [ "$r" -lt "$runs" ]; do echo "$i $r"; r=$((r + 1)); done
  i=$((i + 1))
done | xargs -P "${TRIGGER_JOBS:-4}" -n 2 "$BASH" "$0" --run > "$TRIGGER_PROJ/outcomes"

errors=$(grep -c ' error$' "$TRIGGER_PROJ/outcomes")
if [ "$errors" -eq $((n * runs)) ]; then
  echo "trigger.sh: every run failed; first error:" >&2
  cat "$TRIGGER_PROJ"/runs/*.err 2>/dev/null | grep -m 1 . >&2
  exit 1
fi

jq -nrR --slurpfile qs "$TRIGGER_QUERIES" --argjson runs "$runs" '
  def count(f): map(select(f)) | length;
  [inputs | split(" ") | {i: (.[0] | tonumber), o: .[1]}] as $all
  | [range($qs[0] | length) as $i | $qs[0][$i] as $q | [$all[] | select(.i == $i) | .o] as $o
     | ($o | count(. == "this" or . == "installed")) as $fire
     | (if $q.should_trigger then $fire * 2 >= $runs else $fire * 2 < $runs end) as $pass
     | ($o | map(select(. != "this" and . != "installed")) | group_by(.) | map("\(.[0]) \(length)")) as $also
     | {pass: $pass, line: (
         "\(if $pass then "PASS" else "FAIL" end)  fire \($fire)/\($runs)"
         + " (this \($o | count(. == "this")), installed \($o | count(. == "installed")))"
         + "  expect \(if $q.should_trigger then "fire" else "none" end)"
         + (if $also == [] then "" else "  also: " + ($also | join(", ")) end)
         + "\n      " + ($q.query | gsub("\n"; " ") | if length > 100 then .[:100] + "…" else . end))}]
  | (.[].line),
    "passed \(count(.pass))/\(length) queries, \($runs) runs each, trial name \(env.TRIGGER_TRIAL)",
    (if all(.pass) then empty else "FAILED" end)' < "$TRIGGER_PROJ/outcomes" > "$TRIGGER_PROJ/report" || exit 2
grep -vx FAILED "$TRIGGER_PROJ/report"
[ "$errors" -gt 0 ] && echo "$errors runs errored (claude failed or timed out before a tool call); they count as no fire."
! grep -qx FAILED "$TRIGGER_PROJ/report"
