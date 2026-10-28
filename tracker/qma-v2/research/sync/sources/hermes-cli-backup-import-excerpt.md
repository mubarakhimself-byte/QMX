<!-- Source: https://raw.githubusercontent.com/NousResearch/hermes-agent/main/website/docs/reference/cli-commands.md
     Fetched: 2026-10-28. Excerpt: the 'hermes backup' and 'hermes import' sections (lines 1109-1223), verbatim. -->

## `hermes backup`

```bash
hermes backup [options]
```

Create a zip archive of your Hermes configuration, skills, sessions, and data. The backup excludes the hermes-agent codebase itself, and it does not nest earlier backup artifacts (`backups/`, `state-snapshots/`) — each of those already contains its own copy of `state.db`.

| Option | Description |
|--------|-------------|
| `-o`, `--output <path>` | Output path for the zip file (default: `~/hermes-backup-<timestamp>.zip`). |
| `-q`, `--quick` | Quick snapshot: only critical state files (config.yaml, state.db, .env, auth, cron jobs). Much faster than a full backup. |
| `-l`, `--label <name>` | Label for the snapshot (only used with `--quick`). |
| `-k`, `--keep <N>` | After a full backup, delete older `hermes-backup-*.zip` files in the output directory beyond the newest N (default 3; `0` keeps everything). Custom-named zips are never touched. |

The backup uses SQLite's `backup()` API for safe copying, so it works correctly even when Hermes is running (WAL-mode safe).

**Exit status:** `0` only when every selected file landed in the archive. If some files could not be added (`Backup incomplete: …`), the zip is kept so the rest can still be restored, but the command exits `1` — a cron or systemd timer will not report a partial archive as success, and `--keep` pruning is skipped so older complete archives survive. `2` means another backup was already running.

**What's excluded from the zip:**

- `*.db-wal`, `*.db-shm`, `*.db-journal` — SQLite's WAL / shared-memory / journal sidecars. The `*.db` file already got a consistent snapshot via `sqlite3.backup()`; shipping the live sidecars alongside it would let a restore see a half-committed state.
- `checkpoints/` — per-session trajectory caches. Hash-keyed and regenerated per session; wouldn't port cleanly to another install anyway.
- `models/`, `runtimes/`, `node/` at the root of `~/.hermes` (and of each `profiles/<name>/`) — regenerable runtime downloads, often tens of GB. Deeper directories with the same names (a skill's `models/`) are kept.
- Browser profiles: `browser-profile/` (the real-profile snapshot — copied Cookies / Login Data), `browser-profiles/` (live CDP profiles) at any depth, and `browser_profiles/` (the Browser Use CLI backend's Chromium user-data dir, with its own Login Data / Cookies) at the root of `~/.hermes` and of each `profiles/<name>/`. Credential stores that must never enter an archive; all are regenerated on the next launch.
- Regenerable entries of `cache/` at those same roots — model/plugin catalogs, stamps, browser profiles, tool-output spill. Durable artifacts stay in: `cache/images`, `cache/audio`, `cache/videos`, `cache/documents`, `cache/screenshots` (media delivered to or received from you) and `cache/citations` (the grounded-citations ledger). A deeper `cache/` (inside a skill) is kept whole.
- Unix sockets, devices, and symlinks — a zip cannot hold them; before they were excluded, a stray `gateway.sock` made every full backup report `Backup incomplete`.
- The `hermes-agent` code itself (this is a user-data backup, not a repo snapshot).

### Examples

```bash
hermes backup                           # Full backup to ~/hermes-backup-*.zip
hermes backup -o ~/backups/hermes.zip   # Full backup to specific path
hermes backup --quick                   # Quick state-only snapshot
hermes backup --quick --label "pre-upgrade"  # Quick snapshot with label
```

## `hermes import`

```bash
hermes import <zipfile> [options]
```

Restore a previously created Hermes backup into your Hermes home directory. All files in the archive overwrite existing files in your Hermes home; `--force` only skips the confirmation prompt that fires when the target already has a Hermes installation.

| Option | Description |
|--------|-------------|
| `-f`, `--force` | Skip the existing-installation confirmation prompt. |

:::warning
Stop the gateway before importing to avoid conflicts with running processes.
:::

**Exit status:** `1` when the archive is damaged — before anything is written, every member is decompressed once and its CRC checked; if any fail, the command prints `Error: backup archive is damaged (N member(s) …)` with the offending members and stops with the Hermes home untouched. Also `1` when any file from the archive could not be restored (listed under `Warnings (N files skipped)` and summarised as `Import incomplete: …`). The files that did land stay in place, but a script or the dashboard will not report a partial restore as success. Runtime files the import deliberately keeps from this machine (`gateway.pid`, `gateway_state.json`, …) and the older-backup session warning below do not change the exit status.

### SQLite databases

`.db` members (`state.db`, `kanban.db`, `response_store.db`, …) are not published with a rename like ordinary files. Renaming would replace the file's inode while a gateway, dashboard, or WebUI process still holds the old one open: that process would keep reading pre-import pages and keep writing sessions nobody else can see, and those sessions would simply be absent from the database everyone opens next — with nothing logged. Instead the imported pages are written **into the existing database file**, the same way `/snapshot restore` does it, so every open connection converges on the imported data.

If the live database cannot be replaced safely — the page copy failed *and* another process still holds the file open — the import leaves that database untouched and lists it under `Warnings (N files skipped)`. Stop the holding processes and re-run.

Importing an older backup over newer work is still allowed, but it is no longer silent. When the imported `state.db` holds fewer messages than the one it replaced, the summary reports it:

```
  ⚠ Session data replaced by older backup contents:
    state.db: 12 session(s) / 8912 message(s) -> 3 / 24
    Anything recorded after the backup was taken is not in it.
    Recover from a newer backup or snapshot: hermes snapshot list
```

### Examples
```bash
hermes import ~/hermes-backup-20260423.zip           # Prompts before overwriting existing config
hermes import ~/hermes-backup-20260423.zip --force   # Overwrite without prompting
```

