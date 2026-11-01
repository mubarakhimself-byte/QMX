# Blast radius of the shipped seams Part C changes

Skill `blast-radius`. For each shipped seam this part changes: what changes, the one fact it is safe because of, how far that fact was proven (1 said, 2 pointed at the line, 3 walked the failure, 4 ran it, 5 reproduced in the running app), the risks, what was cleared, and the cheapest check before merge.

**How the code was run.** Against the scratch export of `origin/engine/base` `c93407ca` that Level 0 made (`...\scratchpad\eb`; the files read here were compared with the read-only checkout ignoring line endings: `manifest.py`, `supervisor.py`, `market_data.py`, `heartbeat.py` identical), with its agents environment (`eb\qmx-agents\.venv`, Python 3.14.6), as `python -I -B <script> <export>` so nothing is written into the export. The read-only checkout was only read. Scripts: `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\c1\br\`.

## Summary

| # | Seam | The one fact | Step |
| --- | --- | --- | --- |
| C1 | The host route's principal (AD-303, AD-304) | a host pass carries whatever principal the caller mints; the engine's forwarders mint the constant `operator`, so the node link must mint the real caller's | 4 |
| C2 | The node's operations under the breaker (AD-302) | tool errors accumulate per instance and trip the app at `max_errors`; a manifest may raise it with no upper bound | 4 (rule), 2 (counting) |
| C3 | Every node operation `state = "instance"` (AD-302) | a `state = "none"` operation homed elsewhere starts the app lazily on the caller's machine | 4 |
| C4 | Node reads as `domain_write`; the keys secret's name (AD-302, AD-306) | the manifest refuses an instance read and a secret name with a second slash; `domain_write` and `manage` instance operations load | 4 |
| C5 | Harvest from an app volume through the door; the node-born pin (CF-5) | the door commits a partition staged anywhere under a staging root, and pins only a PC-born file | 4 |
| C6 | The shell cut (AD-323) | no kept organ imports `qmn.host`; the four unclassified modules have one source importer, `qmn/host/__init__.py` | 4 (source), 2 (tests) |
| C7 | Clock facts on heartbeats (AD-319) | today's heartbeat model refuses an unknown field, so cross-machine readers must read rows tolerantly | 4 |
| C8 | App secrets on a server (AD-306) | a missing declared secret stops the start, and the default reader is keyring, whose fallback backend raises | 2 |
| C9 | X6, the cross-machine run pass | a run pass minted on This PC verifies at a server that holds the same pairing key | 4 |
| C10 | The core fixes not yet built (restart, market root, host facts) | each is additive and opt-in by manifest or by the host | 2 |
| C11 | A node volume's `data/grants/` (AD-306, R1-C-14) | today a grant file there is backed up and copied by a move; one backup rule and one snapshot skip stop both | 4 |
| C12 | The promote action's principal (AD-324, R1-C-01) | the seal move already refuses every principal but `operator` on a host route; the promote route copies that check | 2 |

## C1. The host pass carries the caller's principal

**What changes.** The node link mints a host pass per ask for `POST /api/host/forward`; the route answers `manage` operations only to `operator`.

**Proof (step 4).** `brc1_principal.py`:

```text
user     -> pass principal 'operator'
agent    -> pass principal 'agent:s1'
workflow -> pass principal 'run:r9'
host.py:1155: Forwarder(instance, key=key, source=name, principal="operator", now=wall)
```

**Risk confirmed.** A builder who reuses `forwarders_for` (`qmx_host/host.py:1148-1156`) to reach the new route mints `operator` for every caller, so an agent's ask would pass the `manage` rule. Cost: an agent could pause or flatten a node; odds: high if the forwarder is reused. Closed by AD-303: the node link mints `PRINCIPAL.get().principal` per ask.

**Before merge.** A route test with a pass minted for `agent:x` on `kill` answers `refused_principal`; a test that the node link, called inside an agent's context, mints `agent:x`.

## C2. The breaker counts every tool exception

**Proof (step 4).** `brc2_breaker.py` drives the shipped `Supervisor._breach`:

```text
default breaker, 2 tool errors -> ''
default breaker, 3 tool errors -> 'error_limit'
node manifest max_errors=1000, 3 errors -> ''
Breaker accepts max_errors=1000000: 1000000
```

The count rises on every exception in `_call` (`qmx_apps/supervisor.py:921`, step 2) and never decays inside an instance; a trip kills the process (`:825-842`).

**Risk confirmed.** A node whose handlers raise on bad arguments is killed by the third bad call, trading loop included. Closed by AD-302 (never raise; `max_errors = 1000`).

**Before merge.** The operations test in slice C-10 asserts `instance.errors == 0` after good and bad calls.

## C3. A `state = "none"` operation starts the app on the caller

**Proof (step 4).** `brc3_lazy.py` drives the shipped `AppOp._route`:

```text
state=none     homed on ldn-1, asked from pc -> {'ran': 'local'} calls=[('lazy-start-here', 'trading-node'), ('local-run', 'trading-node', 'status')]
state=instance homed on ldn-1, asked from pc -> {'ran': 'remote'} calls=[('remote', 'ldn-1', 'trading-node', 'status')]
```

**Risk confirmed.** A node read declared `state = "none"` would start a second trading node on This PC when asked about a server's node. Closed by AD-302.

## C4. What the manifest accepts

**Proof (step 4).** `brc4_manifest.py` loads temporary `trading-node` definitions with the shipped `Definition.load`:

```text
status: state instance, approval read: REFUSED operations.status keeps instance state, so it cannot be a read
status: state instance, approval domain_write: LOADS
pause: state instance, approval manage: LOADS
secret qmx/token/ctrader-node: REFUSED Secrets must reference qmx/* Credential Manager services.
```

**Cleared.** The keys secret `qmx/trading-node-keys` is one segment and loads; `[breaker] max_errors = 1000` loads.

## C5. The door commits from an app volume, and pins only PC-born files

**Proof (step 4).** `brc5_harvest.py` stages a `bar-m1` partition under a folder shaped like a node volume's outbox and commits it through the shipped `MarketDoor`:

```text
door at server: committed ctrader.live.ldn-1/EURUSD/bar-m1/bid/2026-10 fp=290327b1b872c64e78... pinned markers=0 pending=()
door at pc: committed ctrader.live.ldn-1/EURUSD/bar-m1/bid/2026-10 fp=290327b1b872c64e78... pinned markers=1 pending=('bid/2026-10',)
```

**What it means.** The host's harvest can commit straight from an app volume (the door's staging root is any folder). R1 made Part B's records job that one harvester on every machine (R1-B-02); this part consumes it. Level 0 AD-28's "the node keeps every partition until the PC confirms" is not held by any marker on a server today. CF-5 proposes pinning node-born partitions on a server; `born_on` has three callers, the downloader templates, which pass the door's own placement (`templates/download-*/scripts/download.py`), so a `NODE` branch changes none of them.

**Before merge.** The harvest test commits a node-born partition on a server door, asserts a pin, then clears it through `data.list`'s `confirmed`.

## C6. The shell cut's importers

**Proof (step 4).** `brc6_host_modules.py`, an AST scan of the whole checkout:

```text
qmn.host.runtime_risk_gate: src importers ['qmn/src/qmn/host/__init__.py'] | test files 0
qmn.host.fencing: src importers ['qmn/src/qmn/host/__init__.py'] | test files 1
qmn.host.lineage_persist: src importers ['qmn/src/qmn/host/__init__.py'] | test files 0
qmn.host.registry_mint: src importers ['qmn/src/qmn/host/__init__.py'] | test files 0
qmn.host._supervision: src importers ['qmn/src/qmn/host/__init__.py', 'qmn/src/qmn/host/concurrency.py', 'qmn/src/qmn/host/lifecycle_campaign.py', 'qmn/src/qmn/host/seat_concurrency.py', 'qmn/src/qmn/host/supervise.py']
kept organs importing qmn.host: []
```

The four modules G4a could not classify are dead for the new shell: only the host package's own `__init__` imports them. Tests reach them through `from qmn.host import ...` (step 2: `qmn/tests/test_qmn_runtime_risk_gate.py`, `test_qmn_host_lineage.py`, `test_qmn_host_registry.py` and others), so they leave with the package.

**Risk confirmed.** Tests of kept organs import small names from `qmn.host`: `StandDownTrigger` (`qmn/tests/test_qmn_time.py:19`), `allocate_writer_ids` (`test_qmn_roster.py:37`), and supervision names (`test_qmn_hygiene.py:22-36`). Deleting the package without moving them breaks shipped tests (ruling 52). Closed by AD-323: those names move into `qmn/src/qmn/app/` first.

**Before merge.** `tools/import_scan.py` on the cut's head: no importer of a deleted module; `just ci` green.

## C7. Heartbeat rows are strict

**Proof (step 4).** `brc7_heartbeat.py`:

```text
today's row: Heartbeat
row with a new clock field: REFUSED extra_forbidden
```

**Risk confirmed.** If a server runs a newer build that writes `clock` and This PC parses its rows with today's model, every row is refused and the server looks unreachable. Closed by AD-319: the `heartbeats` verb answers JSON rows, and the node link reads them tolerantly, keeping known fields.

## C8. App secrets on a server

**Proof (step 2).** `brc8_secret_start.py` prints the shipped lines:

```text
secret = self.secret_getter(service, service.split("/", 1)[1])
raise AppError("missing_secret", f"Missing declared credential {service}.", 503)
```

The default `secret_getter` is `keyring.get_password` (`qmx_apps/supervisor.py:254`), and the host builds its control service with no other reader (`qma-harness/src/qma/harness/routes.py:116-123`). With no viable backend, keyring's fallback raises on every call (`keyring/backends/fail.py`, read in the pinned package). That a headless VPS has no viable backend is INFERRED (no desktop session or Secret Service there).

**Risk.** A node app on a server would fail to start. Closed by AD-306 (the server reads `<home>/vault/<name>`, the rule `qmx_control/node.py:79-87` already uses).

**Before merge.** A Linux CI test starts a fixture app declaring a secret with the vault reader and asserts it starts; with the default reader and no backend, that it fails with `startup_failed`.

## C9. X6: a run pass across two machines

**Proof (step 4).** `brc9_run_pass.py` mints with This PC's `PassAuthority` and parses with a server's:

```text
paired server: parse refusal = None
unpaired server: parse refusal = bad_mac: the bearer was not signed by this router
```

The run-pass secret is derived from the pairing key when `vault/pairing-key` exists (`qmx_router/passes.py:246-286`), so the handoff's note that the secret is drawn per process is out of date. Unproven: a run between two real hosts (slice C-17).

## C10. Core fixes not yet built

| Change | The one fact | Step |
| --- | --- | --- |
| `[breaker] restart = "backoff"` | `Breaker` is a strict model with defaults (`manifest.py:108-110`); a new field with default `never` leaves every shipped manifest as today | 2 |
| `QMX_MARKET_ROOT` for `data_reads = ["market"]` | `data_reads` is only logged today (`supervisor.py:700`); apps not declaring it get an unchanged environment (`:598-632`); writes outside the volume stay refused (`bootstrap.py:93-100`) | 2 |
| `road/host/facts.json` | the bootstrap refuses app writes under `road/` (`bootstrap.py:100`), so only the host can write the file | 2 |
| `VenueClientKind.ccxt` | live selection refuses any kind it does not branch on (`qmn/src/qmn/venue/port.py:171-190`), so the new kind needs its own branch and changes no existing one | 2 |
| `label` on cTrader orders | the encoder writes `clientOrderId` only (`encode.py:598`); `label` is an optional protobuf field (help.ctrader.com) | 2 |
| `ZO_HTTP_ADDR` in the server's OpenObserve unit | unset today, which binds 0.0.0.0 (openobserve `src/main.rs`); This PC's own instance sets loopback (`connect_logs.py:186`) and is unchanged | 2 |

## C11. A node volume's grants never leave the machine (R1-C-14)

**What changes.** Two one-line changes to shipped code: `qmx_home/classes.py` gains `Rule("data/apps/*/data/grants/**", "secret", ...)` placed before the `data/apps/**` rule at `:119`, so no backup sends a grant (`secret` is in `NEVER`, `:31`); `qmx_apps/volume.py` `snapshot()` skips `data/grants` beside its `data/tmp` skip (`:271`), so a move (`supervisor.py:1072`) and the road check's copy (`road/validation.py:37`) never carry one.

**Proof (step 4).** `x1c/br/brx1_grants_copy.py` builds a real volume with the shipped `Volume`, writes a grant file under `data/grants/`, and asks the shipped classifier and snapshot; then the same script against copies patched by `x1c/br/patch_grants.py`:

```text
== shipped
backup class of data/apps/trading-node/data/grants/ctrader-node.json: content (rule Rule(glob='data/apps/**', ...)); sent by a backup: True
move snapshot copies: ['app.db', 'data/grants/ctrader-node.json', 'data/node.sqlite']
== patched
backup class of data/apps/trading-node/data/grants/ctrader-node.json: secret (rule Rule(glob='data/apps/*/data/grants/**', ...)); sent by a backup: False
move snapshot copies: ['app.db', 'data/node.sqlite']
```

**Risk confirmed and closed.** Without the change, a live grant on a server would go to every backup storage and travel with a move. The first-match rule order means the new rule must sit before `data/apps/**`; the test in slice C-05e pins it.

**Shipped tests.** The `qmx-home` and `qmx-apps` suites on the patched copies give the same result as on the shipped code (338 passed, 106 failed, 9 skipped, the same failure set; `test_classes.py` and all `qmx-apps` tests pass). The 106 are backup-round tests that fail on the shipped code too in the scratch environment (a round answers `refused`); cause not traced, INFERRED environmental. FC1 traced it: his C: drive under a tenth free (343 passed, 0 failed with that rule off); the build sets TEMP on D:.

**Cleared.** R1's other option, keeping the grant beside `<home>/vault/`, fails: the node is the one refresher and the bootstrap refuses app writes outside the volume (`qmx_apps/bootstrap.py:93-100`).

## C12. The promote action's principal (AD-324)

**The one fact (step 2).** The shipped seal move is a host route that reads `PRINCIPAL.get()` and refuses any principal but `operator` (`qmx_host/market_data.py:1201-1210`); his UI bearer is `Caller("user")`, whose principal is `operator` (`qmx_engine/service/context.py:59-70`), and an agent's is `agent:<id>`. The promote route copies that check, so no agent or workflow can record a promotion.

**Before merge.** Slice C-23's test: an `agent:x` principal answers `refused_principal`; his principal lands one lifecycle event.
