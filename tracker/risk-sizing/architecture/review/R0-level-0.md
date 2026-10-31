# R0. Quick review of the Level 0 spine

Reviewer R0, 31 Oct 2026, brief `architecture/briefs/R0-review-level-0.md`. It reviews and does not rewrite. Reviewed: `level-0/ARCHITECTURE-SPINE.md`, `01-connections.md`, `level-0/blast-radius.md`, `level-0/LEAD-CALLS.md`, `funnel/versions/versions.md`, `funnel/versions/GLOSSARY.md`. Against: STATE midday rulings 1-55, the ledger, the lead's review of the funnel (`funnel/00-lead-review-of-funnel.md`), the edge-case catalogue and its F1-F20 checklist, G1 to G4b, the frame, and the code at `D:\QMX-worktrees\engine-base-read\` (`c93407ca`, read only).

**How it ran.** `bmad-review`, three lenses run in sequence by me (no sub-agents): adversarial, edge-case, verification-gap. The brief's output shape wins over the skill's unranked JSON, so findings are ranked and each names its lens. Code paths below are relative to the engine-base checkout; `APPS`, `HO`, `ENG` stand for `qmx-agents/packages/qmx-apps/src/qmx_apps`, `qmx-host/src/qmx_host`, `qmx-engine/src/qmx_engine`. CHECKED means read or run this session (path:line, or the script named). INFERRED means my judgement.

**Scripts.** `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\r0\owners.py` (case ownership, run as `python -I owners.py <spine> <catalogue>`) and `...\scratchpad\r0\pb_fields.py` (reads cTrader's `openapi-91.pb` descriptor; run with A0's scratch environment's Python).

## Verdict

1. The shape holds. A small core plus three apps is the right pick, ownership is complete (267 of 267 cases owned exactly once, CHECKED by `owners.py`), and his rulings are honoured almost everywhere.
2. The networking section is the weak part. Three of the cross-machine links it calls "built" ride routes the code does not have, and two others point into This PC, which listens on loopback only. Part C would start from a false premise.
3. Five other things the spine treats as settled are open: the "does it trade" check (UT-01), how the node tells its positions from another node's on cTrader, the live sign-in on a server against ruling 135 in code, where the before-dispatch journal write goes, and where block code lives and how it loads.
4. The 567 of 570 score measures the properties, not the cases. About fifty cases have an owner but no handling line in the spine (appendix A). Most are Level 1 detail; five matter now.
5. The author's three open questions are real. One of them is wider than stated (R0-05) and one is not only a bug (R0-01). "Regime" is the only word he needs to see.

## Findings, most severe first

### R0-01 (High) The PC-to-node control, pull and read links ride routes that do not exist
- **Where:** AD-28, AD-44, LC-A0-04; `01-connections.md` §3 rows X1, X3, X7 and the §3 lead paragraph ("every link below rides what exists").
- **What is wrong:** the spine says X1 (deploy, pause, kill, flatten) is an app operation at a remote home with a host pass, X3 (the journal pull) reads the node host's data door with a host pass, and X7 reads node operations the same way. None of these is wired. The run-pass bug is not the only gap.
- **Evidence:** CHECKED. A host pass is admitted on four routes only: the cTrader sign-in begin and code routes and the engine's two forwarding routes (`HO/venue_session.py:89`, `HO/door.py:167-177`, docstring `HO/door.py:33-36`). The forwarding verbs are read-only engine verbs plus `inbox.resolve` (`ENG/service/forward.py:60-63`). `POST /api/data/read` admits run passes only (`HO/door.py:26-31`). The `app_op` executor is composed with no placements (`ENG/control_door.py:308`), so it always runs locally, and the supervisor refuses an app homed elsewhere with `not_home` (`APPS/supervisor.py:527-532`). The remote path exists only as an optional constructor field that nothing sets (`ENG/nodes/app_op.py:95`, `:121-140`).
- **Fix:** mark X1, X3 and X7 NEW in §3 and §6. Add one rule to AD-44: "the PC reaches a node through a small, named host-pass route set (remote app operations, node reads, closed-partition and live-tail reads), added surgically to the door beside the four that exist". Part C designs that route set first, with the run-pass recheck folded in.
- **Lens:** verification-gap, adversarial.

### R0-02 (High) Two links point into This PC, which accepts no connection from another machine
- **Where:** AD-42, AD-44, LC-A0-14; X4 and X9.
- **What is wrong:** X4 has a server's collector ship telemetry to OpenObserve on This PC. X9 has the node send a liveness ping "to the PC host". Both are connections into the PC. The PC host binds loopback only, and so does its OpenObserve. AD-44 has no rule about which side opens a link.
- **Evidence:** CHECKED. `HO/host.py:254` binds `TAILNET if role == "server" else LOOPBACK`. OpenObserve on the PC runs on `127.0.0.1:5080` (`HO/connect_logs.py:7`, `:186-188`). The built server option installs OpenObserve on the server and "points `send_to` at that server" (`HO/connect_logs.py:11-12`), which is engine AD-69's shape that LC-A0-14 reverses.
- **Fix:** add to AD-44: "every cross-machine link is opened by This PC or ends on a server; nothing connects into This PC". For telemetry, either keep the built shape (each server's OpenObserve is home for its own telemetry, and the PC's screens read it through the new host-pass route set of R0-01), or name a NEW inbound listener on the PC's Tailscale address with the ingest credential. I recommend the first: no new port on his PC. Drop X9's "to the PC host" (X2 already detects a dead node from the PC side) and keep only "a server he names".
- **Lens:** adversarial.

### R0-03 (High) Checker layer G, as written, does not catch a unit that trades nonsense (UT-01)
- **Where:** AD-17 (layer G); P2's case UT-01, one of the catalogue's five costliest.
- **What is wrong:** layer G runs the unit on a recorded slice and feeds "QML's unchanged `evaluate_layer2` verdict". That verdict checks safety and determinism, not trading. A unit that is always long, whose exit never fires, or whose signal is constant passes it on real bars exactly as it passes on three instants.
- **Evidence:** CHECKED. The verdict's checks are `static_ast_import_scan`, `logic_loads_in_isolation`, `no_book_present`, `permitted_intent_kinds`, `golden_slice_determinism`, `state_bound_restore_equivalent` and the source manifest (`qml/src/qml/conformance/layer2.py:215-298`). The catalogue's own proof for UT-01 asks for trades happening, exits firing, a non-constant signal and a shuffled-day control (`catalogue.md` UT-01).
- **Fix:** AD-17 G gains a behaviour report beside the unchanged safety verdict: trade count (or a declared "may not trade on this slice"), each exit kind fired or reported unfired, signal not constant, and a shuffled-day control reported. All warnings; the judge's numbers decide (no false positives).
- **Lens:** verification-gap.

### R0-04 (High) The live sign-in on a trading server collides with ruling 135 in code, and the change is not listed
- **Where:** AD-37, AD-45, LC-A0-15; E8; C27; "Amended decisions".
- **What is wrong:** AD-37 stores the live grant "only by the node app in that machine's own store; every other QMX host keeps refusing". In code every host refuses a live-capable grant by name, the trading host included, and the sign-in flow is the host's own. So binding a live account, which is what puts a server into the trading profile, cannot happen without a code change the spine does not name. Second gap on This PC: practice needs a trade-scope grant over demo accounts, and shadow runs need a view-only grant over live accounts. One cTrader grant has one scope, and the store holds one token pair per app per home, so This PC needs two apps or two token names, and the spine does not say which process refreshes each.
- **Evidence:** CHECKED. `LiveGrant` docstring "every QMX host refuses it by name" (`qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:103-113`); `can_trade_live` is any non-view scope listing a live account (`adapters.py:137-146`); the sign-in relays the one-time code from the PC's loopback to the home with a host pass, then refuses a live grant and writes `qmx/token/ctrader-app` (`HO/venue_session.py:1-16`).
- **Fix:** add an "Amended decisions" row: "ruling 135 in code: the host's sign-in accepts a live-capable grant only when the home is the `trading-node` app instance on a host with no chats and no agent steps; the PC relays only the one-time code, never a token". In AD-37, name This PC's two grants (demo trading for the practice node, view-only for live reads) and give each one refresher (the node for the first, the host for the second).
- **Lens:** adversarial, edge-case.

### R0-05 (High) "Two nodes on one account" and "a node replaced" are not handled by node-tagged client order ids
- **Where:** AD-8, AD-13, AD-38, LC-A0-05; cases TN-04 (P12), MA-02 (P10); A0's own adversary review, which "cleared" two nodes on one account.
- **What is wrong:** three gaps. (1) On cTrader a position does not carry the client order id, so a start-up reconcile cannot tell another node's positions by it; only pending orders carry it. On Hyperliquid positions are netted per coin with no tag at all. (2) The kept reconcile organ compares the node's ledger with read-back quantities and returns one verdict per account; it does no per-order attribution, so the foreign-claimant test is new code. (3) A copied server disk carries the node's identity, so a clone passes the machine check (PM-5); and when a server dies, the replacement node sees positions tagged with the old node id, treats them as foreign and refuses the account, with no path to take them over except closing them by hand.
- **Evidence:** CHECKED. `ProtoOAPosition` fields are `positionId, tradeData, positionStatus, swap, price, stopLoss, takeProfit, ...` with no `clientOrderId`; `ProtoOATradeData` carries `label` and `comment`; `ProtoOAOrder` carries `clientOrderId`; `ProtoOAReconcileRes` returns `position` and `order` (from `qmx-agents/packages/qmx-broker/src/qmx_broker/protocol/openapi-91.pb`, read by `pb_fields.py`). The node encodes `clientOrderId` only (`packages/qmf-venue/src/qmf/venue/encode.py:598`). Reconcile verdicts are `reconciled | drift | unknown | out-of-lookback` over persisted read-back (`qmn/src/qmn/venue/live.py:1055-1094`, `packages/qmf-venue/src/qmf/venue/events.py:1265-1289`).
- **Fix:** AD-8: the node tag rides cTrader's `label` as well as the client order id, and Hyperliquid's `cloid`; one node per account (or per Hyperliquid subaccount), recorded on the account record. AD-38: a node identity is the machine id plus an install id minted at first start, and a node whose install id does not match its deployment refuses until he says "this is the same node". Add his "take over" click: once he confirms the old node is gone, the new node adopts that node's tagged positions under protection. This widens the author's open cTrader question; repeated-id behaviour still needs the demo probe.
- **Lens:** adversarial, edge-case.

### R0-06 (Medium) Where the before-dispatch journal write goes is ambiguous, and one reading puts the host on the order path
- **Where:** AD-12, AD-27, C13.
- **What is wrong:** AD-27 says QMB and the node write through P5's writer library, which "commits through the machine's market-data door (its single writer)". That door is a host component that takes finished partition files and a `commit`. A builder who routes the node's journal-before-dispatch write through it makes the host process a step on every order and adds a cross-process call before each send.
- **Evidence:** CHECKED. "A downloader ... writes finished partition files into a staging folder and calls `commit(files)`; nothing else writes the store" (`HO/market_data.py:3-6`). The node's live sink appends to its own CT-13 journal store in process (`qmn/src/qmn/data/observation_sink.py:189-196`).
- **Fix:** AD-27 adds one sentence: the before-dispatch write is the node's own append store on its volume, in process; only closed partitions pass the market-data door, after the fact.
- **Lens:** adversarial.

### R0-07 (Medium) Where block code lives, and how QMB and the node load it, is not decided
- **Where:** AD-16, AD-19, AD-38, P1 growth seam.
- **What is wrong:** AD-19 ships "a catalogue snapshot as QML package data", while AD-38 has each deployment carry "every pinned block's code and fingerprint", and the dictionary file refreshes that package data on every entry publish (`funnel/solutions/dictionary.md` §9). Package data is fixed at build time, but blocks grow through the authoring door with no cap, and agent-written blocks must load at run time on the node. The scan bans `importlib` and `exec` for agent blocks, yet some loader must use them. Two paths for one thing, and no loader named.
- **Evidence:** CHECKED in the files cited; INFERRED that package data cannot be refreshed per publish without writing into an installed package.
- **Fix:** decide at Level 0. Block source is a Library item with its fingerprint. One QML loader compiles pinned sources after a fingerprint check, the same in QMB's sandbox and in the node. A deployment carries a folder of its pinned blocks. Package data holds only the blocks shipped with QML itself. Part A designs the loader.
- **Lens:** adversarial.

### R0-08 (Medium) The connections table misses five links
- **Where:** `01-connections.md` §3 and §4; AD-5, AD-40, AD-42.
- **What is wrong:** (a) software and app updates to a server (host build, his signed node versions, MIS app versions, shadow models from the Lab) have no row, though TN-17 and DO-07 depend on it; (b) AD-5's nightly replay of each live day needs the quotes and bars the node's feed keeper recorded, and X3 carries only journals and reading history (the market journal is costs per minute, not ticks); (c) the PC's slow-tier readings and cross-market board never reach the node, which is right under AD-2, but the table should say "none crosses" so nobody adds one; (d) E8 covers cTrader only, not how a Hyperliquid agent wallet reaches a server; (e) no path tells him about a fault while his PC is off (R0-09).
- **Evidence:** CHECKED by reading §3 and §4 row by row.
- **Fix:** add X10 (updates, PC-initiated through the connect dialog's step runner or the new route set, V-H rule on mismatch), extend X3 with the recorded feed partitions (with their size), add a "none crosses" line for PC readings, add the Hyperliquid wallet step to E8, and add E11 for the alarm path.
- **Lens:** edge-case.

### R0-09 (Medium) No alarm reaches him when his PC is off
- **Where:** AD-42 ("wake him for a short named list"), X9; cases PM-9, OP-04.
- **What is wrong:** the spine names no channel. Telemetry's home is the PC, and the node exists because his laptop goes off (ledger N-08). X9's watcher "alerts him" with no channel either.
- **Evidence:** CHECKED. The only phone path in either file is the broker's own app (E10).
- **Fix:** name an outbound alarm sender on the trading machine (a push or mail service, its key in that machine's own store), on by default for the short list, with its own row E11. Its failure never touches trading.
- **Lens:** edge-case.

### R0-10 (Medium) AD-36 understates the node cut: a kept organ routes through a deleted part
- **Where:** AD-36; "For the risk session" row on the kill line.
- **What is wrong:** AD-36 moves "the three outside callers". Inside `qmn`, the kept kill line and bench fold import Book paper's demotion, and a kept MIS module imports the promotion hub. Deleting Book paper without moving them removes the kill line's breach route, and the spine says the kill line stays unused until the risk session picks its verb, so nobody states what a breach does after the cut.
- **Evidence:** CHECKED in `blast-radius.md` §5: `qmn/capital/kill_line.py:38` and `bench_fold.py:32` import `qmn.paper.demotion`; `qmn/mis/regime_register.py:60-61` imports `qmn.promotion.hub`.
- **Fix:** AD-36 names these callers. Give the kill line a labelled placeholder action after the cut (for example, no new entries on the account), and keep the stop-on-every-order test before and after.
- **Lens:** edge-case.

### R0-11 (Medium) The score proves the properties, not the cases
- **Where:** `versions.md` §4 to §6; the spine's P-section claim that every case is owned and handled.
- **What is wrong:** each case scores the lowest of the properties the catalogue names for it, and A scores 2 on all twenty properties, so A scores 2 on every case unless the author overrode it by hand. 567 of 570 follows from A's own property scores plus three overrides. No per-case handling was checked.
- **Evidence:** CHECKED. `versions.md:142` ("A case scores the lowest score of the properties ... unless a named override applies"); §4 shows A at 40 of 40. My own read finds about fifty cases with no handling line in the spine (appendix A), including UT-01, TN-04 and MA-02, which all scored 2.
- **Fix:** each Level 1 file carries a table of its cases with the handling and the AD or section that holds it. R1 checks it by script: every case id present, each with a non-empty handling.
- **Lens:** verification-gap.

### R0-12 (Medium) Which checker layers run at which door is inconsistent
- **Where:** AD-11, AD-17, AD-29, LC-A0-12.
- **What is wrong:** AD-17 says one function runs layers A to G and is reached four ways. LC-A0-12 says the Library save runs A to E, so code safety (F) would not run at the save. Layer G needs QMB's sandbox and downloaded data, so it cannot run inside a 10-second hook or every save (AG-03, LD-06).
- **Evidence:** CHECKED in the two files; the guard's 10 s timeout is from G2 §2.1 (cited by the catalogue, AG-03).
- **Fix:** one small table in AD-17: hook and catalog row run A to F; the Library save runs A to F; a QMB run and a node deploy require a recorded G verdict for the exact compiled fingerprint, stored with the unit.
- **Lens:** verification-gap.

### R0-13 (Medium) "Only the node may hold an order client, enforced at install" names a check the core cannot make
- **Where:** AD-33, LC-A0-18.
- **What is wrong:** an app is arbitrary code behind an MCP server; nothing at install can see "order-capable" in it. What the core can enforce is the secret map: a manifest names `qmx/*` secrets and the supervisor injects them.
- **Evidence:** CHECKED. `capabilities.secrets` (`APPS/manifest.py:77`), validated to `qmx/*` names (`APPS/manifest.py:311-317`).
- **Fix:** "only the `trading-node` manifest may name the venue trading-grant secrets; install refuses any other app that names them". Add the network allow-list where the Docker tier enforces it.
- **Lens:** adversarial.

### R0-14 (Medium) Who clears each automatic stand-down is not said, and two confirmed calls are missing
- **Where:** AD-23, AD-38, P4 (TN-25); the lead's review "Calls confirmed".
- **What is wrong:** AD-38 says "a repeated fault stands down entries alive" but not who clears it (the catalogue's lead's call 2 says him; ruling 35 says heal). TN-25 pauses units after a broker spec change "until it is accepted", by nobody named. The lead's review confirmed two soak settings (24 hours on the PC before a release, one week on demo before a live binding) and "tested to paper is his click by default"; neither appears in the spine.
- **Evidence:** CHECKED by grep over the spine and `01-connections.md` (no "soak"; "toward live" only).
- **Fix:** one table in AD-38: each automatic stand-down (stale feed, clock band, disk, repeated fault, spec change), what clears it, the default. Add the soak numbers to the deferred list as named settings, and "tested to paper: his click" to AD-23.
- **Lens:** edge-case.

### R0-15 (Low) The held stream does not resume by event id
- **Where:** X2 ("SSE with resume ... from `Last-Event-ID`").
- **What is wrong:** the held stream re-reads current open items every 5 s after a drop; events between drops are not replayed. Heartbeats and state are fine (latest value); guard events can be missed.
- **Evidence:** CHECKED. `HO/streams.py:1-9`, `RETRY_S = 5.0`; `Last-Event-ID` appears only in `qmx-agents/packages/qmx-control/src/qmx_control/server.py`.
- **Fix:** X2 carries latest values only; guard events reach the PC through X3.
- **Lens:** verification-gap.

### R0-16 (Low) The trading profile is one rule, not a third profile
- **Where:** AD-45, LC-A0-15.
- **What is wrong:** the code has a host role (server or not). "Trading" is entered by binding a live account, so it is derived state. One rule says it all: a host holding a live grant refuses chats and agent workflow steps.
- **Evidence:** CHECKED. `HO/host.py:254` branches on `role == "server"`; no profile type exists in the host.
- **Fix:** state the rule and drop the third profile name. Use the code's word (role) or rename it once.
- **Lens:** adversarial (over-building).

### R0-17 (Low) Existing Library kinds overlap the new ones
- **Where:** AD-21, AD-29, C16, AD-39.
- **What is wrong:** a `note` record kind and a `paper-run` record kind already exist, while the spine adds a new notes stream and per-unit paper lanes. `bot` and `strategy` remain live governed kinds beside `unit`, which keeps QML-24's two-registries risk alive.
- **Evidence:** CHECKED by reading every kind file in `qmx-agents/packages/qmx-library/src/qmx_library/kinds/`: `note` and `paper-run` are records; `bot` and `strategy` are governed and not retired; `board`, `bot-card`, `logic` are retired.
- **Fix:** reuse `note` and `paper-run` (extended additively), and set `retired` on `bot` and `strategy` for new saves through their kind files (data, no code).
- **Lens:** adversarial (over-building).

### R0-18 (Low) Lab parts the spine leans on are designed, not built
- **Where:** AD-23 and LC-A0-10 (`settings.lab.identity_rule`), C9 (Lab `QmbPort`), C20.
- **What is wrong:** the identity table and the Lab's QMB port exist only in the Lab spine. QML imports no host, so it cannot read a Lab setting at all.
- **Evidence:** CHECKED. No `identity_rule` anywhere in the code (grep); the Lab's QMB node pack is "DESIGNED" (G4b line 98); the table is Lab AD-16 (`tracker/qma-v2/architecture/lab-and-pods/ARCHITECTURE-SPINE.md:189-193`).
- **Fix:** mark C9 and C20 NEW. Put the identity table in a core setting the host hands to QML as data; the Lab reads the same table.
- **Lens:** verification-gap.

### R0-19 (Low) Smaller gaps
- **QML-22 (P1):** AD-2 refuses non-local rule inputs, but a unit reading another unit's live output on the same machine is local and not refused. Add "a unit never reads another unit's live output; composition is at build time". INFERRED.
- **AD-24 versus ledger contradiction 34:** "the slots read only local inputs" forbids even optional cross-node reads with a fallback, which AD-2 allows. Say "local inputs, plus optional read surfaces per AD-2", so the socket does not decide the risk session's portfolio question. CHECKED in the ledger.
- **AD-2's list** of what the trading path needs omits the host process and its apps supervisor, which kill the node app when they die (`APPS/windows_job.py:35`, kill on job close). State it; it is LC-A0-06's real blast radius. CHECKED.
- **Worlds:** the glossary says practice is demo accounts and paper is a lifecycle state; AD-39 runs paper lanes on demo accounts; AD-27 lists paper, demo and live as worlds. Define "paper" and "demo" once. CHECKED.
- **F1:** AD-6 has readers read every version but no overlap window or deprecation notice, and REST routes stay unversioned (AD-30 versions catalog row schemas only; CA-01).
- **EX-06 (P14):** AD-26 keys instruments by (venue, symbol), but nothing names "the same market at two brokers", which QML-06 and his "more brokers, one record each" need.
- **Glossary:** "passport", "kill line" and "desired state" appear in the spine without an entry.

## The networking table, link by link (his ask)

His ask: every cross-machine link with its transport, the latency it tolerates, what crosses, reconnect and placement; nothing on the order path but node to broker.

| Link | Columns complete | Transport as built | Verdict |
| --- | --- | --- | --- |
| X1 control from the PC | yes | NEW: no remote app operation, no host-pass route (R0-01) | fix the label and design the route |
| X2 heartbeat and state | yes | built held stream; re-reads, no event resume (R0-15) | holds for latest values |
| X3 pull of journals | yes | NEW route; carries no recorded feed (R0-01, R0-08) | fix |
| X4 telemetry | yes | points into loopback-only PC (R0-02) | fix direction |
| X5 Library hub | yes | built | holds |
| X6 remote workflow steps | yes | built, known pass bug | holds as stated |
| X7 node reads | yes | NEW (R0-01) | fix the label |
| X8 connect dialog | yes (version n/a) | built step runner; trading choice NEW | holds |
| X9 liveness | transport not named | into the PC is impossible (R0-02) | name it or cut to "a server he names" |
| missing | | updates, recorded feed, PC readings, Hyperliquid wallet, alarm path (R0-08) | add rows |

**The order path.** Only E1, E3 and E4 are marked on it, which is right for cross-machine links. Two same-machine steps are not named: the host process whose death kills the node app (R0-19), and the before-dispatch journal write if it goes through the host's door (R0-06).

**Placement.** The rule (near the broker; the PC never between a unit and its broker; a live-grant machine runs no agent steps) is stated and CHECKED against research 31 and 38 as cited. The region study is correctly deferred to Part C.

## The author's open questions, and what else is open

| Item | Judgement |
| --- | --- |
| Hyperliquid trigger orders as resting stops | real and open; the testnet probe decides (TN-09) |
| cTrader and a repeated client order id | real, and wider: positions carry no client order id, so attribution needs `label` (R0-05) |
| The cross-machine run-pass bug | real, and not the only gap: host passes do not reach data reads or app operations at all (R0-01) |
| "Regime" | correctly the only word for his veto; the glossary and AD-40 agree; his 31 Oct answer 5 keeps the rest as working words |

**Open but presented as settled:** the PC-to-node routes (R0-01), the direction of telemetry and liveness (R0-02), the trading check in layer G (R0-03), the live sign-in on a server and This PC's two grants (R0-04), position attribution, clones and takeover (R0-05), the before-dispatch journal write (R0-06), the block loader (R0-07), and the alarm path (R0-09).

## Rulings and lead's calls

- **Honoured** (CHECKED by reading each against the spine): standing orders 6 to 10 and 19; rulings 22, 23, 24, 27, 32, 35, 37, 43, 45, 46, 49, 51, 52, 53, 55; the lead's review settlements 1 to 5; its confirmed calls except the two in R0-14; its gaps (both venue questions handed to Part C, the money app word in LC-A0-18, the copilot home in AD-31). AD-33's opt-in restart earns its place: a tripped app is killed and never restarted by itself (`APPS/supervisor.py:825-832`, `:863-865`), which blocks ruling 35.
- **Not honoured as written:** ruling 135 in code is changed without an amended-decisions row (R0-04); ruling 136's "PC is home" for telemetry rests on a transport that does not exist (R0-02); ledger contradiction 34, "the socket must not presume", is pressed by AD-24's local-only clause (R0-19).
- **Lead's calls whose premise fails in code:** LC-A0-04 (R0-01), LC-A0-05 (R0-05), LC-A0-14 (R0-02), LC-A0-18 (R0-13), LC-A0-10 (R0-18), LC-A0-12 (R0-12). The rest stand.

## Claims about code

| Claim in the spine | Result |
| --- | --- |
| live grants refused in the host (`adapters.py:103-146`) | true; refused everywhere, which is R0-04 |
| closed venue enum (`qmn/src/qmn/venue/port.py:40-45`) | true |
| money app restart needs no signature (`APPS/supervisor.py:542-547`) | true (walked, not run) |
| no automatic restart after a trip (`APPS/supervisor.py:828`, `:863`) | true |
| server binds Tailscale only (`HO/host.py:254`) | true; the PC binds loopback, which is R0-02 |
| QMN pins its machine (`configured_runtime.py:278-280`) | true |
| MIS publishes to the Book door only (`signal_snapshot.py:1-4`) | true |
| "a tuned set mints a new bot" (`bot.py:618-628`) | true |
| cTrader limits 50 and 5 a second, 10 s heartbeat (`ctrader.py:123-145`) | true (the constants sit at `:131-136`) |
| only replay is registered (`configured_live_resources.py:38-58`) | true |
| CCXT reads refuse contracts (`adapters.py:330-339`) | true |
| QML's tests ban `qmf.venue` | true (`qml/tests/test_gate_registration.py:491-501` and others) |
| host passes and `POST /api/data/read` carry data between hosts | false (R0-01) |
| an app instance at a remote home answers `app_op` | false as composed (R0-01) |
| X2 resumes from `Last-Event-ID` | false (R0-15) |
| node-tagged client order ids identify positions at reconcile | false on cTrader (R0-05) |
| layer G on recorded bars proves behaviour | false (R0-03) |
| the Lab's identity table exists | design only (R0-18) |

## Over-building

Cut or merge: the third host profile (R0-16); X9 when it duplicates X2 (R0-02); the package-data snapshot beside the deployment's pinned blocks (R0-07); new kinds that duplicate `note` and `paper-run` (R0-17). Kept on purpose and right: the risk socket with one placeholder adapter (ruled as a connector), futures clients as declarations only, the MIS split by job (LC-A0-02 holds: apps cannot stream to each other and a guard may not wait on another app). Forty-five rules is long for Level 0, but each binds a Level 1 part; I found no AD that could go without losing a case.

## Foundation properties, F1 to F20

| Property | Met? |
| --- | --- |
| F1 versioned contracts | partly: no overlap window, routes unversioned (R0-19) |
| F2 defaults | yes (AD-14, AD-15) |
| F3 one way to add | yes (AD-1) |
| F4 owned names | yes (AD-30) |
| F5 declared inputs, known times | yes at Level 0; detail cases in appendix A |
| F6 same code in both worlds | partly: the nightly replay lacks the node's recorded feed (R0-08) |
| F7 unknown is a state | partly: resolution by client order id fails for cTrader positions (R0-05) |
| F8 at least once with an id | yes, with X3 as the backstop for X2 (R0-15) |
| F9 fail closed for risk, open for protection | yes, if R0-06 is fixed |
| F10 immutable records | yes (AD-7) |
| F11 lifecycle with reasons | yes (AD-38) |
| F12 checked at the door, every problem | partly (R0-03, R0-12) |
| F13 observable; health is progress | partly: no alarm with the PC off (R0-09) |
| F14 declared rights | partly: units run in the node's process (accepted, LC-A0-08); install check unbuildable (R0-13) |
| F15 standalone, local first | yes (AD-2), with the host named (R0-19) |
| F16 only he promotes; one automatic stop | partly: clearing of stand-downs unnamed (R0-14) |
| F17 one time scale | yes (AD-10, AD-43) |
| F18 one owner per stream and position | partly: clones and takeover (R0-05) |
| F19 typed market facts | partly: no cross-broker market identity (R0-19) |
| F20 explainable in a sentence | yes (below) |

## The whole architecture in plain sentences (his test)

1. QMX keeps one copy of the few things that must always agree: the language units are written in, with its dictionary and checker; the referee that scores every test; the records; and one page of facts for every market.
2. Everything else that runs is an app on the app core he already has: the backtester, the trading node and the market reader. Each can be replaced, improved, or run in several versions.
3. A unit is one complete trading algorithm. Scripts check it at every door, the backtester tests it, and the node trades it with the same code.
4. Only the trading node sends orders. It trades on its own machine with only what is on that machine, keeps a stop at the broker on every position, heals itself after faults, and waits for him after a risk stop.
5. Only he promotes. The one automatic move is a unit's own risk rule stopping it.
6. His PC is home. Results, journals and readings come back to it when it is on, and nothing is lost while it is off.

I could write these, so F20 passes. Sentence 6 is true by design but not yet in code (R0-01, R0-02), and sentence 4 needs R0-05 and R0-09 to hold when a server dies or his PC is off.

## Appendix A. Cases with an owner but no handling line in the spine

INFERRED by reading every catalogue row's "Proof" against the spine: a case is listed when neither an AD nor its part's lines carry that handling or an equivalent. Most are Level 1 detail; the fix is R0-11's per-part table. Bold marks the five that matter at Level 0.

- **P1 QML:** QML-04 (flat time per streaming update), QML-13 (learned weights through a declared read surface), QML-17 (no implicit long and short mirror), QML-18 (honest entry price after the last input is knowable), QML-19 (closed bars only unless tick input is declared), QML-20 (higher-timeframe values at their close in the venue's day), QML-21 (a "no signal" result for every combiner), **QML-22** (no live unit-to-unit read), QML-25 (first-run interpreter check).
- **P2 the unit:** **UT-01** (R0-03), UT-09 (state schema mismatch starts cold, logged), UT-11 (warm-up source recorded, seam flagged), OP-03 (promotion shows what changed against live).
- **P3 the judge:** QB-11 (the model's training cutoff recorded), QB-22 (improving what-if filters counted as tries), MIS-11 (each proof says what it cannot fail on).
- **P4 records:** TN-25 (who accepts a spec change, R0-14), LD-13 (dividend events).
- **P5 journals:** JR-08 (backfilled rows marked), JR-14 (no orphan artifacts), JR-15 (trades without R flagged).
- **P6 the Library:** LD-03 (per-file stamp check), LD-04 (seams on the card), LD-11 (backups never block a live writer), LD-12 (cross-source offset check).
- **P7 contracts:** CA-10 (token expiry shown).
- **P8 agents:** AG-07 (sources enter as marked data), AG-11 (the same problems twice count as no progress), AG-12 (every number cites a tool receipt), AG-15 (the checker's answer leads with counts).
- **P9 workflows:** WF-07 (long work as a script step or a job).
- **P10 the app core:** **MA-02** (a new home starts after a machine dies, R0-05), MA-03 (examples built and tested in CI).
- **P11 QMB:** QB-05 (contract-by-contract replay with roll events), QB-15 (a zero-trade result labelled), QB-16 (the synthetic generator by class), QB-17 (accepted miss), QB-21 (bars built in the venue's day boundary), **QB-23** (the nightly replay needs the recorded feed, R0-08).
- **P12 the node:** **TN-04** (clones, R0-05), TN-07 (an exchange halt is a market event), TN-15 (a laptop sleep is logged and reconciled on wake), TN-23 (protection follows the filled quantity), TN-26 (close-only mode as an event), TN-31 (the cTrader app request starts on day one), TN-32 (setup measures the round trip).
- **P13 the MIS:** MIS-10 (the unit journal keeps what the unit computed).
- **P14 external:** EX-01 (last value kept per side), EX-02 (the book rebuilt after a reconnect), EX-06 (one market named across venues), EX-15 (the CFD against futures gap measured), EX-16 (the capability record refuses an unattended node where the venue bans it).
- **P15 DevOps and clocks:** DO-03 (an early packet starts OpenObserve on real events), DO-04 (known monitoring gaps closed or listed), CK-10 (baselines in venue session time), CK-13 (durations for 24/7 markets).
- **P0 the host:** OP-02 (the first real start as a named early step), OP-09 (the screen says the market is shut until when).

The 18 risk rows all have a place in "For the risk session", except RS-13 (a gap through the stop) and RS-18 (who sets leverage per unit), which are implied only.
