---
title: The switch, what each storage gets, and when it syncs
type: grilling
mode: AFK
status: closed
blocked_by: [saved-set-by-class, one-place-list]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

What is "one switch", what can he choose under it, and when does a sync run?

## Resolution

- **One main switch**, "sync to my storage", on or off. Off pauses every storage; nothing is deleted.
- **Under it, per storage, four switches, all on by default:** recipes, my content, run results, prices that cannot be downloaded again. This is the shape Chrome, VS Code, Steam and Obsidian share (one switch, a short list underneath, `src:` 1.11). Per-storage choice costs nothing extra, because the sync policy is already per place, and it lets a small free storage skip the big imported ticks while his server takes them (see [Which storage do you connect first? (E1)](first-storage.md)).
- **When:** once a day when something changed, at a time he can set (a PC that was off syncs at its next start), before every update, and on his "sync now". This is Android's rule (daily, when idle, only if something changed, `src:` 1.11). It is not "on every change": a changed store is sent whole (`explore:` 2), and `engine.sqlite` changes all day, so every-change syncing would upload the run ledger many times a day. He can set any cadence down to hourly.
- **A sync is a backup, not a mirror.** Each sync is a dated copy; deleting a file on the PC never deletes a kept copy. Scenario: he deletes a strategy on Tuesday and notices Friday; Monday's copy still holds it (`align:` B).
- **Keep rule per storage**, the built one (`BK/keep.py`: newest days, weeks and months; the newest and the newest checked copy always kept), defaults 14, 8, 12.
- **Every setting comes back with its default.** `GET` of the sync settings returns every value, defaults filled in, so the screen never shows blanks (fixes `HO/backups.py:666-690`, `explore:` 1).
- **The 30-day hold becomes an event.** Pre-change and before-upgrade copies are released after the first whole sync to a storage on another disk, not 30 days after a second-drive copy (`BK/keep.py:16`, `:57-61`).
- **Retry timing is not a setting.** A storage that refused is tried at its next due round; after seven missed rounds the incident says so. These are not choices he makes, so they stay internal and the doctor line states them in words.
- **The volume backup's keys** (`APP_KEYS`, `BK/plan.py:49-53`) leave this section with [What goes before anything is added](subtract-first.md), so the section has one meaning.

## Evidence

- His words: "It's more like a toggle" (`words:151`, the Claude settings switch); "We can have an interval, but we can also study how multiple apps do this" (`words:151`); "some things don't need continuous backup. So there is that type of configuration" (`words:151`).
- The configurable-means-editable standing rule; R137 (no default-closed locks: the switch and every storage can be off).
