---
title: Lock copies on cloud storage with a passphrase? (E4)
type: grilling
mode: HITL
status: closed
blocked_by: [packs-and-compression, connect-storage]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: operator (his answer of 2026-10-28, `../research/sync/05-his-answers-2026-10-28.md`)
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

## Resolution

**No passphrase and no lock of any kind, on any storage. Secrets never travel. QMX adds no encryption layer of its own now. Any encryption added later must never need him to remember anything, and must never leave a copy unreadable once this PC is gone.** The recommended answer above (locked on Drive and R2) is rejected.

His words, verbatim (`../research/sync/05-his-answers-2026-10-28.md`, E4):

> "I don't think it makes sense for us to lock. I mean, we can have a unique character or synchronization with QMX, but I don't think it needs locking. Maybe encryption, but locking, not so much. I mean, I'm imagining myself 10 to 20 days when I've been just doing other side hustles, and you're asking me for a password that most likely I forgot. So I don't know. It doesn't make sense."

What it decides:

- **No rclone `crypt` layer and no passphrase prompt.** A copy on any storage opens on a new PC with nothing but his sign-in to that storage.
- **A copy holds nothing secret.** The secret class never travels (`secrets-stay-home`), so a copy carries key names only, never a key.
- **Encryption that needs no memory, and why none is built now.** A key that only this PC holds would make every copy unreadable once the PC is lost, which is the one case a copy exists for. So that encryption is ruled out. What stays is the storage's own protection: Drive's `drive.file` access (QMX sees only the files it made) and the provider's own encryption at rest. The second point is the coordinator's reading and was not checked against a saved source.
- **"A unique character ... with QMX"** reads as each QMX folder's own identity. A copy lives under its own `QMX-backup/<home_id>/` folder, so QMX knows its own copies by that id (inferred from his words; he did not spell it out).
- **The local `rclone.conf` encryption stays.** It is not a lock on his copies. Its password lives in Credential Manager, he never types it, and on a new PC he simply connects the storage again.

Where it lands: `../research/sync/06-sync-and-connect-design.md` sections 2 and 3, and invariant I4.
