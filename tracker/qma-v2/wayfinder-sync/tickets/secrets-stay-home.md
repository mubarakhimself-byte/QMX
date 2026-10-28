---
title: Secrets never travel; a new PC asks for keys by name
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

What happens to keys, tokens and sign-ins in a sync, and how does a new PC get them back?

## Resolution

- **One secret list, in the class table:** `keys/`, `vault/**`, `rclone.conf`, the four Claude login files (`BK/snapshot.py:71-78`). The harness guard's `secret_files` (`PK/qma-harness/src/qma/harness/tools.py:909-923`) reads it and adds its own extras, which closes the attach review's MUST 6 (the guard misses `data/vault/`).
- **No secret leaves the PC, sealed or not.** The sealed key copy (planned PR 7, `plan:405-459`) is parked in the backlog.
- **Keys travel as names.** Each copy carries the list of key names its recipes need (n8n's credential stubs, OpenCode's `{env:}` references; `src:` 1.8, 1.9). After a restore onto a new PC, the first start shows that list as "keys to fill in", each typed through the write-only key route of [One step-by-step connect dialog for screen and copilot](connect-dialog.md). Sign-ins (Claude plan, cTrader, Google) are done again, as a new device would.
- **rclone's own config is encrypted.** `data/rclone.conf` holds storage tokens. It is encrypted with a password kept in Credential Manager and handed to rclone through `RCLONE_PASSWORD_COMMAND` (`sources/rclone-docs-config-encryption-excerpt.md`), so keys stay in the OS keyring as R116 requires. On a new PC the storage is connected again, which is also the first step of restoring from it.

## Evidence

- R116: keys never printed, keys in the OS keyring. R135: tokens and live-trading keys never leave their home.
- The coordinator's table he answered: keys "Not in the copy. You sign in again on a new PC" (`words:162`); the track record: the sealed key copy was something "you never asked for" (`words:29`).
- `src:` "Secrets travel as names only" (1.11, What fits QMX).
