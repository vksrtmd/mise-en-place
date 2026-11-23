---
paths:
  - "**/Cargo.toml"
  - "**/*.rs"
---

# Rust projects

A new worktree builds every dependency from cold. To reuse them, point every build at one target dir before the first one: `export CARGO_TARGET_DIR=$HOME/.cargo/target/<run>`; child processes and scratch worktrees inherit it.

When agents build in parallel, give every one that dir and `export CARGO_BUILD_JOBS=2`, and have each run only its focused tests (`cargo test <filter>`): separate dirs and uncapped jobs link several copies at once, which runs a memory-capped container out of memory. Cargo's lock on the dir lets one build run at a time; the others print "Blocking waiting for file lock": a queue to wait on.

Run at most 3 Cargo builds at once, and start one only while `df -h ~/.cargo` shows 10 GB free: a target dir grows to several GB.
