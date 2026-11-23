---
name: pr
description: Use when writing or updating a PR title and body.
---

Write the PR from `git diff <default-branch>...HEAD` and its commit list, so it covers every commit, those added after an earlier description included; when updating a PR, rewrite title and body from scratch.

**Title**: imperative mood, at most 60 characters, no trailing period. Name the headline change; when there are several, name what they share (`Rewrite four skills as replace overlays`) and leave the list to the summary.

**Body**: for a _small change_ (one sentence names it, the door is two-way and the blast radius is none or one module, per Risk below), two or three sentences of prose: what changed, why, and the evidence for any claim the reader can't check from the diff. Otherwise, this template.

```markdown
[1–3 sentence summary]

**Risk:** <one-way | two-way> door · <none | one module | several modules | whole repo | outside consumers>[: <one sentence: what a bad merge breaks, or what can't be walked back>]

<details>
<summary>Details</summary>

[per structural change: one sentence, then its visual; omit without one]

**Evidence**

- <behaviour>: before <failing run, output or screenshot>; after <passing run, output or screenshot>

</details>
```

## Summary

The top 1–3 sentences stand alone: a reader who stops there knows what changed and why, in terms of what a user or caller now sees or can do. Several headline changes share a sentence; their list goes in the details. When the repo has a `GLOSSARY.md`, use its terms. Done when it is at most three sentences and names every headline change.

## Risk

- **Door**: a two-way door can be walked back, a one-way door cannot (destructive actions, hard-to-reverse decisions).
- **Blast radius**: the widest scope a bad merge reaches, on the template's scale: layout shift, breakages for consumers, mobile responsiveness, and the like.

The tail after the radius names what can't be walked back for a one-way door, else the worst break for any radius but `none`; a two-way door with radius `none` ends at the radius. Done when the line states door and radius, plus that tail whenever it applies.

## Visuals

Draw a visual only for a structural change, one that moves calls, files, components, states or boundaries; a PR without one gets none. At most two per PR, combined where changes share a shape. Pick the smallest view that makes the point (pseudocode, a call tree, a component tree, a file tree, Mermaid, or the full text of a new block), place it after the one sentence it supports, and keep only the calls, files, props, states and boundaries the reader needs. Done when each structural change is drawn, alone or merged into one of the two.

When the surrounding shape already exists, draw what changes as a `diff` in the shape of the topic, so the reader sees the change in place:

```diff
 submitForm
   createSession
     persistPrompt
+    expandSkillMention
     launchAgent
   navigateToSession
+    subscribeToEvents
```

## Evidence

One line per changed behaviour, holding its before/after pair:

- Screenshots are S-tier: use them when the environment is set up for it and the change is visual.
- Execution output is A-tier: name the test and quote the decisive line of its failing and passing output, or of the console output.
- For a change to docs, skills or prompts: trial runs with the old and new text, a transcript excerpt, or build output.
- When a behaviour couldn't be run, say so and name what would show it.

Done when every changed behaviour has a before/after pair, or a line naming what would show it.

## Linked issue

When the branch name starts with `<n>-`, end the body with `Closes #<n>`, below `</details>` and above any attribution line. Add `Closes #<m>` for each other issue the PR finishes; write `Part of #<m>` for one it only advances.

## After pushing

Before reporting the PR, follow the **Check a PR still merges** bullet of `~/.claude/docs/issue-tracker.md`, when that file exists, and its **Stacked PRs** bullet when the PR's base is another PR's branch.
