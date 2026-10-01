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

The updated wheel was then built and installed into the same external environment before launching the actual entrypoint:

```sh
uv build qmx-agents/packages/qma-daemon --wheel --out-dir /tmp/qma-wheel-current
uv pip install --python /tmp/qma-external-venv/bin/python --find-links /tmp/qma-wheel-check --reinstall --no-deps /tmp/qma-wheel-current/qma_daemon-0.1.0-py3-none-any.whl
cd /tmp && /tmp/qma-external-venv/bin/python /tmp/qma_entrypoint_smoke.py
```

The smoke script created an operator config and corpus under a fresh `/tmp` root, started `python -m qma.daemon`, waited for `daemon.listener_bound`, sent SIGINT, and collected the exit. Result: exit 0; stdout empty; stderr contained `daemon.composed` and `daemon.listener_bound`; no startup refusal.

## Boundaries

This verifies startup/config refusal, wheel-carried mandatory pack resources, and a configured installed daemon process that binds a loopback listener and stops cleanly. It also verifies fail-closed default provider composition. It does not establish live OpenCodex transport, task worker execution, durable result rediscovery after restart, Windows installation, browser behavior, provider entitlement, or release readiness.

## Shared process runtime wiring

`DaemonProcess.compose` now creates one `ExecutionEnvironmentRegistry`, `ComputeRouter`, journal-bound `TaskLedgerStore`, and `TaskGraphDispatcher` over the process's durable `TaskGraphStateService`. `JobHandleService`, `RuntimeService`, and the existing `BacktestingService` use those same job/tool/environment/router objects. `NestedMissionHost` uses the active `roster.compiler`, `process.task_graphs`, shared jobs, and governed variables. Public process properties expose these shared services for the CT-40 serving layer; ProductSessionService remains the grant-binding authority.

Command:

```sh
qmx-agents/.venv/bin/python -m pytest -q -p no:cacheprovider qmx-agents/packages/qma-daemon/tests/test_daemon_process.py qmx-agents/packages/qma-daemon/tests/test_task_graph_state_edges.py qmx-agents/packages/qma-daemon/tests/test_durable_job_handle.py qmx-agents/packages/qma-daemon/tests/test_qmb_backtesting_door.py
```

Result: 38 passed at the runtime-composition stage. `test_daemon_process.py` asserts object identity across the composed dispatcher, durable Task Graph service, JobHandle service, QMB BacktestingService, ToolRegistry, RuntimeService, NestedMissionHost, and roster compiler.

## CT-40 grant-bound invoke adapter

`start_mission` and `launch_task` retain the existing JSON-RPC command names. Their params carry `product_session_ref`, the existing `envelope`, and the operation `payload`. The server resolves the session principal, enabled instance, live published contribution, operation descriptor, and instance configuration revision from ProductSessionService and the live roster, then calls `dispatch_public_call(transport=WIRE)`. Request params cannot inject stores, callbacks, an owner, or an environment. Unsupported operation adapters return a typed `UNAVAILABLE_DEPENDENCY` refusal after grant binding.

The existing `qma.procedure.start` descriptor reaches `NestedMissionHost.compile_parent` only after resolving the operator's exact per-instance entry from `operator-config.json` `qmb_bindings`, a Quant registered with the daemon MailboxStore, and a single registered Graph Template named by `procedure_id`. The compiler is the roster's compiler, the resulting task graph is durably recorded by the shared TaskGraphStateService, and the JobHandle is returned. `qmb.analysis.project` uses the QMA-owned BacktestingService only with the exact configured `owner_actor_id` and `environment_ref`; a payload that attempts to replace those fields is refused. The current `qmb.backtest.run` descriptor cannot reach the existing QMB door: the descriptor payload lacks the recorded `evidence_ref` required by CT-47, so it returns `UNAVAILABLE_DEPENDENCY` instead of deriving a fake reference. Each operator mapping is keyed by exact `instance_id` and `config_revision`, so packs sharing an op id cannot share host identity implicitly.

Focused verification:

```sh
qmx-agents/.venv/bin/python -m pytest -q -p no:cacheprovider qmx-agents/packages/qma-daemon/tests/test_installed_bootstrap_contract.py qmx-agents/packages/qma-daemon/tests/test_daemon_process.py
.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_cli_host.py
qmx-agents/.venv/bin/ruff check qmx-agents/packages/qma-daemon/src/qma/daemon/process.py qmx-agents/packages/qma-daemon/src/qma/daemon/bootstrap_config.py qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/compiler.py qmx-agents/packages/qma-daemon/tests/test_daemon_process.py qmx-agents/packages/qma-daemon/tests/test_installed_bootstrap_contract.py
.venv/bin/ruff check qmb/src/qmb/doors/cli/host.py qmb/tests/test_cli_host.py
uv build qmx-agents/packages/qma-daemon --wheel --out-dir /tmp/qma-wheel-final
uv pip install --python /tmp/qma-external-venv/bin/python --find-links /tmp/qma-wheel-final --reinstall --no-deps /tmp/qma-wheel-final/qma_daemon-0.1.0-py3-none-any.whl
cd /tmp && /tmp/qma-external-venv/bin/python /tmp/qma_entrypoint_smoke.py
```

Results: 43 QMA targeted tests and 42 QMB host tests passed; both Ruff checks passed. The QMA positive control registers a test Quant and Graph Template through existing APIs, dispatches the trusted procedure adapter, and verifies the created JobHandle is retrievable. This proves compilation and job submission, not execution/completion by a worker. The rebuilt QMA wheel installed non-editably into `/tmp/qma-external-venv`; module import came from site-packages. A configured installed entrypoint smoke from `/tmp` again exited 0 and observed `daemon.composed` plus `daemon.listener_bound`. Actual QMB CLI provider execution is not claimed here; unavailable environment declarations and missing bindings fail closed.

## QMB host startup diagnostics

`qmb host start` and `qmb host recover-control` preserve child stderr in `<QMA_DAEMON_ROOT>/logs/qma-daemon-startup.log`. Failed readiness and recovery refusals identify that persistent path, making QMA configuration refusal visible through the actual QMB host door. `test_cli_host.py` covers a failed start with the referenced log, the default spawn stderr destination, and the existing recover/start behavior.
