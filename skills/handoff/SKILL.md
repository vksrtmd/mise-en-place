---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. In a git repo, save it to `$(git rev-parse --path-format=absolute --git-common-dir)/handoff-<slug>.md` and give the user that absolute path: it outlives a session whose temporary directory is discarded on exit, and git never commits it. Outside a git repo, save to the temporary directory of the user's OS (`$TMPDIR`, else `/tmp`; `%TEMP%` on Windows), not the current workspace.

Include a "suggested skills" section in the document, naming which skills the next agent should call the Skill tool for.

Reference content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs) by path or URL.

Redact sensitive information: secrets (API keys, passwords, tokens) and personally identifiable information.

Treat the user's arguments as what the next session will focus on, and tailor the doc to it.
