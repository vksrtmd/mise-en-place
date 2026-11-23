#!/usr/bin/env bash
# Print when text reached an agent's context: one line per tool call (line number, tool, its path,
# command, skill or pattern), and a MARK line where each marker first appears in each kind of entry the
# agent did not write: the text of a user entry (the prompt, a tool result) or of an attachment (a rule, a
# reminder, a hook's additional context). Per kind, so a rule's heading quoted in a tool result does not
# hide the rule's own arrival. Of a hook_success record only its content counts (a SessionStart hook
# fills it; its command and stdout never reach the model). The first prompt_snapshot holds the system
# prompt the agent had from the start, marked "(from the start)"; later snapshots, deferred_tools_record
# and api-request entries replay it or the whole request, and never count, nor do other hook records
# and top-level bookkeeping entries. Reminders the transcript stores as flags (the date, the output
# style) hold no text to match. Other attachments count with
# all their strings, metadata such as a rule's path included.
# A marker that never appears ends the output as a "never MARK" line.
# Usage: timeline.sh <transcript.jsonl> [marker...]
#   Markers are plain substrings, e.g. a rule's heading: timeline.sh agent-1.jsonl "# Lean code" "# Comments"
#   Exits 2 on a missing transcript.
# Bash 3.2 compatible (macOS). Needs jq.
set -u
[ $# -ge 1 ] && [ -f "$1" ] || { echo "usage: timeline.sh <transcript.jsonl> [marker...]" >&2; exit 2; }
f=$1; shift
# Prefix each marker so jq never parses one starting with - as an option.
set -- "${@/#/x}"

jq -nrR --args '
  # Head and tail: a command names its file at the end, and the extension says which rule fires.
  def short: tostring | gsub("\n"; " ") | if length > 90 then .[:40] + "…" + .[-50:] else . end;
  # The text parts of message content: a string, or blocks whose text or content holds it.
  def texts: if type == "string" then . elif type == "array" then .[] | (.text // .content // empty) | texts else empty end;
  # A path keeps its tail: worktree paths share a long head, and the extension says which rule fires.
  def tail: tostring | if length > 90 then "…" + .[-90:] else . end;
  ($ARGS.positional | map(.[1:])) as $marks
  | reduce (inputs | [input_line_number, (fromjson? // null)]) as [$n, $e] ({seen: [], out: [], snap: false};
      if $e == null then .
      elif $e.type == "attachment" and $e.attachment.type == "prompt_snapshot" then
        if .snap then . else .snap = true
          | ([$e.attachment | .. | strings] | join("\n")) as $raw
          | .out += [ $marks[] | select(. as $m | $raw | contains($m)) | "\($n) MARK \(tojson) in prompt_snapshot entry (from the start)" ]
          | .seen += [ $marks[] | select(. as $m | $raw | contains($m)) | [., "prompt_snapshot"] ]
        end
      elif $e.type == "assistant" then
        .out += [ ($e.message.content // [])
                  | if type == "array" then .[] else empty end
                  | select(.type == "tool_use")
                  | "\($n) \(.name): \(.input | if .file_path then .file_path | tail else (.command // .skill // .pattern // .url // .query // .description // "") | short end)" ]
      elif $e.type == "user" or ($e.type == "attachment"
            and (($e.attachment.type // "" | startswith("hook_") | not) or $e.attachment.type == "hook_additional_context" or $e.attachment.type == "hook_success")
            and $e.attachment.type != "deferred_tools_record") then
        # Decoded text only, so quoted markers match. A user entry has a toolUseResult beside its content,
        # holding the edits of the agent and files it never saw: only .message.content counts.
        ([ if $e.type == "user" then $e.message.content | texts elif $e.attachment.type == "hook_success" then $e.attachment.content // empty | strings else $e.attachment | .. | strings end ] | join("\n")) as $raw
        | reduce ($marks[] | select(. as $m | $raw | contains($m))) as $m (.;
            ($e.attachment.type // $e.type) as $kind
            | if .seen | index([[$m, $kind]]) then . else .seen += [[$m, $kind]] | .out += ["\($n) MARK \($m | tojson) in \($kind) entry"] end)
      else . end)
  | .out[], ($marks - (.seen | map(.[0])) | .[] | "never MARK \(tojson)")
' "$@" < "$f"
