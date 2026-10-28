---
title: Sync before every update
type: grilling
mode: AFK
status: closed
blocked_by: [sync-switch-and-timing, copies-on-this-pc]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

He wants "first make sure everything is synced and saved ... before we update" (`words:185`). No updater exists on the PC (`inv:` 5). What is the order, and what does the backend give the future updater?

## Resolution

- **One call, `sync_now(why="before-update")`**, with a time limit. Two callers: the store-upgrade hook in `serve` today (`HO/__main__.py:142-143`), and the desktop updater when it exists.
- **The update order** (Hermes's order with the off-site step added, `src:` 5.2):
  1. Sync to his storage, if the switch is on.
  2. The local before-upgrade copy that PR 228 already makes.
  3. Update the program.
  4. Check: open the stores or start the new version against a copy.
  5. If the check fails, put the old program back. His data is untouched (R141).
- **When step 1 fails:**
  - From the updater, he is there, so it asks with one line: "the sync to `<storage>` failed: `<why>`. Update anyway? Your copy on this PC is fresh."
  - From `serve`'s store upgrade, nobody is asked. It falls back to the local copy with one line and goes on, as PR 228 does.
- **Two local copies on one upgrade become one.** Each store's own `pre-*` copy (`PK/qmx-home/src/qmx_home/versions.py:235-302`) is released once a `before-upgrade` copy of the same moment exists. `pre-*` copies are kept only when that copy failed (`align:` C4).
- **The updater itself is out of scope** (desktop session). This map fixes its first step and the backend call.

## Evidence

His words above, `words:185`: "I think many platforms do this. For example, the Hermes agent does this". Hermes order and its failure line: `sources/hermes-docs-updating.md`.
