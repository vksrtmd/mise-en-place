#!/usr/bin/env bash
input=$(cat)
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')
model=$(echo "$input" | jq -r '.model.display_name // empty')
effort=$(echo "$input" | jq -r '.effort.level // empty')

branch=""
if [ -n "$cwd" ] && [ -d "$cwd" ]; then
  branch=$(git --no-optional-locks -C "$cwd" symbolic-ref --short -q HEAD 2>/dev/null \
    || git --no-optional-locks -C "$cwd" rev-parse --short HEAD 2>/dev/null)
fi

# Tokens spent this session: input + output + cache writes (cache reads excluded, they re-count
# context). Summed over the transcript, last usage per message id wins (streaming repeats an id
# with growing output). ctx is the context the last message carried (input + cache reads +
# cache writes): unlike the spend, it drops after compaction. The scan is cached by transcript
# size so a refresh with no new messages doesn't re-parse the file.
fmt() { awk -v n="$1" 'BEGIN{ if (n>=1e6) printf "%.1fM", n/1e6; else if (n>=1e3) printf "%.1fk", n/1e3; else printf "%d", n }'; }
tokens=""
transcript=$(echo "$input" | jq -r '.transcript_path // empty')
if [ -n "$transcript" ] && [ -r "$transcript" ]; then
  size=$(stat -c %s "$transcript" 2>/dev/null || stat -f %z "$transcript" 2>/dev/null)
  cache="${TMPDIR:-/tmp}/statusline-spend-$(printf '%s' "$transcript" | cksum | cut -d' ' -f1)"
  if [ "$(cut -d' ' -f1 "$cache" 2>/dev/null)" = "$size" ]; then
    read -r _ t_spent t_ctx < "$cache"
  else
    read -r t_spent t_ctx < <(jq -nr '[inputs | select(.message.usage != null) | {k: (.message.id // .uuid), u: .message.usage}]
      | (.[-1].u // {} | (.input_tokens // 0) + (.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0)) as $ctx
      | group_by(.k) | map(.[-1].u | (.input_tokens // 0) + (.output_tokens // 0) + (.cache_creation_input_tokens // 0))
      | "\(add // 0) \($ctx)"' \
      "$transcript" 2>/dev/null)
    echo "$size ${t_spent:-0} ${t_ctx:-0}" > "$cache" 2>/dev/null
  fi
  if [ "${t_spent:-0}" -gt 0 ]; then
    tokens="ctx $(fmt "${t_ctx:-0}") spent $(fmt "$t_spent")"
  fi
fi

# Order, left to right: time, tokens, model, effort, branch, dir. Each part: "colour|text".
parts=("90|$(date +%H:%M:%S)" "32|$tokens" "36|$model" "33|$effort" "35|$branch" "01;34|$cwd")
colored=""
for p in "${parts[@]}"; do
  text=${p#*|}
  [ -z "$text" ] && continue
  colored+="${colored:+ }"$'\033'"[${p%%|*}m$text"$'\033[00m'
done

printf '%s' "$colored"
exit 0
