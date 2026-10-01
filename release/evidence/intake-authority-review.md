# Independent durable intake review

Reviewed 1219cd64 on 2026-10-01. No provider calls or product edits. Combined focused intake/installer/release-gate target: **154 passed** (overlaps other reported targets).

B-11 ownership remains correct: new durable authority is QMF CT13, QMB routes normalization and raw admission through QMF. Replacing the former application-side ledger assertion with independent checked CT13/raw observations does not waive the one-data-layer requirement. Existing restart changed-facts, receipt metadata and real raw lost-ACK controls remain substantive positive controls.

Four actual held-out failures remain:

1. Two `IntakeAuthority.resume` handles on the same actual JournalStore and stable WriterId, both obtained before reserve, have separate stale `_keys`. Same world/key/provider facts but changed receive time yields two accepted distinct canonical CT10 fingerprints. Refresh/serialize canonical authority state at reservation, with one store-wide transaction/ownership boundary; merely separate Python dictionaries are insufficient.
2. Public `stream_name='one'` and `'two'` authorities accept independent canonical rows for the same world/key. Fix the globally canonical authority stream rather than allow callers to partition uniqueness by stream. World remains the legitimate scope boundary.
3. Injected JSONL fsync failure after a complete intent line causes reserve refusal; close/reopen sees the line. With fsync still failing, a new reserve returns that prior intent successfully without a durable recovery barrier. Checked visibility is not confirmed durability. Require a successfully persisted/fsynced recovery barrier before retained uncertain prefix is usable, including restart.
4. Injected actual SourceObservationBoundary.admit returning `Ok(None)` leads download to mark authority complete=True and return success, while independent raw archive observer reports zero rows. Validate typed ObservationReceipt and exact retained observation/archive identity before completion; unknown or mismatched acknowledgements refuse. Explicit True on the authority completion event does not establish that raw admission was acknowledged.

Each reproduction used public authority APIs and actual QMF JSONL store or the actual supplied SourceObservationBoundary seam. No missing provider credentials or external effects were involved. Owner/root received findings promptly.

## Corrective candidate a8d00345

Reviewed `a8d0034543045fa8311b9fd9f6ebaae08a12a2a4`. **Changes remain required.** The original sequential same-store handle control is addressed by a shared coordinator, custom authority stream names now refuse, and raw admission acknowledgments are checked against typed retained CT10 evidence. Independent `Ok(None)` and `Ok('ack')` raw acknowledgments refuse with zero raw observations and no authority completion; typed receipts with wrong archive world or unrelated archive fingerprint refuse with the real raw observation retained but no authority completion.

Stronger actual controls expose these remaining blockers:

1. Same-store coordinator initialization is not atomic. Two concurrent `resume` calls with the same actual `JournalStore` and WriterId can both pass cache lookup before either publishes. A held-out synchronization at recovery barrier entry, with actual barrier writes serialized, returns two accepted handles with different locks and JournalWriters. The first reserve succeeds; the second appends a duplicate per-writer sequence and then refuses its ACK. Checked CT13 reads thereafter refuse with duplicate-sequence loss. Hold initialization/publication under one ownership boundary.
2. Cross-process ownership is not serialized. Two actual forked processes, each opening the same filesystem room with the same stable WriterId, both resume successfully. After B's resume, A's stale writer appends another sequence 1 on reserve and refuses its ACK. B's reserve then observes checked duplicate-sequence loss. No method mocks were used in this reproduction. In-process shared dictionaries cannot protect the canonical physical authority against simultaneous processes; safely refuse a competing authority owner or use an actual process-wide transaction/ownership lock.
3. Recovery barrier durability does not cover rotated prior files. With the public `jsonl_opener(rotation_bytes=1)`, the reserve barrier fsync succeeds and intent fsync fails after its complete line is visible in `000002.jsonl`. After close/reopen, resume and reserve both succeed. Independent recording of actual successful recovery fsync calls finds only new `000003.jsonl` and `000004.jsonl`; the failed intent file is never fsynced. A later file's fsync does not persist an earlier uncertain file's data. This is syscall evidence, not simulated power-loss proof; a primitive that durably reconciles the entire uncertain prefix is needed before retained intents become usable.

All three were sent directly to the current numeric owner and root. No corrected committed candidate has yet been approved in this addendum.
# Corrective review — `be314578d3d106722b50c39862a254d550c4a633`

**APPROVED for the bounded CT15 authority corrections.** Inspected coordinator initialization/publication under the cache lock, OS room transaction lock, per-operation sequence refresh, complete-prefix synchronization and blocked-event reconciliation. No product edits were made.

Independent actual-filesystem controls:

- Simultaneously resume two initially uncached handles over one JournalStore using a thread start barrier. They share the same lock; successive differing receipt metadata returns the first canonical observation and exactly one intent. Checked journal remains valid.
- Two forked processes independently open the same room with the same stable WriterId, both finish resume before either reserves (process barrier), then simultaneously reserve the same key with differing receipt stamps. Both succeed with the identical canonical fingerprint. Reopen checked journal has contiguous sequences and exactly one intent. This reproduces the formerly corrupting stale-resume interleaving without mocking storage or journal methods.
- Actual rotation_bytes=1 fault control makes a visible intent's original 000002.jsonl fsync fail. Reopen with a persistent fsync fault refuses authority. On fault removal, successful fsync calls include the original failed chunk before canonical reuse; a newly rotated barrier alone is no longer the durability proof. This checks syscall coverage, not simulated power loss.
- CT10 admission returning Ok(None), Ok(string), or a real admission receipt with wrong archive world/fingerprint refuses download and emits no CT15 completion. The latter controls retain the real physical raw write, truthfully refusing its corrupt acknowledgment.

Independent suite: `.venv/bin/python -m pytest -q -p no:cacheprovider qa/tests/epic_18/test_e18_l2_download.py qmb/tests/test_data_download.py packages/qmf-data/tests/test_source_boundary.py packages/qmf-data/tests/test_journal_producer.py` — **68 passed**. Prior custom-stream refusal, checked canonical state, uncertain append and producer receipt controls are included. This approval does not extend to providers, credentials, unrelated multi-room transactions or a full execution chain.
