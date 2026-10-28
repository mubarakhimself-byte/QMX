# 06. Sync to my storage, and connect from the screen: the design

Written 2026-10-28 by the sync architect, with the `bmad-architecture` skill in headless amend style and the `codebase-design`, `domain-modeling` and `principle-subtract-before-you-add` skills. It amends `../methodology/62-local-first-design.md` (the sections it replaces are listed in section 18). Design only: no code was written, run or changed.

Inputs: his seeds (`01-his-words-2026-10-28.txt`, `words:N`) and his answers to the three open tickets (`05-his-answers-2026-10-28.md`, his words win over the coordinator's reading); `00-backup-explore.md`, `02-inventory.md`, `03-primary-sources.md` with `sources/`, `04-alignment-and-domain.md` (`align:`); the map `../../wayfinder-sync/MAP.md` and its 23 tickets, all closed (cited by slug, for example `[one-place-list]`); rulings 105 to 145 of `../methodology/26-operator-rulings-and-alignment.md` (`R<n>`, the latest winning). Code truth is `build/br4` at `1e9f695a` in `D:/QMX-worktrees/bld-br4` (PRs 225 to 228) and `build/br5` at `1e5aaabd` in `D:/QMX-worktrees/bld-br5` (PR 229). Shorthands follow the map's README: `BK/` is `qmx-home/src/qmx_home/backup/`, `HO/` is `qmx-host/src/qmx_host/`, `QX/` is `qmx-control/src/qmx_control/`, `PK/` is `qmx-agents/packages/`, all under `bld-br4/qmx-agents/packages/` unless marked `BR5/`.

## 0. In plain words (for him)

- **Your PC comes first.** QMX keeps copies of your work on this PC from the first start. It works fully with no Google Drive, no server and no internet.
- **One switch, "Sync to my storage".** Under it is a list of storages. This PC is always the first row. You add another (Google Drive, another drive, your server, Cloudflare R2, anything rclone reaches) with a click, during install or later.
- **Only what matters is sent.** Your recipes (workflows, mini apps, units, settings), your own content (chats, notes, uploads), your run results, and the prices that can't be downloaded again. Things QMX can rebuild or download again are never sent. Keys and passwords never leave this PC.
- **Small and safe.** Copies are packed and compressed. Each sync is a dated copy, so deleting something by mistake on Tuesday is still in Monday's copy.
- **No passwords to remember.** Nothing is locked. On a new PC you sign in to your storage, pick a copy, and carry on. Then QMX lists the keys to type in again.
- **QMX looks after its copies by itself.** Once a month it tidies and checks them, apart from your own workflows. You can switch any of it off, and you can add an agent if you want one.
- **Before every update QMX syncs first.** If that sync fails, the updater asks you before it goes on.
- **One step-by-step dialog connects anything.** Storage, a server, a GPU or the deep logs all use the same steps. QMX does its part itself and shows you a card only for what only you can do (sign in, pay, type a key). The copilot walks the same steps with you.

## 1. Paradigm and invariants

**Paradigm.** QMX saves the recipe, not the cake (`words:185`). This PC holds the main copy (R136). Every storage, This PC's own copies included, holds whole dated copies made by one round through one storage seam. Every connection, whether storage, compute or deep logs, is one list of idempotent steps on the host's job runner.

These must always be true. A build that breaks one is wrong whatever its tests say.

| # | Invariant | It prevents | Ticket |
|---|---|---|---|
| I1 | QMX is whole with no storage, no network and no account. This PC is the first storage and the default, and every other storage is optional | a first start, an update or a restore that needs a cloud or a server | [first-storage], R136, R142 |
| I2 | One class table decides what every copy, guard and sweep does. Each sync switch names exactly one class. `rebuildable`, `secret` and `scratch` never leave the PC | six lists drifting across five packages (`align:` C1) | [saved-set-by-class] |
| I3 | A secret never travels, sealed or not. A copy carries key names, never a key | a key on someone else's disk; the attach guard missing `data/vault/` | [secrets-stay-home], R116, R135 |
| I4 | No passphrase or lock of any kind. A copy opens on a new PC with only his sign-in to that storage | copies nobody can open after a forgotten password | [lock-cloud-copies] |
| I5 | A copy exists only when its manifest, with a whole trailer, is on the storage. The write order is packs, then index, then manifest. Removal runs in reverse: manifest, then index, then any pack no index names | a half copy read as whole; a killed round that leaves damage | [packs-and-compression] |
| I6 | On a storage every file except `backup.toml` is written once under a name it keeps (a content hash or a stamp). Only `rclone copy` writes. QMX deletes only through its own prune. Never `rclone sync` or `bisync` | a far-side delete; an overwrite racing a reader | [one-rclone-runner] |
| I7 | Each QMX folder writes only under `QMX-backup/<home_id>/` of a storage. One QMX job at a time per folder touches copies (sync, re-pack, check, drill or restore; a second answers 409) | two writers in one folder; a prune deleting a pack a running sync just wrote | [several-machines-one-storage] |
| I8 | A sync makes dated copies and is never a mirror. Nothing deleted on the PC deletes a kept copy | a mistaken delete reaching every copy | [sync-switch-and-timing] |
| I9 | One storage failing never stops another storage or This PC's copies. It opens one incident and is tried again at its next due round | one dead account blocking every copy | [one-free-space-floor] |
| I10 | A restore is checked, shown and confirmed, never picked quietly. The earlier `data/` is set aside whole. Fires and the server link wait for his carry-on | a restore that overwrites newer work, or a schedule firing on restored state | [restore-from-storage] |
| I11 | No QMX cap. A floor protects his drives and accounts only, is shown and is editable. Every setting comes back with its default, is editable in the UI, and every QMX job has its own off switch | hidden limits; blank settings screens; locks he cannot open (R106, R137) | [one-free-space-floor], [sync-switch-and-timing] |
| I12 | Connecting is idempotent. A kind's steps rerun until they converge. His steps are cards. The place row is written last. The screen and the copilot call the same routes | a half-connected place in the list; a wizard and a copilot that disagree | [connect-dialog] |
| I13 | rclone's output never reaches an answer, a log line, a job line or the screen | a token printed through an error message (R116) | [one-rclone-runner] |
| I14 | No settings writer replaces a section to change one key. A partial write merges | the Hub heartbeat wiping `[engine]`, and with it every place row (section 15) | section 15 |

## 2. What is saved: the class table

[saved-set-by-class], [secrets-stay-home], [lock-cloud-copies]

**One deep module**, `qmx_home.classes` (standard library only, a leaf), with one function, `class_of(path, kind=None) -> Class`. Deletion test: without it, six lists come back across five packages (`align:` C1).

| Class | Sync switch | Sent | What |
|---|---|---|---|
| `recipe` | Recipes | yes | `settings.toml`, `profiles/`, `slots/`, `observers.json`, `definitions/`, and Library objects of the recipe kinds (workflow, mini-app, unit, skill, methodology, template, agent, persona, strategy, component, logic) |
| `content` | My content | yes | chats (`claude/projects/*.jsonl`, `chats/<id>.json`), `agent-memory/`, `exports/`, `workspaces/`, Library notes, sources, uploads and `session` items, `apps/<id>/data` (copied under the app's lease), `node/` |
| `result` | Run results | yes | `engine/engine.sqlite`, `engine/inbox.sqlite`, `engine/runs/`, `runs.db`, `control.db`, `portfolio.db`, and Library kinds `workflow-run`, `test-report`, `artifact`, `backtest-result` |
| `prices` | Prices that can't be downloaded again | yes | imported ticks and a live feed's open month (the `keep_series` split, `PK/qmx-hub/src/qmx_hub/bucket.py:19-23`) |
| `rebuildable` | none | never | `library/catalog.db`, `memory/fts.db`, Hindsight's database, fetched and transient blobs, downloadable price series, `cache/`, `logs/`, OpenObserve's data |
| `secret` | none | never | `keys/`, `vault/**`, `rclone.conf`, the four Claude login files (`BK/snapshot.py:71-78`) |
| `scratch` | none | never | locks, SQLite side files, `.part`, staging, heartbeats, process records, `migration/restore-unfinished.txt` |

- **One change from the ticket.** [saved-set-by-class] put unique prices inside `content` while [sync-switch-and-timing] gave them their own switch. Here they are their own class, `prices`, so a switch always names one class.
- **Library objects are classed by kind**, read from the live catalog at copy time. An unknown kind reads `content`, the safe side.
- **Per-machine keys are marked, not left out.** `settings.toml` travels whole. A short list in the same table (`disk.floor_gb`, `[telemetry] send_to`, This PC's own place fields, GPU choices, the rclone binary path) keeps the new machine's values when a copy is restored onto a different machine. The machine is told apart by the cache's machine stamp (62 section K).
- **Every caller reads the table.** The round sends the classes each storage's switches name. The host's room-making list is the evictable part of `rebuildable`. The harness guard and the attach guard read `secret` and add their own extras (closes the attach review's MUST 6).
- **Keys travel as names.** Each copy carries the list of key names its recipes need (n8n's credential stubs, `src:` 1.8). After a restore the first start shows them as "keys to fill in", each typed through the write-only key route (section 9). Sign-ins (Claude plan, cTrader, Google) are done again, as on a new device.
- **`data/rclone.conf` is encrypted** with a password kept in Credential Manager and handed to rclone through `RCLONE_PASSWORD_COMMAND` (`sources/rclone-docs-config-encryption-excerpt.md`). He never types it. On a new PC he connects the storage again, which is also the first step of a restore.
- **No lock (I4).** No `crypt` layer and no passphrase. A key only this PC held would make the copies unreadable exactly when they are needed, so that encryption is ruled out. What protects a cloud copy is the storage's own access (Drive's `drive.file`, `src:` 2.4) and the provider's own encryption at rest; that last point is the coordinator's reading and was not checked against a source.
- **The sealed key copy (planned PR 7)** is parked in the backlog. He never asked for it (`words:29`).

## 3. Where it goes: the storage seam, packs and the one rclone runner

[one-rclone-runner], [packs-and-compression], [spread-over-accounts]

**The seam is the built `Repository` protocol** (`BK/repository.py:192-249`). Two adapters make it a real seam:

- `FolderRepository`, built, for This PC's copies in `backups/quick/` and for a folder on another drive;
- `RcloneRepository`, new, for every rclone kind (Drive, R2, SFTP to his server, rclone's `local` backend in tests).

One correction found by reading the code: the round names the concrete adapter (`BK/round.py:305` builds `FolderRepository(...)`, and `_guard` at `:443` takes one), so the round gains one factory, `open_storage(place) -> Repository`, chosen by the place row's `kind`. The restore already takes any `Repository` (`restore.stage(layout, repo, stamp, ...)`, called that way at `wrapup/evidence/br5/owner_lanes.py:477`).

**Layout on every storage, This PC's included:**

```
<storage>/QMX-backup/<home_id>/
  backup.toml                      which QMX folder writes here and its last copy (the one file rewritten)
  packs/<ab>/<pack sha256>.pack    many pool files, one zstd frame each, and a list of what it holds
  index/<stamp>.json               written once per round: sha256 -> pack, offset, length
  snapshots/<stamp>/manifest.jsonl written last; header, one line per file, trailer
```

- **Pool names stay the sha256 of the original bytes**, so the write check (`BK/repository.py:300-317`) and the restore check (`BK/restore.py:1062-1065`) do not change. Callers never see the word "pack": packs live behind `put_pool`, `fetch` and `sweep`.
- **A pack** closes at about 16 MiB or at the end of a round; a larger file gets a pack of its own. Each file is one zstd frame with `checksum_flag` on (Python 3.14 `compression.zstd`, `src:` 3.1). Parquet, PDF and images are stored without compression. No dictionary and no group frames. The pack size is internal, not a setting: he never chooses it.
- **The index is written once per round**, never rewritten, and can be rebuilt from the packs' own lists. A reader takes the union of every index file.
- **`fetch` is pack-sized.** The adapter downloads a whole pack into `cache/` and reads frames from it. A restore, a check and a drill read whole packs anyway, so no range reads are needed.
- **This PC's copies keep `at: live`** for write-once files (Library objects, frozen price months, the old ticks), which copy nothing. Only mutable files are packed there.
- **No migration.** No real folder holds a PR 225 pool yet: 225 to 229 are not landed and his first real start has not happened.
- **Each storage holds a whole copy.** No `union` and no spreading over accounts ([spread-over-accounts]). Two storages are two whole copies.

**One rclone runner on the PC**, `qmx_home.rclone`. It finds the binary (PATH, a path in Settings, or the pinned release fetched into `cache/tools/rclone/` and checked against its published sha256). It passes `--config data/rclone.conf` and the password command. It returns an exit result and one plain line, never rclone's text (I13), and it records the arguments. The node rebuild's runner (`QX/node.py:470-475`) moves onto it. The Hub's runner on the server (`PK/qmx-hub/src/qmx_hub/bucket.py:72-78`) stays its own, since `qmx-hub` does not depend on `qmx-home`.

**Kept from planned PR 6** (`plan:351-403`): the arrival check (`lsf`), manifest last, never `rclone sync`, the remote-name check, silent errors. **Dropped:** the `cache/backup-send/` hard-link tree.

**Not restic, kopia or rclone `compress`.** restic encrypts every repository with a password it cannot recover, which I4 forbids; it would also replace the tested pool, manifests, keep rule and restore of PRs 225 to 229. rclone `compress` is marked experimental with possible data loss (`sources/rclone-compress.md`).

## 4. The place list, run and keep

[one-place-list], [several-machines-one-storage], [one-free-space-floor], [first-storage]

- **One list**, the built `[engine] placement.<name>.*` rows (`PK/qmx-engine/src/qmx_engine/settings.py:48-65`). This PC (`pc`) is built in and always first. Every other entry is a place. A row gains `kind` and `can` (`run`, `keep`, or both). A storage is a place that can keep; a folder on another drive is a storage of kind `folder`. This reverses 62's "the second drive is not a place" (62 D1).
- **One correction found by reading the code:** `places()` lists every placement name (`settings.py:56-65`), so a storage row would appear as somewhere a workflow can run. `places()` returns only rows whose `can` includes `run`. A row with no `can` reads as `["run"]`, which is what every existing row means.
- **A row holds where and what.** Its sync policy is keyed by place id under `[backup]` (the code name stays; the screen says "Sync to my storage"):

```toml
[engine.placement.gdrive]          # a storage he connected
id = "01J..."                      # stable, so a rename keeps its history
kind = "rclone"                    # folder | rclone | server | modal | e2b
can = ["keep"]
remote = "qmx-01J..."              # its remote in data/rclone.conf

[backup]
on = true                          # "Sync to my storage"
[backup.place.pc]                  # This PC, "Copies on this PC"
on = true
save = ["recipe", "content", "result", "prices"]
every = "1h"                       # when something changed
keep = { hours = 48, days = 7 }
[backup.place.01J...]
save = ["recipe", "content", "result", "prices"]
every = "1d"
at = "03:00"
keep = { days = 14, weeks = 8, months = 12 }
floor = "auto"                     # the larger of 2 GB and a tenth, where the kind reports free space
[backup.upkeep]
every = "1mo"
repack_past = 0.05
check_slice = 12
drill = true
```

  The build picks the exact spellings. What binds is one list in `[engine]` and the policy by place id.
- **`[remote]` and `RemoteSettings` go**, and **`[[backup.targets]]` rows become place rows** with `can = ["keep"]` (section 13).
- **No shared writer (I7).** Each QMX folder writes only under its own `home_id`. Each home prunes and re-packs only its own folder, so no lock is needed (principle separate-before-serializing).
- **Two machines, one home.** A PC that restores a copy takes the copy's `home_id`. If the first PC keeps syncing, the built fork guard refuses whichever writes second. The card then offers two choices: "carry on here" (built, `BK/round.py:170-184`), or the one new choice, "make this a new home", which mints a new `home_id`, so this PC writes its own folder from then on.
- **One local floor** for every local write, This PC's copies and a folder storage on C: included: the larger of 1 GiB and `disk.floor_gb`, or a twentieth of free space when that is unset. It replaces the three floors (`PK/qmx-home/src/qmx_home/versions.py:39`, `HO/disk.py:55-62`, `BK/plan.py:56`). **A storage floor** applies to any kind that reports free space (Drive, SFTP, folder), and is editable per storage. R2 reports none and gets none. A storage at its floor stops before writing, with one incident that names the biggest class it holds. Neither floor is a cap (R106).

## 5. When it runs: the switch, the timing and copies on this PC

[sync-switch-and-timing], [copies-on-this-pc]

- **One main switch.** Off pauses every storage and deletes nothing.
- **Per storage, four switches, one per class**, all on by default. A small free storage can drop `prices` while his server keeps them.
- **One round, many storages.** A round makes one snapshot (`snapshot.make`, built) and writes it to each due storage, filtered by that storage's switches. This PC comes first.
- **This PC's copies** are on by default (R136, "with a local backup always"), hourly when something changed, kept 48 hours then 7 days (the built defaults). They have an off switch (R137) and a cadence. With them off, the round stages its mutable files in `cache/sync-staging/<stamp>/` (scratch), sends them, and removes the staging. With them off and no other storage, the doctor row says in plain words that his work has no copy anywhere.
- **Other storages** sync once a day when something changed, at a time he sets. They also sync before every update and on "sync now". A PC that was off syncs at its next start. He can set any cadence down to hourly. Not "on every change": a changed store is sent whole, and `engine.sqlite` changes all day.
- **Keep rule per storage**: the built one (`BK/keep.py`, newest days, weeks and months; the newest and the newest checked copy always kept).
- **The 30-day hold becomes an event.** Pre-change and `before-upgrade` copies are released after the first whole copy reaches a storage on another disk (`BK/keep.py:16`, `:57-61`).
- **Retry is not a setting.** A storage that refused is tried at its next due round. After seven missed rounds the incident says so.
- **`GET` of the sync settings returns every value with its default** (fixes `HO/backups.py:666-690`).

## 6. Maintenance: QMX's own upkeep

[maintenance-repack-and-check]

- **One monthly job per storage, in the host**, This PC included, each step's numbers a setting:
  1. **Re-pack.** Drop packs that no kept copy names. Rewrite a partly used pack only past 5% unused, with a size limit per run (restic's prune, `src:` 3.2). The order is new packs, then the new index, then delete the old index files, then the old packs. So every index on the storage names only packs that exist.
  2. **Check.** Read every index and manifest. Download and verify one twelfth of the packs, a different twelfth each month.
  3. **Drill.** Restore a random copy's mutable files and a sample of its pool into `cache/restore-drill/` (the built drill, `BK/restore.py:427`, scheduled by PR 229; 62 L2's sample rule stays).
- **Sync and maintenance run in the host, not as workflows**, because they must run with fires paused after a restore and before an update. The host's sweep is the one scheduler. The app volume timer and the weekly template's cron go (section 13).
- **Listed apart.** The screen shows "QMX's own maintenance": the host's jobs and the shipped workflows marked `meta.kind = "maintenance"` (`connections-health`, the guard watchdogs). The marker sits in `meta`, outside the content hash (`PK/qmx-engine/src/qmx_engine/definition/model.py:205-212`). Each item has its own off switch.
- **An agent is optional, none by default.** Each host job emits an event when it ends. He can add a maintenance workflow triggered by that event, with an agent step that reads the result. The work itself never moves into the engine.

## 7. Sync before every update

[sync-before-update]

- **One call, `sync_now(why="before-update")`**, with a time limit. It has two callers: the store-upgrade hook in `serve` now (`HO/__main__.py:142-143`) and the desktop updater when it exists.
- **The order** (Hermes's, with the sync first, `sources/hermes-docs-updating.md`):
  1. sync to his storages, if the switch is on;
  2. the local `before-upgrade` copy (PR 228);
  3. update the program;
  4. check that the stores open, or start the new version against a copy;
  5. if the check fails, put the old program back. His data is untouched (R141).
- **When step 1 fails.** The updater asks in one line: "the sync to `<storage>` failed: `<why>`. Update anyway? Your copy on this PC is fresh." `serve` asks nobody. It falls back to the local copy with one line and goes on (I1).
- **One copy per upgrade.** Each store's own `pre-*` copy (`PK/qmx-home/src/qmx_home/versions.py:235-302`) is released once a `before-upgrade` copy of the same moment exists, and kept only when that copy failed.

## 8. Restore from any storage

[restore-from-storage], [several-machines-one-storage]

- **The built restore is kept whole** (PRs 226, 228, 229): check, confirm with what it replaces, set aside, `replace` for another folder's copy, purged blobs never restored, memory rebuilt, fires and the server link paused until carry-on (I10).
- **A storage is a source.** The card's and Settings' `source` gains the storage kinds beside `folder`, read through the same `Repository` adapter as the sync.
- **On a new PC, from the first-start card:** choose "Restore from my storage"; the storage's connect dialog runs (he signs in again); the newest copies show with machine, time and counts, and he picks one; the check shows what is newer on the PC (the built `newer` counts); restore with steps and counts; the handover; keys to fill in; carry on. Storage rows that came with the copy show "connect again", because `rclone.conf` never travels.
- **From Settings:** PR 229's restore while QMX runs, finished at the next start, with the same sources, plus cancel before the next start (UIH section 26 gap 8).
- **Progress with counts.** A restore reports `done` of `total`: "fetching your copy from `<storage>`" in bytes, then "placing the copy's files" in files. Today both stay 0 (UIH section 19 row 11).
- **Also:** a failed restore into a non-default folder is offered again by the card (PR 228 review low 1). A server holding newer Library history is offered after carry-on (Library AD-14 `adopt`).

## 9. The one connect dialog

[connect-dialog], [connect-storage], [connect-compute], [connect-deep-logs]

**A connection kind is an ordered list of steps**, each `(name, who, check, do)`, where `who` is `his` or `qmx`. One job runs a kind on the built job runner (`HO/jobs.py`). It skips every step whose `check` passes, runs QMX's steps in order, and finishes with `{needs: <his step>}` at a step only he can do. The screen shows that card. When he is done the same job runs again. Resuming is rerunning, so no state machine is saved (principle make-operations-idempotent). The last QMX step writes the place row with `can`, then runs the kind's health check (I12). The first-start card's job route (`/api/first-start/jobs/{id}`) runs the storage kind too, so a restore works before any host exists.

**Routes**, one backend for the screen and the copilot (R145):

- the list of kinds and what each can do (run, keep, both), for the dialog's first question;
- start or rerun a connect job, and read it;
- **a write-only key route**: put a named key into Credential Manager, never read it back, and list which names are set. It serves an R2 key, a Modal or E2B key, and the cTrader app id and secret (UIH section 26 gap 3).

**Storage kind:**

1. QMX: get rclone (PATH, Settings, or the pinned release, checked).
2. His: choose the kind. "Another drive" is one choice and carries the second-drive suggestion (`HO/backups.py:531-566`).
3. In turns: **rclone's own question loop.** `rclone config create <name> <type> --non-interactive` answers with the next question as JSON, and the dialog shows it as one card and sends the answer back with `--state` and `--result` (`sources/rclone-cmd-rclone_config_create.md`). Any rclone kind works with no QMX code per kind; QMX pre-fills what it knows for Drive, R2 and SFTP.
4. QMX: test with free space (where reported) and a small write, read and delete.
5. QMX: write the place row (`can = ["keep"]`) and its policy with defaults.
6. QMX: run the first sync with steps and counts.

Per kind. **Google Drive** uses QMX's own published "Desktop app" client with PKCE and the `drive.file` scope; rclone's shared client stops working during 2026 (`sources/rclone-drive.md`). Registering it is his one-time card with a link, inside the Drive kind, never a builder's step. **R2** is `type = s3, provider = Cloudflare`, with `no_check_bucket = true` and the key through the key route. **His server** is SFTP over Tailscale, offered once the server is connected as compute (R142). **A folder** uses the folder adapter with no rclone; a folder inside the QMX folder is refused, and one on the same drive is kept with a warning. **Never** the QMX folder itself inside a live-sync folder (UIH section 19 row 8).

**Compute kinds.** A server: his cards (choose and pay, the address, a Tailscale one-off auth key, the server password typed in the terminal QMX opens, approve the firewall step); QMX's checked steps (the `qmx node setup` sequence, `QX/node.py:616-652`, split into steps; the place row with `can = ["run", "keep"]`; the status ladder `available → configured → authorized → reachable → healthy`, giving `PK/qmx-engine/src/qmx_engine/triggers/preflight.py:231` its first caller; a one-node smoke test on its own engine; `qmx-recover status` in plain words, R139). Then his later choices, each on its own screen: deep logs there, a storage there, datasets kept there. Key compute (Modal, E2B, a GPU on Modal): his key card, one provider test call, the place row. No server step is ever part of the first start (R142).

**Deep logs kinds.** OpenObserve, self-hosted, one per person (`words:219`, reshaping R123). The setting stays `[telemetry] send_to` (`off`, `this-pc`, or a place), now checked when saved (UIH section 26 gap 6), with a telemetry doctor row from `logs/telemetry.json`. "On this PC": fetch the pinned release into `cache/openobserve/` and check it; run it under the host with its root password in Credential Manager; `ZO_TELEMETRY=false`, a 1 GB disk cache and 30 days of retention (both editable), data under `cache/openobserve/`, loopback binding (UIH section 26 gap 7). "On a server": install the shipped unit files as the server kind's monitoring step. Every other machine gets an OpenTelemetry Collector with an on-disk queue. The outside-agent door (R126) is OpenObserve's MCP endpoint with an agent login the dialog makes. OpenObserve's data is `rebuildable` and never synced. A per-user run without admin rights is the build's first check; if it needs admin, the dialog shows one approval card.

## 10. Install, first start and update: the step sequences

[install-and-first-start], [first-storage]

**Install** (the desktop session builds the installer; these are its steps):

1. Where the program goes: per-user, no admin, `%LOCALAPPDATA%\Programs\QMX` by default, another drive offered when C: is low.
2. Installing, with step lines: getting QMX, getting its Python packages, checking the install.
3. It opens the first-start card and starts nothing before it.

**First start** (the built card, UIH section 19):

1. **Where your QMX is:** make a new folder (each drive's free space shown); open a folder; bring in old data; **restore from my storage (new)**; restore from a folder.
2. **Restore from my storage:** connect the storage (sign in again); pick a copy (machine, time, counts); see what it replaces; restore with steps and counts ("fetching your copy from `<storage>`", "checking the copy", "placing the copy's files", "checking the copy's stores"); the handover; keys to fill in; carry on.
3. **Otherwise:** the handover, then one line, "Your work is kept on this PC", and one optional card, **"Keep your work in another storage too"**. It runs the storage kind and the first sync, and he can skip it. It replaces 62 F step 5's second-drive card; another drive is one choice inside it.
4. **Nothing else.** Deep logs, machine learning, documents, servers and GPUs come later from Settings or the copilot, each with its size.

**Update** (the desktop updater, when built): section 7's order. Its first visible step is "syncing your work to `<storage>`", skipped when only This PC is on.

**Lines the screen reads.** Every step is a job's `step` with `done` of `total` (UIH section 19 row 9). Exit codes stay as built. A store opened read-only is named up front by the health read, not only at the first refused write (UIH section 26 gap 5).

## 11. The words

[screen-words], `align:` B

| On the screen | Means | In the code |
|---|---|---|
| **Sync to my storage** | the one switch; QMX sending his saved set to his storages as dated copies | `[backup] on`, `BK/round.py` |
| **Storage** | the list of places that keep copies, beside **Machines** for compute. First row **This PC** ("Copies on this PC") | place rows with `can` including `keep`; This PC is `pc` |
| **Restore** | rebuilding `data/` from one copy he confirmed | `BK/restore.py` |
| **Maintenance** | QMX's own jobs, listed apart from his workflows | host upkeep jobs; `meta.kind = "maintenance"` |
| **Server link** | the Library's link with a server (what code calls sync) | `Replicator`, `HO/host.py:813-815` |
| **Deep logs** | the monitoring viewer, OpenObserve | `[telemetry] send_to` |
| **Connect** | the step-by-step dialog | a connection kind on the job runner |
| (never) "backup" | | the package and section keep the name |

Design words, for builders: recipe, content, result, prices, rebuildable, secret, scratch (the classes); saved set (the four sent classes); copy (one dated manifest in one storage); pack; place; run and keep; home (`home_id`).

## 12. UI gaps folded in

[ui-gaps-that-belong], UIH section 26

| Gap | Lands in |
|---|---|
| 1. Run place on the run read | Section 4. Once compute is connected the run card says where each run went (the data is on the run's Library object) |
| 3. cTrader app key entry | Section 9, the write-only key route |
| 4. Sync incidents in `GET /api/inbox` | Sections 4 and 5. The inbox read lists open incidents of every kind |
| 5. A read-only store named up front | Section 10, the health read |
| 6. Telemetry value check | Section 9, deep logs |
| 7. Deep logs on this PC | Section 9, deep logs |
| 8. Restore beyond the card | Section 8 (Settings restore, cancel, the after-restore pause), section 6 (the monthly check), section 5 (other storages) |

Gap 2 (broker reads over REST) goes to the broker and connections work. Gap 9 (attach) stays with the parked attach plan; only its secret-list fix lands here (section 2). The coordinator writes the UI notes' sync, storage, maintenance and deep-logs section.

## 13. The subtract list, in the order it runs

[subtract-first], `align:` D. Principle subtract-before-you-add: these land before the additions they make room for. The order is changed from the ticket so that every item with a precondition runs after it.

| Run | Goes or merges | Safe because | Size (at `1e9f695a`) |
|---|---|---|---|
| 1 | `[remote]` and `RemoteSettings` (`PK/qmx-remote/src/qmx_remote/models.py:124-142`, `QX/service.py:840-846`) | no reader but the write check; the settings writer keeps unknown sections word for word; `Target` stays | about 28 |
| 2 | The weekly GitHub snapshot: `QX/backup.py`, its command, route, template `backup-weekly/`, catalog row and test | everything it copies is in the saved set; it installs disabled and nothing runs it; an old `repository` key is ignored, not refused | 356 code, 141 tests |
| 3 | Plan text for planned PRs 6 and 7 (`plan:351-459`); PR 7 to the backlog; `BK/round.py`'s `sealed_keys` hook | no built code depends on it | 109 plan lines, the hook |
| 4 | The old bundle installer `release/install.py` and `release/launcher.py`, which launch `qmb` | nothing outside `release/` names them | 506 |
| 5 | Three free-space floors into one | the 1 GiB minimum still guards a pre-change copy | about 10 |
| 6 | The fixed hourly copy becomes This PC's policy with an off switch | the doctor row says so when no copy exists anywhere | about 5 |
| 7 | The mini-app volume backup (`PK/qmx-apps/src/qmx_apps/backup.py`, `backup_schedule.py`, their wiring, `APP_KEYS`, `_volume_keys`) | **after** the round copies each app's `data/` under its lease (`backup.py:135-142`); app data is then in every copy. "Restore one app" goes to the backlog. Litestream stays | about 300 code, about 90 tests |
| 8 | The node rebuild's own rclone runner (`QX/node.py:470-475`) | **in the same wave** as the one runner (principle migrate-callers-then-delete); its callers read only the exit | 6 |
| 9 | The `cache/backup-send/` hard-link tree | never built; struck from the plan | 0 |

**Size:** about 700 lines of code and templates and about 230 lines of tests (items 1, 2 and 5 to 8), plus 506 lines of the old installer and 109 plan lines. Kept on purpose: the second-drive proposal (a suggestion in the dialog), the status ladder (it gets its first caller), the trading node's backup and QMF's backup block, the Hub's bucket push.

## 14. Failure paths, and how each is proven without an account

[one-free-space-floor], [several-machines-one-storage], [sync-before-update], [first-storage]

**Proof rules.** Every lane runs on throwaway QMX folders under one `homes/` root, as PR 229's lanes do (`owner_lanes.py` refuses a home outside `homes/`). Storages are throwaway folders: the folder kind directly, and the rclone adapter through rclone's `local` backend named in a throwaway `rclone.conf`. That config also holds a planted fake token, and every lane greps its answers, job lines, logs and the storage for it and for every `secret` path (I3, I13). No lane uses a real account. The Drive kind is driven up to the card where he would sign in.

| Path | What must happen | The proof |
|---|---|---|
| **Offline** | The cloud storage reads "not reached" with one line. This PC's copies go on. The storage is tried at its next due round and the incident counts missed rounds. `sync_now(why="before-update")` from `serve` falls back to the local copy and the upgrade goes on | an rclone `sftp` remote at `127.0.0.1` on a closed port: a round answers `skipped` for it and `finished` for This PC; a `serve` store upgrade with it configured completes with one fallback line |
| **Full storage** | At its floor the storage stops before writing, with one incident naming its biggest class; other storages go on. A storage that fills mid-round leaves no copy (I5), and the next round reuses what arrived | the per-storage floor set above the throwaway drive's free space: refused before any file is written. `RCLONE_MAX_TRANSFER=1M` with hard cutoff in the host's environment: no manifest, then a normal round converges and its copy restores hash-equal |
| **A pulled drive** | The folder storage reads "not there (is its drive plugged in?)" (`BK/round.py:324`); a pull mid-round leaves no copy; the next round with the drive back converges | `subst Q: <throwaway>` (no admin), a folder storage on `Q:\`, `subst Q: /d` during a slowed round, then `subst` again and one more round; every kept copy restores hash-equal |
| **A killed sync** | No manifest means no copy. `clean` removes what the round left. The next round reuses packs the index names, and the re-pack drops packs nothing names. A re-pack killed at any point leaves every index naming only packs that exist (section 6 order) | kill the host process during a round slowed with `RCLONE_BWLIMIT`, restart, run a round, restore every kept copy and compare every hash and SQLite row count; the same for a killed re-pack |
| **Two PCs** | Different homes write different folders and never touch each other's packs. Two machines on one `home_id` (after a restore) hit the fork guard, which offers "carry on here" or "make this a new home" | two throwaway folders A and B on one storage: both sync and prune, and A's copies all restore after B's prune. Then B restores A's copy, both sync: the second writer is refused; "make this a new home" gives B its own folder and both go on |
| **A storage that disappears** | Deleted folder or bucket: `backup.toml` is gone, so the fork guard refuses until he carries on, then a whole new copy is sent. Removed remote or revoked access: "not reached; connect it again", and rerunning the dialog skips every step that still passes. Nothing on This PC or another storage is touched | delete the storage folder between rounds; then remove the remote from the throwaway `rclone.conf` and rerun the storage kind: only the remote step and the first sync run again |
| **A corrupted pack** | The monthly check names the pack and opens an incident. A restore that needs it stops with the file named; damage is limited to that pack | flip one byte in one pack of a throwaway storage; run the check; run a restore |
| **Drive without an account** | The dialog reaches the sign-in card and stops there, with nothing written to the place list | run the storage kind with kind `drive` and assert the job ends with `{needs: sign-in}` and no place row |

The invariants each get one literal check on the same lanes. I2: a lane fills one file of each class and asserts the storage holds exactly the four sent classes. I8: delete a strategy, sync, and restore the earlier copy. I10: PR 229's lane 4, fixed as in section 15. I14: section 15's heartbeat test.

## 15. PRs 225 to 229: kept, reshaped and removed

`align:` A1 to A3, read against the code.

| PR | Kept | Reshaped | Removed |
|---|---|---|---|
| **225** copy engine | the sha256 pool, the manifest with its trailer, the size and `mtime_ns` skip, `VACUUM INTO` from `mode=ro`, the copy order, `WRITE_ONCE` and `at: live`, the keep rule, the fork guard, the refusals (inside the QMX folder, links), the `qmx_home.files` helpers | `LEFT_OUT`, `SECRET` and `WRITE_ONCE` (`BK/snapshot.py:37-87`) become readers of the class table; the pool file format becomes packs inside the adapters; the round opens storages through `open_storage(place)`; the three floors become one; the 30-day hold becomes an event; `[[backup.targets]]` and `Target` become place rows; the second-drive proposal becomes a dialog suggestion; the fixed hourly copy becomes This PC's policy | the "everything in `data/`" rule; the `sealed_keys` hook |
| **226** restore | stage and finish, the set-aside, `replace`, purges kept, the lock order, carry-over of leases | the source is any `Repository`, so any storage; progress reports `done` of `total` | none |
| **227** host service | rounds on the host's thread, one `backup` job and 409, incidents, the doctor row (new words), the CLI, `PUT` checked by `BK/plan.parse` | `GET` returns every setting with its default; incidents join `GET /api/inbox`; the host's sweep becomes the one scheduler and gains the monthly upkeep; the fixed 1-hour retry becomes the next due round | `APP_KEYS` and `_volume_keys` (with the volume backup) |
| **228** card restore | restore into a new folder (marker first, pointer after finish), `serve` finishing a staged restore, the restore CLI, the `before-upgrade` copy | the card gains "restore from my storage"; `serve`'s store upgrade calls `sync_now(why="before-update")` first and keeps the local copy as the fallback; `pre-*` copies are released once a `before-upgrade` copy exists; low 1 (a failed non-default restore offered again) | none |
| **229** restore from Settings | the staged restore, cancel, carry-on, the after-restore pause by merge, purge again, the memory rebuild with `reindexed` on success, `restore.lock` in `single_instance`, the set-aside view | the drill's schedule becomes step 3 of the monthly upkeep; Settings' restore takes the storage sources | none |

**PR 229's failed check (lane 4) lands in PR 229's own fix round**, before 229 merges. Lane 4 failed "no fire ran before carry-on" because it saw one `ok` fire (`wrapup/evidence/br5/lanes-full.log:43`). Reading the lane (`owner_lanes.py:460-489`): the trigger is created four hours past due, and then a real host is started to make the quick copy (`:472-474`). That host's sweep can fire the trigger before the copy is taken, so the copy itself may hold the fire. The same single `ok` is seen after carry-on (`lanes-full.log:48`). A copied fire and a fire before carry-on (followed by a skipped catch-up) both produce exactly that log, so the lane cannot tell them apart. This is inferred from the lane code and the log; it was not rerun. The fix round:

1. **Fix the lane.** Record the trigger's fire ids right after `finish(layout)` and before the second host starts. Assert no new id before carry-on, then exactly one new id after it.
2. **Then judge the product.** If a new id appears before carry-on, the pause is set too late: `hold_after_restore` must write `autonomy.paused` before the engine's trigger loop starts (I10). The builder's one-fact test claims that order holds (`builder-report.txt`, not rerun here).
3. **Rerun lane 3.** It failed because a host still held the Library (`lanes-full.log:34-36`), which reads as lane timing.

**The Hub heartbeat bug lands in the same fix round and gates the sync work.** `hear` (`BR5/qmx-host/src/qmx_host/host.py:1024-1028`) compares `section(control, "engine").get("autonomy.paused")`. The section is nested (the lane prints `{'autonomy': {'paused': True}, ...}`), so the dotted key always reads `None`. Whenever the Hub answers "paused", every heartbeat calls `settings_put("engine", {"autonomy": ...})`, and that replaces the whole section (`QX/service.py:800-803`). The section holds `host_name`, `disk.floor_gb`, the scheduler keys and, from this design on, every place row and storage. The fix: read the nested value with the same lookup the engine uses, and write only by merge. PR 229 already merges `autonomy.paused` into `[engine]` after a restore, so `hear` reuses that path (I14). Its test: a host with `host_name`, `disk.floor_gb` and one place row; the Hub answers "paused" for three heartbeats; afterwards `[engine]` holds every key with `autonomy.paused` true, and `settings.toml` was written once. It must land before any storage row lives in `[engine]`, or one paused Hub would erase his storages.

**Stacking.** PR 229 is cut from `0ee50e42`, not from PR 228's head `1e9f695a` (measured with `git merge-base`). The two PRs change no file in common (measured), so restacking 229 onto 228 is clean for git. Both PRs' lanes are rerun on the restacked head, because 229's after-restore hold runs after 228's staged finish in `serve`.

## 16. Build order (dependency units for the planner, not a PR count)

Each unit ends in its own check from section 14. The planner cuts the fewest PRs the code needs (`words:219`).

1. PR 229's fix round (section 15), restacked on 228.
2. The subtract items 1 to 6.
3. The class table and secret list, with the guard reading it, the lease copy of app data, then subtract item 7.
4. Packs inside `FolderRepository`, This PC's policy with staging when it is off, the one floor.
5. The one rclone runner, `RcloneRepository`, `open_storage`, place rows with `kind` and `can`, the `places()` filter, the policy by place id, `GET` with defaults; subtract item 8 in the same wave.
6. The connect-dialog backend and the storage kind, the write-only key route, `[telemetry]`'s check.
7. Restore from a storage on the card and in Settings, progress counts, cancel, keys to fill in, "make this a new home".
8. The monthly upkeep with the maintenance list and its event; sync before update and the `pre-*` release; the read-only store named.
9. The compute kinds and the deep-logs kinds; run place on the run read; incidents in the inbox.

## 17. Deferred, and out of scope

- **Sizes from his real folder.** The saved set, the growth of This PC's copies and the size of `engine.sqlite` are estimates (`inv:` 1). The first real start measures them. Revisit only if they are large: append-only run results, chunking, a dictionary, spreading.
- **Encryption that needs no memory.** None is built. Any later design must keep a copy readable on a new PC with only his storage sign-in (I4).
- **A folder storage on a drive that comes back under another letter** reads "not there" until he edits its path. Finding it by `backup.toml` is backlog.
- **QMX's Google client shipped pre-filled.** Until he registers one, the Drive kind asks for it on his card.
- **The QMF price-store retry** against a large open month, and **OpenObserve per-user on Windows**: the build measures both first.
- **Out of scope** (as the map): engine dispatch of PC-started work to a named place; the desktop installer and updater themselves; broker REST; the attach route; the sealed key copy; a QMX-run account service; the trading node's backup and its monitoring stack; exporting OpenObserve dashboards; the Hub's bucket push and Litestream; restore one app, undo a restore, remove a set-aside folder.

## 18. What this replaces in design 62

| 62 section | Replaced by |
|---|---|
| H, the "QMX backs itself up" bullet | section 0 |
| B3, the pre-change hold "until the next second-drive copy, then 30 days" | section 5 (the hold is an event) and section 7 (one copy per upgrade) |
| C1, "everything in `data/` except" | section 2 |
| C2, quick undo, second drive, off-site tiers and the layout | sections 3, 4 and 5 |
| C3, restore, including "open the sealed key copy" | section 8 |
| C4, the sealed key copy | section 2 (parked) |
| C5, the GitHub backup as an optional target | section 13 (removed) |
| D1, "the second drive is not a place" | section 4 |
| D2, `[placements]` and the backup targets naming a place | section 4 (the built `[engine] placement.*` list with `kind` and `can`) |
| D4 rows Backups, Buckets, OpenObserve, the collector, Vault (the sealed copy) | sections 4, 9 and 2 |
| F step 5 (the second copy) and step 14 (the first backup round) | section 10 |
| F1, the add-a-server walk | section 9, generalized to every kind |
| G, LF8, LF9, LF10, LF12's backup-target part, LF13 | section 16 |
| L1 (the default second drive on the system drive) | section 4 (one floor; another drive is a suggestion) |

L2 (the drill's sample) and L6 (copy a store only when it changed) still bind, through sections 6 and 3.

## 19. Reviewer gate (inline; sub-agents are barred by the brief)

- **Rubric walk.** Every dimension the map named is decided or deferred: what is saved, the seam, the runner, the places, timing, This PC's copies, packs, upkeep, update, restore, connect, install, the UI gaps, the subtract list, failure paths, PRs 225 to 229. No new rule weakens an inherited one. R135 and R116 hold (I3, I13). No cap (R106), no default-closed lock (R137), This PC first (R136, R140, R142).
- **Codebase design.** Two adapters behind the built `Repository` make it a real seam. `classes` and `rclone` are deep leaves whose deletion would put six lists and two runners back. One job runner serves sync, upkeep, restore and connect.
- **Edge lens.** The two code readings that change the map (`places()` lists every row; the round names `FolderRepository`) are folded in. The heartbeat wipe would erase storages, so it gates the sync work. A re-pack's delete order keeps every index truthful.
- **Domain words** are fixed in section 11 and match the tickets. "Sync" on the screen never means the server link.
- **Not run:** `lint_spine.py` (this is not a spine file), the reviewer subagents (barred), and every lane in section 14 (design only).
