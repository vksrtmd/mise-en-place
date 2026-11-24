---
name: discuss
description: Settle a plan or idea with the user as a tree of decisions, deciding what you can and asking only what you can't.
---

If the repo root has a `GLOSSARY.md` or `GLOSSARY-MAP.md`, the repo keeps a domain model: call the Skill tool with "domain-modeling" first.

Map the plan as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled. Each round, settle the whole frontier:

- **Decide it yourself** when one answer is clearly best given what you know. Record the decision and a one-line reason.
- **Ask the user** only for an **unknown** (a fact or preference only they hold: goals, constraints, priorities, taste) or a **close call** (options near enough in trade-offs that the choice is theirs to own, or a one-way door).

When a round has questions for the user, open it with a short list headed "Settled since last round:", one line per decision you made yourself since the user last answered. Then ask the questions all at once, number each and give your recommended answer, and wait for the answers. When your recommendations would leave the frontier empty, end the message with the settled list (the closing list below) written as if they were accepted, so one "yes" answers and confirms. Answers that depart from them or open new decisions continue the session: a new round, or a revised list to confirm.

Recompute the frontier after every round; when you settled the whole round yourself, go straight to the next.

Format the questions like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

For a close call, word the question so "yes" accepts your recommendation; for a multiple-choice one, name the recommended option in the ➡️ line. For an unknown, ask it plainly and put the assumption you'll proceed on in the ➡️ line.

Look up every fact in the environment yourself: directly when it takes a few tool calls, otherwise dispatch a sub-agent with a fresh context window. A running lookup is an unsettled prerequisite: settle the rest of the frontier now, and hold only the decisions downstream of it until the lookup reports.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Then list every settled decision, marking each one you decided yourself with its reason so the user can overturn it, and ask the user to confirm the list. When another skill called discuss, hand it the confirmed list. When the user did, stop once they confirm and ask what comes next: build it (they type `/implement`), write tickets (`/to-tickets`), or stop, with stop the default. Start no build, repo or branch until they pick one.
