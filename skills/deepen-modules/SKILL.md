---
name: deepen-modules
description: Scan a codebase for deepening opportunities, present them in your reply, then route each pick to /to-tickets.
disable-model-invocation: true
---

Surface architectural friction and propose **deepening opportunities**: refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

Use the terms below exactly and, when the repo has a glossary, its terms for the domain: if it defines "Order," talk about "the Order intake module."

## Vocabulary

- **Module**: anything with an interface and an implementation, at any scale: a function, class, package, or tier-spanning slice.
- **Interface**: everything a caller must know to use the module correctly: the type signature plus invariants, ordering constraints, error modes, required configuration, and performance characteristics.
- **Depth**: leverage at the interface, the behaviour a caller (or test) can exercise per unit of interface they learn. **Deep**: much behaviour behind a small interface. **Shallow**: the interface is nearly as complex as the implementation. Deepen by cutting methods, simplifying parameters, and hiding more inside.
- **Seam** _(Michael Feathers)_: a place where you can alter behaviour without editing in that place; the location where a module's interface lives. Say **seam** where others say "boundary". A deep module's **internal seams** serve its own tests; only its **external seam** is exposed.
- **Adapter**: a concrete thing that satisfies an interface at a seam. One adapter means a hypothetical seam; two adapters (typically production and test) mean a real one. Propose a port only for a real seam.
- **Leverage**: what callers get from depth: one implementation pays back across N call sites and M tests.
- **Locality**: what maintainers get from depth: change, bugs, knowledge, and verification concentrate in one place.

**The interface is the test surface**: callers and tests cross the same seam, and wanting to test past the interface means the module is the wrong shape. Once tests exist at a deepened module's interface, the old unit tests on the shallow modules it absorbed are deleted.

**Dependency categories** decide how a deepened module is tested across its seam:

1. **In-process**: pure computation, in-memory state, no I/O. Merge the modules and test through the new interface directly.
2. **Local-substitutable**: the dependency has a local stand-in (PGLite for Postgres, an in-memory filesystem). Test with the stand-in in the suite; the seam stays internal. Without a stand-in, the dependency falls under 3 or 4.
3. **Ports & adapters** (remote but owned): your own services across a network. Define a port at the seam; the module owns the logic and takes the transport as an adapter: in-memory for tests, HTTP/gRPC/queue in production.
4. **Mock** (true external): third-party services (Stripe, Twilio). The module takes the service as an injected port; tests supply a mock adapter.

## Process

### 1. Explore

**Scope before you scan: YAGNI.** Deepening pays off by easing future changes, so weight recently changed code. Decide *where* to look first:

- If the user named a direction (a module, a subsystem, a pain point), take it.
- Otherwise, list the files changed most often in the last three months, `git log --since=3.months --name-only --format= | sort | uniq -c | sort -rn | head -30`, and take as hot spots the first 10 hand-written files in it (30 leaves room to pass over lockfiles and build output such as `dist/`). When fewer than 10 of them changed more than twice, rerun with `--since=1.year`; when that lists nothing (no commits, a shallow clone), take the repo's top-level modules.

When the repo has `GLOSSARY.md` (or `GLOSSARY-MAP.md`) or `docs/adr/`, read the glossary and the ADRs in the area first: the glossary names good seams, and ADRs record decisions this survey leaves settled.

Then spawn a sub-agent with a fresh context window. Brief it with:

- the hot spots or the named direction;
- the whole Vocabulary section, dependency categories included;
- the glossary terms and the ADR decisions in the area, when you read any;
- the friction questions and the deletion test below;
- the handback: candidates, each with its files, the friction and the deletion-test result; then, apart from the candidates, one line per bug, security hole or slow path it trips over.

The sub-agent explores by _friction_. Give it these questions:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow**, with an interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

It applies the **deletion test** to anything it suspects is shallow: would deleting it concentrate complexity, or just move it? A "yes, concentrates" is the signal you want.

The step is done when every hot spot (or the named direction) has been walked.

Keep the survey on structure. Each bug, security hole or slow path in the handback gets one line in your reply, pointing at `/audit-repo`.

### 2. Present candidates

Write the candidates in your reply, one block per candidate, most promising first:

- **Title**: names the deepening ("Collapse the Order intake pipeline").
- **Strength**: `Strong`, `Worth exploring` or `Speculative`, plus the dependency category (`in-process`, `local-substitutable`, `ports & adapters`, `mock`, per Vocabulary).
- **Files**: the paths, as code.
- **Problem**: one sentence. What hurts.
- **Solution**: one sentence. What changes.
- **Wins**: one bullet per gain, six words or fewer, in the Vocabulary's terms ("locality: bugs concentrate in one module", "leverage: one interface, N call sites").

Add a small before/after diagram in a code block where the shape change needs a picture. End with the **top recommendation**: which candidate first, and why, in one sentence.

**ADR conflicts**: surface a candidate that contradicts an existing ADR only when the friction warrants revisiting it, and mark it in the block (e.g. _"contradicts ADR-0007, but worth reopening because…"_).

Stop at candidates: the deepened module's interface is designed later, in the spec or ticket.

### 3. Route the picks

Ask the user which candidates to take further. Each pick goes to `/to-tickets`, which decides whether a spec comes first.

When the user rejects a candidate for a reason a future review would need to avoid re-suggesting it, offer to record it as an ADR (call the Skill tool with "domain-modeling"). Record only reasons that outlast the moment: a constraint, or a trade-off that was decided.

The step is done when every pick is routed to `/to-tickets`, or the user has dropped the pick.
