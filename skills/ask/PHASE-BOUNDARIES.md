# Phase boundaries

A **phase** is a chunk of work inside a session: the discussion, the implementation, the QA. A phase ends when you think *"ok, we're done with that"*.

The **phase boundary** is the gap between two phases, and it is the only place this decision belongs. Mid-phase there is no decision to make: continue, or split the work that's left into subagents. Compacting mid-phase makes the agent lose the thread.

## The tree

Work top to bottom at the boundary. The first **yes** wins.

**1. Can you continue in this session?** Two things make the answer yes: the next phase needs this phase as a **primary source**, or enough room is left inside the [smart zone](https://www.aihero.dev/ai-coding-dictionary/smart-zone) (about 150k tokens on current models) for the next phase to fit. Discussion → implementation is the standard yes: the implementation wants the reasoning verbatim, not a summary of it.

**2. Is the context irrelevant to what comes next?** Is everything in this session (the exploration, the decisions, the dead ends) disposable? If so, **`/clear`**; the old session stays resumable.

Clearing a *relevant* context is one-way: the **why** behind what you built is gone, and reading the diff back doesn't return it.

**3. Do you need to hand off?** Hand off only when you are:

- swapping to a **new harness** (Claude → Codex),
- moving to a **new directory** or repo,
- sending the work to a **colleague**,
- or forking a side task you found **mid-phase** without derailing what you're doing.

**4. Can the task be done AFK?** Scoped tightly enough to run with you away from the keyboard? Then send it to a **subagent** and leave this session untouched. Automated review is the standard case: the agent reads the diff and reports, and you aren't needed while it does.

**5. Otherwise, `/compact`.** Relevant context, same harness, same directory, and you need to stay in the loop: this is where the tree lands, and it lands here often. Pass it an instruction (`/compact we're going to QA this area`) so the summary keeps what the next phase needs.

`/compact` sits last because the questions above are cheaper or more precise, and a summary can flatten a decision.

## Primary and secondary sources

Every move except continuing turns a **primary source** (the session as it happened) into a **secondary source** (a summary of it). Primary keeps full information with lots of noise; a summary is lossy with less noise and more room. This is why question 1 comes first.
