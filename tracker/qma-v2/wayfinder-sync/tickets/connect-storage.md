---
title: Connect a storage
type: grilling
mode: AFK
status: closed
blocked_by: [connect-dialog, one-rclone-runner, one-free-space-floor]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

What are the steps of the storage kind, for Google Drive, R2, his server, a folder on another drive, and any other rclone remote?

## Resolution

**The steps:**

1. QMX: get rclone (on PATH, named in Settings, or fetched pinned into `cache/tools/rclone/` and checked).
2. His: choose the kind. The second-drive suggestion is one choice (`HO/backups.py:531-566`).
3. QMX and his, in turns: **rclone's own question loop.** `rclone config create <name> <type> --non-interactive` answers with the next question as JSON (name, help, default, choices, whether it is a password). The dialog shows it as one card, sends his answer back with `--state` and `--result`, and gets the next question (`sources/rclone-cmd-rclone_config_create.md`). For Google the sign-in page opens in his browser. So any of rclone's storage kinds works with no QMX code per kind; QMX pre-fills the answers it knows for Drive, R2 and SFTP.
4. QMX: test it with free space (`about`, where the kind reports it) plus a small write, read and delete under its folder.
5. QMX: write the place row (`can = ["keep"]`) and its sync policy with defaults (all four switches on).
6. QMX: run the first sync, with steps and counts.

**Per kind:**

- **Google Drive** uses QMX's own Google sign-in client, not rclone's shared one. rclone says its shared client "will stop working during 2026 ... creating one is now required" (`sources/rclone-drive.md`).
  - QMX's client is a published "Desktop app" client with PKCE. It asks only for `drive.file`, which is non-sensitive, needs no Google review, and keeps the files visible in his Drive. `drive.appdata` would hide them and is wiped when he removes QMX's access (`src:` 2.4).
  - Published, sign-ins do not expire after 7 days. Under 100 users it can stay unverified behind a warning screen.
  - Registering it is a one-time step he does in Google Cloud. It is folded into [Which storage do you connect first? (E1)](first-storage.md). Friends sign in through the same client.
- **Cloudflare R2:** `type = s3, provider = Cloudflare`, region `auto`, his account endpoint, and an access key typed through the write-only key route. Set `no_check_bucket = true` for an "Object Read & Write" token (`src:` 2.3). R2 reports no free space, so it gets no floor.
- **His server:** SFTP over Tailscale. It becomes available once the server is connected as compute (R142: the server comes second).
- **A folder on another drive:** the built folder adapter, no rclone. A target inside the QMX folder is refused; one on the same drive is kept with a warning (PR 225).

**Never:** the QMX folder itself inside a Drive, OneDrive or Dropbox live-sync folder. The card already refuses that (UIH §19 row 8). "Sync to Google Drive" means QMX sends packs through rclone.

## Evidence

His words: "even someone else can just sync to their Google Drive and it will use that" (`words:185`); "Google Drive is so small ... I can figure out a way to get storage via Google subscription" (`words:151`). `src:` 2.3 to 2.5 and "What fits QMX" under section 2.
