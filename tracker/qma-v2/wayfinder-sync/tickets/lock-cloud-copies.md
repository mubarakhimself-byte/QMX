---
title: Lock copies on cloud storage with a passphrase? (E4)
type: grilling
mode: HITL
status: open
blocked_by: [packs-and-compression, connect-storage]
claimed_by: ""
created: 2026-10-28
owner: operator
---

## Question (for him, in plain words)

Your chats, strategies and run results would sit on Google's or Cloudflare's disks. Should QMX lock them so only your passphrase opens them?

## Why it is yours

It can't be undone if it goes wrong. Suppose you forget the passphrase and lose this PC too. Then nobody can open those copies, you included, and there is no way to recover them. Keys and passwords are never in the copies either way.

## Recommended answer

**Lock copies on cloud storage (Google Drive, R2) by default. Leave them unlocked on your own server and on a drive you plug in.**

- You choose the passphrase once, when you connect the storage.
- QMX keeps it in Windows' password safe on this PC, so you never type it day to day.
- QMX then asks you to save it somewhere safe, such as a password manager or paper. The first sync waits until you have typed it twice.
- On a new PC you type it once to restore.
- Your PC always holds the main copy, so a forgotten passphrase loses your work only if this PC is lost as well.

Say "yes" to accept. Or say "don't lock" or "lock everywhere".

## What changes with the answer

The default for each storage kind only. The lock is rclone's own `crypt` layer over a storage, added without changing the pack format (`src:` 3.3, "Encryption inside the pack"). Switching it later is possible: QMX would send the copies again into a locked or unlocked folder (inferred from how `crypt` wraps a remote; not tested).

## Evidence

- rclone `crypt` encrypts file contents and names. It does not hide length or modification time (`sources/rclone-crypt.md`).
- `drive.file` means QMX sees only the files it made (`src:` 2.4). It does not stop someone who gets into your Google account from reading them.
- R135: keys never leave their home, so they are never in a copy.
