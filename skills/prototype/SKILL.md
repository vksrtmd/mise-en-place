---
name: prototype
description: Build a throwaway prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like.
---

# Prototype

A prototype is throwaway code that answers one question. Write the question in one line at the top of the prototype, where the user will see it, so the answer can be checked against it later.

## Pick the shape

The question picks it. When it is ambiguous and the user isn't around, take the shape the surrounding code suggests (a backend module → logic, a page or component → UI) and state that assumption beside the question.

### Logic: "does this state model feel right?"

One self-contained HTML file with inline CSS and JS, opened by double-click, so it can be handed to a non-developer: no framework, bundler or server.

- The logic lives in one pure module that never touches the DOM. The page is a thin shell calling into it, so the validated module lifts into the real code.
- Labels and state read in domain language, the way the business says them.
- Top to bottom: the question; the current state as labelled fields, re-rendered after every action with the change called out; one free-play button per action; tabbed guided walkthroughs, one per scenario (the happy path, a tricky edge case, an attempt at something that should be illegal), each a plain-language description over the ordered buttons to press, starting from a reset state.

### UI: "what should this look like?"

Three variants (five at most) that disagree on structure: layout, information hierarchy, primary affordance. Two variants that differ only in colour or copy count as one; redraw one of them.

- Mount the variants in the existing page that would host the feature, behind a `?variant=` search param, keeping its data fetching, auth and surrounding chrome so each variant is judged at real density. Only for a surface with no plausible host page, add a throwaway route that follows the project's routing convention and has `prototype` in its name.
- Each variant uses the project's component library and owns its layout.
- One shared floating switcher, styled apart from the design: ← and → buttons and arrow keys (ignored while a field has focus) cycle the variants, a label names the current one, the router updates `?variant=` so a variant survives reload, and it renders only outside production builds.
- A variant that mutates calls a stub.

## Build rules

- Write it without tests, polish or abstractions, with only the error handling that keeps it running (it sits outside the test-first loop).
- Keep state in memory. When the question is about persistence, use a scratch DB or file named `PROTOTYPE-wipe-me`.
- Put it next to the code it is for, named so a reader sees it is a prototype.

## Hand over and capture

Hand over the file, or the URL with its variant keys. The feedback worth having sounds like "that shouldn't be possible" or "the header from B with the sidebar from C"; add the actions, scenarios or variants it asks for.

Once the question is answered:

1. Commit the whole prototype, every variant included, to a throwaway branch kept out of main: it stays as a primary source.
2. Record the verdict, the question it settled and that branch's name on the implementation issue when there is one, otherwise in the commit message.
3. Fold the decision into the real code: the validated logic module lifts into its real module; the winning variant is rewritten to production standard in its host page, or promoted to a real route when it had none, and the other variants, the switcher and any throwaway route go.
