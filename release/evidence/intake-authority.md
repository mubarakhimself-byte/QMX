# Durable CT-15 intake authority

QMF now owns the durable CT-15 `(source, source-native id, revision)` mapping in
the per-world CT-13 journal. Each key first records an `intent` containing the
exact normalized CT-10 row and its full observation fingerprint. QMB admits that
retained row through the existing CT-10 boundary, then records an explicit
`complete: true` event. Both writes use `JournalWriter` and checked stream
recovery, so a restart can replay an uncompleted intent after a lost CT-10
acknowledgement. The QMB `.qmb_intake_keys.jsonl` side channel is removed.

Retries compare a provider-fact fingerprint that excludes only receipt metadata
(writer, sequence, receive-wall-time). Matching facts reuse the retained CT-10
observation and its original known-at value; changed facts under the same key
refuse, while a new revision appends a distinct observation. The same mapping is
projected from the entire world journal across writer boot epochs.

The authority uses one fixed `ct15-intake-authority` stream per world. Multiple
handles resumed against the same JournalStore share its writer, canonical mapping,
and reservation lock; every reservation rebuilds the mapping from checked CT-13
events before it can reuse a key. Resume and reservation first append a recovery
barrier and verify its typed physical store receipt against the exact raw row and a
checked journal reopen. This fsync barrier makes a visible prefix usable only after
a successful durability boundary, including after a prior append failed after its
line became visible. Alternate stream names are refused so they cannot partition
world-local key uniqueness.

QMB marks CT-15 completion only after CT-10 returns an `ObservationReceipt` whose
observation fp1 and retained archive receipt match the canonical row, then reads
that archive artifact back through `SourceObservationBoundary.read` and verifies
the complete observation identity. Unknown or incomplete acknowledgments leave
the durable intent incomplete and return a typed refusal.

The former assertion that any QMB-authored file implied a second data store was
replaced with checks for the QMF CT-13 intent/completion and their full CT-10
fingerprint. The regressions cover same-key restart idempotence, changed facts,
new revisions, changed receive/writer metadata, and a real raw-room append whose
acknowledgement is lost before reopening and replaying the retained intent.

Validation run after the held-out corrections:

```text
.venv/bin/python -m pytest -q -p no:cacheprovider -c pyproject.toml qmb/tests/test_data_download.py qa/tests/epic_18/test_e18_l2_download.py packages/qmf-data/tests/test_journal_producer.py packages/qmf-data/tests/test_source_boundary.py
66 passed

.venv/bin/ruff check packages/qmf-data/src/qmf/data/intake_authority.py packages/qmf-data/src/qmf/data/__init__.py qmb/src/qmb/data/download.py qmb/tests/test_data_download.py --output-format concise
All checks passed

.venv/bin/pyright packages/qmf-data/src/qmf/data/intake_authority.py packages/qmf-data/src/qmf/data/__init__.py qmb/src/qmb/data/download.py
0 errors, 0 warnings, 0 informations
```

Independent Sol retest and the full release install/gate suite remain pending.
