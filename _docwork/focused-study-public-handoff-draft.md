# Focused authenticated Study and public readback lane

Base verified clean: `5acb4a6483567976be771880d57b30482da4ec6b`,
`C:/Users/Mubarak/Documents/Codex/2026-10-04/task-12/backend-candidate`.
Isolated candidate: `task-20/study-public`, branch
`backend/focused-study-public-20261004`. This is a functionality increment, not
platform acceptance. Canonical documentation remains untouched; the adjacent
patch is a proposal. No push, protected merge, UI change, deployment, credentials,
live financial actions, paid provider calls, memory or skill edits.

## Implemented joins

1. `qmb.optimize.run` follows the existing authenticated grant, frozen Task
   payload, actual durable outbox/lease/attempt and observed deployment checks.
   It passes the actual command through QMA preflight and CT47 invocation.
   The early dispatched-input hash check runs inside the canonical grant-checked
   callback, before consuming a place-run logical invocation. Later live authority
   checks remain. No grant binder or central parameter ceiling was changed here.
2. QMB selects exactly one Book, Alternative or AlternativeStudy descriptor.
   The private versioned Study descriptor pins the complete existing Alternative
   binding, canonical Study space, registered objective, unit/currency, parameter
   bindings, sampler settings and stable Study fingerprint. It reconstructs the
   plan from registered persisted ports and pinned builder bytes. Its outer hash
   is pinned first; the operational fingerprint is derived afterward, avoiding a
   fingerprint cycle. Malformed/ambiguous descriptors refuse without fallback.
3. Actual QMB CLI execution owns compute, generation history, terminal trial
   artifacts and the occurrence witness. QMA accepts the existing seven-field
   Study result through the persisted expected invocation and proof wrapper; it
   does not invent Book-only identity fields. Verify-only requires full ordered
   history and an existing exact occurrence; it cannot execute missing trials or
   create a witness. Resuming execution remains the execution door's responsibility.
4. Authenticated `get_job` returns `verified_result` for an owned DONE QMB handle
   only after independent QMB reopen matches its immutable stored proof. Existing
   originating ProductSession and operator checks remain. Restart uses the durable
   expected invocation and exact source bytes; a changed source refuses readback.
5. `qmb.analysis.project` v1 resolves its `run_fp1` as the declared Book result run
   fingerprint, never an ExperimentSpec fingerprint. It selects one owned DONE
   source, verifies that selected source again, and asks QMB for canonical CT32/CT29
   projection. Since v1 has no predicate field, it uses QMB's identity predicate
   `{"exclude":[]}`. Output remains `artifact_ref`: `{fp1,kind:"saved-view",body}`,
   where fp1 is of the canonical body. The body is an inline return-only view;
   query authority does not authorize publication, artifact persistence or an
   Experiment Ledger append. Study has no fabricated CT32 view: its public
   readback is the seven-field result on `get_job`.
6. Actual Windows `qmb.exe`/`QMB.EXE` are recognized production preflight doors.
   Cancellation files are isolated per owned transport, so identical compiled job
   IDs in separate daemon roots cannot inherit an earlier cancellation signal.
   Explicit operator-configured cancellation paths retain their existing behavior.
   Durable projection has the same bounded 30-second child deadline as verification.

## Proof and limits

The authenticated test uses real HTTP pairing and WebSocket CT40, actual frozen
AgentCapabilityStore admission, dispatch, authoring request, provider execution,
host-observed deployment receipt and durable CT47 registration. The injected
provider is explicitly **synthetic offline** (`synthetic:offline-authoring-v1`),
called once. It makes no model or commercial-provider claim. The predicted spec
fingerprint pins graph inputs; the spec is initially unregistered and is registered
only by the actual admitted authoring execution. Task and agent identity are checked
against the resulting durable lease/attempt/provenance. The fixture supplies a real
declared Quant via existing mailbox APIs; the separate actor-install workflow lane
owns public actor creation and wiring, not this lane.

The registered Alternative interpreter is also an explicit offline fixture. Its
declared `observed_frontier_count` objective is a unit-count control, not a profit
or live-market claim. Actual production QMB resolves persisted recorded inputs,
invokes this registered interpreter and stores its two sampler-selected trials;
neither provider nor policy fixture is shipped as a production implementation.

Persisted CT10 data, CT12 split, replay request, registry/Bot/QML declaration and
conformance, Study descriptor, two generations/trials, terminal artifacts and
occurrence are real local stores. Repeated reads and fresh module restart preserve
the QMB byte snapshot. Negative controls exercise stale grant, wrong owner,
changed source, cancellation, duplicate/changed attempt, changed builder/objective/
unit/descriptor/Study fingerprint, incomplete history and missing new-attempt
occurrence. Incomplete verify refuses before any trial or witness mutation;
execution resumes the remaining trial and then pure verification succeeds.

Accepted gate results and exact proof-file hashes are recorded in
`focused-study-public-evidence-draft.json`. Historical failed runs stay in task-20;
they are not relabeled as acceptance. Independent reviewer `study_review` checked
source authority and descriptor boundaries and ran its own regressions and Book
public projection/restart journey. Its detailed outcome is recorded with evidence.

The local isolated interpreter borrows pinned third-party distributions from
preserved dependency environments. Parent and stripped-child import proof requires
all checked project modules to come from this candidate; this is not a fresh frozen
dependency installation claim. Normal Windows token is necessary to acquire the
existing native directory LIST anchors on this host. Restricted-token refusal,
ACLs and containment guards were preserved. The broader QMA type attempt in this
borrowed environment reported optional `langmem`/cross-test stub resolution
diagnostics; the four owned production files pass strict typing with the nested
project configuration. No memory code, optional-dependency policy or gate was
weakened to change that result. The inherited QMA/QMN coverage floor failures,
whole-QMB formatting and release/hosted acceptance limits remain separate.

## Shared integration ownership

QMA: `backtest/{cli,expected,service}.py` and these exact `process.py` seams:
DONE `get_job` verification; grant-checked early Task input prevalidation;
Mapping result serialization; optimize tool contribution mapping; common
backtest/optimize worker route and actual command; verified Book projection.
The actor lane's isolated modules and wiring must be composed by the parent.
The central grant ceiling fix `29f75aa6dabcb6101487d07e1171f475be6aa25e` is separate;
this lane did not implement or bypass it. Review controlled `process.py` composition.

QMB: `doors/cli/__init__.py`, `host/{qma_cli,operator_alternative_replay,
operator_alternative_study,operator_study_replay,delegated_cli}.py`.
Tests/fixtures: `qa/integration/test_qma_{registered_replay,authenticated_study}.py`,
`qmb/tests/{operator_study_fixture_support,test_operator_study_cli,
test_operator_replay_process}.py`. Windows fixture directory labels hash the
opaque original job ID solely for legal storage paths; exact invocation identity
is retained in the domain context and witness.

## Runnable commands on this host

Use normal Windows user execution; source setup below is external lane-local and
changes only the isolated task-20 runtime. The actual QMB executable is installed
offline from this worktree via the official build backend. No network is required.

```powershell
Set-Location C:\Users\Mubarak\Documents\Codex\2026-10-04\task-20\study-public
. ..\setup-runtime.ps1
$env:UV_CACHE_DIR = '..\uv-cache'
uv pip install --python $lanePython --offline --no-deps --no-build-isolation --editable .\qmb
& $lanePython -m pytest qa/integration/test_qma_registered_replay.py qa/integration/test_qma_authenticated_study.py -p no:cacheprovider --basetemp=..\proof-public-replay -q
& $lanePython -m pytest qmb/tests/test_operator_alternative_study.py qmb/tests/test_operator_alternative_replay.py qmb/tests/test_operator_replay_process.py qmb/tests/test_operator_study_cli.py qmb/tests/test_qma_cli.py qmb/tests/test_optimize_replay_study.py qmb/tests/test_study_stop.py qmx-agents/packages/qma-daemon/tests/test_qmb_cli_transport.py qmx-agents/packages/qma-daemon/tests/test_backtest_expected_context.py qmx-agents/packages/qma-daemon/tests/test_qmb_optimize_study_transport.py qmx-agents/packages/qma-daemon/tests/test_qmb_backtesting_door.py qmx-agents/packages/qma-daemon/tests/test_qmb_local_startup.py -p no:cacheprovider --basetemp=..\proof-focused-replay -q
& $lanePython _docwork/focused-study-source-proof.py ..\focused-source-replay.json
& $lanePython -m pyright --project qmx-agents/pyproject.toml qmx-agents/packages/qma-daemon/src/qma/daemon/backtest/cli.py qmx-agents/packages/qma-daemon/src/qma/daemon/backtest/expected.py qmx-agents/packages/qma-daemon/src/qma/daemon/backtest/service.py qmx-agents/packages/qma-daemon/src/qma/daemon/process.py
& $lanePython -m pyright qmb/src/qmb/host/delegated_cli.py qmb/src/qmb/host/operator_study_replay.py qmb/src/qmb/host/operator_alternative_study.py qmb/src/qmb/host/operator_alternative_replay.py qmb/src/qmb/host/qma_cli.py qmb/src/qmb/doors/cli/__init__.py qmb/tests/operator_study_fixture_support.py qmb/tests/test_operator_study_cli.py qmb/tests/test_operator_replay_process.py
git apply --check _docwork/focused-study-public-contracts-draft.patch
```

Source proof compares the fixed reviewed base, so it can be replayed after commit;
the recorded manifest remains the acceptance identity. No general
integration/coverage/release claim follows from these focused commands.
