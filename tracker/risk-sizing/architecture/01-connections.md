# 01. Every connection between the parts, inside QMX and outside it

Written 2026-10-31 by agent A0 (its only writer). This is the master every part's contracts must match: who calls whom, where it runs, the data that crosses (named shapes and their owner), the direction, the version rule, and what happens when the other side is down. The rules behind it are the Level 0 spine (`level-0/ARCHITECTURE-SPINE.md`, cited as AD-n); the words are the glossary's (`funnel/versions/GLOSSARY.md`). A Level 1 spine that needs a connection changed proposes the change in its own "Contract changes" section; this file's writer folds it in.

**Labels.** EXISTS = merged on `origin/engine/base` `c93407ca` (path given or cited through the grounding file that checked it). NEW = to be built. CHECKED = read or run this session; INFERRED = judgement.

## How to read this

**The one rule over every row (AD-2).** A unit trades with only what is on its own machine. No row below that crosses machines may be needed for a unit to trade; the only cross-machine link on the order path is the trading node's own link to its venue.

**Where.** `in-process` (one Python process); `same machine` (two processes on one machine: a host and an app, or two apps); `cross-machine` (over the network between his machines); `external` (to a broker, exchange, data vendor or time source).

**Version rules.**

| Code | Rule |
| --- | --- |
| V-S | the shape carries `schema_version`; fields addable, meanings never change; readers read every version they support (AD-6) |
| V-K | a Library kind's schema file with `schema_version`; stores open, upgrade after a copy, or refuse by name (Library AD-3, AD-35) |
| V-P | the call is pinned to `(app, version)`; the pin is revalidated per call and never resolves to another version silently (engine AD-64) |
| V-CT | a CT contract format version; a reader refuses a version it does not know (fail closed); CT-23 format 3 is the unit's sized intent (AD-18) |
| V-H | both sides state their contract versions on connect; on a mismatch the node keeps trading what it has and refuses new deployments until they match (AD-6) |
| V-L | a pinned library or protocol descriptor (`ccxt` 4.5.85, cTrader `openapi-91.pb`); the venue's capabilities are re-verified at every connect and after any upgrade (CT-18) |

**Down.** What happens when the other side is down, slow or unreachable.

## 1. Where each part runs

| Part | This PC (profile `pc`) | A server in profile `trading` | A server in profile `server` |
| --- | --- | --- | --- |
| P0 host | yes | yes (no chats, no agent steps) | yes |
| P1 QML, P2 unit template | in every process that hosts units or checks them | inside the node app and the MIS instance (package data snapshot) | inside workflow steps |
| P3 judge | yes | no | inside workflow steps if he places them there |
| P4 records | the Library's kinds and refresh jobs | a snapshot inside the node app's volume | Library replica |
| P5 journals | the home of every journal (pulled) | written locally first | replica of what the PC holds, if he keeps copies there |
| P6 Library | primary | a cache fed at deploy time | server Library (hub) |
| P8 copilot and agents | yes | never | workflow agent steps only |
| P9 workflows | yes | no agent steps; the node's own scripts only | workflow worker |
| P11 QMB app | default instance | no | capacity he may add |
| P12 trading node app | practice instance (demo accounts) | live instance | never |
| P13 MIS app | PC instance (slow tier, cross-market, board, models in shadow) | node instance (that machine's markets) | no |
| P15 OpenObserve | home | collector with a disk queue (optional stand-in) | collector |

## 2. Inside one machine

| # | From | To | Where | What crosses (shape, owner) | Door | Dir | Version | Down |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | Copilot or workflow agent step | QML checker | in-process in the host | unit document `qmx.unit/1` (P2) in; check result (P1: errors and warnings as kind, where, message, hint; checker version; catalogue snapshot id) out | catalog row `unit_check` (NEW, core toolset) | ask | V-S | n/a (same process) |
| C2 | Any author (copilot, agent, script, shell, him) | Library | in-process in the host | unit document in; governed draft or a refusal with every problem out | Library save; the `unit` kind file names the QML checker (AD-29, NEW) | ask | V-K | n/a |
| C3 | Workflow script step | QML checker | in-process in the engine's script process (host Python has `qml` importable, G4b Q1) | as C1 | `import qml` inside the template's unit-check step (NEW) | ask | V-S | n/a |
| C4 | Core-plugin hook after a Library save or a unit file write | QML checker | a command the CLI runs (`python -m qmx_tools.unit_check`) | as C1, returned as `additionalContext` | `qmx-agents/plugin/hooks/hooks.json` (NEW, Should, after a probe) | ask | V-S | the hook times out (setting, default 8 s, under the guard's 10 s); the Library save still checks |
| C5 | Copilot or agent | QML door | in-process | words, roles, data level, class in; one-line catalogue index out; templates in, unit drafts out; unit in, card text out | rows `blocks_find`, `unit_new`, `unit_explain` (NEW) | ask | V-S | n/a |
| C6 | QML | catalogue snapshot; instrument records snapshot | in-process | blocks by `id@version` (P1); units of measure, data levels, calendars (P4) | QML package data; a snapshot file | read | V-S | a missing pinned block or record is a check error, never a guess |
| C7 | Copilot or agent | QMB app | same machine (host to app) | run request (unit `id@version`, markets, window, data recipe, cost profile, seed, purpose, study ref) in; run handle, then result id out | existing `backtest` rows (`CTL/catalog.py:284-317`) forwarding through the core landing (NEW binding) | ask | V-P, V-S | the call waits up to `qmb_tool_wait_s` (default 600 s), then returns the handle; the app's breaker logs a crash |
| C8 | Workflow | QMB app | same machine, or the app's home elsewhere | as C7, pinned to a version | `app_op {app: qmb, job: backtest, pin}` (EXISTS node kind; app NEW) | ask | V-P | an unreachable home waits, never fails (engine AD-64) |
| C9 | The Lab | QMB app | same machine | as C7 | Lab `QmbPort`, default adapter `app_op` (Lab AD-5, amended) | ask | V-P | as C8 |
| C10 | QMB app | core landing | same machine (app to host) | finished result (P11's `backtest-result` extension of Library AD-29) and the run's daily R stream in; run id and principal stamp issued; try ledger row written | `backtest_and_land` (PR 204, STACKED, rebased into the host) | ask | V-S | no result lands without a core run id; a killed run lands as "failed, killed" |
| C11 | QMB app | market-data door | same machine | partitions by fingerprint; his holdout choice applied where served | `materialise` (`qmx_host/market_data.py`, EXISTS) | read | V-K | a missing month names which data and how to download it |
| C12 | QMB app, trading node app, MIS app | QML compiled unit or reading block | in-process inside each app | the compiled factory by unit `id@version`; reading blocks by `id@version` | the structural `BotFactory` seam (EXISTS, CHECKED) | call | V-S | n/a |
| C13 | QMB app, trading node app | journal writer | in-process | envelope plus kind records (P5); QMB's land inside the `backtest-result`'s blobs, the node's in partitions committed through its machine's market-data door | the writer library in `packages/qmf-data` (extended) | write | V-S | journal-before-dispatch: a failed write blocks the effect, never a stop or exit (AD-12) |
| C14 | Judge | Library | in-process in the host | verdict, baseline card, proposal card (P3) as governed drafts; reads the try ledger and the study spec | Library landing (EXISTS) | write | V-K | n/a |
| C15 | Workflow templates and agents | journals, reading history, instrument records | in-process in the host | queries with a required time window in; rows, digests out | rows `journal_query`, `readings_query`, `instrument_get` (NEW); `data_features` (EXISTS) | read | V-S | a query past the data says where the data stops |
| C16 | Agents | notes stream | in-process | analysis and proposals, each linked to the rows it explains | a write row on the notes stream (NEW) | write | V-S | n/a |
| C17 | Library ref log | workflow templates | in-process in the engine | a landed item (kind, output name, producer) fires a trigger | event triggers (PR 160, EXISTS) with a loop guard (NEW) | event | V-S | catch-up after downtime by setting per trigger |
| C18 | Venue refresh jobs | instrument, venue and account records | in-process in a workflow on a host with a read grant | new record versions (P4) | Library kinds (NEW) | write | V-K | the last version stays in force; a record older than its maximum age is flagged |
| C19 | Downloaders and feed recorders | market-data door | same machine | staged partition files, then `commit` | the door's single writer (EXISTS) | write | V-K | an empty trading hour is a fetch failure until a retry and a second source agree |
| C20 | The Lab | MIS app | same machine | trained model readings as Library `model` items, in shadow | Library items; MIS app operation to register a shadow reading (NEW) | write | V-K | the default reading stays live |
| C21 | Feed keeper (inside the node app) | units and the node's guards | in-process inside the node app | normalised prints, quotes, book updates, bars (P14's internal format) | in-process fan-out (QMN's loop and accumulator, kept) | push | V-S | a stale feed stops new entries for that market; protection stays |
| C22 | Node's guards | reading history | in-process | execution-health readings stamped with time and version (P1 cards), `source = node` | the journal writer, stream `reading history` | write | V-S | as C13 |
| C23 | MIS app, node instance | the node machine's market-data store | same machine | bars and quote ticks recorded by the feed keeper (live rooms and frozen partitions) | market-data door `read` (EXISTS) | read | V-K | readings go stale; units are unaffected |
| C24 | MIS app instance | reading history, Library events, the board | same machine | stamped readings; state-change events; the board with `stale_after` per tier | partitions `source = mis`; Library records; `provides.board` (EXISTS homes, G4b Q6) | write | V-S | the board goes stale; consumers fall back |
| C25 | Unit (inside the node) | the board | same machine | optional placement read: which of his admitted markets are in the unit's condition now | a read surface with `stale_after` (NEW) | read | V-S | falls back to every admitted market on the unit's own conditions |
| C26 | Node app | its volume | in-process | the desired state: deployments, accounts, modes, snapshots, unshipped journals | the app's own volume (EXISTS mini-app volume) | read and write | V-S | the node converges to it on every start |
| C27 | Node app | the host's key store on its machine | same machine | the venue grant for that machine (live only on a trading-profile host) | Credential Manager on This PC; owner-only vault file on a server (EXISTS stores) | read | n/a | no grant, no session; shown as a venue state |

## 3. Between machines (networking)

Machines: This PC (Windows, loopback-bound host), any server (Linux, host bound to its Tailscale address only, `HO/host.py:254`), all on his tailnet. Every link below rides what exists: REST and SSE with `Last-Event-ID` resume and MCP over streamable HTTP on the host's one port behind one bearer (`CTL/server.py`, G2 §6); one held stream per reachable owned node into the merged inbox (`HO/streams.py`); host-to-host passes with `POST /api/data/read` (`HO/door.py:26-36`); the Library hub (Library AD-11, AD-14); OpenTelemetry over the tailnet with a disk-backed queue (engine AD-69, amended in AD-42).

| # | From → To | What crosses (shape, owner) | Transport and door | Latency it tolerates | How often, how much | Order path | Down, reconnect and backfill | Placement | Version |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| X1 | His click or the copilot on This PC → the node app on its home | deployment as desired state (unit version, markets, account, practice or live); `pause`, `resume`, `kill`, `flatten`, `mode` (P12 operations) | app operation at a remote home (engine AD-64) over the host port on Tailscale, a host pass; `money` operations need his signature | seconds | rare; a deployment carries the compiled unit, calibrated values and instrument snapshots (kilobytes to a few megabytes) | no | an unreachable home waits and the call is kept as desired state; the node converges when reached; the kill switch has two more paths: the node's own screen when reached directly, and the broker's own app as the last resort, written on the node's page | either side | V-H, V-P |
| X2 | Node → This PC inbox | heartbeat (state, reason, unit summary, clock band and offset, zone, `tzdata`, version, last broker contact), node state, guard events | held stream per reachable owned node, SSE with resume | seconds to a minute | heartbeat every 60 s (setting); events as they happen; small | no | the PC shows "unreachable since" with the last values; on reconnect the stream resumes from `Last-Event-ID`; unreachable after 3 missed heartbeats (setting) | PC holds the stream | V-H, V-S |
| X3 | This PC → node (pull) | closed journal partitions and the live tail; the node's reading history (P5, P13) | a PC-side job reading the node host's data door with a host pass (NEW job) | minutes | live tail every 5 minutes, closed partitions at once (settings); the market journal is about 1 to 2 GB a year per broker for the instruments traded (research 12, INFERRED for his set); unit journals are events (small) | no | the node keeps every partition until the PC confirms a verified copy; idempotent by writer id and sequence, so a resend changes nothing; a week offline loses nothing; on the server the disk guard stops tick recording before journals | PC pulls | V-S, V-H |
| X4 | Node → OpenObserve on This PC | spans, gauges, logs | OTLP over HTTP through the one telemetry switch; a collector with a disk queue on the server | minutes | batches; drops counted | no | fire and forget; the queue drains when the PC is back; a server may run its own OpenObserve as a stand-in | collector on the server, home on the PC | V-S |
| X5 | This PC Library ↔ a server Library | Library objects, refs, edges | the Library hub's replication (EXISTS) | minutes to hours | as items land | no | offline is normal; ordered by parent hashes; a stale head is an alarm, not a merge (Library AD-14) | either | V-K |
| X6 | This PC → a workflow step placed on a server | step inputs and outputs; data reads | run passes; `POST /api/data/read` (EXISTS) | minutes | per step | no | **known gap:** a run pass minted on the PC fails at the server's door (G2 §6, backlog "Cross-machine run passes"); fixed and rechecked before any PC-minted run relies on a server; until then such steps wait `placement` | data-heavy steps run where their partitions are (engine AD-70) | V-H |
| X7 | Agents and the node watcher on This PC → node reads | `status`, `units`, `positions`, `journal_tail`, `passport` (P12) | as X1, read operations only | seconds | on demand and on the watcher's schedule | no | answered from the PC's last values and the view-only broker read when unreachable | PC | V-P |
| X8 | Connect dialog on This PC → a new server | his cards, then checked rerun-safe steps (install, firewall with a 5-minute undo, Tailscale bind, `qmx-recover`, chrony, the node app, the MIS instance, the venue sign-in on that machine, the self-test) | SSH and Tailscale through the shipped step runner (PR 232; trading-node choice NEW) | minutes | setup time only | no | every step can be rerun; the dialog names the failed step; one place row written last | n/a | n/a |
| X9 | Node → an off-server liveness watcher | an alive ping with zero authority | QMN's liveness heartbeat (kept organ) to the PC host and to any QMX server he names | minutes | every heartbeat interval | no | a missing ping alerts him; nothing acts on its own | a machine other than the node's | V-S |

**Placement rules (AD-44).** A trading node sits near its broker's servers; the PC is never between a unit and its broker. Measured from his PC: about 156 to 167 ms for a TCP handshake to cTrader live and about 31 ms to Hyperliquid, against about 0.5 ms median for in-process fan-out (research 31, research 38, CHECKED there). A region study by distance to IC's and Spotware's servers is owed to Level 1 C. A machine holding a live grant runs the trading profile only; workflow steps are never placed there (engine AD-70).

## 4. Outside QMX

| # | From → To | What crosses | Transport | Latency it tolerates | How often | Order path | Down, reconnect and backfill | Version |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | Trading node → cTrader Open API | CT-19 commands (place, cancel, close, close all, amend protection) and CT-20 events; spot, depth and trendbars; reconcile reads | TLS protobuf on port 5035, one long-lived session per environment per machine; OAuth token with one refresher per grant (EXISTS organ, NEW live profile) | the network floor; the signal-to-send budget for a 1-minute unit is 1,000 ms (setting) | 50 requests a second, 5 for history (the venue's own limits, `ctrader.py:123-145`); heartbeat within 10 s | **yes** | no cancel-on-disconnect at cTrader, so every order carries its stop at the broker; a silent socket is caught by the heartbeat bound and forced to reconnect; "connected" is not "ready" until authenticated, subscribed and capabilities re-verified; gap replay of fills; no entries until ready, exits allowed; never resent blind (UNKNOWN) | V-L, V-CT |
| E2 | This PC host → cTrader Open API (reads) | accounts, balance, positions, a quote, trendbars, symbol specs, each stamped demo or live | one short TLS session per read; a view-only live grant or a demo grant (EXISTS, never run on his folder) | seconds | on demand and for refresh jobs | no | a failed read says why; the PC's app is a different cTrader app from any trading machine's | V-L |
| E3 | Trading node → Hyperliquid | orders, positions, funding, open interest, book, trades with taker side | CCXT 4.5.85's `hyperliquid` class (REST signed actions within a nonce window) and `ccxt.pro` streams (CHECKED offline: create, cancel, edit, positions, funding, open interest, book, leverage, trigger and reduce-only orders, sandbox) (NEW adapter) | the network floor; nonce window around block time | the venue's own limits (per IP 10 websockets, 1,000 subscriptions, 2,000 messages a minute; an address action budget) | **yes** | `scheduleCancel` never relied on; protection re-placed after any cancel; open orders kept under a margin of the 1,000 cap; the clock band is checked before signing; testnet for practice; a testnet probe before the first live order | V-L |
| E4 | Trading node → Binance, Bybit and other CCXT venues | as E3 | CCXT unified calls and streams (NEW, Should) | as E3 | venue limits | **yes** | as E3; a per-symbol countdown cancel only if protective orders survive it | V-L |
| E5 | This PC host → CCXT venues (reads) | balances, positions, quotes, bars, specs, funding, open interest, books, now including contract markets | CCXT (EXISTS spot reads; contract reads NEW) | seconds | on demand and refresh jobs | no | demo rows refused where no sandbox exists (PR 224) | V-L |
| E6 | Downloaders on This PC → Dukascopy, Binance Vision | historical partitions | HTTP, scheduled workflows (EXISTS templates) | hours | scheduled | no | an empty hour is a failure until a retry and a second source agree; licence on the card | V-L |
| E7 | Data route or futures broker (placeholders) → node or PC | trades with aggressor side, depth, open interest for CME underlyings | Databento (key check only today); Rithmic R|Protocol and CQG WebAPI (WebSocket plus protobuf) as declared placeholders | n/a until switched on | n/a | yes for a futures broker, no for data only | off until he chooses and pays; nothing in the core assumes one | V-L |
| E8 | His browser → a venue's sign-in page | the venue's own consent; a one-time code to the host's loopback receiver (`127.0.0.1:47613` for cTrader) | the venue's OAuth (EXISTS for cTrader) | n/a | once per grant | no | QMX never sees a password; the token lands in that machine's store | V-L |
| E9 | Each machine → time sources | clock offset | Windows Time on This PC; chrony with four or more sources on servers | n/a | continuous | no (but gates it) | an unproven offset flags rows `clock_ok = false`; past the halt band a trading node takes no new entries | n/a |
| E10 | The broker's own app (his phone or desktop) → his account | his manual close or flatten | the venue's app | n/a | only when the node is unreachable | his last resort | written on the node's page | n/a |

## 5. The shapes that cross, and their one owner

| Shape | Owner (one writer) | Carried by | Defined in |
| --- | --- | --- | --- |
| Unit document `qmx.unit/1` | P2 (schema); authors write documents | Library `unit` kind | Level 1 A |
| Check result | P1 | C1 to C4 | Level 1 A |
| CT-23 format 3 sized unit intent | P1 (its family lives in `packages/qmf-risk`; the node consumes it) | in-process, unit to the host that drives it | Level 1 A |
| Catalogue entry and block (extended `component` kind) | P1 | Library; QML package data; carried inside each deployment | Level 1 A |
| Reading card (schema) | P1 | catalogue | Level 1 A |
| Stamped reading and the default reading packs per class | P13 (the `mis` app, `source = mis`) and the node's guards (`source = node`), one writer per series | partitions in reading history | Level 1 C |
| QMB operations and the `backtest-result` extension | the QMB contract (P11) | app operations; core landing | Level 1 B |
| Study spec, verdict, baseline card, try ledger row | P3 | Library kinds; landing | Level 1 B |
| Journal envelope and kinds | P5's writer library | partitions with cards; `journal_query` | Level 1 B |
| Node operations, `node_state`, `unit_states`, heartbeat | P12 | app operations; held stream | Level 1 C |
| Deployment (desired state) | P12 | X1; the node's volume | Level 1 C |
| Instrument, venue and account records | P4's refresh jobs | Library kinds; node snapshots | Level 1 C |
| CT-18 capability declaration and measured profile; CT-19 commands; CT-20 events | `packages/qmf-venue` (kept) | venue-client port | EXISTS |

## 6. Known gaps on these links

| Gap | Link | Who closes it |
| --- | --- | --- |
| A run pass minted on the PC fails at a server's door | X6 (and X3 if it used a run pass) | Level 1 C rechecks against the merged stack; the pull job uses a host pass |
| No live host profile in the node; the PC side of the node link never existed | X1, X2, X3 | Level 1 C (AD-36, AD-45) |
| Plugin hooks under the Agent SDK are unprobed | C4 | a probe before the hook packet (Level 1 A) |
| Whether Hyperliquid accepts a reduce-only trigger order as a resting stop; whether cTrader rejects a repeated client order id | E1, E3 | Level 1 C proves on demo and testnet, or designs around them |
| The `qmb` app does not exist, so `app_op {app: qmb}` fails today | C8 | Level 1 B |
| Webhook deliveries carry no sender signature | inbound webhooks (not on the unit path) | backlog |

## 7. Using this file

A Level 1 part checks each of its connections against a row here: the same shape name and owner, the same door, the same version rule, the same behaviour when the other side is down. A connection a part needs that is not here is proposed in that part's "Contract changes" section. A row here that a part cannot meet is a conflict to surface, never a local override.
