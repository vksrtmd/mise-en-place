---
name: research
description: Use when a question needs researching against primary sources, or when reading legwork should go to a background agent.
---

First **probe** every host the question's primary sources live on: `curl -sS -m 10 -o /dev/null -w '%{http_code}\n' https://<host>/`. A host is blocked when the code is `000`, since curl got no response. A question with a blocked host goes to the user: write a self-contained **research prompt** (the question, its context, and the steps and Done line below) for them to run in an agent with open internet access. When the question comes from a ticket, post the prompt on it as a comment, label it `ready-for-human`, and name the blocked hosts in the comment; otherwise give the prompt to the user.

Hand each question whose hosts all answer, its context, and the steps and Done line below to a **background agent** so you keep working while it reads. Start it fresh, not as a fork. When the session can't run one, do the research yourself.

The research:

1. Trace every claim to the **primary source** that owns it: official docs, source code, specs, first-party APIs.
2. Write the findings to a single Markdown file, each claim cited to its primary source.
3. Save it where the caller names; otherwise where the repo already keeps such notes, matching that convention; with no convention, pick a sensible location.

Done when every part of the question is answered or marked unverifiable, each answer cited to a primary source, and the file's path is reported to the caller with every denied or blocked action quoted verbatim.
