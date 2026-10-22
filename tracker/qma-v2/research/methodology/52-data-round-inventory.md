# 52 — Data round: what exists on the ground, seed by seed

Date: 2026-10-22. Read-only inventory. Nothing was changed, merged or committed; this file is the only write.

**How this was read.** Code is `origin/engine/base` at `8af1a1cd` (the 42 build PRs, PR 122, rebuild/base's fixes and the eight server PRs 156-163), read with `git show`, `git grep`, `git ls-tree`, `git log` and `git diff 6b16e461..8af1a1cd` (what changed since file 50). No checkout. Proof of what each PR showed comes from the build store `D:\QMX-worktrees\qma-ship\build\` (`review/*-check-*.md`, `BACKLOG.md`, `IDEAS.md`, `QUESTIONS-FOR-OPERATOR.md`, `review/RESUME-2026-10-22-server-run.md`). Disk facts were read on this PC today. The checklist is `51-data-round-seeds.md` sections 1-7. File 50 is the base and is not repeated; where 50 still holds, this file says so and cites it.

**A note on timing.** The deletion pass (old daemon, old runs, old host) is running right now on top of `8af1a1cd`. It removes the old agent daemon, which contains old "experiments" and "procedures" code. That code is not the Lab and nothing below counts it.

---

## 0. Plain-words summary

1. **Most of the plumbing exists, little of it carries real data.** The new Library store, its version control, the server-side copy of it, the remote run machinery and the monitoring are written and were proven in test runs, some of them on your Contabo server. But your own QMX home on this PC has never run the new system: it holds only the old Library file (110 KB of test junk), with no new Library folder, no engine folder and no logs folder (checked today).
2. **The old Library is still the one agents use.** Every chat save, search and read goes to the old Library file. Each save is copied into the new store as it happens, but the switch-over to the new store has not been done.
3. **There is still no market data, no downloader, no uploads.** Nothing changed here since file 50. The price-history code works in tests, the store is empty, nothing fetches from the internet, and there is no way to hand QMX a book, PDF or file.
4. **Version control is real, but only half reachable.** The new store does drafts, branches, three-way merges, full history, "who changed what", conflict records, "show me how it looked on Tuesday", and claims so two agents don't do the same job. Workflows and chat-session records use it. Chat agents saving notes, strategies or files do not: they go through the old Library, which only keeps numbered copies. Files agents edit on disk are not versioned at all.
5. **The server connection works in tests, not yet in daily use.** A workflow can run some steps on the server and some on the PC, server runs show up on the PC, a dead machine's run can be taken over by another, and keys reach remote runs in sealed form. But the running app never actually syncs its Library with the server copy; that only happens in test scripts. And a remote step cannot reach market data or the backtester, because neither has a door.
6. **Trading nodes cannot talk to your PC at all.** The node code only listens on its own machine.
7. **Monitoring exists for workflows, chats and mini apps,** plus the PC-to-server view. There is no monitoring for the Lab (it does not exist), the Library on the PC, or a trading node. An outside agent like Claude Code can reach QMX only through a local door that needs a secret token from the Windows vault, and that token gives full control, not read-only access. There is no single log store and nothing leaves the PC except remote-run records.
8. **Mini apps are half plugins.** A published bundle can become a Claude plugin with skills, helper agents and commands; that was proven in tests. But nothing turns a published app into a plugin in the running app, an app's own tools never reach a chat, and an app's outputs never reach the Library.
9. **The Lab has no code of its own.** What exists underneath it is the workflow engine (drafts, test runs, "run just this part" with saved results), about a dozen Lab-style templates that wait for a backtester door, and chat references that can point at an old run. There is no Lab service, no notebook, no graph-and-code editor and no Lab copilot tools.
10. **The memory engine fits the server.** It was ruled "does not fit" against an invented 2 GB line. The server has 11,960 MB of RAM, 11,340 MB free when idle; the memory engine's peak was 2,687 to 2,799 MB, leaving about 8.5 GB. Several other sizing numbers on the server are invented too (section 3).
11. **Disk on this PC is nearly full:** about 12 GB free on C: and 8 GB on D:. ML training on the PC "with the data there" needs a plan for space first.

Counts over the 64 rows in section 1: **16 built, 34 partial, 3 designed only, 11 missing.**

---

## 1. Seed → status → evidence → gap

Status words: **BUILT** (code exists and a PR proved it), **PARTIAL** (some code exists; the stated part is missing), **DESIGNED** (a decision exists, no code), **MISSING** (neither). Paths are in `8af1a1cd` unless they start with a drive letter. `PKG/` means `qmx-agents/packages/`.

### 1. The Library takes in all data

| # | Seed | Status | Evidence | Gap |
|---|---|---|---|---|
| 1 | One central home; QMF's data role, QMB's results and the five Libraries fold into it | PARTIAL | New store `PKG/qmx-library/src/qmx_library/store.py` (content-addressed objects and blobs, ref log, edges, FTS5 catalog). Importers for the old Library, the registry, apps and the bucket in `migrate/` (LIBM PR 135, LIB4 PR 157). Host attaches the dual write: `PKG/qmx-host/src/qmx_host/host.py:489-490` `control.attach_library_mirror(DualWrite(store))` | The old Library file is still the truth: `library_save/search/get/versions/link` in `PKG/qmx-control/src/qmx_control/service.py:643-659` read and write `library.db`. Cut-over not done; the nightly comparison template `migrate/lib-dual-run-diff/` has no trigger. Mini-app outputs (`artifacts.db`) and QMB results still land elsewhere. By design market data stays out of the Library (Library AD-10; see extra finding E1). Who still writes each old store: section 2 |
| 2 | QMB asks the source for data; it holds none | PARTIAL | QMB never fetches (`qmb/src/qmb/data/policy.py`), reads by fingerprint (file 50 §4) | It reads a local folder path, not a service; keeps its own result files and run ledger (`qmb/src/qmb/results/`, `orchestrator/ledger.py`); no market-data service exists |
| 3 | Historical data for any instrument (FX, CFDs, metals, indices, futures, crypto) | PARTIAL | QMF instrument identity is an opaque `(venue, symbol)` pair (`packages/qmf-core/src/qmf/core/identity.py:269`), so any symbol fits. Store, splits, seal, Dukascopy decoder in `packages/qmf-data/src/qmf/data/`. Swap financing in `qmb/src/qmb/execution/financing.py` | No fetcher anywhere (unchanged since 50 §2.1); the store on this PC does not exist; no futures expiry or roll model found in QMB; Dukascopy decoder only |
| 4 | Sources beyond Dukascopy, e.g. CCXT for crypto | PARTIAL | `PKG/qmx-broker/src/qmx_broker/adapters.py` reads bars from cTrader or any ccxt exchange, at most 1,000 per call | Bars are handed to the chat and forgotten; no history download, no storage, no dataset card |
| 5 | His uploads (books, PDFs, files) | MISSING | The store can hold any bytes: kinds `artifact`, `source`, `note` have binary or text slots (`kinds/*.schema.json`) | No upload route (REST routes: `qmx_control/server.py:135-186`; no multipart anywhere in new packages). No PDF-to-text. `@file`/`@folder`/`@url`/`@youtube` references are refused "arrives with REF2" (`qmx_control/context.py`) |
| 6 | What agents gather (pages, YouTube transcripts, research) | PARTIAL | Kind `source` (url, fetched_date, transcript, content). The video template `templates/a-fill-the-library/` stores its files as `run-file` artifacts at run end (`qmx_engine/trace_export.py`) | Nothing writes a `source` object (no caller found). Chat finds are kept only if the agent calls `library_save` (old Library). No Whisper, no logged-in sources |
| 7 | Workflow outputs | BUILT | `qmx_engine/trace_export.py`: a `workflow-run` object, a `trace` artifact and every listed file as an artifact, linked `produced-by`/`run-of`; passed runs land on `main` by the standing rule (`qmx_library/landing.py`). LIB1 PR 131 lane 2 proved it through the host | Lives only in the new store, which his real home does not have yet. The engine run on its own still uses a private fake Library (`ports/library_fake.py`) |
| 8 | Lab outputs | MISSING | No Lab package (no `qmx_lab` in `PKG/`) | Everything; see rows 53-63 |
| 9 | Mini-app outputs | PARTIAL | The sink exists: `PKG/qmx-apps/src/qmx_apps/artifacts.py:67` `LibrarySink`, `supervisor.py:250` `attach_library`; APP2a PR 146 lane 3 landed an output in a test | `ControlService.app_runtime()` builds the supervisor with no sink (`service.py:1243-1270`), so in the running app outputs stay in `artifacts.db` (BACKLOG APP2a line 183) |
| 10 | Pod outputs | DESIGNED | Kinds `pod`, `pod-block` exist as schemas; Lab AD-10, AD-11 | No pod code. 51 says not to build on pods |
| 11 | Artifacts: units and bots | PARTIAL | Kinds `bot` (with `logic.py` and `card.json` blobs), `unit`, `strategy`, `book`, `bms`, `binding`; registry importer `migrate/from_registry.py` | Nothing writes them; no real bot exists anywhere (50 §1.4); the unit is still a design in the risk session; mirror-or-replace of the registry is open (Library OPEN-2) |
| 12 | Indicators and indicator combinations | PARTIAL | `packages/qmf-indicators` (TA-Lib wrapped, batch and streaming); kind `component` (Python code); template `bc-build-a-component` | No indicator kind or combination kind; the template is a draft waiting on the sandbox; indicators made by agents have no home or lineage |
| 13 | Reports | PARTIAL | Workflow reports land as artifacts (row 7) | QMB result files never reach the Library; agent backtests would save kind `backtest` in the old Library; three result shapes (50 §3.3) |
| 14 | Logs and observability as data | PARTIAL | `workflow-run` kind has `trace`, `logs/*`, `transcripts/*` slots; the trace is exported; the Hub writes its own health as a `test-report` on `refs/hub/health` (`PKG/qmx-hub/src/qmx_hub/server.py` header) | Host, chat, app and heartbeat logs stay as files under the home (section 4 rows) |
| 15 | Computer-use and browser outputs (screenshots, recordings) | MISSING | No browser or computer-use code in the new packages (only two template scripts mention screenshots) | Everything; engine AD-44 and AD-33 are designs |
| 16 | Trade journals | MISSING | Template `t7-trade-journal-review` exists and says it "waits for the trading node"; QMF has decision journals for the node (`qmf/data/journal.py`, `logbooks.py`) | No journal kind, no entry path for his own trades, schema not settled, no node running |
| 17 | News | PARTIAL | One free calendar feed, three fetchers (scheduled task, node recorder, `t3-news-calendar-watch`), unchanged since 50 §2.2 | No headlines, no actuals, nothing stores into the Library except the template's daily strip |
| 18 | Historical-data journeys: copilot quick idea, Lab experiment, backtest, ML on his PC | MISSING | Agent data tools exist as rows (`qmx_control/catalog.py` `DOMAIN_ROWS`) | Every one returns nothing: the harness still builds `DomainContext(root=home.root)` with no store (`PKG/qma-harness/src/qma/harness/harness.py:403`); QMB's agent door is still "scaffolded, not shipped" (`qmb/src/qmb/doors/mcp/__init__.py`) |
| 19 | Data hygiene: agents must not duplicate | PARTIAL | Same bytes give the same id (`store.py` `fp1`, `_write_once`); "already built" lookup `find_by_intent`; claims (row 31) | Engine never calls claims; market-data fingerprints include the window, so two copies of one day differ (50 §2.1); three news fetchers; two dataset lists (`datasets.json` vs `dataset` cards) |
| 20 | Data quality | PARTIAL | `qmf/data/verify.py`, `qmb/src/qmb/data/verify.py`, `gap_check.py`; Library schema checks on every put; quarantine marks flow downstream (LIB2 PR 136) | Nothing runs on real data; no freshness or disk alerts |
| 21 | Storage (where bytes live) | PARTIAL | Store roles writer, replica, cache (`store.py` `StoreRole`); Hub; replication `PKG/qmx-hub/src/qmx_hub/replicate.py`; bucket importer `migrate/from_bucket.py`; `qmx node setup` flips `[library] primary = server` (LIB4 lane 3) | Replication `sync()` is called only by lane scripts (`scripts/live/server/*.py`), never by the host; the host always opens a local writer (`host.py:489`). The home's weekly backup lists `library.db` but not the new store folder (`qmx_control/backup.py`). No market-data backup |
| 22 | In-sample, out-of-sample, holdout | PARTIAL | Splits and the 12-month seal (`qmf/data/splits.py`, `seal.py`); optimisation scores train and records test (`qmb/src/qmb/optimize/splits.py`); walk-forward | The seal applies only when a caller passes it; the agent tool path opens the store without it (50 §4.2); no change since |
| 23 | Synthetic data | PARTIAL | `qmb/src/qmb/data/generate.py`: four generators (block bootstrap, gaussian resample, gaussian noise, GBM), `scenarios.py` | Forex-CFD only; no agent or workflow route; nothing generated |
| 24 | Lineage: family tree for strategies, indicators, units | PARTIAL | Every object carries `parents`; closed relation list includes `variant-of`, `derived-from`, `branches-from`, `merged-from` (`port.py` `RELATIONS`); `walk` and `as_of`; workflows get a real `variant-of` (`qmx_engine/service/drafts.py`); QML has strategy families (`qml/src/qml/conformance/layer1.py`) | Nothing writes lineage for strategies, indicators or units; QML families are not mirrored into the Library |
| 25 | Storage stack: graph, relational, or both (Neo4j) | BUILT | Files plus one SQLite catalog with a relations table and FTS5 (`qmx_library/fts.py`), graph walk in code (`store.py` `walk`), parse-first search with graph citations (`search.py`, LIB3 PR 139) | It is "both" in one SQLite file today; no Neo4j. Whether that holds at real volume is unmeasured: search was tuned on about 20 objects (BACKLOG LIB3 line 147) |

### 2. Version control for everything agents touch

| # | Seed | Status | Evidence | Gap |
|---|---|---|---|---|
| 26 | Drafts and branches | BUILT | Ref spaces `refs/drafts/<item>`, `refs/agents/<session>/<item>`, `refs/runs/<run>`, `refs/variants/<item>`, `refs/sessions/...` with owners (`qmx_library/principal.py` `may_advance`); `Store.branch`; working copies `checkout`/`commit` (Library AD-20) | Used by workflow drafts (engine adapter `adapter.py`) and chat session records (`qmx_host/sessions.py:447`). No chat tool lets an agent branch a note, strategy or bot |
| 27 | Merges | BUILT | Three-way merge with `merged-from` to both sides, fast-forward, `ff-only` (`store.py` `merge`, `_three_way`). LIB1 lane 3: "the draft holds both edits after a fast-forward and a three-way merge" | Merge of two blob edits picks one side (LIB1 lows) |
| 28 | History | BUILT | Append-only `refs/log.jsonl`; `Store.history`; `as_of` on resolve/get/search/walk (LIB2 lane "asof") | The `library_versions` door reads the old Library |
| 29 | Who changed what | BUILT | Every ref move records its principal (`operator`, `agent:<id>`, `run:<id>`, `engine:<store>`, `hub`, `migrator`); a write on another's ref is refused (LIB1 lane 3) | Same exposure gap as row 26 |
| 30 | Conflicts | PARTIAL | A failed merge writes a `merge-conflict` object (`kinds/merge-conflict.schema.json`), `Store.resolve` | No door shows or resolves a conflict for an agent or for him |
| 31 | Claims (don't do the same work twice) | PARTIAL | `Store.claim/release/renew_claims` compare-and-swap; Hub `claims.py`; renewed by heartbeat; LIB4 lane 2 across PC and Contabo: "exactly one claimed, the loser linked and built nothing" | Nothing in the engine or the chat tools calls `claim` (no caller under `PKG/qmx-engine/src`); only lane scripts do |
| 32 | Several agents and he edit the same thing at once | PARTIAL | Per-agent refs merged into the draft are proven for workflows (LIB1, BUG2) | Chat agents save through `library_save` into the old Library, which keeps numbered versions by root id with no branch, owner or merge |
| 33 | Files and code agents edit on disk | PARTIAL | Workflow attempts write to their own overlay and commit declared files only (`qmx_engine/workers/zones.py`, engine AD-51); chats can rewind CLI file checkpoints (`qma/harness/chat.py:538-581`) | Engine AD-49 (a git worktree per concurrent writer) is not built: a helper gets a separate folder, "a git worktree is AD-49 and arrives with the Library" (`qma/harness/delegate.py:856-858`) |

**What he thought was built.** The store-level version control is built and proven. What is missing is the door: chat agents never touch it except through workflow drafts and session records.

### 3. Everything off his machine connects back

| # | Seed | Status | Evidence | Gap |
|---|---|---|---|---|
| 34 | A workflow step on the server reaches the Library Hub | PARTIAL | Hub server (`qmx_hub/server.py`: `/v1/op/<verb>`, `/v1/blob`, events, heartbeat, journals), client (`qmx_library/client.py`), LIB4 lanes on Contabo (save on the Hub read back, purge on every copy) | The running host never talks to the Hub for Library data: `HubClient` is imported only by `scripts/live/server/*`; `hub_link` is used only for heartbeats (`host.py:658`). One writer per store root means a Hub and an engine on one machine must share a process, not built (BACKLOG TRG2b line 237). The Hub routes `runs/<run_id>/` the sidecar ships to do not exist, so remote telemetry stays local (REM verdict) |
| 35 | Run passes | BUILT | `PKG/qmx-router/src/qmx_router/passes.py`: signed pass per run, deadline, revocation list; RTRP PR 158 lane E25 "10 checks, 0 failed", verify median 0.019 ms | The harness `cli_spawn` does not hand the pass to a child yet (RTRP backlog) |
| 36 | Credentials on remote machines | BUILT | Sealed vault `qmx_router/vault.py` (X25519 + AES-256-GCM, broker names refused); lane E26 "cached keys answer with the vault stopped"; facts and leases shared across two hosts (E53) | GPT half not run (no sign-in) |
| 37 | One workflow partly on the server, partly on the PC | BUILT | Remote worker `qmx_engine/workers/remote.py` and sidecar `PKG/qmx-remote/src/qmx_remote/sidecar.py`; REM PR 159: "5 of 5 one-node CPU jobs ran on Contabo", E13 "placed attempt's events landed in the home ledger", E27 "4 of 6 agent nodes run and 2 wait placement" | `runner.py` never sets a job's placement; the adapter reads `runs_on` from the definition as a workaround (REM verdict) |
| 38 | A remote step running QMB with market data and the Library | MISSING | — | No data reference in a run bundle (`qmx_remote/models.py` `RunBundle`), no `data_scope` on the pass (designed in Library AD-12, absent in `passes.py`), no market-data service, no QMB door, no QMB machine |
| 39 | Server runs seen and recovered on the PC; triggers across machines | BUILT | OPS2 PR 162 (provider 401 on Contabo reaches the PC inbox, one pause flag on both hosts, "server unreachable since"); ADOPT PR 163 (another machine adopts a run whose home died); TRG2b PR 160 (event triggers from the Library ref log, 52 s p95 across machines) | OPS2's lanes ran two homes on the PC over loopback, not across the tailnet (QUESTIONS file). Mirrored journals are Hub files, not Library objects (BACKLOG ADOPT line 250) |
| 40 | Trading nodes connect back (journals, results, kill-switch signals, fast sync) | MISSING | Node doors listen on localhost HTTP and a Unix socket (`qmn/src/qmn/doors/`); an outbound alive-ping exists in `qmn/src/qmn/observability/` but never ran | Unchanged since 50 §6: no path from any node to the PC; the agent `node.state` tool needs the node in the same process |
| 41 | What a trading node needs versus a workflow worker | DESIGNED | Older node docs (liveness heartbeat, DEC-0262), 50 §6.2-6.3; the server worker role exists as `qmx_host` role `node` (`host.py:478-483`) | Not designed against today's pass, vault and Hub. "Node" names both the worker and the trading node |

### 4. A DevOps layer at every level

| # | Seed | Status | Evidence | Gap |
|---|---|---|---|---|
| 42 | Workflows | BUILT | Spans, traces, `runs_explain`, `ops_spans`, inbox, trigger incidents with masked signatures (`qmx_engine/ledger/inbox_table.py`) | — |
| 43 | Agents and chats | BUILT | Chat journal, slot table, `ops_heartbeats` tool (`catalog.py` `HOST_ROWS`); OPS1 PR 134 | — |
| 44 | Mini apps | BUILT | App heartbeats, `apps_logs`, `apps_evidence`, app incidents (`inbox_table.py` `APP_INCIDENTS`) | — |
| 45 | The Lab | MISSING | No Lab | — |
| 46 | The Library | PARTIAL | Hub health objects and `qmx node verify` doctor (`qmx_control/node.py:156-208`); `qmx_library/status.py` | No heartbeat subject for the Library (subjects are host, run, app: `qmx_engine/heartbeat.py`); no replication-lag reading in the running app because replication doesn't run |
| 47 | Trading nodes | PARTIAL | Logs, metrics, alerts and alive-ping code plus Prometheus/Grafana/Loki planners (`qmn/src/qmn/observability/`, `qmn/deploy/observability/`) | Never deployed, never connected to the PC |
| 48 | One view across PC, server and node; logs leave the PC | PARTIAL | PC reads server heartbeats and forwarded reads (OPS2) | Logs in about ten places (50 §2.7); no central log store; no OTLP anywhere in new packages (Library AD-13 designs it) |
| 49 | An outside agent (Claude Code) can observe QMX and say what is wrong | PARTIAL | HTTP MCP and REST on `127.0.0.1`, behind a bearer token kept in the Windows vault (`qmx_control/server.py` `local_token`, `create_mcp`, `BearerGate`); log files are plain files under the home | No setup flow for an outside agent; the token gives every row including manage rows, no read-only observer token; the heartbeat and journal tools are harness rows, not on `/mcp`; nothing reachable from outside the PC |

### 5. Mini apps as plugins, stored in the Library

| # | Seed | Status | Evidence | Gap |
|---|---|---|---|---|
| 50 | Mini apps are Claude plugins (agents, MCP tools, skills) | PARTIAL | `PKG/qma-harness/src/qma/harness/packs.py`: a published `bundle.tar` becomes a plugin view with skills, agents and commands; PACK PR 144 lanes loaded a pack's skill, agent and command mid-chat | `materialise` is called by nothing in the running app (BACKLOG PACK line 171); an app's own tools (`app:<id>` rows) are not bound by `qma/harness/tools.py:498-515` (BACKLOG APP2a line 182); pack hooks and MCP servers are excluded on purpose |
| 51 | Mini apps live in the Library | PARTIAL | Kind `mini-app` (`bundle.tar`) and `mini-app-instance`; importer `migrate/from_apps.py` | Apps are kept in the app store's own definition folders; `apps_publish` (`service.py:1112-1122`) never writes a Library object |
| 52 | A mini app moves between machines | BUILT | APP2b PR 161: lease handed PC to Contabo, 100 MB blob identical on both, state intact, a step waits `placement` and resumes | The bundle came from the PC's definitions folder, not the Library (BACKLOG APP2b line 244) |

### 6. The Lab

| # | Seed | Status | Evidence | Gap |
|---|---|---|---|---|
| 53 | A Lab backend (service, document kinds, node pack) | MISSING | Designed: `architecture/lab-and-pods/` Lab AD-1 to AD-18 | No `qmx_lab`; the old daemon's experiments and procedures are being deleted and were never the Lab |
| 54 | Editor: graph and code of one draft | PARTIAL | Workflow drafts, validate, test, versions, archive (`workflows_*` rows in `service.py`; `qmx_engine/service/drafts.py`, `tests.py`, `versions.py`) | No graph or code projection, no bot-code drafts, no round-trip check (Lab AD-2) |
| 55 | "Create new" like VS Code; levels and templates | PARTIAL | 37 engine templates (`qmx_engine/templates/catalog.py`), install, "crystallise a workflow" | No new-project flow, no levels, no Lab document kinds |
| 56 | Notebooks | MISSING | Designed: Lab AD-9 `KernelPort` | Everything |
| 57 | Procedures: backtest, sweep, walk-forward, robustness, training | PARTIAL | The work exists inside QMB (`qmb/src/qmb/optimize/`, `robustness/`, `sweep/`); templates `l1-idea-to-first-result`, `l4-overnight-lab-loop`, `d3-iterate-against-qmb`, `d4-variant-comparison`, `d6-ml-training-run`, `b-build-and-prove`, `rs3-source-to-lab-test` | Each says it waits for QMB's door or the sandbox; none can run |
| 58 | Run just this part; skip what is fresh | BUILT | Memo of finished nodes (`qmx_engine/ledger/memo.py`), selected-subgraph test runs (`service/tests.py`) | Applies to workflows only |
| 59 | Pull Tuesday's results into today's run | PARTIAL | A chat can attach `@run`, `@library`, `@session`, `@memory` (REF1; `qmx_control/context.py`), and read the store as it stood at a time (`as_of`) | A workflow cannot: the engine's `library` node kind is registered but not available (`qmx_engine/definition/registry.py:94`), and nothing resolves `@` references in workflow inputs. QMB results are not in the Library to pull |
| 60 | Run results across a strategy hypothesis | PARTIAL | Kind `hypothesis` whose status is computed from results linked `tests` (LIB2) | No runner that takes a hypothesis and fans out experiments |
| 61 | The copilot reaches all of it | PARTIAL | Context references, memory, `library_mark` | The Lab copilot's 17 tools do not exist; the copilot's Library search reads the old Library, so the new search never answers it (BACKLOG LIB3 line 146) |
| 62 | Pods | DESIGNED | Lab AD-10 to AD-12; kinds `pod`, `pod-block` | No code; 51 says don't build on pods |
| 63 | ML on his PC first (Quadro T1000, 4 GB), data there | MISSING | MIS training pipeline inside the node package (about 8,700 lines, 50 §6.1); `d6-ml-training-run` template (waits) | No market data on the PC; C: 12 GB free and D: 8.3 GB free (read today); no placement row or recipe for local GPU training |

### 7. The memory engine (Hindsight) on the server

| # | Seed | Status | Evidence | Gap |
|---|---|---|---|---|
| 64 | Real numbers, not the invented 2 GB line | BUILT (measured) | PRB-S PR 156, `scripts/probes/server/FINDINGS.md`: Contabo 11,960 MB RAM, 193 GB disk; free 11,340 MB idle; Hindsight peak resident 2,687-2,799 MB; free RAM dropped only 1,601 MB at rest; recall quality identical to the PC | The verdict "does not fit" is against the plan's invented 2,048 MB line. On real numbers about 8.5 GB stays free with Hindsight running. The capacity math also uses invented figures: `overhead_mb` 6,144 reserved for services that mostly do not exist yet (market-data service, monitoring), `session_mb` 1,536, `ram_budget_mb` 12,288 (above the real 11,960), `attempt_memory_mb` 2,048 (`qmx_engine/settings.py:146-150`; SOLUTION-DESIGN line 975). Measured, the box idles at about 620 MB used |

---

## 2. The five old Libraries: who still writes to them

| Store | Written by today | Read by |
|---|---|---|
| Old Library `~/.qmx/library.db` + `artifacts/` | Every `library_save` and `library_link` (chat tools, REST, HTTP MCP), the memo save, large tool answers (50 §2.6); a test leak wrote 11-14 junk items into his real one (BACKLOG line 141) | Every agent and REST Library read, the eval-task list |
| New store `<home>/library/` | The dual-write mirror of every old-Library save, all workflow outputs, chat session records, memory rows | Context references, memory, marks, the engine; not yet the copilot's search. Absent from his real home |
| Engine fake `~/.qmx/engine/library-fake.sqlite` | The engine when it runs without the host | Same |
| Mini-app outputs `~/.qmx/artifacts.db` | Every app landing (no Library sink in the running app) | Apps' consumers; the importer |
| QMB's registry view and the QMF registry room | Nothing (no registry data on the PC) | QMB, QML, the node |

## 3. Things the seeds did not mention that the data round must handle

1. **Market data and the Library point opposite ways.** The seed says everything data-related moves into the Library. The design keeps ticks and bars out of it and cites them by `dataset` cards (Library AD-10, spine "Deferred" row). Nothing writes a dataset card today, and the agent tools keep a separate `datasets.json`. This needs a decision, not a default.
2. **Nothing has run on his real home.** `~/.qmx` holds `control.db`, `library.db` (110 KB), `runs.db` and one artifact folder; no `library/`, `engine/` or `logs/` folders. Every "BUILT" above was proven in test homes or on Contabo scratch folders.
3. **The server sync is proven but not switched on.** Replication runs only in lane scripts, and one writer per store root forbids a separate Hub and engine on the server. The cut-over needs a host-side sync loop and a Hub-backed Library port.
4. **Size limits on bytes.** The Hub takes one request body of at most 64 MB (`qmx_hub/server.py:66`) with no chunking, and blobs are read whole into memory. Books, videos, recordings, model weights and datasets over that size cannot travel. Search indexes only the first 1 MB of text per blob (`store.py` `TEXT_LIMIT`), and PDFs are never turned into text.
5. **The PC is nearly full.** C: 97 % used (12 GB free), D: 95 % (8.3 GB free). The 10 GB of old ticks sit on C:; a 715 MB test memory database sits on C: (QUESTIONS file). The design lets the PC drop a blob only after two verified remote copies, which needs the sync that is not running.
6. **Invented numbers besides the 2 GB line:** the server's 6,144 MB overhead, 1,536 MB per session, 12,288 MB budget, 2,048 MB per attempt, the 2 GiB sync-back cap (SOLUTION-DESIGN), the Hub's 64 MB body, the 1 MB search text, the broker's 1,000-bar read. Each should come from the real machines or be removed.
7. **A workflow step cannot read or write the Library mid-run.** The `library` node kind is not available; only run-end export writes, and scripts read files. Most data journeys need this step.
8. **The holdout lock is still optional**, and the agent path still skips it (50 §4.2). Any door built in this round must apply it on the serving side.
9. **The copilot's tools are still empty for data, backtests, bots and the node** (row 18); filling them at start-up is the same gap as in 50 §5.
10. **Kinds missing from the roster** for the seeds' inputs: no trade journal, indicator, news item, screenshot or recording, upload or document kind (some could reuse `source` or `artifact`; the roster is 38 schema files, 4 retired). Four retired kinds still parse (`board`, `bot-card`, `logic`, `template`).
11. **Backups don't cover the new store.** The weekly snapshot lists `library.db` but not `<home>/library/` (`qmx_control/backup.py`; BACKLOG LIB1 line 99); market data has no backup at all.
12. **Concise answers.** A default Library search page is about 46,000 characters and spills (BACKLOG CAT lines 79-80); with real data volume this gets worse.
13. **Two "nodes".** The host's `node` role is a server worker; the trading node is another program. The round should name them apart before designing connections.
14. **The deletion pass is live** on `8af1a1cd` and removes the old daemon and old run paths; any data design should start from its result, not from today's tree.
