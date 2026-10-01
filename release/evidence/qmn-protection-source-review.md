# Independent protection source producer review

Verdict: **FAIL** for the reviewed six-file snapshot. Source producer/readback only; this is not entry-plan, ratchet, OrderPath, supervision-pump, installed-node, or real-provider approval. Local tests use the existing conformance fixture and benign temporary evidence stores.

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
