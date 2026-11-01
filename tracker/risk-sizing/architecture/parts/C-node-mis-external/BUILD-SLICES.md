# Build slices for Part C

Ordered, PR-sized slices a builder takes one at a time. Every slice keeps the shipped tests green (`just ci` on Windows, the Linux lanes) and runs the blast-radius check named for it (`BLAST-RADIUS.md`). A slice that changes a shipped test does it on purpose and names the test and the new value in its Verify line. The node comes late in the whole build (STATE midday ruling 35): slices C-01 to C-09 and C-24 make the host, records, MIS, read rows and links it stands on; C-10 is the smallest node that runs end to end. None of those waits on the node: Part B's records job (B15), which C-09 uses, tests on a fixture app volume and no longer waits on a node (R1-B-04). Dependencies on parts A and B name their slice ids as R1 merged them (`review/R1-findings.md`, check 3).

Commands run from the repository root of a build checkout. `just ci` is the shipped gate; the named test files are new in their slice.

Amended in the R1 fix round (`review/R1-FIXES-X1-C.md`): C-05 and C-12 are split into PRs (C-05a to C-05d, C-12a to C-12c); C-23 (promote and deploy) and C-24 (the core read rows) are new.

## C-01. Every machine proves its clock

- **Goal.** One clock probe; clock facts on every host heartbeat; doctor lines for clock, `tzdata` age and the next mismatch week.
- **Files.** `qmx-agents/packages/qmx-host/src/qmx_host/clock_probe.py` (NEW); `qmx-engine/src/qmx_engine/heartbeat.py` (optional `clock` field); `qmx-host/src/qmx_host/host.py` (writes it); the harness doctor lines; tests.
- **Depends on.** Nothing.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_clock_probe.py qmx-agents/packages/qmx-engine/tests/test_heartbeat.py -q` (a probe against a local SNTP stub returns its offset; a row with `clock` round-trips; an older row without it still loads); `just ci`.
- **He sees.** The doctor shows "Clock: 3 ms off time.windows.com" or "Windows Time is stopped: turn it on" with his button.

## C-02. Instrument, venue and account records

- **Goal.** The three kinds with the exact keys of `RECORDS.md` §2 (every key Part A's `CONTRACTS.md` §2.3 reads, under the same name; one class enum with underscores; `data_levels` in `qmx.data-level/1`); the CCXT public refresh template (Hyperliquid and Binance markets, no keys needed); `market_id`; the conversion check.
- **Files.** `qmx-agents/packages/qmx-library/src/qmx_library/kinds/instrument.schema.json`, `venue.schema.json`, `account.schema.json` (NEW); `qmx-engine/src/qmx_engine/templates/refresh-ccxt-records/` (NEW); tests.
- **Depends on.** Nothing in this part; the Library's kind loader as built.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-library/tests/test_market_kinds.py -q` (a record per class loads; the key-parity test asserts the instrument kind's keys include every key of Part A's §2.3 list and its class enum equals `RECORDS.md` §2's; no record carries `roll_rule`; the gold-at-two-sizes test gives equal R; a pips conversion without a pip definition is refused); the template's script step runs on a fixture market list; `just ci`.
- **He sees.** Instrument pages for perps (contract unit, funding interval, data levels) in the Library.

## C-03. Calendars as data and a per-market open check

- **Goal.** Calendar data packages (CME, index breaks, 24/7 with funding clocks) beside the forex one; the engine's `market_open` precheck becomes a per-market calendar check; the mismatch-week test.
- **Files.** `extensions/qmf-calendar-cme/`, `qmf-calendar-indices/`, `qmf-calendar-crypto247/` (NEW); `qmx-engine/src/qmx_engine/triggers/preflight.py` (the check takes a `market_id`); tests.
- **Depends on.** C-02 (records name their calendar).
- **Verify.** `uv run pytest extensions qmx-agents/packages/qmx-engine/tests/test_preflight_calendar.py -q` (crypto is open on Saturday; CME's daily break; every rule across 8 to 29 March and 25 October to 1 November 2026); `just ci`.
- **He sees.** A crypto template no longer waits for Monday.

## C-04. OpenObserve on real events

- **Goal.** Start OpenObserve on This PC with real host and app events; the host ships app logs from volumes; incidents exported; the note row redacted.
- **Files.** `qmx-host/src/qmx_host/app_logs.py` (NEW, the log shipper); `qmx-host/src/qmx_host/connect_logs.py` (no change to the binding); the note row's redaction; tests.
- **Depends on.** Nothing.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_app_logs.py -q` (a fake app's JSONL lines reach a stub OTLP endpoint; with the endpoint down, nothing blocks and drops are counted); a lane starts the pinned OpenObserve on loopback and queries one shipped line back; `just ci`.
- **He sees.** "Deep logs" opens with this PC's real events; "Telemetry: off" when off.

## C-05a. Core change 3: restart with back-off, opt-in

- **Goal.** `[breaker] restart = "backoff"` (Level 0's core change 3): a tripped app that opted in starts again with back-off (5 s doubling to 300 s), each trip and start logged; a `money` app restarts only its active signed version (MA-05).
- **Files.** `qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py` (`Breaker.restart`, default `never`); `supervisor.py` (the trip path); `qmx-agents/packages/qmx-apps/tests/test_restart_backoff.py` (NEW).
- **Depends on.** Nothing.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-apps/tests/test_restart_backoff.py -q` (a tripped app with `restart = "backoff"` starts again after 5 s and a second trip waits 10 s; an app without it stays down, as today; a `money` app restarts only its active signed version); `uv run pytest qmx-agents/packages/qmx-apps/tests -q` with the shipped breaker tests unchanged; `just ci`.
- **He sees.** Nothing yet; an app that crashes comes back by itself when it opted in.

## C-05b. Core change 4: a read-only market root for apps that declare it

- **Goal.** The supervisor hands `QMX_MARKET_ROOT` to an app whose manifest declares `data_reads = ["market"]`; writes there stay refused.
- **Files.** `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` (the app environment, `:598-632`); `qmx-agents/packages/qmx-apps/tests/test_data_reads.py` (NEW).
- **Depends on.** Nothing.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-apps/tests/test_data_reads.py -q` (an app declaring `data_reads = ["market"]` sees the root and reads a partition; an app without it gets the environment it gets today; a write under the root is refused by the bootstrap's audit hook); `uv run pytest qmx-agents/packages/qmx-apps/tests -q` unchanged; `just ci`.
- **He sees.** Nothing yet.

## C-05c. Core change 5: host facts in every app volume

- **Goal.** The host writes `road/host/facts.json` (`CONTRACTS.md` §5, `holdout` included) into each supervised app's volume before the app starts and on every change.
- **Files.** `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` (a facts hook the host passes in, called before start); `qmx-agents/packages/qmx-host/src/qmx_host/host.py` (composes the facts, the Settings `[data]` holdout among them); `qmx-agents/packages/qmx-apps/tests/test_host_facts.py` (NEW).
- **Depends on.** Nothing.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-apps/tests/test_host_facts.py -q` (the file exists before the app's first heartbeat; a Settings change to `[data] holdout` rewrites it; an app's own write under `road/` is still refused); the shipped road tests unchanged (`uv run pytest qmx-agents/packages/qmx-apps/tests -q`); `just ci`.
- **He sees.** Nothing yet.

## C-05d. Core change 6: a server reads declared app secrets from its vault

- **Goal.** On role `server` the host builds the control service with a secret reader over `<home>/vault/<name>` (owner-only), because keyring has no backend on a headless server.
- **Files.** `qmx-agents/packages/qmx-host/src/qmx_host/host.py`; `qmx-agents/packages/qma-harness/src/qma/harness/routes.py` (`control_service` takes the reader, `:116-123`); `qmx-agents/packages/qmx-host/tests/test_server_secrets.py` (NEW).
- **Depends on.** Nothing.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_server_secrets.py -q`, on Windows and Linux with keyring's fail backend forced (a fixture app declaring a secret starts with the vault reader; with the default reader it fails `startup_failed`, as `BLAST-RADIUS.md` C8 says); `just ci`.
- **He sees.** Nothing yet.

## C-06. The host route and the node link

- **Goal.** `POST /api/host/forward` with the five verbs (`apps.job` with optional `inputs`, refused to every principal but `operator` for a `money` app; `data.list` accepts `confirmed`, and Part B's B16 later adds the pin and the `verify` call behind it); `qmx_host.node_link` with the outbox and `issued_at`; `app_op` composed with `Placements`; the core `node` rows read through the node link (moving `node_state` off `qmn.doors`); the control server states the host build's version (CA-01).
- **Files.** `qmx-host/src/qmx_host/host_route.py`, `node_link.py` (NEW); `qmx-host/src/qmx_host/door.py` (one entry); `qmx-engine/src/qmx_engine/control_door.py:308`; `qmx-control/src/qmx_control/catalog.py` (rows `node_units`, `node_positions`, `node_journal_tail`, `node_passport`); `qmx-control/src/qmx_control/server.py:415` (the OpenAPI version from the package); `qmx-tools/src/qmx_tools/functions.py`, `service.py` (the caller moved); `qmx-tools/tests/test_tools.py` (changed on purpose, below); tests.
- **Depends on.** Nothing in this part; Part B's B1 for `inputs` reaching a job.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_host_route.py qmx-agents/packages/qmx-host/tests/test_node_link.py -q` (two hosts on two loopback ports with one pairing key: `heartbeats` answers; an agent pass on a `manage` operation is refused; an agent pass on `apps.job` of a fixture `money` app answers `refused_principal` and on a `runs` app runs with its `inputs`; a pass for another place is refused; a queued `pause` applies once when the far host returns; every answer carries `schema_version`; the OpenAPI document's version equals the package version); Level 0's `br10_host_pass_routes.py` and `br11_app_op_remote.py` rerun as tests (five host-pass routes; homed-here keeps the local path); `uv run pytest qmx-agents/packages/qmx-tools/tests/test_tools.py -q` with `qmx-tools/tests/test_tools.py:374-376` changed on purpose in this PR: the `node` server's count goes from 2 to 6 (the four new rows); `just ci`.
- **He sees.** The copilot's "node state" answers "no trading node is set up yet" instead of an error.

## C-07. Contract markets on This PC and the public data routes

- **Goal.** The CCXT read adapter opens to contract markets; the data-route port normalises Hyperliquid, Binance and Bybit public trades and books into the internal format.
- **Files.** `qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:330-339`; `packages/qmf-venue/src/qmf/venue/routes/` (NEW, the normaliser); tests.
- **Depends on.** C-02.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-broker/tests/test_ccxt_contracts.py packages/qmf-venue/tests/test_routes_normalise.py -q` (a perp's funding and open interest read; a recorded Hyperliquid trades frame normalises to `print` events with the aggressor side); Level 0 `br8_host_orders.py` reruns with no order call on the host; `just ci`.
- **He sees.** Perps positions, funding and open interest in his market tools.

## C-08. Reading blocks moved, the reading runner and the record

- **Goal.** `qmn/src/qmn/mis` moves to `packages/qmf-readings` unchanged in logic; "regime" becomes "volatility state"; the reading runner; reading records (with `source` and `machine` in the body) written through Part B's writer library; the golden replay.
- **Files.** `packages/qmf-readings/` (NEW, moved); `qmn/src/qmn/mis/` (removed after the move, its two internal callers moved: `regime_register.py:60-61`); tests moved.
- **Depends on.** Part A's reading card schema and catalogue entry form (A11); Part B's writer library (B8).
- **Verify.** `uv run pytest packages/qmf-readings -q` (the moved labelers' tests green; the runner over a recorded day writes records with every field of `CONTRACTS.md` §7, `source` and `machine` included; the golden replay compares unit, QMB and runner values per reading id and version); `just ci`.
- **He sees.** Nothing yet.

## C-09. The MIS app on This PC

- **Goal.** The `mis` app: `configure`, `status`, the bar, session, day and cross-market readings of the default packs from Library history; reading history harvested home by Part B's records job; the board artifact; sealed holdout months skipped.
- **Files.** `qmx-agents/apps/mis/` (NEW: `app.toml`, `server.py`, `pyproject.toml`, `uv.lock`); first-start card one-click enable; tests.
- **Depends on.** C-05a, C-05b, C-05c, C-08, C-03; Part B's records job (B15), which tests on a fixture app volume and does not wait on the node.
- **Verify.** `uv run pytest qmx-agents/apps/mis/tests -q` (configured on two fixture markets it publishes records for each reading the markets' levels allow, none for the rest; with the host facts' `holdout` on from a month, no record lands for that month or later; stopping it changes no unit); `just ci`.
- **He sees.** The MIS tab fills with readings for the markets he has data for, each with its freshness word.

## C-24. The core read rows `instrument_get` and `readings_query`

- **Goal.** The two rows of `CONTRACTS.md` §12 in the new core toolsets `instrument` and `readings`: an instrument record by market or venue and symbol at an instant; reading history over a required time window, the open month included, saying where the data stops. Agents and the slow-lane templates read readings only through this row.
- **Files.** `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py` (two `domain_fn` rows; `instrument` and `readings` join `CORE_TOOLSETS`); `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py` (the two functions); tests in `qmx-tools` and `qma-harness`.
- **Depends on.** C-02 (records), C-08 (the reading record); Part A's A8 (the harness derives its domain groups from the catalog, `qma-harness/src/qma/harness/tools.py:641`, `:668`, so a new toolset is served); Part B's B8 (the `journal-readings` envelope).
- **Verify.** `uv run pytest qmx-agents/packages/qmx-tools/tests/test_read_rows.py qmx-agents/packages/qma-harness/tests -q` (`instrument_get` returns the version in force at an instant from fixture records; `readings_query` over fixture `journal-readings` partitions returns rows in the window, pages by cursor, and a window past the data answers `data_ends_at`; a copilot chat's surface lists both rows); `qmx-tools/tests/test_tools.py:374-376` unchanged, because both rows sit in new toolsets; `just ci`.
- **He sees.** The copilot can tell him what the MIS read for a market last week, and the facts of any instrument.

## C-10. The smallest node: start it and see it started

- **Goal.** The `trading-node` app skeleton: the store, every operation answering (reads real, changes accepted into `desired` in arrival order, `superseded` for an older change), identity minted, never-raise, breaker values, no job declared, venues "not set up", node state "Ready, no units".
- **Files.** `qmn/src/qmn/app/` (NEW: `store.py`, `operations.py`, `identity.py`, `server.py`); `qmx-agents/apps/trading-node/` (NEW manifest and entry); tests.
- **Depends on.** C-05a (restart), C-05c (host facts), C-06 (node link), C-01 (clock facts); Part B's B8 (the writer library and its committed reader, which `journal_tail` reads with).
- **Verify.** `uv run pytest qmn/tests/test_app_operations.py qmn/tests/test_app_identity.py -q` (every operation through the supervisor's real `call` answers under 2 s with `instance.errors == 0`, bad arguments included; a `pause` whose `issued_at` is older than an applied `resume` for the same scope answers `superseded`, while an older `kill` still applies; a direct call without an op id gets one minted; the manifest declares no job; `journal_tail` called while the node is mid-write returns only whole lines and leaves the writer's file unchanged (Part B's X1B-NEW-1); a copied volume on another machine fingerprint refuses trading until `confirm_same_node`); `just ci`.
- **He sees.** "Start a trading node on This PC": one click, steps tick, the node card says "Ready, no units yet".

## C-11. The trading-node kind in the connect dialog, on This PC

- **Goal.** The kind's steps for the This PC placement (cTrader app request as a waiting step, the keys document through the key route, clock, install and enable with his signature, sign-in step present, round-trip measurement, self-test skeleton, passport, place row last).
- **Files.** `qmx-host/src/qmx_host/connect_node.py` (NEW kind), `connect.py` (registered in `KINDS`); tests.
- **Depends on.** C-10.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_connect_node.py -q` (a rerun after a kill at each step converges on one place row; the waiting step blocks only its own later steps); `just ci`.
- **He sees.** The setup list, with "Waiting for cTrader to approve your app" as a step that ticks when he pastes the id.

## C-12a. The node trades a dummy unit on the conformance venue

- **Goal.** The runtime: the feed keeper over the conformance venue client; units hosted through Part A's `construct_unit` and driven through Part B's shared unit handler; `deploy` with its files staged by the node link, compile after the answer and the G fingerprint check; warm-up; the order path with the protection gate; journal before dispatch; the encoder's `label`.
- **Files.** `qmn/src/qmn/app/runtime.py`, `feed_keeper.py` (NEW); `qmx-host/src/qmx_host/node_link.py` (staging into `data/deployments/<deployment_id>/in/`); `packages/qmf-venue/src/qmf/venue/encode.py` (`label`, length checks); `qmn/tests/test_protection_every_order.py` (NEW); tests.
- **Depends on.** C-10; Part A's A4 (loader) and A5 (`construct_unit`, `HostedUnit`); Part B's B5b (the shared unit handler `qmb/src/qmb/host/unit_handler.py`) and B8 (writer library). The G record is a fixture `test-report` in these tests; the real one comes from Part B's `behaviour_check` (B5b), and the promote action uses it.
- **Verify.** `uv run pytest qmn/tests/test_app_runtime.py qmn/tests/test_protection_every_order.py qmn/tests/test_app_feed_keeper.py -q`: the dummy unit opens and closes on the conformance venue with its stop at the broker; the quantity the conformance venue receives equals the sizer receipt's quantity after lot rounding (CA-03); `deploy` answers before a 40 s compile; a staged file missing or with another fingerprint refuses `deploy` naming it, and a 32 MB weights fixture, twice the old limit, deploys (no size limit); a session dropped mid-book shows `book_state = rebuilding` and no reader sees a half book until a fresh snapshot (EX-02); a socket silent past the heartbeat bound reconnects and no entry is placed until the session is ready (TN-19); `just ci`.
- **He sees.** Run locally against the test venue, the node card says "Trading, 1 unit".

## C-12b. Reconcile with attribution, and the network-cut drill

- **Goal.** Reconcile at start and on every reconnect with attribution (mine, foreign, untagged, twin); the UNKNOWN path with no blind resend.
- **Files.** `qmn/src/qmn/app/reconciler.py`, `attribution.py` (NEW); tests.
- **Depends on.** C-12a.
- **Verify.** `uv run pytest qmn/tests/test_app_attribution.py qmn/tests/test_app_unknown_drill.py -q`: a twin-tagged order stands the account down; an untagged position is protected and flagged; the drill (TN-01): the conformance venue drops the answer to a send, the node marks the stream UNKNOWN, reads open orders by client order id and positions by tag, does not resend, and ends with exactly one position; `just ci`.
- **He sees.** A position that is not the node's shows as "not ours, protected".

## C-12c. The paper lane and the stand-down table

- **Goal.** The per-unit paper lane (decisions and simulated fills, no orders, world `paper`); Level 0 AD-38's stand-down table, each row clearing as that table says; a risk stop written as the unit's `lifecycle` event (`by: risk_rule`).
- **Files.** `qmn/src/qmn/app/paper_lane.py`, `stand_down.py` (NEW); tests.
- **Depends on.** C-12a.
- **Verify.** `uv run pytest qmn/tests/test_app_paper_lane.py qmn/tests/test_app_stand_down.py -q` (a paper deployment sends no order and journals its trades with world `paper`; each stand-down row stops entries, keeps exits and broker stops, and clears by its rule; a risk stop lands one `lifecycle` event and waits for his click); `just ci`.
- **He sees.** The unit's journal shows its first paper trade.

## C-23. Promote and deploy: his click

- **Goal.** Spine AD-324: the host route `POST /api/units/promote` on This PC, his principal `operator` only; it records the move through Part B's host lifecycle writer (`qmx_host/lifecycle.py` `record_move`), which folds and refuses illegal moves, builds the deployment document from the Library (files by fingerprint, the G `test-report`, the starting numbers, the record snapshots) and asks `deploy` through the node link; parks and retires ask `withdraw`.
- **Files.** `qmx-agents/packages/qmx-host/src/qmx_host/promote.py` (NEW: the route and the deployment builder); `qmx-agents/packages/qmx-host/src/qmx_host/host.py` (mounts the route beside the seal move); `qmx-agents/packages/qmx-host/tests/test_promote.py` (NEW).
- **Depends on.** C-12a, C-12c (deploy, the paper lane), C-06 (node link), C-02 (records); Part B's B13 (`qmx_host/lifecycle.py`, over Part A's A9 `fold`) and B5b (the G record).
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_promote.py -q`: his principal promotes the dummy from tested to paper, which lands one lifecycle event and one deployment accepted on the conformance node with the G record's fingerprint and the unit's defaults; an `agent:x` principal answers `refused_principal`; draft to live answers `illegal_move`; a repeated op id lands nothing new; a promotion from paper to live carries the last values and watermark of fixture paper-lane calibration rows; a live move onto a live-world account on a host without the trading profile answers `trading_profile_off`, while one onto a demo account goes through; a park asks `withdraw`; `just ci`.
- **He sees.** "Promote to paper" on a tested unit's page, then the node card shows the unit warming up.

## C-13. Healing

- **Goal.** Inner supervisor with back-off, `CrashLoopFold` moved into `qmn/src/qmn/app/healing.py`, the stuck detector, `safe_to_restart`.
- **Files.** `qmn/src/qmn/app/healing.py` (NEW); tests.
- **Depends on.** C-12a, C-05a.
- **Verify.** `uv run pytest qmn/tests/test_app_healing.py -q` (an exception restarts the runtime; 5 in 10 minutes stands down alive; a frozen runtime exits the process and the supervisor restarts it with the kill level still in force; a risk stop survives a restart); `just ci`.
- **He sees.** "Healing" on the card and a Heals tab line, then "Trading" again.

## C-14. The first real start on his folder (OP-02)

- **Goal.** A named step he takes: the new host on his own QMX folder, his cTrader demo sign-in for the practice node's own trading app, the dummy unit promoted through his click onto a demo account, a complete passport, and the node's real journal coming home.
- **Files.** none new; a run script `tools/first_real_start.py` (NEW) that checks each fact and prints PASS or FAIL per line.
- **Depends on.** C-11, C-12a, C-12b, C-12c, C-13, C-23; Part B's B15; his sign-in (ruling 37: only this step waits on it).
- **Verify.** `python tools/first_real_start.py` (folder found, practice node Ready, demo session ready, test trade with stop placed, observed and closed, passport landed, and the practice node's real journal rows found in This PC's store through Part B's records job, the open month within `[records] open_harvest_s` plus a minute, R1-B-04).
- **He sees.** His own practice node trading the dummy unit on his demo account.

## C-15. cTrader demo probes and drills

- **Goal.** Prove `label` survives onto the position and through a partial close; record what cTrader does with a repeated `clientOrderId`; attribution on demo; the network-cut drill (TN-01) and the refresh drill (TN-05) on demo.
- **Files.** `qmn/probes/ctrader_demo/` (NEW scripts).
- **Depends on.** C-14.
- **Verify.** `python qmn/probes/ctrader_demo/run.py` prints PASS or FAIL per mark (`EXTERNAL.md` §2), including: the socket closed right after a send leaves exactly one position after reconnect, with no resend; a forced grant refresh stores the new grant before the old is discarded, the session is ready again, and a second refresher is refused.
- **He sees.** Nothing new; the passport gains "attribution proven on demo" and "refresh proven on demo".

## C-16. Hyperliquid through CCXT, on testnet

- **Goal.** The `ccxt` venue client, `VenueClientKind.ccxt`, the position-trigger protection form, cloid tags, the open-order margin, the agent wallet in the keys document; the testnet probe.
- **Files.** `qmn/src/qmn/venue/ccxt_client.py` (NEW); `qmn/src/qmn/venue/port.py`; `qmn/src/qmn/order/protection.py`; `qmn/probes/hyperliquid_testnet/` (NEW).
- **Depends on.** C-12a, C-12b; his testnet agent wallet for the probe only.
- **Verify.** `uv run pytest qmn/tests/test_ccxt_client.py -q` (mapping against a fake exchange with CCXT's method names; unmapped error is UNKNOWN); `python qmn/probes/hyperliquid_testnet/run.py` (`EXTERNAL.md` §3 marks).
- **He sees.** A Hyperliquid testnet binding on the practice node.

## C-17. A server

- **Goal.** The kind's server placement (shipped server steps first, then chrony, the node and MIS apps, keys entered in the server's own window, round trip, self-test on demo); the server's OpenObserve bound to its Tailscale address; the route and node link across two real hosts; the run-pass recheck between them; the node's Linux grant folder made machine-bound (spine AD-306).
- **Files.** `qmx-host/src/qmx_host/connect_node.py` (server steps); `qmx-host/deploy/openobserve.service` (`ZO_HTTP_ADDR`); `qmx-agents/packages/qmx-home/src/qmx_home/classes.py` (one rule before `:119`: `data/apps/*/data/grants/**` is `secret`); `qmx-agents/packages/qmx-apps/src/qmx_apps/volume.py` (`snapshot()` skips `data/grants`, beside the `data/tmp` skip at `:271`); tests and a lane script.
- **Depends on.** C-11 to C-13, C-05d (secrets on a server).
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_connect_node_server.py qmx-agents/packages/qmx-home/tests/test_classes.py qmx-agents/packages/qmx-apps/tests -q` (steps rerun-safe against a fake SSH runner; a grant file under a node volume's `data/grants/` is classed `secret`, is not sent by a backup and is not copied by a move snapshot, the checks of `BLAST-RADIUS.md` C11 as tests; the shipped qmx-home and qmx-apps tests unchanged); the lane `tools/lanes/two_hosts.py` on his server (heartbeats, `apps.ask status`, a queued pause, a PC-minted run pass reading data, a deployment whose files reach the server through the hub and stage before `deploy`).
- **He sees.** "London-1: Ready" on his PC, with its clock, round trip to cTrader and passport.

## C-18. Alarms and liveness

- **Goal.** The ntfy channel and the Healthchecks.io sink; setup cards for both destinations; the short list; open-calendar filtering.
- **Files.** `qmn/src/qmn/app/alarms.py` (NEW adapters over the kept organs); setup steps; tests.
- **Depends on.** C-12a; C-11 or C-17 for the cards.
- **Verify.** `uv run pytest qmn/tests/test_app_alarms.py -q` (a protection escalation reaches a stub ntfy endpoint with priority 5; a weekend stale feed sends nothing; a failed send is counted and trading continues).
- **He sees.** A test notification on his phone during setup.

## C-19. Updates to a server

- **Goal.** A node or MIS version published on This PC installs on the server from its Library replica at a safe point; host builds through the step runner only while `safe_to_restart`.
- **Files.** `qmx-host/src/qmx_host/app_updates.py` (NEW); tests.
- **Depends on.** C-17.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_app_updates.py -q` (two homes on one machine: a version replicated to the second installs with its expected hash; a mismatched contract version refuses new deployments and keeps trading, CA-06).
- **He sees.** "Update London-1" with "waiting for a safe moment" when trades are open.

## C-20. The shell cut

- **Goal.** Spine AD-323: move the kept names, repoint their tests, delete `qmn.host`, `seats`, `promotion`, `paper`, `doors`, `bench`, the rest of `observability`, the deploy recipes and the Grafana stack, with the tests of what is deleted.
- **Files.** `qmn/src/qmn/` (deletions), `qmn/src/qmn/app/` (moved names), `qmn/tests/` (repointed and deleted), `qmn/deploy/`.
- **Depends on.** C-14 (the new shell traded on demo), C-12b, C-12c, C-13.
- **Verify.** `uv run pytest qmn/tests/test_protection_every_order.py -q` before and after; `python tools/import_scan.py` on the head shows no importer of a deleted module; `just ci`.
- **He sees.** Nothing, except about 47,000 fewer lines.

## C-21. The live binding path

- **Goal.** The connect dialog's "bind a live account" steps (chats and agent steps off, `[host] trading_profile = true`), the node keeping a live-capable grant only then, the release and binding cards showing the two soaks, his signature on the live lane.
- **Files.** `qmx-host/src/qmx_host/connect_node.py` (bind-live steps); `qmx-host/src/qmx_host/trading_profile.py` (NEW: refusals for chats and agent steps); tests.
- **Depends on.** C-17, C-18.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_trading_profile.py -q` (with the profile on, a chat route is not mounted and an agent step placed there is refused; This PC refuses the setting; a live-capable grant is discarded when host facts say off and kept when on).
- **He sees.** "Bind a live account" ends with the soak card; going live is his click.

## C-22. The board inside the node (a Should)

- **Goal.** A host feed relay passes the `mis` instance's landed board to the node's `[feeds.board]`; units with a placement read use it with `stale_after` and fall back to every admitted market.
- **Files.** `qmx-host/src/qmx_host/feed_relay.py` (NEW); the node's feed handling; tests.
- **Depends on.** C-09, C-12a.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_feed_relay.py -q` (a landed board reaches the node; a stale board makes the unit use every admitted market).
- **He sees.** On the node page, which of a unit's markets the board favours now.

## Order, merged with parts A and B

As R1's check 3 merged it, with this round's splits: ground first (C-01, C-02, C-04, C-05a, C-05b, C-05c, C-05d, C-06); then C-03, C-07; C-08 and C-09 with the dictionary and the MIS on This PC; C-24 after Part A's A8; the node late: C-10, C-11, C-12a, C-12b, C-12c, C-23, C-13, C-14, C-15, C-16, C-17, C-18, C-19, C-20, C-21, C-22. No slice here needs a later one.
