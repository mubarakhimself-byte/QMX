---
title: What the screen calls it (E3)
type: grilling
mode: HITL
status: closed
blocked_by: [saved-set-by-class]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: operator (his answer of 2026-10-28, `../research/sync/05-his-answers-2026-10-28.md`)
owner: operator
---

## Question (for him, in plain words)

What words does the screen use for this feature?

## Why it is yours

You see these words every day. "Backup" already confused you: you read it as outside machines (`words:70`). And inside QMX, "sync" already means the Library's link with your server.

## Recommended answer

| What it is | Word on the screen |
|---|---|
| Sending your work to your storage | **Sync to my storage** (the one switch) |
| What you connect to hold it (Drive, R2, your server, another drive) | **Storage**, next to **Machines** for compute |
| Coming back from a copy | **Restore** |
| The copies kept on this PC | **Copies on this PC** |
| QMX's own jobs, apart from your workflows | **Maintenance**, your word (`words:185`) |
| The Library's link with your server | **Server link** |
| The monitoring viewer | **Deep logs** (already the design's word) |
| "Backup" | not on the screen |

Say "yes" to accept. Or change any row, for example "call it Sync to my account".

## What changes with the answer

Only the words on the screen, in the UI notes and in the plain-words lines QMX shows. Code names do not change.

## Evidence

`align:` B, the two word collisions (the Library's server link is `Replicator` at `HO/host.py:813-815`; "sync is not a backup" at `explore:` 4). Design 62 uses "Deep logs" (`design:328-330`).

## Resolution

**The recommended words, with This PC shown as the first storage.**

His words, verbatim (`../research/sync/05-his-answers-2026-10-28.md`, E3):

> "Let's go with your recommendation, but consider the response to the last question."

"The last question" is E1, where he put his machine first. So the table above stands with one change: under **Storage**, the first row is **This PC**, shown as **Copies on this PC**, and it is the default storage, not an extra.

| What it is | Word on the screen |
|---|---|
| Sending your work to your storages | **Sync to my storage** (the one switch) |
| The list of places that hold copies | **Storage**, next to **Machines** for compute. First row **This PC** ("Copies on this PC"), then each one he connects |
| Coming back from a copy | **Restore** |
| QMX's own jobs, apart from his workflows | **Maintenance** |
| The Library's link with a server | **Server link** |
| The monitoring viewer | **Deep logs** |
| "Backup" | not on the screen |

Code names do not change: the package stays `qmx_home.backup` and the settings section stays `[backup]`.

Where it lands: `../research/sync/06-sync-and-connect-design.md` section 11.
