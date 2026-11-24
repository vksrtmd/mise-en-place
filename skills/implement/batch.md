# Batch

Land the run's tickets on one **integration branch**, with every ticket resolved the way the issue tracker closes work.

The **parent** is the issue whose sub-issues the tickets are (a spec, or any issue), when they all share one. The user names the run by its parent or by a list of ticket refs; a run with no parent has the parentless branches below.

When the user names a **subset** of the parent's tickets, the run's tickets are that subset; every other ticket of the parent is **left out**. When the user names a parent without a subset, the run's tickets are all the parent's open tickets. A subset is named by ticket refs or by a description of the work (`only the backend`); for a description, pick the open tickets whose titles and bodies match it, and confirm the list with the user before step 1. Listed refs that don't all share one parent are the run's tickets, with none left out. A listed ref that is closed drops out of the run: name it to the user. When no ticket remains in the run (every listed ref closed, or no open ticket matches the description), stop and tell the user.

You orchestrate: you read the graph and dispatch subagents, who write the code.

The tickets form a **task graph**: blocking edges decide what can start. The **frontier** is every unstarted ticket whose blockers have all merged into the integration branch, unless it waits on a human ticket. Track merges yourself, because a tracker's blocked-by count drops only when a blocker closes, at the end of the run.

The run uses a **draft PR**, marked as closing the parent (when there is one) and its tickets, when the tracker closes work through PRs or the user asked for one.

A **human ticket** is one labelled `ready-for-human`. Its implementer only prepares what the human acts on (a script, a doc, a config change), and it is never done: the human still has to act. A ticket it blocks that needs the human's step **waits on** it, and so does every ticket a waiting ticket blocks.

## Steps

When the notes dir already holds `RUN-STATE.md` (a resumed or restarted run), read it first and continue from the step it records, with its agents and frontier.

1. Read the parent (when there is one) and every ticket of the run and write down the graph. A blocker outside the run must already be closed; when one is open, ask the user whether to add it to the run. When two tickets that can run at once touch one shared file (a message catalogue, a config registry, a shared type), add a blocking edge between them, or pin the exact names each one adds, for both implementers' prompts. Done when every ticket has its blockers listed, every blocker is in the run or closed, and every pair that can run at once and shares a file has an edge or pinned names.
2. When the tickets need exploration (code to locate, external docs), run one exploration subagent (`general-purpose`: an `Explore` agent can't write files) that saves markdown notes to the **notes dir**, `$(git rev-parse --path-format=absolute --git-common-dir)/<run>-notes/`, for every later prompt to point at; `<run>` is the integration branch's name with each `/` as `-`. Its brief carries the wait block of the Implementer template. The notes dir sits in the repo's git dir, so it outlives a container restart and git never commits it. The notes hold each ticket's body, and a section per ticket naming the files and docs that ticket needs. Done when the notes cover every file and external doc the tickets name, and every ticket has its section.
3. Create the integration branch from `<remote>/<default branch>` with `--no-track`, in its own worktree. With no remote (`git remote` prints nothing), create it from the local default branch, read `<remote>/<default branch>` as the local default branch in every later step, drop the merger's pull and push clauses and the report of what the pull brought in, and open no PR. Put every worktree of this run where the user's instructions place worktrees, else beside the repo. Find the **full check**: the command the repo's `AGENTS.md` / `CLAUDE.md` or CI runs over everything; when neither names one, ask the user. When it runs a suite on fixed ports (e2e), the implementer's `<command>` leaves that suite out and the merger's, run one at a time, keeps it: drop the merger's same-tree skip. Write `RUN-STATE.md` in the notes dir, creating the dir when step 2 didn't run: the integration branch and worktree, the full check, the graph, and each ticket's state (agent ID, branch, merged SHA, send-backs used). Done when the integration worktree exists, you hold the full check's command, and `RUN-STATE.md` exists.
4. Start an implementer in the background for each frontier ticket, up to the caps of `~/.claude/docs/track-builds.md` step 4, record its agent ID and branch in `RUN-STATE.md`, and keep track-builds' step 5 heartbeat while any agent runs. Done when every frontier ticket has an implementer or waits for a slot.
5. Handle each report by the Retries rules, which send a branch back, stop it, or pass it to a merger. Run mergers one at a time, and open any draft PR after the first merge. After each merge, update `RUN-STATE.md`. Each merge, the end of step 6 and the start of step 8 are boundaries for the Context rule of `~/.claude/rules/global.md` (Long runs): check it there and suggest `/compact` when it says to. Recompute the frontier and return to step 4. Done when every ticket has merged, is stopped, or waits on a human ticket.
6. Review the integration branch:
   - From the integration worktree, call the Skill tool with `code-review`, passing `<remote>/<default branch>` as the fixed point, the parent ref (the run's ticket refs when there is no parent), and as settled each commit a merger pulled in, as pushed by a human, each waiting, stopped or left-out ticket, as left out of this run, and each patch, as pushed by the user later. Keep the review's `## Notes` for step 8's report.
   - When the review reports findings, hand them to one fix-round implementer.
   - Run a merger on the fix round's branch, then verify each fix by re-reading the code the finding cites at the merge SHA and running any test the fix added. That ends the review.

   Done when every finding is fixed, or kept for step 8's report with the reason it stands.
7. Remove every implementer worktree. From the integration worktree, run `git branch -d` on the branch of every implementer whose work merged: `-d` checks the branch is merged into that worktree's `HEAD`. Keep each stopped ticket's branch for step 8's report.
8. Close the run. A ticket is **done** when it merged with no undone work noted, is not a human ticket, and has no patch left for the user to push. The parent is done when every ticket of the parent is done or already closed; a run with no parent has nothing to close here.
   - File each bug an implementer or the review found outside the run's scope as an issue, a sub-issue of the parent (a plain issue when there is none), and link each from any draft PR.
   - When a draft PR exists, keep its closing marks only on done tickets, and on the parent only when there is one and it is done, then mark it ready for review.
   - When the tracker closes work other than through PRs, resolve each done ticket, and the parent when there is one and it is done, the way the tracker closes work.
   - Report:
     - the integration branch;
     - each ticket stopped on a red check, with its branch and the tickets it blocks;
     - each human ticket as awaiting the human, with its human step and the tickets that wait on it;
     - each patch for the user to push, with its path and the branch it goes on;
     - the undone work noted;
     - the review's notes;
     - each finding left standing, with its reason;
     - each bug filed, with its issue.

## Subagents

### Model

Start every subagent fresh, not as a fork: a fork inherits your context and ignores `model`.

Pass `model` on every Agent call you dispatch from these steps (`code-review` picks its own reviewers'):

- `"opus"` for an implementer whose ticket's main work changes a **trust boundary** (network topology, TLS, credentials, auth, permissions, sandboxing), and for the fix round when a finding touches a trust boundary;
- `"sonnet"` for every other implementer, the merger and the exploration subagent. When a sonnet implementer's ticket touches a trust boundary only in passing (one check, one guard), its warning is: `The <check> at <place> is a trust boundary: when its input is missing or malformed, it denies.`

### Retries

A report is **green** when the full check exited 0, else **red**. Send each implementer back at most once, with SendMessage to the same agent carrying the check output or the new tip, on the first of:

- it reports red or names undone work;
- its merger reports red and the integration tip it reports is not an ancestor of the implementer's head SHA (`git merge-base --is-ancestor <tip> <head>` fails): it goes back to merge the new tip.

A merger red only in tests its ticket added (each failing test the merger names is in `git diff <integration tip>...<head SHA>`), which passed in the implementer's green check (a race the merge exposed), sends the implementer back once more without asking the user, even after its one send-back; a second such red stops the ticket.

An implementer report that names a conflict tdd stopped on goes to the user first: ask, then SendMessage the answer to the same agent; it keeps its one send-back. Every other red report stops the ticket; keep its check output for the report. A merger whose pull or push fails stops all merging: show the user its output, wait for them, then rerun the step that failed. An implementer already sent back goes to a merger on green, with any undone work noted. A stopped ticket stops every ticket it blocks. These rules cover the fix round of step 6 too.

### Prompts

Send each implementer and merger its template, filling the `<slots>`:

- Add only what is specific to the ticket: a warning, a shared name to use.
- When the ticket changes files the session hands to the user to push (a patch, as for `.github/workflows/` under a token that can't push them), the warning is: `Put <those files> in a patch in the directory $(git rev-parse --path-format=absolute --git-common-dir), where git never commits it and it outlives your worktree. Its file name carries <integration branch>, the branch the user pushes it to, not <branch>. Report its path as the patch, apart from undone work.`
- For a human ticket, the warning is: `Prepare only <what the human acts on>. Report the step left to the human as the human step, apart from undone work.`
- `<items>` is what a test can show among the ticket's acceptance criteria, each behaviour its "What to build" states, and each decision of the parent it links to, or `none`; for a human ticket, only those the prepared work meets before the human acts.
- For a Cargo or vitest build, the implementer's warning and the merger's prompt carry the shared target dir, job cap and focused tests of `~/.claude/rules/rust.md` (Cargo) or the vitest lock of `~/.claude/rules/js.md`, with `<run>` filled in.
- Keep the `Notes:` sentence only when step 2 ran, naming the ticket's section, each attribution clause only when the session gives a trailer, and the merger's push clause only when the run uses a draft PR.
- For the fix round, the first sentence becomes `Fix these code-review findings: <findings>. Reproduce each one marked unverified first; one that does not reproduce stays unfixed, with its output as the reason.`, and `<items>` is the findings a test can show.

Implementer:

```
Implement <ticket ref> of <parent ref> (drop this clause when there is no parent). Notes: <notes dir>; start from <ticket section>, which holds the ticket body, and open other notes only where it points. <ticket-specific warning, if any>
Items a test can show: <items>
Run any command over 2 min with `run_in_background: true` and wait for the completion notification. Don't poll. To use Monitor, first call ToolSearch with `select:Monitor`; its `timeout_ms` caps at 1800000 (30 min): re-arm it on expiry. Stop every background task you started, a server included, before handing back, by its task ID with TaskStop; never `pkill`, or `kill` on what a `pgrep -f` pattern matches: either can hit other agents' runs and your own shell. A block you can't clear within 10 minutes (another agent's work, a missing tool) ends your run: hand back your report with the block named. Waiting on a build lock or a `flock` is a queue, not a block.

1. Run `git worktree add <worktree path> -b <branch> <integration branch>` and work there.
2. When there are items, call the Skill tool with `tdd`, passing it those items. Build the rest directly. Write docs that state how the code behaves (ADR, README) last, once the tests showing that behaviour pass. Leave the rules in standards docs as they are: when the work needs one changed, report it as a decision instead.
3. Commit the work, ending each commit message with: <attribution trailer>
4. Merge the <integration branch> tip into <branch> and run the full check (<command>). Done when it exits 0, or you can name why it stays red. The orchestrator merges and opens any PR.
5. Report: branch, head SHA, the full check's exit status and last line verbatim, anything the work left undone, each rule it needs changed, each finding left unfixed with its reason, each conflict tdd stopped on, each bug found outside the ticket's scope, and the human step or patch when told to report one.
```

Merger:

```
In <integration worktree>, when `git ls-remote --exit-code --heads <remote> <integration branch>` succeeds, run `git pull --ff-only <remote> <integration branch>` first: a human may have pushed to it. When the pull fails, stop and report its output.
Then run `git merge --no-ff --no-commit <branch>`, resolving conflicts so both sides' tickets still hold. `--no-commit` skips the post-merge hook: when the merge changes a dependency lockfile, run the install for it (the one the hook or the repo's docs run) before the check.
When `git write-tree` prints the same hash as `git rev-parse <head SHA>^{tree}`, the implementer's green check already covers this tree: skip the check. Otherwise run the full check (<command>) on the result. When it exits 0 or was skipped, commit, ending the message with: <attribution trailer>, then push <integration branch>; when its output contains `[remote rejected]`, push once more; when a push still fails, stop and report its output. Otherwise run `git merge --abort`.
Run any command over 2 min with `run_in_background: true` and wait for the completion notification. Don't poll. To use Monitor, first call ToolSearch with `select:Monitor`; its `timeout_ms` caps at 1800000 (30 min): re-arm it on expiry. Stop every background task you started, a server included, before handing back, by its task ID with TaskStop; never `pkill`, or `kill` on what a `pgrep -f` pattern matches: either can hit other agents' runs and your own shell. A block you can't clear within 10 minutes (another agent's work, a missing tool) ends your run: hand back your report with the block named. Waiting on a build lock or a `flock` is a queue, not a block.
Report: the commits the pull brought in, the integration tip after the pull, the merge SHA when you committed, each conflict and how you resolved it, and the full check's exit status and last line verbatim, with each failing test's name, or `skipped: same tree as <head SHA>`.
```
