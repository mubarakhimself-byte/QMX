# 62. Local first: the design

Written 2026-10-26 by the local-first architect. Rulings 105 to 145 of file 26 bind, the latest winning; rulings 136 to 145 drive this. Inputs: `62a-local-first-rubric-walk.md` (the walk of every system, the messy files, the no-server first boot, the UI's compute places), `62b-local-first-research.md` (patterns, folders per OS, versions, local backups, OpenObserve and Hindsight on Windows), `61-server-substitute-and-wu9b.md` section D (gaps G1 to G12). Code truth is `build/wu9` at `d7391716` in `D:/QMX-worktrees/bld-wu9` (equal to `engine/base` `d82be318` apart from merges); the UI design is `ui-review/repair`, read for intent only. The three spines were amended in place with the `bmad-architecture` skill in amend mode (section I). Nothing was committed or pushed, and no file under `~/.qmx`, Documents, `DATA_NARL`, a vault or a keyring was read.

## H. In plain words (for him)

- **Your data gets one folder of its own.** It is called `QMX`. On your PC it goes on the drive with the most free room, so `D:\QMX` today (your C: drive is short of space). You can pick another place on the first start and move it later in Settings.
- **The folder is yours, not the program's.** Uninstalling QMX, installing it again, or a release that goes wrong never touches it. A new install finds it and carries on where you left off. Everything inside is in open formats: plain folders, JSON, TOML, Markdown, SQLite and Parquet.
- **The folder has five parts, each with one job.** `data` is your work. `keys` holds the few key files that are not in Windows' password safe. `backups` holds quick-undo copies. `cache` holds things QMX can make again (program pieces, downloaded model files, work folders of running jobs); deleting it loses nothing. `logs` holds QMX's own diary. A small label file at the top says "this is a QMX folder, version 2".
- **Nothing is written all over your PC any more.** The stray folders found today (`.qmx.zones`, `.pg0`, `.hindsight`, caches in your profile, a `qmx-home` folder wherever a command was typed) all move into the QMX folder or go away. The only things outside it are your keys in Windows' password safe, one small note in your user settings that says where the QMX folder is, and the program itself.
- **Versions are checked, never guessed.** A newer QMX upgrades the folder after it backs it up first. An older QMX that finds something it does not understand says so by name and which version you need. Going back one release always works.
- **QMX backs itself up.** Every hour it keeps a quick-undo copy in the folder, and every day it copies everything to a second drive you choose. Old copies are thinned out on their own. Restoring is a button on the start screen, and it works even when the folder will not open. Your keys can go into a sealed copy that only your passphrase opens.
- **"On this PC" or "on a server" is one choice everywhere.** This PC is always the first choice and the default. A server you add later appears in the same list beside it, wherever work or data can live in either place: a workflow, a dataset, a broker sign-in, the deep logs, a backup. Every run says where it ran.
- **The first start needs no server.** QMX starts on your PC, brings in your old data safely (the old folder is left exactly as it is), and works fully. Adding a server comes later, when you want one, and the copilot walks you through it step by step.
- **The trading node stays the one thing whose natural home is a server.** It can still run on your PC. Units, not bots, run there; that design belongs to the unit and trading-node sessions.

## A. The QMX folder

### A1. Where it lives

| System | Default offered at the first start | He may choose | Never |
|---|---|---|---|
| Windows | `<drive>:\QMX` on the fixed local drive with the most free space when that is not C:, else `%USERPROFILE%\QMX`. On his PC today: `D:\QMX` (C: had 22.4 GB free, D: 65.4 GB on 2026-10-24) | any local fixed-drive folder | inside `%LOCALAPPDATA%` or `%APPDATA%` (Velopack and Squirrel delete `%LOCALAPPDATA%\<packId>` on uninstall; MSIX redirects and deletes AppData writes), inside the program's install folder or the git checkout, on a network drive (SQLite's WAL needs a local disk), inside a OneDrive, Dropbox or Google Drive folder (a live-synced database corrupts; Anki and Obsidian say the same) |
| Linux desktop | `~/QMX` | any local folder, `$XDG_DATA_HOME/qmx` if he wants it hidden | the same list |
| macOS | `~/QMX`, offered at setup so the user chose it (Apple bars writing to user folders unasked) | any local folder | the same list |
| A server QMX sets up | the path setup writes into the host's unit (today `/srv/qmx/home/.qmx`, built by WU9) | set by setup only | — |

The first-start card refuses the "never" places by name and warns for a removable drive. The program's own install tree and its webview profile live wherever the installer puts them; nothing in them is data. Two rules bind the installer the desktop packet chooses (engine AD-48 Deferred): it is not a virtualized MSIX package, and its package id is not `QMX` while anything QMX writes lives under `%LOCALAPPDATA%\QMX`.

### A2. The pointer

A small config file says where the folder is, the way Obsidian's global folder lists vaults and Firefox's `profiles.ini` lists profiles.

| System | Pointer file |
|---|---|
| Windows | `%APPDATA%\QMX\home.toml` |
| Linux | `$XDG_CONFIG_HOME/qmx/home.toml` (`~/.config/qmx/home.toml`) |
| macOS | `~/Library/Application Support/QMX/home.toml` |

```toml
home = 'D:\QMX'
recent = ['D:\QMX']
```

The same folder holds the PC's recovery twin, `bin\qmx-recover.ps1`, and its `recover.conf` (one block per server: SSH target and key path, no secret), moved out of the data folder (62a row "the recovery script"). The host rewrites the twin on start when its version differs.

**One resolver, every entry point** (62a gap L9). In order: the `--home` flag; `QMX_HOME`; the pointer; the default path of A1 if it holds `qmx-home.toml`; then each fixed drive's `<drive>:\QMX\qmx-home.toml`. If none is found, the desktop app shows the first-start card (section F) and every command line program refuses with one line ("no QMX folder found: start QMX once, or pass --home"). Nothing ever creates a folder implicitly: not in the current folder (`./qmx-home` from `qmx node setup`, `pair`, `vault install`, `C/node.py:857,874,898`), not in temp (`python -m qmx_engine` with no `--home`, `E/__main__.py:133`), not at `Path.home() / ".qmx"` (five places, 62a section B). A test or lane creates one only with `--home <path> --create`. A lost pointer loses nothing: the scan finds the folder, and the card offers "Open an existing QMX folder".

### A3. The tree

`<QMX>` is the folder. What every package calls `home` in code today is `<QMX>/data`, so the packages' own paths inside it keep their names; only what is not data moves out. Formats: TOML, JSON, JSONL, Markdown, SQLite, Parquet, raw blobs, plain text, and one PostgreSQL data folder.

```
<QMX>/
  qmx-home.toml                TOML     the label: home id, format version, store versions (section B)
  README.txt                   text     plain words: what this folder is, which parts are safe to delete
  data/                        his data; backed up whole except the exclusions in C1
    settings.toml              TOML     every setting the UI edits, the place list and [telemetry] included
    observers.json             JSON     observer tokens by hash, never the token (AD-69)
    profiles/                  TOML     the model registry rows he edits
    slots/                     Markdown his prompt slot texts (methodology/general.md and the like)
    claude/                    the plan chats' CLI home: projects/*/<chat>.jsonl transcripts (his chats);
                                        .credentials.json is the plan login, the one secret file in data/
    claude-relayed/            the key chats' CLI home; projects/ is a junction to claude/projects
    chats/<id>.json            JSON     one record per chat; chats/<id>/ holds the launch files rebuilt per launch
    runs/<id>/journal.jsonl    JSONL    one usage journal per chat (a chat's, not an engine run's)
    exports/<chat>-<stamp>/    Markdown, JSON  chat exports he asked for
    agent-memory/<slug>/       Markdown the CLI's auto memory per working folder
    workspaces/                folders  his and the agents' working folders; wf-<id>/ per workflow
    library/                   the Library store as built: objects/ blobs/ refs/ edges/ annotations/
                                        kinds/ (JSON, JSONL, raw bytes); catalog.db (SQLite index,
                                        rebuildable); checkout/ (working copies, AD-20); uploads/ (partials)
    market/                    Parquet  price partitions <source>/<subject>/<kind>/<variant>/<year>/<month>,
                                        the open month as open.parquet; SQLite metadata; .staging/ for commits
    memory/                    SQLite   the built-in recall index (FTS5) and the snapshot slot
    memory/hindsight/pg/       Postgres Hindsight's database (PostgreSQL 18 + pgvector through pg0); an index
                                        of Library rows, rebuildable but slow, so backed up by dump (C1)
    engine/engine.sqlite       SQLite   the run ledger: events, memos, spans, triggers, fires, wakes
    engine/inbox.sqlite        SQLite   inbox and incidents
    engine/runs/<run>/         JSON, JSONL  the frozen workflow copy and trace-<seq>.jsonl of each run
    control.db                 SQLite   the control plane
    runs.db                    SQLite   the run index
    apps.db                    SQLite   mini apps
    apps/<id>/{data,blobs,road}/        each mini app's own volume
    portfolio.db               SQLite   broker portfolio reads
    backtests/<ref>.json       JSON     recorded backtest run configurations (until they become Library items)
    node/                      folders  a trading node's state when he runs one on this PC (QMN's rooms,
                                        state, evidence, staging, archive; the trading-node session's layout)
    migration/                 JSON, SQLite  switch reports; pre/ and retired/ (the old library.db, read only)
  keys/                        secret files; never in a plain backup, only in the sealed key copy (C4)
    pairing-key                bytes    this home's pairing key (or run-pass-key before pairing)
    vault.key                  bytes    this machine's vault key (was the nested <home>/.qmx/vault.key)
    vault-store.json           JSON     sealed key copies for servers (ciphertext)
    tokens.json, control-token          on a server only (Windows keeps both in Credential Manager)
    revoked.json               JSON     the revocation list of run passes (was passes/revoked.json)
  backups/                     quick-undo snapshots on this drive (C2) and backups.jsonl, the backup log
  cache/                       rebuildable; delete any time with QMX closed
    machine.toml               TOML     this machine's id and the home id; a mismatch empties cache/ at start
    plugins/                   program  materialised pack plugins (was plugins/)
    envs/<hash>/               program  mini apps' uv environments (was environments/)
    apps/                      program  app definition images (was definitions/), road-locks/, network/, replicas/
    models/                    files    HF_HOME, TORCH_HOME and the other model caches: Hindsight's embedder and
                                        reranker (was memory/hindsight/hf/), Docling's and torch's downloads
    pg0/                       program  pg0's unpacked PostgreSQL binaries (was ~/.pg0/installation)
    zones/<run>/{code,work,attempts}/   each run's working zone (was ~/.qmx.zones)
    market-handles/            Parquet  materialised big-read handles (was market/handles/)
    openobserve/               program + data  the local deep log viewer when he turns it on (E1)
    run/                       pid files (was procs/), probe results (was state/), hub.port, the host's port
  logs/                        text, JSON  host.log (was control.log), the live readings the LOGS constant names
                                        (heartbeat, connection, feed, telemetry), hindsight/ (was ~/.hindsight),
                                        otlp/ when telemetry writes files; rotated, 30 days by default, not backed up
```

**Data, config, state, cache, secrets.**

| Class | What | Where | Backed up |
|---|---|---|---|
| Data | everything he made or QMX made for him: the Library, prices, chats and transcripts, the ledger, memory, apps' volumes, settings | `<QMX>/data/` | yes, every snapshot (C1) |
| Config: his | settings, place list, profiles, prompt slots | `<QMX>/data/` (they are his choices) | yes |
| Config: where the folder is | the pointer and the recovery twin's conf | the per-OS config folder (A2) | no (rebuilt by the scan) |
| State | logs, live readings, pids, ports, work zones of running jobs | `<QMX>/logs/`, `<QMX>/cache/run/`, `<QMX>/cache/zones/` | no |
| Cache | program pieces and downloads QMX rebuilds from a definition or a URL | `<QMX>/cache/` | no |
| Secrets | provider keys, read and data keys, the control token, tokens of connections homed here | Windows Credential Manager `qmx/*` (ruling 116), `<QMX>/keys/`, `data/claude/.credentials.json` | only in the sealed key copy (C4); the plan login and connection tokens never (he signs in again) |

The cache sits inside the QMX folder, on the drive he chose, not on C:, because its bulk (model files, environments, work zones, the deep log viewer's window) would fill a small system drive. It is stamped with the machine, so a folder carried to a new PC rebuilds its cache instead of running another machine's environments.

**Program pieces go to `cache/`, never to `data/`.** Mini apps' environments, materialised plugins, app images, pg0's binaries and model downloads are rebuilt from their locked definition or URL on demand; a cache entry whose digest or Python differs is rebuilt. The program itself (the install tree, or today the git checkout and its `.venv`) is never inside the QMX folder.

**Script children's caches** (62a section C row 6): a script node's environment gains `HF_HOME=<QMX>/cache/models/huggingface`, `TORCH_HOME=<QMX>/cache/models/torch` and `XDG_CACHE_HOME=<QMX>/cache/models/xdg`, so Docling, torch and pip downloads stop landing in his profile. `TEMP` stays the OS temp folder: QMX's own scratch there (`qmx-merge-*`, `qmx-backup-*`, `qmb-*`, `qml_*`) is cleaned on exit and stays scratch.

**Memory inside the folder** (62b section 6): QMX starts pg0 itself with `data_dir=<QMX>/data/memory/hindsight/pg` and its binaries under `cache/pg0/`, and hands Hindsight `HINDSIGHT_API_DATABASE_URL`, because Hindsight's own pg0 wrapper passes no data folder (`QA/qmx-memory/src/qmx_memory/hindsight.py:82`, `db_url = "pg0"`). Hindsight's own log folder is pointed at `<QMX>/logs/hindsight/`; probe P-HSDIRS confirms the setting name, and if none exists the host starts Hindsight with its `HOME` set to `<QMX>/cache/hindsight-home/`.

**The work zones** (62a gap L5): `zones_root` becomes `<QMX>/cache/zones`. The built guard (`E/workers/zones.py:82-89`: never the home, inside it or above it) holds unchanged against `<QMX>/data`, which was run: the proposed root passes it (section J, fact 2). `home_of(work)` (`zones.py:92-96`, used by three template scripts, `a-fill-the-library` and `ask-the-panel`) derives the home by stripping `.zones` and returns the wrong folder for the new root (section J, fact 3); it becomes "walk up to the folder holding `qmx-home.toml`, return its `data/`", until a `library` node serves those templates `engine_view`. A trained model leaves the zone as a Library `model` item with its weights as a blob (Lab AD-20), so retention can prune zones freely.

### A4. The UI's settings

The UI design keeps settings in the browser's `localStorage` in nine files (62a section A1). In the desktop app that storage sits in the webview's profile under the installer's folder, which an uninstall deletes. When the UI is wired, every setting it keeps goes through the host into `data/settings.toml` (`[ui]` for theme, layout defaults and the demo switch); the webview keeps only view state (an open tab, a column width).

### A5. Every messy file and where it goes (ruling 143)

| Messy file today (62a section C) | Where it goes |
|---|---|
| `~/.qmx.zones/` beside the home | `<QMX>/cache/zones/` |
| `~/.pg0/instances/hindsight` | `<QMX>/data/memory/hindsight/pg/` (rebuilt from Library rows at the switch; the old instance is left for him to remove) |
| `~/.pg0/installation` | `<QMX>/cache/pg0/` |
| `~/.hindsight/` | `<QMX>/logs/hindsight/` |
| `%TEMP%/qmx-engine-*` homes | gone: the engine CLI uses the resolver and refuses without a folder |
| `%TEMP%` scratch (`qmx-merge-*`, `qmx-weekly-*`, `qmx-backup-*`, `qmb-*`, `qml_*`) | stays OS scratch, cleaned on exit (allowed) |
| `~/.cache/huggingface`, profile caches from script children | `<QMX>/cache/models/` through the child's environment |
| `%LOCALAPPDATA%/uv` | stays: uv's own shared cache and Python installs, like pip's, documented |
| `~/.config/systemd/user/` chat memory slice (Linux) | stays: system config by design |
| Windows Credential Manager `qmx/*` | stays: by design (ruling 116) |
| `./qmx-home` in the current folder | gone: `qmx node setup`, `pair`, `vault install` use the resolver |
| Browser `localStorage` settings | `data/settings.toml` through the host (A4) |
| Old ticks in `C:/Users/Mubarak/Documents/QMX/data/raw/...` (ruling 130) | imported into `data/market/` after the first start (F step 11); the original is left untouched, and removing it stays his call (funnel Q4) |
| Server folders `/srv/qmx/*`, `/var/lib/qmx/*`, `/etc/qmx/*`, `/var/lib/qmx-observability`, `/var/lib/qmx-recover` (two server homes side by side) | stay as built for now; folding `/var/lib/qmx` into the one server home is in the stand-in round (Library Deferred) |
| Hard-coded `D:/QMX-worktrees/qma-ship/...` paths in live lanes | test evidence only; lanes take `--home` (BACKLOG) |
| Repo-relative `out/`, `data/` from test scripts | BACKLOG: write under the lane's home |
| `.svelte-kit/`, `.vite/`, `evidence/`, `workroom/` in the checkout | dev clutter in the program folder, not data; `.gitignore` (BACKLOG) |
| `environments/`, `plugins/`, `definitions/`, `road-locks/`, `network/`, `replicas/` inside the home | `<QMX>/cache/` (A3) |
| `<home>/.qmx/vault.key` (a `.qmx` inside `.qmx`) | `<QMX>/keys/vault.key` |
| `<home>/vault/*`, `vault-store.json`, `passes/revoked.json` | `<QMX>/keys/` |
| `<home>/bin/qmx-recover.ps1` and its conf | the pointer's config folder (A2) |
| `control.log`, `logs/` | `<QMX>/logs/` |
| `procs/`, `state/`, `hub.port` | `<QMX>/cache/run/` |
| `telemetry.json` | `[telemetry]` in `data/settings.toml` |
| `weekly-backup.json` and `.lock` | `<QMX>/backups/backups.jsonl` |
| `%LOCALAPPDATA%\QMX\qma-daemon` (62b) | no longer written: `qma-daemon` is deleted on `engine/base` (no `LOCALAPPDATA` path to it in the code); a leftover folder is listed for him by the first start |

No production code writes into the git checkout at run time (62a), so the program folder needs no change.

## B. Versions

### B1. The label at the top

```toml
format = "qmx-home"
format_version = 2          # 0 = the old layout (library.db), 1 = today's flat ~/.qmx, 2 = the QMX folder
home_id = "0193..."         # UUIDv7, minted once; backups and servers name the home by it
created_by = "0.9.0"
last_written_by = "0.9.0"

[stores]                    # version and min_reader per store; a cache of the truth below
library    = { version = 1, min_reader = 1 }
market     = { version = 1, min_reader = 1 }
engine     = { version = 4, min_reader = 3 }
inbox      = { version = 1, min_reader = 1 }
control    = { version = 1, min_reader = 1 }
runs_index = { version = 1, min_reader = 1 }
apps       = { version = 1, min_reader = 1 }
portfolio  = { version = 1, min_reader = 1 }
chats      = { version = 1, min_reader = 1 }
settings   = { version = 1, min_reader = 1 }
memory_fts = { version = 1, index = true }
catalog    = { version = 1, index = true }
hindsight  = { version = "1.1.0", postgres = 18, index = true }
```

**Where the truth lives.** A SQLite store's own file is the truth: `PRAGMA application_id` (one QMX id, so tools recognise the file), `PRAGMA user_version` for the version, and a `qmx_meta` row for `min_reader` (the engine keeps its built `meta` table and adds the `min_reader` key). A store of plain files (the Library, the market layout, chats, settings) keeps its version in the label. When the label and a file disagree, the file wins and the label is rewritten. Library kinds keep their own `schema_version` and the refusal by kind of Library AD-14.

`min_reader` is the oldest store version whose code can still read and write this store safely. A step that only adds (a nullable column, a new table, a new optional field, a new folder) leaves it; a step that changes what existing data means raises it.

### B2. Open, migrate or refuse

For the folder (`format_version`) and for each store, in this order:

1. **Same version:** open.
2. **The store is older:** take the pre-migrate snapshot (B3), then run the forward steps one at a time, each in its own transaction, then write the new version. A step that fails rolls back its own transaction, and the store stays at the last good version with an incident naming the step.
3. **The store is newer, and `min_reader` is at or below this release's version:** open normally. Unknown optional fields, tables and folders are kept as they are and never deleted; the settings writer preserves unknown keys and sections word for word, so an older release cannot drop what a newer one added.
4. **The store is newer, and `min_reader` is above this release's version:** refuse by name: "This QMX folder's run ledger was written by QMX 0.11 (ledger version 7). This QMX reads version 5 or older. Install 0.11 or newer, or restore the copy taken before the upgrade." The Library and the market store open read-only instead, because their files are open formats the older reader understands as far as it goes. Every other refused store stays closed, and the parts of QMX that need it say why.
5. **An index never refuses** (`catalog.db`, the FTS5 recall index, Hindsight's database): a version it cannot open is rebuilt from evidence, or bypassed while it rebuilds (memory answers from the built-in FTS5 adapter, engine AD-18).

Today's engine refuses any newer ledger, even one changed only by an additive step (`E/ledger/migrations.py:100-103`; run in section J, fact 4); step 3 is the change.

### B3. Backup before every migration

Before any step of rule 2, and before a switch, an import, a restore or a move of the folder, QMX takes a **pre-change snapshot** in `backups/` (C2) of every store about to change, named `pre-<what>-<from>-<to>-<stamp>`. It is kept until the next daily second-drive copy succeeds and then for 30 more days, and it never counts against the hourly rotation.

### B4. Going back to an older release (62a gap L10)

- **Expand, then contract.** A release that needs a meaning change ships it in two releases: the first writes both the old and the new form and leaves `min_reader` alone; the next stops writing the old form and raises `min_reader`. So **the previous release always opens a folder the current release wrote**, and a broken release can be rolled back one step with nothing lost. The installer keeps the previous version for that rollback (engine AD-48).
- **Two or more releases back,** a store may refuse by rule 4. Then the startup card offers the pre-upgrade snapshot (B3) with a plain list of what returning to it loses (runs, items and chats since that time, counted), or read-only browsing of the Library. There is no silent downgrade and no backward migration.
- Rollback on a server stays `qmx-recover rollback` (engine AD-71), under the same rules.

## C. Local backup

### C1. What

Everything in `data/`, except:
- `library/catalog.db` and the FTS5 recall index (rebuilt from evidence on restore);
- `library/uploads/*.part`, `market/.staging/`, `chats/<id>/` launch files, lock files, SQLite `-wal` and `-shm` files (each SQLite file is copied whole by `VACUUM INTO`, which is consistent while QMX runs);
- `claude/.credentials.json` and `claude-relayed/.credentials.json` (the plan login; he signs in again on a new PC);
- Hindsight's live Postgres files: the database is copied by `pg_dump -Fc` when pg0's bundle carries `pg_dump` (probe P-PGDUMP), otherwise by stopping Hindsight for the moment of the copy and copying the folder. Either way, losing it costs only a rebuild from Library rows.

Immutable files (Library objects and blobs, frozen price partitions) are copied once by hash and never again; append-only logs (`refs/log.jsonl`, `edges/*.jsonl`) are copied up to their last full line; mutable files are copied whole.

### C2. When, and where

| Copy | Where | When | Kept (Settings, Data and backups) |
|---|---|---|---|
| **Quick undo** | `<QMX>/backups/` on the same drive | every hour while QMX runs and something changed; before every migration, switch, import, restore or folder move | every hourly copy for 48 hours, then one a day for 7 days; pre-change snapshots as B3 |
| **Second drive** | a folder on another drive he picks, `<target>/QMX-backup/<home_id>/` | once a day (03:00 by default; if the PC was off, at the next start or wake; and on closing QMX when the last copy is over a day old); before every migration | 14 daily, 8 weekly, 12 monthly |
| **Off-site, optional** | a server he added, a bucket, or a private GitHub repository | the server and the bucket daily after the second-drive copy; GitHub weekly | per target |

A quick-undo snapshot holds only the mutable files and a list of the immutable ones by hash, because those already sit unchanged in the live store; it is small and fast, and it undoes a bad edit or a bad migration. It does not survive a dead disk, which is the second drive's job (62b: Anki, Zotero and Obsidian all say a same-disk copy and a sync are not backups).

**The second drive's layout** works on any filesystem, NTFS, exFAT on a USB disk included, with no hard links:

```
<target>/QMX-backup/<home_id>/
  backup.toml                  which home, its label at the last copy, the last result
  pool/ab/cd/<sha256>          every immutable file once
  snapshots/<UTC stamp>/
    manifest.jsonl             one line per pooled file: path, sha256, size
    files/...                  the mutable files copied whole (SQLite by VACUUM INTO), the memory dump
```

Thinning deletes snapshot folders; a sweep then removes pool files no snapshot lists. Before a copy the free space on the target is checked against what the copy needs, and a full target refuses whole with an inbox task, never a half snapshot.

**The default target** is the largest fixed drive that is not the QMX folder's drive (61 gap G7): on his PC, with the folder on D:, that is a folder on C: (`C:\QMX-backup`) until he names a better one such as a USB disk. While no second drive is set, the start screen and the data health read say so in plain words ("your work has no copy on another drive"). A PC with one drive gets the same warning and the offer of a USB disk or an off-site target.

### C3. Restore, in plain words

- From the start screen ("Restore from a backup"), which works even when the folder will not open, or from Settings, Data and backups.
- He picks a copy by date. QMX closes its stores, moves the current `data/` aside into `backups/before-restore-<stamp>/` (never deleted by QMX), rebuilds `data/` from the copy, checks every hash, rebuilds the indexes and opens.
- After a restore, copying to and from any server stays paused until he presses "carry on". A server that holds newer saves than the restore shows them first ("your server has 37 saves newer than this copy: bring them back?"), and bringing them back is Library AD-14's `adopt`; nothing a server holds overwrites the restore on its own.
- **Restore on a new PC:** install QMX, choose "Restore from a backup" on the first-start card, point it at the second drive, then open the sealed key copy with his passphrase (C4) and sign in to the plan and to broker connections again.
- **Drill, without him:** once a month QMX restores one random snapshot into `cache/restore-drill/`, checks every hash and row count, and writes the result into the data health read; a failed drill is an incident.

### C4. The sealed key copy

Keys that would make a new PC a re-entry, not a restore (62a row "router and providers"): the static `qmx/*` entries in Credential Manager (model, read and data keys) and the files in `keys/` except `tokens.json`. When he sets a passphrase in Settings, QMX derives a key pair from it (Argon2id), keeps only the public half, and seals every key copy to it, so the daily backup needs no passphrase; opening the copy needs it. Off until he sets one; while off, the Data and backups page says keys are not in the backup. OAuth tokens and live-trading keys are never in it (Library AD-12, ruling 135): those connections are signed into again on their home.

### C5. What the GitHub backup becomes

The weekly snapshot to a private GitHub repository (`C/backup.py`, `T/backup-weekly`) stops being QMX's backup. It becomes one optional off-site target kind, off by default: settings, profiles, prompt slots and his published definitions (workflows, skills, mini apps, methodologies, as their JSON), weekly, never a key, a chat or a blob. Its bare-repository-as-dry-run quirk (`C/backup.py:68-77`) retires with it. The `backup-weekly` template becomes the `backup` script workflow, which runs every target of C2 on its own schedule.

## D. "On this PC" or "on a place": one concept

### D1. The words

- **This PC**: the machine where the QMX folder lives. Built in, cannot be removed, always the default.
- **Place**: anywhere else QMX may run work or keep a copy: a server he owns (Contabo), a rented GPU, an agent host (Amp, Cloudroom), a serverless runner (E2B, Modal), another QMX machine, a bucket. In the UI the list is "Machines" (Settings, Servers and data); in code it is the placement registry (engine AD-30).
- **Run** and **keep**: what a place can do. This PC and a server do both; a rented GPU only runs; a bucket only keeps.
- **Stand-in**: a place that keeps a job going while This PC is off and hands it back (the later stand-in round, 61 section D).
- **Copy**: what a place keeps. This PC holds the main copy of everything; a place holds copies.
- **Home of a connection**: the one machine that holds a sign-in and opens its sessions (engine AD-67). This PC by default.

The second drive is not a place: it is a backup target on This PC (C2).

### D2. The model

- **One list.** `[placements]` in `data/settings.toml`. `pc` is built in. Every other row is one he adds, under a name he chooses, with `kind`, `can = ["run", "keep"]`, its adapter, relay mode and `link_out` (engine AD-30). No row ships as a default: the `placement.contabo.*` defaults on every PC (`E/settings.py:134-138`) go, and a new row takes its kind's defaults when he adds it. A row has a stable `id` as well as its name, so renaming a place keeps its history.
- **Per job.** A workflow has a default `runs_on` (`[pc]` unless he sets it) and a node may override it (built). A trigger has one `home_engine`: the place whose engine fires it, `pc` by default; with no server, everything is homed on This PC. "When this PC is off, run on" names a stand-in, built in the stand-in round. A job never needs a place to exist: a list with no healthy place but This PC runs on This PC; a node that names only a missing place waits `placement` with one line.
- **Per dataset.** A dataset card's annotation `keep_on` (Library AD-10) lists places that also keep a copy of its partitions; This PC always keeps the main copy. Freeing This PC's copy of a dataset is a per-dataset choice he makes, possible only when two places hold verified copies, off by default.
- **Per connection.** A connection's home (engine AD-67) is `pc` unless he moves it to a place.
- **Per service.** Monitoring's target (engine AD-69), memory's place (engine AD-18), the central relay (engine AD-28) and each off-site backup target name a place from the same list.

### D3. What the ledger records

Every node attempt and every `workflow-run` object records `place` (the name at the time), `place_id`, `machine` (the device name, engine AD-30), and `placed_by: default | chosen | spilled | stand_in`. A run card reads "Ran on This PC" or "Ran on contabo, standing in". The ledger's `CHECK (home_engine IN ('pc', 'contabo'))` (`E/ledger/migrations.py:36,59`) refuses any other name today (run in section J, fact 5); a forward step rebuilds the `triggers` table without it, the service checks names against the place list when it writes, and a trigger whose place was removed reads `blocked_config` ("the place 'x' was removed"). `E/definition/validate.py:29` checks against the list, not a fixed set; `H/host.py:879-883` stops naming a nameless non-PC host `contabo`: a host started with `--role node` must be given `--place <name>` by setup.

### D4. Every system: the local default, the place option, the screen

The 29 systems of 62a plus the two scripts it also walked. Screens are on `ui-review/repair`, `apps/qmx-ui/src/`; **missing** names a screen or control the UI session must add (handoff list in section G).

| System | On This PC (default) | On a place (option) | Where he chooses |
|---|---|---|---|
| Copilot and harness | chats run in the host on This PC | an agent node placed on a place runs its own harness there (engine AD-20) | Copilot work area shows where each job runs (`lib/copilot/WorkArea.svelte`; text fix: jobs run on This PC unless placed) |
| Router and keys | This PC's relay, keys in Credential Manager | a place's own relay, or the central relay on a place he marks | Settings, Models and tools; relay per row on the Machines list |
| Memory (Hindsight) | on This PC, database in `data/memory/hindsight/pg` | a server runs its own only for work placed there, off by default (`[memory] hindsight`) | **missing**: Settings, Copilots, a "Memory" row (engine, where it runs, rebuild) |
| The UI | the desktop app on This PC | never (no web version, ruling 32) | none |
| The Lab | runs start on This PC | any run placed on a place | Lab machine picker, Compute panel, New… "Where it runs" (exist); the sweep dialog's default changes from `vps-fsn` to This PC |
| Pods (not built) | a pod's home is This PC | a place | Portfolio kill grid: **missing** a "This PC" column (`KillMatrix.svelte`) |
| Mini apps | local processes on This PC | an app's home on a place (engine AD-64) | Mini apps page: "Runs on" is display only; **missing** a picker |
| Workflows | `runs_on [pc]`, triggers homed on This PC | per node `runs_on`; a stand-in later | Lab New… "Where it runs" (exists); **missing** on a workflow's own page: "Runs on" and "When this PC is off" on the trigger card |
| Templates | every template defaults to This PC | `run-on-a-machine` asks which place | Workbench guided start (exists) |
| Market-data door | This PC's store is the main copy of every partition | a place's door serves the copies kept there | **missing**: "Kept on" on a dataset's Library page |
| Downloaders | on This PC, into `data/market` | placed on a place (stand-in later) | Settings, Servers and data, Data sources: **missing** "Runs on" and "Kept on" |
| Old-ticks import | into This PC's store | a place gets a copy only for work placed there | the first-start card and Data and backups: **missing** "Bring in old data" |
| QMB backtests | the door on This PC | a QMB machine he adds, as capacity | Lab run dialogs (exist) |
| QML | in process | — | none |
| Trading node | can run on This PC (state in `data/node/`) | a trading server, its natural home (ruling 140) | Portfolio trading servers (exists, "set up from Settings, Compute" becomes "Servers and data"); Settings, Brokers and accounts |
| MIS (later) | trains on This PC | a training place | Lab Training panel (exists) |
| ML training | This PC's GPU slot | a rented GPU place reading through a door | Lab Training panel, guided start "Where should it train?" (exist) |
| Extraction (Docling) | a workflow on This PC | placed on a place for a big batch | **missing**: "Runs on" in a source's settings (Data sources) |
| Internal health and logs | on This PC always | each place's health reaches This PC by its heartbeat | Workbench status bar, doctor (exist) |
| OpenTelemetry collector | none needed: QMX's exporters send straight to the local viewer | a place's collector when that place is the target | **missing**: Settings, Developer, "Deep logs" |
| OpenObserve (deep logs) | off; "On this PC" runs it locally | "On a server" sends to that place | the same "Deep logs" control |
| Backups | quick undo here, the second drive | a server, a bucket or GitHub as off-site copies | **missing**: Settings, You, a "Data and backups" tab |
| Buckets | none | a place that keeps copies | Machines "Add machine", storage bucket (exists); "Kept on" (missing, above) |
| The Library | This PC is primary (`[library] primary = pc`) | places keep copies of what their work needs | the item page header shows where its bytes are (Library AD-33); "Kept on" (missing, above) |
| The Library Hub | none on This PC (the port is in-process) | runs on each server | the Machines row's health |
| Sync | none without a place | per server, This PC never waits | the Machines row (sync lag) |
| Vault and keys | Credential Manager and `keys/` | sealed copies to places by allow-list (engine AD-28) | Settings, Models and tools; the sealed key copy on Data and backups (missing, above) |
| Connections and brokers | each sign-in's home is This PC | moved to a server so it reads while This PC is off | Settings, Brokers and accounts: "tied to the server" becomes **missing** "Signed in on: This PC / <place>" |
| Feeds | on This PC | placed on a place (stand-in later) | Data sources (missing choice, above) |
| Remote placements | none | each place he adds | Machines list, "Add machine" (exists); **missing** the copilot's "Help me add a server" entry (F3) |
| Recovery script | the twin in the pointer's folder | `qmx-recover` on each server | **missing**: a "Recovery" line on each Machines row, with the command to run |

Screens that must stop assuming a server (62a section F): Copilot work area and How do I ("running on your servers"), the Library unit page ("Runs headless on the server" becomes "Runs where you place it"), the sweep dialog's `vps-fsn` default, Brokers and accounts' "tied to the server", and the Portfolio pointer to a "Settings, Compute" tab that does not exist.

## E. The changes that make each server-only and partial system local first

### E1. The six server-only systems

- **The collector and OpenObserve (monitoring).** Telemetry is off until `[telemetry] send_to` names a target: `off` (default), `this-pc`, or a place. The server's address leaves the code at all three sites (`QA/qma-harness/src/qma/harness/launch.py:404-414,562`, `E/telemetry.py:49`, `QA/qmx-memory/src/qmx_memory/hindsight.py:63,227`); a chat gets `CLAUDE_CODE_ENABLE_TELEMETRY` and an OTLP endpoint only from that setting, and Hindsight's tracing likewise. **On this PC:** at his click QMX downloads OpenObserve's Windows build (174.7 MB for 1.1.2, 62b) into `cache/openobserve/`, runs it under the host's supervision with `ZO_DATA_DIR=<QMX>/cache/openobserve/data`, `ZO_HTTP_ADDR=127.0.0.1`, `ZO_TELEMETRY=false`, `ZO_MEM_TABLE_MAX_SIZE` 256 MB, `ZO_DISK_CACHE_MAX_SIZE` 1 GB and retention from the Settings window (7 days), with its root password generated and kept as `qmx/openobserve-root` in Credential Manager (never replicated). No collector runs on This PC: the in-process exporters and each chat send OTLP over HTTP straight to OpenObserve on loopback, because a collector's disk queue is for a network that sleeps, which loopback does not. **On a server:** as built (the collector over the tailnet, OpenObserve behind it). The internal layer never depends on either; the Library keeps every run's trace and logs (engine AD-69).
- **Buckets.** A bucket is a place that only keeps. This PC pushes to it directly with rclone (it runs on Windows), as an off-site backup target (C2) and for datasets that list it in `keep_on`. The remote runner's defaults `bucket: "vps:/srv/qmx/bucket"`, `root: "/srv/qmx/bucket"` and `default_target = "vps"` (`QA/qmx-remote/src/qmx_remote/models.py:103,123-124`) go. The server-to-bucket push of Library AD-16 stays for what a server made.
- **The Library Hub.** A server's role by nature. On This PC the Library port is in-process and no Hub runs. The standalone Hub's `primary` default becomes `pc` (`QA/qmx-hub/src/qmx_hub/server.py:969`), and the bootstrap stops writing `primary = "server"` (G12).
- **cTrader connections** (62a gap L1). A connection's home is `pc` when he names no other (`H/venue_session.py:68`). The refusals `pc_not_home`, `not_paired` and `waiting_for_server` for a PC-homed connection go (`:304-309,347`): This PC exchanges the sign-in code itself, keeps the tokens in Credential Manager as `qmx/token/ctrader-app`, and runs the one venue session. Ruling 135 holds unchanged: This PC holds read-only and demo sign-ins only; a sign-in whose accounts can trade live money still lives only on a trading server, and the "this key can trade live money" refusal stays. The one-home rule holds too: moving a connection's home to a server is a fresh sign-in on that server, after which This PC deletes its own tokens, because a refresh token cannot be copied without logging the other copy out. WU8's "the PC never stands in as home" rule was right for a world where the server was the home; with no server, This PC is the home, and there is only ever one.
- **Remote placements.** None by default. A job with no place runs on This PC; "configure the remote target in Settings first" appears only when he asked for a place that is not set up.

### E2. The eleven partial systems

- **The UI.** Settings through the host into `data/settings.toml` (A4); the first-start card (F); the missing screens of D4; the server-assuming texts fixed (D4, last paragraph). The UI session owns all of it.
- **The Lab.** The PC store is the main copy (the comment "materialises partitions into the PC cache", `C/lab.py:17`, is reworded); its data panel needs the door, which opens with WU11.
- **Templates.** Every template defaults to `pc`; `run-on-a-machine` (`T/run-on-a-machine/definition.json:24`) gets a `place` slot the guided start fills, This PC first.
- **The market-data door.** The `Placement` enum's "the server holds the main copy and is the primary" (`H/market_data.py:106`) gives way to the place names; a commit's `born_on` defaults to the host's own place (`pc` on This PC; `:495`, the HTTP body at `:953`); the door's `primary` follows `[library] primary` (WU11); the door opens without a holdout (WU11, ruling 137). A partition born on This PC is final at once; a partition born on a server stays pinned there until This PC has verified its copy (G2 reversed, Library AD-10 and AD-28).
- **The downloaders.** `[data] root` defaults to `<QMX>/data/market`, the same root as the host's door, so the step stops failing on a fresh folder; `placement` defaults to the host's place (`T/download-dukascopy/scripts/download.py:228-234`, `download-binance/...:157`, `download-ccxt/...:160`). The old-ticks import defaults to the resolver's folder and no raw backup (the original stays where it is): `--market` and `--raw-backup` (`scripts/data/import_old_ticks.py:771,781`).
- **QMB backtests.** The host binds the door on This PC by default; a QMB machine is a place he adds for capacity (engine AD-31). The door itself (PR 204's successor) belongs to the unit session (`QMB-BACKTEST-DOOR-HANDOFF.md`); this design only fixes where it runs.
- **The trading node** (the trading-node session's area; G11). When he runs a node on This PC its state folder defaults to `<QMX>/data/node/`, so his folder alone restores it; a node on a server sends its records home to This PC when it is up.
- **The MIS** (last, per his rulings). Its outputs land in the Library and its pins are read from the QMX folder, not from the checkout's `uv.lock` (`qmn/src/qmn/mis/regime_train.py:2075-2080`).
- **ML training.** `torch` becomes the optional "machine learning" part of the program (an extra of `qmx-engine`, installed from Settings with its size shown), so a fresh install can train once he turns it on; a template that needs it says so in preflight (`blocked_config`, one line) instead of failing to import. The trained model lands in the Library as a `model` item with its weights blob (Lab AD-20), not only in the zone (`T/d6-ml-training-run/scripts/train.py:38`).
- **Extraction.** Docling becomes the optional "documents" part the same way; the upload door starts `extract-source` (today nothing but the catalog calls it, `T/catalog.py:478-482`); it runs on This PC by default, its model downloads in `cache/models/`.
- **Backups.** Section C.

### E3. The YES systems with a messy file

- **Memory:** pg0's folders inside the QMX folder (A3).
- **Mini apps:** environments, images and runtime folders to `cache/` (A3).
- **Workflows:** zones to `cache/zones/` (A3); place names from the list (D3).
- **The vault:** `keys/` (A3); the sealed key copy (C4).
- **The Library:** a host refuses to start on a folder that holds `library.db` and no `qmx-home.toml`, and names the first-start card as the way to bring it in (62a gap L4).
- **The recovery script:** the PC twin in the pointer's folder (A2).

## F. The first start on a PC with no server

The program today is a git checkout and its `.venv` (the boot recipe in `WRAPUP-PLAN.md`); the installer comes with the desktop packet. The steps are the same either way.

1. **Get the program.** Clone, `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`. No server, no Docker.
2. **Start QMX.** The resolver finds no pointer and no folder, so the first-start card opens with three choices: "Make a new QMX folder" (pre-filled with A1's default and each drive's free space), "Open an existing QMX folder", "Restore from a backup". When it finds an old-layout folder at `~/.qmx` (a `library.db` and no `qmx-home.toml`), it adds "Bring in your old QMX data from `C:\Users\Mubarak\.qmx`" and pre-selects it.
3. **Make the folder.** QMX writes `qmx-home.toml` (format 2, a new `home_id`), `README.txt`, the five parts and the pointer. A free-space check comes first.
4. **Bring in the old data, safely** (62a gap L4). The old folder is never written:
   1. QMX checks that no QMX process holds `~/.qmx` and that the new drive has room for a copy.
   2. It lists every file of `~/.qmx` with its size and sha256 (`data/migration/old-layout-list.json`).
   3. It copies `~/.qmx` into the new `data/` (SQLite files through the backup API, the rest byte for byte) and checks every hash against the list. The untouched original is the backup.
   4. On that copy only, it runs the built switch (`scripts/data/switch_library.py`, `qmx_library.migrate.from_library_b.switch_over`): `library.db`, `artifacts.db` and `artifacts/` are frozen under `data/migration/pre/`, imported into `data/library/` with the known test junk filtered, verified by counts per kind, version chains, links, memo rows and blob hashes, and only then moved read-only to `data/migration/retired/`. A failed verification leaves the new folder unfinished and is reported; deleting it and trying again costs nothing, because the original is untouched.
   5. It writes the switch report and shows it in plain words (items per kind, what was filtered, what moved).
   6. It takes the first quick-undo snapshot, and once he names a second drive (step 5), the first second-drive copy.
   7. The old `~/.qmx`, `~/.pg0` and `~/.hindsight` stay as they are. The start screen offers to remove them once QMX has run on the new folder for a week; removing them is his click.
5. **The second copy.** The card proposes the default target of C2 and lets him pick another (a USB disk is better than C:). He may skip; the warning stays until he sets one.
6. **Sign in and add keys.** He signs in to his Claude plan once (`/login` in `data/claude`) and types provider keys in Settings, Models and tools, where they go to Credential Manager. No agent does this.
7. **The host starts** (`python -m qmx_host serve --role pc`, the folder from the pointer). It reads the label, checks every store by B2, takes the single-instance lock, makes the control token in Credential Manager, and touches no network address that is not a model provider. Telemetry is off.
8. **First chat.** Plan and key chats run with no telemetry send.
9. **Memory.** On first use QMX starts pg0 with its data in `data/memory/hindsight/pg` and Hindsight downloads its embedder and reranker into `cache/models/` (sizes shown); recall works from the built-in adapter until it is ready, and the index builds from the Library rows the switch brought in.
10. **Templates.** The template pack installs into the Library and test-runs each template on a real model (WU5).
11. **Market data.** The door opens with no holdout (WU11); the downloaders write into `data/market` by default; a first small Dukascopy download proves it. The old 10 GB of ticks is imported into `data/market` from where it is (`import_old_ticks.py`, defaults of E2), after a free-space check; the original stays.
12. **Backtests from a chat,** once the unit session's door lands (PR 204's successor): the door runs on This PC.
13. **A cTrader demo sign-in** with This PC as its home (E1).
14. **The first backup round** runs that night; the first restore drill a month later.
15. **Optional parts,** each from Settings with its size: machine learning, documents (Docling), the deep log viewer on This PC.

Nothing in 1 to 15 asks for a server, a Docker install or a public address.

### F1. What the copilot's add-a-server walk hands off to later (ruling 145)

The walk is the methodology session's to build, on the wizard pattern: the copilot shows one step card at a time, each a step only he can perform, checks it before the next, and can stop and resume. The backend gives it this contract:

- **His steps (the cards):** choose and pay for a server (his money); give QMX the address; sign the server into his Tailscale network; run the one setup command in a terminal QMX opens for him (he types the server's password there himself, never into chat); approve the firewall step.
- **QMX's steps (each a resumable operation with a check):** the existing `qmx node setup` sequence (bootstrap, the recovery script and its conf, the firewall close with the fresh-SSH check, the host install, the standalone Hub stopped, pairing, the key copy), then a new row in the place list under the name he chose, then preflight walking `available` to `healthy`, then a one-node smoke test on the new place, then `qmx-recover status` shown in plain words and the PC twin's conf updated.
- **What he decides afterwards, each on its own screen (D4):** whether the deep logs go there; whether it is an off-site backup target; which datasets it also keeps; whether a broker sign-in moves there (a fresh sign-in); and, once the stand-in round lands, which schedules it runs while This PC is off.
- **What it never does:** make the server the main copy, move `main`, or become a step of the first start.

## G. Build plan outline (for later; not a WRAPUP-PLAN section)

`QA/` is `qmx-agents/packages/`, other shorthands as in `WRAPUP-PLAN.md`. Each piece is one PR: one build, one check, one fix round. Phase 1 makes the first start possible; WU11 and the unit session's backtest door join it.

**Phase 1: the folder and the first start**

| # | Piece | Files area | Done when | The one check |
|---|---|---|---|---|
| LF1 | One resolver, one layout, one label | new leaf package `QA/qmx-home/` (stdlib only: `resolve()`, `Layout`, `Label`); every entry point: `HO/__main__.py`, `qma/console.py`, `QX/server.py`, `TL/servers.py`, `BR/server.py`, `QX/node.py`, `E/__main__.py` | every entry point finds the same folder by A2's order; nothing creates a folder implicitly | a test runs each entry point's resolution with a pointer, `QMX_HOME` and a flag and asserts one path; a grep test finds no `Path.home() / ".qmx"` or cwd default outside `qmx-home` |
| LF2 | The tree | `qma/harness/home.py` (`QmxHome` takes the `Layout`), `E/workers/zones.py` (`zones_root`, `home_of`), `AP/supervisor.py` (environments, images, runtime to `cache/`), `R/vault.py` and `QX/server.py` (`keys/`), `HO/host.py` (logs, `cache/run`), `QA/qmx-memory/hindsight.py` (pg0 `data_dir`, model cache, log folder), `E/nodes/script.py` (child cache variables); a format 1 to 2 layout step for existing test homes | a fresh folder holds exactly the five parts and the label; every file A5 names lands where it says | a live lane boots a throwaway folder with `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` and `HOME` pointed at a scratch profile, runs a chat, a memory recall, a script workflow and a mini app, and lists every file created outside the QMX folder: only Credential Manager entries, uv's cache and OS temp scratch |
| LF3 | Versions | `qmx-home` (`Label`, `check_open`), `E/ledger/migrations.py` (`min_reader`, rule 3), each SQLite store's opener, the settings writer (unknown keys kept), the pre-change snapshot hook | B2's five rules hold for the folder and each store | a test opens stores one version newer with `min_reader` unchanged (opens) and raised (refuses by name, Library read-only); a settings round trip keeps an unknown section |
| LF4 | The old-layout first start | the first-start card's backend (`HO/` startup route), `scripts/data/switch_library.py` called on the copy, the refusal of L4 in `QX/library.py` | F step 4 runs end to end and never writes the old folder | a lane on a synthetic old-layout folder: the switch report matches, and the old folder's file list and hashes are unchanged afterwards |
| LF5 | No server in the defaults | the three telemetry sites; `QX/node.py:177` (vault machine default); `RM/models.py:103,123-124`; `HB/server.py:969`; `node-bootstrap.sh` (`primary` line); `HO/market_data.py:106,495,953`; the three downloaders; `scripts/data/import_old_ticks.py`; `C/lab.py:17` | a host started with no settings opens no connection to any address that is not a model provider, and every default names This PC | a unit test asserts a chat's launch environment has no OTLP variable while `send_to = "off"`, plus a grep test for IP literals in production code |
| LF6 | The place list | `E/ledger/migrations.py` (the `triggers` step without the `CHECK`), `E/triggers/rows.py:37`, `E/definition/validate.py:29`, `E/settings.py:134-138`, `HO/host.py:879-883` (`--place`), `T/run-on-a-machine`, D3's run fields | a place he adds under any name can home a trigger and be named in `runs_on`; runs record D3's fields | the ledger test inserts a trigger homed on `home-server` after the step and reads `blocked_config` when that place is removed |
| LF7 | cTrader homed on This PC | `HO/venue_session.py` (home default, the refusals), `BR/` reads, the host's key store write | a demo sign-in on a PC with no server reads accounts | the WU8 sign-in lane, run with no server and the home `pc` |
| — | WU11 (planned) | as planned | the door opens with no holdout | as planned |
| — | Backtest door (unit session, PR 204's successor) | the unit session's | a chat backtest lands one result on This PC | the unit session's |

LF1 to LF4 and WU11 make the first start possible; LF5 removes the quiet failed sends; LF6 and LF7 can follow in either order.

**Phase 2: the local backup**

| # | Piece | Files area | Done when | The one check |
|---|---|---|---|---|
| LF8 | Snapshots, the second drive, restore | a `backup` module in `qmx-control` (or its own package) replacing `C/backup.py`; the `backup` script workflow replacing `T/backup-weekly`; the startup card's restore route; `data/settings.toml [backup]` | C1 to C3 work, the drill included; the GitHub target is the C5 subset | a lane backs up a filled throwaway folder to a second folder, deletes `data/`, restores, and compares every evidence hash and every SQLite row count |
| LF9 | The sealed key copy | `R/vault.py` (export and import), Settings' passphrase route | C4 works on a second scratch profile | a lane seals, wipes the scratch profile's `qmx/*` test entries, restores them, and a key chat answers |

**Phase 3: optional parts on This PC**

| # | Piece | Files area | Done when | The one check |
|---|---|---|---|---|
| LF10 | The deep log viewer on This PC | the host's supervisor (start, stop, health), `[telemetry]`, the download step | E1's "on this PC" works under the host | a chat's trace is found through the local OpenObserve's search API |
| LF11 | Machine learning and documents as optional parts | `qmx-engine` extras, preflight's `needs`, the upload door to `extract-source`, `train.py` landing the model | one PDF is extracted on This PC and one small model lands as a `model` item | the two template lanes with the extras installed, and preflight's one line with them absent |

**Phase 4: the place choice on every screen**

| # | Piece | Files area | Done when | The one check |
|---|---|---|---|---|
| LF12 | Places across systems | dataset `keep_on`, a connection's home move, backup targets from the list, `[telemetry]` and `[memory]` naming places; the Settings reads the UI needs for each D4 screen | every D4 row has a backend read and write | an API test per row |
| LF13 | The add-a-server walk's backend | `QX/node.py` setup steps as resumable operations with status and checks | the walk's machine steps can run, stop and resume from a card | a dry run on a scratch target with each step's status read back |

**Later:** the stand-in round (61 section D: G4, G6, G8, G11) is its own design round. The UI rows of D4 go to the UI session's handoff list.

**What it touches in today's plan.**
- **WU11:** kept as planned and folded into phase 1; its `primary` change is the one D needs.
- **PR 204 (WU4):** not redone. It belongs to the unit session (`QMB-BACKTEST-DOOR-HANDOFF.md`); this design only fixes that its door runs on This PC by default.
- **WU10 and gate G-CT:** G-CT no longer waits for a server host, because the sign-in can be homed on This PC (LF7). WU10's forwarding to a home host stays for a connection homed on a server; its "reads through the server" becomes "reads through the home, This PC by default". LF7 edits WU8's and WU10's files (`HO/venue_session.py`, `BR/`), so it is stacked after both.
- **The real-step order:** ruling 142 puts the first start before the server setup. The wrap-up's "the server setup, then the cTrader sign-in, then the first boot" becomes "the first start (F), then the cTrader demo sign-in on This PC, then the server setup when he adds a server (F1)". WU9's server setup stays built and waits for that.
- **WU5's "weekly backup trigger enabled after the first boot":** replaced by LF8's backup round; the GitHub snapshot becomes optional (C5).
- **DR0 (copying the old ticks to the server) and G-FLIP:** replaced by F step 11 and withdrawn (61); nothing in phase 1 to 4 needs a bucket (G-R2 closed).

## I. Spine amendments made

Every amendment is marked *Local first (62)*. AD ids are stable; titles that read server-first were reworded in place (62a section D item 14).

- **Library spine:** AD-34 added (the QMX folder: one resolver, one layout, one label; data apart from the program), AD-35 added (versions: open, migrate after a backup, or refuse by name; one release back always opens); AD-16 amended (the local backup: quick undo, the second drive, restore, the sealed key copy, GitHub as an optional target); AD-10 and AD-28 amended (This PC holds the main copy of every partition and durable blob; a server-born partition stays pinned on its server until This PC verifies it; `keep_on` per dataset; G2 and G7 decided); AD-7, AD-11, AD-24, AD-26 (retitled) and AD-27 amended (the schedule default is `pc`; no Hub on This PC; claims on the primary; extraction on This PC by default); conventions, capability map, container view and Deferred rows updated.
- **Engine spine:** AD-72 added (This PC or a place: one list, one choice per job, dataset, connection and service, recorded on every run, shown on a named screen); AD-30 (retitled) amended (the place list replaces fixed names; no shipped server rows; a host's place name from setup); AD-3, AD-10, AD-18, AD-24, AD-31 (retitled), AD-48, AD-52, AD-67 and AD-69 amended (triggers homed on any place, `pc` by default; Pause everything on This PC; Hindsight's database in the folder and on This PC always; zones under `cache/`; the backtest door on This PC; the first-start card and the folder check; every entry point through the resolver; a connection homed on This PC with no server; telemetry off until he points it somewhere, the deep viewer on This PC as an option); conventions, stack, structural seed and Deferred rows updated.
- **Lab spine:** AD-5, AD-8 and AD-20 amended (the local door; a controlled host is This PC or an owned place he marks; a pod's home is a place, This PC by default; the model leaves the zone as a Library item; machine learning as an optional part); inherited table updated.
- `lint_spine.py`: 0 findings on all three spines. All three memlogs carry the decisions.

## J. The facts it is safe because of (blast radius, run on built code)

A probe script in the session scratchpad imported the built engine at `d7391716` (read only, writing only in a temp folder) and printed:

```
1 default zones_root(data) = QMX\data.zones
2 proposed root passes the guard: True
3 home_of(proposed work) = QMX\cache\zones (expected QMX/data)
4 newer ledger refused: LedgerSchemaError ledger schema version 4 is newer than this engine's 3
5 home_engine='home-server' refused: CHECK constraint failed: home_engine IN ('pc', 'contabo')
```

- **Fact 2 (proven by running):** with `home = <QMX>/data`, a zones root at `<QMX>/cache/zones` satisfies the built guard as it stands, so the stray-path protection of engine AD-24 survives the move with no change to the guard.
- **Fact 3 (a risk found by running):** `home_of` returns the wrong folder for the new root and three shipped template scripts call it; LF2 changes it (A3). Without that, those templates read a ledger that does not exist.
- **Fact 4:** today an older engine refuses a newer ledger even when the newer step only added, so rollback needs B2's rule 3 (LF3).
- **Fact 5:** today no place but `pc` and `contabo` can home a trigger; LF6's table step is required, not cosmetic.
- **Why the move of `home` to `<QMX>/data` is low risk** (pointed at the lines, not run): packages build their paths from the `home` they are given (`QmxHome.root`, `<home>/library`, `<home>/market`, `<home>/engine`), so keeping those names inside `data/` moves only what A5 lists. Cleared: no production module writes into the checkout (62a). Risk to fix in LF2: the guard's rules are derived from the home (`qma/harness/tools.py:933-955`): `qmx_homes` is `[home.root]` and the protected list names `procs/`, `state/` and the plugin folder under it. Once `keys/`, `cache/` and `logs/` sit beside `data/`, `qmx_homes` must be the whole QMX folder and the protected list must name `keys/`, `cache/run/` and `cache/plugins/`, or an agent's shell could edit them unasked; LF2's check adds a guard test for each.
- **The cTrader home change** rests on ruling 135's one-home rule, not on a server: with no server there is one home, This PC. Risk: a PC home and a later server home both holding tokens of one app. Cleared by design: moving a home is a fresh sign-in on the new home and This PC deletes its tokens (E1); LF7's lane checks that only one key store holds `qmx/token/ctrader-app` afterwards.

## K. Reviewer gate (inline; sub-agents are barred by the brief)

- **Rubric walk.** Every dimension the altitude owns is decided or deferred: where data lives per OS, the pointer, the tree, classes, versions, backup, restore, the place model, every system's local default, the first start, the add-a-server hand-off. No new AD weakens an inherited one: Library AD-12 and engine AD-28's key rules are untouched (the sealed key copy never carries a token or a live-trading key); ruling 135's live-key rule stands in E1; no money gate or sandbox returns (rulings 116 to 118); no default-closed lock is added (ruling 137: telemetry off is not a lock on anything he can do, and every optional part is one switch); every new text says "unit", never "bot", where it means his trading logic.
- **Codebase design.** One deep module, `qmx-home`, with a small interface (`resolve()`, `Layout`, `Label.check_open()`), replaces five home defaults and three cwd defaults; it is a leaf (stdlib only), so every package may import it without a cycle (61's layering note). The deletion test passes: without it, eight call sites each re-derive the folder. The backup has one layout for the second drive and the quick undo, not two code paths.
- **Domain model.** Words fixed in D1 and used throughout: QMX folder, data, keys, backups, cache, logs, This PC, place, run and keep, copy, stand-in, home of a connection. "Server" stays the plain word for one kind of place; "home" in code keeps meaning the data folder.
- **Edge lens.** A folder carried to a new PC: the cache's machine stamp empties the cache, keys come from the sealed copy, the plan login and connection tokens are signed into again. A lost pointer: the scan finds the folder. A full second drive: the copy refuses whole with a task. A restore while a server holds newer saves: copying stays paused until he chooses. A store one release newer: opens (expand, then contract). Hindsight's database newer than the installed Hindsight: memory answers from the built-in adapter while it rebuilds. An exFAT USB disk: the pool layout needs no hard links.

## What needs him

Nothing now. Every question here was technical and is settled above. Two things will reach him later as clicks on a screen, not as questions: removing the old `~/.qmx`, `~/.pg0` and `~/.hindsight` folders after QMX has run on the new folder for a week (F step 4.7), and setting a passphrase if he wants his keys in the backup (C4). Paying for a server stays his money call when he wants one (F1).

## L. Edge-case review applied (coordinator, 2026-10-26)

The coordinator ran the edge-case-hunter lens over this design and folded one round of guards in. Each binds its build piece.

1. **The default second drive must not fill the system drive.** With the folder on D:, C2's default target is C:, and his C: is the short drive (22.4 GB free on 2026-10-24). Guard (LF8): the default target is never the system drive when a copy would leave it below the larger of Windows' own low-disk warning and 10 % free; then the card offers a USB disk or an off-site target, and the "your work has no copy on another drive" warning stays until he picks one.
2. **The monthly restore drill must not double the folder.** A full restore into `cache/restore-drill/` would copy every pooled file, the 10 GB of ticks included. Guard (LF8): the drill restores one snapshot's mutable files and a random sample of pooled files, checks their hashes and the SQLite row counts, checks free space first, and deletes the drill folder when it ends.
3. **Telemetry to a hard-coded public address is live today.** Every chat on a fresh PC would try to reach the server's public IP. Guard (order): LF5 lands before the first real start on his PC, not after it, so phase 1's order is LF5, LF1, LF2, LF3, LF4, WU11, then LF6 and LF7.
4. **Server homes change layout too.** WU9 built server homes in the flat layout (`/srv/qmx/home/.qmx`). Guard (LF2): the format 1 to 2 layout step runs on a server home as well, from `qmx node update` and `qmx-recover repair`, with the same pre-change snapshot, and `recover.conf` names the new `data/` and `keys/` paths.
5. **The first start must refuse a folder another program syncs live.** A1 bars OneDrive, Dropbox and Google Drive by policy; the card must detect it. Guard (LF4): the card refuses a path under a known sync client's root (OneDrive's `OneDrive*` environment variables, Dropbox's and Google Drive's info files) by name, and warns for a folder Windows' "Known Folder Move" redirects (Documents, Desktop) into OneDrive.
6. **Quick-undo snapshots of a growing ledger.** An hourly `VACUUM INTO` of a large `engine.sqlite` costs time and space. Guard (LF8): a quick-undo snapshot copies a SQLite store only when its `data_version` or file size changed since the last snapshot, and the snapshot log records each copy's seconds and bytes, so the cost is visible in the data health read.
