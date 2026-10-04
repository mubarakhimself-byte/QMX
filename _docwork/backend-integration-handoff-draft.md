# Combined backend operator/API handoff — DRAFT

This candidate composes reviewed native/SDK skills, governed QMB data/replay,
and recorded spot paper reads. It is an isolated local branch, not a deployment
or a whole-backend acceptance certificate. Claude owns UI; UI wiring has not
started and no frontend integration is assumed or exercised here. No credentials,
broker accounts, real orders, paid provider calls or network setup were used.

## Start and test

Use an installed Python 3.14 environment with declared dependencies and the
installed QMB console entrypoint. SDK extras are needed to verify native peers.
Do not treat `PYTHONPATH` as package installation. Historical verification used
the existing task-8 QMB interpreter with task-11 SDK packages, task-6 native SDK
site-packages **and its `win32`/`win32/lib` paths**, and existing runtime packages,
all read-only. Current verification uses task12's isolated
`evidence/combined-runtime-env` with an offline editable QMB entrypoint and recorded
borrowed third-party distributions. Its .pth source paths point to this candidate,
including children that strip PYTHONPATH. Bytecode is disabled.
The primary QMB environment's site-packages precede borrowed SDK packages:
otherwise DuckDB/Click/Cryptography pins are shadowed. The final pinned setup
passes dependency integrity; earlier mixed-package broad logs retain their
actual versions and are not canonical dependency-gate certification.
`task-12/run-local-check.ps1` records that local setup. No registry install occurs.

Portable checked entrypoint:

```powershell
& ./tools/backend-integration-check.ps1 -PythonExe $python `
  -ExtraDependencyPath $dependencyPaths -Suite seams -EvidenceRoot $evidenceRoot
```

Available suites: `authoring`, `seams`, `native`, `memory`, `quality`, `qmb-seams`,
`qmn-seams`, `qma` (branch coverage and80%aggregate floor), `qmn`, `data-qmb`.
Each creates a new evidence folder, records source HEAD/dirty state,
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

Final pinned offline seam selection:84passed/no skips. Native correction also
received independent review and81focused passes. Full component gates remain
red and retain their pre-correction/mixed-import setup in the work ledger and
evidence manifest. No final whole-platform certificate follows from these runs.

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

Keep CT47 Agent-authored. The accepted optional host-admitted authoring flow derives
registered owner, dispatched lease, attempt and actually observed provider
deployment from canonical host state and actual adapter output; the model supplies
spec content only. Actual synthetic execution is verified; authenticated provider
acceptance remains separate. See the admitted authoring handoff for setup/recovery.
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

Current official LangChain documentation was consulted through Context7 for
[middleware ordering/state](https://docs.langchain.com/oss/python/langchain/middleware/custom)
and [checkpointed unit-test threads](https://docs.langchain.com/oss/python/langchain/test/unit-testing).
Those SDK mechanisms supply hook/checkpoint behavior; QMX admission and operation
authority remain host-owned. Local released native SDK source/protocol fixtures
provide offline adapter evidence, not real account authorization.

## Accepted memory increment

Reviewed memory `916832bd` is combined as `4400ac05`. Configured research requests
now recall/retain typed summary revisions through the existing workflow. The
canonical journal owns records and supersession; LangGraph Store is a disposable
authorized projection. Fresh jobs and disk restart retain scope/source pins.
Memory, invocation context and authored ledger remain separate contracts.

LangMem extraction is opt-in and accepts an explicit injected BaseChatModel;
startup never calls extraction or initializes embeddings. Exact extra pins and
transitive hashes are in the nested lock, with no existing package upgrade.
To provision the optional test environment from qmx-agents, use
`uv sync --frozen --all-packages --extra memory-extraction`, then
`uv run --no-sync poe check` so a default sync cannot remove the extra.
This follows [uv's optional-dependency sync contract](https://docs.astral.sh/uv/concepts/projects/sync/#syncing-optional-dependencies).
Use the portable integration runner's `-Suite memory` with the corresponding
dependency environment for bounded crossmodule checks. General actor-memory
routing, automatic consolidation/evaluation and agent-authored ledgers remain.

## Historical quality composition gate limits at33165e84

The entire reviewed quality `47b15d4e` series is combined through `19f35af9`,
including cancellation-safe aggregate verdicts. The local join explicitly
installs the memory extra in nested CI and preserves it through all five tasks.
CI controls and source coverage enforcement keep their original floors. Hosted
CI execution, actual workflow cancellation and full mutation strength remain
unverified. The portable integration runner adds `-Suite quality`.

The completed composed QMA run has 2049 passing tests and no failed/skipped tests;
its gate remains red at 78.98% aggregate and77.54% daemon coverage. Subprocess
measurement now includes the real daemon entrypoint and all tracked source.
Full QMA lint/format pass; full nested strict source typing has68 errors across
nine existing files, recorded separately from the quality lane's four root
typing errors. The single ledger and exact evidence JSON describe bounded next
fixes. Operator startup/API instructions above remain valid; these results do
not establish native account auth, remote operation or full backend readiness.

## Latest reviewed successor checkpoint

Source checkpoint `cb62b839` adds accepted host-admitted authoring, four exact
QMA typing patches, the complete QMN series with its required independent repair,
and the complete QMB series with both mandatory independent repairs. Exact
composition maps are `backend-reviewed-successor-series-audit-draft.json` and
`backend-qmb-composition-audit-draft.json`. Existing startup/API instructions above
remain; opt-in authoring setup and explicit recovery are detailed in
`backend-admitted-authoring-handoff-draft.md`.

Latest appropriate full checks ran at clean5fa3e9e2: QMA2076passed, zero failed/
skipped, aggregate79.08%and daemon77.68%; QMN1130passed16platform skips7live tests
excluded,73.17%. Both gates remain RED at unchanged80%coverage. Full QMA strict
typing now604files with zero diagnostics. Composed QMB affected check129passed,
9existing Windows skips; full source QMB1460pass19skip1Studyfailure remains
historical, not a new successor gate. Exact commands/source proof/hashes are in
`backend-current-component-gates-draft.json` and the QMB handoff draft.

Directory DELETE sharing is denied; directory WRITE sharing is intentional.
Tested late junction mutation causes refusal before target writes. Universal
hardlink alias exclusion, hardware-cache and physical power-cut behavior are not
proven. Details and actual checked hashes: native repair review draft.

Remaining bounded functionality: owned-DONE read-only projection with original
verified context, real Alternative Study dispatch/envelope/result verification,
durable operator actor lifecycle and general workflows, paired data/correction
folding, coverage and release/hosted quality acceptance. Full native auth is
unverified; ordinary native tools stay restricted, remote endurance is unproven,
and DeepSeek policy cap/key support is pending. Full platform acceptance is false.
