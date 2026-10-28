---
title: Restore from my storage, on a new PC and from Settings
type: grilling
mode: AFK
status: closed
blocked_by: [connect-storage, several-machines-one-storage, secrets-stay-home]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

"I installed it again ... six months later ... it's as if I didn't leave" (`words:151`). How does a restore from his storage work on the built restore code?

## Resolution

- **The built restore is kept whole:** checked, then confirmed, showing what it replaces. The earlier data is set aside whole. Another folder's copy replaces data only with `replace`. A purged blob is never restored. Memory is rebuilt. After a restore, fires and server sync wait for his carry-on (PRs 226, 228, 229; `align:` A2 rows 20 to 33).
- **A storage is a restore source.** The `source` of the card and of Settings gains the storage kind beside `folder` (UIH §19 row 12). It is read through the same `Repository` adapter as the sync.
- **On a new PC (the first-start card):**
  1. He picks "Restore from my storage".
  2. The storage's connect dialog runs: he signs in again.
  3. The copies list shows the newest copies with machine, time and counts, and he picks one (Steam's way).
  4. The check shows what is newer on the PC; the built `newer` counts warn when he would go backwards (Hermes's warning, `src:` 5.2).
  5. The restore runs, then the handover.
  This is Android's "restore before first launch" (`src:` 1.2).
- **From Settings:** PR 229's restore while QMX runs, finished at the next start, with the same storage source.
- **Progress with counts.** A restore reports `done` of `total` today: "fetching your copy from `<storage>`" in bytes, then "placing the copy's files" in files. Today `done` and `total` stay 0 for a restore (UIH §19 row 11).
- **After the restore:** the first start shows the keys to fill in (key names travel in the copy), then the built carry-on card.
- **A server holding newer Library history** than the restored copy is offered after carry-on (Library AD-14 `adopt`, design:266).
- **Two more restore items:**
  - Cancel a staged restore before the next start (UIH §26 gap 8).
  - A failed restore into a non-default folder is offered again by the card (PR 228 review low 1).

## Evidence

R141 (a reinstall picks up exactly where he left off), extended to a new PC by his words. PR 228 restore from the card, reviewed clean (`words:122`).
