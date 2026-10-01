# QMA host bootstrap and installed pack resources

Scope: MA 01 and MA 02 bootstrap/resource slice, plus the MA 03 default-provider refusal. The full mission/task composition is tracked separately. Python environment: CPython 3.14.7; nested QMA environment at `qmx-agents/.venv`; source pin `a0e8769772e469bf54bd312cc1e27e7995e16c3b`.

## Baseline reproduction

Command:

```sh
qmx-agents/.venv/bin/python /workspace/qmx-audit-inputs/packets/reproductions/check_miniapp_runtime.py
```

Before the repair, the actual `python -m qma.daemon` child exited 2 with empty stdout and only one stderr INFO `daemon.composed` JSON line. `DaemonProcess.compose` without config returned a typed refusal because `research-corpus` requires operator-principal `root_path`; explicit `research_corpus_plugin_load_config(seed)` composed successfully and activated all five source-tree packs. The source-tree pack resolver found `qmx-agents/plugins`. The no-handler OpenCodex deployment returned synthetic `Ok(OpenCodexCallResult(...content='opencodex:...'))`. The audit probe contained no wheel files.

The new focused regression was run before implementation:

```sh
qmx-agents/.venv/bin/python -m pytest -q -p no:cacheprovider qmx-agents/packages/qma-daemon/tests/test_installed_bootstrap_contract.py
```

Expected baseline: 3 failed. The installed-resource check found no mandatory manifests; entrypoint stderr lacked the config guidance; and the config-loader import did not exist.

## Implemented behavior

The daemon now reads the operator-owned JSON file `<QMA_DAEMON_ROOT>/operator-config.json`, with a required string field `research_corpus_root_path`. The field remains a filesystem path and flows through the existing `research_corpus_plugin_load_config` helper and existing seed-root validator. No default corpus location is invented. Missing, malformed, or invalid configuration refuses startup with an actionable `daemon.startup_refused` ERROR JSON line. `--recover-control` uses the same config and diagnostic path.

The QMA daemon distribution now contains the five mandatory desk-pack manifests and activators under `qma/daemon/bundled_packs`. `default_plugins_root()` prefers that installed bundle; `QMA_DAEMON_PLUGINS_ROOT` is an explicit pack-root override, and editable source development retains the ancestor lookup fallback. A default OpenCodex deployment now returns `UNAVAILABLE_DEPENDENCY` until a transport handler is explicitly provided. The in-process deterministic hook is named `test_handler` and is only selected by test composition.

## Verification

```sh
uv sync --project qmx-agents
qmx-agents/.venv/bin/python -m pytest -q -p no:cacheprovider qmx-agents/packages/qma-daemon/tests/test_installed_bootstrap_contract.py qmx-agents/packages/qma-daemon/tests/test_desk_plugin_pack_registration.py qmx-agents/packages/qma-daemon/tests/test_daemon_process.py qmx-agents/packages/qma-daemon/tests/test_local_proxy_broker_egress.py
qmx-agents/.venv/bin/python -m ruff check qmx-agents/packages/qma-daemon/src/qma/daemon/__main__.py qmx-agents/packages/qma-daemon/src/qma/daemon/bootstrap_config.py qmx-agents/packages/qma-daemon/src/qma/daemon/plugins/packs.py qmx-agents/packages/qma-daemon/src/qma/daemon/proxy/opencodex.py qmx-agents/packages/qma-daemon/tests/test_installed_bootstrap_contract.py qmx-agents/packages/qma-daemon/tests/test_local_proxy_broker_egress.py
qmx-agents/.venv/bin/python /workspace/qmx-audit-inputs/packets/reproductions/check_miniapp_runtime.py
```

Results: 29 targeted tests passed; Ruff passed. The audit probe now reports an actionable config refusal, the no-handler provider path returns `UNAVAILABLE_DEPENDENCY`, and configured editable composition loads all five packs.

Clean non-editable distribution check (commands run from the repository root):

```sh
uv build packages/qmf-core --wheel --out-dir /tmp/qma-wheel-check
uv build packages/qmf-registry --wheel --out-dir /tmp/qma-wheel-check
uv build packages/qmf-data --wheel --out-dir /tmp/qma-wheel-check
uv build packages/qmf-risk --wheel --out-dir /tmp/qma-wheel-check
uv build qmx-agents/packages/qma-core --wheel --out-dir /tmp/qma-wheel-check
uv build qmx-agents/packages/qma-wire --wheel --out-dir /tmp/qma-wheel-check
uv build qmx-agents/packages/qma-daemon --wheel --out-dir /tmp/qma-wheel-check
uv venv /tmp/qma-external-venv --python 3.14
uv pip install --python /tmp/qma-external-venv/bin/python --find-links /tmp/qma-wheel-check /tmp/qma-wheel-check/qma_daemon-0.1.0-py3-none-any.whl
cd /tmp && /tmp/qma-external-venv/bin/python /tmp/qma_external_smoke.py
```

The daemon import came from `/tmp/qma-external-venv/lib/python3.14/site-packages/qma/daemon`; the pack root came from `site-packages/qma/daemon/bundled_packs`; all five manifests were present and configured `DaemonProcess.compose` returned `Ok` with all five packs activated. The install was non-editable and the process ran with `/tmp` as cwd, outside the checkout.

## Boundaries

This verifies startup/config refusal, wheel-carried mandatory pack resources, and fail-closed default provider composition. It does not establish live OpenCodex transport, a completed daemon serving process, mission/task worker execution, durable result rediscovery after restart, Windows installation, browser behavior, provider entitlement, or release readiness.

## Shared process runtime wiring

`DaemonProcess.compose` now creates one `ExecutionEnvironmentRegistry`, `ComputeRouter`, journal-bound `TaskLedgerStore`, and `TaskGraphDispatcher` over the process's durable `TaskGraphStateService`. `JobHandleService`, `RuntimeService`, and the existing `BacktestingService` use those same job/tool/environment/router objects. `NestedMissionHost` uses the active `roster.compiler`, `process.task_graphs`, shared jobs, and governed variables. Public process properties expose these shared services for the CT-40 serving layer; ProductSessionService remains the grant-binding authority.

Command:

```sh
qmx-agents/.venv/bin/python -m pytest -q -p no:cacheprovider qmx-agents/packages/qma-daemon/tests/test_daemon_process.py qmx-agents/packages/qma-daemon/tests/test_task_graph_state_edges.py qmx-agents/packages/qma-daemon/tests/test_durable_job_handle.py qmx-agents/packages/qma-daemon/tests/test_qmb_backtesting_door.py
```

Result: 38 passed. `test_daemon_process.py` asserts object identity across the composed dispatcher, durable Task Graph service, JobHandle service, QMB BacktestingService, ToolRegistry, RuntimeService, NestedMissionHost, and roster compiler. This establishes shared wiring only. A production CT-40 handler, actual selected-template worker execution, QMB CLI round trip, and restart result discovery are still open; no deterministic fake worker was introduced to claim those outcomes.
