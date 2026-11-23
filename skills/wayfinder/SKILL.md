---
name: wayfinder
description: Plan a huge chunk of work (more than one agent session can hold) as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the destination is clear.
disable-model-invocation: true
---

A loose idea has arrived, too big for one agent session, and wrapped in fog: the way from here to the **destination** isn't visible yet. Wayfinding is about finding that way. This skill charts the way as a **shared map** on the repo's issue tracker, then works its **decision tickets** one at a time until the route is clear.

Naming the destination is the first act of charting: it shapes every ticket. It might be a spec to hand off, a decision to lock before planning starts, or a change made in place like a data-structure migration.

## Plan

Wayfinder is **planning** by default: each ticket resolves a decision, and the map is done when the way is clear, with every decision made before someone goes and does the thing. The pull to just do the work is usually the signal you've reached the edge of the map and it's time to hand off. An effort can carry execution into the map itself through its **Notes**; absent that, produce decisions.

## Refer by name

Every map and ticket is an issue with a **name**, its title. In everything the human reads (narration, the map's Decisions-so-far), refer to it by name, with its id and URL riding inside as the link.

## The Map

The map is a single issue on this repo's issue tracker, labelled `wayfinder:map`, the canonical artifact; its tickets are its child issues. It is an **index**: it gists each decision made and links the ticket holding its detail, so each decision lives in one place, its ticket.

The "Wayfinding operations" section of the issue tracker doc says where the map, its child tickets, blocking, and frontier queries live.

### The map body

The whole map at low resolution, loaded once per session. Open tickets are found by query.

```markdown
## Destination

<what reaching the end of this map looks like: the spec, decision, or change this effort is finding its way to. One or two lines; every session orients to it before choosing a ticket.>

## Notes

<domain; skills every session should consult; standing preferences for this effort>

## Decisions so far

<!-- the index: one line per closed ticket, enough to judge relevance, then zoom the link for the detail the ticket holds -->

- [<closed ticket title>](link): <one-line gist of the answer>

## Not yet specified

<!-- see "Fog of war": in-scope fog you can't ticket yet; graduates as the frontier advances -->

## Out of scope

<!-- see "Out of scope": work ruled beyond the destination; closed, never graduates -->
```

### Tickets

Each ticket is a child issue of the map. Its body is the question, sized to one agent session:

```markdown
## Question

<the decision or investigation this ticket resolves>
```

Each ticket carries a `wayfinder:<type>` label, one of `research`, `prototype`, `discussion`, `task` (see [Ticket Types](#ticket-types)). `wayfinder:` labels are the only labels a map and its tickets carry: they mark decisions, which triage labels like `ready-for-agent` don't describe.

A session **claims** a ticket by assigning it to the dev driving the map, **first**, before any work, so concurrent sessions skip it. That assignee _is_ the claim: an open, unassigned ticket is unclaimed.

Blocking uses the tracker's **native** dependency relationship, which renders the frontier _visually_ in the tracker's UI, so the human sees what's takeable without opening the map; only a tracker lacking it falls back to a body convention. A ticket is **unblocked** when every ticket blocking it is closed; the **frontier** is the open, unblocked, unclaimed children, the edge of the known.

The answer is recorded on resolution as a comment (see [Work through the map](#work-through-the-map)). Link assets created while resolving a ticket from the issue.

## Ticket Types

Every ticket is either **HITL** (human in the loop, worked _with_ a human who speaks for themselves) or **AFK**, driven by the agent alone. A HITL ticket resolves once the human has answered every question put to them and confirmed the resolution.

- **Research** (AFK): Reading documentation, third-party APIs, or local resources like knowledge bases to surface a fact a decision waits on. Resolved by calling the Skill tool with "research", which runs it in a background agent. Use when knowledge outside the current working directory is required.
- **Prototype** (HITL): Raise the fidelity of the discussion by making a cheap, rough, concrete artifact to react to (an outline, a rough take, a stub, or UI/logic code) by calling the Skill tool with "prototype". Links the prototype as an asset. Use when "how should it look" or "how should it behave" is the key question.
- **Discussion** (HITL): Conversation. The default case. Always call the Skill tool with "discuss".
- **Task** (HITL or AFK): Manual work that must happen before a _decision_ can be made: nothing to decide, prototype, or research, but the discussion is blocked until it's done. Signing up for a service so its API can be judged, provisioning access, moving data so its shape can be seen. This is the one type that _does_, and it earns its place by unblocking a decision. The agent drives it alone where it can (AFK); otherwise it hands the human a precise checklist (HITL). Resolved when the work is done; the answer records what was done and any resulting facts (credentials location, new URLs, row counts) later tickets depend on.

## Fog of war

The map is _deliberately_ incomplete: chart only what you can see. Beyond the live tickets lies the **fog of war**: decisions and investigations you can tell are coming but can't yet pin down, because they hang on questions still open. Resolving a ticket clears the fog ahead of it, graduating whatever's now specifiable into fresh tickets, until the way to the destination is clear and no tickets remain.

The map's **Not yet specified** section holds that dim view: the suspected question, the area to revisit. Everything there is in scope but not sharp enough to ticket, written as loosely or fully as the view allows; it doubles as a signpost for collaborators.

**Fog or ticket?** The test is whether you can state the question precisely now, _not_ whether you can answer it now.

- **Ticket when** the question is already sharp, even if it's blocked.
- **Not yet specified when** you can't yet phrase it that sharply. Leave the fog coarse: one patch may graduate into several tickets, or none, once the frontier reaches it.

## Out of scope

The destination fixes the scope; work beyond it is **out of scope** and goes in the map's **Out of scope** section. It never graduates: it returns only if the destination is redrawn, as a fresh effort. When an existing ticket turns out to sit past the destination, **close it** and add one line to **Out of scope**: the gist, why it's out of scope, and a link to the closed ticket; Decisions so far records only the route walked.

## Invocation

Work through resolves one ticket per session. Charting resolves only its research tickets, in parallel, and the Charting decisions ticket.

### Chart the map

User invokes with a loose idea.

1. **Name the destination.** Call the Skill tool with "discuss" to pin down what this map is finding its way to: the spec, decision, or change. Propose the destination and put it to the user: it fixes the scope, so it's settled first and settled by them.
2. **Map the frontier.** Discuss again, **breadth-first** this time: fan out across the whole space, surfacing the open decisions and the first steps takeable now. Done when every branch off the destination is a settled decision, a ticket, fog, or out of scope. **If this surfaces no fog** (the way to the destination is already clear, the whole journey small enough for one session), you don't need a map. Stop and ask the user how they'd like to proceed.
3. **Create the map** (label `wayfinder:map`): Destination and Notes filled in, the fog sketched into **Not yet specified**. Record the decisions the charting discussion settled as one closed `wayfinder:discussion` ticket titled "Charting decisions", its resolution comment the confirmed list from `discuss`, and index it in Decisions-so-far.
4. **Create tickets for what the discussion left open** (unknowns and close calls, research, tasks) as child issues of the map, then wire blocking edges in a **second pass** (issues need ids before they can reference each other). Write cross-references in that pass too, with real ids: a placeholder `#<n>` auto-links to an unrelated issue. Wiring sorts them into the frontier and the blocked.
5. **Run the research.** For each `research` ticket you just created, **claim it** (see [Tickets](#tickets)), then call the Skill tool with "research", naming as its save location a throwaway `research/<name>` branch in its own worktree, so the session's checkout stays on its branch: push it and open no PR, since it is never merged. When each reports, put a context pointer to its findings on the ticket, naming the file by the path the research agent reported, as `git show origin/research/<name>:<reported path>`, which resolves without the branch checked out, and resolve the ticket as in Work through steps 5–6.
6. Stop once every research ticket is resolved or, its sources blocked, labelled `ready-for-human` with its research prompt: charting is one session's work.

### Work through the map

User invokes with a map (URL or number). A ticket is **optional**: without one, you pick the next decision.

1. Load the **map** body.
2. Choose the ticket. If the user named one, use it. Otherwise take the first frontier ticket in order. **Claim it** (see [Tickets](#tickets)).
3. **Read the prior research** before resolving or dispatching anything: every closed ticket the ticket's body and comments cite or that Decisions-so-far indexes as bearing on its question, and each research file their context pointers name. Run `git fetch origin` first, since research branches are never merged. When a pointer names only a ticket or a branch, find the file with `git ls-tree -r --name-only origin/research/<name>`; when there is none, say so in every brief. A comment written before the research landed holds stale hypotheses; the file holds the facts.
4. Resolve it as the type its label names (see [Ticket Types](#ticket-types)). Every subagent brief names the research files from step 3 by their exact `git show` paths, so the agent reads the facts itself. **Zoom as needed**: fetch the full body of any other related ticket on demand; call the Skill tool for whichever skills the `## Notes` block names. If in doubt, call the Skill tool with "discuss".
5. Record the resolution. Check it first: post only claims about the code you checked against it. A `discuss` ticket's resolution is its confirmed list; decisions outside that list (made after the user confirmed it) go to the user before posting, even when they answered "your recommendation". Then post the answer as a **resolution comment**, **close** the issue, and **append a context pointer** to the map's Decisions-so-far.
6. Add newly-surfaced tickets (create-then-wire); graduate any fog the answer has made specifiable, clearing each graduated patch from **Not yet specified** so it lives only as its new ticket. If the answer reveals that a ticket (this one or another) sits beyond the destination, **rule it out of scope**. If the decision invalidates other parts of the map, update or delete those tickets.
7. Stop: the session's one ticket is resolved.

Other sessions may be editing the tracker concurrently: the user may run unblocked tickets in parallel.
