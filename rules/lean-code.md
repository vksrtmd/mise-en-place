---
paths:
  - "**/*.{js,jsx,ts,tsx,mjs,cjs,py,go,rs,c,cc,cpp,h,hpp,java,kt,swift,rb,php,cs,scala,lua,sh,bash,zsh,sql}"
---

# Lean code

Code like a lazy senior developer: the best code is the code never written. Solve the whole problem with the least new code.

## Before you write

List every place your change must reach: callers, tests, fixtures, config, exports. Check what your change could break for users: data it would destroy or expose, callers that stop working. That is scope. Extra features are not.

## The smallest complete change

Take the first option that fully works:

1. Does it need to exist? Name the features, options and flexibility nobody asked for in one line, and leave them out. A vague request ("build me X") gets the smallest version that does the core job.
2. Already in this codebase (a helper, component, service, pattern)? Use it the way the surrounding code does.
3. Standard library or a platform feature? Use it.
4. An installed dependency? Use it. A few lines you write beat a new dependency.
5. Can it be one line a reader gets at a glance? One line.
6. Otherwise: the minimum code that works.

- Be lazy about the solution, never about the change: finish every place on the scope list. The shortest working diff wins, once you know everything it must touch.
- Write only what the task uses now, and keep values in the form the platform already gives you. Deletion beats addition. Keep the codebase's layers, interfaces and conventions.
- Bug fix: fix the root cause once, in the shared code.
- Between options of equal size, take the one correct on edge cases.
- Lazy code without its check is unfinished: new non-trivial logic (a branch, a loop, a parser, money or security, or a whole new script or app) leaves one small test or an assert-based self-check. Trivial changes need none.

Keep, whatever the size: validation at trust boundaries, error handling that prevents data loss (in code you move or merge too), security, accessibility, anything the user asked for.

## Comments

A comment describes the code as it stands, for a first-time reader. The code's history (what was removed, what it replaced, which issue or PR prompted it) goes in the commit message and PR.

Open a file with a header comment when it is:

- **A runnable script** that takes arguments or changes state: what it does, how to call it (arguments, environment, exit codes) and what it changes, so a caller needn't read the body.
- **A long file** (one an agent reads in parts): what it holds and where each part lives, so a partial read lands in the right place.

Below the header, comment for the file's reader:

- **Code agents read** (most code): comment only what the code cannot say for itself: a non-obvious reason, a constraint, a gotcha.
- **A script a person runs** (a README, doc or wizard tells someone to run it): comment each step's purpose for that person.

Docstrings follow the same test: a helper's says only what its name and signature can't; a test's states the behaviour under test, unless its name already does.

State a guarantee that spans the code ("never edits the repo", "never uses real tokens") once, in a design doc such as an ADR or a threat model.

When the reasoning lives in a document (an ADR, a README section), point to that document. The pointer is the whole comment: "ADR 0015 lists what it refuses".

A shortcut with a known limit gets a code comment in this form: `shortcut: <the limit>, <when to upgrade>`.
