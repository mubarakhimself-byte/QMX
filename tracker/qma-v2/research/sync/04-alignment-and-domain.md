# Sync to my storage, and connect from the screen: alignment and domain

Written 2026-10-28 for the sync design round. Method: the `codebase-design`, `domain-modeling` and `principle-subtract-before-you-add` skills. Nothing was run, built or changed; this file is the only output.

Where the references point:

- `words:` is `research/sync/01-his-words-2026-10-28.txt` (his seeds tonight and the coordinator's replies he answered). `inv:` is `02-inventory.md`, `explore:` is `00-backup-explore.md`, both in the same folder.
- `plan:` is `tracker/qma-v2/BACKUP-RESTORE-PLAN.md`. `design:` is `research/methodology/62-local-first-design.md`. `rulings:` is `research/methodology/26-operator-rulings-and-alignment.md`.
- `review:` is `D:/QMX-worktrees/qma-ship/wrapup/review/`. `machines:` is `D:/QMX-worktrees/qma-ship/wrapup/evidence/machines-design-vs-backend-2026-10-27.md`. `attach:` is `tracker/qma-v2/ATTACH-PLAN.md` at `b08f13e7`.
- `QA/` is `D:/QMX-worktrees/bld-br4/qmx-agents/packages/` at `1e9f695a` (PRs 225 to 228). `BR5/` is `D:/QMX-worktrees/bld-br5/qmx-agents/packages/` at `1e5aaabd` (PR 229). `BK/` is `QA/qmx-home/src/qmx_home/backup/`, `HO/` is `QA/qmx-host/src/qmx_host/`, `QX/` is `QA/qmx-control/src/qmx_control/`.

## What tonight's seeds say, in one paragraph

He does not want copies piling up on his laptop (C: 17 GB free, D: 58 GB, words:101, :108). He wants what games and Chrome do: one switch, his stuff kept in "his account", and a reinstall six months later picks up as if he never left (words:151). Save only what matters: the recipes (JSON definitions, as n8n, OpenCode and Claude Code do), his own content and the run results that cannot be made again; rebuild everything else (words:185, :188-195). Compress it, and re-pack and check it as monthly upkeep (words:185, :197). rclone reaches Google Drive, R2, Contabo and his server, so a friend connects their own Drive (words:185, :201). Sync before every update (words:185, :203). Upkeep workflows are QMX's own and must not be confused with his strategy workflows (words:219). Compute, storage, GPU and OpenObserve are connected from the screen through a step-by-step dialog that sets itself up or hands him a link, a wizard or the copilot (words:219). Self-hosted OpenObserve, not its cloud (words:219). No eight PRs; the planning workflow justifies the count (words:219).

---

## A. Ledger of earlier decisions

Status: **PR** shipped in a built PR (225 to 228 reviewed CLEAN, 229 built and not reviewed, one live check failing, words:53); **designed** written in a plan or design and not built; **chat** said in chat only; **reversed** reversed tonight. Verdict: **keep**, **reshape** (kept, changed by tonight's seeds) or **retire**.

### A1. The copy engine (B1, PR 225)

| # | Decision | Status | Verdict | Where |
|---|---|---|---|---|
| 1 | Each place holds a pool with each file once by sha256, plus one manifest per copy; the manifest ends with a trailer line, and a copy without a whole trailer is unreadable | PR 225 | keep. This is the sync's store; only the pool's file format changes (packs, D3) | `BK/repository.py:1-25`, `:192-249`; plan:541 |
| 2 | A file whose size and `mtime_ns` match the last manifest is not read again; a round with nothing changed writes nothing | PR 225 | keep. It is what makes "sync on change" cheap | `BK/snapshot.py:9-12`; plan:535, :593 |
| 3 | SQLite copied by `VACUUM INTO` from a `mode=ro` connection | PR 225 | keep | plan:76, :475 |
| 4 | Copy order: stores, then Library logs, then other mutable files, price month data before its `state.json`, written-once files last | PR 225 | keep | plan:540 |
| 5 | `SECRET`: `vault/**`, `rclone.conf`, the four Claude login files, all of `keys/`, never in a copy in clear | PR 225 | keep, and it becomes the one secret list (C4) | `BK/snapshot.py:71-78`; plan:536 |
| 6 | `LEFT_OUT`: indexes, Hindsight's database, evictable blobs, price cache, scratch, locks, SQLite side files | PR 225 | reshape. It becomes the "rebuildable" and "scratch" classes of one table (C1); add `migration/restore-unfinished.txt` (review br4-check-1e9f695a.md, last edge case) | `BK/snapshot.py:37-62`; plan:537 |
| 7 | `WRITE_ONCE`: Library objects, born blobs, tombstones, frozen price months, migration folders | PR 225 | keep | `BK/snapshot.py:80-87`; plan:539 |
| 8 | Everything in `data/` is copied except the lists above; all of `market/` included | PR 225; design C1 | reshape. Copy by class: recipes, content and results go; prices go only when they cannot be downloaded again (inv:38) | design:229-235; `BK/snapshot.py:81-88` |
| 9 | The quick undo runs every hour, always on, 48 hours then 7 days | PR 225 and 227 | reshape. A setting with an off switch and a cadence he edits (words:101; explore:26); it copies the same classes as the sync | `HO/backups.py:273`; `BK/plan.py:140`; plan:513 |
| 10 | Quick-undo files written once stay live in `data/` and are named `at: live` | PR 225 | keep | plan:535 |
| 11 | The second drive is a proposal he accepts, never a target by itself | PR 225 and 227 | keep, demoted: one suggestion on the storage dialog's first question | plan:533 (E-M8); `HO/backups.py:531-566` |
| 12 | Keep rule counts the newest days, weeks and months that hold a copy; the newest and the newest drilled copy are always kept | PR 225 | keep, for every storage | `BK/keep.py`; plan:542 (E-M5) |
| 13 | Pre-change and `before-upgrade` copies are held until 30 days after the first copy to another drive | PR 225 | reshape. "After the first sync to his storage". Without one, they are kept forever today (explore:58) | `BK/keep.py:16`, `:57-61`; design:217 |
| 14 | Fork guard: a place another QMX folder wrote to, or a place whose `backup.toml` vanished, is refused until he carries on | PR 225 | keep. It matters more now: a second laptop or a friend can point at the same Drive | plan:543 (E-S7) |
| 15 | A copy refuses whole before writing when room is short; the quick undo stays above the larger of 1 GiB and the host's floor | PR 225 | reshape into one floor (C4). A folder he names on C: has no floor today (explore:64) | `BK/snapshot.py:188-195`; `BK/round.py:229` |
| 16 | A target inside the QMX folder is refused; one on the same drive is kept with a warning | PR 225 | keep | plan:76 |
| 17 | Links and junctions are never followed | PR 225 | keep | plan:76 |
| 18 | The copy helpers moved to `qmx_home.files` | PR 225 | keep | `QA/qmx-home/src/qmx_home/files.py` (254 lines) |
| 19 | Compression | not built | add (packs, D3; words:197) | inv:65-83 |

### A2. Restore (B2, B4, B5; PRs 226, 228, 229)

| # | Decision | Status | Verdict | Where |
|---|---|---|---|---|
| 20 | Every restore is checked, then confirmed: it shows the runs, Library moves, chats and price months it would replace | PR 226, 228, 229 | keep | plan:544 (E-M1); App G:605 |
| 21 | A restore sets `data/` aside whole in `backups/before-restore-<stamp>/`, never deleted by QMX; Settings shows their total size | PR 226, 229 | keep | plan:545; E-S13 |
| 22 | Secrets and app leases are carried over from the set-aside data | PR 226 | keep | plan:538 |
| 23 | Another folder's copy replaces data only with `replace` | PR 226, 228 | keep | plan:608 (E-S8) |
| 24 | A purged blob is never restored, and is purged again at the first start | PR 226, 229 | keep | plan:299 (E-S17, R-S3) |
| 25 | `finish` lock order; `single_instance` takes `restore.lock` first | PR 226, 229 | keep | plan:546 (F5) |
| 26 | After a restore: no server sync, fires paused by a merge into `[engine]` that a Hub heartbeat cannot undo, until he carries on | PR 229 | keep. One live check still fails (a run seen before carry-on, words:53); the coordinator's fix-or-park call | plan:547; `BR5/qmx-host/src/qmx_host/host.py` |
| 27 | Memory is rebuilt after a restore; `reindexed` is written only on success | PR 229 | keep | plan:299 (E-S15) |
| 28 | Monthly drill on each target in turn, a random copy, a sample, in `cache/restore-drill/` | PR 226 (code), 229 (schedule) | reshape. It becomes the "check" half of the monthly re-pack and check (C3) | `BK/restore.py:427`; plan:299, :319 |
| 29 | Restore from the first-start card into a new folder: marker first, pointer only after finish | PR 228 | keep. This is his "reinstall six months later" path; its source becomes his storage (C3) | plan:244 (E-M3) |
| 30 | `serve` finishes a staged restore before any store opens | PR 228 | keep | plan:251 |
| 31 | Before a store upgrade, `serve` takes a `before-upgrade` quick copy of the whole folder; a failed copy is one line and the start goes on | PR 228 | reshape. With a storage connected, sync first, then upgrade (words:185, :203); the local quick copy stays the fallback | `HO/__main__.py:142-143`, `:218-250`; plan:548 |
| 32 | A restore from Settings stages while QMX runs and finishes at the next start | PR 229 | keep | plan:550 |
| 33 | A failed restore into a folder that is not the default is not offered again by a new card | PR 228, low 1 | keep as a low; fold into the storage restore (C3) | review/br4-check-1e9f695a.md, low 1 |

### A3. The host service and settings (B3, PR 227)

| # | Decision | Status | Verdict | Where |
|---|---|---|---|---|
| 34 | Rounds run inside the host on their own thread, not as a workflow | PR 227 | keep for the sync itself: it must run with the engine paused and before an update. Upkeep that he may hang an agent on is shown on its own list (C3) | plan:549, :591 |
| 35 | Every round, scheduled or asked for, is a `backup` job; a second one answers 409 | PR 227 | keep | `HO/backups.py:283-291`; E-S18 |
| 36 | A round he must act on opens an incident; an unplugged disk after seven intervals | PR 227 | keep. The 1-hour retry and the 7-interval warning are fixed in code (explore:28) | `HO/backups.py:77`, `:79`; E-S6 |
| 37 | One doctor row `backups` | PR 227 | keep, its words follow the new vocabulary | `HO/backups.py` (`doctor_line`) |
| 38 | `PUT /api/settings/backup` is checked by `BK/plan.parse`; the app volume keys pass to their own model (`APP_KEYS`) | PR 227 | reshape. `APP_KEYS` goes when the volume backup merges (D2) | `QX/service.py:285-302`, `:879-881`; `BK/plan.py:49-53` |
| 39 | `GET /api/backups` sends timing and on/off but not keep counts, leave-out or drill; defaults live only in code | PR 227 | reshape. The read returns every setting with its default, so the screen never shows blanks (rule "configurable is UI-editable") | `HO/backups.py:666-690`; explore:37 |
| 40 | The price store retries a rename for about 1.3 s while a backup reads the file (QMF) | PR 227 | keep. Sending only non-downloadable series cuts how often it is hit; the big-file case is still unmeasured | `QA/qmf-data/src/qmf/data/series.py:107-108`, `:166-178`; explore:91 |
| 41 | `python -m qmx_host backup` and `restore` | PR 227, 228 | keep | plan:569 |
| 42 | The Hub's dotted-key compare makes `hear` call `settings_put("engine", ...)` on every heartbeat, wiping his other `[engine]` keys | found by the PR 229 builder, being confirmed (words:5) | keep the fix. Not sync work; it rides PR 229's fix round | `BR5/qmx-host/src/qmx_host/host.py:1028-1029`; plan:486 |

### A4. Designed and not built

| # | Decision | Status | Verdict | Where |
|---|---|---|---|---|
| 43 | B6: an rclone target kind, per-file upload from a hard-link tree in `cache/backup-send/`, `lsf` arrival check, manifest last, never `rclone sync`, no room check, never rclone's own text in an answer | designed | reshape into the core of the sync (C2). Keep the arrival check, manifest last, "never `rclone sync`", the remote-name check and the silent errors. Drop the hard-link tree (packs replace it) | plan:351-403; App G:597 |
| 44 | B7: the sealed key copy with a passphrase | designed | retire for now, parked. He never asked for it (words:29); in the account model he signs in again on a new PC (words:162) | plan:405-459; design:272 |
| 45 | GitHub weekly snapshot becomes an optional "definitions only" target | designed | retire. Any storage gets the recipes; a second code path for a subset is not needed | design:276; plan:484 |
| 46 | Second drive daily at 03:00, on closing, before every migration | designed (design), partly PR | reshape. Sync on change (debounced), a daily safety round, and before an update | design:242 |
| 47 | Off-site tier: a server, a bucket or GitHub, daily after the second drive | designed | reshape. One tier, "his storage", which can be a folder on another drive, his server, Drive, R2 or any rclone remote | design:243 |
| 48 | A server that holds newer saves than a restored copy offers them first (Library AD-14 `adopt`) | designed, not in any PR | keep, open | design:266 |
| 49 | A Hindsight `pg_dump` instead of the rebuild | backlog | retire. The rebuild is built and Hindsight is an index | plan:485; inv:37 |
| 50 | Tail-only copy of an append-only log | backlog | reshape. Compression makes a whole copy of a text log cheap; revisit only if a measured log grows large | plan:485 |
| 51 | A mini app's `road/` copied under its lease | backlog, unproven | keep. It is the safety need before the volume backup can go (D2) | plan:480, :485 |
| 52 | Undo a restore; remove a set-aside folder on his click | backlog | keep | plan:485 |
| 53 | The agent guard protecting folder targets outside the QMX folder | backlog | keep, for folder storages | plan:485 |

### A5. Places, connecting and monitoring

| # | Decision | Status | Verdict | Where |
|---|---|---|---|---|
| 54 | One place list; This PC built in; a place can `run`, `keep` or both; every service names a place from it | designed (D2); the list is built (LF6), `can` is not | keep, and build `can` now: a storage is a place that keeps | design:293, :297; machines:36 (#7) |
| 55 | "The second drive is not a place: it is a backup target on This PC" | designed | reversed tonight. He wants storage connected from one screen (words:219); a folder on another drive becomes a storage of kind `folder` in the same list | design:289 |
| 56 | `[remote]` / `RemoteSettings`, a second machine list nothing reads | built, unused | retire (D3) | `QA/qmx-remote/src/qmx_remote/models.py:124-142`; machines:89 (a9) |
| 57 | Setup does not add the server to the place list | PR (WU9), gap | reshape. Writing the place row is the last step of the connect dialog | `QX/node.py:616-652`; machines:25 (#1), :86 (a6) |
| 58 | A bucket as a keep place; rclone remotes made by hand | designed (LF12), not built | reshape into "connect storage" (C3) | machines:28 (#4); design:452 |
| 59 | Setup as resumable steps with status, startable from a card (LF13) | designed, not built | reshape. Generalised to every connection kind on the host's job runner (C3) | design:453; machines:29 (#5) |
| 60 | The add-a-server walk: his steps as cards, QMX's steps as resumable checked operations, his later choices on their own screens; built on the wizard pattern; the copilot walks him | designed (F1), ruling 145 | keep, generalised to compute, storage, GPU and deep logs (words:219) | design:407-412; rulings:277 |
| 61 | The `available → configured → authorized → reachable → healthy` ladder | built, no caller | keep. It becomes the compute dialog's check | `QA/qmx-engine/src/qmx_engine/triggers/preflight.py:231` |
| 62 | PC-started work actually running on a named place, and a PC-made trigger reaching a server's ledger | gap, "needs a ruling" | keep open. It is technical, not his call; it gates "connect compute and use it" | machines:48 (#14), :88 (a8) |
| 63 | `[telemetry] send_to`: off (default), this-pc, or a place | PR (LF5) | keep; add a check on `PUT` (any value is saved today) | `QA/qma-harness/src/qma/telemetry.py:1-46`; `QX/service.py:73`, `:796-900` |
| 64 | OpenObserve on This PC at his click: download into `cache/openobserve/`, run under the host, root password in Credential Manager, no collector on the PC | designed (LF10), not built | reshape. It is the "deep logs: here" choice of the connect dialog | design:347, :445 |
| 65 | On a server: OpenObserve and the collector as unit files with hand install steps; setup has no monitoring step | built, partial | reshape. The server dialog's monitoring step installs them | `QA/qmx-host/deploy/openobserve.service:11-17`; `QX/node.py:634-651`; inv:164-165 |
| 66 | Ruling 123: OpenObserve's free tier is fine as external monitoring | ruling | reshaped tonight: self-hosted only, the cloud's ingest price is too high for logs (words:219) | rulings:231 |
| 67 | Ruling 126: two DevOps layers (in-app health, OpenObserve) from one source of events | ruling | keep. OpenObserve needs no backup: it views records the Library keeps | rulings:234; explore:97 |
| 68 | The trading node's own Prometheus, Loki and Grafana stack | built (QMN) | leave to the trading-node session (standing rule: node internals are not re-discussed here); flag the overlap with OpenObserve | explore:96 |
| 69 | "Deep logs" control and a "Data and backups" tab | designed as missing; not in `UI-HANDOFF.md` | keep; the UI notes need a sync, storage and deep-logs section (words:106) | design:328-330 |
| 70 | The first-start card refuses a QMX folder under OneDrive, Dropbox or Google Drive's live sync | designed (L5) | keep. "Sync to Google Drive" means QMX sends packs through rclone; the folder itself never sits in Drive's sync folder | design:512 |
| 71 | The attach plan's guard misses `data/vault/`, so `@file` can put a pairing key into the Library, which copies and replicates it | plan review MUST 6 | keep. Fixed by one secret list (C4) | review/plan-attach-edge-cases.md:21; `QA/qma-harness/src/qma/harness/tools.py:909-923` |
| 72 | No PR of the attach program edits the backup package | plan | keep. The attach plan stays parked and separate; its uploads are "his content" | attach:44, :397 |

### A6. Rulings that bind the sync

| Ruling | What it says for this round | Verdict | Where |
|---|---|---|---|
| 106 | No QMX caps; a provider's own limit is the only limit | keep. No size cap on the storage; the floor protects his own drives only | rulings:206 |
| 116 | Keys never printed; keys in the OS keyring | keep. rclone's output is never echoed (it can hold tokens) | rulings:216; `QA/qmx-apps/src/qmx_apps/backup.py:56` |
| 121 | The server holds the main copy | already reversed by 136 | rulings:229, :265 |
| 135 | Tokens and live-trading keys never leave their home | keep. They are never in a copy, sealed or not | rulings:250 |
| 136, 140 | The PC is home; a server or storage holds copies, never the main copy | keep | rulings:265, :272 |
| 137 | No default-closed locks | keep. Every upkeep job and the sync itself can be switched off | rulings:266 |
| 141 | His data is independent of the app; a reinstall picks up where he left off | keep, extended tonight to a new PC through his storage (words:151) | rulings:273 |
| 143 | Every file has a documented home | keep. New files (the pack index, the storage's remote in `data/rclone.conf`) get rows in design A3 | rulings:275 |
| 144, 145 | External compute and storage are added from the screen; the copilot walks him | keep; they define the connect dialog | rulings:276-277 |

### A7. Chat only, tonight

| # | What was said | Verdict | Where |
|---|---|---|---|
| 73 | Save the recipe, not the cake | keep; it is section B's first word | words:185, :188-195 |
| 74 | Compress; re-pack from scratch on a schedule and check | keep (D3) | words:185, :197 |
| 75 | rclone as the one way to reach any storage | keep | words:185, :201 |
| 76 | Spread data over several free Google accounts | open, question E2 | words:185, :201; inv:105-111 |
| 77 | Sync before every update, as Hermes does | keep; no updater exists on the PC yet, so it hangs on the store-upgrade hook now | words:185, :203; inv:115-125 |
| 78 | A real "QMX account" sign-in service run by him is a bigger, separate job | settled by his answer: each person connects their own storage through rclone (words:185, "even someone else can just sync to their Google Drive") | words:166 |
| 79 | Keys are not in the copy; he signs in again on a new PC | settled (his silence on the table, and the track record's "you never asked for it") | words:29, :162 |
| 80 | Merge the mini-app backups into the new program | keep (D2); he liked it | words:142, :151 |
| 81 | PRs 6 and 7 as planned are dropped; the sync is planned small | keep | words:168, :185 |
| 82 | Upkeep workflows are not his workflows | keep (B, C3) | words:219 |
| 83 | An agent may be attached to upkeep | keep, optional, none by default | words:185 |

---

## B. The domain words

One line each, with what each maps to in the code. These replace plan Appendix F's words where they differ.

| Word | Means | In the code |
|---|---|---|
| **Recipe** | A small definition QMX rebuilds a thing from: a workflow, a mini app's manifest, a unit, a skill or methodology, his settings | Library objects of kinds `workflow`, `mini-app`, `unit`, `skill`, `methodology`, `template`, `agent`, `persona`, `strategy`, `component`, `logic` (`QA/qmx-library/src/qmx_library/kinds/`); a workflow's `definition.json` plus scripts (`QA/qmx-engine/src/qmx_engine/ports/library.py:89-140`); `app.toml` (`QA/qmx-apps/src/qmx_apps/manifest.py:287`); `data/settings.toml`, `profiles/`, `slots/`, `observers.json` |
| **His content** | What he made or said that cannot be made again | `claude/projects/*.jsonl`, `chats/<id>.json`, `agent-memory/`, `exports/`, `workspaces/`, Library notes, sources, uploads and `session` items, `apps/<id>/data`, `node/` (inv:35) |
| **Run result** | What a run produced; kept because an AI answer does not come out the same twice | `engine/engine.sqlite`, `engine/inbox.sqlite`, `engine/runs/`, `runs.db`, `control.db`, `portfolio.db`; Library kinds `workflow-run`, `test-report`, `artifact`, `backtest-result` (inv:36) |
| **Rebuildable** | What QMX makes again or fetches again, so it is never sent | `library/catalog.db`, `memory/fts.db`, Hindsight's database, fetched and transient blobs, downloadable price series, all of `cache/` and `logs/`, OpenObserve's data (`BK/snapshot.py:37-62`; `HO/disk.py:41-46`) |
| **Secret** | A key, token or login; never leaves this PC in clear; he signs in again elsewhere | `BK/snapshot.py:71-78` plus `keys/`; the harness guard's `secret_files` (`QA/qma-harness/src/qma/harness/tools.py:909-923`) |
| **Saved set** | Recipes, his content and run results: what a sync sends | none yet; today "everything in `data/` minus `LEFT_OUT` and `SECRET`" |
| **Place** | Anywhere outside This PC that QMX can run work on or keep things in. This PC is not a place; it is home | `[engine.placement.<name>]` (`QA/qmx-engine/src/qmx_engine/settings.py:56-67`) |
| **Compute** | A place that can run: his server, a GPU, Modal, E2B | a place row; `can` is designed, not built (machines:36) |
| **Storage** | A place that can keep: a folder on another drive, his server over SFTP, Google Drive, R2, any rclone remote | today `[[backup.targets]]` of kind `folder` only (`BK/plan.py:44-48`) |
| **Sync** | QMX sending his saved set to his storage, on change, daily and before an update, as dated copies he can go back to. It is a backup, not a mirror: deleting a file on the PC never deletes a kept copy | `BK/round.py` `run_round` with a storage target |
| **Copy** | One dated moment of the saved set in one storage | `snapshots/<stamp>/manifest.jsonl` (`BK/repository.py`) |
| **Pack** | Many small pool files compressed into one file with an index | not built (inv:79) |
| **Quick undo** | Copies on This PC's own drive in `backups/quick/`, for a fast undo with no network; optional | `BK/round.py:39`; `HO/backups.py:273` |
| **Restore** | Rebuilding `data/` from one copy he confirmed, with the earlier data set aside whole | `BK/restore.py` (`stage`, `finish`) |
| **Upkeep** (maintenance workflow) | A job QMX runs for its own health: re-pack and check the copies, the connection probe, pruning. Listed apart from his work; he can switch any off and add an agent step | the `backup-weekly`, `connections-health` and guard templates sit on his shelf today (`QA/qmx-engine/src/qmx_engine/templates/catalog.py:190`, `:396-433`); a marker can go in a workflow's `meta`, outside its hash (`QA/qmx-engine/src/qmx_engine/definition/model.py:207-212`) |
| **His workflow** | A strategy, research, feed or anything he builds; a recipe in his Library | Library kind `workflow` |
| **Connect** | The step-by-step dialog that adds a compute, a storage or deep logs: his steps as cards, QMX's steps as checked jobs | none yet; `QX/node.py:616-652` for a server, as one blocking command |

Two collisions to settle in words:

- **"Sync" already means the Library's link with a server** (`Replicator`, `HO/host.py:813-815`), and the explore says "sync is not a backup" (explore:81). Recommendation in E3.
- **"Backup" confused him** (words:70: "backups would literally just mean external compute"). The screen should lead with "sync" and "restore" and keep "backup" out of his words.

Scenarios that test the words:

- He deletes a strategy on the PC by mistake on Tuesday and notices Friday. The sync sent Monday's copy, which still holds it; restore brings it back. A mirror would have lost it. So a sync keeps dated copies.
- A friend's laptop and his laptop point at the same Drive folder. Each QMX folder has its own `home_id`, so each writes under its own folder; if a second PC restored his copy and then syncs, the fork guard (A1 row 14) stops it until he carries on.
- The imported old ticks (about 10 GB, `rulings:238`) cannot be downloaded again, so they are his content and go once, by hash; a Dukascopy month can be downloaded again, so it is rebuildable and never goes.

---

## C. Deep modules and seams

### C1. "What to save" is decided once

Today six places decide what matters, each its own way:

| Where | What it decides |
|---|---|
| `BK/snapshot.py:37-87` | `LEFT_OUT`, `SECRET`, `WRITE_ONCE` |
| `BK/plan.py` `leave_out` | his own globs |
| `HO/disk.py:41-46` (`EXPENDABLE`) | what the host deletes for room: the same four folders `LEFT_OUT` names |
| `QA/qmx-apps/src/qmx_apps/backup.py:98-108` | the volume backup's own skip list |
| `QX/backup.py:25-33` | the weekly snapshot's own small-store list |
| `QA/qma-harness/src/qma/harness/tools.py:909-923` | the guard's secret files, which lack `data/vault/` (A5 row 71) |

The deep module: one table in `qmx_home` (the leaf, standard library only), `classes.py`, with one function `class_of(path, kind=None) -> Class`, where a class is `recipe`, `content`, `result`, `rebuildable`, `secret` or `scratch`. A Library object is classed by its kind, read from the live `catalog.db` at copy time; an unknown kind reads `content`, the safe side. A price series is classed `content` when it cannot be downloaded again (imported, or a live feed's open month) and `rebuildable` otherwise.

Callers: the snapshot sends the classes his `[sync] save` list names (all three by default) and never `rebuildable`, `secret` or `scratch`; the host's giving-way list is the evictable part of `rebuildable`; the harness guard and the attach guard read `secret`, adding their own extras (`settings.toml`, his `~/.claude`) on top. Deletion test: removing the table puts six lists back across five packages.

### C2. A storage is reached once

- **The seam is the `Repository` protocol** (`BK/repository.py:192-249`: `pool_has`, `put_pool`, `put_copy`, `copies`, `manifest`, `read_extra`, `fetch`, `drop`, `sweep`, `room`). It has one adapter today (`FolderRepository`); the rclone adapter makes it a real seam with two. The round, restore and drill do not change.
- **Packs and compression live inside the adapters**, behind `put_pool`, `fetch` and `sweep`. The pool name stays the sha256 of the original bytes, so the write check and the restore check are unchanged (inv:78). The re-pack is the adapter's `sweep`. Callers never learn the word "pack".
- **One rclone runner on the PC**, `qmx_home.rclone.run(args, *, config)`: finds the binary, passes `--config`, never returns rclone's text (it can hold tokens), maps failure to one plain line, records the arguments. Today the PC side has two runners that each handle errors differently: the app volume one hides the text (`QA/qmx-apps/src/qmx_apps/backup.py:42-61`); the node rebuild raises with rclone's own stderr (`QX/node.py:470-475`). The Hub's runner (`QA/qmx-hub/src/qmx_hub/bucket.py:72-78`) runs on the server, and `qmx-hub` does not depend on `qmx-home`; it stays its own until a reason appears.
- **The storage's credentials** live in `data/rclone.conf`, which is already secret (`BK/snapshot.py:73`). On a new PC he connects the storage again (signs in), which is also the first step of restoring from it.

### C3. Where a connect dialog's steps run

- **The runner is the host's job runner** (`HO/jobs.py:1-133`): `running`, then `finished` with a result or `stopped` with one line, with `step`, `done` of `total` and counts. No new state is needed.
- **A connection kind is an ordered list of steps.** Each step is `(name, who, check, do)`, `who` being `his` or `qmx`. One job runs QMX's steps in order and skips any step whose `check` already passes, so resuming is running again (idempotent; no saved state machine). It finishes with `{"needs": <his step>}` when it reaches a step only he can do; the screen shows that card, and when he is done it starts the job again.
- **One backend, two front ends.** The screen's cards and the copilot's walk (ruling 145) call the same steps through the same routes, so the wizard and the copilot never diverge.
- **The kinds**, each ending by writing its place row with `can`:
  - **Storage:** choose the kind; his step: sign in through the browser page rclone opens (Drive), or type a bucket key into Credential Manager (R2); QMX's steps: create the remote in `data/rclone.conf`, test it (list and free space), write the place row with `can = ["keep"]`, run the first sync.
  - **Server:** `qmx node setup`'s steps (`QX/node.py:616-652`), each given a check, then the place row (machines a6), the status ladder (`preflight.py:231`), a one-node smoke test, `qmx-recover status` (design:410).
  - **Deep logs:** on This PC, download OpenObserve into `cache/openobserve/`, start it under the host, keep its password in Credential Manager, set `[telemetry] send_to`; on a server, the unit files' install steps (inv:164).
- **Restore on a new PC** is the storage kind's dialog run from the first-start card, then the built card restore (A2 row 29) with the storage as its source.
- **Sync and upkeep run in the host**, beside the replicator (`HO/host.py`), because they must run with fires paused and before an update. The monthly re-pack and check is an upkeep job; upkeep jobs show on their own list, apart from his workflows, and he can switch each off. An agent step is added by a maintenance workflow that calls the host's route and reads its result, not by moving the work into the engine (keeps plan:591's reasons).
- **Sync before an update** is one call, `sync_now(why="before-update")`, which the store-upgrade hook in `serve` (`HO/__main__.py:142-143`) calls today and the desktop updater calls when it exists. With no storage connected or no network, the local quick copy is the fallback, with one line.

### C4. Helpers and floors that merge

| Today | Merged into |
|---|---|
| Three free-space floors: 1 GiB (`QA/qmx-home/src/qmx_home/versions.py:39`), a twentieth of free space at start or `disk.floor_gb` (`HO/disk.py:55-62`), a tenth of the drive for the proposal (`BK/plan.py:56`), combined at `BK/round.py:229` | One floor, `max(1 GiB, disk.floor_gb or a twentieth of free space)`, applied to every local write, a folder storage on C: included; shown and editable in Settings |
| Two secret lists (`BK/snapshot.py:71-78`, `tools.py:909-923`) | One list in `qmx_home`; the guard adds its extras |
| Two PC rclone runners | One (C2) |
| Three schedulers: the host's backup sweep (`HO/backups.py:252`), the app volume timer (`QA/qmx-apps/src/qmx_apps/backup_schedule.py:10`), the weekly template's cron (`catalog.py:396-404`) | The host's sweep |
| Two machine lists (`[remote]`, `[engine.placement]`) and a third "where" list (`[[backup.targets]]`) | One place list with `can`. A storage's location moves into its place row; its sync policy (`every`, `at`, `keep`, `on`) stays in `[sync]` by place id. No real folder holds `[[backup.targets]]` rows yet (225 to 229 are not landed and his first real start has not happened), so the move costs no migration of his data |
| `[backup]` shared by two meanings (`APP_KEYS`, `BK/plan.py:49-53`; `_volume_keys`, `QX/service.py:300-302`) | One meaning |
| LF3's per-store pre-change copies (`versions.py:235-302`) and PR 228's whole-folder `before-upgrade` copy, both on every upgrade | Release each `pre-*` copy once a `before-upgrade` copy of the same moment exists; keep `pre-*` only when that copy failed |

---

## D. The subtract list

Do these before adding the sync. Lines are at `QA/` `1e9f695a`.

| # | Delete or merge | Lines | What keeps it safe |
|---|---|---|---|
| 1 | **The weekly GitHub snapshot.** `QX/backup.py` (198), `QX/__main__.py` (28, its only command), the route and import (`QX/service.py:46`, `:1344-1364`, about 22), the template `backup-weekly/` (`definition.json` 31, `scripts/backup.py` 46, `README.md` 22), its catalog row (`catalog.py:396-404`, 9), its test `QA/qmx-control/tests/test_weekly_backup.py` (141) | 356 code, 141 tests | Nothing else imports `weekly_backup` (searched). It installs disabled and its "enable after first boot" step was withdrawn (design:462), so nothing runs it. Keep `repository` in the ignored `[backup]` keys for one release, so an old settings file still saves. Move or drop `weekly-backup.json` and `.lock` from `data/` (ruling 143, plan:484) |
| 2 | **The mini-app volume backup.** `QA/qmx-apps/src/qmx_apps/backup.py` (196), `backup_schedule.py` (51), the wiring in `QX/service.py` (imports `:26-27`, `:630`, `:1628-1639`, `:1703-1705`, routes and their two agent operations `:1655-1684`, `_volume_keys` `:300-302`, about 50), `APP_KEYS` (`BK/plan.py:49-53`, 5), its tests in `QA/qmx-apps/tests/test_storage.py` (4 of 10 tests) | about 300 code, about 90 tests | App volumes are already in every copy minus heartbeats and scratch (`BK/snapshot.py:52-53`). First prove or fix a `road/` copied without the app's lease (plan:480, :485): copy it under the lease the volume backup takes (`backup.py:135-142`). Litestream for container apps is a different job and stays. A "restore one app" goes to the backlog |
| 3 | **`[remote]` and `RemoteSettings`.** `QA/qmx-remote/src/qmx_remote/models.py:124-142` (19), `QX/service.py:44`, `:65`, `:840-846` (about 9), the fixture in `QA/qmx-remote/tests/test_remote.py:14`, `:33-34` | about 28 code | No reader (searched: only the write check imports it). `Target` in the same file stays: place rows use it. The settings writer keeps unknown sections word for word, so an old `[remote]` in a file is harmless |
| 4 | **The node rebuild's own rclone runner** (`QX/node.py:470-475`), onto C2's runner | 6 | Its callers read only the exit; the new runner's line replaces rclone's stderr in the error |
| 5 | **Three floors into one** (C4) | about 10 | The 1 GiB minimum still guards a pre-change copy |
| 6 | **The fixed hourly quick undo** (`HO/backups.py:273`, `BK/plan.py:140`) into a setting with an off switch | about 5 changed | With it off and no storage connected, the doctor row says his work has no copy anywhere, in plain words |
| 7 | **Plan text for B6 and B7** (plan:351-459), superseded by the sync plan; B7 to the backlog | 109 plan lines, 0 code | Nothing built depends on them; `BK/round.py`'s `sealed_keys` hook stays as an unused parameter or goes with it |
| 8 | **The `cache/backup-send/` hard-link tree** (designed for B6) | never built | Packs replace it |
| 9 | **The old bundle installer** `D:/QMX-worktrees/bld-br4/release/install.py` (480) and `release/launcher.py` (26), which launch `qmb` | 506, optional | Nothing outside `release/` names them (searched). Delete now or with the desktop installer; either way the sync-before-update hook does not use them |

Size: about 700 lines of code and templates and about 230 lines of tests go in items 1 to 6, plus 506 more if the old installer goes too. The sync's additions then land on a smaller base: one class table, one rclone adapter with packs, one runner, `can` on place rows, and the connect steps on the job runner.

Not on the list, on purpose: the second-drive proposal (`BK/plan.py:296`, `HO/backups.py:531-566`) stays as the storage dialog's suggestion; the trading node's backup and QMF's backup block (`qmn/src/qmn/data/backup*.py`, `QA/qmf-data/src/qmf/data/backup.py`) cover another machine; the status ladder (`preflight.py:231`) gets its first caller instead of going.

---

## E. Questions only he can settle

Filtered out, because the code, a ruling or tonight's words settle them: a QMX-run account service (words:185 settles it: each person connects their own storage); keys in the copy (words:29, :162: parked); whether the quick undo can be switched off (the configurable rule: yes); whether upkeep can be switched off (ruling 137: yes); what counts as rebuildable (technical); OpenObserve against Grafana and Prometheus (he settled it, words:219); self-hosted against cloud OpenObserve (words:219); the PR count (the planning workflow decides, words:219); the trading node's own monitoring (the node session's).

**E1. Which storage do you connect first? (money)**
Google Drive on your main account's free space, Google One (new monthly cost), Cloudflare R2 (free up to 10 GB), or your server (already paid, 100 GB, needs the server set up first).
Recommendation: Google Drive on your main account's free space. The saved set is estimated at tens to a couple hundred MB compressed (inv:41-48), it is the path your friends would use, and it costs nothing. Buy a bigger plan only when the measured set outgrows it. Your server is the second storage, once it is set up.

**E2. Spread copies over several free Google accounts? (risk to your accounts)**
rclone can merge several accounts into one (`union`), but losing any one account loses the files on it, and Google treats several free accounts used to get around storage limits as abuse, which can get the accounts suspended (inv:105-111).
Recommendation: no. One account per storage. If you want more safety, connect a second storage that holds a full second copy (your server), not a share of one.

**E3. What do we call it on the screen? (vocabulary)**
"Sync" is your word, but QMX already uses "sync" for the Library's link with a server.
Recommendation: on the screen, "Sync to my storage" for your feature, "Restore" for coming back, "Storage" for what you connect, beside "Machines" for compute. The server link is shown as "Server link" in your words. "Backup" leaves the screen.

**E4. Lock the copies on someone else's storage with your passphrase? (irreversible)**
Your chats, strategies and run results would sit on Google's or Cloudflare's disks. rclone can encrypt them (`crypt`), so only your passphrase opens them; but a forgotten passphrase loses every copy, and there is no way to recover it.
Recommendation: locked by default on a cloud storage (Drive, R2), unlocked on your own server and on a drive you plug in. The passphrase is asked once when you connect the storage and kept in Windows' password safe on this PC; on a new PC you type it once to restore. Keys and tokens stay out of the copy either way (ruling 135).
