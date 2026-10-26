# 62a. Local first: a rubric walk of every QMX system

Written 2026-10-26 by a read-only research pass. Code truth is `build/wu9` at `d7391716` in `D:/QMX-worktrees/bld-wu9`, which equals `engine/base` at `d82be318` apart from merge commits. The UI design is `ui-review/repair` at `eea09941` (`C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair/apps/qmx-ui`), read as design intent. Rulings 136 and 140 to 145 of file 26 bind. This extends `61-server-substitute-and-wu9b.md` section D (gaps G1 to G12) and does not repeat them; where a row here touches one of them it names it. Nothing was edited, committed or pushed, and no vault, keyring or `~/.qmx` file content was read.

Paths in rows are short: `QA/` is `qmx-agents/packages/`, `E/` is `QA/qmx-engine/src/qmx_engine/`, `T/` is `E/templates/`, `H/` is `QA/qmx-host/src/qmx_host/`, `C/` is `QA/qmx-control/src/qmx_control/`, `UI/` is `apps/qmx-ui/src/` on the design branch.

## Plain words first

- **Most of QMX already runs on the PC with no server.** Chats, the router, memory, workflows, mini apps, the Library and the settings all start on his PC and never look for a server unless a setting names one. The PC's Library is the main copy by default (`[library] primary` is `pc`).
- **Three things still assume a server is there.** Connecting a cTrader account refuses the PC outright. The outside monitoring (the collector and OpenObserve) exists only on the server, and every chat and Hindsight send to the server's public address, which is typed into the code. Backups go to a private GitHub repository or to a server bucket, never to a second drive on his PC.
- **Several systems run on the PC but carry the server's name as their default.** The data downloaders call themselves the server, a finished price month is stamped "born on the server", one template runs "on contabo", and the list of places a job can run is fixed to three names, one of them Contabo.
- **His data is mostly in one folder, `~/.qmx`, in open formats, outside the program.** Deleting the git checkout leaves it alone. But some of it lands outside that folder: every workflow run's work sits in a second folder beside it (`~/.qmx.zones`), Hindsight's database sits in `~/.pg0`, and downloaded model files land in caches under his user profile. Program pieces also sit inside his data folder (Python environments, plugin copies, scripts).
- **His real `~/.qmx` today is the old layout** (`library.db`, `artifacts/`, `control.db`, `runs.db`) and has never been switched. If the new host starts on it before the switch script runs, it opens a fresh empty Library beside the old one and says nothing.
- **The UI design is already local first.** Day one shows "this laptop" only, and every "add a machine" menu is an option. A few screens still assume a server (the copilot's work area says jobs run on servers, the sweep dialog starts on a VPS), and no screen yet says where his data folder is or where the local backup goes.

## A. The walk, one row per system

Grades: **YES** runs fully on a PC with no server; **PARTIAL** runs on the PC but something needed is missing, refused or server-shaped; **NO** cannot work without a server today; **not built** has no code.

### A1. Human-facing: the agentic system, the UI, the Lab, pods, mini apps, workflows

| System | External compute or storage it uses or assumes | Where it runs by default (file:line) | PC, no server | Where its data lives, format, inside or outside program and checkout | Uninstall, reinstall, broken release | Gap and one-line recommendation |
|---|---|---|---|---|---|---|
| Copilot and harness (`qma-harness`) | Model providers over the internet (inherent). Every chat's Claude CLI sends OpenTelemetry to the server's collector. | On the PC, in the host process; home `Path.home()/".qmx"` (`QA/qmx-host/src/qmx_host/__main__.py:26`); the CLI's config dir is `<home>/claude` (`QA/qma-harness/src/qma/harness/home.py:122`) | YES | `<home>/claude/` (login `.credentials.json`, transcripts `projects/*/<chat>.jsonl`), `chats/<id>.json`, `procs/`, `state/`, `runs/<id>/journal.jsonl`, `exports/`, `agent-memory/`, `workspaces/`. JSON, JSONL, Markdown. Outside the checkout. The plugin is read from the checkout (`home.py:77`, `parents[5]/"plugin"`). | Survives deleting the checkout. A reinstall at a different plugin digest refuses until the shipped manifest matches (`home.py:95-102`), which is right. | The telemetry target is the server's public IP, hard-coded and always on (`QA/qma-harness/src/qma/harness/launch.py:404-414`, added to every launch at `:562`). Make telemetry off unless `telemetry.json` names a collector, and read the address from settings, never from code. |
| Router and providers (`qmx-router`) | Provider APIs (inherent). The central relay is a placement option, `placement.contabo.relay = "local"` (`E/settings.py:135`). | On the PC, in the host. Profiles at `<home>/profiles` (`H/host.py:973`). | YES | `profiles/`, `passes/revoked.json` (`QA/qmx-router/src/qmx_router/passes.py:332`). Keys in Windows Credential Manager `qmx/<provider>`. | Keys survive an app uninstall (they are in Windows, not the folder); they do not survive a Windows reinstall or a new PC, and QMX has no export for them. | Offer a sealed key export to the backup folder (his passphrase), so a new PC is a restore, not a re-entry. |
| Memory (`qmx-memory`, Hindsight) | Embedder and reranker models downloaded on first use; embedded Postgres (`pg0`). | On the PC (`H/host.py:432-436`: the PC always runs Hindsight; node and server roles only when `[memory] hindsight` says so). | YES | `<home>/memory/` (FTS5 SQLite, snapshot slot), `memory/hindsight/hf/` (model cache, `QA/qmx-memory/src/qmx_memory/hindsight.py:222`). Hindsight's own Postgres data is **outside the home**: `db_url = "pg0"` with no data folder (`hindsight.py:82`) puts it in `~/.pg0/instances/hindsight`, which exists on his PC today. Postgres files are not an open format, but Hindsight is a rebuildable index; the rows are Library objects. | Uninstall leaves `~/.pg0` behind (a messy file); a reinstall rebuilds the index from the Library (costs time only). | Pass a data folder to pg0 under `<home>/memory/hindsight/pg`, and say in Settings that the index rebuilds from the Library. Hindsight's traces also go to the server's IP (`hindsight.py:63,227`). |
| The UI (design, `ui-review/repair`) | None on day one. "Add machine" offers a VPS, a cloud GPU, Colab, a bucket (`UI/lib/settings/ServersDataSection.svelte:182-195`). | A Vite dev server on `127.0.0.1:5173` (the host's `--ui-origin` default, `QA/qmx-host/src/qmx_host/__main__.py:29`). Not wired to the host: actions say "needs the daemon" (`ServersDataSection.svelte:103`). | PARTIAL | UI state is in the browser's `localStorage` in nine files (for example `UI/lib/settings/settings.svelte.ts`, `UI/lib/lab/lab.svelte.ts`, `UI/lib/apps/apps.svelte.ts:755-765`). That is outside his data folder and is lost with a browser profile reset. | A browser reset loses UI settings; a reinstall of QMX does not touch them, but they are not in his folder either. | When the UI is wired, every setting it keeps goes through the host into `settings.toml`; the browser keeps only view state (open tab, column widths). |
| The Lab (`C/lab.py`) | The PC's GPU slot; the market-data door. | On the PC: a training run is a PC placement (`C/lab.py:15-17`, `:182` `"placement": "pc"`). | PARTIAL | Projects are Library `collection` items; workspace layout is an annotation. Inside the home. | Survives. | The Lab "materialises partitions into the PC cache" (`C/lab.py:17`): the PC is named a cache of the server's data (G2's wording in code). Its data panel needs the market door, which stays shut until a seal boundary is set (`H/host.py:907-923`, WU11 not landed). Call the PC store the main copy and land WU11. |
| Pods | Design only (Lab AD-10 to AD-12). The UI's kill grid is pods by servers (`UI/lib/portfolio/KillMatrix.svelte:3-5`). | Nowhere. | not built | None. | None. | When pods are built, a pod's home is a placement like any other, `pc` by default; the kill grid shows "this PC" as a column when no server exists. |
| Mini apps (`qmx-apps`) | Docker only at tier T2 (`C/service.py:1398-1415`); app backups need an rclone remote (`QA/qmx-apps/src/qmx_apps/backup.py:26-30,134-137`). | On the PC: `placement: str = "pc"` (`QA/qmx-apps/src/qmx_apps/supervisor.py:247`), tier T1 local processes by default (`C/service.py:429`). | YES | `<home>/apps.db`, `artifacts.db`, `artifacts/`, `definitions/<hash>/app.toml`, `apps/<id>/{data,blobs,road}`, `road-locks/`, plus program pieces: `environments/<hash>/` (uv virtual environments, `supervisor.py:264,381`), `network/`, `replicas/`. SQLite, JSON, TOML. Inside the home. | Data survives. The virtual environments inside the data folder can break when the Python or uv on the PC changes after a reinstall. | Move `environments/` out of the data folder into a program cache (rebuilt from the locked definition on demand), so the data folder holds only data. |
| Workflows (the engine, `qmx-engine`) | Placements: `pc`, `contabo`, `qmb`. | On the PC: a node's placement is `"pc"` (`E/nodes/base.py:39`); webhooks home on `pc` (`E/settings.py:108`). | YES | `<home>/engine/engine.sqlite`, `engine/inbox.sqlite`, `engine/runs/<run>/workflow/` and `trace-*.jsonl`, `workspaces/wf-<id>/`. Each run's working zone is **outside the home**, in a sibling folder `<home>.zones/<run>/{code,work,attempts}` (`E/workers/zones.py:82-89`). SQLite, JSON, JSONL. | Uninstall leaves `~/.qmx.zones` as a second top-level folder; a reinstall at an older engine refuses the newer ledger (`E/ledger/migrations.py:100-103`), so "go back to the previous version" cannot open a home a newer release touched. | Put zones under `<home>/zones/` with the stray-path guard kept, and make placement names his own list (see section C). A downgrade path (or a read-only open) for the ledger is needed before a rollback can be promised. |
| Templates (`E/templates/`) | Downloaders, backup (GitHub), extraction (Docling), training (torch), `run-on-a-machine`. | Mostly the PC (no `runs_on` means `pc`). Exceptions: `run-on-a-machine` runs on `contabo` (`T/run-on-a-machine/definition.json:24`); downloaders call themselves the server (rows below). | PARTIAL | Template folders ship in the package (read only); runs write under the home and the zones. | Survive. | Default every template to `pc`; `run-on-a-machine` asks which machine instead of naming Contabo. |

### A2. Less human-facing, compute-heavy: data, backtests, QML, the trading node, the MIS, extraction, training

| System | External compute or storage it uses or assumes | Where it runs by default (file:line) | PC, no server | Where its data lives, format, inside or outside | Uninstall, reinstall, broken release | Gap and one-line recommendation |
|---|---|---|---|---|---|---|
| QMF data and the market-data door (`packages/qmf-data`, `H/market_data.py`) | None required; the design makes the server the main copy. | The host's door is `<home>/market` (`H/host.py:913`, `MARKET` at `:127`), with the machine's role as its placement. | PARTIAL | `<home>/market/<source>/<subject>/<kind>/<variant>/<month>.parquet` (open month `open.parquet`, `packages/qmf-data/src/qmf/data/series.py:4-9`), SQLite metadata, `handles/`. Parquet and SQLite: open. Inside the home. | Survives. | The door stays shut with no seal boundary (`H/host.py:907-923`; ruling 137, WU11 not landed). The `Placement` enum says "the server holds the main copy and is the primary" (`H/market_data.py:106`), and a commit defaults to `born_on = SERVER` (`:495`, the HTTP body at `:953`), so a PC commit that names nothing is recorded as server-born. Flip both defaults to `PC` with G2. |
| Data downloaders (`T/download-dukascopy`, `download-binance`, `download-ccxt`) | The provider's free files over the internet (inherent). | On the PC (no `runs_on`), but each opens its door as the server: `placement = Placement(str(data.get("placement") or "server"))` (`T/download-dukascopy/scripts/download.py:234`, `download-binance/...:157`, `download-ccxt/...:160`). | PARTIAL | Wherever `[data] root` points. There is **no default**: the step fails with "this home's settings name no [data] root" (`download-dukascopy/scripts/download.py:228-233`). The host door uses `<home>/market` instead, so two notions of the data root exist. | Survives if the root is inside the home; anywhere else it is whatever drive he named. | Default `[data] root` to `<home>/market` (one root for the host and the templates) and default `placement` to `pc` (G5 in code). |
| Old ticks import (`scripts/data/import_old_ticks.py`) | The server home. | Defaults to the server: `--raw-backup /srv/qmx/data/raw-backup` (`:771`), `--market SERVER_HOME/market` (`:781`). | PARTIAL | The 10 GB of old ticks sit in `C:/Users/Mubarak/Documents/QMX/data/raw/...` (ruling 130), outside the home. | Not affected. | G9 holds; the defaults in code are the concrete lines to change. |
| QMB backtests (`qmb/`) | A "dedicated QMB machine" in the design (`QA/qmx-tools/src/qmx_tools/service.py:176-181`, placement `qmb` in `E/definition/validate.py:29`). | The QMB library runs wherever it is called; its scratch work goes to the OS temp folder (`qmb/src/qmb/host/replay.py:811`, `runner.py:346,399`, `operator_replay.py:509`). | PARTIAL | Results land in the Library as `backtest-result` items. QMB's own CLI writes `results/` under the project root it is given (`qmb/src/qmb/results/ct32.py:129`). | Survives. | The agents' `backtest` tool needs a `backtest_door`, and **no production code binds one** (only `QA/qmx-tools/tests/test_tools.py:165`); a chat gets "This host binds no qmb_backtest door" (`service.py:293-299`). Bind a PC door in the host by default; the `qmb` placement becomes extra capacity. |
| QML (the unit library, `qml/`) | None. | A library, used in process. | YES | Units are Library items. | Survives. | None for this principle. |
| QMN and the trading node (`qmn/`) | A Linux server is the natural home (ruling 140). | The deploy is Linux and systemd: `/var/lib/qmx`, `/var/lib/qmx-observability` (`qmn/deploy/install.py:44-45`, `qmn/deploy/systemd/units.py:47-48`). A Windows deployment path exists (`qmn/src/qmn/host/configured_runtime.py:51-52`). The supervisor needs `QMX_ROOT`, `QMX_STATE`, `QMN_EVIDENCE_BIND` with no defaults (`qmn/src/qmn/host/_supervision.py:478-485`). | PARTIAL | Node state under `/var/lib/qmx/{rooms,state,evidence,staging,archive}` (`qmn/deploy/observability/stack.py:198-200`, `qmn/src/qmn/data/backup_run.py:82`), never in the PC's home. | A node's records are not in his data folder, so his folder alone does not restore a node. | The unit and trading-node sessions own this (G11). For this principle: on a PC the node's state folder defaults to `<home>/node/`, and a node's records come home to the PC. |
| The MIS (`qmn/src/qmn/mis/`) | A training machine (MIS training is last, per his rulings). | Needs `--output-dir` (`regime_train.py:1411`, `regime_eval.py:1077`) and finds the git checkout by walking up to `uv.lock` (`regime_train.py:2075-2080`). | PARTIAL | Wherever `--output-dir` points. | Tied to the checkout: it reads the lock file of the program, not the data folder. | When the MIS is built, its outputs go to the Library and `<home>`, and it reads its pins from the home, not the checkout. |
| ML training on the GPU (`T/d6-ml-training-run`, the Lab) | The PC's GPU. | The PC: `placement.pc.gpu_slots = 1` (`E/settings.py:133`), the dataset step opens the door as `pc` (`T/d6-ml-training-run/scripts/dataset.py:173`). | PARTIAL | Weights `weights.pt` in the run's zone (`train.py:38`), so outside the home in `<home>.zones/`. | A zone is pruned by retention; a model kept only there is lost. | `torch` is declared in **no** `pyproject.toml`, so a fresh install cannot train. Declare it as an optional extra, and land the trained model in the Library (blob plus lineage) rather than leaving it in the zone. |
| Extraction (Docling, `T/extract-source`) | Docling's models (downloaded on first use). | Where the run is placed, the PC by default; a child process (`T/extract-source/extract/scripts/extract.py:1-11`). | PARTIAL | Text lands in the Library. Docling's model downloads go to the user profile cache, because script nodes inherit `HOME`, `APPDATA`, `LOCALAPPDATA`, `TEMP` and not `HF_HOME` (`E/nodes/script.py:44-52`). | Model caches survive outside the folder (messy). | Docling is declared in **no** `pyproject.toml` (the step answers "not installed") and nothing calls `extract-source` but the catalog (`T/catalog.py:478-482`). Declare it as an optional extra, wire the upload door to it, and give script children a cache folder under the program cache. |

### A3. DevOps, monitoring, backups, buckets, the Library, the Hub, sync, keys, connections, feeds

| System | External compute or storage it uses or assumes | Where it runs by default (file:line) | PC, no server | Where its data lives, format, inside or outside | Uninstall, reinstall, broken release | Gap and one-line recommendation |
|---|---|---|---|---|---|---|
| Internal health view and logs | None. | On the PC: engine inbox and incidents (`E/ledger/inbox_table.py:116`), `<home>/control.log` (`H/host.py:1143`), `<home>/logs/` (`T/connections-health/scripts/health.py:102`). | YES | SQLite, text, JSON. Inside the home. | Survives. | None. |
| OpenTelemetry collector | The server. | Server only: "There is no collector on the PC" (`QA/qmx-host/deploy/otelcol.yaml:1-5`); the engine's exporter is off unless `telemetry.json` or `QMX_OTLP_ENDPOINT` names one (`E/telemetry.py:13-16,554`), but its fallback default is the server's IP (`E/telemetry.py:49`). | NO | The server's queue `/srv/qmx/monitoring/otelcol/queue`. | Not on the PC. | Ruling 140 lists monitoring. Ship the same collector config as an optional PC service (or the in-process exporter writing OTLP JSON files under `<home>/logs/otlp/`), and send to a server only when he adds one. |
| OpenObserve | The server. | `QA/qmx-host/deploy/openobserve.service` (Linux systemd, `ZO_DATA_DIR=/srv/qmx/monitoring/openobserve`). | NO | The server. | Not on the PC. | OpenObserve ships a Windows binary; offer "run the deep log viewer on this PC" in Settings, with the server as the long-retention copy. |
| Backups | A private GitHub repository via `gh`, or a server bucket. | `backup.repository` unset means nothing is backed up (`T/backup-weekly/scripts/backup.py:24-29`). A local folder is accepted only as a bare git repository and is treated as a "dry run" (`C/backup.py:68-77`); the real path must be `owner/repo` on GitHub (`:79-96`). | PARTIAL | The snapshot leaves out every blob, `chats/`, the Claude transcripts, `engine/engine.sqlite`, `control.db`, `portfolio.db` and `artifacts.db` (the database list `C/backup.py:25-32` and the filter `:118-132`). | A restore from it would lack his chats, run history and every file blob. | G7 named the shape; the code facts are new: make a local folder (another drive) a first-class target, copy the whole home minus rebuildable caches, and keep GitHub and buckets as extra copies. |
| Buckets | rclone remotes on the server. | Server only: the Hub's bucket push (`QA/qmx-hub/src/qmx_hub/bucket.py:1-8`); the remote runner's defaults `bucket: "vps:/srv/qmx/bucket"`, `root: "/srv/qmx/bucket"` (`QA/qmx-remote/src/qmx_remote/models.py:103,124`); the bootstrap makes a `type = local` remote on the server (`C/node-bootstrap.sh:55-56`). | NO | The server. | Not on the PC. | A bucket is an optional extra copy the PC can push to directly (rclone runs on Windows); the PC's backup target list includes it. |
| The Library (`qmx-library`) | None required. | The PC: `<home>/library` (`C/library.py:65-74`), primary `pc` by default (`C/node.py:249`). | YES | `objects/ab/cd/<hex>.json`, `blobs/ab/cd/<hex>`, `blobs/fetched/`, `blobs/transient/`, `blobs/tombstones/`, `refs/log.jsonl`, `refs/claims.json`, `edges/<store>.jsonl`, `annotations/log.jsonl`, `kinds/*.schema.json`, `catalog.db` (rebuilt), `writer.lock`, `uploads/<id>.part` (`QA/qmx-library/src/qmx_library/store.py:1-26`). JSON, JSONL, raw bytes, SQLite index. Open and inside the home. | Survives. On his real home the old `library.db` sits beside it; the host opens a new empty store with no warning (see section E). | G1 to G8 hold. New: refuse to start (or offer the switch) when `library.db` exists and `library/` is empty. |
| The Hub (`qmx-hub`) | A server by role. | Standalone Hub defaults: `--home /var/lib/qmx` (`QA/qmx-hub/src/qmx_hub/server.py:957`), `primary` defaults to `server` when `hub.toml` names none (`:969`). | NO (server part, not needed on the PC) | `/var/lib/qmx/hub.toml`, `hub.port`. | Not on the PC. | Default `primary` to `pc` in the standalone Hub too (G12 covers the bootstrap line only). |
| Sync (PC and server) | A second machine by nature. | The PC links to a Hub only when `[library] hub_url` and a pairing key exist (`H/host.py:886-892`); otherwise nothing syncs and nothing waits. | YES (the PC never waits) | Outbox under `<home>/library/` (`E/heartbeat.py:334`). | Survives. | G6 holds. |
| The vault and keys | Windows Credential Manager on the PC; a sealed key copy for servers. | The PC: keys under `qmx/*` in Credential Manager; the control token `qmx/control-token` (`C/server.py:51-72`). | YES | Outside the home: Credential Manager. Inside: `vault/pairing-key`, `vault/tokens.json`, a nested `<home>/.qmx/vault.key` (`QA/qmx-router/src/qmx_router/vault.py:62-65,196`), `vault-store.json`. | Credential Manager survives an app uninstall, not a Windows reinstall. The nested `.qmx` folder inside `.qmx` is confusing. | Rename the nested key folder to `<home>/vault/` and add the sealed export from the router row. |
| Connections and brokers (`qmx-broker`, `H/venue_session.py`) | The broker; for cTrader a server "home" for the sign-in. | cTrader's home defaults to `contabo` (`H/venue_session.py:68`) and the PC is refused: `pc_not_home`, "the PC never holds the sign-in; name the server as home" (`:304-306`); without a pairing key it answers `not_paired` (`:347`), without a server URL `waiting_for_server` (`:308-309`). | NO (cTrader) | `<home>/portfolio.db` (`QA/qmx-broker/src/qmx_broker/service.py:109`), `vault/tokens.json` on the home machine. | Survives where it is held. | Ruling 135's one-home rule is about where a sign-in lives, not about needing a server. When no server exists the PC is the home for read-only and demo sign-ins; the home moves to a trading server when he adds one. Rulings 140 and 142 need this. |
| Feeds (`T/feed`) | Source sites over the internet (inherent); Firecrawl and agent browsers for two methods. | The PC (no `runs_on`); items land as Library `source` items (`T/feed/README.md:9-17`). | YES | Library items, inside the home. | Survives. | The spine still says feeds default to the server (G5, engine AD-68). The `firecrawl` and `browser` methods are unbuilt regardless of placement. |
| Remote placements (`qmx-remote`) | SSH, Amp, Modal, E2B targets. | `default_target = "vps"` (`QA/qmx-remote/src/qmx_remote/models.py:123`). | NO (by nature, extra capacity) | Remote. | Not on the PC. | Default target empty: a job with no target runs on `pc`, and "Configure the remote target in Settings first" (`:130`) only appears when he asked for remote. |
| The recovery script (ruling 139) | The server. | `C/qmx-recover.sh` on the server; the PC twin is written to `<home>/bin/` (61 WU9b). | YES (the PC twin is local) | `<home>/bin/qmx-recover.ps1` and its conf: a program file inside his data folder. | A reinstall leaves an old script in the data folder. | Keep the twin in the program folder and have it read the home path from the pointer file (section B). |

### Counts

29 systems walked. **Local first today: 11** (copilot and harness, router, memory, mini apps, workflows, QML, internal health, the Library, sync, the vault, feeds). **Partial: 11** (the UI, the Lab, templates, the data door, the downloaders, QMB, QMN, the MIS, ML training, extraction, backups). **Server-only: 6** (the collector, OpenObserve, buckets, the Hub, cTrader connections, remote placements). **Not built: 1** (pods). Of the six server-only, the Hub and remote placements are servers by nature and fine; the collector, OpenObserve, buckets and cTrader connections break rulings 140 and 142.

## B. Today's QMX home, as the code creates it

The default home is `Path.home() / ".qmx"` in five separate places (`QA/qmx-host/src/qmx_host/__main__.py:26`, `QA/qma-harness/src/qma/console.py:822`, `C/server.py:487`, `QA/qmx-tools/src/qmx_tools/servers.py:43` through `QMX_TOOLS_ROOT`, `QA/qmx-broker/src/qmx_broker/server.py:75` through `QMX_HOME`). There is no single pointer that says where his data is, and `qmx node setup`, `pair` and `vault install` default to `./qmx-home` in the current folder (`C/node.py:857,874,898`).

```
~/.qmx/                                   the home (QmxHome.root)
  settings.toml            TOML     every setting; the one file the UI edits
  control.db               SQLite   control plane (C/service.py:470)
  observers.json           JSON     observer list (C/service.py:82)
  runs.db                  SQLite   run index (C/runs.py:26)
  control.log              text     host log (H/host.py:1143)
  telemetry.json           JSON     optional collector config (E/telemetry.py:46)
  logs/                    JSON     telemetry counters, health output
  claude/                  CLI home: .credentials.json (plan login), projects/*/<chat>.jsonl
  claude-relayed/          CLI home for key chats; projects/ is a junction to claude/projects
  chats/<id>.json          JSON     one record per chat; chats/<id>/ launch settings
  procs/<id>.json          JSON     pid files
  state/                   JSON     probe results
  runs/<id>/journal.jsonl  JSONL    usage journal per chat
  exports/<chat>-<stamp>/           chat exports
  agent-memory/<slug>/     Markdown auto memory per workspace
  workspaces/              folders  default working folders; wf-<id>/ per workflow
  slots/                   Markdown surface slots (methodology/general.md)
  plugins/                 program  materialised pack plugins
  profiles/                         model registry
  library/                 the Library store (JSON, JSONL, raw blobs, SQLite index)
  memory/                  SQLite FTS5, snapshot; memory/hindsight/hf/ model cache
  engine/engine.sqlite     SQLite   the run ledger (E/ledger/store.py:52)
  engine/inbox.sqlite      SQLite   inbox and incidents
  engine/runs/<run>/       JSON, JSONL  frozen workflow copy, trace-<seq>.jsonl
  market/                  Parquet + SQLite meta, handles/
  apps.db, artifacts.db    SQLite   mini apps
  artifacts/               blobs    app artifacts
  definitions/<hash>/      TOML, files  app images
  environments/<hash>/     program  uv virtual environments
  apps/<id>/{data,blobs,road}/      app volumes
  road-locks/, network/, replicas/  app runtime
  portfolio.db             SQLite   broker portfolio
  vault/                   pairing-key, tokens.json (+ .lock), control-token (headless Linux only)
  .qmx/vault.key           raw 32 bytes, this machine's vault key
  vault-store.json         JSON     sealed key copies
  passes/revoked.json      JSON
  hub.toml, hub.port       TOML, text   (server and Hub)
  weekly-backup.json/.lock JSON
  migration/               pre/, retired/, dry/, alarms.jsonl, switch-report.json
  bin/                     program  the recovery twin and its conf
~/.qmx.zones/<run>/{code,work,attempts}/   OUTSIDE the home: every run's zone (E/workers/zones.py:82)
```

Formats in use: TOML, JSON, JSONL, Markdown, SQLite, Parquet, raw blobs, plain text, and Postgres (Hindsight's index, in `~/.pg0`). All but Postgres are open; Postgres holds only a rebuildable index.

His real `~/.qmx` today (top-level names only): `artifacts/`, `control.db`, `library.db` (with `-wal` and `-shm`), `runs.db`. No `settings.toml`, no `claude/`, no `library/`. It is the old layout and has not been switched.

Mixed in the data folder but not data: `environments/`, `plugins/`, `definitions/` images, `bin/`. Ruling 141 wants the program and the data loosely coupled; these four are program pieces that a reinstall should own.

## C. Messy files: everything written outside the home

| Where | Who writes it (file:line) | Kind |
|---|---|---|
| `~/.qmx.zones/` beside the home | every workflow run (`E/workers/zones.py:82-89`) | a second top-level data folder |
| `~/.pg0/instances/hindsight`, `~/.pg0/installation` | Hindsight's embedded Postgres, no data folder passed (`QA/qmx-memory/src/qmx_memory/hindsight.py:82`); both exist on his PC | data outside the home |
| `~/.hindsight/` | Hindsight's own defaults (daemon log); present on his PC | stray folder |
| `%TEMP%/qmx-engine-*` | `python -m qmx_engine` with no `--home` makes a whole home in temp (`E/__main__.py:133`) | a home in temp |
| `%TEMP%/qmx-merge-*`, `qmx-weekly-*`, `qmx-backup-*`, `qmb-*`, `qml_*` | Library merges (`store.py:160`), the weekly backup clone (`C/backup.py:109`), app backups (`QA/qmx-apps/src/qmx_apps/backup.py:132`), QMB replays (`qmb/src/qmb/host/replay.py:811`, `runner.py:346,399`) | scratch, cleaned on exit; fine if it stays scratch |
| `~/.cache/huggingface`, `%LOCALAPPDATA%` caches | script children inherit the real `HOME`, `APPDATA`, `LOCALAPPDATA`, `TEMP` (`E/nodes/script.py:44-52`), so Docling, torch and pip caches go to his profile | caches outside both program and data |
| `%LOCALAPPDATA%/uv` | uv's cache and Python installs, used by app environments (`QA/qmx-apps/src/qmx_apps/supervisor.py:359-381`) | program cache, acceptable |
| `~/.config/systemd/user/` | the chat memory slice on Linux (`QA/qma-harness/src/qma/harness/procs.py:444-447`) | system config |
| Windows Credential Manager `qmx/*` | keys and the control token (`C/server.py:61-67`) | by design (ruling 116) |
| `./qmx-home` in the current folder | `qmx node setup`, `pair`, `vault install --pc-home` (`C/node.py:857,874,898`) | a stray home wherever he typed the command |
| Browser `localStorage` | the UI design, nine files (section A1) | settings outside his folder |
| `C:/Users/Mubarak/Documents/QMX/data/raw/...` | the old ticks (ruling 130) | data outside the home |
| `/srv/qmx/*`, `/var/lib/qmx/*`, `/etc/qmx/*`, `/var/lib/qmx-observability`, `/var/lib/qmx-recover` | the server and node (`C/node.py:95-112`, `C/node-bootstrap.sh:46-72`, `qmn/deploy/install.py:44-45`) | server layout; two server homes exist side by side (`/srv/qmx/home/.qmx` for the host, `/var/lib/qmx` for the bootstrap and Hub) |
| Hard-coded `D:/QMX-worktrees/qma-ship/build/...` | live lanes, for example `scripts/live/engine/bug3_gates.py:63`, `scripts/live/apps/app2a_lanes.py:34`, `e61_app_check.py:26` | test evidence only; no production module carries a `D:/` path |
| Repo-relative `out/`, `data/` | `scripts/live/engine/e50_overlays.py:49-50`, `scripts/probes/server/p_app.py:69` | test scripts writing into the current folder |
| The main checkout | untracked `.svelte-kit/` and `.vite/` at `C:/Users/Mubarak/Desktop/QMX` (git status), `evidence/` and `workroom/` folders in the build tree | dev clutter in the program folder |

No production code writes into the git checkout at run time: templates, the QMN failure list and the plugin are only read from it.

## D. Defaults that point at a server or assume one

1. The collector address `http://155.133.27.86:4318` is typed into code three times: `QA/qma-harness/src/qma/harness/launch.py:404` (always on for every chat, `:407-414,562`), `E/telemetry.py:49` (the fallback once enabled), `QA/qmx-memory/src/qmx_memory/hindsight.py:63,227` (always on). With no server these sends fail quietly. If Contabo ever gives that address to someone else, chat telemetry and Hindsight traces go to a stranger.
2. Downloaders open their door as `server` (`T/download-dukascopy/scripts/download.py:234`, `download-binance/scripts/download.py:157`, `download-ccxt/scripts/download.py:160`).
3. A price commit is `born_on = SERVER` unless named (`H/market_data.py:495,953`); the enum says the server is primary (`:106`).
4. `run-on-a-machine` runs on `contabo` (`T/run-on-a-machine/definition.json:24`).
5. The placement list is closed to `pc`, `contabo`, `qmb` (`E/definition/validate.py:29`); the ledger's `home_engine` column only accepts `pc` or `contabo` (`E/ledger/migrations.py:36,59`; `E/triggers/rows.py:37`); a non-PC host with no name calls itself `contabo` (`H/host.py:879-883`). A second server, or a server that is not at Contabo, has no name to take.
6. `placement.contabo.*` rows ship as defaults on every PC (`E/settings.py:134-138`), so Settings shows a Contabo machine he may never have.
7. cTrader's sign-in home is `contabo` and the PC is refused (`H/venue_session.py:68,304-306`).
8. The remote runner's default target is `vps` and its bucket is `vps:/srv/qmx/bucket` (`QA/qmx-remote/src/qmx_remote/models.py:103,123-124`).
9. The standalone Hub's `primary` defaults to `server` (`QA/qmx-hub/src/qmx_hub/server.py:969`); the bootstrap writes `primary = "server"` (G12).
10. The vault's machine default is `contabo` (`C/node.py:177`, used by `vault install` and `vault key`).
11. Backtests assume "one dedicated QMB machine" (`QA/qmx-tools/src/qmx_tools/service.py:178`), and nothing binds a PC door.
12. The Lab calls the PC store a cache (`C/lab.py:17`).
13. The collector and OpenObserve exist only as Linux services (`QA/qmx-host/deploy/otelcol.yaml:1-5`, `openobserve.service`).
14. Spine text still homes things on the server: engine AD-30 "Contabo is the always-on home", engine AD-68 feeds, Library AD-26 "the server holds the main copy this week" (titles at `workflow-engine/ARCHITECTURE-SPINE.md:265,609`, `library-and-data/ARCHITECTURE-SPINE.md:214,490`). The 61 amendments mark them superseded in the body; the titles and the C4 box still read server-first.

Already right: `[library] primary` defaults to `pc` (`C/node.py:249`), Hindsight runs on the PC (`H/host.py:432-436`), node placement defaults to `pc` (`E/nodes/base.py:39`), webhooks home on `pc` (`E/settings.py:108`), mini apps run on `pc` (`supervisor.py:247`), the engine's own exporter is off by default (`E/telemetry.py:13-16`), and the host links to no Hub until both `hub_url` and a pairing key exist (`H/host.py:886-892`).

## E. A first boot on a PC with no server, step by step

1. **Get the program.** Clone the repository, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/` (the boot recipe in `WRAPUP-PLAN.md:80-85`). Needs git, uv and internet. There is no installer; "the program" is a git checkout and its `.venv`. *Works.*
2. **If the home is the old layout, switch it first.** His real `~/.qmx` holds `library.db` and `artifacts/`. `scripts/data/switch_library.py` must run before the host (`switch_library.py:1-21`). If he skips it, the host opens a new empty `library/` beside the old files with no warning (`C/library.py:65-74`), and his items look gone. *Trap.*
3. **Start the host.** `python -m qmx_host start --home ~/.qmx --port 8766`; the role is `pc` by default (`QA/qmx-host/src/qmx_host/__main__.py:28`). It writes the home layout and makes `qmx/control-token` in Credential Manager. No server is touched. *Works* (proven on a throwaway home, `LAUNCH-AND-CLEANUP-MAP.md:131`).
4. **Sign in once and add keys.** `/login` inside `~/.qmx/claude`; provider keys as `qmx/<provider>` in Credential Manager. No screen does this yet (the UI is not wired), so it is a manual step. *Works by hand.*
5. **Chat and delegate.** Plan chats and key chats run. Each chat's CLI tries to send telemetry to the server's IP and fails quietly. *Works, with a quiet failed send.*
6. **Memory.** Hindsight starts on first use, downloads its embedder and reranker into `memory/hindsight/hf/`, and puts its database in `~/.pg0` (about 2.2 GB of memory at peak, per P-MEM). *Works; writes outside the home.*
7. **Workflows and templates.** Workflows run on the PC; zones appear in `~/.qmx.zones`. Installing the template pack test-runs each template on real models (`T/install.py:3-8`), so it needs a provider. *Works.*
8. **Market data.** The host's door stays shut until `[data] seal_boundary_ns` is set (`H/host.py:907-923`); the downloaders fail until `[data] root` is set (`download.py:228-233`), and then label their months as server-born. *Fails until two settings are typed by hand; WU11 fixes the first.*
9. **Backtests from a chat.** "This host binds no qmb_backtest door" (`QA/qmx-tools/src/qmx_tools/service.py:293-299`). *Fails.*
10. **Connect a cTrader account.** Refused: `pc_not_home`, then `not_paired`, then `waiting_for_server` (`H/venue_session.py:304-309,347`). *Fails with no server.*
11. **Backups.** Nothing is backed up until `backup.repository` names a private GitHub repository; no local drive target exists (`C/backup.py:68-96`). *Not available locally.*
12. **Extraction and training.** Docling and torch are in no `pyproject.toml`, so `extract-source` answers "not installed" and the training step cannot import torch. *Fails until installed by hand.*
13. **Monitoring.** The internal health view works. The deep log view (OpenObserve) does not exist without a server. *Partial.*
14. **The UI.** The design runs as a Vite dev server and shows day one ("this laptop" only), but its actions say "needs the daemon". *Design only.*

So a no-server first boot gives him chats, memory, workflows, mini apps, feeds and the Library today. It does not give him market data without two hand-typed settings, backtests from chat, a broker connection, any backup, extraction, training or the deep log view.

## F. Where the UI design lets him add or choose external compute or storage (rulings 144, 145)

Every place below is on `ui-review/repair`, under `apps/qmx-ui/src/`. "Assumes a server" means the screen reads as if one exists on day one.

| Screen | What he can add or choose | File | Assumes a server? |
|---|---|---|---|
| Settings, Connections, **Servers and data**, Machines | "Add machine": a VPS over SSH, a cloud GPU (AWS, RunPod), Google Colab, a storage bucket. Day one lists only this laptop ("Lab, Storage", "Here"). | `lib/settings/ServersDataSection.svelte:80-97,168-195`; tab id `servers` in `routes/settings/+page.svelte:49` | No |
| Settings, Servers and data, **Data sources** | Add a source: upload, API provider, scrape a site (Firecrawl switch), RSS feed, with a schedule. No choice of where it runs or where its data is kept. | `lib/settings/ServersDataSection.svelte:106-160,245-395` | No, but missing the "on this PC / on a server" choice ruling 140 asks for |
| Settings, Connections, **Brokers and accounts** | Accounts as live, demo or watch-only, "tied to the server that trades it". | `lib/settings/BrokersSection.svelte:5` | Yes |
| Lab header, **machine picker** | Pick the machine to look at; "Runs start on this laptop"; "Add or manage machines" opens Settings. Day one shows only this laptop. | `lib/lab/MachinePicker.svelte:3-6,24-25,58,88-89` | No |
| Lab, **Compute** panel | Add a server over SSH, Colab, AWS/GCP/Azure, RunPod/Lambda/Vast, another QMX machine; "Add storage" (marked new scope). | `lib/lab/panels/ComputePanel.svelte:20-24,118-127` | No |
| Lab, **Resources** panel | Machines group, with a link to Settings. | `lib/lab/panels/ResourcesPanel.svelte:20-45` | No |
| Lab, **where a job runs** chip | Shows local, remote host or cloud; off-machine work is tinted. | `lib/lab/EnvChip.svelte:3-22` | No |
| Lab, **New…** dialog | The workflow path has a "Where it runs" step. | `lib/lab/StartDialog.svelte:102-108` | No |
| Lab, **sweep** dialog | The machine for a sweep; the default is `vps-fsn`. | `lib/lab/ScenarioDialog.svelte:96-109` | Yes (default should be this laptop) |
| Lab, runs, matrix, training, agents panels | Filter by machine; "Ran on another machine". | `lib/lab/panels/RunsPanel.svelte:31,94-98`, `MatrixPanel.svelte:150-156`, `TrainingPanel.svelte:63-67`, `AgentsPanel.svelte:4-19`, `lib/lab/MachineEmpty.svelte` | No |
| Workbench, **guided start** | "Where should the first test run?", "Where should it train?", "Where does it run?", each with "This laptop" first. | `lib/workbench/GuidedStart.svelte:46-48,78-80,110-112` | No |
| Workbench, **day one** lines | "Only this laptop", "No trading servers", "Add a machine". | `lib/workbench/day-one.ts:24,57,84` | No |
| Workbench, **status bar** | Machines menu and "Manage machines". | `lib/workbench/StatusBar.svelte:50-70` | No (demo list only) |
| Portfolio, **trading servers** strip and panel | Server health, latency, move accounts; "set up from Settings → Compute" (no tab by that name; it is "Servers and data"). | `lib/portfolio/ServersStrip.svelte`, `lib/portfolio/panels/NodesPanel.svelte:3-6,135` | Yes, by nature (ruling 140: the node's natural home) |
| Portfolio, **kill switch** grid | Pods down the side, servers across. | `lib/portfolio/KillMatrix.svelte:3-5,37-43` | Yes (needs a "this PC" column) |
| Mini apps | "Runs on: This laptop" or "Its own box on this laptop" (display only, no picker). | `lib/apps/apps.svelte.ts:220,255,330,446,550,816` | No |
| Copilot, **work area** | Each job shows where it runs; the comment says "Jobs run on servers, so they carry on when QMX or this laptop closes". | `lib/copilot/WorkArea.svelte:4-8,79` | Yes |
| Copilot, **How do I** | "running on your servers when QMX is closed". | `lib/copilot/HowDoI.svelte:40` | Yes |
| Library item page | No storage choice; a unit's page says "Runs headless on the server". | `lib/library/items.ts:345` | Yes |

Missing screens, which rulings 141 to 145 need: where his data folder is and how to move it; where the local backup goes (another drive) and when it last ran; per-workflow "run on this PC / on a server" outside the Lab's New dialog; per-dataset "kept on this PC / also on a server or bucket"; the copilot's step-by-step "add a server" walk (ruling 145) has no entry point yet beyond the "Add machine" menu, which is the natural place for it.

## G. The ten most important gaps (new, beyond G1 to G12)

| # | Gap | Where | Recommendation |
|---|---|---|---|
| L1 | cTrader cannot be connected on a PC with no server | `H/venue_session.py:68,304-309,347` | The PC is the sign-in home when no server exists (read-only and demo); the home moves when he adds a trading server. Ruling 135's one-home rule stays. |
| L2 | The server's public IP is typed into code and every chat sends to it | `launch.py:404-414`, `E/telemetry.py:49`, `hindsight.py:63,227` | Off by default; the address comes from Settings; never a literal in code. |
| L3 | No local backup; the backup leaves out blobs, chats, transcripts and the run ledger | `C/backup.py:25-32,68-132` | A local folder on another drive is the default target and copies the whole home minus rebuildable caches; GitHub and buckets are extras. |
| L4 | The new host opens an empty Library beside his old `library.db` without a word | `C/library.py:65-74`; his real home today | Refuse to start, or offer the switch, when `library.db` exists and `library/` is empty. |
| L5 | Run zones and Hindsight's database live outside the home | `E/workers/zones.py:82-89`; `hindsight.py:82` and `~/.pg0` | Zones under `<home>/zones/`; pg0's data folder under `<home>/memory/hindsight/pg`. |
| L6 | Placement names are a fixed list with Contabo in it, down to a database check | `E/definition/validate.py:29`, `E/ledger/migrations.py:36,59`, `H/host.py:883`, `E/settings.py:134-138`, `T/run-on-a-machine/definition.json:24` | Placements are his list in Settings (`pc` built in, servers he adds); a migration drops the `CHECK`. |
| L7 | Market data does not open on a fresh PC: no seal means shut, no `[data] root` means fail, and months are stamped server-born | `H/host.py:907-923`; `download.py:228-234` (three templates); `H/market_data.py:106,495,953` | Land WU11; default the root to `<home>/market` for both the host and the templates; default `placement` and `born_on` to `pc`. |
| L8 | Backtests from a chat go nowhere | `QA/qmx-tools/src/qmx_tools/service.py:176-200,293-299` (no production binding) | The host binds a PC backtest door by default; the `qmb` machine is added capacity. |
| L9 | No single "where is my data" pointer; five defaults and a cwd-relative `./qmx-home` | `__main__.py:26`, `console.py:822`, `C/server.py:487`, `servers.py:43`, `broker/server.py:75`, `C/node.py:857,874,898` | One resolver (`QMX_HOME`, else a small pointer file the installer writes, else `~/.qmx`) used by every entry point; Settings shows it and can move it. |
| L10 | Program pieces sit in the data folder, and an older release cannot open a home a newer one touched | `environments/`, `plugins/`, `definitions/`, `bin/` under the home; `E/ledger/migrations.py:100-103` | Move rebuildable program pieces to a program cache; add a home format version file and a read-only open for older releases, so "a broken release never touches it" (ruling 141) holds both ways. |

Also worth backlogging (smaller): Docling and torch declared as optional extras with a cache folder for script children (`E/nodes/script.py:44-52`); the remote runner's `vps` defaults (`models.py:103,123-124`); the standalone Hub's `primary` default (`server.py:969`); the nested `<home>/.qmx/vault.key` (`vault.py:62-65`); a PC-side collector option; the UI's `localStorage` settings; the sweep dialog's `vps-fsn` default; the copilot work area's "jobs run on servers" text; the Portfolio's "Settings → Compute" pointer to a tab that does not exist.
