# Blast radius of the shipped seams the Level 0 spine changes

Agent A0, 31 Oct 2026, skill `blast-radius`. For each shipped seam the spine changes: what the change does, the one fact it is safe because of, how far that fact was proven (1 said, 2 pointed at the line, 3 walked the failure, 4 ran it, 5 reproduced in the running app), the risks found, what was cleared, and the cheapest check before merge.

**How the code was run.** Against a scratch export of `origin/engine/base` `c93407ca` (`scratchpad/eb`, files compared with the read-only checkout ignoring line endings: `intents.py`, `door.py`, `dispatch.py`, `factory.py`, `conformance/__init__.py` identical), on Windows 11 with Python 3.14.6 in the export's own environments (`eb/.venv`; `eb/qmx-agents/.venv` synced with `uv sync --frozen --all-packages`). The read-only checkout `D:\QMX-worktrees\engine-base-read\` was only read (`git show`). Scripts live in this agent's scratchpad under `a0/br/` and run as `python -I <script> <export>`.

Scratchpad: `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\a0\br\`.

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

## Not proven here

- Plugin hooks firing under the Agent SDK in QMX's launch path (needs a running chat).
- The run-pass failure at a server's door after the merged stack (needs two hosts).
- Any order against cTrader or Hyperliquid (needs his sign-in; nothing in the build waits on it, ruling 37).
