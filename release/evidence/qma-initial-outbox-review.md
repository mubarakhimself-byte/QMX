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
