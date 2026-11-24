#!/usr/bin/env bash
# PreToolUse(Bash): block git commands that throw away uncommitted work, other agents' worktrees,
# their stash entries or pushed history.
# Catches slips, not evasion. Known issues, each pinned in tests/test_block_destructive_git.py:
# - no string match sees through `g=git; $g reset --hard`;
# - an unpaired apostrophe (echo it's) pairs with the next one on its line and hides what's between;
# - a single-quoted -m '...' message spanning lines is checked line by line, as commands;
# - a "<<EOF" inside quotes is taken for a heredoc, and the lines after it go unchecked;
# - "git checkout <path>" reads like "git checkout <branch>", so a lone path is let through;
# - a cd inside ( ) still counts after the subshell closes, so "git branch -D" is checked in its directory.

# Fail closed: a hook that can't read the command must not allow it.
command -v jq >/dev/null || { echo "BLOCKED: jq is not on PATH, so the destructive-git hook can't check this command." >&2; exit 2; }
input=$(cat)
cmd=$(jq -r '.tool_input.command // empty' <<<"$input") || { echo "BLOCKED: the destructive-git hook couldn't parse its input." >&2; exit 2; }
dir=$(jq -r '.cwd // empty' <<<"$input")
# Drop heredoc bodies: what cat or "git commit -F -" reads is text, not commands. Keep the body
# when the line runs a shell (bash <<EOF, cat <<EOF | sh), which executes it.
cmd=$(awk '
  n {
    line = $0
    if (tabs[i]) sub(/^\t+/, "", line)
    if (line == delim[i]) { if (++i > n) n = 0 }
    else if (keep) print
    next
  }
  {
    print
    keep = /(^|[^[:alnum:]_.-])(ba|da|k|z)?sh([[:space:]]|$)/
    rest = $0; i = 1
    while (match(rest, /(^|[^<])<<-?[[:space:]]*[\\\047"]?[[:alnum:]_]+/)) {
      tok = substr(rest, RSTART, RLENGTH); rest = substr(rest, RSTART + RLENGTH)
      sub(/^[^<]?<</, "", tok)
      tabs[++n] = sub(/^-/, "", tok)
      sub(/^[[:space:]]*[\\\047"]?/, "", tok)
      delim[n] = tok
    }
  }' <<<"$cmd")
# Join backslash-continued lines, as the shell does, so "git reset \<newline>--hard" is one command.
# After the heredoc pass: a body line ending in \ must not swallow its closing delimiter.
cmd=${cmd//$'\\\n'/}
# Before quote stripping, for the branch -D expansion check below; heredoc bodies are already gone.
unquoted=$cmd
# Unquote the script of sh -c, bash -lc or eval, so a wrapped command is checked like a bare one.
wrap="((^|[^[:alnum:]_-])((ba|da|k|z)?sh([[:space:]]+-[[:alnum:]]+)*|eval)[[:space:]]+)"
# perl -0 reads the whole string, so a double-quoted message spanning lines is one string (BSD sed is per line).
# Single quotes pair within a line, so an apostrophe (it's) can't hide the lines after it.
cmd=$(perl -0pe "s/$wrap'([^'\n]*)'/\\1 \\6 /g; s/$wrap\"((?:[^\"\\\\]|\\\\.)*)\"/\\1 \\6 /gs" <<<"$cmd")
# Drop the remaining quoted strings so commit messages and echo text can't match.
cmd=$(perl -0pe "s/'[^'\n]*'//g; s/\"(?:[^\"\\\\]|\\\\.)*\"//gs" <<<"$cmd")
# Tabs to spaces, runs of spaces to one, so "git worktree  prune" still matches.
cmd=$(tr -s "\t " "  " <<<"$cmd")

block() {
  echo "BLOCKED: '$1' ${2:-discards uncommitted work. Commit first (a WIP commit is fine)}, or ask the user to run it." >&2
  exit 2
}

# Resolves a cd or -C target against $dir; prints nothing when it can't (a quoted path was stripped).
at() {
  case $1 in
    /*) echo "$1" ;;
    '~'*) echo "$HOME${1#\~}" ;;
    ''|*\$*) ;;
    *) [[ -n $dir ]] && echo "$dir/$1" ;;
  esac
}

# Succeeds when "git ... branch -D <names>" loses no commit: each tip is on a ref other than the
# named branches (origin's copy, main), or its diff since the default branch forked landed
# there as one commit (a squash merge).
lossless() {
  local d=$dir t tip def mb id skip=0 n=0 names=() tips=()
  [[ ${1%% branch *} =~ \ -C\ ([^\ ]+) ]] && d=$(at "${BASH_REMATCH[1]}")
  [[ -n $d ]] || return 1
  for t in ${1#* branch }; do
    ((skip)) && { skip=0; continue; }
    case $t in
      *[\<\>]) skip=1 ;;
      -*|*[\<\>]*) ;;
      *) tip=$(git -C "$d" rev-parse -q --verify "refs/heads/$t^{commit}") || return 1
         names+=("refs/heads/$t") tips+=("$tip") ;;
    esac
  done
  # A repo without a remote squash-merges into its local main or master.
  for def in "$(git -C "$d" rev-parse -q --verify --abbrev-ref origin/HEAD)" origin/main main master; do
    git -C "$d" rev-parse -q --verify "$def^{commit}" >/dev/null && break
  done
  for tip in "${tips[@]}"; do
    ((++n))
    git -C "$d" for-each-ref --contains "$tip" --format='%(refname)' | grep -qvxF "${names[@]/#/-e}" && continue
    mb=$(git -C "$d" merge-base "$def" "$tip" 2>/dev/null) || return 1
    id=$(git -C "$d" diff "$mb" "$tip" | git patch-id --stable | cut -d' ' -f1)
    [[ -n $id ]] && git -C "$d" log -p --no-merges "$mb..$def" | git patch-id --stable | cut -d' ' -f1 | grep -qxF "$id" || return 1
  done
  ((n))
}

# One shell command per line: split on ; & | ( ) ` and newlines, so subshells and $(...) count.
# shellcheck disable=SC2020  # each separator char becomes a newline
while IFS= read -r seg; do
  # Follow cd, so "cd /x && git branch -D y" checks y in /x.
  [[ $seg =~ ^\ *cd(\ +([^\ ]*))?\ *$ ]] && { dir=$(at "${BASH_REMATCH[2]}"); continue; }
  [[ $seg =~ (^|[[:space:]/])git[[:space:]](.*) ]] || continue
  args=" ${BASH_REMATCH[2]} "
  case $args in
    *" reset "*" --hard "*|*" reset --hard "*) block "git reset --hard" "discards uncommitted work. Set it aside with 'git commit -am wip', undo later with 'git reset --soft HEAD~1'" ;;
    *" clean "*) [[ $args =~ \ -[a-zA-Z]*f|\ --force ]] && block "git clean -f" ;;
    *" stash "*)
      # Every worktree shares one stash stack: push/pop/drop/clear can take or lose another session's entry.
      [[ $args =~ \ stash\ (list|show|apply|create|branch)\  ]] ||
        block "git stash" "uses the stash stack every worktree shares. Set work aside with 'git commit -am wip', undo later with 'git reset --soft HEAD~1'" ;;
    *" checkout "*)
      # -f alone or combined (-qf), "." or "-- <path>": each overwrites edited files.
      # The "." of "git -C . checkout" is a directory, not a pathspec.
      a=${args// -C . / }
      [[ $a =~ \ (-[[:alpha:]]*f[[:alpha:]]*|--force|\.)\  || $a =~ \ --\ [^\ ] ]] &&
        block "git checkout -f / . / -- <path>" "overwrites edited files. To put back your committed version of one file, run 'git show HEAD:<file> > <file>'; to keep your edits, first 'git commit -am wip', undo later with 'git reset --soft HEAD~1'"
      # "<ref> <path>" overwrites like "-- <path>": two operands mean a path. -b, -B and
      # --orphan take the start point as their second operand, and git refuses paths with them.
      read -ra w <<<"${a#* checkout }"
      n=0 skip=0
      for t in "${w[@]}"; do
        ((skip)) && { skip=0; continue; }
        case $t in
          -b|-B|--orphan|--) break ;;
          *[\<\>]) skip=1 ;;  # redirect operator: its target follows
          -*|*[\<\>]*) ;;
          *) ((++n)) ;;
        esac
      done
      ((n >= 2)) && block "git checkout <ref> <path>" "overwrites the file in your worktree. To take a file from another commit, run 'git show <ref>:<file> > <file>' (delete the file when <ref> lacks it)" ;;
    *" rm "*)
      # -f removes files with local edits, edits included; --cached leaves the worktree alone, -n removes nothing.
      [[ $args =~ \ (-[[:alpha:]]*f[[:alpha:]]*|--force)\  && ! $args =~ \ (--cached|--dry-run|-[[:alpha:]]*n[[:alpha:]]*)\  ]] &&
        block "git rm -f" ;;
    *" switch "*)
      [[ $args =~ \ (-[[:alpha:]]*f[[:alpha:]]*|--force|--discard-changes)\  ]] && block "git switch --discard-changes" ;;
    *" restore "*)
      # --staged (-S) alone only unstages; anything touching the worktree (-W) discards edits.
      [[ $args =~ \ (--staged|-[[:alpha:]]*S[[:alpha:]]*)\  && ! $args =~ \ (--worktree|-[[:alpha:]]*W[[:alpha:]]*)\  ]] ||
        block "git restore" "overwrites edited files. To put back your committed version of one file, run 'git show HEAD:<file> > <file>'; to keep your edits, first 'git commit -am wip', undo later with 'git reset --soft HEAD~1'" ;;
    *" branch "*)
      # -D, or -d with -f, deletes an unmerged branch and its reflog; -d alone refuses to, squash merges included.
      [[ $args =~ \ -[[:alpha:]]*D || ($args =~ \ (--delete|-[[:alpha:]]*d) && $args =~ \ (--force|-[[:alpha:]]*f)) ]] &&
        ! lossless "$args" && {
          # The quote stripping and the split on ` and ( above lose the expansion; $unquoted keeps it.
          re=$' branch [^;&|\n]*[$`]'
          [[ $unquoted =~ $re ]] &&
            block "git branch -D" "names a branch through \$ or a backtick, which the hook can't expand to check. Pass branch names literally"
          block "git branch -D" "deletes commits that are on no other ref and not merged into the default branch, maybe another agent's. Push the branch or merge it first; the hook checks before the command runs, so a merge earlier in the same command doesn't count. Once merged, delete it with 'git branch -d'"
        } ;;
    *" worktree remove "*)
      # Without --force git refuses a worktree with changes; with it, they go, even another agent's.
      [[ $args =~ \ (-f+|--force)\  ]] &&
        block "git worktree remove --force" "deletes the worktree's uncommitted changes, and it may be another agent's. When it is yours and plain remove refuses, run 'git -C <path> status --short', delete each untracked file, restore each modified one with 'git -C <path> show HEAD:<file> > <path>/<file>', then remove it without --force" ;;
    *" worktree prune "*)
      # Prunes every registration whose directory this process can't see: other agents' worktrees too.
      [[ $args =~ \ (-n|--dry-run)\  ]] || block "git worktree prune" "drops other agents' worktree registrations. Remove your own with 'git worktree remove <path>'" ;;
    *" push "*)
      # -f (alone or in -uf), --force, --force-with-lease, --mirror or a +refspec can overwrite pushed
      # commits. A lease only spares commits it hasn't fetched; a fast-forward needs no flag.
      [[ " ${args#* push }" =~ \ (-[[:alpha:]]*f[[:alpha:]]*|--force[^\ ]*|--mirror|\+[^\ ]*)\  ]] &&
        block "git push --force" "can overwrite pushed commits. Push without it; if the remote rejects the push, fetch and rebase or merge" ;;
  esac
done < <(tr ';&|()`' '\n\n\n\n\n\n' <<<"$cmd")
exit 0
