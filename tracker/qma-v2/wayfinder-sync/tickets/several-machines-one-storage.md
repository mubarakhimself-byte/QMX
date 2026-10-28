---
title: Several PCs and one storage
type: grilling
mode: AFK
status: closed
blocked_by: [one-rclone-runner]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

His second laptop, a friend, or a restored PC can point at the same Drive folder. Who writes what, and who prunes?

## Resolution

- **No shared writer.** Each QMX folder has its own `home_id` and writes only under `QMX-backup/<home_id>/` in a storage (UIH §24 row 2). Each home prunes and re-packs only its own folder. So kopia's "one maintenance owner" lock (`src:` 3.3) is not needed: the sharing it serializes does not exist.
- **The fork guard stays and matters more** (`align:` A1 row 14, PR 225): a storage folder another QMX folder wrote to, or one whose `backup.toml` vanished, is refused until he carries on.
- **Only homes sync to a storage.** A server is a stand-in (R136); what a server makes reaches the PC through the Library's server link, and the Hub's own bucket push stays for the server (`PK/qmx-hub/src/qmx_hub/bucket.py`).
- **Picking a copy never happens quietly.** On a restore, the screen shows the newest copies with machine name, time and counts, and he picks, as Steam does (`src:` finding 2, 1.11). Pool files cannot conflict, because a file's name is its own hash; only "which copy is the latest" can.

## Evidence

Principle separate-before-serializing (give each actor its own state; lock only when one shared writer is a real invariant). `src:` 1.10, 3.3. `align:` B scenario 2.
