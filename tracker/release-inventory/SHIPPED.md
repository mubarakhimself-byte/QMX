# What QMX can do now

By area, in plain words. "Now" means the code on `origin/engine/base` at `3ae41ffc` (2026-11-08). Paths are on that branch. Short names used below:

- `pk/` = `qmx-agents/packages/`
- `apps/` = `qmx-agents/apps/`

**How sure.** Each line says how it is known. **git** = proved by a merged PR in `MERGED-PRS.md`. **code** = the file or folder was read on `engine/base` in this pass. **PR** = read in the PR body on GitHub. **doc** = read in a plan or handoff. Nothing here was run.

## Three things true of every area

1. **No screen talks to any of it.** The UI on `engine/base` is the 2026-10-01 baseline (`apps/qmx-ui`). There is no desktop shell (no Tauri or Electron in the repo). Everything below is reached through the copilot, a REST route on the host, a workflow, or a command line. (code)
2. **Nothing has run on his real folder or a real broker account.** The first real start and the demo proofs wait for his one cTrader demo sign-in. (PR #328, #352)
3. **Risk and sizing are placeholders.** The real risk core is open PRs #353-#369 and is not shipped. A unit trades with placeholder sizing and exits. (gh, doc `tracker/risk-sizing/build/RISK-SIZING-PLACEHOLDERS.md`)

---

## 1. The host (one program for everything)

- One program, `python -m qmx_host serve`, runs the copilot's chats, the workflow engine, the Library and the app supervisor on one port, behind one bearer. Roles: `pc`, `node`, `server`. Also `start`, `status`, `stop` and `backup`. (git #119, code `pk/qmx-host/src/qmx_host/__main__.py`)
- It gives exit codes meant for a desktop app, for example 3 when a first start is due. (code, same file)
- REST routes for chats, sessions, approvals, usage, the doctor, inbox, runs, workflows, triggers, apps, backups, connect, first start, data and settings. The routes come from the harness router (`pk/qma-harness/src/qma/harness/routes.py`), the engine router (`pk/qmx-engine/src/qmx_engine/service/rest.py`), the host's own routers (`backups.py`, `connect.py`, `first_start.py`, `market_data.py`, `promote.py`, `door.py`), and catalog rows with a REST form (`pk/qmx-control/src/qmx_control/catalog.py`). (code)
- The doctor page (`GET /api/doctor`) shows health lines: disk and memory floors (#179), clock (#247), store versions (#213), and what did not open (#222). (git, code)
- Places: This PC is always `pc`. Servers are places he names (#212). Each run records where it ran. No server is in the defaults (#208). (git)
- Security: secrets are redacted at one seam (#118). Each host has its own pass key (#326). The vault is owner-only on every machine (#316). App manifests may not ask for the host's own secrets (#313). Agents are kept out of every grants folder (#312). (git)

## 2. Installs and first start

- **First start card**, before any QMX folder exists: new folder, open a folder, restore from a copy, or bring in old data. Routes `/api/first-start/*`, CLI `first-start`, `new`, `open`, `bring-in`, `restore`. (git #209-#214, #219, #228, #234; code `pk/qmx-host/src/qmx_host/first_start.py`)
- **One QMX folder** with a fixed layout, found one way (#209, #210). Old data is brought in on first start, in the background, with a report that labels unproven test items (#214, #217, #219). (git)
- **Store versions**: a folder opens, upgrades after a backup, or refuses by name (#213). It syncs a copy before every upgrade (#234). (git, code)
- **On first start** the dummy unit lands in the Library as a draft (#256). The dictionary is ported in as a collection that waits for one publish click (#270). (git, PR)
- **Template install** runs as a job with progress (#223) into the real Library (#199). (git)
- **The first real start script** `tools/first_real_start.py` checks, one PASS or FAIL line per fact, that the node is ready for a unit on his real folder. It has never run on his folder. (git #328, #352; PR)
- **The foundation proof** `tools/proof_foundation.py` runs 18 named checks. Check 18 (a real chat and backtest) runs only with `QMX_TEST_LIVE=1`. (git #347; PR)
- **Release bundle**: `release/install.py` and `release/launcher.py` build and install a checksum-bound bundle. Its README calls it "a release candidate under verification" from the older era. Last touched 2026-11-02. Not checked against the new host. (code)
- **Not there:** a desktop app, a Windows installer, and a "getting started" list. (code: no matches)

## 3. Mini apps

- **The core:** a manifest (`app.toml`), a supervisor with a crash breaker and opt-in restart with back-off, operations, jobs, `provides` (what an app lands in the Library), app volumes, Docker on Linux. (git #37, #40, #144, #146, #161, #242; code `pk/qmx-apps/src/qmx_apps/`)
- Apps load as Claude plugins, so a chat gets their tools (#144, #198). (git)
- A workflow can tell an app's job what to do and read its answer (#236). One "lander" puts every job's result in the Library (#252). (git)
- Apps get the host's facts in their volume (#246) and a read-only market folder if they declare it (#244). A server reads an app's declared secrets from its vault (#264). (git)
- Installs pick up fresh source (#310, #318). A repair reaches QMB and the MIS at the next start; the node waits for his signature (#331). A stuck install stops after 30 minutes (#331). (git, PR)
- **First-party apps, all headless** (no screen of their own): QMB, the MIS, the trading node (`apps/qmb`, `apps/mis`, `apps/trading-node`). (code)
- **Example apps:** `examples/apps/` exchange-status, macro-daily-bias, mql5-articles, weekend-watcher. Every example and first-party app starts and answers, tested in CI (#304). (code, git)

## 4. Workflows and templates

- **The engine:** the `qmx.workflow/1` format, validate and lint, a run ledger, replay from any node, fan-out by chunk, join, loop, wait, subworkflows, graders, monitors, the failure ladder, a watchdog and inbox items. (git #96-#107; code `pk/qmx-engine/src/qmx_engine/`)
- Drafts, tests, versions, runs and "explain" over REST (#102). Every resumed run lands (#218). A live run takes inputs from REST or its trigger (#220). (git)
- **Triggers:** cron, interval, events from the Library ref log, webhooks, market time, catch-up once, claims, priorities and one pause switch (#105, #133, #160, #162). Code `pk/qmx-engine/src/qmx_engine/triggers/`. (git, code)
- **Agent steps** run on any provider through the router, pause at plan limits, and can write only the file they were asked for (#103, #104, #243). A stuck detector stops loops (#115). (git)
- **Steps placed next to their data**, or on a server through the remote worker (#159, #197). Opt-in since LF5. (git)
- **About 55 template folders** in `pk/qmx-engine/src/qmx_engine/templates/`. Groups: research (`rs0`-`rs8`, `a-fill-the-library`, `clippings-into-research`), Lab (`l1`, `l4`, `d3`, `d4`, `d6`, `d9`), units (`b-build-and-prove`, `u1`-`u4`), slow lane and MIS (`s1`-`s5`), desk and review (`db-desk-brief`, `morning-digest`, `rv-weekly-review`, `t3`, `t4`, `t7`), risk and portfolio drafts (`rk2`, `rk5`, `rk8`, `p1`, `p2`, `dc`), data (`download-dukascopy`, `download-binance`, `download-ccxt`, `refresh-ccxt-records`, `feed`, `synthetic-data`), and others (`ask-the-panel`, `revolution-loop`, `crystallise-a-workflow`, `ev-copilot-eval-battery`, `connections-health`, `run-on-a-machine`). (code) Which ones run end to end today was not checked; the October handoff counted 22 runnable and 23 drafts before the unit build. (doc)
- The copilot builds, validates and test-runs a workflow from one sentence (#152). (git)

## 5. Units and QML

- **The unit document** `qmx.unit/1` with a parser and a generated schema (`qml/src/qml/unit/`, #239). (git, code)
- **Blocks** are loaded one way. There are 113 standard blocks in `qml/src/qml/blocks/stdlib/`: indicators, statistics as readings, markets beyond forex, exits and halts (#249, #273, #276, #279, #280). (git, code)
- **The checker** checks a unit at every layer and names every problem at once (`qml/src/qml/check/`, #253). It feeds problems back to the agent while it writes (#262). It refuses what QMX cannot run, naming the field (#332). (git, code)
- **Compile and run** a unit inside QML; it tunes one of its own numbers from its own trades, with a receipt (#251, `qml/src/qml/compile`, `motion`). Behaviour is kept through restarts and upgrades (#255). (git, code)
- **Plain rules** such as "only enter when ADX is above 25" become working slots (#334). (git, PR)
- **Lifecycle:** one table decides "new version or new unit"; each unit has one lifecycle; nothing reaches paper or live without his click (#250, #337, `qml/src/qml/lifecycle`). (git)
- **Units in the Library:** a published unit has passed every check (#256). The copilot writes and checks a unit (#258) through the `unit` and `blocks` toolsets (`unit_new`, `unit_check`, `unit_explain`, `blocks_find`, `blocks_get`, `blocks_check`, `blocks_match`). (git, code `catalog.py`)
- **The dictionary** in its new form with doors (#266), 239 entries ported (#270), real status per page and no duplicate names (#337). Porter in `tools/dictionary/`. (git, code)
- **Every number has a measure and a market**, so a stop cannot mean ten times what was meant on another market (#248). (git)
- **The risk socket** has contract tests and a rip-out list for the risk session (#272). (git)

## 6. QMB backtests and the judge

- **QMB is the first mini app** (`apps/qmb`). Jobs: backtest, behaviour check, conformance, sweep, walk-forward, robustness, optimize, what-if, replay check. It lands `backtest-result` in the Library. (git #261, #289; code `apps/qmb/app.toml`)
- It trades from the Library's typed monthly price partitions and a JSON request (#240). It reads his contract facts (#333) and his downloaded data, and names a missing month before it starts (#335). Long history holds up and runs faster (#268, #338). (git)
- Fills, sizes, costs, carry and margin behave like a real market. A gap loss is not capped at 1R (#274). Futures replay contract by contract (#278). Gold is read at its own price scale (#315). (git)
- Results show money and R, drawdown, and how close each trade came to its stop. Costs say "not calibrated" (#339). The unit's journal is kept in every run (#267). (git, PR)
- **QMB versions:** a new version is proved before it becomes the default, and variants run side by side (#281). (git)
- **The judge** (`pk/qmx-judge/src/qmx_judge/`: `judge.py`, `tries.py`, `shrink.py`, `paper.py`, `presets.py`, `conformance.py`, `landing.py`) counts tries (#275). It cannot be talked round: a friendlier study is a counted try and no market can be dropped (#340). One true verdict and one paper per decision (#341). (git, code)
- The copilot runs backtests through the `backtest` toolset (`backtest_run`, `status`, `results`, `compare`, `judge_run`). (code `catalog.py`) The older agent-backtest path (WU4, PR #204) is **not merged**. (gh)

## 7. The trading node

- **A headless app** (`apps/trading-node`, version 0.1.14, risk "money") that serves `qmn.app` operations: status, units, positions, journal tail, passport, deployments, records, deploy, withdraw, pause, resume, kill, flatten, bind, sign-in, self-test, rotate keys and more. The runtime is the old node code in `qmn/src/qmn/`. (code `app.toml`, `server.py`)
- **Start it** on This PC from the connect dialog (#282, #288), or on a server with the same checked steps (#325). Reached from This PC through one host route and a node link (#277). (git)
- **Trades** the dummy unit against the conformance venue (#287). The cTrader demo venue is bound (#311). Hyperliquid through CCXT on testnet (#298). (git) None of it has traded on a real demo account. (PR)
- **Promote and deploy** only by his click: `POST /api/units/promote` answers only to his principal, builds the deployment from the Library and asks the node to deploy (#302, `pk/qmx-host/src/qmx_host/promote.py`). Only the markets he chose (#327). Fixed edge cases (#348). Deployed units really run (#349). (git, code)
- **Paper lane per unit** and a stand-down table (#293). Every paper trade reaches his Library (#342). (git)
- **Reconcile** with attribution, survive a network cut, and keep the position exact after partial fills (#292, #319). The broker wins after a cut (#343). Stops are encoded the way cTrader expects (#321). (git)
- **Heals itself** and keeps risk stops through restarts (#301). Status and kill tell the truth (#327). RED and flatten really close (#345). Back-off on a broken connection, "closed" over weekends (#351). (git)
- **Records come home** to This PC from servers (#300). This PC watches nodes without touching them (#306). The node reads the MIS board with a fallback (#309). (git)
- **Not built:** the live-account path (C-21), updating a server node at a safe moment (C-19), cutting the old node shell (C-20), and the demo attribution proof (C-15). (gh: no PR)

## 8. The MIS (market information)

- **A headless app** (`apps/mis`) with four operations: configure, status, round, board. It reads this machine's market store and publishes readings per market (change, efficiency, variance ratio, Hurst, spread state), each with its health and a freshness word. It never trades. (git #295; code `apps/mis/app.toml`; PR)
- It publishes by itself after a download, and keeps going when one read fails (#350). (git, PR)
- Agents read readings and instrument facts through the `readings` and `instrument` toolsets (#294). The reading blocks live in `packages/qmf-readings` (#271). (git, code)

## 9. The Library

- **One store** for everything: write-once objects, content-named blobs, an append-only ref log, edges and annotations, and a rebuildable search catalog. No delete, only archive. (git #131; code `pk/qmx-library/src/qmx_library/`)
- **49 kinds**, each a schema file in `qmx_library/kinds/`: unit, backtest-result, dataset, instrument, venue, account, trade, verdict, try, paper-run, hypothesis, source, note, session, workflow, workflow-run, mini-app, model, pod, pod-block, death-certificate and others. Every kind has a card and a page (#190). (code, git)
- Search is parse-first and ranks trusted results first, with a curator (#139). Marks travel upstream, ideas get a status, reads can be "as of a date" (#136). Branch, merge, history and blame for chat agents (#195). (git)
- Chat sessions are saved as Library items (#141). Context references with `@` (#143). Any file comes in through one streaming upload door, with text extracted (#193). (git)
- Price history is stored as typed monthly partitions with one card per series (#184), behind one market-data door (#185). The door is open by default and a holdout is his choice per study (#207, #335). Data routes are in `pk/qmx-host/src/qmx_host/market_data.py`. (git, code)
- The Library can live on a server with a Hub, claims and purge; the PC syncs selectively; a flip moves it on his click (#157, #180-#183, #202, #206). All opt-in since LF5. (git)
- Venue, instrument and account records are versioned facts (#257, #323). (git)

## 10. The copilot and agents

- **The harness** runs Claude Code chats: interactive, background and child chats, approvals (allow once, allow always, reject, answers), interrupt, rewind, model and effort switch with the cost warning, export, compaction per chat, the usage page with plan windows and the overage stop. (git #77-#90, #92, #121; code `pk/qma-harness/src/qma/harness/routes.py`)
- **The guard** replaced the old money gate (#125, #174). Promote is a host route, never a tool (`promote.py` docstring). In the catalog, `node_propose_order` only writes an unsigned proposal and always asks; "nothing in the catalog places, amends or cancels an order" (`catalog.py`). The exception is cTrader's own MCP, which lets agents act on **demo** accounts only (#324). (git, code)
- **The router** (`pk/qmx-router/`): providers as data, one row per model, routing by model id, an in-house chat-completions lane, the account pool, one error classifier, registry-made sub-agents, provider test from a chat, keyless providers skipped (#137-#149, #201, #203). A GPT lane on his ChatGPT plan (#89). An OpenCode Go profile ships (`qmx_router/profiles/opencode-go.toml`). (git, code)
- **The catalog**: one description per operation, shared by chats, workflows and REST. About 19 core toolsets: library, workflows, data, backtest, research, node, broker_read, apps_admin, memory, context, delegate, settings_read, ops, router, lab, unit, blocks, instrument, readings. (git #127, #132; code `catalog.py` `CORE_TOOLSETS`)
- **Delegate v2**: helpers return a handle at once and report back between turns (#151). (git)
- **Memory** on Hindsight with the built-in search as backup: recall, note, check, forget, rebuild (#153; code `pk/qmx-memory/`). (git, code)
- **Eval battery** tests the copilot like a workflow (#138). (git)
- **Broker reads** for agents: accounts, account state, positions, quotes, symbol info, bars. Every read says demo or live (#215). cTrader's own MCP for agents, demo accounts only (#324, `qma/harness/demo_only.py`). (git, code)
- **The Lab** has a backend workspace and trains models on the PC's GPU (#194; `lab` toolset). Pods are **not built**. (git, code)

## 11. Data, brokers and connections

- One registry of connections, each with a health word (#189). Feeds and downloaders run as scheduled workflows: Dukascopy, Binance, CCXT, the calendar (#191). (git)
- cTrader sign-in on This PC works with no server, says why a read failed, and refreshes an expired pair (#205, #211, #221). A demo row is refused on an exchange with no demo mode (#224). Contract markets, public trades and books through CCXT (#265). Calendars for every market (#263). (git)
- The old 10 GB of ticks were saved on the server with checksums and imported there (#173, #186). (git)
- **Not built:** cTrader through the server (DR5B, WU10). (doc, gh)

## 12. Backups and sync

- Copies on This PC and on a second drive, made by the host on its own; restore from the first-start card, the command line or Settings, with a drill (#225-#229). (git; code `pk/qmx-host/src/qmx_host/backups.py`, `pk/qmx-home/src/qmx_home/backup/`)
- What is saved is decided by class. Keys never travel; a restored folder lists "keys to fill" (#231, #234). (git)
- Connect a storage from one dialog; pack, compress and send copies through rclone with monthly upkeep (#230, #233). Sync before every update (#234). (git)

## 13. Alarms, logs and monitoring

- One heartbeat and one incident shape on the host. The `ops` toolset answers "what is running here and why is it slow" (#134). Server runs show on the PC, with one pause switch everywhere (#162). (git)
- **Phone alarms** through his ntfy topic, plus a Healthchecks.io liveness ping, set up from two connect-dialog cards (#303). They work on the installed node and say so when off (#346). Alarms follow the market calendar (#322). (git, PR; code `qmn/src/qmn/app/alarms.py`, `pk/qmx-host/src/qmx_host/connect_node.py`)
- **Deep logs:** events go to OpenObserve when telemetry names a target. It is off until he sets it (#192, #208, #260). App logs and incidents ship through the same switch (#260, `pk/qmx-host/src/qmx_host/app_logs.py`). (git, code)
- **Clocks:** every machine proves its clock against time.windows.com (#247, `pk/qmx-host/src/qmx_host/clock_probe.py`). A drifting clock stops entries on the node (#351). (git, code)

## 14. Where plans and code differ

| Plan said | Code shows | How known |
|---|---|---|
| The server is the Library's main copy (DATA-PLAN, 22-24 Oct) | No server in the defaults; This PC is home; servers are opt-in (LF5 #208, rulings 136-139) | git, doc |
| The price door keeps holdout months sealed (DR3B) | Open by default; a holdout is per study (#207, #335) | git |
| Agent backtests through QMB's door (WU4) | PR #204 still open; units backtest through the QMB app instead (#261) | gh |
| The first real start trades the dummy on his demo (C-14) | The script now only proves the node is ready, and nothing deploys until a unit passes the judge (#352) | git, PR |
| Unit plan: 91 sections | 87 built; C-15, C-19, C-20, C-21 never built | gh |
| UI-HANDOFF (28 Oct) lists screens for the October backend | Backend grew a lot since (unit build, repair); UI-HANDOFF was not updated after 28 Oct | doc, git |
| Risk core designed (plan/risk-core) | Not merged; the first template was rejected on 7 Nov; round 2 is open PRs #353-#369 | gh, doc |
