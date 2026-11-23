# Writing Agent Briefs

An agent brief is a structured comment posted on an issue when it moves to `ready-for-agent`. It is the contract an AFK agent works from; the original body and discussion are context.

## Principles

### Durability over precision

The issue may sit in `ready-for-agent` for weeks while the codebase changes. Write the brief to survive renames, moves and refactors:

- Describe interfaces, types and behavioral contracts; name the types, function signatures or config shapes to look for or modify.
- Leave out file paths and line numbers; they go stale. Don't assume the current implementation structure will remain.

### Behavioral, not procedural

Describe **what** the system should do; the agent explores the codebase fresh and decides how.

- **Good:** "The `SkillConfig` type should accept an optional `schedule` field of type `CronExpression`"
- **Bad:** "Open src/types/skill.ts and add a schedule field on line 42"
- **Good:** "When a user runs `/triage-tickets` with no arguments, they should see a summary of issues needing attention"
- **Bad:** "Add a switch statement in the main handler function"

### Complete acceptance criteria

Every brief has concrete, independently verifiable criteria.

- **Good:** "Running `gh issue list --label needs-triage` returns issues that have been through initial classification"
- **Bad:** "Triage should work correctly"

### Explicit scope boundaries

State what is out of scope, so the agent doesn't gold-plate or assume adjacent features.

## Template

```markdown
## Agent Brief

**Category:** bug / enhancement
**Summary:** one-line description of what needs to happen

**Current behavior:**
What happens now. For bugs, the broken behavior; for enhancements, the status quo the feature builds on.

**Desired behavior:**
What should happen after the work, with edge cases and error conditions.

**Key interfaces:**
- `TypeName`: what needs to change and why
- `functionName()` return type: what it returns now vs should return
- Config shape: any new configuration options

**Acceptance criteria:**
- [ ] Specific, testable criterion

**Out of scope:**
- Adjacent thing that is separate
```

## Example (bug)

```markdown
## Agent Brief

**Category:** bug
**Summary:** Skill description truncation drops mid-word, producing broken output

**Current behavior:**
When a skill description exceeds 1024 characters, it is truncated at exactly
1024 characters regardless of word boundaries, ending mid-word
(e.g. "Use when the user wants to confi").

**Desired behavior:**
Truncation should break at the last word boundary before 1024 characters
and append "..." to indicate truncation.

**Key interfaces:**
- The `SkillMetadata` type's `description` field: no type change needed,
  but the logic that populates it needs to respect word boundaries
- Any function that reads SKILL.md frontmatter and extracts the description

**Acceptance criteria:**
- [ ] Descriptions under 1024 chars are unchanged
- [ ] Descriptions over 1024 chars are truncated at the last word boundary
      before 1024 chars
- [ ] Truncated descriptions end with "..."
- [ ] The total length including "..." does not exceed 1024 chars

**Out of scope:**
- Changing the 1024 char limit itself
- Multi-line description support
```

