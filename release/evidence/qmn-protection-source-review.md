# Independent protection source producer review

Current verdict: **PASS, bounded corrected producer/readback snapshot** below. Earlier FAIL sections retain defect history and are superseded only by the final exact-hash review. Source producer/readback only; this is not entry-plan, ratchet, OrderPath, supervision-pump, installed-node, or real-provider approval. Local tests use the existing conformance fixture and benign temporary evidence stores.

## Exact reviewed source

- `qmn/src/qmn/data/observation_sink.py`: `17d2c84da6097b711b3e43ff93517592bd8b076235b4ebeeba99b25433cf9ef9`
- `qmn/src/qmn/ledger/protection_state.py`: `ced4f109d5c10ffbbf657e1ee7ccd98ef74476a82831cac5ae1230f678e10276`
- `qmn/tests/test_qmn_protection_state.py`: `70f66e6679c1bfdef1f6a16f969ca9f652db621b91eee324c05c02d9ce6131a0`
- `qmn/src/qmn/loop/accumulator.py`: `073407612d8b0823151721a01bc50fa240da4c6692dbd27a81ad8102046cca79`
- `qmn/src/qmn/data/intake.py`: `9435cc2b9e15b18690c5adc1d455a91d757b09ea340b3f4332155d2aba07b66d`
- `qmn/src/qmn/venue/live.py`: `21da25eb09e4d4f3bf6f5ebcfe2390661e51e159d35c1933c7e23e98fd074d31`

## Actual positive and blockers

`.venv/bin/python -m pytest -q -p no:cacheprovider qmn/tests/test_qmn_protection_state.py qmn/tests/test_qmn_protection_readback.py`: **4 passed in 1.06s**. The genuine LiveClient receive → private JSON-text archive + CT10 → CT13 join → reopened resolver → stop 108523 positive passes. This preserves decoded response JSON, not original protobuf bytes.

`.venv/bin/python /tmp/review_protection_source.py` captures genuine resolver inputs from the public fixture. Ordinary `dataclasses.replace` on its actual source event produces three exceptions: payload=None → TypeError; payload='junk' → ValueError; instant=123 → AttributeError. The resolver canonicalizes before validating nominal event fields. Sequence=True and writer=None controls already refuse.

`.venv/bin/python /tmp/review_protection_ack.py` wraps actual JournalWriter.record: the physical append occurs normally, then its returned typed receipt is replaced. event=None, event.payload=None, and store_receipt=None cause AttributeError/TypeError before typed refusal. Changing only store_receipt.engine to 'parquet' or format_version to True is accepted by the complete original positive fixture. Durable row existence does not establish these claimed metadata fields.

Require exact receipt/event/store classes and finite nominal field validation before canonicalization; enforce JSONL engine and strict integer format 1; retain logical versus physical sequence validation, checked readback, and exact physical row proof. Findings delivered to numeric owner and root. Corrected source hashes and independent hostile-ACK rerun are required before approval. Other requested ambiguity/foreign-source controls remain unapproved in this failed snapshot.


## Corrected ACK snapshot — remaining persisted join FAIL

Original finite probes now return typed refusal: payload None/string, instant123, writerNone/sequenceTrue; actual-written ACK eventNone/payloadNone/storeNone/foreign-engine/bool-format all refuse. Actual original receive/reopen positive remains successful.

`.venv/bin/python /tmp/review_protection_join.py` creates a genuine second CT13 DATA_QUALITY row using JournalWriter.resume with the authorized original writer and stream. It carries original CT10 sequence0/raw refs but the CT13 event sequence is1 and duplicated join.writer is foreign. Checked resolver accepts stop108523. Physical readback and event fingerprints are genuine. Recovery fails to enforce producer invariants source_observation.sequence==source_event.sequence and duplicated join.writer==actual source/event writer. This is a bounded actual provenance false-admission; no source edit. Owner/root notified, corrected freeze/retest required.

Observed corrected source hashes:
- `qmn/src/qmn/data/observation_sink.py`: `77b68c0a4956cd80d36156c7d8e1f531e82d9b6d9a4c1fbe8cd4fa1d14f3bdf8`
- `qmn/src/qmn/ledger/protection_state.py`: `903d1b88402a1529f7b0de132a2838cd58c20ce8e345f7b5a5f330b03c41ed11`
- `qmn/tests/test_qmn_protection_state.py`: `9d182b691906e80a75cf13adb93ea80ad66761baa241168d11b6bf7379d17171`


## Second join correction — hostile durable body ACK remains FAIL

Observed source sink77b68c0a4956cd80d36156c7d8e1f531e82d9b6d9a4c1fbe8cd4fa1d14f3bdf8; resolver69eb3866983b2176d4b706b1b3e63ddb25d064f1093a43325c079adc9ae32b03; testd9b86ae8a26588fe5f605ec373694c70e91a580fc7c6779d367b125ce440f2ec. Original malformed resolver/ACK and genuine persisted foreign-writer/reused-sequence controls now refuse. Four source+decoder tests pass1.03s. Nine independent foreign account/session/PID/symbol/bool-digit/malformed-instrument controls refuse. Actual intake/reopen positives for three adjacent finite stopLoss values around1.08523 preserve Python binary64 JSON roundtrip bits; no protobuf capture claim.

New `.venv/bin/python /tmp/review_protection_body_ack.py` wraps real JournalWriter.record and appends a payload containing an additional foreign_body marker instead of the requested body. Returned receipt and indexed physical row are genuine, but the full original intake/reopen test ACCEPTS. The sink compares returned event against its own fingerprint and physical row, without joining exact requested payload/instant. Require canonical full expected payload comparison and exact expected instant before returning SinkAck. Findings delivered owner/root; approval remains blocked pending corrected source.


## Final corrected snapshot — bounded PASS

Eight independent local probe scripts and the four-test source/decoder slice were rerun via `.venv/bin/python /tmp/run_protection_final_review.py`. Exact argv/stdout/stderr and before/after hashes are retained in `/workspace/qmx-protection-final-independent-review.json`; all source hashes remained unchanged throughout. Pytest **4 passed in0.95s**.

- `qmn/src/qmn/data/observation_sink.py`: `0625bc5fd7eaccf4db124dc8ebfade0c18235c75d3374c327d7d84b19295dda6`
- `qmn/src/qmn/ledger/protection_state.py`: `69eb3866983b2176d4b706b1b3e63ddb25d064f1093a43325c079adc9ae32b03`
- `qmn/tests/test_qmn_protection_state.py`: `56f0bc15ea44c4b39ad1fb62b15322902e04978ecef7297119faee57fa044ce7`
- `qmn/src/qmn/loop/accumulator.py`: `073407612d8b0823151721a01bc50fa240da4c6692dbd27a81ad8102046cca79`
- `qmn/src/qmn/data/intake.py`: `9435cc2b9e15b18690c5adc1d455a91d757b09ea340b3f4332155d2aba07b66d`
- `qmn/src/qmn/venue/live.py`: `21da25eb09e4d4f3bf6f5ebcfe2390661e51e159d35c1933c7e23e98fd074d31`

Genuine LiveClient receive→retained JSON-text raw archive+CT10→actual CT13 physical readback→resolver reopen still yields108523. Malformed payload/instant/writer/logical boolean, missing event/store, foreign engine/boolean format, wrong physical index, nonempty edges, altered durable body and requested-time ACKs refuse. A writer mutating its supplied dictionary in place before actual append also refuses: expected canonical bytes/fingerprint are captured BEFORE the writer call. Source+event writer/sequence/frontier joins reject the genuine second event reusing original CT10 provenance with foreign nested writer. Nine account/session/PID/symbol/digits/instrument context controls refuse. Three adjacent finite binary64 stop values survive actual intake/archive/reopen; JSON roundtrip bits remain exact.

The hostile ACK probes perform real physical writes; refusal means no false successful SinkAck, not rollback of an already written event or proof of complete uncertain-write reconciliation. Their printed AssertionError is the original positive fixture rejecting the returned TypedRefusal, rather than an exception inside the guarded boundary. Checked resolver requires unique checked event and physical row, with original logical provenance; generic all-store duplicate/restart reconciliation is outside this bounded approval.

PASS is limited to this six-file source producer/readback chain and local fixture. No original protobuf-byte capture, real provider connection, protection plan, ratchet execution, OrderPath integration, node decision pump, installed full candidate, or full-product acceptance is claimed. Root alone may stage/commit; no product/test edits made by reviewer.

Root independently reproduced the latest source snapshot: `uv run --no-sync pytest -q qmn/tests/test_qmn_protection_state.py qmn/tests/test_qmn_live.py qmn/tests/test_qmn_data.py qmn/tests/test_qmn_loop.py qmn/tests/test_qmn_protection_plan.py` gave **36 PASS, 1 SKIP in 0.95s**, `/workspace/qmx-qmn-protection-request-snapshot-root.log`. The separate plan tests are characterization of an active private primitive and do not expand this six-file approval. Root-config Pyright against the exact six source/test paths gave **0 errors, 0 warnings, 0 informations**. The skipped sandbox-token test remains provider NOT RUN. All six hashes match the independent manifest above.
