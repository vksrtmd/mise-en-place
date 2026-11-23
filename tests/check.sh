#!/usr/bin/env bash
# Repo guardrail. Run from anywhere; exits non-zero and prints file:line: message per problem.
# Bash 3.2 compatible (macOS): no associative arrays, no GNU-only flags.
set -u
cd "$(dirname "$0")/.." || exit 2

# Built-in Claude Code commands, plus backticked tokens that look like /name but are
# paths or routes, not skills.
ALLOW="clear compact goal tmp settings"

fail=0
out=$(mktemp) || exit 2
trap 'rm -f "$out"' EXIT
report() { echo "$1"; fail=1; }

files=$( { find skills docs rules -name '*.md' -type f 2>/dev/null; [ -f CLAUDE.md ] && echo CLAUDE.md; } | sort)

# 1. Dangling skill references. A code span (text between a pair of single backticks)
# that is exactly "/" + a kebab-case name, optionally followed by a space and args:
# `/to-tickets`, `/compact keep the QA notes`. Not `/tmp/x` or `src/x/docs`.
# Checked inside fenced code blocks too: a template naming a skill must name a real one.
for f in $files; do
  awk '{
    n = split($0, a, "`")
    for (i = 2; i < n; i += 2)
      if (a[i] ~ /^\/[a-z0-9]+(-[a-z0-9]+)*( .*)?$/) {
        name = substr(a[i], 2); sub(/ .*/, "", name)
        print FNR " " name
      }
  }' "$f" | while read -r line name; do
    case " $ALLOW " in *" $name "*) continue ;; esac
    [ -f "skills/$name/SKILL.md" ] || echo "$f:$line: /$name has no skills/$name/SKILL.md"
  done
done > "$out"

# 2. Broken relative links: [text](target) outside fenced code blocks and code spans,
# where target is not a URL, #anchor or mailto:. The #fragment is dropped and the path
# resolved against the linking file's directory.
for f in $files; do
  dir=$(dirname "$f")
  awk '
    /^[ \t]*(```|~~~)/ { fence = !fence; next }
    fence { next }
    {
      s = $0; gsub(/`[^`]*`/, "", s)
      while (match(s, /\]\([^)]*\)/)) {
        t = substr(s, RSTART + 2, RLENGTH - 3); s = substr(s, RSTART + RLENGTH)
        sub(/^</, "", t); sub(/[ >].*$/, "", t)
        if (t == "" || t ~ /^(https?:|mailto:|#)/) continue
        sub(/#.*/, "", t)
        print FNR " " t
      }
    }' "$f" | while read -r line target; do
    [ -e "$dir/$target" ] || echo "$f:$line: broken link: $target"
  done
done >> "$out"
[ -s "$out" ] && { cat "$out"; fail=1; }

# 3. Install drift: the README's `for d in ...; do` install loop must name only files that exist and every
# installed top-level directory (all but .git, .claude, .github, tests and ignored ones).
loop_line=$(grep -n '^ *for d in [^;]*; do' README.md | head -n 1)
if [ -z "$loop_line" ]; then
  report "README.md:1: no 'for d in ...; do' install loop found"
else
  lnum=${loop_line%%:*}
  loop=$(echo "${loop_line#*:}" | sed 's/^ *for d in //; s/; do.*//')
  for d in $loop; do
    [ -e "$d" ] || report "README.md:$lnum: install loop names $d, which does not exist"
  done
  for p in * .[!.]*; do
    [ -d "$p" ] || continue
    case "$p" in .git|.claude|.github|tests) continue ;; esac
    git check-ignore -q "$p" && continue
    case " $loop " in *" $p "*) ;; *) report "README.md:$lnum: top-level directory $p is missing from the install loop" ;; esac
  done
fi


# 4. Hook and skill-script tests: one tests/test_*.py per hook and per skill script.
for t in tests/test_*.py; do
  "$t" || fail=1
done

exit $fail
