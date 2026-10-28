---
title: Packs and compression inside QMX's own pool
type: grilling
mode: AFK
status: closed
blocked_by: [saved-set-by-class]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

How are copies compressed ("zip files", `words:185`), and does QMX build that itself or use restic, kopia or an rclone layer?

## Resolution

- **QMX's own pool gains packs.** Many small pool files go into one pack file: one zstd frame per file with `checksum_flag` on, then a header listing each file's sha256, offset and length. An index maps sha256 to pack, offset and length and can be rebuilt from the pack headers.
- **The pool name stays the sha256 of the original bytes**, so the write check (`BK/repository.py:300-317`) and the restore check (`BK/restore.py:1062-1065`) are unchanged end to end.
- **Write order:** packs, then index, then manifest; delete in reverse. This is PR 225's safe copy order carried over (`src:` 3.3).
- **One pool format for every storage**, the folder kind and the copies on this PC included, so there is one restore path. The copies on this PC keep their `at: live` entries for write-once files, which copy nothing. No real folder holds a PR 225 pool yet (225 to 229 are not landed, and his first real start has not happened), so no migration is needed.
- **Already-compressed files** (Parquet, PDF, images) go into packs without compression, as kopia does by type.
- **No trained dictionary and no group frames now.** One frame per file gives about 2.4 times on QMX's templates; a dictionary gives 4.8 and one long stream 5.9 (`src:` 3.1, measured). The saved set is tens to a couple hundred MB (`inv:` 1, estimate), so the ratio barely matters; what matters on Drive is the file count ("about 2 files per second", `sources/rclone-drive.md`), and packs fix that whatever the ratio. Revisit only if the measured set is large.
- **Not restic or kopia.** restic encrypts every repository with a password it cannot recover (`sources/restic-design.md`, AES-256 on every file), which would force [Lock copies on cloud storage with a passphrase? (E4)](lock-cloud-copies.md) to "always". It would replace the sha256 pool, manifests, keep rule and restore that PRs 225 to 229 built and tested (+8,935 lines, `explore:` 6), and add a binary to every machine. The pack layer is one module inside the adapters, standard library only (Python 3.14 `compression.zstd`, present on this PC with zstd 1.5.7, `src:` 3.1).
- **Not rclone `compress`** ("experimental. Things may break and data may be lost", `sources/rclone-compress.md`). **Not rclone `sync` or `bisync`** toward the pool: a file named by its own hash never changes, so `copy` is enough, and `sync` deletes on the far side (`src:` 2.2).
- **The room check** keeps counting raw bytes, which overestimates with compression: the safe side (`inv:` 3, item 4).

## Evidence

His words: "zip files can compact a lot. The issue would be corruption, but we are dealing with mostly text" (`words:185`). A corrupted pack is caught by each file's sha256 and by zstd's frame checksum; damage is limited to that pack (`inv:` 3).
