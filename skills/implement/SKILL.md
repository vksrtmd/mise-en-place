---
name: implement
description: "Implement a ticket or the agreed plan inline, or a parent issue or group of tickets with subagents."
disable-model-invocation: true
---

Build the work the user names. When the user names one issue, fetch it and its sub-issues first.

- One ticket, an issue with no open sub-issues, or the plan agreed in this conversation: follow the steps below.
- Several tickets (a parent issue with open sub-issues, a list of ticket refs, or a description of a group of a parent's tickets such as `only the backend`): follow [batch.md](batch.md) instead of the steps below.

1. When the user passes an issue or ticket reference, fetch it from the issue tracker, including its open/closed state; when it could match more than one ticket, ask which. State its title and state, and stop when it is closed.
2. Build it, calling the Skill tool with "tdd" at the seams the work's spec or ticket agreed, when it names any. Typecheck and run the test file you touched after each change. When the work asks you to check or measure something, write the result beside that item in its issue (in the PR body, for a plan with no issue), so its reviewers see it. When tdd stops on a conflict, ask the user, then resume it with the answer. Done when every acceptance criterion is met, and the typecheck and the full test suite pass.
3. Commit to the current branch.
4. Call the Skill tool with "code-review", with the commit the branch started from as the fixed point (usually `origin/<default branch>`). It reviews `git diff <ref>...HEAD`, so it sees only committed work.
5. Commit any fixes the review leads to on top.
6. File each bug you found outside the work's scope as an issue, a sub-issue of the ticket's parent (a plain issue when it has none), so it outlives the PR.
7. Push the branch and open a pull request, calling the Skill tool with "pr" to write its title and body, which links each issue step 6 filed. When the current branch is the default branch, stop after step 6 and tell the user. With no remote (`git remote` prints nothing), stop after step 6 and tell the user the branch is ready to merge.
