---
title: Back up the orphaned 10 GB tick history now
type: task
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
---

## Question

The EURUSD and USDJPY tick history (about 10 GB, 2003-2026) under `Documents\QMX\data\raw` has no backup and no reader. Copy it to the bucket (and the server) and verify two copies before anything else touches it.

## Recommended answer

He confirms the bucket target; the agent runs rclone with a checksum verify and records counts and hashes. Re-ingest is a data-track PR in `ENGINE-PLAN.md`.

## Sources

Study 30 section 0 items 2, 5 and question 3; `33-state-of-play.md` section 3 item 9; ruling 81.
