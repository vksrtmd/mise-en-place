#!/usr/bin/env bash
# PreToolUse(Bash): warn when `gh pr create|edit` from an issue branch sends a body (--body, or
# --body-file read from the command's heredoc or a file) without a keyword that closes an issue
# (`Closes #<n>`).

input=$(cat)
cmd=$(jq -r '.tool_input.command // empty' <<<"$input")

[[ $cmd =~ gh[[:space:]]+pr[[:space:]]+(create|edit) ]] || exit 0
[[ $cmd =~ [[:space:]](--body|-b|--body-file|-F)([[:space:]]|=) ]] || exit 0

# Only a branch named <issue_number>-<slug> delivers an issue: --head/-H, else the branch the
# command runs on (a leading `cd DIR &&`, else the hook's cwd). An unknown branch still warns.
dir=$(jq -r '.cwd // "."' <<<"$input")
[[ $cmd =~ ^[[:space:]]*cd[[:space:]]+([^[:space:]\;\&\|]+) ]] && { d=${BASH_REMATCH[1]//[\"\']/}; [[ $d == /* ]] && dir=$d || dir=$dir/$d; }
if [[ $cmd =~ [[:space:]](--head|-H)(=|[[:space:]]+)([^[:space:]\;\&\|]+) ]]; then branch=${BASH_REMATCH[3]//[\"\']/}
else branch=$(git -C "$dir" branch --show-current 2>/dev/null); fi
[[ -z $branch || $branch =~ ^[0-9]+- ]] || exit 0

body=$cmd
if [[ $cmd =~ (--body-file|-F)(=|[[:space:]]+)(\"[^\"]*\"|\'[^\']*\'|[^[:space:]\;\&\|]+) ]]; then
  f=${BASH_REMATCH[3]} f=${f//[\"\']/}
  [[ $f == /* ]] || f="$(jq -r '.cwd // "."' <<<"$input")/$f"
  [ -r "$f" ] && body+=$'\n'$(cat "$f")
fi
# GitHub closes the issue on any of these keywords, in any case.
shopt -s nocasematch
[[ $body =~ (^|[^[:alnum:]])(close[sd]?|fix(e[sd])?|resolve[sd]?):?[[:space:]]+#[0-9] ]] && exit 0

jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext:
  "The PR body you are sending has no `Closes #<n>`. If this branch is named `<issue_number>-<slug>` and delivers that issue, the body must say `Closes #<n>`. `Refs` leaves the issue open after merge. Keep `Refs` only for partial work."}}'
exit 0
