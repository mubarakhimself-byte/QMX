# Data integrity repair evidence

Candidate: `release/rc-2026-10-01`. Validation used the existing workspace environment
with `uv run --no-sync`; Python was 3.14.7. The root `uv sync` was left untouched.
Fixtures used temporary synthetic stores only. No production data, external providers,
credentials, or live services were accessed.

## Baseline and repaired contracts

Before source edits, the packet reproduction
`uv run --no-sync pytest -q /workspace/qmx-audit-inputs/packets/reproductions/test_foundation_data_regressions.py`
reported `3 failed, 3 passed in 0.70s`. DF01 failed because same-handle retry acknowledged
an event while the JSONL stream remained malformed; DF02 failed because a nested mapping
under a sequence could mutate the fragment's fp1 content; DF03 failed because a missing
supersedes witness caused the room-wide read to refuse before exact retry could restore it.
The reopen-before-retry, corroborates-retry, and RegistrationRecord deep-freeze controls
passed.

The same packet command after repair reported `6 passed in 1.54s`. The committed
regressions additionally cover partial writes, repeated partial retry, complete-line
fsync uncertainty, corrupt newline-terminated byte preservation, rotation ordinal/offset/
sequence recovery, witness failure followed by reopen, torn-edge recovery, witnessless
edge refusal without witness manufacture, a competitor committing while an intent is
pending, and nested mapping/list/tuple freeze input/output checks. A pending supersedes
retry rechecks the room-wide graph and allows only its exact fingerprint and identity to
be unwitnessed; held-out review also confirmed pending incoming-fork, outgoing-fork, and
cycle conflicts refuse while the competing edge remains readable.

The JSONL engine now marks append state uncertain before physical I/O. Both `find` and a
direct retrying `append` rebuild the index before answering or writing. Recovery keeps the
committed prefix, quarantines a no-LF tail through the existing recovery path, and leaves
newline-terminated malformed bytes untouched while refusing. A complete valid line after
an fsync error is reconciled by ordinary idempotency lookup and read back once.

Registry as-of and config fragments recursively freeze every mapping inside every nested
list/tuple. Identity content and fp1 remain unchanged; public container types remain
mapping proxies and tuples. ConfigFragment is source-inspected and covered with a
constructed fragment; this does not claim a previously observed schema-valid ConfigFragment
failure or an actual sweep failure.

## DF04 disposition

Deferred before adoption. A source search found `record_multiroom` / `extra_writes` only in
qmf-data's JournalWriter implementation, with no production caller. Its callback list is
still held in memory and does not survive restart. The application that eventually adopts
multi-room writes must own a durable intent/completion record or refuse resume until it
reconciles the secondary writes. qmf-data does not become a workflow scheduler, and this
repair adds no multi-room restart claim.

## Commands and results

All commands ran from the release root and used the pre-existing environment:

```text
uv run --no-sync pytest -q packages/qmf-data/tests
551 passed in 7.12s

uv run --no-sync pytest -q packages/qmf-registry/tests
168 passed in 2.93s

uv run --no-sync pytest -q qmb/tests/test_deep_fragment_immutability_contracts.py qmb/tests/test_config_fragments.py qmb/tests/test_registryread.py
38 passed in 2.47s

uv run --no-sync pytest -q /workspace/qmx-audit-inputs/packets/reproductions/test_foundation_data_regressions.py
6 passed in 1.54s

uv run --no-sync ruff check packages/qmf-data/src/qmf/data/store/engines/jsonl.py packages/qmf-data/tests/test_integrity_recovery_contracts.py packages/qmf-registry/src/qmf/registry/persistence.py packages/qmf-registry/tests/test_ct09_persistence.py qmb/src/qmb/registryread/as_of.py qmb/src/qmb/config/fragments.py qmb/tests/test_deep_fragment_immutability_contracts.py
All checks passed

git diff --check
passed (no output)
```

Independent reviewer command:

```text
.venv/bin/python -m pytest -q -p no:cacheprovider packages/qmf-data/tests packages/qmf-registry/tests qmb/tests/test_registryread.py qmb/tests/test_config_fragments.py qmb/tests/test_deep_fragment_immutability_contracts.py .
757 passed in 8.85s
```

The broad command `uv run --no-sync pytest -q qmb/tests` ran `1,294 passed, 13 failed in
139.12s`. Failures were outside the changed fragment modules: one CT-32 documentation
substring assertion; QMB sandbox/host/example worker and run-config failures; and study-stop
/ workbench-lane failures. This release workspace has concurrent unrelated source and
documentation edits, so those failures are recorded as observed and are not attributed to
the immutable-reference patch. The focused registry-read and config-fragment suites above
passed.

Compatibility: no public signatures, schemas, fp1 recipes, or reference container types
changed. The edge write adds an internal content-addressed pending-intent record for
supersedes retries. It is not served as lineage evidence; the JSONL edge remains unreadable
until its integrity witness exists. Existing stores need no migration. An edge written by
the previous implementation that already lacks its witness has no intent record and stays
fail-closed; it requires operator-directed recovery. This does not certify power-loss,
Windows filesystem, deployed-storage, or universal durability behavior.
