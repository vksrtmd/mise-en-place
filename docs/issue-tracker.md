# Issue tracker: GitHub

Every repo tracks issues and specs as GitHub issues in its own GitHub repo, through the `gh` CLI.

## Conventions

- **Create an issue** (what a skill means by "publish to the issue tracker"): `gh issue create --title "..." --body "..."` (heredoc for multi-line bodies).
- **Read an issue** (what a skill means by "fetch the relevant ticket"): `gh issue view <number> --json number,title,body,labels,comments`, one number per call. Read comments through `--json`: off a TTY, `--comments` prints only comments, so nothing when there are none.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with `--label` and `--state` filters.
- **Make an issue a sub-issue of a parent**: `gh issue create --parent <parent> ...`, or `gh issue edit <parent> --add-sub-issue <child>` afterwards (`gh` 2.94+). Older `gh`: `gh api --method POST repos/<owner>/<repo>/issues/<parent>/sub_issues -F sub_issue_id=<child-db-id>` (database id, as in **Blocking** below). Without sub-issues, put `Part of #<parent>` at the top of the child body.
- **Blocking**: GitHub's **native issue dependencies**, the canonical, UI-visible representation. Add an edge with `gh issue create --blocked-by <n>,<n> ...` or `gh issue edit <child> --add-blocked-by <blocker>` (`gh` 2.94+). Older `gh`: `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where `<blocker-db-id>` is the blocker's numeric **database id** (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, _not_ the `#number` or `node_id`). Where dependencies aren't available, fall back to a `Blocked by: #<n>, #<n>` line at the top of the child body. A ticket is unblocked when every blocker is closed.
- **Count open blockers**: `gh api repos/<owner>/<repo>/issues/<n> --jq .issue_dependencies_summary.blocked_by` (open blockers only; 0 means startable). `gh issue view <n> --json blockedBy` also lists closed blockers, so filter it: `--jq '[.blockedBy.nodes[] | select(.state == "OPEN")] | length'`.
- **Comment**: `gh issue comment <number> --body "..."`. **Labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`.
- **Close**: `gh issue comment <number> --body "<explanation>"`, then `gh issue close <number>`. On an already-closed issue, `gh issue close --comment` drops the comment and still exits 0.
- **CI status of a branch or PR**: `gh pr checks <pr>` for a summary (exits 8 while checks are pending) or `gh run list --branch <branch>` for run ids. Wait on a run with this loop, run in the background; it ends when the run completes or a `gh` call fails:

  ```sh
  while s=$(gh run view <run-id> --json status -q .status) && [ "$s" != completed ]; do sleep 30; done; gh run view <run-id> --json conclusion,jobs
  ```

  A `conclusion` of `success` is green; on any other value, read `gh run view <run-id> --log-failed`. An empty `conclusion` means the loop stopped on a failed `gh` call: read its stderr and rerun the loop. `gh pr checks --watch` and `gh run watch <run-id> --exit-status` both exited 1 within seconds on runs still in progress, so wait with the loop.
- **Check a PR still merges**: after pushing a PR and before reporting it, run `gh pr view <n> --json mergeable -q .mergeable`, every 10 seconds for up to a minute while it prints `UNKNOWN` (GitHub computes it lazily). On `CONFLICTING`, `git fetch origin`, merge `origin/<its base branch>` into the branch, resolve, `git push`, and check again.
- **Conflict resolutions**: text a resolution rewrites is a new change; for text under `skills/`, give it the static pass of `~/.claude/skills/review-skill/SKILL.md`, when that exists.
- **Stacked PRs** (a PR whose base is another PR's branch):
  - Before opening one, check the base PR's `mergeable`; on `CONFLICTING`, bring the base up to date first (per **Check a PR still merges**) when it is yours, else ask the user. Tell the user that squash-merging the base will make the stacked PR conflict.
  - When a stacked PR you own shows `CONFLICTING` or its base PR shows `MERGED`, `git fetch origin`, then take the squash commit `S` (`gh pr view <base-pr> --json mergeCommit -q .mergeCommit.oid`) and the base's tip `T` (`--json headRefOid -q .headRefOid`):
    1. When `git merge-tree --write-tree S^ T` prints the same tree as `git rev-parse S^{tree}` (the squash holds exactly the base's work), `git merge -s ours S` in the stacked branch: it records the squash as merged and keeps the stacked work. Otherwise `git merge S` and resolve.
    2. `git merge origin/main` for what landed after the squash, then `git push`.
    3. `gh pr edit <n> --base main`, and check `mergeable` again.

Infer the repo from `git remote -v`; `gh` does this inside a clone, so keep the shell there and give body files by absolute path (`--body-file /tmp/tickets/1.md`). Outside a clone `gh` fails with `fatal: not a git repository`; when you must run there, pass `-R <owner/repo>` to each `gh` call and the full `repos/<owner>/<repo>` path to `gh api`, using the repo you confirmed below.

File issues only into the repo you are working in. In a fork `gh` can default to the upstream parent, so before the first `gh issue create` of a session, from inside the clone, check the target with `gh repo view --json nameWithOwner` and confirm it with the user if it is not their repo.

Before rerunning a batch of `gh issue create` calls that failed partway, run `gh issue list --state all --limit 1000 --json number,title` (it returns 30 by default) and create only the titles it lacks: a blind rerun files duplicates.

## Triage labels

The five triage roles are labels named after the role: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. Before applying any label (a triage role, `wayfinder:*`), create it if the repo lacks it: `gh label create <name>` (`gh label list` shows what exists).

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: an issue labelled `wayfinder:map`, holding the Destination / Notes / Decisions so far / Not yet specified / Out of scope body. `gh issue create --label wayfinder:map`.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (see **Make an issue a sub-issue of a parent**). Where sub-issues aren't enabled, add the child to a task list in the map body and put `Part of #<map>` at the top of the child body. Labels: `wayfinder:<type>` (`research`/`prototype`/`discussion`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: see **Blocking** under Conventions.
- **Frontier query**: list the map's open children (`gh issue list --state open`, scoped to the map's sub-issues / task list), drop any with an open blocker (see **Count open blockers**, or an open issue in the `Blocked by` line) or an assignee; first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me`, the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far.
