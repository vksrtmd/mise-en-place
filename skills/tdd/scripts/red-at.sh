#!/usr/bin/env bash
# Run a new check against old code: a detached worktree at <rev>, the named files copied in from the
# current worktree, an optional setup, then the test. Prints the test's output and exits with its status,
# so a check that goes red on <rev> exits non-zero; a failing setup exits 125 (can't test, as in git bisect).
# The current worktree is never touched.
# Usage: red-at.sh <rev> [--setup "<cmd>"] --copy <file>... -- <test cmd>...
#   Paths are relative to the current worktree's root. RED_AT_DIR overrides where the scratch worktree goes
#   (default: <root>/.claude/worktrees/red-at-<pid>, inside the repo so bind mounts and the host see it).
set -euo pipefail

usage() { echo "usage: red-at.sh <rev> [--setup \"<cmd>\"] --copy <file>... -- <test cmd>..." >&2; exit 2; }
[ $# -ge 1 ] || usage
rev=$1; shift
setup=""; files=()
while [ $# -gt 0 ]; do
  case $1 in
    --setup) [ $# -ge 2 ] || usage; setup=$2; shift 2 ;;
    --copy) shift; while [ $# -gt 0 ] && [ "$1" != "--" ] && [ "$1" != "--setup" ] && [ "$1" != "--copy" ]; do files+=("$1"); shift; done ;;
    --) shift; break ;;
    *) usage ;;
  esac
done
[ ${#files[@]} -gt 0 ] && [ $# -gt 0 ] || usage

root=$(git rev-parse --show-toplevel)
git rev-parse --verify -q "$rev^{commit}" >/dev/null || { echo "red-at: no commit $rev" >&2; exit 2; }
for f in "${files[@]}"; do [ -e "$root/$f" ] || { echo "red-at: no file $f under $root" >&2; exit 2; }; done

wt=${RED_AT_DIR:-$root/.claude/worktrees/red-at-$$}
exclude="$(git rev-parse --git-common-dir)/info/exclude"
case $wt in "$root"/.claude/worktrees/*)
  grep -qxF .claude/worktrees/ "$exclude" 2>/dev/null || echo .claude/worktrees/ >> "$exclude" ;;
esac

# Commit the scratch state on the detached HEAD, so a plain `git worktree remove` succeeds; the commit is
# on no branch and gc drops it.
cleanup() {
  git -C "$wt" add -A >/dev/null 2>&1 || true
  git -C "$wt" -c user.name=red-at -c user.email=red-at@localhost -c commit.gpgsign=false \
    commit -q --no-verify -m "red-at scratch" >/dev/null 2>&1 || true
  git worktree remove "$wt" || echo "red-at: left $wt in place; remove it with git worktree remove" >&2
}
git worktree add -q --detach "$wt" "$rev"
trap cleanup EXIT

for f in "${files[@]}"; do mkdir -p "$wt/$(dirname "$f")"; cp -p "$root/$f" "$wt/$f"; done
echo "red-at: $(git -C "$wt" rev-parse --short HEAD) + ${files[*]}" >&2
cd "$wt"
[ -z "$setup" ] || bash -c "$setup" || { echo "red-at: setup failed" >&2; exit 125; }
set +e; "$@"; status=$?; set -e
echo "red-at: exit $status" >&2
exit $status
