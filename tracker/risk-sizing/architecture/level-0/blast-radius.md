# Blast radius of the shipped seams the Level 0 spine changes

Agent A0, 31 Oct 2026, skill `blast-radius`. For each shipped seam the spine changes: what the change does, the one fact it is safe because of, how far that fact was proven (1 said, 2 pointed at the line, 3 walked the failure, 4 ran it, 5 reproduced in the running app), the risks found, what was cleared, and the cheapest check before merge.

**How the code was run.** Against a scratch export of `origin/engine/base` `c93407ca` (`scratchpad/eb`, files compared with the read-only checkout ignoring line endings: `intents.py`, `door.py`, `dispatch.py`, `factory.py`, `conformance/__init__.py` identical), on Windows 11 with Python 3.14.6 in the export's own environments (`eb/.venv`; `eb/qmx-agents/.venv` synced with `uv sync --frozen --all-packages`). The read-only checkout `D:\QMX-worktrees\engine-base-read\` was only read (`git show`). Scripts live in this agent's scratchpad under `a0/br/` and run as `python -I <script> <export>`.

Scratchpad: `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\a0\br\`.

**Amended 2026-10-31 evening by agent X0** after review R0: items 10 to 14 added for the seams the R0 fixes change (the host route, `app_op`'s placements, the node's own trading grant, the Library kinds R0-17 named, the supervisor's call timeout), and items 3 and 5 extended. X0's scripts live in `...\scratchpad\x0\` and run as `python -I <script> <args>` with the export's agents environment (`eb/qmx-agents/.venv`); the export's `door.py`, `venue_session.py`, `app_op.py`, `forward.py` and `control_door.py` were compared with the read-only checkout ignoring line endings: identical.

## Summary

| # | Seam the spine changes | The one fact it is safe because of | Proven to step |
| --- | --- | --- | --- |
| 1 | QML's "the bot may not size" and CT-23's entry intent with no size (AD-18) | a CT-23 reader refuses an unknown contract format version; so a sized unit intent stamped format 3 can never be silently sized by the Book path. **Found on the way:** an unknown key is silently dropped, so a size must never travel as a new key | 4 |
| 2 | QML's factory seam, now fed by a compiler (AD-16) | `BotFactory` is a structural protocol; `construct_bot` accepts any object with a matching `construct`, so a compiled factory needs no change in QMB or the node | 4 |
| 3 | The conformance gate moved off the 1-2-3 slice onto recorded bars (AD-17) | `evaluate_layer2` is a pure verdict over an observations record; the slice enters only as a fingerprint | 4 |
| 4 | QMB's silent runner replaced by a runner that trades a unit (AD-34, AD-35) | a trading replay path already exists and fills, prices in R and ledgers a fixture bot through the same factory seam; the new runner is wiring, not a new loop. PR 204's runner set is a closed set checked at one line, so a new name is additive | 4 (replay), 2 (runner set) |
| 5 | QMN's seat door and the node's shell replaced (AD-36) | nothing outside `qmn/` imports the replaced shell except three named callers | 4 |
| 6 | The Library's kind check returns every problem; the `unit` kind gets a real schema (AD-29) | no non-test code reads a refusal's message text; 28 test lines do, so the first problem stays the message head | 4 |
| 7 | The money app gate for the trading node (AD-33) | publishing a `money` app needs his bound signature; a restart of the active signed version needs none | 4 (publish), 3 (restart) |
| 8 | CCXT reads opened to contract markets on the PC (AD-41) | no QMX host source contains an order call; opening reads cannot place an order | 4 |
| 9 | Hyperliquid through the pinned CCXT (AD-41) | CCXT 4.5.85's `hyperliquid` class declares orders, positions, funding, open interest, books, trigger and reduce-only orders and a sandbox | 4 offline; venue behaviour unproven |
| 10 | One more host-pass route on every host (AD-46) | the door admits a host pass only on a closed route set, and every admitted route verifies the pass itself; one added entry changes no other route's answer | 4 |
| 11 | `app_op` composed with its `Placements` (AD-46) | for an app homed on the asking machine the routed path is the same local run as today; only an app homed elsewhere goes `remote`, or waits `placement` when unreachable | 4 |
| 12 | The node keeps its own trading grant (AD-37, ruling 135 row) | the host's cTrader paths read, replace and delete only `qmx/token/ctrader-app` and read only `qmx/read/ctrader-app`, so a grant the node keeps under another name in its own store never meets the host's refusal, and the refusal's tests stay unchanged | 4 (scan) |
| 13 | R0-17's retirement of `bot` and `strategy` (rejected) | a save of a retired kind is refused, and shipped tests and the registry migration save those kinds, so retiring them breaks shipped tests | 3 |
| 14 | Node operations reached by `apps.ask` (AD-33, X1) | the supervisor stops an app whose tool call passes 30 s, so a node operation must answer fast and do slow work after the answer | 2 |

## 1. Sizing: CT-23 format 3, never a new key

**What changes.** Units own their sizing (STATE correction 2). The spine routes a unit's sized entry as a new CT-23 contract format version (3); the Book path (formats 1 and 2) stays.

**Where grep stops.** `parse_inbound_intent` (`packages/qmf-risk/src/qmf/risk/door.py:936-1010`) refuses `requested_r` (`:912-933`), refuses an unknown `contract_format_version`, and by design ignores unknown keys under a known version ("an unknown optional field never breaks a format-1 consumer", its docstring). QML's `accept_intents` (`qml/src/qml/protocol/intents.py:148-210`) guards `requested_r` and Book-side fields, then calls the same parser.

**Proof (step 4).** `br1_ct23_sizing.py` builds a real `EntryIntent` (the example bot's construction) and feeds six variants to both doors:

```text
A plain entry: ACCEPTED type=RiskEvaluationRequest
B entry + requested_r: REFUSED category=invalid input field=requested_r
C entry + requested_quantity (a unit size under a new key): ACCEPTED type=RiskEvaluationRequest
   EntryIntent fields after parse: ['instrument', 'direction', 'reason_code', 'execution_target', 'proposed_r', 'cited_evidence', 'advisory_stop_proposal']
   size survived the parse: False
D entry stamped contract_format_version=3: REFUSED category=unsupported capability field=contract_format_version
E QML accept_intents, mapping + requested_quantity: ACCEPTED type=tuple
F QML accept_intents, mapping stamped version 3: REFUSED category=unsupported capability field=contract_format_version
```

**Risks confirmed.** A size sent as a new key is dropped silently by both doors and the Book would size the trade (cost: wrong position size, silent; odds: high if a builder takes the obvious path). Closed by AD-18.

**Cleared.** The format-3 stamp fails closed at both doors today; no change to the Book path is needed for it to stay safe.

**Before merge.** Keep `br1_ct23_sizing.py`'s cases C, D, E and F as tests in the packet that adds format 3: C and E pin that the old doors still drop unknown keys (so nobody relies on them), D and F pin the fail-closed refusal, and a new case sends a format-3 unit intent end to end through QML, the node's door and a demo order with the size intact.

## 2. The factory seam takes a compiled factory

**What changes.** QML's compiler emits the factory QMB and the node already drive.

**Proof (step 4).** `br2_factory_seam.py` builds a factory class at run time (`type(...)`, not hand-written in a module), checks it against the protocol, hosts it and drives it through the example's golden slice; then lists every caller of `construct_bot` and `restore_bot` outside tests:

```text
structural BotFactory: True
construct_bot accepted the compiled factory: True HostedBot
driven through the slice: True
construct_bot callers outside tests: ['qmb/src/qmb/host/adapter.py:59', 'qml/src/qml/conformance/harness.py:122', 'qml/src/qml/protocol/factory.py:300', 'qmn/src/qmn/seats/host.py:255']
restore_bot callers outside tests: ['qml/src/qml/conformance/harness.py:165']
direct .construct( calls in qmb/qmn src: []
```

**Risks.** The node's caller sits in `qmn/seats/host.py`, which the shell replacement deletes (item 5): the new node shell must call `construct_bot` too, not the factory directly. Low odds, caught by the first demo run.

**Cleared.** No host calls `.construct(` directly, so nothing bypasses `construct_bot`'s assignment check and intent door.

## 3. The conformance gate on recorded bars

**What changes.** Checker layer G runs a compiled unit over a recorded slice in QMB's sandbox instead of three instants valued 1, 2, 3.

**Proof (step 4).** `br3_layer2_recorded.py` collects the example's real Layer 2 observations, then re-labels them with a recorded-slice fingerprint and feeds the unchanged `evaluate_layer2`:

```text
golden slice instants: 3 | distinct frame values: [... 'value': 1 ..., ... 'value': 2 ..., ... 'value': 3 ...]
loaded_in_isolation stamped by the in-process collector: True
verdict on golden-slice observations: pass
verdict on the same observations re-labelled as a recorded slice: pass | slice fingerprint carried: fp1:sha256:75ffbef6236e3
differing second run on the recorded slice: fail golden_slice_determinism
```

**Risks confirmed.** The in-process collector stamps `loaded_in_isolation=True` itself (`qml/src/qml/conformance/layer2.py:321`, and the run above). Any verdict collected in-process proves nothing about isolation. Closed by AD-17: layer G's observations are collected only inside QMB's sandbox (`qmb/src/qmb/host/runner.py:72-85`).

**Cleared.** The six checks and their verdict need no change; only a collector that drives real bars is new (`collect_layer2_observations` generates the golden slice internally at `layer2.py:312`).

**What the verdict cannot prove (R0-03, added by X0).** The verdict's checks are imports, isolation, no book, permitted intent kinds, determinism, state restore and the source manifest (`qml/src/qml/conformance/layer2.py:215-298`). None looks at trades, so a unit that is always long, whose exit never fires, or whose signal is constant passes on recorded bars exactly as it passes on three instants. AD-17 adds the behaviour report beside the verdict (trade count, exits fired, signal not constant, a shuffled-day control), all warnings. **Before merge:** the dummy unit and three broken twins (always long, an exit that cannot fire, a constant signal) through layer G; the verdict passes all four and the report names each twin's fault.

## 4. A runner that trades a unit

**What changes.** PR 204's only runner is `silent`. The spine needs a runner that trades a compiled unit on Library data.

**Proof of the replay path (step 4).** Two fixture tests that trade through `execute_recorded_replay_request` (`qmb/tests/test_replay_execution.py`):

```text
$ python -m pytest qmb/tests/test_replay_execution.py -q -x -p no:cacheprovider -k "economic_terminal_path or nofill_control"
9 passed in 108.64s (0:01:48)
```

The economic test asserts one closed trade with realised money -106, fees 2, `realized_r` -53/50 (-1.06R) and a durable terminal ledger line (`test_replay_execution.py`, assertions at lines 213 to 231 of the file).

**The runner set (step 2).** `origin/build/wu4:qmb/src/qmb/host/backtest_door.py:60` `RUNNERS: Final[frozenset[str]] = frozenset({"silent"})`, checked at `:142-143` (`if runner not in RUNNERS: return invalid(...)`). A new runner name is additive; configs naming `silent` keep working.

**Risks.** The trading path today takes its inputs from Python fixtures (`qmb/tests/replay_fixture_support.py:297-346`, G1 §3.3); making them data is the real work (AD-35). The typed-partition entry is missing (G1 §4.3). R exists in exit records and is not surfaced in results (G1 §4.4). All three are build items, not blast radius.

**Before merge.** The dummy unit's golden run through the new runner, with an identical trade list on rerun (the conformance pack's first golden).

## 5. Replacing the node's shell

**What changes.** The node keeps its organs and replaces its shell (host, seats, promotion, Book paper, doors, bench, observability beyond the heartbeat).

**Proof (step 4).** `br4_node_shell.py` walks every Python file in `packages`, `extensions`, `qml`, `qmb`, `qmn`, `qmx-agents`, `tools` and `scripts` with `ast`:

```text
qmn.seats: importers outside qmn/ -> []
qmn.promotion: importers outside qmn/ -> []
qmn.paper: importers outside qmn/ -> []
qmn.doors: importers outside qmn/ -> ['qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py', 'qmx-agents/packages/qmx-tools/src/qmx_tools/service.py', 'qmx-agents/packages/qmx-tools/tests/test_tools.py']
qmn.host: importers outside qmn/ -> []
qmn.bench: importers outside qmn/ -> []
qmn.observability: importers outside qmn/ -> []
kept organs imported outside qmn/: {}
kept organ imports replaced part: qmn.capital -> qmn.paper ['qmn/src/qmn/capital/bench_fold.py', 'qmn/src/qmn/capital/kill_line.py']
kept organ imports replaced part: qmn.mis -> qmn.promotion ['qmn/src/qmn/mis/regime_register.py']
```

**The callers to move in the same wave.** `qmx_tools/functions.py:10` (`from qmn.doors.api import read_status`) and `qmx_tools/service.py:17` (`DoorRuntime`), the agent's node-state tool; `qmn/capital/kill_line.py:38` and `bench_fold.py:32` (`route_protective_demotion` from `qmn.paper.demotion`); `qmn/mis/regime_register.py:60-61` (`qmn.promotion.hub`).

**Risks.** The kill line routes a breach through the Book paper's demotion: deleting `qmn.paper` without moving that call would break the kill line (cost: protection lost; odds: certain if missed). The scan names it. The four `host` modules G4a could not classify (`runtime_risk_gate`, `fencing`, `lineage_persist`, `registry_mint`) are inside `qmn.host` and leave with it; that only one of them is re-exported for a kept organ was not found by this scan (cleared at step 4 for outside importers, step 2 inside).

**Before merge.** A test that every order the node places carries its stop at the broker, run before and after the deletion (catalogue TN-34); the scan rerun on the PR's head with an empty outside-importer list.

**Added by X0 (R0-09, R0-10).** Two modules of the otherwise replaced `qmn.observability` package stay as organs: `liveness.py` (the outbound alive-ping) and `alerts.py` (the closed push list and its `NotificationChannel` port). The scan must treat them as kept, so its outside-importer check covers only the rest of the package. The kill line is per binding (`qmn/capital/kill_line.py:1-9`); after its call into `qmn.paper.demotion` is moved, a breach acts through the labelled placeholder of AD-36 (no new entries for that binding, a risk stop). **Before merge:** a test that a breach stops new entries for that binding and leaves its exits and broker stop in place, before and after the deletion.

## 6. The Library's kind check

**What changes.** The `unit` kind gets a real schema; the check returns every problem; a kind file may name a checker.

**Proof (step 4).** `br6_library_validator.py`:

```text
unit kind fields schema: {'type': 'object', 'properties': {}}
unit kind accepted arbitrary fields: True
trade kind refusal (two bad fields given): schema_invalid | schema_invalid: trade: 'account' is a required property
non-test code comparing a refusal message as text: []
test lines comparing message text: 28
```

**Risks.** Changing the message's head would break 28 shipped test assertions (ruling 52: every change keeps the shipped tests green). Closed by AD-29: the first problem stays the message head; the full list rides a separate field.

**Cleared.** No production code parses refusal text (`qmx_library/kinds/__init__.py:46-55` raises with `problems[0].message`).

## 7. The trading node as a money app

**What changes.** The node is the one `money` app allowed an order path.

**Proof (step 4, publish).** `pytest packages/qmx-apps/tests/test_road.py -k risk_rules_signature` in the export: `3 passed in 16.54s`; for `money`, publishing without a signature raises `signature_required`, with the signature lands `stage live` and records `proposal_only: True` (`test_road.py:181-197`).

**Restart (step 3).** `qmx_apps/supervisor.py:542-547` refuses to start a `money` app only when no active signed version exists; a restart of the active version passes that check. The test fixture fakes `start`, so this was walked in code, not run.

**Risks.** The recorded word `proposal_only` (`qmx_apps/road/__init__.py:360`) no longer describes a node that sends orders. It is evidence text, not a capability filter (only one other reader, `qmx_broker/server.py:71`, sets it as metadata). Level 1 C replaces the word for the node with the order capability AD-33 names, surgically.

## 8. CCXT reads opened to contract markets

**What changes.** The PC's CCXT adapter stops refusing contract markets for reads (`qmx_broker/adapters.py:330-339`).

**Proof (step 4).** `br8_host_orders.py` scans every call named like an order (`create_order`, `cancel_order`, `edit_order`, the cTrader order requests and others):

```text
order calls in QMX host source: []
RESULT: order calls exist only outside the host (node and venue packages, tests); opening the CCXT read filter adds no order path.
```

## 9. Hyperliquid through the pinned CCXT

**Proof (step 4, offline).** `br9_ccxt_hyperliquid.py` in the agents environment:

```text
ccxt version: 4.5.85
{'createOrder': True, 'cancelOrder': True, 'editOrder': True, 'fetchPositions': True, 'fetchFundingRate': True, 'fetchOpenInterest': True, 'fetchOrderBook': True, 'setLeverage': True, 'sandbox': True, 'createTriggerOrder': True, 'createStopLossOrder': None, 'createReduceOnlyOrder': True, 'watchTrades': None, 'watchOrderBook': None}
pro streaming class present: True
```

**Unproven.** Whether the venue keeps a reduce-only trigger order as a resting stop that survives the node's death, and how it behaves after `scheduleCancel`. The streaming methods live on the `ccxt.pro` class (present). A testnet probe in Level 1 C decides; until then catalogue TN-09 stays below full marks.

## 10. One more host-pass route (AD-46)

**What changes.** Every host serves `POST /api/host/forward`, and the door's `host_pass_call` admits a host pass on it. The route verifies the pass against its own host name, applies the claimed principal, and answers a closed verb set (`apps.ask`, `apps.job`, `heartbeats`, `data.list`, `data.fetch`).

**The one fact.** The door admits a host pass only on the routes in its set, and each admitted route checks the pass itself (`qmx_host/door.py:166-179`; the begin and code routes check at `qmx_host/venue_session.py:240-243`; the forward route at `qmx_engine/service/forward.py:378-384`). Adding one entry leaves every other route's answer as it is.

**Proof (step 4).** `br10_host_pass_routes.py` imports the shipped door and asks `host_pass_call` about seven routes, with and without the pass header:

```text
host-pass route set: [('GET', '/api/engine/forward/stream'), ('POST', '/api/engine/forward'), ('POST', '/api/venue/ctrader/begin'), ('POST', '/api/venue/ctrader/code')]
run-pass route: ('POST', '/api/data/read')
POST /api/venue/ctrader/begin           pass admitted=True  no pass=False
POST /api/venue/ctrader/code            pass admitted=True  no pass=False
POST /api/engine/forward                pass admitted=True  no pass=False
GET  /api/engine/forward/stream         pass admitted=True  no pass=False
POST /api/data/read                     pass admitted=False  no pass=False
POST /api/apps/trading-node/call        pass admitted=False  no pass=False
POST /api/host/forward                  pass admitted=False  no pass=False
```

This is also R0-01's evidence run: no route carries a host pass to data or to an app operation today.

**Risks.** (1) A host pass carries the caller's claimed principal, so any host holding the pairing key can claim `user`. That is the same trust the engine's forward route already gives `inbox.resolve` (`qmx_engine/service/api.py:165-166`); cost: a stolen pairing key could pause or flatten a node; odds: low; the pairing key never leaves the two machines (engine AD-12). (2) A builder who lets the route answer any app tool, not only declared operations, widens it past the catalog. The catalog builds a row only from declared operations (`qmx_apps/manifest.py:130-133`), and `apps.ask` must go through the same declaration.

**Before merge.** `br10` rerun showing exactly five admitted routes; a test that an agent principal's pass is refused on a `manage` operation; a test that a pass minted for another host's name is refused (`wrong_engine`, `qmx_engine/service/forward.py:128-129`).

## 11. `app_op` with its placements (AD-46)

**What changes.** `qmx_engine/control_door.py:308` composes `AppOp` with no `Placements`, so every `app_op` runs locally and a node homed on a server is refused `not_home` by that machine's supervisor (`qmx_apps/supervisor.py:527-532`). The fix composes it with its `Placements`, whose `remote` asks the home through AD-46's `apps.job`.

**The one fact.** For an app homed on the asking machine, `AppOp._route` with `Placements` takes the same local path as without them; only an app homed elsewhere goes `remote`, or waits `placement` when the home is unreachable (`qmx_engine/nodes/app_op.py:121-145`).

**Proof (step 4).** `br11_app_op_remote.py` drives the shipped `AppOp._route` with a fake runner and fake placements:

```text
no placements (as composed today): {'ran': 'local', 'app': 'trading-node', 'job': 'status'}
homed here: {'ran': 'local', 'app': 'trading-node', 'job': 'status'}
homed on a server: {'ran': 'remote', 'home': 'ldn-1'}
server unreachable waits: True placement
no remote door: placement_unreachable
calls: [('local', 'trading-node', 'status'), ('local', 'trading-node', 'status'), ('remote', 'ldn-1', 'trading-node', 'status')]
```

**Cleared.** An app that never moved reads its home as this machine (`qmx_apps/supervisor.py:1050-1055`), so every app on This PC keeps today's path.

**Before merge.** `br11`'s cases as a test in the engine package; the engine's shipped `app_op` tests green.

## 12. The node keeps its own trading grant (AD-37)

**What changes.** The node app exchanges its own sign-in code with its machine's trading registration and keeps the pair in its own store. The host's refusal of live-capable grants, its token name and its tests stay as built.

**The one fact.** The host's cTrader read and sign-in paths touch only two key names: `qmx/token/ctrader-app` (read, replace, delete) and `qmx/read/ctrader-app` (read). A pair the node keeps under another name never meets the refusal.

**Proof (step 4, a scan of the shipped source).** `br12_token_names.py`:

```text
service.py {'CTRADER_TOKENS': ['delete:248', 'read:253', 'read:271', 'read:282', 'delete:326', 'read:343', 'delete:344', 'replace:351', 'read:352']}
venue_session.py {'CTRADER_APP': ['read:193'], 'TOKEN_NAME': ['replace:289', 'delete:453']}
CTRADER_TOKENS = "qmx/token/ctrader-app"
```

(`TOKEN_NAME` is `CTRADER_TOKENS`, `qmx_host/venue_session.py:81`.)

**Risks confirmed.** (1) A practice node that kept its demo-trade grant under `qmx/token/ctrader-app` would share the host's slot: the host's next sign-in or refresh replaces or deletes it (`service.py:248`, `:351`). Cost: the practice node loses its session; odds: high if a builder reuses the name. Closed by AD-37's naming rule. (2) A `connections` row whose `credential_ref` named the node's entry would route the host's reads through the node's grant (`qmx_broker/service.py:176`). Closed by "no `connections` row references it".

**Before merge.** A test that the host's connection list refuses a `credential_ref` naming a `trading-node` grant; the shipped refusal tests (`qmx-broker/tests/test_pc_home.py`, `test_refresh.py`; `qmx-host/tests/test_pc_home.py`, `test_refresh.py`) green and unchanged.

## 13. Retiring `bot` and `strategy` (R0-17, rejected)

**What R0 proposed.** Set `retired` on the `bot` and `strategy` kind files.

**The fact that stops it (step 3).** A save of a retired kind is refused with `unknown_kind` (`qmx_library/store.py:966-967`, `kinds/__init__.py:47-48`). Shipped tests save `strategy` items (`qmx-control/tests/test_library_store.py:26`, `test_library_runs_cache.py:32`, `:41`, `:55`, `test_control.py:407`), and the registry migration maps bots and strategy families into those kinds (`qmx_library/migrate/from_registry.py:32-33`). Retiring them would break those tests (ruling 52). Not run: walked from the refusal line to each save.

**Cleared instead.** The unit path never writes `bot` or `strategy`, pinned by a test (AD-29); retirement waits for the PR that moves the migration and those tests.

## 14. Node operations under the supervisor's call timeout (AD-33)

**The fact (step 2).** The supervisor's `call` waits 30 s and then stops the app (`qmx_apps/supervisor.py:957-963`).

**Risk confirmed.** A `deploy` that compiled the unit and verified its snapshots inside the call could pass 30 s and stop the trading node. Cost: the node is down until it heals; odds: medium on a slow server. Closed by AD-33: a deploy is accepted as desired state and compiled after the answer.

**Before merge.** A test that `deploy` answers before it compiles, with a compile that sleeps past 30 s in the test.

## Not proven here

- Plugin hooks firing under the Agent SDK in QMX's launch path (needs a running chat).
- The run-pass failure at a server's door after the merged stack (needs two hosts).
- AD-46's route end to end between two hosts, and This PC reaching a server's OpenObserve over the tailnet (need two hosts).
- cTrader's `label` surviving onto the position, its length limit, and Hyperliquid's `cloid` on every order kind (need demo and testnet sign-ins).
- Any order against cTrader or Hyperliquid (needs his sign-in; nothing in the build waits on it, ruling 37).
