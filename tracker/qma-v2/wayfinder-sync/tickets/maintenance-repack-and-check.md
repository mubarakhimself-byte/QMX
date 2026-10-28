---
title: Monthly re-pack and check as QMX's own maintenance
type: grilling
mode: AFK
status: closed
blocked_by: [packs-and-compression, several-machines-one-storage]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

He asked for re-zipping on a schedule plus quality checks, "maybe every after month", as maintenance, kept apart from his own workflows, with an agent attachable. What runs, where, and how is it shown?

## Resolution

- **One monthly job per storage, in the host:**
  1. **Re-pack:** drop packs no kept copy names; rewrite a partly used pack only past 5% unused, with a size limit per run (restic's prune, `src:` 3.2). New data already lands in new packs, so nothing re-uploads the whole set every month.
  2. **Check:** read every index and manifest, and download and verify one slice of the packs, a different twelfth each month (restic `--read-data-subset=n/t`).
  3. **Drill:** restore a random copy's sample into `cache/restore-drill/` (the built drill, `BK/restore.py:427`, never scheduled today, `explore:` 1).
  Each step's numbers (schedule, threshold, slice, sample) are settings with their defaults.
- **Sync and maintenance run in the host, not as workflows.** The sync must run with the engine's fires paused after a restore and before an update (`plan:549`, `:591`). The host's sweep becomes the one scheduler: the app volume timer (`PK/qmx-apps/src/qmx_apps/backup_schedule.py:10`) and the weekly template's cron (`catalog.py:396-404`) go (`align:` C4).
- **Maintenance is listed apart from his work.** The screen shows "QMX's own maintenance": the host's jobs (sync, re-pack and check) and the shipped workflows marked `meta.kind = "maintenance"` (`connections-health`, the guard watchdogs). The marker sits in `meta`, outside the content hash, so it needs no schema change (`PK/qmx-engine/src/qmx_engine/definition/model.py:205-212`, read this session). Each item has its own off switch (R137).
- **An agent is optional, none by default.** Each host maintenance job emits an event when it ends; he can add a maintenance workflow triggered by that event, with an agent step that reads the result and writes a note. The work itself never moves into the engine.

## Evidence

- His words: "Or after a given amount of time, we re-zip. Also, there can be quality checking ... It's more like maintenance work, maybe every after month or so ... it would be very good if I can attach an agent to them in the entire QMX" (`words:185`); "please don't confuse agentic workflows and external workflows ... they're the ones that now we are talking about, like maintenance" (`words:219`).
- Today maintenance templates sit on his shelf with his workflows, with nothing marking them as QMX's own (`inv:` 2).
