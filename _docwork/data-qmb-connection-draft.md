# Data-to-QMB connection: implementation and documentation draft

Status: **draft for parent review / Documentation Factory reconciliation**. This
file and the companion `.patch` do not change ratified architecture or claim the
complete platform acceptance. Baseline: `ffb7590bbda1ec8d5dc126b9fdc3205c888dffac`.
No UI, native adapters, QMF/QML/node source, protected branches, push or merge.

## Implemented bounded changes

- `qmb.backtest.run@1` publishes required `run_fp1` **and** `evidence_ref`.
  CT40 input validation rejects omission before dispatch; receipt identity and
  nonblank/content checks remain runtime/domain semantics. The field names are
  distinct: `run_fp1` is the registered ExperimentSpec identity at this door;
  `evidence_ref` is the persisted QMB ReplayInputRequest identity, never a catalog
  row or archive observation identity. Existing `as_of` runtime refusal remains.
- `qmb.analysis.project@1` advertises the environment requirement its configured
  daemon adapter already enforces. It remains `occupancy=query`, effect `read`;
  an environment declaration is not occupancy acquisition or CT32 minting.
- Optional `qmb_local_environment` in OS-owned `operator-config.json` registers
  one existing CT46 `local` declaration before persistence opens. The registry is
  shared by router, dispatcher and BacktestingService and reconstructed on each
  start. Absence keeps the previous unbound behavior. Invalid configuration
  refuses startup. No environment/provider is inferred from client requests.
- Authoritative coverage refuses unreadable artifacts, invalid raw row shape,
  artifact identity mismatch and invalid identified CT10 observations. Refusals
  include `artifact_ref` (the archive filename digest) and
  `coverage_complete=false`; unrelated valid raw artifacts remain allowed.
  Cached coverage never becomes authority. No pinned receipt/write semantics
  changed, and a successful min/max range still does not establish continuity.

## Operator configuration / runbook draft

Merge this optional fragment into the existing operator-owned file:

```json
{
  "qmb_local_environment": {
    "provider_ref": "operator-local-qmb",
    "network": "none"
  }
}
```

The fragment accepts exactly those two fields, a nonblank provider reference,
and `network=none`. It is a declared posture, **not an OS network sandbox** or a
promise that QMB/dependencies are usable. QMB retains its separate CLI child and
domain writes. This does not configure a worker model or authorize a broker,
account, risk system, provider, order or remote node. Environment changes need a
daemon restart. The existing separate `qmb_bindings` map must still name an exact
instance/config revision, registered Quant owner and `env:local`. Never substitute
a fabricated Quant/Agent/model or write receipts into a second authority store.

Use the committed lockfiles and normal official registry installs in an isolated
environment; root `uv sync --locked` installs QMB, nested QMA can be added with
`uv sync --locked --inexact` into that same task environment. Activate its Scripts
directory so QMA resolves the installed `qmb` executable. The nested sync has
some dependency pin differences from root: a combined environment is a local
validation setup, not installed-artifact release certification. Keep all QMF raw,
registry, requests/descriptors, QMB journals/terminals and QMA roots under their
existing owners. Do not synchronize competing writable database roots.

Listener/PID health answers whether a process is alive. Operation readiness also
needs installed dependencies, correct configured roots and owners, exact binding,
grants, legitimate CT47 registration/attempt, source pins and readback. No new
readiness wire method was added. Report per-operation refusal evidence; do not
present this local declaration or existing host status as platform-ready.

## Executed evidence and remaining blockers

Task-8 `evidence/` (outside git) retains command outputs, pytest roots and exact
backend request/result/refusal JSON from `backend_probe.py`.

- Startup/restart, descriptor and required-input tests execute normal existing
  composition and structural validation. The retry regression retains its
  original no-duplicate/read-vs-place-run assertions with the corrected input.
- Real installed QMB replay/CLI fixture suite: 11 passed, including CT32/terminal
  reopen, forged claim and boolean-attempt negatives. These reuse an existing
  synthetic domain spec/context, **not legitimate CT47 registration or CT40
  acceptance**. A later fresh CLI process reopens the retained terminal result.
- Corruption fixtures reproduce baseline successful empty coverage for damaged
  or emptied canonical metadata and an exception for scalar rows. Candidate
  returns explicit storage refusals for all those cases.
- Historical recorded Dukascopy bytes hit an inherited Windows blocker:
  `qmf.data.intake_authority._ProcessLock` unconditionally imports POSIX `fcntl`.
  Bounded catalog/download/materializer/projection suites initially produced
  10 failures / 27 passes; ingestion failures share this blocker. Shared QMF
  changes must be coordinated with the parent before editing; no mock lock was
  substituted. Thus restart/reingest/correction/quality full acceptance is open.
- CT47 requires a genuine dispatched Agent, observed attempt and model deployment.
  No production registration path was located. Do not interpret existing fixture
  registration helpers as authority. Ordinary non-CT47 QMB CLI/library execution
  remains the existing permissible domain path and mints no ExperimentSpec; it
  does not satisfy authenticated platform acceptance.
- Normal CT40 session opening still refuses missing binding or registered Quant
  ownership. A configured binding alone creates neither a Quant nor a grant.
- Current projection CLI does not consume the delegated query context to load
  pinned CT32/CT29 sources. An actual query child returns a missing-input refusal;
  declaration metadata does not resolve this connection. Source/result selection
  must use a proper existing pinned-source path, not discovery of arbitrary
  descriptor files or client-chosen filesystem roots.
- Full authenticated CT40 run, cancellation/recovery on that run, and projection
  readback after daemon restart remain **unaccepted**. Existing fixture tests for
  ownership/grants/unknown/cancel are regression evidence, not this missing journey.

Backup/telemetry export, root/nested release gates, installed Windows/Linux artifact
certification, power-loss/endurance and remote deployment remain separate readiness
work. Broader spot crypto/FX broker/account/node design and the new Lab concept are
deferred and owned by other lanes; this slice imposes no global account/server.

## Concrete documentation reconciliation map

The companion `data-qmb-documentation-draft.patch` is an unapplied review draft:
it uses zero-context additions; validate with
`git apply --check --unidiff-zero _docwork/data-qmb-documentation-draft.patch`.

| Document | Proposed reconciliation | Evidence / limit |
|---|---|---|
| `docs/components/qma-daemon.md` | Describe opt-in local composition and exact operator bindings; separate liveness/readiness | Startup/restart tests; CT40 refusal fixtures |
| `docs/components/qmb.md` | Required replay request; projection environment/query distinction; explicit catalog integrity refusal | Descriptor/input and corruption tests; projection connection still blocked |
| `docs/contracts/ct-47-qma-experiment-spec.yaml` | Comment on concrete API field identities and unchanged provenance gate | No new CT or permission; full CT47 journey unaccepted |
| `docs/architecture/stack.md` | Record installed dependency/OS requirements and declaration limits | Optuna resolved from PyPI; Windows `fcntl` blocker retained |
| `docs/scenarios/SCN-0012-qmb-replay-run.md` | Add actual acceptance checklist and executed-vs-fixture distinction | Full ingest-to-authenticated-run chain remains open |
| `docs/scenarios/SCN-0016-projection-vs-path-dependent.md` | Clarify configured environment is compatible with zero occupancy; source bridge still missing | Actual query refusal; no new CT32 claim |

Documentation Factory routing follows `CLAUDE.md` and `docs/AGENTS.md`; no factory
publication or external action was invoked. Do not silently apply this draft as
ratified decisions. Parent review must reconcile the exact final commit/evidence.

Official installation guidance checked: [uv environments](https://docs.astral.sh/uv/pip/environments/)
and [Optuna installation](https://optuna.readthedocs.io/en/stable/installation.html).
