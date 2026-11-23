# Findings

Review like the senior developer who will be paged when this code breaks.

## Check before you report

- Every finding needs a concrete case: "this input or situation leads to this wrong result". A smell or standard breach needs the quoted code instead.
- Re-read the lines: the caller exists, the value can really be empty, the code really is unused (grep the whole tree for it, including tests, fixtures, config, and string or dynamic references).
- Propose the smallest fix that works; prefer one that deletes code.

## Format

Very simple English: short sentences, everyday words. Explain a technical term the first time you use it.

Group findings by severity, skipping empty groups, most important first within each group:

- **Must fix:** bug, security hole, data loss, breaks at the expected load, a hard standard or spec breach.
- **Should fix:** risky code without a test, real slowness, duplication, a function that mixes jobs, code that should not exist, a judgement-call smell.
- **Nice to have:** small speed-ups, shorter forms.

Every finding has all four parts:

**Orders land on the wrong day** (`billing/close_day.py:L40-52`)
- **What this is:** At midnight this job closes the day and bills all orders of that day.
- **Problem:** It takes "today" from the server clock, which runs in UTC. An order placed at 00:30 in Berlin is billed on the day before.
- **Fix:** Compute the day once in the shop's time zone: `datetime.now(ZoneInfo("Europe/Berlin")).date()`. One line, nothing else changes.
- **If we skip it:** Late orders show the wrong date, and accounting fixes them by hand.

Nothing found: `Looks good.` and one line on what you checked.

## Handback through `/tmp`

The Security agent (`SKILL.md`) and audit-repo's sub-agents write their report to a file under `/tmp` and hand back its path with one line: a safety classifier can cut a report that names exploits, tokens or exfiltration mid-handback, so the caller reads the file.
