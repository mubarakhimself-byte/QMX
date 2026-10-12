> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

---
id: 18
title: How agents build things and know what exists
label: wayfinder:grilling
status: open
assignee:
blocked-by: [02, 03, 04]
who-decides: Operator (HITL)
---

## Question

This was the question that started the redesign: how does a copilot **build, maintain, open and edit** mini apps, workflows, widgets and plugins by default?

Also:
- How does an agent know QML, QMB, QMF and the Library exist? (Tools, SDKs, skills, or all three.)
- How does it read and parse data, and confirm that what it stored was really stored (hooks)?
- How do two agents avoid editing the same Library item or file at once?
- Cross-surface reach: from the Lab, use something in Portfolio; from the main chat, reach both; and the copilot knows which surface it is acting on.

Inputs: `qmx-internal.md` §a and §d; `backlog.md` (Library v2); tickets 03, 04 and 17.
