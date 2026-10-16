---
title: Decision 6: save the Experimentation Board on the backend?
type: grilling
mode: HITL
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "SUPERSEDED. Answered by ruling 31 (saved in the session; the Board is the Lab node editor); the browser-only wording is wrong (study 24, ruling 32)."
closed: 2026-10-16
---

## Question

May the Experimentation Board be saved on the backend, so a board survives restarts and workflows can run it? (This changes two docs that say the Board lives only in the browser.)

## Recommended answer

Yes.

## What it unblocks

The Board object, `scope-run`, the iteration counter, the L1 pilot. ADR-0024 is updated in the next docs pass.

## Sources

`19` section 1 and section 6; `20-review-a` rewritten decision 6; `05-qmx-today.md` §3.

## Resolution

Resolved. Ruling 31: the Board is saved as a draft and is the Lab editor's Graph mode (engine AD-11, Lab AD-2, Library kind `board`). (Map rewrite 2026-10-16.)
