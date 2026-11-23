# Out-of-Scope Knowledge Base

`.out-of-scope/` records rejected enhancement requests, so a repeat request gets the earlier decision surfaced instead of re-litigated. One file per **concept**, not per issue, with a kebab-case name recognizable without opening it (`dark-mode.md`).

## File format

```markdown
# Dark Mode

This project does not support dark mode or user-facing theming.

## Why this is out of scope

The rendering pipeline assumes a single palette defined in `ThemeConfig`;
theming would need a theme context, theme-aware styles and stored preferences,
which doesn't fit the project's focus on content authoring.

## Prior requests

- #42: "Add dark mode support"
- #87: "Night theme for accessibility"
```

Write the reason as something substantive and durable: project scope, a technical constraint or a strategic decision. "Too busy right now" is a deferral, not a rejection.

## Check (step 1)

Read every file and match by concept, not keyword ("night theme" matches `dark-mode.md`). On a match, tell the maintainer which file matches and why it was rejected, and ask whether that still holds:

- **Confirm**: add the issue to the file's Prior requests, then close it.
- **Reconsider**: update or delete the file; the issue proceeds through normal triage. Old issues stay closed.
- **Related but distinct**: proceed with normal triage.

## Write (step 5, rejected enhancement)

1. Append the issue to a matching file's Prior requests, or create a file with the concept as the heading, a one-line decision, the reason and the first prior request.
2. Comment on the issue explaining the decision and naming the file.
3. Close it with the `wontfix` label.
