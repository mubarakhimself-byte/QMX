---
title: Library answers to engine requests L11-L14
type: task
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-16
---

## Question

`ENGINE-REQUESTS-ANSWERED.md` answers L1-L10 only. Answer L11 (vault beside the Hub), L12 (run token grows into the run pass), L13 (imported traces), L14 (placement on run summaries) against the Library spine, and fold the answers in.

## Unblocks

Library doc changes (row on AD-12).

## Sources

`architecture/workflow-engine/`LIBRARY-REQUESTS.md L11-L14; `architecture/library-and-data/`ENGINE-REQUESTS-ANSWERED.md; engine AD-28, AD-30, AD-32.

## Resolution

Resolved. Library ENGINE-REQUESTS-ANSWERED now answers L11-L17; AD-12 rewritten so no worker ever holds a provider key (run passes only) (27c fix 9).
