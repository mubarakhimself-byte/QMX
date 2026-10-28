# What is on the ground for "sync to my account" and "connect from the screen"

Read on 2026-10-28. Nothing was run except `rclone version` and `rclone help backends`. No real QMX folder, rclone config, key store, server or service was opened or started.

Where the references point:

- `QA/` is `D:/QMX-worktrees/bld-br4/qmx-agents/packages/` (branch `build/br4` at `1e9f695a`, backup PRs 225 to 228).
- `design:` is `D:/QMX-worktrees/agent-system/tracker/qma-v2/research/methodology/62-local-first-design.md`.
- `plan:` is `D:/QMX-worktrees/agent-system/tracker/qma-v2/BACKUP-RESTORE-PLAN.md`.
- `explore:` is `D:/QMX-worktrees/qma-ship/wrapup/history/BACKUP-EXPLORE.md`; `machines:` is `D:/QMX-worktrees/qma-ship/wrapup/evidence/machines-design-vs-backend-2026-10-27.md`. Facts from those two are reused, not read again.

Tags: **EXISTS** works today, **PARTIAL** some of it works, **MISSING** not there.

---

## 1. Recipes, his content, run results, and what can be rebuilt

### Where each kind of thing lives

The QMX folder has five parts: `data`, `keys`, `backups`, `cache`, `logs` (`QA/qmx-home/src/qmx_home/__init__.py:52`). The design's tree lists every file (design:52-115).

| Thing | Tag | Where and in what format | Typical size |
|---|---|---|---|
| Workflow definitions | EXISTS | A workflow is a folder: `definition.json` plus the scripts it names (`QA/qmx-engine/src/qmx_engine/ports/library.py:89-140`). It is saved as a Library object of kind `workflow`. Drafts sit on `refs/drafts/<item>`, published versions on `main` (`ports/library.py:1-10`, `:67`). So a workflow is JSON plus a few script files inside `data/library/`. | The 51 shipped templates: definitions 1.1 to 11.6 KB each, 205 KB in all; with scripts, 2.2 MB for the whole pack (measured with `wc -c` and `du` on `QA/qmx-engine/src/qmx_engine/templates/`). |
| Mini-app definitions | EXISTS | An app is a folder with `app.toml` (`QA/qmx-apps/src/qmx_apps/manifest.py:287`). Installing copies it as an immutable image to `data/definitions/<hash>/`, recorded in `apps.db` (`QA/qmx-apps/src/qmx_apps/supervisor.py:103-111`, `:338`). The image is not in the backup's leave-out list, so backups copy it (`QA/qmx-home/src/qmx_home/backup/snapshot.py:37-64`). | `app.toml` is 0.4 to 1.3 KB. A whole example app is 83 to 239 KB (`D:/QMX-worktrees/bld-br4/examples/apps/*`). |
| Unit definitions | PARTIAL | A Library kind `unit` exists with no fields yet (`QA/qmx-library/src/qmx_library/kinds/unit.schema.json`). The unit design is still being decided (`D:/QMX-worktrees/agent-system/tracker/risk-sizing/STATE.md`). When built, a unit is a Library JSON object like a workflow. | None yet. Expected small (JSON). |
| Settings, provider rows, place list | EXISTS | One file, `data/settings.toml` (TOML). It holds the place list, `[telemetry]`, `[backup]`, providers and connections (design:57). The screen reads and writes it per section through `GET/PUT /api/settings/{section}` (`QA/qmx-control/src/qmx_control/service.py:750`, `:796`). Model rows are `data/profiles/` (TOML), prompt texts are `data/slots/` (Markdown) (design:59-60). | Kilobytes. |
| Other Library recipes | EXISTS | Kinds `skill`, `methodology`, `template`, `agent`, `persona`, `mini-app`, `strategy`, `component`, `logic` (`QA/qmx-library/src/qmx_library/kinds/`, 40 schemas). Each object is one canonical JSON file in `library/objects/`; bytes are in `library/blobs/` named by hash (`QA/qmx-library/src/qmx_library/store.py:4-15`). | Small JSON each. |

### What each `data/` folder is

| Class | Folders | Save it? |
|---|---|---|
| **Recipes** | `settings.toml`, `profiles/`, `slots/`, `observers.json`, `definitions/` (app images), Library objects of kinds workflow, skill, methodology, mini-app, unit, strategy and similar | Yes. Small. |
| **His own content** | `claude/projects/*.jsonl` (chat transcripts), `chats/<id>.json`, `agent-memory/`, `exports/`, `workspaces/`, Library notes, sources and uploads he made, `session` items (the host also records every chat into the Library, `QA/qmx-host/src/qmx_host/host.py:12-14`), `apps/<id>/data` (each mini app's own data), `node/` when a trading node runs on the PC | Yes. Chats are likely the bulk. Note that chats live twice: as transcripts and as Library `session` items. |
| **Run results** | `engine/engine.sqlite` (ledger: events, memos, spans), `engine/inbox.sqlite`, `engine/runs/<run>/` (frozen workflow copy and traces), `runs.db`, `control.db`, `portfolio.db`, Library kinds `workflow-run`, `test-report`, `artifact`, `backtest-result` (design:69-77) | His choice. AI answers do not come out the same twice, so some are worth keeping. They are mixed with recipes in one Library, so a "save only recipes" choice must pick by Library kind, which the catalog knows per object. No such selection exists today. |
| **Rebuilt or fetched again** | `library/catalog.db`, `memory/fts.db`, `memory/hindsight/pg/**` (Hindsight's database), `library/blobs/fetched/**`, `cache/prices/**`, telemetry queue: all already left out of copies (`QA/qmx-home/src/qmx_home/backup/snapshot.py:37-45`). All of `cache/` (environments, app builds, models, pg0, work zones, the PC's OpenObserve) and `logs/` are outside `data/` and never copied (design:97-115). | No. |
| **Prices** | `market/` Parquet by month. Downloaded series can be fetched again. Some cannot: the imported old ticks and a live feed's open month. The server's bucket push already knows this split (`keep_series`, `QA/qmx-hub/src/qmx_hub/bucket.py:19-23`). Today's backup copies all of `market/` (finished months once, by hash) (`snapshot.py:81-88`). | Only the series that cannot be downloaded again. |
| **Secrets** | `keys/`, `data/vault/`, `data/rclone.conf`, the Claude login files. Never in a copy in clear (`snapshot.py:71-78`). | No (he signs in again), unless the sealed key copy is built. |

### Estimate of the "must save" set

Not measured: his real folder was not read. From the code and the formats:

- Recipes alone: under 10 MB, even with a hundred workflows and a dozen apps.
- Recipes plus his own content: about 100 MB to 1 GB. Chat transcripts and uploaded files are most of it.
- Text compresses about 5 to 10 times, so the sent set is likely tens of MB to a couple hundred MB.
- What is left out (prices that can be fetched, indexes, Hindsight, caches, OpenObserve) is the multi-GB part.

---

## 2. Internal (maintenance) workflows

**PARTIAL.**

- **Maintenance workflows exist, mixed with his strategy workflows.** The template pack ships three: weekly GitHub snapshot `backup-weekly` (`QA/qmx-engine/src/qmx_engine/templates/catalog.py:396-404`, cron Mondays 06:00), `connections-health` every 5 minutes (`catalog.py:425-433`), and the trading guard watchdogs (`catalog.py:190`). They install disabled like every template (`templates/install.py:1-8`). Nothing marks them as QMX's own: same shelf, same enable switch.
- **The pattern for one works.** `backup-weekly` is one script node that imports QMX code, does the job and files a `maintenance:backup` incident when it fails (`templates/backup-weekly/scripts/backup.py:14-46`). A monthly re-pack and check could run the same way, on a cron trigger.
- **An agent can be attached.** The engine has an `agent` node type and an `llm` node (`QA/qmx-engine/src/qmx_engine/nodes/agent.py`, `nodes/llm.py`). A maintenance workflow can add an agent step after the script, for example to read the check's result and write a note.
- **A marker costs no schema change.** A workflow's `meta` keeps any extra key and sits outside the content hash (`QA/qmx-engine/src/qmx_engine/definition/model.py:207-212`). A key like `meta.kind = "maintenance"` would let the screen show these apart and let QMX install them enabled.
- **Host jobs that are not workflows.** The host runs fixed loops in code: heartbeats with an hourly log prune, the daily idle-chat export, Library sync to a server, and the backup sweep (`QA/qmx-host/src/qmx_host/host.py:808-819`; the backup sweep is `QA/qmx-host/src/qmx_host/backups.py:252`). The mini-app volume backup has its own timer (`QA/qmx-apps/src/qmx_apps/backup_schedule.py:10`). These are not visible as workflows and have no agent hook.
- **Missing:** a "QMX's own" flag, a separate list in the screen, and a rule for who may turn one off.

---

## 3. Compression

**MISSING.** Backup PRs 225 to 228 compress nothing. No `zlib`, `gzip`, `lzma`, `zstd`, `zipfile` or `tarfile` appears in `QA/qmx-home/src/qmx_home/backup/` (searched).

How the store works today:

- A place holds a pool with each file once, named by the sha256 of its bytes, plus one manifest per copy (`QA/qmx-home/src/qmx_home/backup/repository.py:1-25`).
- Writing checks the fingerprint: the copy is hashed as it is written, and a mismatch places nothing (`repository.py:300-317`).
- Restore checks it again: each fetched file is hashed and compared with the manifest line (`QA/qmx-home/src/qmx_home/backup/restore.py:1062-1065`).
- Every place goes through one `Repository` interface (`repository.py:192-249`), so a new kind of place does not touch the round or restore logic.

What would change to store compressed packs:

1. **Per-file compression (small change).** Keep the pool name as the sha256 of the original bytes. Compress while copying and hash the original stream on the way in, so the write check is unchanged. On fetch, decompress and hash the output, so the restore check is unchanged. The fingerprint stays end to end on the real bytes. Python 3.14's own `compression.zstd` keeps the backup code standard-library only (the backup package's rule, `backup/__init__.py:1-2`; QMX pins Python 3.14, `D:/QMX-worktrees/bld-br4/qmx-agents/pyproject.toml:7`). Skip files that are already compressed (Parquet, PDF, images): they gain little.
2. **Packs (bigger change).** Many small files go into one pack file with an index: sha256, pack, offset, length. This matters for Google Drive, which is slow with many small files. The pool sweep becomes a re-pack: write new packs without the files no copy names, check them, then drop the old packs. That is the monthly "re-zip from scratch and check" he asked for.
3. **What stays as is.** The manifest, the keep rule, the "unchanged file is not read again" skip (`QA/qmx-home/src/qmx_home/backup/snapshot.py:9-12`), and the quick undo's "still live" entries, which copy nothing.
4. **One gap to fix with it.** The room check counts raw bytes (`snapshot.py:188-195`). With compression it overestimates, which is the safe side.

A corrupted pack is caught: the hash of each decompressed file fails, and zstd frames carry their own checksum. The damage is limited to the files in that pack, so packs should be kept moderate in size.

---

## 4. rclone

**PARTIAL.** Used in five places, none of them the PC's own backup:

| Use | Where |
|---|---|
| Mini-app volume backup, nightly by default, `rclone copy --checksum` to a remote named in `[backup]` | `QA/qmx-apps/src/qmx_apps/backup.py:26-61`, `:122-196` |
| The server's Library push to a bucket | `QA/qmx-hub/src/qmx_hub/bucket.py:1-25` |
| Rebuilding a server from a bucket, `qmx node rebuild --remote` | `QA/qmx-control/src/qmx_control/node.py:405-475`, `:929` |
| The server bootstrap installs rclone 1.75.1 and ships app logs and traces to a local bucket | `QA/qmx-control/src/qmx_control/node-bootstrap.sh:37-41`, `:55-61`, `:116-117` |
| The trading node's encrypted nightly backup to Backblaze, still switched off | `D:/QMX-worktrees/bld-br4/qmn/src/qmn/data/backup_run.py`; explore:82 |

The off-site backup through rclone is planned, not built (plan:351-361).

**On this PC:** `D:/Tools/rclone/rclone.exe` is **v1.75.2**, Windows amd64, go1.26.9. It is not on the default `PATH` (the plan adds it for lanes, plan:52). A config file `rclone-qmx.conf` sits beside it; it was not opened.

**`rclone help backends`** lists Google Drive (`drive`), S3-compatible (Cloudflare, Hetzner, Wasabi and others), SFTP (his server), Backblaze B2, OneDrive, Dropbox, and three helpers that matter here:

- **`union`**: merges several remotes into one. Its write rule can send each new file to the remote with the most free space, so a hash pool spreads over several Google accounts. Losing one account loses the files on it, unless the rule writes to all of them (then it copies, it does not spread).
- **`combine`**: maps top-level folders to different remotes, for example `pool` on one account and `snapshots` on another.
- **`crypt`** (encrypt), **`compress`** (experimental), **`chunker`** (split big files), **`hasher`** (checksums for remotes that lack them).

So spreading over several accounts is viable through `union`, untested.

**Terms risk:** Google's terms treat using several free accounts to get around storage limits as abuse, which can get the accounts suspended; one paid account (his 5 TB plan) has no such risk.

---

## 5. Before an update

**PARTIAL.**

- **No updater on the PC.** The program is a git checkout and its `.venv` (design:378-380). No version check or update command exists for the PC. `D:/QMX-worktrees/bld-br4/release/install.py` (480 lines) and `release/launcher.py` (26 lines) are an older bundle installer that launches `qmb`; nothing in `qmx_host` uses them.
- **On a server:** `qmx node update` drains the host, then installs a pinned revision and lays out the folder (`QA/qmx-control/src/qmx_control/node.py:824-865`). It takes no backup first.
- **What runs before a store upgrade today (PC and server):**
  - When a store will upgrade, `serve` first takes a quick copy of the whole folder tagged `before-upgrade`, into `backups/quick` on the same drive (`QA/qmx-host/src/qmx_host/__main__.py:142-143`, `:218-250`). If it cannot be made, one line is printed and the start goes on.
  - Each store also copies itself before its own upgrade step, into `backups/pre-*` (`QA/qmx-home/src/qmx_home/versions.py:235-302`).
  - Both copies are local only. Nothing sends anything off the PC before an update.
- **Missing:** "sync to my account first, then update" needs an update command to hang it on, and a sync step that finishes (or is skipped by his choice) before the program changes.

---

## 6. Connecting machines and storage from the screen

### Machines: **PARTIAL**

- The place list is read and written through `GET/PUT /api/settings/engine` (machines #6). The reader is `QA/qmx-engine/src/qmx_engine/settings.py:56-67`. There is no dedicated route and no check of the fields on write.
- Adding a server is a command only: `qmx node setup <host> --machine <name>`, run on the PC over SSH (`QA/qmx-control/src/qmx_control/node.py:616-652`). Its steps print lines; it is not a resumable job, and no route starts it (machines #1, #5).
- Setup does not add the server to the place list. He must add the row by hand (machines #1).
- Compute providers: Modal and E2B as place rows with keys in the vault. No connect or test call. No Colab, AWS or RunPod (machines #2, #3).
- The status ladder `available → configured → authorized → reachable → healthy` exists in `QA/qmx-engine/src/qmx_engine/triggers/preflight.py:231`, and nothing calls it.
- The planned walk (copilot step cards, his steps vs QMX's steps) is written down (design:405-412) and its backend is a later step, "the add-a-server walk's backend" (design:453). Not built: no `resumable` setup anywhere in the code (searched).

### Storage: **PARTIAL**

- The only kind of backup place is a folder (`QA/qmx-home/src/qmx_home/backup/plan.py:44-48`, `:161-163`). One button accepts the suggested second drive (`POST /api/backups/targets/default/accept`, `QA/qmx-host/src/qmx_host/backups.py:655-660`).
- A bucket or account as a place that only keeps is designed (design:297, :331, :348) and planned under "places across systems" (design:452). Not built: no `keep_on` and no `can` field in the code (searched).
- rclone remotes are set up by hand in `rclone.conf`. Nothing in QMX creates one or signs in to Google (no `rclone config create` or `authorize` call, searched). `data/rclone.conf` is already treated as a secret file (`snapshot.py:73`; `QA/qma-harness/src/qma/harness/tools.py:921`).

### What a step-by-step dialog needs from the backend

1. **One job runner for connect steps.** The host already has background jobs with `step`, `done` of `total`, counts and one plain stop line (`QA/qmx-host/src/qmx_host/jobs.py:1-60`). Server setup and storage connect should run through it, step by step, resumable.
2. **Storage connect:** a call that creates an rclone remote (for Google Drive, the sign-in page opens in his browser and rclone keeps the token in `data/rclone.conf`), a "test it" call (list and free space), and then a place row that can only keep.
3. **Server connect:** setup as jobs; then write the place row (machines group (a) item 6); then walk the status ladder; then a one-node smoke test (design:410).
4. **Per-machine choices after connect:** deep logs here or not, backups here or not, which datasets it keeps (design:411). Each needs a read and a write.
5. **Telemetry install on that machine** (item 7).
6. **A list of what can be connected**, with what each kind can do (run, keep, both) for the dialog's first question. Missing: the place row has no role or `can` field (machines #7).

---

## 7. OpenObserve across machines

**PARTIAL.**

- **The setting.** `[telemetry] send_to` is `off` (default), `this-pc`, or a place name (`QA/qma-harness/src/qma/telemetry.py:1-46`). `this-pc` means `http://127.0.0.1:5080/api/default` (`telemetry.py:22`). A place means that machine's collector at `http://<name>:4318` over Tailscale (`telemetry.py:25`, `:46`). Chats, the engine's exporter, Hindsight and the host all read it (`QA/qma-harness/src/qma/harness/launch.py:567`, `QA/qmx-engine/src/qmx_engine/telemetry.py:553`, `QA/qmx-memory/src/qmx_memory/hindsight.py:106`, `QA/qmx-host/src/qmx_host/host.py:552`).
- **Saving it is not checked.** `PUT /api/settings/telemetry` stores any value (the section is in the list at `QA/qmx-control/src/qmx_control/service.py:73`; there is no check for it in `settings_put`, `service.py:796-900`). A bad value or a place that is not in the place list quietly sends nothing (`telemetry.py:49-65`).
- **Choosing `this-pc` only points at a port.** Nothing downloads, installs or starts OpenObserve on the PC. No code outside the server's recovery script names OpenObserve (searched `QA/*/src`). The plan for it (download into `cache/openobserve/`, run under the host, password in Credential Manager) is written (design:347) as the step "the deep log viewer on This PC" (design:445), not built.
- **On the server.** `openobserve.service` (data in `/srv/qmx/monitoring/openobserve`, port 5080) and `otelcol.service` with a disk queue are unit files with hand steps in their comments: "Install, once, as root" (`QA/qmx-host/deploy/openobserve.service:11-17`, `:29-34`; `QA/qmx-host/deploy/otelcol.service:1-27`). The recovery script knows both units (`QA/qmx-control/src/qmx_control/qmx-recover.sh:27`).
- **A newly connected machine gets nothing.** Server setup's steps have no monitoring step (`QA/qmx-control/src/qmx_control/node.py:634-651`).
- **Opening the viewer.** Only by hand in a browser: OpenObserve on the server at port 5080, reachable from the PC over Tailscale because the firewall lets all Tailscale traffic in (`qmx-recover.sh:542`). Sign in with the root email and password kept in `/etc/qmx/openobserve.env` on the server. Not checked live.
- **Doctor and screen.** No doctor row for telemetry; the doctor's rows are usage, the GPT lane, the relay, the process cap, the Library and backups (`QA/qma-harness/src/qma/harness/harness.py:1007-1030`; `QA/qmx-host/src/qmx_host/host.py:756`, `:763`). The data health read carries the exporter's sent, dropped and failed counters from `logs/telemetry.json` (`QA/qmx-control/src/qmx_control/service.py:2065-2069`, `:2124`). The "Deep logs" control is marked missing in the design (design:328-329). The UI agent's notes (`UI-HANDOFF.md`) have no entry for it or for backup settings (searched).

---

## 8. Old work: keep, reshape or no longer needed

| Piece | What it is | Verdict | Why |
|---|---|---|---|
| PR 225 (`build/br1`) | Copies on this PC and a second drive: settings reader, keep rule, hash pool, one round | **Reshape** | The pool, manifest, keep rule and safe copy order are exactly what a sync needs. Change: the hourly quick undo becomes a setting he can switch off (fixed at `QA/qmx-host/src/qmx_host/backups.py:273`; `QA/qmx-home/src/qmx_home/backup/plan.py:140`), and "leave out" becomes "what to save" by class (item 1). |
| PR 226 (`build/br2`) | Restore and the drill | **Keep** | A sync is useless without the way back. The drill (built, never scheduled, explore:20) becomes the check step of the monthly maintenance workflow. |
| PR 227 (`build/br3`) | The host makes copies by itself; warnings, doctor row, routes, price-store retry | **Reshape** | Keep the service, doctor row and routes. The timing changes from "every hour" to "on change, daily, and before an update". The price-store retry in QMF stays. |
| PR 228 (`build/br4`) | Restore from the start screen and the command line; copy before each upgrade | **Keep** | The first-start "Restore from a backup" is the "reinstall and it is as if I never left" path. It needs the account as a place to restore from. |
| PR 229 (`build/br5`, `D:/QMX-worktrees/bld-br5`, `1e5aaabd`) | Restore from Settings; safe first start after a restore | **Keep** | 5 files, +1,381 / −41 over `0ee50e42`. One check still fails (the scheduled-run check). |
| Planned PR 6 (plan:351-361) | Off-site copies through rclone | **Reshape into the core** | This becomes "sync to my account": an rclone place, compressed packs (item 3), maybe several remotes (item 4). Its per-file upload from a hard-link tree and its `lsf` arrival check change if packs are used. Merge the mini-app volume backup into it. |
| Planned PR 7 (plan:405-418) | Seal his keys into the copies with a passphrase | **Not needed now** | He never asked for it. In the account model he signs in again on a new PC and keys are not saved (the coordinator's own table, his-words:162). Park it as an option. |
| Attach plan (`ATTACH-PLAN.md` at `b08f13e7`) and its review (10 MUST) | Attach Library items, uploads, files, pages and videos to chats | **Keep, separate** | It does not overlap the sync. Two touch points: uploads land in his Library as his own content, so they are in the save set; and its review's MUST 6 (the attach guard misses `data/vault/`, `plan-attach-edge-cases.md` M6) should use the backup's one secret list (`snapshot.py:71-78`) so both agree. |
| Machines gap map (machines:1-114) | 25 machine capabilities, 6 / 13 / 6 | **Keep, and it feeds the dialog** | "Connect from the screen" needs its group (a) item 6 (setup adds the place row), item 3 (role and `can` on a place row), the walk's backend (design:453), and the bucket as a keep place (design:452). New needs it does not list: storage sign-in through rclone, and OpenObserve installed per machine. |

---

## 9. Code the new design would replace or merge

| Code | Lines | What happens |
|---|---|---|
| Weekly GitHub snapshot: `QA/qmx-control/src/qmx_control/backup.py` | 198 | Replace. Everything it copies is in the new copies (explore:76). Keep at most a "GitHub" place that saves recipes only, as the design says (design:274-276). |
| Its route `POST /api/backup/weekly`: `QA/qmx-control/src/qmx_control/service.py:1344-1364` | ~21 | Goes with it. |
| Its template `QA/qmx-engine/src/qmx_engine/templates/backup-weekly/` (definition 1,164 bytes, `scripts/backup.py` 46 lines, README) and catalog row `templates/catalog.py:396-404` | ~55 | Replace with the monthly re-pack-and-check maintenance workflow. |
| Mini-app volume backup: `QA/qmx-apps/src/qmx_apps/backup.py` | 196 | Merge. App volumes (`data/apps/<id>/`) are already in every copy, minus heartbeats and scratch (`snapshot.py:55-56`). |
| Its timer `QA/qmx-apps/src/qmx_apps/backup_schedule.py` | 51 | Goes with it. |
| Its wiring and routes `POST /api/apps/{id}/backup` and `/restore`: `QA/qmx-control/src/qmx_control/service.py:1628-1684` | ~57 | Goes with it. A per-app restore may stay as "restore one app from a copy". |
| Shared `[backup]` keys for app backups: `APP_KEYS` `QA/qmx-home/src/qmx_home/backup/plan.py:49-53` and `_volume_keys` `service.py:300-302` | ~8 | Goes: one `[backup]` meaning. |
| Unused machine list `RemoteSettings`: `QA/qmx-remote/src/qmx_remote/models.py:124-142`, its check `service.py:842-846`, and `"remote"` in the settings sections | ~25 | Delete. Nothing reads it (machines: "the `[remote]` section, which nothing uses"). `Target` in the same file stays: place rows use it. |
| Four rclone wrappers: `QA/qmx-apps/src/qmx_apps/backup.py:42-61`, `QA/qmx-control/src/qmx_control/node.py:470-475`, the Hub's calls in `QA/qmx-hub/src/qmx_hub/bucket.py`, and the planned `BK/rclone.py` | ~30 now | Merge into one helper that never echoes rclone's own output (it can hold credentials, `qmx_apps/backup.py:56`). The Hub's server push itself stays for what a server made (design:348). |
| Three free-space floors: 1 GB `QA/qmx-home/src/qmx_home/versions.py:39`, the host floor `QA/qmx-host/src/qmx_host/disk.py:55-62`, a tenth of the drive `backup/plan.py:56` | — | Merge into one floor he can see and change. |
| Fixed hourly quick undo: `QA/qmx-host/src/qmx_host/backups.py:273` | 1 rule | Becomes a setting with an off switch. |
| Old bundle installer `D:/QMX-worktrees/bld-br4/release/install.py`, `release/launcher.py` | 480 + 26 | Not part of the sync. Noted because it is not the real install path; a candidate to delete when the desktop installer comes. |

Left alone: the trading node's backup (`qmn/src/qmn/data/backup*.py`), QMF's backup building block (`packages/qmf-data/src/qmf/data/backup.py`) and container apps' live copies (explore:78, :82-83). They cover another machine or another job.

---

## Progress he sees today on first start and install

- **Install:** no installer. He clones and runs `uv sync` (design:380). Nothing shows progress.
- **The first-start card** (`GET /api/first-start`, routes at `QA/qmx-host/src/qmx_host/first_start.py:996-1005`):
  - "Make a new folder" and "Open a folder" answer at once, with no job.
  - "Restore" and "Bring in old data" answer 202 with a job, read at `/api/first-start/jobs/{id}`, one at a time (`first_start.py:888-965`).
  - A job reads as `running`, `finished` with a result, or `stopped` with one plain line; while running it carries `step`, `done` of `total` and counts (`QA/qmx-host/src/qmx_host/jobs.py:43-70`).
- **Bring-in steps** (with counts): "listing your old folder", "copying", "checking the copy", "moving your Library into the new one", "opening the new folder's stores" (`QA/qmx-host/src/qmx_host/bring_in.py:133-137`, counts at `:492`).
- **Restore steps** (a step line only, no counts): "checking the copy", "placing the copy's files", "checking the copy's stores" (`QA/qmx-home/src/qmx_home/backup/restore.py:290`, `:324`, `:326`); the finish runs staged, set-aside, moved-in, purges, carried files, labelled, logged (`restore.py:68-76`).
- **A backup round's steps:** stores, library logs, files, price months, files written once (`QA/qmx-home/src/qmx_home/backup/snapshot.py:100`).
- **Exit codes the desktop app branches on:** `serve`, `start`, `status`, `stop` exit 3 when a first start is due and 2 when a folder is refused; `first-start --serve` exits 4 when its port is taken, 0 after a handover (handover line last on stdout), 1 when it stopped with no handover (`QA/qmx-host/src/qmx_host/__main__.py:37-43`, `:69`).
- **Missing for a loading sequence:** an install step list, a restore with counts, and a "syncing your account" step.
