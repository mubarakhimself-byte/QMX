---
title: One storage seam and one rclone runner
type: grilling
mode: AFK
status: closed
blocked_by: [packs-and-compression]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

Where does "any storage he connects through rclone" plug into the built code, and how many rclone callers does the PC keep?

## Resolution

- **The seam is the built `Repository` protocol** (`BK/repository.py:192-249`: `pool_has`, `put_pool`, `put_copy`, `copies`, `manifest`, `read_extra`, `fetch`, `drop`, `discard`, `sweep`, `room`, `clean`, `about`, `set_about`; read this session). It has one adapter today, `FolderRepository`. An rclone adapter makes it a real seam with two. The round, restore and drill do not change.
- **Packs live inside the adapters**, behind `put_pool`, `fetch` and `sweep`; callers never see the word "pack".
- **Only `rclone copy` writes to a storage; QMX deletes only through its own prune**, after the index no longer names a pack (`src:` 2.2, 3.2).
- **Kept from planned PR 6** (`plan:351-403`): the arrival check (`lsf`), manifest written last, "never `rclone sync`", the remote-name check, and never rclone's own text in an answer. **Dropped:** the `cache/backup-send/` hard-link tree (packs replace it).
- **One rclone runner on the PC**, in `qmx_home`: it finds the binary, passes `--config` and the config password command, never returns rclone's output (it can hold tokens, `PK/qmx-apps/src/qmx_apps/backup.py:56`), maps a failure to one plain line, and records the arguments. The node rebuild's own runner (`QX/node.py:470-475`, which today raises with rclone's stderr) moves onto it. The Hub's runner on the server (`PK/qmx-hub/src/qmx_hub/bucket.py:72-78`) stays its own: `qmx-hub` does not depend on `qmx-home`.
- **The binary.** QMX uses an rclone on PATH or one named in Settings; otherwise the connect dialog's first QMX step fetches the pinned release into `cache/tools/rclone/` and checks its published sha256. It is `rebuildable`. Today `rclone.exe` v1.75.2 sits at `D:/Tools/rclone/`, off PATH (`inv:` 4).

## Evidence

His words: "R-Clone like sorts me out everywhere. That's perfect. Which means even someone else can just sync to their Google Drive" (`words:185`). `align:` C2. R116 (no key text in any output).
