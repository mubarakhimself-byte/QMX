# Windows intake and QMB recovery: review draft

This follows checkpoints `23fba3d5` and `797159d1`. Parent coordination explicitly assigned this lane the existing QMF intake locking files. The previous proposal is now applied, with real production-path tests. No canonical Docs/BMAD files or native/research lane files were edited.

## Implemented bounded fixes

- CT15 uses native Windows byte-range locking on the permanent offset-zero lock file, while retaining POSIX flock. Contention retries EACCES/EAGAIN; other errors propagate. Acquisition/unlock failure closes descriptors; repeated close is harmless. There is no thread-only substitute or new package dependency.
- Held-writer JSONL prefix synchronization opens Windows rotations with nontruncating `r+b`, enabling actual fsync. POSIX retains `rb`. The previous read-only Windows handle produced Bad file descriptor once ingestion passed the original fcntl failure. Only an already-held writer may synchronize the prefix; exact persisted bytes remain unchanged.
- The two-process CT15 ingestion test uses spawn, with cleanup covering partial startup as well as successful/failed execution. Actual native contention, eleven-second contention, normal release, terminated holder release and descriptor failure cleanup are tested.
- QMB checks existing confirmation and journal state before economic replay. An exact completed invocation returns only after existing full artifact/terminal/occurrence verification. Missing or corrupt CT32, missing occurrence, changed attempt, and partial Book journal refuse without rerun or backfill. The original retry produced duplicate sequence zero in a retained Book journal; the installed CLI regression reproduces that failure before the fix.
- Owned comments/docstrings were corrected to comply with the repository's vocabulary guard. No guard was weakened.

Windows flushing references: [Python fsync](https://docs.python.org/3/library/os.html#os.fsync), [Microsoft FlushFileBuffers: writable handle requirement](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers). Lock references: [Python msvcrt](https://docs.python.org/3/library/msvcrt.html), [Microsoft locking](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/locking?view=msvc-170).

## Verified data connection and limits

The recorded synthetic Dukascopy historical bi5 fixture now really ingests, restarts/reingests idempotently and appends a new revision while preserving original immutable Parquet bytes. Exact production requests/results/refusals are retained in `task-8/evidence/dukascopy-connection-final/request-result-refusals.json`.

That fixture exposes an additional production boundary: `download(side=both)` currently archives only bid. Replay requires one persisted bid and ask observation per frontier. A second ask request uses the identical provider-native CT15 key and correctly refuses changed facts. Quality and the persisted CT12 replay request both refuse missing ask. The implementation does not relabel provider-native IDs, rewrite retained receipts, recover discarded ask values from imagination, or weaken intake uniqueness.

For an independent supported single-observation path, `test_download_replay_connection.py` decodes explicitly synthetic local provider bytes whose own IDs are already side-specific. It invokes the existing ProviderAdapter/download/CT15/CT10 APIs for each side; rebuilds stores for reingest; checks real quality and coverage; admits an explicitly linked correction without altering originals; pins the original six observations in persisted CT12/replay input; installs the trusted diagnostic Book descriptor; executes actual installed QMB CLI; verifies actual stored CT32/terminal; and reopens projection in a fresh Python process. Its diagnostic Bot registry is a domain fixture. Its explicitly labelled spec identity is not a CT47 registration. It mints no Agent/model provenance and claims no authenticated CT40 acceptance.

Corrected CT10 input itself remains refused by QMB's existing `correction_of` guard until an explicit resolution fold exists. The diagnostic replay uses its original immutable pins; it does not claim to evaluate the correction. The production Dukascopy paired-quote representation and correction-resolution fold require a contract-preserving follow-up. Changing the same CT15 key to mean multiple observations without a versioned mapping would change retained receipt semantics.

## Recovery scope

Sequential repeat of an exactly completed delegated Book invocation reuses verified durable truth without duplicate effects. Installed CLI regressions also remove/tamper artifacts, occurrence and terminal, or change attempt, and compare all retained fixture bytes around each refusal. Partial journal recovery is fail-closed, not automatic resumption. QMA single-run occupancy remains required: this check-then-execute change is not a standalone interprocess transaction lock for arbitrary concurrent QMB CLI invocations. Authenticated CT40 cancellation/recovery remains unproven without legitimate authoring provenance.

## Precise decisions for the parent

1. Public projection selector: QMA currently interprets `run_fp1` as ExperimentSpec; QMB's completed `run_fp1` means resolved configuration and its result separately carries `experiment_spec_fp1`. Recommend selecting the completed resolved run and adding required `predicate`. Resolve only the bound owner's unambiguous DONE handle and verified expected/result artifacts. The query CLI must consume that pinned original context. Preserve query occupancy and existing role/grants. If preserving the existing ExperimentSpec interpretation, require a separately named resolved-run selector and reject multiple matching executions; do not guess.
2. Projection publication: a public read query lacks a dispatch lease/model deployment. Recommend read-only projection through the current owner/grant checks, with publication remaining on the existing dispatched-Agent path. Automatically manufacturing a lease to publish a read would change ledger authority.
3. CT47: recommend the existing Agent-authored path using the same registering/executing Task and mission, deriving lease/attempt/deployment from actual canonical dispatch and observed model execution. An operator-authored alternative would require an explicit authority/security contract amendment. Current production Quant/Desk durable authoring, normal Task dispatch, and canonical registration ingress remain absent. No real observed provenance source was supplied, and this task forbids provider execution/spend; shape-valid fixture strings cannot satisfy this gate.

## Operational readiness and review evidence

Listener/PID health proves reachability, not operation readiness. Backtest readiness requires owner/binding/config revision, current grants, persisted replay input/CT12, trusted runtime descriptor, execution declaration/provider and observed authoring provenance. Projection additionally requires completed owned source artifacts and predicate. Missing source, corrupt archive, stale config/grants, ownership or provenance must refuse before effects.

Initial actual lock/ingestion regression: 56 passed, 3 skipped. Recovery negative regression: 2 passed, with multiple real CLI children. Joined synthetic domain path: 1 passed before adding fresh-process projection, which is included in final verification. Full QMA packages: 1,876 passed; root workspace tests are included in final commit verification. Full QMF/QMB sweep: 1,994 passed, 14 failed, 22 skipped. No ingestion failures remain. The broad failures expose native/research lane issues, an intentionally unfinished alternative-study ingress, obsolete projection examples, encoding/path assertions and broad guards; the two owned vocabulary violations have been corrected without weakening guards. Exact final-commit tests, remaining failures and independent review are recorded in the outer final handoff.

Large backup/telemetry work remains outside this lane. Full governed acceptance remains false. Parent integration, push and merge were not performed.
