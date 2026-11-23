# Correctness lens

Order of importance: correct, safe, holds under load, tested, fast, lean.

## Understand first

- Read the diff, then the code it touches: callers of every changed function, the functions it calls, the tests, the README. Trace the real flow: where data comes in, what is stored, what goes out.
- When a signature, return value or behaviour changes, grep every caller. For each interface the diff changes (an env var, CLI flag, file format, config key), grep the whole repo, CI workflows included, for its consumers.

## Look for

The code in scope is the diff in a review, or the flows an audit traces.

1. **Bug:** wrong result, crash, missed edge case (empty, zero, last item, rounding, time zones), callers that disagree with what a function returns, a fix applied in one caller while the shared function stays broken, the same rule applied differently in two places.
2. **Risk:** security holes (injection, weak randomness, secrets in code, missing checks on input from users), data loss (writes in the wrong order, no transaction), and **hidden failures**:
   - a `catch` that is empty, only logs and carries on, or is broad enough to swallow unrelated errors (name the ones it would hide)
   - a default value, `null` or empty result returned on error, or `?.` skipping an operation that should have failed loudly
   - a fallback the spec does not ask for, above all one to a mock or stub outside tests
   - retries that run out without telling anyone
3. **Scale:** fine for one user, wrong for many: check-then-write races, the same work done by every process, memory or lists that only grow, a query per item, O(n^2) on big input, per-process state that must be shared. Judge against the expected load the repo states (README, deploy config): one person running a script, or many users and processes at once. Say which load you assumed.
4. **Missing test:** risky logic (a branch, a parser, money, security, data writes, a bug fix, an error path, the rejecting side of a validation) with no test that fails when it breaks. Name the one test that would catch the break. Before reporting, confirm no existing test, integration tests included, already covers it.
5. **Speed:** slow paths, and work repeated in a hot loop.
6. **Lean:** code that should not exist or should be smaller.
   - delete: dead code, unused options, flags and config, speculative features
   - reuse: the repo already has this helper (name the path)
   - stdlib / native: the standard library or platform already does it; a dependency doing what a few lines or the platform can do
   - split: one function or class doing several unrelated jobs, so it is hard to read or test. Split by job, each piece a real job, not a helper that only shortens a function.
   - the smells in standards.md

A shortcut marked with a `shortcut:` comment that names its limit is a decision, not a finding, unless the expected load already crosses it.

The lens is done when every item has met all the code in scope, and each item has findings or is named clean.
