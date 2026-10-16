---
title: Library OPEN-4: dense retrieval in v1
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
---

## Question

Ship semantic (dense) retrieval in v1?

## Recommended answer

Yes, optional and rebuildable (sqlite-vec plus a small local embedding model behind a Settings flag), re-ordering only.

## Sources

`architecture/library-and-data/`OPEN-DECISIONS.md OPEN-4; Library AD-8.
