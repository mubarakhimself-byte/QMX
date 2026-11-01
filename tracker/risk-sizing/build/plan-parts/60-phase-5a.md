## Make every machine prove its clock (C-01)

Phase 5, the trading node and external connections. Part C slice C-01, Part C `DEVOPS-CLOCKS.md`, Level 0 AD-10 and AD-43, lead's call LC-X1-03. Ruling 35 (the node checks that things work). Real step none. Done when one clock probe exists, every host heartbeat carries optional clock facts read tolerantly, and the doctor shows the clock, the `tzdata` age and the next mismatch week.

**Depends on.** Nothing.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/clock_probe.py` and `qmx-agents/packages/qmx-host/tests/test_clock_probe.py`.
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/heartbeat.py` (an optional `clock` field, and readers that ignore fields they do not know, because the shipped models forbid unknown fields at `:70`, `:85` and `:101`) and `qmx-agents/packages/qmx-engine/tests/test_heartbeat.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py` (writes the clock facts) and the doctor lines in `qmx-agents/packages/qma-harness/src/qma/console.py`, which the builder confirms is where the doctor lives.

**Build.**

- [ ] Write the probe against an SNTP source, the heartbeat field, and three doctor lines with his button to turn on Windows Time.

**You see.**

- [ ] The doctor says "Clock 3 ms off time.windows.com", or "Windows Time is stopped, turn it on" with a button for his click.

**Verify, unit.**

- [ ] A probe against a local SNTP stub returns its offset. A row with `clock` round-trips. An older row without it still loads. A newer row with an unknown field loads in an older reader. Run `uv run pytest qmx-agents/packages/qmx-host/tests/test_clock_probe.py qmx-agents/packages/qmx-engine/tests/test_heartbeat.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The probe against a local SNTP stub set 120 ms off. Save `c01-offset.log`. Pass when it reports 120 ms within 5 ms.
- [ ] Lane 3. A heartbeat row with `clock` and one with an extra unknown field. Save `c01-tolerant.log`. Pass when both load.
- [ ] Lane 4. The doctor on This PC with Windows Time stopped on a scratch profile, or its status mocked. Save `c01-doctor.log`. Pass when the line says it is stopped and names the fix.
- [ ] Lane 5. The doctor's `tzdata` line. Save `c01-tzdata.log`. Pass when it shows the pinned version, its age, and the next mismatch week.
- [ ] Lane 6. The shipped heartbeat tests. Save `c01-heartbeat.log`. Pass when they pass unchanged.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds for one probe.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case, on clocks. The blast-radius fact is that an older reader loads a newer heartbeat row (LC-X1-03).

@merge

## Start OpenObserve on real events (C-04)

Phase 5, the trading node and external connections. Part C slice C-04, Part C `DEVOPS-CLOCKS.md`, Level 0 AD-42. Ruling 42 (OpenObserve self-hosted, agents read-only, build on what the wrap-up session shipped). Real step none. Done when the pinned OpenObserve starts on This PC with real host and app events, the host ships app logs from volumes, incidents export, and the note row is redacted.

**Depends on.** Nothing.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/app_logs.py` (the log shipper) and `qmx-agents/packages/qmx-host/tests/test_app_logs.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py` (starts the shipper). `qmx-agents/packages/qmx-host/src/qmx_host/connect_logs.py` keeps its binding unchanged.

**Build.**

- [ ] Ship each app's JSONL log lines through the one telemetry switch, with drops counted and nothing blocking, and redact the note row.

**You see.**

- [ ] "Deep logs" opens with this PC's real events, or says "Telemetry off" when it is off.

**Verify, unit.**

- [ ] A fake app's JSONL lines reach a stub OTLP endpoint. With the endpoint down, nothing blocks and drops are counted. Run `uv run pytest qmx-agents/packages/qmx-host/tests/test_app_logs.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A fake app's log lines with a stub OTLP endpoint. Save `c04-ship.log`. Pass when every line arrives.
- [ ] Lane 3. The same with the endpoint down. Save `c04-down.log`. Pass when the app keeps running and the drop count rises.
- [ ] Lane 4. Start the pinned OpenObserve on loopback and query one shipped line back. Save `c04-openobserve.log`. Pass when the line comes back.
- [ ] Lane 5. Telemetry off. Save `c04-off.log`. Pass when nothing is sent and the state reads off.
- [ ] Lane 6. A note row holding a key-shaped string. Save `c04-redact.log`. Pass when the stored row shows it redacted.
@menu

**Verify, perf.**

- [ ] Metric. Log lines per second the shipper sends without drops.
- [ ] Probe. Lane 2 at rising rates.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that `connect_logs.py`'s loopback binding is unchanged (`qmx_host/connect_logs.py:186-188`).

@merge

## Let a server read an app's declared secrets from its vault (C-05d)

Phase 5, the trading node and external connections. Part C slice C-05d, mini-app core change 6 of Level 0 AD-33, Level 0 AD-37. Rulings 46 and 53. Real step none. Done when, on role `server`, the host builds the control service with a secret reader over `<home>/vault/<name>` (owner-only), because keyring has no backend on a headless server.

**Depends on.** Nothing.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py` and `qmx-agents/packages/qma-harness/src/qma/harness/routes.py` (`control_service` takes the reader, `:116-123`).
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_server_secrets.py`.

**Build.**

- [ ] Add the vault reader for role `server` only. This PC keeps Credential Manager as built.

**You see.**

- [ ] Nothing yet.

**Verify, unit.**

- [ ] With keyring's fail backend forced, a fixture app declaring a secret starts with the vault reader, and with the default reader it fails `startup_failed`. Run `uv run pytest qmx-agents/packages/qmx-host/tests/test_server_secrets.py -q` on Windows and on Linux.

**Verify, live.**

@lane1
- [ ] Lane 2. On Windows, a fixture app declaring a secret, with role `server` and keyring's fail backend. Save `c05d-windows.log`. Pass when it starts with the vault reader.
- [ ] Lane 3. The same with the default reader. Save `c05d-default.log`. Pass when it fails `startup_failed`, as Part C `BLAST-RADIUS.md` C8 says.
- [ ] Lane 4. On Linux, in a throwaway folder `/srv/qmx/check/c05d/` on `qmx-server` as user `qmx`. Save `c05d-linux.log`. Pass when the app starts with the vault reader.
- [ ] Lane 5. A vault file that is not owner-only. Save `c05d-perms.log`. Pass when the reader refuses it by name.
- [ ] Lane 6. Grep every lane log for the fixture secret's value. Save `c05d-noleak.log`. Pass when it never appears.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds to read one secret.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on secrets. The blast-radius fact is C8, the default reader fails on a headless server.

@merge

## Keep a node's trading grant on its own machine (C-05e)

Phase 5, the trading node and external connections. Part C slice C-05e, mini-app core change 7 of Level 0 AD-33, Part C AD-306, R1-C-14 and fix-check FC1 G3. Rulings 46 and 53. Real step none. Done when a volume's `data/grants/` is classed `secret` by the backup classes and skipped by the move snapshot, so no backup or move carries a live grant.

**Depends on.** Nothing.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-home/src/qmx_home/classes.py` (one rule before `:119`, `data/apps/*/data/grants/**` is `secret`) and `qmx-agents/packages/qmx-apps/src/qmx_apps/volume.py` (`snapshot()` skips `data/grants`, beside the `data/tmp` skip at `:271`).
- [ ] Edit `qmx-agents/packages/qmx-home/tests/test_classes.py` and create `qmx-agents/packages/qmx-apps/tests/test_volume_grants.py`.

**Build.**

- [ ] Add the two one-line rules and their tests.

**You see.**

- [ ] Nothing yet. A backup or a move of a node never carries its trading grant.

**Verify, unit.**

- [ ] A grant file under a node volume's `data/grants/` is classed `secret`, is not sent by a backup, and is not copied by a move snapshot (the checks of Part C `BLAST-RADIUS.md` C11 as tests). The shipped `qmx-home` and `qmx-apps` tests pass unchanged with `TEMP` on `D:/Temp`. Run `uv run pytest qmx-agents/packages/qmx-home/tests/test_classes.py qmx-agents/packages/qmx-apps/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Classify a fixture grant file under a node volume. Save `c05e-class.log`. Pass when it is `secret`.
- [ ] Lane 3. A backup round of a throwaway folder holding that volume, with `TEMP` on `D:/Temp`. Save `c05e-backup.log`. Pass when the grant file is not in the backup.
- [ ] Lane 4. A move snapshot of the volume. Save `c05e-snapshot.log`. Pass when the grant file is not copied and every other `data/` file is.
- [ ] Lane 5. The 106 `qmx-home` backup tests with `TEMP` on `D:/Temp`. Save `c05e-home.log`. Pass when they pass, which confirms fix-check FC1's disk finding.
- [ ] Lane 6. A restore of that backup onto a second throwaway folder. Save `c05e-restore.log`. Pass when the node volume restores without a grant and the node asks for a sign-in.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for one backup round of the fixture folder.
- [ ] Probe. Lane 3 at the parent and the head, interleaved.
- [ ] Baseline. The parent's round, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on the live grant. The blast-radius fact is C11, run by Part C, both copies happen today and both one-line rules stop them.

@merge

## Reach a node from This PC through one host route and a node link (C-06)

Phase 5, the trading node and external connections. Part C slice C-06, Part C `NETWORKING.md`, Level 0 AD-44 and AD-46, R1-C-04, R1-C-05 and R1-C-12. Standing order 7 and ledger CC-11 (agents never change trading). Real step none. Done when `POST /api/host/forward` serves its five verbs with the principal rule, `qmx_host.node_link` queues changes with `issued_at`, `app_op` is composed with its `Placements`, the core `node` rows read through the link, and the control server states the host build's version.

**Depends on.** B1.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/host_route.py` and `qmx-agents/packages/qmx-host/src/qmx_host/node_link.py`, and edit `qmx-agents/packages/qmx-host/src/qmx_host/door.py` (one entry in the set `host_pass_call` admits) and `qmx-agents/packages/qmx-host/src/qmx_host/host.py` (mounts the route).
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/control_door.py` (`:308`, `app_op` composed with `Placements`), `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py` (rows `node_units`, `node_positions`, `node_journal_tail`, `node_passport`) and `qmx-agents/packages/qmx-control/src/qmx_control/server.py` (`:415`, the OpenAPI version from the package).
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py` and `qmx-agents/packages/qmx-tools/src/qmx_tools/service.py` (the node-state caller moved off `qmn.doors`) and `qmx-agents/packages/qmx-tools/tests/test_tools.py`, where `node` goes from 2 to 6 tools on purpose (`:374-376`).
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_host_route.py` and `qmx-agents/packages/qmx-host/tests/test_node_link.py`.

**Build.**

- [ ] Write the route with the closed verbs `apps.ask`, `apps.job` (optional `inputs`, refused to every principal but `operator` for a `money` app), `heartbeats`, `data.list` (accepts `confirmed`) and `data.fetch`. A `manage` operation answers only to `operator`.
- [ ] Write the node link's outbox, so a change to an unreachable node waits as desired state and applies once.

**You see.**

- [ ] The copilot's "node state" answers "no trading node is set up yet" instead of an error.

**Verify, unit.**

- [ ] Two hosts on two loopback ports with one pairing key. `heartbeats` answers. An agent pass on a `manage` operation is refused. An agent pass on `apps.job` of a fixture `money` app answers `refused_principal`, and on a `runs` app runs with its `inputs`. A pass for another place is refused. A queued `pause` applies once when the far host returns. Every answer carries `schema_version`. The OpenAPI version equals the package version. Level 0's `br10_host_pass_routes.py` and `br11_app_op_remote.py` rerun as tests. `node` lists 6 tools. Run `uv run pytest qmx-agents/packages/qmx-host/tests/test_host_route.py qmx-agents/packages/qmx-host/tests/test_node_link.py qmx-agents/packages/qmx-tools/tests/test_tools.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Two hosts on This PC on two loopback ports, `heartbeats` asked across. Save `c06-heartbeats.log`. Pass when the far host's newest rows come back with `schema_version`.
- [ ] Lane 3. An agent pass on a `manage` operation and on a `money` app's job. Save `c06-principal.log`. Pass when both answer `refused_principal`, and `operator` gets through.
- [ ] Lane 4. Queue a `pause` while the far host is down, then start it. Save `c06-outbox.log`. Pass when the pause applies exactly once.
- [ ] Lane 5. A workflow's `app_op` to a `runs` app homed on the far host, with inputs. Save `c06-remote.log`. Pass when the job runs there with its inputs and the result comes back.
- [ ] Lane 6. Ask the copilot on `haiku` "what is my trading node doing?" Save `c06-copilot.log`. Pass when it answers that no trading node is set up yet.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds for one `heartbeats` ask across two loopback hosts.
- [ ] Probe. Lane 2 repeated 100 times.
- [ ] Baseline. A local `ops_heartbeats` read at the head.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, because this route must never let an agent change trading. The blast-radius facts are Level 0 items 10 and 11, five host-pass routes, and an app homed here keeps the local path.

@merge

## Read contract markets on This PC and normalise public trades and books (C-07)

Phase 5, the trading node and external connections. Part C slice C-07, Part C `EXTERNAL.md`, Level 0 AD-41. Rulings 28, 39 and 40 (CCXT handles everything, open the wrapper; order flow as data). Real step none. Done when the CCXT read adapter opens to contract markets and the data-route port normalises Hyperliquid, Binance and Bybit public trades and books into one internal format, with no order call on any host.

**Depends on.** C-02.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py` (`:330-339`).
- [ ] Create `packages/qmf-venue/src/qmf/venue/routes/` (the normaliser), `qmx-agents/packages/qmx-broker/tests/test_ccxt_contracts.py` and `packages/qmf-venue/tests/test_routes_normalise.py`.

**Build.**

- [ ] Open the read adapter to perps and futures on CCXT 4.5.85, reads only. Write the normaliser to `print`, quote, book and bar events with the aggressor side.

**You see.**

- [ ] Perps positions, funding and open interest in his market tools.

**Verify, unit.**

- [ ] A perp's funding and open interest read. A recorded Hyperliquid trades frame normalises to `print` events with the aggressor side. Level 0 `br8_host_orders.py` reruns with no order call on the host. Run `uv run pytest qmx-agents/packages/qmx-broker/tests/test_ccxt_contracts.py packages/qmf-venue/tests/test_routes_normalise.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A perp's funding and open interest from recorded responses. Save `c07-perp.log`. Pass when both read with their timestamps.
- [ ] Lane 3. Recorded Hyperliquid, Binance and Bybit trade frames. Save `c07-prints.log`. Pass when each normalises to `print` events with the aggressor side.
- [ ] Lane 4. Level 0 `br8_host_orders.py` at the head. Save `c07-noorders.log`. Pass when no host source holds an order call.
- [ ] Lane 5. A live public read of Hyperliquid BTC perp funding, no keys. Save `c07-public.log`. Pass when a rate comes back, or the lane records that the network was down.
- [ ] Lane 6. Recorded book frames from the three venues. Save `c07-books.log`. Pass when each normalises to one book format.
@menu

**Verify, perf.**

- [ ] Metric. Events per second the normaliser handles.
- [ ] Probe. Lane 3's frames replayed in a loop.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is Level 0 item 8, no order code exists on any host.

@merge

## Start the smallest trading node and see it started (C-10)

Phase 5, the trading node and external connections. Part C slice C-10, Part C `NODE.md`, AD-301 to AD-306, Level 0 AD-33 and AD-36. Rulings 27, 35 and 43 (the node is a mini app, "just a server", one click). Real step none. Done when the `trading-node` app starts with every operation answering, changes accepted into `desired` in arrival order with `superseded` for an older change, identity minted, no job declared, venues "not set up", and the state "Ready, no units".

**Depends on.** C-05a, C-05c, C-06, C-01, B8.

**Files.**

- [ ] Create `qmn/src/qmn/app/store.py`, `qmn/src/qmn/app/operations.py`, `qmn/src/qmn/app/identity.py` and `qmn/src/qmn/app/server.py`, and `qmn/tests/test_app_operations.py` and `qmn/tests/test_app_identity.py`.
- [ ] Create `qmx-agents/apps/trading-node/` (the manifest, risk `money`, naming the one secret `qmx/trading-node-keys`, and its entry), and edit `tools/test_all.py` if the app folder has tests of its own.
- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py` so install refuses any app other than `trading-node` that names the venue trading-grant secrets (Level 0 AD-33's secret map, LC-A0-18, Part C AD-306). No slice built this rule, so the plan puts it here, where the secret is first named.

**Build.**

- [ ] Write the store, the operations, which never raise and answer inside the supervisor's 30 s call timeout, the identity of machine id plus install id, and the breaker values. The node declares no job.

**You see.**

- [ ] On a throwaway folder the node starts and its card reads "Ready, no units yet". Starting it from the setup list arrives in C-11.

**Verify, unit.**

- [ ] Every operation through the supervisor's real `call` answers under 2 s with `instance.errors == 0`, bad arguments included. A `pause` whose `issued_at` is older than an applied `resume` for the same scope answers `superseded`, while an older `kill` still applies. A direct call without an op id gets one minted. The manifest declares no job. `journal_tail` called mid-write returns only whole lines and leaves the writer's file unchanged. A copied volume on another machine fingerprint refuses trading until `confirm_same_node`. Another app naming the grant secret is refused at install. Run `uv run pytest qmn/tests/test_app_operations.py qmn/tests/test_app_identity.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Every operation through the supervisor's real `call`, bad arguments included. Save `c10-ops.log`. Pass when each answers under 2 s and `instance.errors` stays 0.
- [ ] Lane 3. An older `pause` after a newer `resume`, then an older `kill`. Save `c10-order.log`. Pass when the pause answers `superseded` and the kill applies.
- [ ] Lane 4. `journal_tail` while the node writes. Save `c10-tail.log`. Pass when only whole lines come back and the writer's file is unchanged.
- [ ] Lane 5. Copy the node's volume to a second throwaway folder with another machine fingerprint. Save `c10-copied.log`. Pass when it refuses trading until `confirm_same_node`.
- [ ] Lane 6. Install a fixture app that names `qmx/trading-node-keys`. Save `c10-secretmap.log`. Pass when install refuses it by name.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds per operation answer.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. Fails when any operation takes 2 s or more.

**Review gate.** Lenses edge-case and adversarial, because this is the money app. The blast-radius fact is that a node operation must answer inside the supervisor's 30 s call timeout, because a timeout stops the app (`qmx_apps/supervisor.py:957-963`).

@merge

## Add the trading node to the connect dialog for This PC (C-11)

Phase 5, the trading node and external connections. Part C slice C-11, Part C `NODE.md`, Level 0 AD-37 and AD-45. Rulings 35 and 37 (one click sets it up; sign-ins come later and nothing waits on them). Real step none. Done when the kind's steps for This PC (the cTrader app request as a waiting step, the keys document, clock, install and enable with his signature, the sign-in step, round trip, self-test skeleton, passport, place row last) rerun safely and converge on one place row.

**Depends on.** C-10.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py` and `qmx-agents/packages/qmx-host/tests/test_connect_node.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/connect.py` (registered in `KINDS`).

**Build.**

- [ ] Write the steps on the shipped step runner. A waiting step blocks only its own later steps. The sign-in step is present and never run by the build.

**You see.**

- [ ] The setup list, with "Waiting for cTrader to approve your app" as a step that ticks when he pastes the id.

**Verify, unit.**

- [ ] A rerun after a kill at each step converges on one place row. The waiting step blocks only its own later steps. Run `uv run pytest qmx-agents/packages/qmx-host/tests/test_connect_node.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Kill the setup at each step in turn and rerun it, on a throwaway folder. Save `c11-rerun.log`. Pass when every run ends with exactly one place row.
- [ ] Lane 3. The waiting step left open. Save `c11-waiting.log`. Pass when only its own later steps wait and the rest run.
- [ ] Lane 4. Paste a fixture app id into the waiting step. Save `c11-paste.log`. Pass when the step ticks and its later steps run.
- [ ] Lane 5. Run the whole setup without a sign-in. Save `c11-nosignin.log`. Pass when the node reads "Ready, no units yet" and each venue reads "not set up".
- [ ] Lane 6. The signature step for the node version. Save `c11-signature.log`. Pass when install waits for the signature and a restart of the signed version needs none (`qmx_apps/supervisor.py:542-547`).
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the whole This PC setup without a sign-in.
- [ ] Probe. Lane 5.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that the shipped connect kinds still register and run (`qmx_host/connect.py` `KINDS`).

@merge
