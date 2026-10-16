---
title: Library OPEN-2: mirror or replace the QMF registry room
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
---

## Question

For governed trading records (bots, pods, bindings, results), does the Library mirror the QMF registry room or replace it?

## Recommended answer

Mirror: verbatim copy under the same fp1; the node's registry room stays the governed evidence copy; divergence is a collision alarm.

## Sources

`architecture/library-and-data/`OPEN-DECISIONS.md OPEN-2; DEC-0188; CT-09.
