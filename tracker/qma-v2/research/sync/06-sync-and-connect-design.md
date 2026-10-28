# 06. Sync to my storage, and connect from the screen: the design

Written 2026-10-28 by the sync architect, with the `bmad-architecture` skill in headless amend style and the `codebase-design`, `domain-modeling` and `principle-subtract-before-you-add` skills. It amends `../methodology/62-local-first-design.md` (the sections it replaces are listed in section 18). Design only: no code was written, run or changed.

Inputs: his seeds (`01-his-words-2026-10-28.txt`, `words:N`) and his answers to the three open tickets (`05-his-answers-2026-10-28.md`, his words win over the coordinator's reading); `00-backup-explore.md`, `02-inventory.md`, `03-primary-sources.md` with `sources/`, `04-alignment-and-domain.md` (`align:`); the map `../../wayfinder-sync/MAP.md` and its 23 tickets, all closed (cited by slug, for example `[one-place-list]`); rulings 105 to 145 of `../methodology/26-operator-rulings-and-alignment.md` (`R<n>`, the latest winning). Code truth was `build/br4` at `1e9f695a` in `D:/QMX-worktrees/bld-br4` (PRs 225 to 228) and `build/br5` at `1e5aaabd` in `D:/QMX-worktrees/bld-br5` (PR 229). After the review fold (section 20) code truth is `build/br5` at `78587edc` (PRs 225 to 229, with 229's fix round), and every line cited in sections 2 to 15 that the fold touched is at that commit. Shorthands follow the map's README: `BK/` is `qmx-home/src/qmx_home/backup/`, `HO/` is `qmx-host/src/qmx_host/`, `QX/` is `qmx-control/src/qmx_control/`, `PK/` is `qmx-agents/packages/`, all under `bld-br4/qmx-agents/packages/` unless marked `BR5/`.

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
| I5 | A copy exists only when its manifest, with a whole trailer, is on the storage. The write order is packs, then index, then manifest. Dropping a copy removes only its manifest. Index files and packs are removed only by the re-pack, after it has written a merged index that names every pack a kept copy uses (section 6) | a half copy read as whole; a killed round that leaves damage; a dropped copy's index taking with it the only line that locates a pack a newer copy still uses | [packs-and-compression] |
| I6 | On a storage every file except `backup.toml` is written once under a name it keeps (a content hash or a stamp). Only `rclone copy` writes. QMX deletes only through its own prune and re-pack, and never a pack younger than the safety window (section 6). Never `rclone sync` or `bisync` | a far-side delete; an overwrite racing a reader; a prune on one machine deleting a pack another machine has just sent | [one-rclone-runner] |
| I7 | Each QMX folder writes only under `QMX-backup/<home_id>/` of a storage. Per storage, one QMX job at a time touches its copies (a send, re-pack, check, drill or restore; a second answers 409). A send to one storage never holds This PC's copies or another storage. Across machines nothing is locked: the safety window and the guard checked again just before the manifest is written keep two writers on one `home_id` from damaging each other | two writers in one folder; a prune deleting a pack a running sync just wrote; a slow cloud upload stopping This PC's hourly copies | [several-machines-one-storage] |
| I8 | A sync makes dated copies and is never a mirror. Nothing deleted on the PC deletes a kept copy | a mistaken delete reaching every copy | [sync-switch-and-timing] |
| I9 | One storage failing never stops another storage or This PC's copies. It opens one incident and is tried again at its next due round | one dead account blocking every copy | [one-free-space-floor] |
| I10 | A restore is checked, shown and confirmed, never picked quietly. The earlier `data/` is set aside whole. Fires and the server link wait for his carry-on | a restore that overwrites newer work, or a schedule firing on restored state | [restore-from-storage] |
| I11 | No QMX cap. A floor protects his drives and accounts only, is shown and is editable. Every setting comes back with its default, is editable in the UI, and every QMX job has its own off switch | hidden limits; blank settings screens; locks he cannot open (R106, R137) | [one-free-space-floor], [sync-switch-and-timing] |
| I12 | Connecting is idempotent. A kind's steps rerun until they converge. His steps are cards. The place row is written last. The screen and the copilot call the same routes | a half-connected place in the list; a wizard and a copilot that disagree | [connect-dialog] |
| I13 | rclone's raw output never reaches an answer, a log line, a job line or the screen. Only the parsed question fields `Name`, `Help`, `Examples` and `Type` of the connect loop reach a card; rclone's `Error` becomes one fixed line; the `Default` of an `IsPassword` question is never shown. A secret is never in a command line, and the runner records argument names only | a token printed through an error message or read from the process list (R116) | [one-rclone-runner] |
| I14 | No settings writer replaces a section to change one key, the REST route included. An in-process write merges through `settings_update`; `PUT /api/settings/{section}` merges the keys it is sent, and removing a key is named in the body | the Hub heartbeat wiping `[engine]`, and a screen saving from an old read wiping the host's own merge writes and every place row (section 15) | section 15 |

## 2. What is saved: the class table

[saved-set-by-class], [secrets-stay-home], [lock-cloud-copies]

**One deep module**, `qmx_home.classes` (standard library only, a leaf), with one function, `class_of(path, kind=None) -> Class`. It takes a path relative to the QMX folder, so `data/vault/**` and `keys/` are told apart (`keys/`, `cache/` and `logs/` sit beside `data/`, `HM/__init__.py:52`; a flat home's old `logs/` moves to `data/logs`, `:54-55`). Deletion test: without it, six lists come back across five packages (`align:` C1).

| Class | Sync switch | Sent | What (paths under `data/` unless marked) |
|---|---|---|---|
| `recipe` | Recipes | yes | `settings.toml` (with any key-shaped value left out by name, below), `profiles/`, `slots/`, `definitions/`, `apps.db` (the mini-app catalogue, `HM/stores.py:73-79`), `library/kinds/`, and Library objects of the recipe kinds (workflow, mini-app, unit, skill, methodology, template, agent, persona, strategy, component, logic) |
| `content` | My content | yes | chats (`claude/projects/<project>/<chat>.jsonl`, `qma/harness/chat.py:535`, and `chats/<id>.json`), `agent-memory/`, `exports/`, `workspaces/`, Library notes, sources, uploads and `session` items, each mini app's volume `apps/<id>/` (`app.db`, `memory.db`, `data/`, `blobs/`, `road/`, `qmx_apps/volume.py:130-134`; its `logs/` is `rebuildable`), `node/`, `migration/pre/**` and `migration/retired/**`, and **any path no rule names** |
| `result` | Run results | yes | `engine/engine.sqlite`, `engine/inbox.sqlite`, `engine/runs/`, `runs.db`, `control.db`, `portfolio.db`, and Library kinds `workflow-run`, `test-report`, `artifact`, `backtest-result` |
| `prices` | Prices that can't be downloaded again | yes | every file under `market/` (frozen months, open months and their `state.json`), until a series carries its own "can be downloaded again" mark |
| `rebuildable` | none | never | `library/catalog.db`, `memory/fts.db`, Hindsight's database, fetched and transient blobs, `cache/` (beside `data/`, the downloaded `cache/prices` included), `logs/`, an app's `logs/`, OpenObserve's data |
| `secret` | none | never | `keys/` (beside `data/`), `vault/**`, `rclone.conf` and any `rclone.conf.unreadable-*`, the four Claude login files (`BK/snapshot.py:71-78`) |
| `scratch` | none | never | locks, SQLite side files, `.part`, staging, heartbeats, process records, `migration/restore-unfinished.txt`, the rest of each Claude home that QMX makes again at launch (the builder lists each from `qma/harness/home.py:199-213`), and every link (the relayed home's `projects/` is a link to the plan home's, `home.py:212`, never followed) |

- **One change from the ticket.** [saved-set-by-class] put unique prices inside `content` while [sync-switch-and-timing] gave them their own switch. Here they are their own class, `prices`, so a switch always names one class.
- **Prices are sent whole, the safe side.** No PC code knows which series can be downloaded again: `keep_series` (`PK/qmx-hub/src/qmx_hub/bucket.py:115`) has no caller outside tests and runs inside the Hub on the server. So every `market/` file is `prices`, as PR 225 copies it today. Downloaded prices live in `cache/prices`, which is `rebuildable` already.
- **A path no rule names is `content`, the safe side**, which is what PR 225 does today (it copies everything in `data/` that is not left out). The table is built from every path the code writes (`STORES`, `LEFT_OUT`, `Volume.create`, both Claude homes), and a lane fills a throwaway folder through each package's own writers and asserts every path it finds has a rule of its own, so the default is a guard, not a habit.
- **Library objects are classed by kind**, read from the live catalog at copy time. An unknown kind reads `content`. The Library's logs (`library/refs`, `edges`, `annotations`, `BK/snapshot.py:92`) are small and every object needs them, so they travel whole in every copy that sends any Library class. A copy whose switches left a kind out holds refs to objects it lacks; the restore names those objects as "left out by your switches", and the build first proves the Library opens such a folder.
- **Per-machine keys are marked, not left out.** A short list in the same table (`disk.floor_gb`, `[telemetry] send_to`, This PC's own place fields, GPU choices, the rclone binary path, and `observers.json`, whose observer token hashes, `QX/service.py:90-94`, belong to the PC that minted them) keeps the new machine's values when a copy is restored onto a different machine. The machine is told apart by the cache's machine stamp (62 section K).
- **A key pasted into `settings.toml` never travels.** The harness lists `settings.toml` among the files that "hold or may hold a login or a key" (`qma/harness/tools.py:909-923`), and a hand edit gets no check. Before a copy is sent, `classes.secret_values(settings)` finds every value under a key named like a secret (the names of `_no_secrets`, `QX/service.py:305-317`, which then reads them from `classes`) or shaped like one (`sk-ant-`, as `qma/harness/project.py:60`, and the other published key prefixes the build lists). Each is left out of the copy by its key path and listed as a key to fill in. `settings.toml` stays on the guard's extra list.
- **Every caller reads the table.** The round sends the classes each storage's switches name. The host's room-making list is the evictable part of `rebuildable`. The harness guard reads `secret` and adds its own extras (the attach route is parked; its guard reads the same list when it is built, which closes the attach review's MUST 6).
- **Keys travel as names.** Each copy carries the list of key names its recipes need (n8n's credential stubs, `src:` 1.8) and the key paths left out of `settings.toml`. After a restore the first start shows them as "keys to fill in", each typed through the write-only key route (section 9). Sign-ins (Claude plan, cTrader, Google) are done again, as on a new device.
- **`data/rclone.conf` is encrypted** with a password kept in Credential Manager and handed to rclone through `RCLONE_PASSWORD_COMMAND` (`sources/rclone-docs-config-encryption-excerpt.md`). He never types it. On a new PC he connects the storage again, which is also the first step of a restore. **It never becomes a lock:** when the password command fails (his old QMX folder opened on a reinstalled Windows, whose Credential Manager is new), the runner sets the conf aside as `rclone.conf.unreadable-<stamp>` (a `secret`, never sent), marks each storage "connect again" with one line, and never loops on the error.
- **No lock (I4).** No `crypt` layer and no passphrase. A key only this PC held would make the copies unreadable exactly when they are needed, so that encryption is ruled out. What protects a cloud copy is the storage's own access (Drive's `drive.file`, `src:` 2.4) and the provider's own encryption at rest; that last point is the coordinator's reading and was not checked against a source.
- **The sealed key copy (planned PR 7)** is parked in the backlog. He never asked for it (`words:29`).

## 3. Where it goes: the storage seam, packs and the one rclone runner

[one-rclone-runner], [packs-and-compression], [spread-over-accounts]

**The seam is the built `Repository` protocol** (`BK/repository.py:192-249`). Two adapters make it a real seam:

- `FolderRepository`, built, for This PC's copies in `backups/quick/` and for a folder on another drive;
- `RcloneRepository`, new, for every rclone kind (Drive, R2, SFTP to his server, rclone's `local` backend in tests).

One correction found by reading the code: the round names the concrete adapter, so the built factory `repository_of(target, layout)` and `source_of(document)` (`BK/plan.py:256-283`) becomes the one `open_storage(place) -> Repository`, chosen by the place row's `via`, and every site that builds a `FolderRepository` itself goes through it: `_send` (`BK/round.py:305`), `carry_on` (`:173`), `_target_key` (`:619`), the quick copy (`:203`, `BK/snapshot.py:183`) and the host's (`HO/backups.py:434`, `:971`, `:1028`, `:1046`). `_guard` (`BK/round.py:443`) and `place_key` (`:613-615`) take any `Repository`, and every adapter gives a stable place key built from the place id, so the restore's `_key` (`BK/restore.py:1151-1158`) stops falling back to `where` for the rclone adapter. The restore already takes any `Repository` (`restore.stage(layout, repo, stamp, ...)`, `BK/restore.py:267`).

**Layout on every storage, This PC's included:**

```
<storage>/QMX-backup/<home_id>/
  backup.toml                      which QMX folder writes here and its last copy (the one file rewritten)
  packs/<ab>/<pack sha256>.pack    many pool files, one zstd frame each, and a list of what it holds
  index/<stamp>-<n>.json           written once per confirmed batch: sha256 -> pack, offset, length; trailer
  index/merged-<stamp>.json        written once by a re-pack: every pack a kept copy uses
  bad/<stamp>.json                 written once by a check or drill: sha256s found damaged
  snapshots/<stamp>/manifest.jsonl written last; header (format qmx-backup/2), one line per file, trailer
```

- **Pool names stay the sha256 of the original bytes**, so the write check (`BK/repository.py:300-317`) and the restore's own check (`BK/restore.py:697-701`; the drill's is at `:1055-1066`) do not change. Callers never see the word "pack": packs live behind `put_pool`, `fetch` and `sweep`.
- **A pack** closes at about 16 MiB or at the end of a round; a larger file gets a pack of its own. Each file is one zstd frame with `checksum_flag` on (Python 3.14 `compression.zstd`, `src:` 3.1). Parquet, PDF and images are stored without compression. No dictionary and no group frames. The pack size is internal, not a setting: he never chooses it.
- **Indexes are written as packs arrive.** After each batch of packs is confirmed on the storage by `lsf`, the round writes one small index file naming them, `index/<stamp>-<n>.json`, with a trailer like a manifest's. So a round killed or cut off halfway leaves every pack that arrived named, and the next round reuses them instead of sending them again. A reader takes the union of every whole index file. An index without a whole trailer is skipped with one incident and rebuilt from the packs' own lists at the next re-pack. The manifest is still written last (I5).
- **A damaged file is marked, not deleted.** A write-once pack cannot lose one frame (I6), so the drill's `discard` (`BK/restore.py:1066`, `BK/repository.py:370-371`) becomes a write of the sha256 into a new `bad/<stamp>.json`. `pool_has` reads the bad lists, so the next round that holds that file packs it again, and the next re-pack drops the damaged pack once no kept copy needs it.
- **The format string changes.** A manifest made with packs says `qmx-backup/2` (today `FORMAT = "qmx-backup/1"`, `BK/repository.py:42`), so an older QMX refuses it with its clear line (`BK/restore.py:503-508`) instead of failing file by file. This QMX reads both.
- **`fetch` is pack-sized and one at a time.** The adapter downloads one whole pack into `cache/sync-fetch/`, reads the frames it needs, and deletes it before the next. A restore, a check and a drill read whole packs anyway, so no range reads are needed. That folder and `cache/sync-staging/` count against the one local floor (section 4), and both are emptied at the next start.
- **This PC's copies hard-link write-once files** (Library objects, frozen price months, the old ticks) into This PC's pool as loose `pool/<ab>/<cd>/<sha256>` files, PR 225's layout, which costs no space on the same drive and keeps a file that is removed or damaged outside QMX's own writers. Where the drive refuses links (exFAT), the copy keeps `at: live` for it and the doctor row says so. Mutable files are packed there. QMX's own writers never remove a write-once file except by a purge, which the restore already handles through its tombstone (`BK/restore.py:636-645`), and the Library's "delete" moves a ref, a mutable file that every copy holds.
- **No migration.** No real folder holds a PR 225 pool yet: 225 to 229 are not landed and his first real start has not happened.
- **Each storage holds a whole copy.** No `union` and no spreading over accounts ([spread-over-accounts]). Two storages are two whole copies.

**One rclone runner on the PC**, `qmx_home.rclone`. It finds the binary (PATH, a path in Settings, or the pinned release fetched into `cache/tools/rclone/` and checked against its published sha256), and refuses with one line any binary older than the pinned minimum. It passes `--config data/rclone.conf` and the password command. A secret never goes in a command line: an R2 key, a server password or any `IsPassword` answer is read from Credential Manager and handed to that one call as rclone's environment variable for the option (the "Env Var" each option documents, as `sources/rclone-drive.md:649-662`), so neither the process list nor the conf holds it. It returns an exit result and one plain line, never rclone's text (I13). It sorts a failure by exit code and by rclone's JSON log read inside the runner (offline, sign-in expired, full, not found), never shown. It records argument names only, with every value of a secret option masked.

**The server keeps its own runners.** The seam is PC against server, not package against package. `qmx node rebuild` runs on the server: it restores into `/srv/qmx/library` (`QX/node.py:96`) and its `_rclone` also runs `systemctl stop` (`QX/node.py:432`, `:455`, `:470-474`), with the server's own config. The Hub's runner (`PK/qmx-hub/src/qmx_hub/bucket.py:72`) runs on the server too. Both stay as built. (The earlier reason, that `qmx-hub` does not depend on `qmx-home`, was wrong: `qmx-hub` depends on `qmx-engine`, which depends on `qmx-home`.) The PC callers, the rclone adapter and the connect dialog, use `qmx_home.rclone`; the mini-app volume backup's runner goes with it (section 13).

**Kept from planned PR 6** (`plan:351-403`): the arrival check (`lsf`), manifest last, never `rclone sync`, the remote-name check, silent errors. **Dropped:** the `cache/backup-send/` hard-link tree.

**Not restic, kopia or rclone `compress`.** restic encrypts every repository with a password it cannot recover, which I4 forbids; it would also replace the tested pool, manifests, keep rule and restore of PRs 225 to 229. rclone `compress` is marked experimental with possible data loss (`sources/rclone-compress.md`).

## 4. The place list, run and keep

[one-place-list], [several-machines-one-storage], [one-free-space-floor], [first-storage]

- **One list**, the built `[engine] placement.<name>.*` rows (`PK/qmx-engine/src/qmx_engine/settings.py:48-65`). This PC (`pc`) is built in and always first. Every other entry is a place. A row gains `via` (how QMX reaches it: `folder`, `rclone`, `ssh`, `modal` or `e2b`) and `can` (`run`, `keep`, or both). A storage is a place that can keep; a folder on another drive is a storage reached `via = "folder"`. This reverses 62's "the second drive is not a place" (62 D1).
- **`kind` keeps its built meaning.** The code already reads `placement.<name>.kind` as the registry kind `owned`, `managed_vm`, `managed_agent_host` or `serverless` (`preflight.py:66`, `:218-222`). The refusal that keeps his plan login off provider machines reads it (`preflight.py:256`, `:283-290`), and the forwarder keeps only `kind == "owned"` (`PK/qmx-engine/src/qmx_engine/service/forward.py:154`). So a connected server is written `kind = "owned"`, Modal or E2B their provider kind, and a storage that cannot run writes no `kind`. The connection type is `via`, a new field.
- **Two corrections found by reading the code:** `places()` lists every placement name (`settings.py:56-65`), and `forward.placement_rows` (`forward.py:160-176`) lists every row without it, so a storage row would appear as somewhere a workflow can run or forward. Both return only rows whose `can` includes `run`. A row with no `can` reads as `["run"]`, which is what every existing row means.
- **A row holds where and what, in one write.** Connecting writes the place row only. Its sync policy is keyed by place id under `[backup]` (the code name stays; the screen says "Sync to my storage"), and a keeping place with no policy reads every default, so nothing is lost if QMX stops between two writes. A policy whose place row is gone is ignored and removed at the next write of `[backup]`:

```toml
[engine.placement.gdrive]          # a storage he connected
id = "01J..."                      # stable, so a rename keeps its history
via = "rclone"                     # folder | rclone | ssh | modal | e2b
can = ["keep"]                     # no kind: it cannot run
remote = "qmx-01J..."              # its remote in data/rclone.conf
client_id = "...apps.googleusercontent.com"   # Drive only; a Desktop client is public, not a secret

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
repack_per_run = "all"             # no limit by default; he can set a size per run
safety = "24h"                     # a pack younger than this, or than two rounds, is never deleted
check_slice = 12
drill = true
before_update_wait = "10m"         # how long an update waits for the sync before it asks
```

  The build picks the exact spellings. What binds is one list in `[engine]` and the policy by place id.
- **`[remote]` and `RemoteSettings` go**, and **`[[backup.targets]]` rows become place rows** with `can = ["keep"]` (section 13).
- **No shared writer (I7).** Each QMX folder writes only under its own `home_id`. Each home prunes and re-packs only its own folder, so no lock is needed (principle separate-before-serializing).
- **Two machines, one home.** A PC that restores a copy takes the copy's `home_id`. If the first PC keeps syncing, the built fork guard refuses whichever writes second, and offers "carry on here" (built, `BK/round.py:170-184`). The guard is check-then-act (`BK/round.py:443-466`), so two rounds that start before either writes a manifest both pass it. Two rules close that. The round reads the storage's newest manifest again just before it writes its own, and writes no manifest (no copy, I5) when another machine wrote since. And no prune or re-pack deletes a pack younger than the safety window (24 hours and two rounds of this home, whichever is later; kopia's time-based safety, `sources/kopia-maintenance.md:85-93`), so a pack another machine sent a moment ago is never deleted under it. Google Drive can hold two files of one name (`sources/rclone-drive.md:1923-1932`); a pack or an index is named by its content or by a stamp, so two of one name hold the same bytes.
- **A stamp is later than every copy it joins.** Today a stamp is moved past the newest copy only in This PC's copies (`_stamp`, `BK/round.py:604-610`), so with those copies off a clock moved back would make the guard name his own storage "another QMX folder". A copy's stamp is later than the newest copy on every storage it is written to and than the last stamp in `backups/backups.jsonl`.
- **One local floor** for every local write, This PC's copies, a folder storage on C:, `cache/sync-staging/` and `cache/sync-fetch/` included: the larger of 1 GiB and `disk.floor_gb`, or a twentieth of free space when that is unset. It replaces the three floors (`PK/qmx-home/src/qmx_home/versions.py:39`, `HO/disk.py:55-62`, `BK/plan.py:320`). **A storage floor** applies to any kind that reports free space (Drive, SFTP, folder), and is editable per storage. R2 reports none and gets none. A storage at its floor stops before writing, with one incident that names the biggest class it holds. Neither floor is a cap (R106).

## 5. When it runs: the switch, the timing and copies on this PC

[sync-switch-and-timing], [copies-on-this-pc]

- **One main switch.** Off pauses every storage and deletes nothing.
- **Per storage, four switches, one per class**, all on by default. A small free storage can drop `prices` while his server keeps them.
- **One round, many storages, one job each.** A round makes one snapshot (`snapshot.make`, built) and writes This PC's copy first. Each other due storage then gets its own send job from that pinned copy, filtered by that storage's switches. This PC's slot is released as soon as its copy is written, so a multi-hour first upload to Drive never holds This PC's hourly copies, the drill or a restore (I7, R136). The pinned copy is kept until every send that started from it ends.
- **This PC's copies** are on by default (R136, "with a local backup always"), hourly when something changed, kept 48 hours then 7 days (the built defaults). They have an off switch (R137) and a cadence. With them off, the round stages its mutable files in `cache/sync-staging/<stamp>/` (scratch, under the local floor), sends them, and removes the staging when the last send ends; staging left by a killed round is removed at the next start. With them off and no other storage, the doctor row says in plain words that his work has no copy anywhere.
- **A torn manifest does not stop pruning for good.** The built sweep refuses while any manifest is not whole (`BK/repository.py:373-378`), and `clean` removes only folders with no manifest (`:391-404`). On a storage without atomic uploads one killed manifest write would leave the storage growing forever. So `clean` removes a torn manifest whose stamp is older than this home's newest whole copy on that storage (it was never a copy, I5), with one incident naming it, and the sweep then runs.
- **Other storages** sync once a day when something changed, at a time he sets. They also sync before every update and on "sync now". A PC that was off syncs at its next start. He can set any cadence down to hourly. Not "on every change": a changed store is sent whole, and `engine.sqlite` changes all day.
- **Keep rule per storage**: the built one (`BK/keep.py`, newest days, weeks and months; the newest and the newest checked copy always kept).
- **The 30-day hold becomes an event.** Pre-change and `before-upgrade` copies are released after the first whole copy reaches a storage on another disk (`BK/keep.py:16`, `:57-61`).
- **Retry is not a setting.** A storage that refused is tried at its next due round. After seven missed rounds the incident says so.
- **`GET` of the sync settings returns every value with its default** (fixes `HO/backups.py:666-690`).

## 6. Maintenance: QMX's own upkeep

[maintenance-repack-and-check]

- **One monthly job per storage, in the host**, This PC included, each step's numbers a setting:
  1. **Re-pack.** Drop packs that no kept copy names. Rewrite a partly used pack only past 5% unused (restic's prune, `src:` 3.2), with a size per run that is "all" by default and editable. The order is new packs, then one merged index `index/merged-<stamp>.json` naming every pack a kept copy uses, then delete the index files it replaces, then the old packs. So every index on the storage names only packs that exist, and no pack a kept copy uses is ever named by no index (I5). No pack younger than the safety window is deleted (I6), and a re-pack writes nothing while a send to that storage runs (I7).
  2. **Check.** Read every index and manifest. Download and verify one twelfth of the packs, a different twelfth each month.
  3. **Drill.** Restore a random copy's mutable files and a sample of its pool into `cache/restore-drill/` (the built drill, `BK/restore.py:427`, scheduled by PR 229; 62 L2's sample rule stays).
- **Sync and maintenance run in the host, not as workflows**, because they must run with fires paused after a restore and before an update. The host's sweep is the one scheduler. The app volume timer and the weekly template's cron go (section 13).
- **Listed apart.** The screen shows "QMX's own maintenance": the host's jobs and the shipped workflows marked `meta.kind = "maintenance"` (`connections-health`, the guard watchdogs). The marker sits in `meta`, outside the content hash (`PK/qmx-engine/src/qmx_engine/definition/model.py:205-212`). Each item has its own off switch.
- **An agent is optional, none by default.** Each host job emits an event when it ends. He can add a maintenance workflow triggered by that event, with an agent step that reads the result. The work itself never moves into the engine.

## 7. Sync before every update

[sync-before-update]

- **One call, `sync_now(why="before-update")`**, which waits `before_update_wait` (10 minutes by default, a visible and editable setting, not a cap) before it asks. It has two callers: the store-upgrade hook in `serve` now (`_copy_before_upgrade`, called at `HO/__main__.py:143`, defined at `:218-245`) and the desktop updater when it exists.
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
- **On a new PC, from the first-start card:** choose "Restore from my storage"; the storage's connect dialog runs (he signs in again); the newest copies show with machine, time and counts, and he picks one; the check shows what is newer on the PC (the built `newer` counts); restore with steps and counts; the handover; keys to fill in; carry on. Storage rows that came with the copy show "connect again", because `rclone.conf` never travels, **except the one he restored from**: after the restore, the row the dialog just wrote replaces the copy's row for that same storage (matched by `via` and where it points: the folder path, or the remote's type and root), so the storage he restored from is connected and carries on syncing.
- **Google Drive on a new PC needs the same Google client.** With `drive.file`, rclone sees "only those files and folders it creates" (`sources/rclone-drive.md:171-176`), and Google ties that access to the app, meaning the OAuth client's project (inferred from `sources/gdrive-api-scopes.md:488-489`; not tried on an account). A Desktop client's id and secret are public, not secrets (`sources/google-oauth-installed-apps.md:278-280`), so they sit in the place row and travel with the recipes. On a new PC the restore card asks for the same client id when QMX ships none, and says where it is in his Google Cloud console. Once QMX ships its own published client (section 9), every PC uses it and the question goes. Proving that a new client sees none of the old copies, and the same client sees them, needs a throwaway Google account he signs in to; builders prove everything up to that card.
- **From Settings:** PR 229's restore while QMX runs, finished at the next start, with the same sources, plus cancel before the next start (UIH section 26 gap 8).
- **Progress with counts.** A restore reports `done` of `total`: "fetching your copy from `<storage>`" in bytes, then "placing the copy's files" in files. Today both stay 0 (UIH section 19 row 11).
- **Also:** a failed restore into a non-default folder is offered again by the card (PR 228 review low 1). A server holding newer Library history is offered after carry-on (Library AD-14 `adopt`).

## 9. The one connect dialog

[connect-dialog], [connect-storage], [connect-compute], [connect-deep-logs]

**A connection kind is an ordered list of steps**, each `(name, who, check, do)`, where `who` is `his` or `qmx`. One job runs a kind on the built job runner (`HO/jobs.py:77-133`). It skips every step whose `check` passes, runs QMX's steps in order, and finishes with `{needs: <his step>}` at a step only he can do. The screen shows that card. When he is done the same job runs again. Resuming is rerunning, so no state machine is saved (principle make-operations-idempotent); the one thing a card carries back is rclone's own `state` string for the question loop. The last QMX step writes the place row with `via` and `can`, then runs the kind's health check (I12). The first-start card's job route (`/api/first-start/jobs/{id}`) runs the storage kind too, so a restore works before any host exists.

**One step holds a live process: the Google sign-in.** rclone's browser sign-in waits on a local listener (`http://127.0.0.1:53682/`, `sources/rclone-drive.md:93`), and ending a job would kill it. So the sign-in is its own long job, `rclone authorize drive --auth-no-open-browser` (`sources/rclone-cmd-rclone_authorize.md:26-27`), which never opens a browser itself. Its card shows the `127.0.0.1` link; he opens it; the job reads the token into the encrypted conf and ends; the storage kind then reruns. Cancelling the card stops the job.

**Routes**, one backend for the screen and the copilot (R145):

- the list of kinds and what each can do (run, keep, both), for the dialog's first question;
- start or rerun a connect job, and read it;
- **a write-only key route**: put a named key into Credential Manager, never read it back, and list which names are set. It serves an R2 key, a Modal or E2B key, and the cTrader app id and secret (UIH section 26 gap 3).

**Storage kind:**

1. His: choose the kind. "Another drive" is one choice and carries the second-drive suggestion (`BK/plan.proposal`, `BK/plan.py:296`). A folder needs no rclone, so connecting one works offline (I1).
2. QMX, for a kind that needs rclone only: get rclone (PATH, Settings, or the pinned release, checked), refusing one older than the pinned minimum.
3. In turns: **rclone's own question loop.** `rclone config create <name> <type> --non-interactive` answers with the next question as JSON, and the dialog shows it as one card, built from the parsed fields only (I13), and sends the answer back with `--state` and `--result` (`sources/rclone-cmd-rclone_config_create.md:88-111`). With `--continue` rclone wants passwords "in the clear" (`:109-110`), so an answer to an `IsPassword` question never goes in `--result` on the command line: it goes to Credential Manager through the key route and reaches rclone as an environment variable on that one call (section 3). Whether rclone takes `--result` from its environment the way it takes every flag is the build's first check; where it does not, the loop refuses an `IsPassword` question with one line and QMX handles that kind's secret itself, as it does for R2. Any other rclone kind works with no QMX code per kind; QMX pre-fills what it knows for Drive, R2 and SFTP.
4. QMX: test with free space (where reported) and a small write, read and delete.
5. QMX: write the place row (`via`, `can = ["keep"]`), one write; its policy reads the defaults (section 4).
6. QMX: run the first sync with steps and counts.

Per kind. **Google Drive** uses a "Desktop app" client with PKCE and the `drive.file` scope; rclone's shared client stops working during 2026 (`sources/rclone-drive.md:47-49`). It is a one-click choice only once QMX ships its own published client. Until then the Drive card says in plain words that making the client takes about ten minutes in Google Cloud, links the steps, and offers another drive or his server instead (his E1 answer asks for less friction). The card also says the client must be set to "In production": Google expires the sign-in of a client left in "Testing" after 7 days (`sources/google-oauth2-overview.md:575-576`). Registering QMX's own client is his one-time step, never a builder's. **R2** is `type = s3, provider = Cloudflare`, with `no_check_bucket = true`; its key goes through the key route and reaches rclone by environment, so `rclone.conf` holds none. **His server** is SFTP over Tailscale with the key file the server kind made in `keys/`, offered once the server is connected as compute (R142). **A folder** uses the folder adapter with no rclone; a folder inside the QMX folder is refused, and one on the same drive is kept with a warning. **Never** the QMX folder itself inside a live-sync folder (UIH section 19 row 8).

**A sign-in that ends.** Google also ends a refresh token unused for six months or past 100 per client (`sources/google-oauth2-overview.md:540-582`). The runner sorts that failure apart from "offline" (section 3), and the storage reads "sign in to `<storage>` again" with the one card that reruns the sign-in job.

**Compute kinds.** A server: his cards (choose and pay, the address, a Tailscale one-off auth key, the server password typed in the terminal QMX opens, approve the firewall step); QMX's checked steps (the `qmx node setup` sequence, `setup_steps` at `QX/node.py:616-652`, split into steps; the place row with `via = "ssh"`, `kind = "owned"` and `can = ["run", "keep"]`; the status ladder `available → configured → authorized → reachable → healthy`, giving `PK/qmx-engine/src/qmx_engine/triggers/preflight.py:231` (`placement_state`) its first caller; a one-node smoke test on its own engine; `qmx-recover status` in plain words, R139). Then his later choices, each on its own screen: deep logs there, a storage there, datasets kept there. Key compute (Modal, E2B, a GPU on Modal): his key card, one provider test call, the place row (`via` = `modal` or `e2b`, its provider `kind`, `can = ["run"]`). No server step is ever part of the first start (R142).

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
| 1 | `[remote]` and `RemoteSettings` (`PK/qmx-remote/src/qmx_remote/models.py:124-142`, `QX/service.py:44`, `:65`, `:840-846`) | no reader but the write check; the settings writer keeps unknown sections word for word; `Target` stays | about 28 |
| 2 | The weekly GitHub snapshot: `QX/backup.py`, its command (`QX/__main__.py`), operation and route (`QX/service.py:46`, `:1346-1360`), template `backup-weekly/`, catalog row (`PK/qmx-engine/src/qmx_engine/templates/catalog.py:397-401`) and test | everything it copies is in the saved set; it installs disabled and nothing runs it; an old `repository` key is ignored, not refused | 356 code, 141 tests |
| 3 | Plan text for planned PRs 6 and 7 (`plan:351-459`); PR 7 to the backlog; the `sealed_keys` hook in `BK/round.py` and `HO/backups.py` | no built code depends on it | 109 plan lines, the hook |
| 4 | ~~The old bundle installer~~ | **struck by the review (M6)**: `tools/build_release.py:207-208` and `:255-256` copy `release/launcher.py` and `release/install.py` into the bundle, and `tools/tests/test_runtime_wheel_closure.py:63` loads `install.py`. The installer, its builder and that test stay until the desktop session replaces the builder | 0 |
| 5 | Three free-space floors into one | the 1 GiB minimum still guards a pre-change copy | about 10 |
| 6 | The fixed hourly copy becomes This PC's policy with an off switch | the doctor row says so when no copy exists anywhere | about 5 |
| 7 | The mini-app volume backup: `backup()`, `restore()`, `BackupSettings` and `_rclone` in `PK/qmx-apps/src/qmx_apps/backup.py`, `backup_schedule.py`, their wiring (`QX/service.py:26-27`, `:630`, `:1628`, `:1703-1705`), `APP_KEYS` (`BK/plan.py:49`) and `_volume_keys` (`QX/service.py:300-302`) | **after** the round copies each app's `road/` under the road lease, which the host hands the round as a hook because `qmx-home` cannot import `qmx-apps` (`VolumeLease(home / "road-locks", app_id)`, `qmx_apps/backup.py:135-143`). The round already copies every SQLite file, `app.db` and `memory.db` included, by `VACUUM INTO` from a `mode=ro` connection (`BK/snapshot.py:339`, found by its header at `:489`), so no live store tears. `snapshot` and `checksum` stay, moved into `qmx_apps/volume.py`, because the supervisor's handovers and the road check import them (`supervisor.py:34`, `road/validation.py:14`). "Restore one app" goes to the backlog. Litestream stays | about 250 code, about 90 tests |
| 8 | ~~The node rebuild's own rclone runner~~ | **struck by the review (M7)**: it runs on the server and also runs `systemctl` (`QX/node.py:432`, `:455`, `:470-474`); it stays | 0 |
| 9 | The `cache/backup-send/` hard-link tree | never built; struck from the plan | 0 |

**Size:** about 650 lines of code and templates and about 230 lines of tests (items 1, 2, 3, 5, 6 and 7), plus 109 plan lines. Kept on purpose: the second-drive proposal (a suggestion in the dialog), the status ladder (it gets its first caller), the trading node's backup and QMF's backup block, the Hub's bucket push, the node rebuild's runner and the old bundle installer.

## 14. Failure paths, and how each is proven without an account

[one-free-space-floor], [several-machines-one-storage], [sync-before-update], [first-storage]

**Proof rules.** Every lane runs on throwaway QMX folders under one `homes/` root, as PR 229's lanes do (`owner_lanes.py` refuses a home outside `homes/`). Storages are throwaway folders: the folder kind directly, and the rclone adapter through rclone's `local` backend named in a throwaway `rclone.conf`. Fake secrets are planted in three places: a token in that config, an answer to an `IsPassword` question of the loop, and a key pasted into a hand-edited `settings.toml`. Every lane greps its answers, job lines, logs, the process list it records and the storage for each of them and for every `secret` path (I3, I13). No lane uses a real account. The Drive kind is driven up to the card where he would sign in. A test seam slows the folder adapter's copy, because `RCLONE_BWLIMIT` slows only rclone. I4 for Drive (a new PC sees its copies) needs a throwaway Google account he signs in to; it is his step, not a lane.

| Path | What must happen | The proof |
|---|---|---|
| **Offline** | The cloud storage reads "not reached" with one line. This PC's copies go on. The storage is tried at its next due round and the incident counts missed rounds. `sync_now(why="before-update")` from `serve` falls back to the local copy and the upgrade goes on | an rclone `sftp` remote at `127.0.0.1` on a closed port: a round answers `skipped` for it and `finished` for This PC; a `serve` store upgrade with it configured completes with one fallback line |
| **Full storage** | At its floor the storage stops before writing, with one incident naming its biggest class; other storages go on. A storage that fills mid-round leaves no copy (I5), and the next round reuses what arrived | the per-storage floor set above the throwaway drive's free space: refused before any file is written. `RCLONE_MAX_TRANSFER=1M` with hard cutoff in the host's environment: no manifest, then a normal round converges and its copy restores hash-equal |
| **A pulled drive** | The folder storage reads "not there (is its drive plugged in?)" (`BK/round.py:324`); a pull mid-round leaves no copy; the next round with the drive back converges | `subst Q: <throwaway>` (no admin), a folder storage on `Q:\`, `subst Q: /d` during a slowed round, then `subst` again and one more round; every kept copy restores hash-equal |
| **A killed sync** | No manifest means no copy. `clean` removes what the round left. The next round reuses every pack a batch index names, and the re-pack drops packs nothing names once they pass the safety window. A re-pack killed at any point leaves every index naming only packs that exist, and every pack a kept copy uses named (section 6 order) | kill the host process during a round slowed with `RCLONE_BWLIMIT` (rclone) or the folder seam (folder), restart, run a round and assert it sent no pack twice, restore every kept copy and compare every hash and SQLite row count; the same for a re-pack killed after each of its steps |
| **Two PCs** | Different homes write different folders and never touch each other's packs. Two machines on one `home_id` (after a restore) hit the fork guard, which offers "carry on here". Two rounds that start together never leave a copy that names a deleted pack | two throwaway folders A and B on one storage: both sync and prune, and A's copies all restore after B's prune. Then B restores A's copy and two hosts on one `home_id` run rounds and a re-pack at the same moment, many times: every manifest on the storage restores hash-equal, and the round that wrote second wrote no manifest |
| **Sign-in expired** | The storage reads "sign in to `<storage>` again" with the one card; the incident says so; This PC and other storages go on | an rclone runner fake that answers with an expired-token log line: the round's line, the incident and the job's `needs` name the sign-in, never "not reached" |
| **A storage that disappears** | Deleted folder or bucket: `backup.toml` is gone, so the fork guard refuses until he carries on, then a whole new copy is sent. Removed remote or revoked access: "not reached; connect it again", and rerunning the dialog skips every step that still passes. Nothing on This PC or another storage is touched | delete the storage folder between rounds; then remove the remote from the throwaway `rclone.conf` and rerun the storage kind: only the remote step and the first sync run again |
| **A corrupted pack** | The monthly check names the pack, writes its files to a bad list and opens an incident. A restore that needs it stops with the file named; damage is limited to that pack; the next round packs the named files again | flip one byte in one pack of a throwaway storage; run the check; run a restore; run a round and assert the files are in a new pack |
| **A torn index or manifest** | An index without its trailer is skipped with an incident and rebuilt at the next re-pack; a torn manifest older than the newest whole copy is removed by `clean` and pruning goes on | truncate one index and one manifest on a throwaway storage, run a round, then a re-pack |
| **Drive without an account** | The dialog reaches the sign-in card and stops there, with nothing written to the place list, and no browser opened | run the storage kind with kind `drive` and assert the sign-in job's card holds a `127.0.0.1` link, no browser process started, then stop the job and assert no place row |

The invariants each get one literal check on the same lanes. I2: a lane fills a throwaway folder through each package's own writers and asserts every path it finds has a rule, then that the storage holds exactly the four sent classes. I8: delete a strategy, sync, and restore the earlier copy, on This PC and on a folder storage; then remove a write-once file by hand and restore it from This PC's copy. I10: PR 229's lane 4 as fixed (section 15). I14: section 15's heartbeat test, and a `PUT /api/settings/engine` sending one key that leaves every other key.

## 15. PRs 225 to 229: kept, reshaped and removed

`align:` A1 to A3, read against the code.

| PR | Kept | Reshaped | Removed |
|---|---|---|---|
| **225** copy engine | the sha256 pool, the manifest with its trailer, the size and `mtime_ns` skip, `VACUUM INTO` from `mode=ro`, the copy order, `WRITE_ONCE` and `at: live`, the keep rule, the fork guard, the refusals (inside the QMX folder, links), the `qmx_home.files` helpers | `LEFT_OUT`, `SECRET` and `WRITE_ONCE` (`BK/snapshot.py:37-87`) become readers of the class table; the pool file format becomes packs inside the adapters; the round opens storages through `open_storage(place)`; the three floors become one; the 30-day hold becomes an event; `[[backup.targets]]` and `Target` become place rows; the second-drive proposal becomes a dialog suggestion; the fixed hourly copy becomes This PC's policy | the "everything in `data/`" rule; the `sealed_keys` hook |
| **226** restore | stage and finish, the set-aside, `replace`, purges kept, the lock order, carry-over of leases | the source is any `Repository`, so any storage; progress reports `done` of `total` | none |
| **227** host service | rounds on the host's thread, one `backup` job and 409, incidents, the doctor row (new words), the CLI, `PUT` checked by `BK/plan.parse` | `GET` returns every setting with its default; incidents join `GET /api/inbox`; the host's sweep becomes the one scheduler and gains the monthly upkeep; the fixed 1-hour retry becomes the next due round | `APP_KEYS` and `_volume_keys` (with the volume backup) |
| **228** card restore | restore into a new folder (marker first, pointer after finish), `serve` finishing a staged restore, the restore CLI, the `before-upgrade` copy | the card gains "restore from my storage"; `serve`'s store upgrade calls `sync_now(why="before-update")` first and keeps the local copy as the fallback; `pre-*` copies are released once a `before-upgrade` copy exists; low 1 (a failed non-default restore offered again) | none |
| **229** restore from Settings | the staged restore, cancel, carry-on, the after-restore pause by merge, purge again, the memory rebuild with `reindexed` on success, `restore.lock` in `single_instance`, the set-aside view | the drill's schedule becomes step 3 of the monthly upkeep; Settings' restore takes the storage sources | none |

**Overtaken by PR 229's fix round (review N1, N2).** What this section asked for is done on `build/br5`, and the sync work stacks on it:

- **Stacking is done.** `e8026bc8` joins PR 228 (`1e9f695a`) under PR 229 by a merge commit, and `78587edc` is the fix round on top.
- **Lane 4 is fixed and passes.** The diagnosis (`wrapup/evidence/br5/owner-lane4-diagnosis.log`) showed the only fire was one the copy already held, made by the host that took the copy. The lane now makes the quick copy in process and counts fires by id and run start. It passes "the copy holds the trigger past due and no fire of it" and "no fire ran before carry-on" (`wrapup/evidence/br5/lanes-fix.log:30-32`). The product's order held: `hold_after_restore` sets the pause before the engine opens.
- **Lane 3 is fixed and passes.** The lane's stop now waits for the whole process tree.
- **The Hub heartbeat merges.** `hear` (`HO/host.py:1024-1038`) reads the nested `autonomy` table and changes it through `settings_update` (`QX/service.py:782-790`), which writes nothing when the section is unchanged. The lane shows `[engine]` keeping `host_name`, `disk.floor_gb` and the scheduler keys beside the pause (`lanes-fix.log:33`). The fresh reviewer's verdict is CLEAN at `78587edc` (`wrapup/review/br5-check-78587edc.md`).
- **What is still open belongs to this design.** The REST route `PUT /api/settings/{section}` still replaces the section it is sent (`settings[section] = values`, `QX/service.py:918`), so a screen saving from an old read would undo the host's merge writes to `[backup]` and `[engine]` (`HO/backups.py:769`, `:884`, `:919`) and drop place rows. I14 now covers the route: it merges the keys sent, and a key is removed only when the body names it. That lands in the sync program's first PR, before any storage row lives in `[engine]`.

## 16. Build order (dependency units for the planner, not a PR count)

Each unit ends in its own check from section 14. The planner cuts the fewest PRs the code needs (`words:219`); `../../SYNC-PLAN.md` cuts these into five PRs in three waves.

1. ~~PR 229's fix round~~, done at `78587edc` (section 15).
2. The subtract items 1, 2, 3, 5 and 6, and the settings route that merges (I14).
3. The class table and secret list, with the guard and the settings scan reading it, the road-lease copy of app data, then subtract item 7.
4. Packs inside `FolderRepository`, This PC's policy with staging when it is off and hard links for write-once files, the one floor.
5. The one rclone runner, `RcloneRepository`, `open_storage`, place rows with `via` and `can`, the `places()` and `placement_rows` filter, the policy by place id, `GET` with defaults.
6. The connect-dialog backend and the storage kind, the write-only key route, `[telemetry]`'s check.
7. Restore from a storage on the card and in Settings, progress counts, cancel, keys to fill in, the restored storage's row merged.
8. The monthly upkeep with the maintenance list and its event; sync before update and the `pre-*` release; the read-only store named.
9. The compute kinds and the deep-logs kinds; run place on the run read; incidents in the inbox.

## 17. Deferred, and out of scope

- **Sizes from his real folder.** The saved set, the growth of This PC's copies and the size of `engine.sqlite` are estimates (`inv:` 1). The first real start measures them. Revisit only if they are large: append-only run results, chunking, a dictionary, spreading.
- **Encryption that needs no memory.** None is built. Any later design must keep a copy readable on a new PC with only his storage sign-in (I4).
- **A folder storage on a drive that comes back under another letter** reads "not there" until he edits its path. Finding it by `backup.toml` is backlog.
- **"Make this a new home"** (a second PC that restored a copy minting its own `home_id`) is in no ticket (review N5), so it is backlog under "let's not expand the domain". The fork guard's built "carry on here" stays the one choice, and the safety window keeps two writers from damaging each other meanwhile.
- **Proving Drive on a new PC** (I4 for Drive) needs a throwaway Google account he signs in to, once QMX's own client is registered. It is his step after the program, not a builder lane.
- **The old bundle installer** (`release/install.py`, `release/launcher.py`) stays with its builder until the desktop session replaces it (review M6).
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
| D2, `[placements]` and the backup targets naming a place | section 4 (the built `[engine] placement.*` list with `via` and `can`) |
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

## 20. Review folded

The review `D:/QMX-worktrees/qma-ship/wrapup/review/design-sync-edge-cases.md` (13 MUST, 16 SHOULD, 9 NOTE) is folded here on 2026-10-28. Each finding was checked against the code at `build/br5` `78587edc` before it was folded. Two were partly wrong, and the part that was wrong is said below; the rest of each is folded.

**MUST**

- **M1, `kind` already means the registry kind.** Verified (`preflight.py:66`, `:218-222`, `:256`, `:283-290`; `forward.py:154`, `:160-176`). Changed: the connection type is a new field `via`; `kind` keeps `owned` and the provider kinds; `places()` and `forward.placement_rows` both filter by `can` (section 4).
- **M2, the class table missed real paths.** Verified (`chat.py:535`, `home.py:212`, `HM/stores.py:73-79`, `volume.py:130-134`, `BK/snapshot.py:92`). Changed: the paths are corrected and rooted at the QMX folder; `apps.db`, the whole app volume, the Library logs, `library/kinds` and `migration/**` have rows; an unnamed path is `content`; a lane asserts every path the writers make has a rule (sections 2 and 14).
- **M3, a key pasted into `settings.toml` would travel.** Verified (`tools.py:909-923`, `QX/service.py:305-317`). Changed: `classes.secret_values` leaves every key-named or key-shaped value out of the copy by key path and lists it as a key to fill in; `_no_secrets` reads the same names (section 2).
- **M4, nothing makes the `keep_series` split.** Verified (`bucket.py:115` has no caller outside tests). Changed: every `market/` file is `prices` and is sent (section 2).
- **M5, subtract item 7 deleted imported code and named the wrong lease.** Verified for the imports (`supervisor.py:34`, `road/validation.py:14`) and for the lease (`qmx_apps/backup.py:135-143` is the road lease). Partly wrong: a live `app.db` does not tear, because the round already copies every SQLite file by `VACUUM INTO` from `mode=ro` (`BK/snapshot.py:339`, `:489`). Changed: `snapshot` and `checksum` move into `volume.py`; only the volume backup itself goes; the host hands the round a road-lease hook (section 13).
- **M6, the old installer is named outside `release/`.** Verified (`tools/build_release.py:207-208`, `:255-256`; `tools/tests/test_runtime_wheel_closure.py:63`). Changed: item 4 is struck; the installer stays with the desktop session (sections 13 and 17).
- **M7, the rclone seam is PC against server.** Verified (`QX/node.py:96`, `:432`, `:470-474`; `qmx-hub` depends on `qmx-engine`, which depends on `qmx-home`). Changed: the node rebuild's and the Hub's runners stay on the server, item 8 is struck, and the wrong reason is corrected (sections 3 and 13).
- **M8, two machines on one `home_id` could delete each other's new packs.** Verified (`BK/round.py:443-466` checks then acts; `BK/repository.py:372-385` deletes any unnamed pool file at once). Changed: a safety window (24 hours and two rounds) before any pack is deleted, and the guard read again just before the manifest; a lane runs two hosts at once (I6, I7, sections 4 and 14).
- **M9, dropping a copy's index orphaned shared packs.** Verified by reading the layout. Changed: dropping a copy removes only its manifest; index files go only in the re-pack after a merged index (I5, section 6).
- **M10, a killed round could not reuse arrived packs.** Verified by reading the layout. Changed: a small index per confirmed batch, with the manifest still last (section 3).
- **M11, This PC's `at: live` gives no undo for a write-once file.** Partly wrong: QMX's own writers remove a write-once file only by a purge, which the restore handles (`BK/restore.py:636-645`), and the Library's delete moves a ref, which every copy holds, so the strategy lane passes on This PC. Right for a file removed or damaged outside QMX (`BK/restore.py:644-651` refuses then). Changed: This PC hard-links write-once files into its pool, with `at: live` and a doctor line only where links fail (section 3).
- **M12, secrets would sit in command lines the runner records.** Verified (`sources/rclone-cmd-rclone_config_create.md:109-110`). Changed: no secret in argv; it reaches rclone as an environment variable from Credential Manager; argument names only are recorded; the loop's `IsPassword` path is the build's first check with a stated fallback (sections 3 and 9).
- **M13, `drive.file` ties copies to one Google client.** Verified as an inference from the sources (`rclone-drive.md:171-176`, `gdrive-api-scopes.md:488-489`); not tried on an account. Changed: a Desktop client is public (`google-oauth-installed-apps.md:278-280`), so its id travels in the place row; the restore card asks for the same client id until QMX ships one published client; the account proof is his step (sections 8, 9 and 17).

**SHOULD**

- **S1, I13 against the question cards.** Changed: I13 names the parsed fields that reach a card and masks `IsPassword` defaults (section 1).
- **S2, the Drive sign-in holds a live listener.** Verified (`rclone-drive.md:93`, `rclone-cmd-rclone_authorize.md:26-27`). Changed: the sign-in is its own long job with `--auth-no-open-browser`; the lane asserts the `127.0.0.1` link and that no browser started (sections 9 and 14).
- **S3, an expired Google sign-in had no row.** Changed: the runner sorts that failure, the storage reads "sign in again", the card requires "In production", and section 14 has the row.
- **S4, registering a Google client is not a click.** Changed: the Drive card says it takes about ten minutes until QMX ships its client, and offers another drive or his server (section 9).
- **S5, a slow storage held This PC's copies.** Changed: one send job per storage from a pinned copy; This PC's slot is released once its copy is written (I7, section 5).
- **S6, a clock moved back could trip the guard.** Verified (`BK/round.py:604-610` checks only This PC's copies). Changed: a stamp is later than every storage's newest copy and the log's last stamp (section 4).
- **S7, no repair for a damaged pack or index.** Verified (`BK/restore.py:1066`, `BK/repository.py:370-371`). Changed: a write-once bad list that `pool_has` reads, a trailer on every index, and an unreadable index skipped with an incident and rebuilt (section 3).
- **S8, a torn manifest stopped pruning for good.** Verified (`BK/repository.py:373-378`, `:391-404`). Changed: `clean` removes a torn manifest older than the newest whole copy, with an incident (section 5).
- **S9, the floor missed the new local writes.** Changed: staging and the fetch cache count against the floor, one pack is fetched at a time, and stale staging goes at start (sections 3, 4 and 5).
- **S10, rclone fetched before a kind is chosen.** Changed: the kind is chosen first, a folder needs no rclone, and an rclone older than the pinned minimum is refused (sections 3 and 9).
- **S11, the encrypted conf as a lock after a reinstall.** Changed: a conf that cannot be opened is set aside, each storage reads "connect again", and nothing loops (section 2).
- **S12, the storage he restored from read "connect again".** Changed: the row the dialog wrote replaces the copy's row for that same storage (section 8).
- **S13, the settings route still replaces a section.** Verified (`QX/service.py:918`). Changed: I14 covers the route; `PUT` merges the keys sent and removal is named (sections 1 and 15).
- **S14, several lanes could not fail as claimed.** Changed: a concurrent two-host lane, a folder slow-down seam, secrets planted in a loop answer and a hand-edited `settings.toml`, and Drive's I4 marked as his step (section 14).
- **S15, the format string did not change.** Verified (`BK/repository.py:42`). Changed: packed manifests say `qmx-backup/2`, and this QMX reads both (section 3).
- **S16, `open_storage` missed call sites.** Verified (`BK/round.py:173`, `:613-619`; `BK/restore.py:1151-1158`). Changed: the built `repository_of` and `source_of` (`BK/plan.py:256-283`) become `open_storage`, and every `FolderRepository(...)` site, the host's four included, goes through it with a stable key per place (section 3).

**NOTE** (folded where cheap; none changes his rules)

- **N1 and N2.** Section 15 now reads the fix round at `78587edc`. Lane 4's assertion settled on "no fire before carry-on" with the copy holding no fire, and it passes.
- **N3.** The restore's own check is cited at `BK/restore.py:697-701` (section 3).
- **N4.** `observers.json` is per-machine (section 2).
- **N5.** "Make this a new home" moved to the backlog (section 17).
- **N6.** UI gaps 1, 3 and 5 stay in through the closed ticket [ui-gaps-that-belong]; the coordinator tells him in one line that they ride along.
- **N7.** `class_of` takes paths relative to the QMX folder (section 2).
- **N8.** The re-pack's size per run ("all") and the update's wait (10 minutes) have visible, editable defaults (section 4).
- **N9.** Connecting writes the place row only; a policy with no row is ignored and removed (section 4).
