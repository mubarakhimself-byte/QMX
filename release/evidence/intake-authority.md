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
handles resumed against the same JournalStore share the canonical mapping and
reservation lock. Initialization is serialized through publication of that shared
coordinator. Every resume and reservation acquires a room-local OS lock, refreshes
the writer sequence and stream index, rebuilds keys from checked CT-13 events, and
persists a recovery barrier before proceeding. Prefix recovery fsyncs every extant
rotation chunk and the stream directory metadata, so a barrier in a later chunk
cannot authorize an earlier visible but unsynced intent. A blocked event is retried
only if its sequence is still free or already contains that exact event; conflicting
sequence history returns a typed refusal. Alternate stream names are refused so they
cannot partition world-local key uniqueness.

QMB marks CT-15 completion only after CT-10 returns an `ObservationReceipt` whose
observation fp1 and retained archive receipt match the canonical row, then reads
that archive artifact back through `SourceObservationBoundary.read` and verifies
the complete observation identity. Unknown or incomplete acknowledgments leave
the durable intent incomplete and return a typed refusal.

The former assertion that any QMB-authored file implied a second data store was
replaced with checks for the QMF CT-13 intent/completion and their full CT-10
fingerprint. The regressions cover concurrent in-process resume initialization,
two real filesystem-backed download processes sharing one writer sequence, same-key
restart idempotence, changed facts, new revisions, changed receive/writer metadata,
and an fsync fault in a rotated intent chunk followed by recovery that proves that
prior chunk was synced before reuse.

Validation run after the held-out corrections:

```text
uv run --no-sync pytest qmb/tests/test_data_download.py qa/tests/epic_18/test_e18_l2_download.py packages/qmf-data/tests/test_journal_producer.py packages/qmf-data/tests/test_source_boundary.py -q
68 passed

uv run --no-sync ruff check packages/qmf-data/src/qmf/data/intake_authority.py packages/qmf-data/src/qmf/data/journal_producer.py packages/qmf-data/src/qmf/data/store/engines/__init__.py packages/qmf-data/src/qmf/data/store/engines/jsonl.py packages/qmf-data/src/qmf/data/store/journal.py packages/qmf-data/src/qmf/data/store/streams.py qmb/src/qmb/data/download.py qmb/tests/test_data_download.py --output-format concise
All checks passed

uv run --no-sync python -m pyright packages/qmf-data/src/qmf/data/intake_authority.py packages/qmf-data/src/qmf/data/journal_producer.py packages/qmf-data/src/qmf/data/store/engines/__init__.py packages/qmf-data/src/qmf/data/store/engines/jsonl.py packages/qmf-data/src/qmf/data/store/journal.py packages/qmf-data/src/qmf/data/store/streams.py qmb/src/qmb/data/download.py
0 errors, 0 warnings, 0 informations
```

Independent Sol retest and the full release install/gate suite remain pending.


Root integration validation after `be314578`:
`uv run --no-sync pytest packages/qmf-data/tests -q` — PASS, 556 tests in
4.99 seconds. Exact output `/workspace/qmx-qmf-data-post-intake.log`.
QMF data product sources remained identical to the reviewed CT15 correction;
other application integration was still in progress. This broadens the
bounded data regression evidence, not whole-release acceptance.
