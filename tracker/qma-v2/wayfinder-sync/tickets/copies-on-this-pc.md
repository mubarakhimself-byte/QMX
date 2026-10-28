---
title: "Copies on this PC: kept, smaller, switchable"
type: grilling
mode: AFK
status: closed
blocked_by: [saved-set-by-class, packs-and-compression]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

The hourly quick undo is fixed in code and cannot be switched off (`HO/backups.py:273`, `BK/plan.py:140`, read this session). The coordinator suggested "off if you sync to your account" (`words:168`). What does it become?

## Resolution

- **It stays, on by default.** R136 says the PC holds everything first, "with a local backup always". The coordinator's "off if you sync" was his own suggestion, not the operator's, and R136 outranks it.
- **It becomes a setting with an off switch and a cadence**, default hourly when something changed, keep 48 hours then 7 days (the built defaults). With it off and no storage connected, the doctor row says in plain words that his work has no copy anywhere.
- **It copies the same classes as the sync** (recipes, content, results), never rebuildable, secret or scratch, and it uses packs and compression like every storage. That answers his space worry at the source: the explore's 3 to 11 GB worst case on D: was uncompressed whole-folder churn (`explore:` 2); text and SQLite compress several times over (`src:` 3.1).
- **Its folder stays `backups/quick` inside the QMX folder** (`BK/round.py:39`).
- **Defaults are tuned once from his real folder.** The sizes above are estimates; his real folder was never read (`inv:` 1). The first real start measures the saved set and the copies' growth (map fog).

## Evidence

- His words: "what if I don't want to be making copies every hour? ... when you do make backups every hour, you're sort of duplicating data ... Space is an issue" (`words:101`).
- R136 ("with a local backup always"), R137 (no lock he cannot switch off), the configurable-means-editable rule.
- His answer to "off if you sync": "it's viable, but first look at what I said at the start of this dictation" (`words:185`), which pointed at saving small recipes, not at removing the local copy.
