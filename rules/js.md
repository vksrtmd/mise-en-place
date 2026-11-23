---
paths:
  - "**/package.json"
  - "**/*.{js,jsx,ts,tsx,mjs,cjs}"
---

# JS projects

A new worktree has no `node_modules`, so typecheck, tests and pre-commit hooks fail in it. Run the install the lockfile names (`npm ci`, `pnpm install --frozen-lockfile`, `yarn install --immutable`) before the first check. Symlinking the main checkout's `node_modules` also works, but a `node_modules/` ignore pattern skips only directories, so git sees the symlink: remove it before committing.

When agents run vitest in parallel, wrap each run in one shared lock: `flock /tmp/<run>-vitest.lock <test cmd>`. Unlocked parallel runs oversubscribe the CPU, and vitest workers time out starting.
