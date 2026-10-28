---
title: One free-space floor, and full storage
type: grilling
mode: AFK
status: closed
blocked_by: [one-place-list]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

Three free-space floors exist, a folder he names on C: has none, and a full Google account hurts his Gmail. What protects his drives and accounts?

## Resolution

- **One floor for every local write:** the larger of 1 GiB and `disk.floor_gb` (or a twentieth of free space when unset). It replaces the three floors (`PK/qmx-home/src/qmx_home/versions.py:39`, `HO/disk.py:55-62`, `BK/plan.py:56`, combined at `BK/round.py:229`) and now covers a folder storage on C: too, which today can fill his system drive (`explore:` 2). Shown and editable in Settings.
- **A floor on any storage that reports free space**, default the larger of 2 GB and a tenth of the account, editable per storage. Google Drive and SFTP report free space; R2 does not and has no account to protect (`src:` 2.1). A Google account over quota stops Drive uploads and can affect Gmail, and after two years over quota content "may be removed" (`sources/google-one-storage-terms.md`).
- **When a storage reaches its floor,** that storage's sync stops before writing, one incident names the biggest class it holds, and the other storages carry on. QMX never spreads one copy over several storages (see [Spread copies over several free Google accounts (E2)](spread-over-accounts.md)).
- **Not a cap.** R106 bans QMX usage and spend caps. A floor limits nothing he does; it keeps his drives and his mail account usable, and he can change it.

## Evidence

His words: "if you look at the C drive and then the D drive, you realize ... Space is an issue" (`words:101`); C: 17 GB free, D: 58 GB free (`words:108`). `align:` C4 first row.
