# Build slices for Part C

Ordered, PR-sized slices a builder takes one at a time. Every slice keeps the shipped tests green (`just ci` on Windows, the Linux lanes) and runs the blast-radius check named for it (`BLAST-RADIUS.md`). The node comes late in the whole build (STATE midday ruling 35): slices C-01 to C-09 make the host, records, MIS and links it stands on; C-10 is the smallest node that runs end to end. Dependencies on parts A and B name the packet, not a number, because those parts number their own slices.

Commands run from the repository root of a build checkout. `just ci` is the shipped gate; the named test files are new in their slice.

## C-01. Every machine proves its clock

- **Goal.** One clock probe; clock facts on every host heartbeat; doctor lines for clock, `tzdata` age and the next mismatch week.
- **Files.** `qmx-agents/packages/qmx-host/src/qmx_host/clock_probe.py` (NEW); `qmx-engine/src/qmx_engine/heartbeat.py` (optional `clock` field); `qmx-host/src/qmx_host/host.py` (writes it); the harness doctor lines; tests.
- **Depends on.** Nothing.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_clock_probe.py qmx-agents/packages/qmx-engine/tests/test_heartbeat.py -q` (a probe against a local SNTP stub returns its offset; a row with `clock` round-trips; an older row without it still loads); `just ci`.
- **He sees.** The doctor shows "Clock: 3 ms off time.windows.com" or "Windows Time is stopped: turn it on" with his button.

## C-02. Instrument, venue and account records

- **Goal.** The three kinds and the CCXT public refresh template (Hyperliquid and Binance markets, no keys needed); `market_id`; the conversion check.
- **Files.** `qmx-agents/packages/qmx-library/src/qmx_library/kinds/instrument.schema.json`, `venue.schema.json`, `account.schema.json` (NEW); `qmx-engine/src/qmx_engine/templates/refresh-ccxt-records/` (NEW); tests.
- **Depends on.** Nothing in this part; the Library's kind loader as built.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-library/tests/test_market_kinds.py -q` (a record per class loads; the gold-at-two-sizes test gives equal R; a pips conversion without a pip definition is refused); the template's script step runs on a fixture market list; `just ci`.
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

## C-05. The mini-app core fixes that truly block

- **Goal.** `[breaker] restart = "backoff"` (opt-in); `QMX_MARKET_ROOT` for apps declaring `data_reads = ["market"]`; the host writes `road/host-facts.json` into app volumes; the server role's secret reader reads `<home>/vault/<name>`.
- **Files.** `qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py` (`Breaker.restart`); `supervisor.py` (restart after a trip with back-off; the environment variable; the host-facts write); `qmx-host/src/qmx_host/host.py` and `qma-harness/src/qma/harness/routes.py` (`control_service` takes a secret reader on a server); tests.
- **Depends on.** Nothing.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-apps/tests/test_restart_backoff.py qmx-agents/packages/qmx-apps/tests/test_data_reads.py -q` (a tripped app with `restart = "backoff"` starts again after 5 s and a second trip waits 10 s; an app without it stays down, as today; a `money` app restarts only its active signed version; an app declaring `data_reads = ["market"]` sees the root, others do not, and a write there is refused); `just ci`, with the shipped breaker and road tests unchanged.
- **He sees.** Nothing yet; an app that crashes comes back by itself when it opted in.

## C-06. The host route and the node link

- **Goal.** `POST /api/host/forward` with the five verbs; `qmx_host.node_link` with the outbox; `app_op` composed with `Placements`; the core `node` rows read through the node link (moving `node_state` off `qmn.doors`).
- **Files.** `qmx-host/src/qmx_host/host_route.py`, `node_link.py` (NEW); `qmx-host/src/qmx_host/door.py` (one entry); `qmx-engine/src/qmx_engine/control_door.py:308`; `qmx-control/src/qmx_control/catalog.py` (rows `node_units`, `node_positions`, `node_journal_tail`, `node_passport`); `qmx-tools/src/qmx_tools/functions.py`, `service.py` (the caller moved); tests.
- **Depends on.** Nothing in this part.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_host_route.py qmx-agents/packages/qmx-host/tests/test_node_link.py -q` (two hosts on two loopback ports with one pairing key: `heartbeats` answers; an agent pass on a `manage` operation is refused; a pass for another place is refused; a queued `pause` applies once when the far host returns); Level 0's `br10_host_pass_routes.py` and `br11_app_op_remote.py` rerun as tests (five host-pass routes; homed-here keeps the local path); `just ci`.
- **He sees.** The copilot's "node state" answers "no trading node is set up yet" instead of an error.

## C-07. Contract markets on This PC and the public data routes

- **Goal.** The CCXT read adapter opens to contract markets; the data-route port normalises Hyperliquid, Binance and Bybit public trades and books into the internal format.
- **Files.** `qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:330-339`; `packages/qmf-venue/src/qmf/venue/routes/` (NEW, the normaliser); tests.
- **Depends on.** C-02.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-broker/tests/test_ccxt_contracts.py packages/qmf-venue/tests/test_routes_normalise.py -q` (a perp's funding and open interest read; a recorded Hyperliquid trades frame normalises to `print` events with the aggressor side); Level 0 `br8_host_orders.py` reruns with no order call on the host; `just ci`.
- **He sees.** Perps positions, funding and open interest in his market tools.

## C-08. Reading blocks moved, the reading runner and the record

- **Goal.** `qmn/src/qmn/mis` moves to `packages/qmf-readings` unchanged in logic; "regime" becomes "volatility state"; the reading runner; reading records written through Part B's writer library; the golden replay.
- **Files.** `packages/qmf-readings/` (NEW, moved); `qmn/src/qmn/mis/` (removed after the move, its two internal callers moved: `regime_register.py:60-61`); tests moved.
- **Depends on.** Part A's reading card schema and catalogue entry form; Part B's writer library.
- **Verify.** `uv run pytest packages/qmf-readings -q` (the moved labelers' tests green; the runner over a recorded day writes records with all fields; the golden replay compares unit, QMB and runner values per reading id and version); `just ci`.
- **He sees.** Nothing yet.

## C-09. The MIS app on This PC

- **Goal.** The `mis` app: `configure`, `status`, the bar, session, day and cross-market readings of the default packs from Library history; reading history harvested home; the board artifact.
- **Files.** `qmx-agents/apps/mis/` (NEW: `app.toml`, `server.py`, `pyproject.toml`, `uv.lock`); first-start card one-click enable; tests.
- **Depends on.** C-05, C-08, C-03; Part B's harvest.
- **Verify.** `uv run pytest qmx-agents/apps/mis/tests -q` (configured on two fixture markets it publishes records for each reading the markets' levels allow, none for the rest; stopping it changes no unit); `just ci`.
- **He sees.** The MIS tab fills with readings for the markets he has data for, each with its freshness word.

## C-10. The smallest node: start it and see it started

- **Goal.** The `trading-node` app skeleton: the store, every operation answering (reads real, changes accepted into `desired`), identity minted, never-raise, breaker values, venues "not set up", node state "Ready, no units".
- **Files.** `qmn/src/qmn/app/` (NEW: `store.py`, `operations.py`, `identity.py`, `server.py`); `qmx-agents/apps/trading-node/` (NEW manifest and entry); tests.
- **Depends on.** C-05 (restart, host facts), C-06 (node link), C-01 (clock facts).
- **Verify.** `uv run pytest qmn/tests/test_app_operations.py qmn/tests/test_app_identity.py -q` (every operation through the supervisor's real `call` answers under 2 s with `instance.errors == 0`, bad arguments included; a copied volume on another machine fingerprint refuses trading until `confirm_same_node`); `just ci`.
- **He sees.** "Start a trading node on This PC": one click, steps tick, the node card says "Ready, no units yet".

## C-11. The trading-node kind in the connect dialog, on This PC

- **Goal.** The kind's steps for the This PC placement (cTrader app request as a waiting step, the keys document through the key route, clock, install and enable with his signature, sign-in step present, round-trip measurement, self-test skeleton, passport, place row last).
- **Files.** `qmx-host/src/qmx_host/connect_node.py` (NEW kind), `connect.py` (registered in `KINDS`); tests.
- **Depends on.** C-10.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_connect_node.py -q` (a rerun after a kill at each step converges on one place row; the waiting step blocks only its own later steps); `just ci`.
- **He sees.** The setup list, with "Waiting for cTrader to approve your app" as a step that ticks when he pastes the id.

## C-12. The node trades a dummy unit on the conformance venue

- **Goal.** The runtime: feed keeper over the conformance venue client, deploy with compile after the answer and the G-verdict fingerprint check, warm-up, the order path with the protection gate, journal before dispatch, reconcile with attribution, the per-unit paper lane, the stand-down table.
- **Files.** `qmn/src/qmn/app/runtime.py`, `reconciler.py`, `feed_keeper.py`, `attribution.py` (NEW); `packages/qmf-venue/src/qmf/venue/encode.py` (`label`, length checks); `qmn/tests/test_protection_every_order.py` (NEW); tests.
- **Depends on.** C-10; Part A's compiler, loader and G verdict; Part B's writer library.
- **Verify.** `uv run pytest qmn/tests/test_app_runtime.py qmn/tests/test_protection_every_order.py qmn/tests/test_app_attribution.py -q` (the dummy unit opens and closes on the conformance venue with its stop at the broker; `deploy` answers before a 40 s compile; a twin-tagged order stands the account down; an untagged position is protected and flagged); `just ci`.
- **He sees.** The node card says "Trading, 1 unit (practice)"; the unit's journal shows its first paper trade.

## C-13. Healing

- **Goal.** Inner supervisor with back-off, `CrashLoopFold` moved into `qmn/src/qmn/app/healing.py`, the stuck detector, `safe_to_restart`.
- **Files.** `qmn/src/qmn/app/healing.py` (NEW); tests.
- **Depends on.** C-12, C-05.
- **Verify.** `uv run pytest qmn/tests/test_app_healing.py -q` (an exception restarts the runtime; 5 in 10 minutes stands down alive; a frozen runtime exits the process and the supervisor restarts it with the kill level still in force; a risk stop survives a restart); `just ci`.
- **He sees.** "Healing" on the card and a Heals tab line, then "Trading" again.

## C-14. The first real start on his folder (OP-02)

- **Goal.** A named step he takes: the new host on his own QMX folder, his cTrader demo sign-in for the practice node's own trading app, the dummy unit on a demo account, a complete passport.
- **Files.** none new; a run script `tools/first_real_start.py` (NEW) that checks each fact and prints PASS or FAIL per line.
- **Depends on.** C-11, C-12, C-13; his sign-in (ruling 37: only this step waits on it).
- **Verify.** `python tools/first_real_start.py` (folder found, practice node Ready, demo session ready, test trade with stop placed, observed and closed, passport landed).
- **He sees.** His own practice node trading the dummy unit on his demo account.

## C-15. cTrader demo probes

- **Goal.** Prove `label` survives onto the position and through a partial close; record what cTrader does with a repeated `clientOrderId`; attribution on demo.
- **Files.** `qmn/probes/ctrader_demo/` (NEW scripts).
- **Depends on.** C-14.
- **Verify.** `python qmn/probes/ctrader_demo/run.py` prints PASS or FAIL per mark (`EXTERNAL.md` §2).
- **He sees.** Nothing new; the passport gains "attribution proven on demo".

## C-16. Hyperliquid through CCXT, on testnet

- **Goal.** The `ccxt` venue client, `VenueClientKind.ccxt`, the position-trigger protection form, cloid tags, the open-order margin, the agent wallet in the keys document; the testnet probe.
- **Files.** `qmn/src/qmn/venue/ccxt_client.py` (NEW); `qmn/src/qmn/venue/port.py`; `qmn/src/qmn/order/protection.py`; `qmn/probes/hyperliquid_testnet/` (NEW).
- **Depends on.** C-12; his testnet agent wallet for the probe only.
- **Verify.** `uv run pytest qmn/tests/test_ccxt_client.py -q` (mapping against a fake exchange with CCXT's method names; unmapped error is UNKNOWN); `python qmn/probes/hyperliquid_testnet/run.py` (`EXTERNAL.md` §3 marks).
- **He sees.** A Hyperliquid testnet binding on the practice node.

## C-17. A server

- **Goal.** The kind's server placement (shipped server steps first, then chrony, the node and MIS apps, keys entered in the server's own window, round trip, self-test on demo); the server's OpenObserve bound to its Tailscale address; the route and node link across two real hosts; the run-pass recheck between them.
- **Files.** `qmx-host/src/qmx_host/connect_node.py` (server steps); `qmx-host/deploy/openobserve.service` (`ZO_HTTP_ADDR`); tests and a lane script.
- **Depends on.** C-11 to C-13.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_connect_node_server.py -q` (steps rerun-safe against a fake SSH runner); the lane `tools/lanes/two_hosts.py` on his server (heartbeats, `apps.ask status`, a queued pause, a PC-minted run pass reading data).
- **He sees.** "London-1: Ready" on his PC, with its clock, round trip to cTrader and passport.

## C-18. Alarms and liveness

- **Goal.** The ntfy channel and the Healthchecks.io sink; setup cards for both destinations; the short list; open-calendar filtering.
- **Files.** `qmn/src/qmn/app/alarms.py` (NEW adapters over the kept organs); setup steps; tests.
- **Depends on.** C-12; C-11 or C-17 for the cards.
- **Verify.** `uv run pytest qmn/tests/test_app_alarms.py -q` (a protection escalation reaches a stub ntfy endpoint with priority 5; a weekend stale feed sends nothing; a failed send is counted and trading continues).
- **He sees.** A test notification on his phone during setup.

## C-19. Updates to a server

- **Goal.** A node or MIS version published on This PC installs on the server from its Library replica at a safe point; host builds through the step runner only while `safe_to_restart`.
- **Files.** `qmx-host/src/qmx_host/app_updates.py` (NEW); tests.
- **Depends on.** C-17.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_app_updates.py -q` (two homes on one machine: a version replicated to the second installs with its expected hash; a mismatched contract version refuses new deployments and keeps trading).
- **He sees.** "Update London-1" with "waiting for a safe moment" when trades are open.

## C-20. The shell cut

- **Goal.** Spine AD-323: move the kept names, repoint their tests, delete `qmn.host`, `seats`, `promotion`, `paper`, `doors`, `bench`, the rest of `observability`, the deploy recipes and the Grafana stack, with the tests of what is deleted.
- **Files.** `qmn/src/qmn/` (deletions), `qmn/src/qmn/app/` (moved names), `qmn/tests/` (repointed and deleted), `qmn/deploy/`.
- **Depends on.** C-14 (the new shell traded on demo), C-13.
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
- **Depends on.** C-09, C-12.
- **Verify.** `uv run pytest qmx-agents/packages/qmx-host/tests/test_feed_relay.py -q` (a landed board reaches the node; a stale board makes the unit use every admitted market).
- **He sees.** On the node page, which of a unit's markets the board favours now.
