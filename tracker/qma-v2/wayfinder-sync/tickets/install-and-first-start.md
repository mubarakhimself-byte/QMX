---
title: What install and first start show, step by step
type: grilling
mode: AFK
status: closed
blocked_by: [restore-from-storage, connect-storage, sync-before-update]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

"Even in the UI installation, when I'm installing for the first time or reinstalling or updating" (`words:185`): what step sequence do install, first start and update show, and which backend lines feed it?

## Resolution

**Install** (the desktop installer, which the desktop session builds; this fixes its steps):

1. Where the program goes: per-user, no admin, the default under `%LOCALAPPDATA%\Programs\QMX`, with another drive offered when C: is low.
2. Installing, with step lines: getting QMX, getting its Python packages, checking the install.
3. It opens the first-start card. It does not start QMX by itself before that.

This follows Docker Desktop and Ollama: per-user, no admin, folder choice up front (`src:` 5.1). His C: has 17 GB free (`words:108`).

**First start** (the built card, UIH §19, with one choice and one card added):

1. **Where your QMX is:**
   - make a new folder (each drive's free space shown);
   - open a folder;
   - bring in old data;
   - **restore from my storage (new)**;
   - restore from a folder.
2. **If he restores from his storage:**
   - connect the storage, signing in again;
   - pick a copy from the newest ones (machine, time, counts);
   - see what it replaces;
   - restore, with steps and counts: "fetching your copy from `<storage>`", "checking the copy", "placing the copy's files", "checking the copy's stores";
   - the handover;
   - the keys to fill in;
   - the carry-on card.
3. **Otherwise:** the handover, then one optional card, **"Keep your work in your storage"**. It runs the storage connect dialog and the first sync with steps, and he can skip it. It replaces design F step 5's second-drive card; the second drive is one choice inside it.
4. **Nothing else.** Deep logs, machine learning and documents, servers and GPUs come later from Settings or the copilot, each with its size (design F step 15). No server step is part of the first start (R142, design F1).

**Update** (the desktop updater, when built): the order in [Sync before every update](sync-before-update.md). Its first visible step is "syncing your work to `<storage>`".

**Lines the screen reads:**

- Each step is a job's `step` with `done` of `total`, through the job shape built for the card and the host (UIH §19 row 9).
- The exit codes stay as built (UIH §19 rows 3 and 4).
- A store opened read-only is named up front, not only at the first refused write (UIH §26 gap 5). A restore of an older copy, or a rolled-back update, can leave a store newer than the program.

## Evidence

- His words above. R141 (data independent of the app), R142 (QMX on the PC first, the server second).
- Android restores before first launch (`src:` 1.2). Hermes's update steps (`src:` 5.2).
- Today there is no installer: he clones and runs `uv sync` (`inv:`, "Progress he sees today").
