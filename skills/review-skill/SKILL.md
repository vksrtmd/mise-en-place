---
name: review-skill
description: Review a skill against agent-prose, then run the skill on what reading can't settle. Use when the user asks to review a skill, or a change under review edits a SKILL.md or the files it points at.
---

Review the skill the user names (a path, a skill name, or a branch: then every skill its diff changes) in two passes: a **static pass** (reading, plus running the skill's scripts on throwaway cases) that always runs, and a **run pass** only for questions reading can't settle. When the review checks a change you made at the user's request and this pass wasn't handed to you, apply the findings that fix a _bug_, _drift_ or _gap_, then report every finding; the user picks among the rest. Otherwise report first and apply only the fixes the user picks.

## 1. Static pass

When you wrote the change, or the review runs before opening a PR, hand this pass to a fresh subagent, unless it was handed to you. Brief it with only these facts: this file at the branch's copy when the change edits it, the branch, the skill's directory and the incidents the change answers (substep 5). Tell it to run the pass itself and report findings and dropped passages only, as its final message, then take them into the report.

1. Invoke `agent-prose` with the Skill tool, unless its text is in your context; when the change under review edits `agent-prose`, read its files at the branch's copy instead.
2. When reviewing a skill, read every file in it; when reviewing a change, read every file it touches whole and, of the others, the parts the changed text relies on. When the skill is generated from another source (a marker file or the repo's docs say so), review the generated files, but aim each fix at the source, since the next build overwrites the output.
3. Apply every rule in every document `agent-prose` loads to every prose file you read (SKILL.md, docs, script headers); scripts get substep 7. Record each finding as: file:line, the rule by its leading word (_no-op_, _negation_, _sprawl_, _duplication_, _completion criterion_, ...), the quoted text, and the fix. Mark it **open** when only running the skill could decide it: a possible no-op, a description that may fire too rarely or too often.

   Hunt these _red flags_ in particular:
   - a prohibition (`don't`, `never`, `avoid`, `instead of`, a contrast `X, not Y`) with no positive target beside it, or one that could be phrased positively (_negation_);
   - a reason told as an incident (an event with one run's numbers or setting) where the cause it shows would do (_cause_);
   - a name tied to one environment: a repo, a container, a build layout, a host path with no condition the agent can check (_portable_).
4. When reviewing a change, for every passage it deletes, name where it now lives, or call it **dropped**: a finding for the user to confirm.
5. When reviewing a change that answers an incident (a retro candidate, a bug), **replay** that incident against the new text: a case it still lets through is a finding (_gap_).
6. When a file summarizes other skills (a _router skill_, per `agent-prose`), check each summary against the SKILL.md it describes; a claim that skill does not make is a finding (_drift_).
7. Read every script in the skill (when reviewing a change, every script it touches or its changed text relies on) against what its SKILL.md tells the agent about it: arguments, exit codes, output. Wherever the SKILL.md relies on a script's exit code or output, run it on a throwaway case, starting with the repo's tests for it when they exist. A script that does something other than what the SKILL.md relies on is a finding (_bug_), with the command and the output that show it.

The pass is done when every rule has met every prose file read and has findings or is named clean, every deleted passage has a home or is called dropped, every incident the change answers has been replayed, every summary of another skill is checked against it, and every script in scope is checked against what its SKILL.md relies on.

## 2. Run pass

Only for **open** findings. First settle what a transcript already on disk can: how the environment behaves, or how the current version ran, since those sessions loaded it rather than the text under review. Findings about the new text need new sessions; run them only once the user agrees: they spend real tokens.

Each brief asks the agent to return its report as its final message and to write files only for the work product itself; the harness can refuse report files to a subagent, which then routes around the refusal.

Put the workspace outside the skill's directory and out of version control, somewhere the user can open files from.

In Claude Code, [`scripts/timeline.sh`](scripts/timeline.sh) `<transcript> <marker>...` shows when a rule, skill or reminder entered an agent's context. It prints each tool call and, per marker, the line where it first arrived in each kind of entry (the prompt, a tool result, or an attachment such as a rule), so a tool result quoting a rule shows apart from the rule's own arrival. An attachment lands after the whole batch of parallel results: weigh every call in the batch as its cause.

Both kinds of finding compare the version under review against a baseline: the old version when reviewing a change, no skill otherwise. Take the old version as its whole directory, extracted with `git archive <base> <skill dir> | tar -x -C <workspace>` so the files it points at come along.

- **Behaviour** (no-op, wasted steps): apply *Running a skill* from `agent-prose` with one subagent per version per prompt. The Skill tool loads the installed copy, so each brief names one SKILL.md to follow, and only that one: the reviewed copy (the worktree's, for a branch), or the old version's extracted copy. Compare the transcripts (in Claude Code, `~/.claude/projects/<project>/<session id>/subagents/agent-*.jsonl`).
- **Triggering**: write about 20 queries to a JSON file, `[{"query": "...", "should_trigger": true}, ...]`. Half should fire the skill, each phrased the way a different user would ask; the rest are _near misses_ that share the skill's keywords but belong to another skill or to none. Write each per *Running a skill*, with the detail a real user gives: paths, names, a line of backstory. Run [`scripts/trigger.sh`](scripts/trigger.sh) `<skill dir> <queries.json>` on each version's copy, on a machine with a logged-in `claude` CLI and the skills the near misses belong to installed. Where it reports `every run failed`, give the user both commands to run and keep the finding open until they paste the reports.

The run pass is done when each open finding has a verdict backed by its evidence: pass rates, or an excerpt from each version's transcript.

## 3. Report

Static findings in one list, ordered by how far each breaks agent behaviour (_bug_, _duplication_ and _negation_ before _no-op_ and style), each opening with its file:line and marked **applied** when you applied it. Then each **dropped** passage, quoted, in its own list, for the user to confirm. End the static part with one line, `clean: <rules and red flags with no finding>`. Then each open finding with its evidence (pass rates, or a transcript excerpt per version) and a verdict: confirmed, refuted, or still open.

Rewritten text gets the static pass again, on its own diff only: fixes applied after a static pass, and text rewritten while resolving a merge or rebase conflict (`git diff <merge>^1 <merge>` and `git diff <merge>^2 <merge>` show a merge's; `git range-diff` a rebase's).
