---
title: Library OPEN-7: do copilot-chat merges of governed kinds still ask?
type: grilling
mode: HITL
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-16
---

## Question

Now that workflows never wait (ruling 57), does a copilot-chat merge of a governed kind (unit, bot, pod, workflow, mini app, skill) into `main` still ask him once?

## Recommended answer

Yes, keep the one ask in chats; ruling 57 is about unattended workflows.

## Sources

`architecture/library-and-data/`OPEN-DECISIONS.md OPEN-7; Library AD-18; `33-state-of-play.md` section 3 item 8.

## Resolution

Resolved. Chat merges into `main` ask once (MANAGE, Library AD-9): lifecycle kinds by ruling 80, governed kinds on the existing recommendation (DEC-0188) (27c fix 15, 27d judgment 4).
