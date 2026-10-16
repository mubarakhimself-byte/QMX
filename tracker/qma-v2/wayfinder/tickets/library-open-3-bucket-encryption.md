---
title: Library OPEN-3: encrypt the bucket copy
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
---

## Question

Encrypt the bucket copy of every Library object?

## Recommended answer

Yes, one rule: rclone crypt keyed from the escrowed `qmx/backup-payload-key`; the server replica stays plaintext.

## Sources

`architecture/library-and-data/`OPEN-DECISIONS.md OPEN-3; ruling 42; Library AD-16.
