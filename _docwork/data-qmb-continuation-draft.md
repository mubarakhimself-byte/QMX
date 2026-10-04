# Data-to-QMB continuation — review draft

The preserved checkpoint is `23fba3d5bb7391b74c9990a8b48d7025f9d42b9e`, also retained on `checkpoint/data-qmb-23fba3d5`. This continuation does not supersede the open platform-acceptance status in the first handoff.

## Independent fixes completed

Production operator replay now stores the actual canonical CT32 container through the existing exclusive writer. The fixed location is beneath the descriptor's trusted journal root: `qmb-results/<resolved-config-digest>/results/ct-32.json`. Verification checks the stored identity against the terminal. No receipt identity/schema is rewritten.

`project_operator_replay` consumes the original pinned run context and one validated builder/input snapshot. It reopens stored CT32 and operator-bound CT29, then calls existing projection validation/filtering. It neither executes a replay to fill missing data nor publishes an Experiment Ledger entry. Missing or corrupt CT32 refuses. The real replay fixture now pins its actual registry-as-of and selected Bot, rather than weakening those existing source checks.

The CLI transport now refuses a query child's nonzero exit. Previously an exit-7 child produced an `Ok` query receipt. This does not yet connect the public CT40 projection route.

The extended installed CLI test verifies stored identity, read-only domain projection, one builder load, unchanged fixture data bytes, corrupt/missing refusal and no backfill. Final relevant replay/projection/source-integrity regression: **45 passed** (`evidence/projection-final.txt`). Full QMA regression: **1,879 passed** (`evidence/qma-continuation.txt`). Independent focused review: **13 passed**, no actionable findings. Owned-file lint/format and typing pass. These remain synthetic domain tests, not legitimate CT47/CT40 provenance acceptance.

## Windows locking: concrete proposal pending ownership coordination

All ten catalog/download ingestion failures were reproduced again in `task-8/evidence/windows-ten-red.txt` (10 failed, 16 passed), with POSIX-only `fcntl` as the shared cause. Native-process exclusion tests reproduce the same defect (2 failed, 1 passed).

The parent explicitly required coordination with spot lane `01a10656` before editing QMF intake. The production file remains unchanged pending that response. The reviewed, unapplied proposal is `task-8/locking-proposal.patch`, targeting only `packages/qmf-data/src/qmf/data/intake_authority.py`.

It preserves POSIX flock and uses standard-library Windows msvcrt offset-zero, one-byte native locking, including on an empty file. Nonblocking acquisition retries contention indefinitely, propagates other errors, keeps the lock file, closes descriptors on acquisition/unlock errors, and makes close idempotent. It adds no dependency and never substitutes a thread-only lock. Independent review recommended removing EDEADLK from retryable errors; the proposal includes that tightening. The test proposal is `task-8/locking-tests-proposal.py`. Implementation and real production ingestion/concurrent-writer verification remain pending coordination; isolated tests of the exact proposed module are distinct from acceptance of the actual QMF path.

Official references: [Python msvcrt](https://docs.python.org/3/library/msvcrt.html), [Microsoft locking](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/locking?view=msvc-170), [Windows file lock lifecycle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfile).

## Public projection decisions

The actual root causes are separate:

1. `qmb.analysis.project@1` admits only `run_fp1/as_of`, omitting QMB's required nonempty predicate.
2. QMA transmits query JSON in `QMA_QMB_DOOR_PAYLOAD`; `analysis_project` ignores it and receives no source/predicate.
3. Operator replay retained only CT32 digest, not its body — fixed in this continuation.
4. The host requests coordinated publication without a dispatch lease/model deployment; publication refuses even if QMB succeeds.

Proposed bounded public repair, awaiting the exact schema/authority choice: require `predicate`; resolve source only through the operator-bound owner's durable DONE QMB handle and verified expected/result artifacts; refuse missing/ambiguous/corrupt sources; pass original pinned context to QMB without caller-selected roots; keep coordinated `analysis.published` under the existing dispatched-Agent flow. Require successful child exit and exact source/predicate/as-of result matching. Do not invent an Agent lease for a read query. Clarify whether `run_fp1` denotes ExperimentSpec or resolved run config before binding that selector; current process treats it as the former while QMB terminal result distinguishes both.

## Legitimate CT47/Quant authoring: precise missing edges

Read-only independent review found:

- `create_quant` is a pure operator-authorized creation function; production CT40 `quant.create/desk.create` handlers and durable definition persistence are absent. Mailbox registration alone retains Quant in memory; journal restore does not reconstruct its definition.
- The daemon does not invoke TaskGraph dispatch in the normal authoring flow. `submit_agent_request` snapshots do not establish canonical Agent/Task/TaskLedger provenance and currently expose corpus browse.
- `ExperimentSpecService.register` persists supplied lease/attempt/deployment but has no production registration ingress deriving them from an actual dispatched Task. Shape-valid fixture strings are not proof.
- Current execution and Experiment Ledger authority require the same registering Task/mission; a separate authoring Task followed by a different execution Task is incompatible without a material contract amendment.

Recommended legitimate flow: authenticated operator creates/persists Quant and Desk; host resolves recorded request/config/data/environment and configured model/harness; compiler materializes the same operation Task with full pinned input; daemon creates the Agent and dispatches that Task; an actual authorized provider/model execution establishes observed deployment and attempt; host registers CT47 from freshly resolved canonical state; exact-hash authenticated CT40 places real QMB CLI execution. Renderer/model output must never supply lease, attempt, owner, deployment authority or roots.

The requested decision is Agent-authored same-Task registration with a real already-authorized provenance source, versus a new operator-authored registration mode. The latter changes ledger authority/security semantics. No model execution, fabricated provenance, new HTTP experiment service, live provider, credential or spend was introduced.

## Recovery and readiness limits

Terminal persistence currently precedes CT32 storage and occurrence attribution. A crash in that window fails closed; query cannot backfill. Full cancellation/recovery remains unproven. Repeated execution requires a separately verified reuse policy for an identical existing artifact; exclusive writing must not be relaxed to overwrite. Operation readiness still depends on authority/source/dependency checks and cannot be inferred from PID/listener health.

This is a draft mapping for parent review. No canonical documentation, factory, UI or native lane was modified.
