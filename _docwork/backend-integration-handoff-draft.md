# Combined backend operator/API handoff — DRAFT

This candidate composes reviewed native/SDK skills, governed QMB data/replay,
and recorded spot paper reads. It is an isolated local branch, not a deployment
or a whole-backend acceptance certificate. Claude owns UI. No credentials,
broker accounts, real orders, paid provider calls or network setup were used.

## Start and test

Use an installed Python 3.14 environment with declared dependencies and the
installed QMB console entrypoint. SDK extras are needed to verify native peers.
Do not treat `PYTHONPATH` as package installation. Current local verification uses
the existing task-8 QMB interpreter with task-11 SDK packages, task-6 native SDK
site-packages **and its `win32`/`win32/lib` paths**, and existing runtime packages,
all read-only. Bytecode is disabled. All QMX source paths point to this candidate.
`task-12/run-local-check.ps1` records that local setup. No registry install occurs.

Portable checked entrypoint:

```powershell
& ./tools/backend-integration-check.ps1 -PythonExe $python `
  -ExtraDependencyPath $dependencyPaths -Suite seams -EvidenceRoot $evidenceRoot
```

Available suites: `seams`, `qma` (branch coverage and 80% aggregate floor), `qmn`,
`data-qmb`. Each creates a new evidence folder, records source HEAD/dirty state,
script hash, executable/source/dependency paths and exact arguments, then keeps
stdout, failures, skip reasons and exit status. Evidence roots stay outside Git.
The QMA tracked-inventory/per-package gate additionally uses
`tools/nested_coverage_report.py`; it does not replace the aggregate gate.

Normal daemon entrypoint is `python -m qma.daemon`. Set `QMA_DAEMON_ROOT` to a
chosen operator-owned runtime root with `operator-config.json`; default Windows
placement is `%LOCALAPPDATA%/QMX/qma-daemon`. Root/config mutations require the
operator's OS ownership. Config needs an existing `research_corpus_root_path`.
`QMA_DAEMON_BIND_PORT` defaults to 8765; binding remains loopback. Do not launch
this candidate against existing production/paper data while evaluating fixtures.
The combined test seeds fresh explicitly labelled simulation data.

Optional `qmb_local_environment` contains an explicit `provider_ref` and
`network: none`. This is an execution-environment declaration, not an OS network
sandbox or a grant. The same registry serves QMB/router/dispatcher. Normal
QMB app-use also requires an exact `qmb_bindings` instance/revision/owner/environment
mapping, a registered Quant, current grants and legitimate dispatched authoring.

Optional `agent_sdk` configuration and generic skills are described in
`qmx-agents/examples/SDK_REQUEST_RUNTIME.md` and `SDK_SKILLS_HOOKS.md`.
Native session configuration stays separate in `NATIVE_AGENT_SESSIONS.md`.
Do not put secret values in skills, request payloads or operator fixture files.

## API contract for Claude

Use the existing paired CT-40 WebSocket and `initialize` negotiation. Connection
health and discovery do not grant operations. Host-advertised capabilities,
operator session identity, contribution/version, instance/config revision,
parameter ceilings and current grants remain mandatory. Client init cannot
enable an absent SDK or create owner/environment/provenance records.

Agent methods: `submit_agent_request`, `get_agent_request`,
`cancel_agent_request`, `resume_agent_request`. Submit carries only
`product_session_ref`, host `profile_id`, prompt and `idempotency_key`.
Status/cancel/resume carry exact request/session identities. Host binds provider,
model, behavior, snapshots and tool authority. Keep original idempotency keys
when retrying a lost acknowledgement; explicit resume owns interrupted work.

Spot: `open_product_session` for `pack:trading-readonly` /
`trading-readonly:positions` / package `0.1.0`; then
`grant_product_session` for `qmn.spot.paper.query` version 1. Invoke through
`start_mission` with the normal hashed invocation envelope and payload exactly
containing the operator-pinned `provider_connection_id`, `venue_id`, `account_id`.
Each account has its own config revision and opaque authority scope. Clients
cannot supply SQLite paths, writer callbacks, credential refs or other accounts.
No spot execution agent operation is published. Results explicitly retain
`simulation: true`, recorded behavior and retained state/audit version markers.
Same-revision account/path/policy retargeting cannot reuse an old session/grant.

QMB: `qmb.backtest.run` requires persisted `evidence_ref`, exact spec selector,
current dispatched task/lease/attempt/deployment, owner/environment and verified
replay preparation. No arbitrary child execution or renderer-selected roots.
QMB owns CT29/CT32/terminal production. Completed recovery verifies the original
occurrence and artifacts before returning; it does not repeat or backfill effects.
The retained original data remains immutable when a correction is admitted.

`qmb.analysis.project` has a remaining public bridge/selector/publication gap.
Its current public `run_fp1` names the ExperimentSpec whereas QMB's result
`run_fp1` names a resolved run. Never select an arbitrary latest result or claim
a positive public projection merely because direct domain projection passes.
Direct persisted projection verifies CT29/CT32 and original context without
execution. A normal read query lacks Agent dispatch provenance for coordinated
Experiment Ledger publication.

## Contract decisions and limits

Keep CT47 Agent-authored. The next legitimate authoring flow must derive the
registered owner, dispatched lease, attempt and actually observed provider
deployment from canonical host state; the model supplies spec content only.
Initial human/no-model authoring would require a separately versioned contract
amendment. No dummy deployment, minted Agent or fixture identity establishes it.

Recommended projection extension: retain the existing ExperimentSpec selector
for compatibility, introduce a separately named resolved-run selector, resolve
only a bound owner's unambiguous DONE handle, and reopen verified expected/result
artifacts. Pass the original pinned context through the host-owned subprocess
door. Separate a granted read from publication requiring dispatched authority.

Paired Dukascopy bid/ask under one retained CT15 key needs a receipt-preserving
versioned observation representation; changing native IDs is not a fix.
`correction_of` resolution folding remains. Spot FX deliverability, live venues,
remote endurance/worker supervision/distributed fencing, native authenticated
providers, ordinary native tools, cold restore/release packaging and DeepSeek
policy/key support remain unverified or pending. Rich memory/context/actors,
authored ledgers, general workflow authoring and analytics/API/DevOps acceptance
remain visible in the single work ledger; passing QMA does not certify them.

No protected merge/push/publish/deploy is authorized. Canonical documentation is
unchanged; this handoff and any produced documentation patch remain drafts.
