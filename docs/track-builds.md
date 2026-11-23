# Building in tracks

A **track** is a part of a build that one agent can finish against a fixed contract (backend and viewer, say); a build that doesn't split is one track. Each track agent edits files, so the Subagents rules in `~/.claude/rules/global.md` and `~/.claude/docs/subagents.md` apply: its own scratch branch and worktree, integrated one branch at a time. A batch of tickets runs the same way, one ticket or group per track.

1. Settle the design and the contract between tracks yourself (an API shape, a schema, the names each track adds). For a bug, the settled design is a red command that reproduces it, and the seams are the bug's. A design call you can't settle in a brief keeps the build inline. A change that suppresses or skips something (a filter, an exemption, a quoted-text rule) puts in its contract the signals it must keep: for each shape it suppresses, a real failure printed next to that shape, as a case that must still flag. Before writing the contract, name how the rule could swallow a real failure.
2. Split by file: seams or tickets that touch the same file, test helper or fake go to one agent, or run one after another, the next starting from the integrated branch. A brief that would have to warn "another agent is editing this directory" marks a split to redo.
3. Brief one Sonnet agent (`model: "sonnet"`) per track to call the Skill tool with "tdd", handing it:
   - its seams as items, and the contract;
   - the test files it runs: its own only. Port-bound tests (e2e on fixed ports) run one agent at a time: hand them to one track, or keep them for yourself after integration;
   - for a Cargo build, the shared target dir, job cap and focused tests of `~/.claude/rules/rust.md`, with `<run>` filled in;
   - for a vitest run, the lock of `~/.claude/rules/js.md`, with `<run>` filled in;
   - the wait block, its text copied into the brief (the harness blocks `sleep N; cat`, and Monitor called unloaded fails with InputValidationError):

     > Run any command over 2 min with `run_in_background: true` and wait for the completion
     > notification. Don't poll. To use Monitor, first call ToolSearch with `select:Monitor`;
     > its `timeout_ms` caps at 1800000 (30 min): re-arm it on expiry. Stop every background task you started before handing
     > back, by its task ID with TaskStop; never `pkill`, which also kills other agents' runs. A
     > block you can't clear within 10 minutes (another agent's work, a missing tool) ends your
     > run: hand back your report with the block named. Waiting on a build lock
     > or a `flock` is a queue, not a block.

   - its report: branch, head SHA, its tests' exit status, each conflict tdd stopped on, and each bug it found outside its track.
4. Run at most 6 agents at once, starting the next as a slot frees: more burn the usage limit without finishing sooner. Cargo tracks follow the tighter cap in `~/.claude/rules/rust.md`; read it before planning a Cargo build (it loads by itself only once you touch a Rust file).
5. When an agent stops on a conflict, ask the user, then resume it with SendMessage, carrying the answer. Once you've read an agent's report, stop it with TaskStop, and stop your own watchers for it; each of your own wait loops has a `timeout` too.

   While agents run, keep a heartbeat: a recurring CronCreate job every 20 minutes (load it with ToolSearch `select:CronCreate`), deleted with CronDelete once the last agent reports. A chain of background `sleep`s dies when one wake lands inside a usage limit; a recurring job fires again after the limit resets. On each wake, check every running agent's transcript (`~/.claude/projects/<project>/<session id>/subagents/agent-*.jsonl`): one unchanged for 10 minutes is hung. Read its last lines, then SendMessage it the way out, or TaskStop it and dispatch the track again with the block in its brief.
6. Integrate the branches, then run the full check once yourself: every test suite and linter the repo has.
7. File each bug the agents found outside the build's scope as an issue (`~/.claude/docs/issue-tracker.md`), a sub-issue of the build's ticket or spec when it has one, and link each from the PR body.
