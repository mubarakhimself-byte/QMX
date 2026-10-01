# Independent INITIAL outbox review

Verdict: **FAIL** for the initial held five-path source snapshot below. This is source publisher/migration review, not normal mini-app, complete current-worker, terminal-proof, installed, or second-pack approval. No product/test/Git edits by reviewer.

- `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/outbox.py`: `0b045552860d854144768e7c296c604a0930caded68723d398bd2e7faa95a45b`
- `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/projection.py`: `7e170836135ff6b376749e135510ce971c9d5f93a38a4703592ffb9a454b0386`
- `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/dispatcher.py`: `2379bbd79e640ce6de1653d41470b3dd6e030411d1626ab801e37805ffcdd347`
- `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/__init__.py`: `f0480d74ef389964ef94207c1bc9ba06fb3365cbc42739f34e8402baeddd0c73`
- `qmx-agents/packages/qma-daemon/tests/test_task_graph_outbox.py`: `b96d7f6939a7e581caba395b9bb61b55a5a9e3bf50c5e9b49a6afd60528db393`

With PYTHONPATH=qmx-agents/packages/qma-core/src:qmx-agents/packages/qma-daemon/src:qmx-agents/packages/qma-wire/src, `.venv/bin/python -m pytest -q -p no:cacheprovider` on test_task_graph_outbox.py, test_task_graph_state_edges.py, test_procedure_door_successors.py: **32 passed in2.28s**. These positives do not close the following independent failures.

`PYTHONPATH=... .venv/bin/python /tmp/review_initial_outbox.py` uses a real compiled READY root and actual DaemonProcess SQLite projection/public TaskGraphDispatcher. Valid operation inputs dispatch one outbox row and a lease. Ordinary replacement op_version=True also dispatches SUCCESS with one row/lease because successor_target substitutes version1. Replacing only root Task.mission_id with foreign text, retaining original compiled graph/Mission, also succeeds with one row/lease. Require exact operation descriptor/target validation and coherent Task/graph/Mission linkage before publication/environment/lease effects; later receiver refusal is insufficient.

Migration FAIL by source: projection.ensure_schema opportunistically renames/copies/drops the NOT NULL predecessor table during ordinary startup, retaining KNOWN_STORE_SCHEMA_VERSION=1. Governing persistence/schema.py refuses unknown/new stores and never silently upgrades. persistence/lifecycle.py names FR-Q37/AD-27 explicit preflight→backup→dry-run→transform→verify/restore. The migration test only validates preserved selected columns; it does not prove versioned backup/distinct destination/failure restore or old startup refusal. Root independently identified this and instructed an explicit versioned migration, rather than relaxing the root discriminator.

Existing authored-template/crash/reopen positives remain meaningful: no fabricated predecessor, initial-root partition and null predecessor, rolled-back outbox/no lease on injected transaction failure, real dispatch acceptance and reopened same invocation. Those bounded positives do not waive malformed operation, foreign Mission identity, or schema authority. Findings delivered execution/root; held source must be corrected and frozen before approval.


## Explicit migration correction — remaining FAIL

Corrected `/tmp/review_initial_outbox.py` genuine root still dispatches one row/lease, while bool op-version and foreign Task Mission now refuse with ZERO rows/leases. Root operations now pin full approved input payload hash.

Actual local `/tmp/review_outbox_migration.py`: ordinary source migrates with unchanged source bytes and extra table retained. Source named source#part.sqlite instead returns refusal BUT creates unintended sibling source: unescaped SQLite file URI loses the read-only query inside a fragment. An open WAL writer is admitted. `/tmp/review_migration_snapshot.py` uses real SQLite commit to a benign extra table between actual backup and destination copies: migration SUCCESS, backup has before row only, destination has before plus during-migration row. Main-file hash excludes WAL so this full-store drift is not detected. Need safe URI construction, actual sole-writer/stopped-WAL proof, destination derived from the verified single backup, and full schema/table verification. Root/execution notified. No external target, credentials, provider, product/test edits, or Git mutation.

Observed exact seven-path snapshot:
- `qmx-agents/packages/qma-daemon/src/qma/daemon/persistence/task_graph_outbox_migration.py`: `3a91bb1e94309f9a4315e884e5c9512a18d65d5b246845c83b43e940209e78f6`
- `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/outbox.py`: `74a7b63072446d7af2eda14db4e13d292a96b6ada6ecbd10e5222331e3d42529`
- `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/projection.py`: `1fdab39b139fcd9639df1e60352170da8b453e969c2dc6e605b46fd1925e54d9`
- `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/dispatcher.py`: `e08a27bdfd94b406dc183b6216ceeb0947a89ed2d1f213077e475843c013f854`
- `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/__init__.py`: `f0480d74ef389964ef94207c1bc9ba06fb3365cbc42739f34e8402baeddd0c73`
- `qmx-agents/packages/qma-daemon/tests/test_task_graph_outbox.py`: `f380c8a044a9105c97df5ae88378bee215b3a5eae3abd492de7c014f48091490`
- `qa/integration/test_qma_registered_replay.py`: `03952c1de521a4242e32d657ca267936da8c55062e21d4a5409230d17b770668`

## Bounded follow-up against held migration `928122b7` — FAIL

This follow-up records the original seven held paths only. All hashes matched at entry; the four taskgraph implementation hashes remained unchanged at the post-probe check. Migration owner began repair after findings were delivered. Those ongoing edits are not covered by this verdict. No product/test files or assertions were edited, no commit made, and no provider/security testing occurred.

| Held path | SHA256 |
| --- | --- |
| `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/outbox.py` | `74a7b63072446d7af2eda14db4e13d292a96b6ada6ecbd10e5222331e3d42529` |
| `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/projection.py` | `1fdab39b139fcd9639df1e60352170da8b453e969c2dc6e605b46fd1925e54d9` |
| `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/dispatcher.py` | `e08a27bdfd94b406dc183b6216ceeb0947a89ed2d1f213077e475843c013f854` |
| `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/__init__.py` | `f0480d74ef389964ef94207c1bc9ba06fb3365cbc42739f34e8402baeddd0c73` |
| `qmx-agents/packages/qma-daemon/src/qma/daemon/persistence/task_graph_outbox_migration.py` | `928122b784f040459ba5b22f140801afa5af44dc68328812f767d99bf64ae0d6` |
| `qmx-agents/packages/qma-daemon/tests/test_task_graph_outbox.py` | `89f120a15a3fee6648f8710c35ed2f55bc2dfa251b2131caeefc34ae2dbcbd66` |
| `qa/integration/test_qma_registered_replay.py` | `03952c1de521a4242e32d657ca267936da8c55062e21d4a5409230d17b770668` |

Commands (cwd `/workspace/QMX-release`; `PYTHONPATH=qmx-agents/packages/qma-core/src:qmx-agents/packages/qma-daemon/src:qmx-agents/packages/qma-wire/src`):

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider \
  qmx-agents/packages/qma-daemon/tests/test_task_graph_outbox.py \
  qmx-agents/packages/qma-daemon/tests/test_task_graph_state_edges.py \
  qmx-agents/packages/qma-daemon/tests/test_procedure_door_successors.py \
  qa/integration/test_qma_registered_replay.py
```

First invocation: **43 passed, 1 failed in 17.58s**, because the real local replay child could not find `qmb` on the ambient PATH. Repeat with `PATH=/workspace/QMX-release/.venv/bin:$PATH`: **44 passed in 27.22s**. This corrects the local command environment without changing any test or assertion. The integration path uses an actual registered template, normal MissionCompiler, materialize and public dispatch, which automatically produces the root outbox; it does not seed that row by hand. Provider, complete current-worker and installed-entrypoint acceptance are separate.

Independent local diagnostics used `.venv/bin/python /tmp/review_initial_outbox.py`, `.venv/bin/python /tmp/review_outbox_migration.py` and `.venv/bin/python -` with the archived exact heredoc bodies below.

**Bounded corrected positives:** the valid compiled root dispatches one INITIAL row/lease. Boolean operation version and foreign Task Mission alone refuse before effects (zero rows and leases). Root payload hash is pinned. Startup refuses the old unmarked predecessor-required table without a silent layout transform. URI `#` sources now migrate to a distinct backup and destination with unchanged source bytes and retained sentinel table rows. Pending WAL sidecars refuse before output creation. An actual `root/.daemon_writer` acquired through `DaemonWriterLock` blocks migration of the real `root/daemon/daemon.sqlite` layout with no output files. Source inspection and observed copies confirm dry-run and destination both derive solely from the backup. Existing rollback/reopen/refuser controls pass.

**Remaining failures:**

1. **P1 — present non-string operation id skips operation publication/validation** (`taskgraph/dispatcher.py:769`). Change only `op_id` to `True` on the otherwise valid compiled READY QMB root. Public dispatch returns SUCCESS, creates zero outbox rows, and retains both dispatch and environment leases. The guard treats malformed present operation ids as generic non-operation Tasks. Distinguish an absent operation declaration from a present malformed value and refuse the latter before effects.

2. **P1 — Task/graph agreement does not establish actual Mission linkage** (`taskgraph/dispatcher.py:771`). Change the graph Mission id and all of its Task Mission ids to the same foreign id, while materializing with the original genuine compiled Mission. Public root dispatch returns SUCCESS with one outbox row and both leases. Require the operation Task/graph to resolve to the materialized Mission identity and owner before publication/placement. The simpler foreign-Task-only refusal is corrected but insufficient.

3. **P1 — schema-only WAL drift escapes snapshot verification** (held migration `_source_snapshot_matches`, `_database_rows`). Start a stopped WAL-mode source with no sidecars, an exact v1 outbox and a retained ordinary table. After the actual source→backup copy, a local SQLite writer commits `CREATE INDEX preserved_note_idx ON preserved(note)` into WAL. No row values change and the main file SHA remains unchanged. Migration returns SUCCESS: source has the index, backup and destination do not. Table rows alone are not a full-store schema census. Include schema objects in source/backup/destination verification or reject all reappearing sidecars through completion; preserve the verified backup and refuse on drift.

All three findings were delivered to root and Execution owner. A later optional view probe encountered the owner actively editing the migration and raised a closed-connection schema-census error. It provides no frozen-source view finding and no current approval; owner reported correcting that intermediate ordering. Further probes stopped on root instruction.

All local programs and command/result/source identity notes are preserved in `/workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/`; `SHA256.json` binds every archived file. Exact inline diagnostics are now `review_initial_extra.py`, `review_migration_schema_snapshot.py`, `review_migration_lock_and_schema_attempt.py` (retained fixture-error attempt), and `review_migration_view_in_progress.py` (source-drift observation). `REVIEW_ARGV_SOURCE_NOTES.json` preserves original argv, environment and results. Prior four retained programs remain intact.

**Pending:** a fresh frozen-source correction review; broader coupled journal/SQLite/ledger/ExperimentSpec/JobHandle persistence; normal installed entrypoint; complete current worker/terminal proof; provider and security lanes. The 44 local test positives do not waive the three held-source failures or constitute release acceptance.

## Frozen seven-path correction re-review — PASS, bounded

Independent GPT 6.1 Sol ordinary local persistence re-review on 2026-10-01. These hashes matched before and after test/regression/static execution. This append closes the three prior held-snapshot P1 findings for this exact new freeze; prior FAIL evidence remains historical. No product/test edits, commits, new probe programs, security tests or provider calls.

| Path | SHA256 |
| --- | --- |
| `qmx-agents/packages/qma-daemon/src/qma/daemon/persistence/task_graph_outbox_migration.py` | `f3ab8931d0458ab6d6ffa6d27c370c35d970ae725f55add3b11bb4a077e4d79d` |
| `qmx-agents/packages/qma-daemon/tests/test_task_graph_outbox.py` | `d9031b7c5d9fc6f5678aa3f03b3673cb909f75525c14ed6e859128fdc3927e2e` |
| `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/outbox.py` | `74a7b63072446d7af2eda14db4e13d292a96b6ada6ecbd10e5222331e3d42529` |
| `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/projection.py` | `1fdab39b139fcd9639df1e60352170da8b453e969c2dc6e605b46fd1925e54d9` |
| `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/dispatcher.py` | `fdecc716ced2546df82cab47dc57d580b1defe0b76733ad8ed28c4fbecad3f49` |
| `qmx-agents/packages/qma-daemon/src/qma/daemon/taskgraph/__init__.py` | `f0480d74ef389964ef94207c1bc9ba06fb3365cbc42739f34e8402baeddd0c73` |
| `qa/integration/test_qma_registered_replay.py` | `03952c1de521a4242e32d657ca267936da8c55062e21d4a5409230d17b770668` |

Cwd `/workspace/QMX-release`; `PYTHONPATH=qmx-agents/packages/qma-core/src:qmx-agents/packages/qma-daemon/src:qmx-agents/packages/qma-wire/src`; test command uses `PATH=/workspace/QMX-release/.venv/bin:$PATH`:

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider qmx-agents/packages/qma-daemon/tests/test_task_graph_outbox.py qmx-agents/packages/qma-daemon/tests/test_task_graph_state_edges.py qmx-agents/packages/qma-daemon/tests/test_procedure_door_successors.py qa/integration/test_qma_registered_replay.py
```

**47 passed in 27.90s.** This is this scoped latest-source suite, not a rerun or approval of the owner’s broader earlier 86-test snapshot. Existing generic non-operation Tasks still dispatch through predecessor/state-edge controls. The real registered replay integration compiles the operation root via normal MissionCompiler and lets public dispatch create its outbox automatically.

The following unchanged archived programs each ran as `.venv/bin/python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/<program>` with the above PYTHONPATH and exited 0:

- `review_initial_outbox.py`: valid actual compiled root gives one row/lease; boolean operation version and foreign Task Mission refuse with zero rows/leases.
- `review_initial_extra.py`: present boolean operation id and coherent foreign graph/Tasks versus the genuine materialized Mission now both refuse with zero outbox rows, zero dispatch lease and zero environment lease. The three operation/Mission failures are closed. Source distinguishes absent operation inputs from present malformed declarations and joins Mission id, graph id/template, owner and the Task/node set before publication/placement.
- `review_outbox_migration.py`: normal and `source#part.sqlite` migration succeed with original source bytes unchanged and retained ordinary table rows; pending WAL refuses with no outputs.
- `review_migration_schema_snapshot.py`: the same actual post-backup `CREATE INDEX preserved_note_idx` WAL-only change now refuses even though the main SHA remains unchanged. Only source→backup occurs; backup remains the original schema, no destination is created. The schema-only snapshot failure is closed.

Static migration review confirms actual source-root `DaemonWriterLock` acquisition, URI-safe read-only SQLite opens, main SHA plus full user-table-row and sqlite_master object census recheck after backup and before successful return, exact backup/source schema-and-record equality, and preservation checks after disposable dry-run and actual destination transform. Both transformed copies derive solely from the verified backup. Source remains unchanged; verified backup and original restore path remain available on refusal. Layout 2 retains the existing outbox rows and changes nullable predecessor plus explicit marker only; unrelated schema loss refuses instead of receiving success. Existing old-startup refusal, five parent step receipt, scratch cleanup, transactional rollback, receiver/reopen and row/schema drift controls all pass.

`CORRECTED_REVIEW_ARGV_SOURCE_NOTES.json` in the existing diagnostic archive binds exact argv, environment, programs, results and this seven-file freeze. Existing archived scripts and original notes verified against their prior SHA manifest before reuse; updated `SHA256.json` binds the new notes as well. No earlier diagnostics were overwritten.

**No remaining finding in this bounded correction review.** Broader coupled journal/SQLite/ledger/ExperimentSpec/JobHandle persistence, complete normal worker/terminal proof, Book coupling, final installed entrypoint, provider/security and final immutable-candidate factory/static/QA/release acceptance remain separate and pending. Corrected INITIAL publication and SQLite-copy migration do not fill those lanes.
