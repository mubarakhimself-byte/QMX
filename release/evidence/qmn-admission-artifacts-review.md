# QMN admission artifact independent review

2026-10-01. Independent GPT 6.1 Sol bounded durable-content/source review. **FAIL: one P2 reader environment-contract mismatch.** The four existing tests pass, and the valid persistence path preserves its explicit unverified-input limits. This review does not approve complete admission evidence, a fitted live baseline or readiness.

Held source SHA-256 values matched at entry and completion:

| File | SHA-256 |
| --- | --- |
| `qmn/src/qmn/host/admission_artifacts.py` | `46ae855a3ea993c6d2e802b4bab7d88fd1f2a4ad5a2febad47bee8e6fcc46adf` |
| `qmn/tests/test_qmn_admission_artifacts.py` | `ea7af91a29911853a1e10dd082f292dba7a4fea7d9c0949daf128ad1f1a47836` |

No product/test edits, commits, credentials, network/provider calls or security testing were performed. Disjoint new `admission_evidence` joins were outside scope. Only this evidence file and a preserved ordinary local diagnostic were written.

## Finding

**P2 — Typed reader accepts a demo-conditioned artifact in the LIVE artifact boundary.** The writer explicitly rejects `artifact.key.environment != "live"`. In contrast, `_decode_sqs_baseline` at `admission_artifacts.py:539` accepts any environment supported by `sqs_baseline_key`, and `read_sqs_baseline` at line 288 calls `_read_quote_sources`, which checks LIVE quote rows and venue/instrument but never checks the decoded key's environment. It then returns the demo-key artifact as `PersistedSqsBaseline`.

A finite pre-existing-content fixture confirmed the mismatch: the official CT-11 `append_raw` store persisted an internally consistent, canonically encoded envelope with `key.environment="demo"`, correctly recomputed nested/envelope/archive identities and a complete typed reference, citing actual fixture LIVE bid/ask observations for the correct venue/instrument. `read_sqs_baseline` accepted it and returned the demo key. The normal `persist_sqs_baseline` writer was not used to admit this malformed business content; the byte store's successful write only models pre-existing content presented to the semantic reader. A genuine LIVE writer/readback positive preceded it. The reader changed no fixture file hashes or census.

The reopened value still had `derivation_verified=False`; this finding does not claim fit attestation or readiness occurred. It concerns disagreement between the writer and reader's LIVE conditioning contract. Revalidate the decoded artifact with the shared LIVE baseline validator, or enforce the same LIVE environment rule in the common decoder/reader before success. Add the negative persisted-content case alongside the genuine reopened positive; do not rely only on writer refusals. The coordinator was notified for the Numeric owner, and no repair is assumed approved at this freeze.

## Commands and results

Working directory `/workspace/QMX-release`:

```sh
uv run --no-sync pytest -q -p no:cacheprovider qmn/tests/test_qmn_admission_artifacts.py
```

**PASS: 4 passed in 1.19s.** The added finite reader-boundary check used:

```sh
PYTHONPATH=/workspace/QMX-release/qmn/tests uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_qmn_admission_artifact_environment.py
```

The diagnostic asserts both held hashes before and after execution and preserves its exact result. It was needed to resolve the concrete reader/writer environment question found during static review; no other probe programs or broad audit were run.

| Bounded contract | Result |
| --- | --- |
| Genuine durable artifact and sources | PASS. The positive creates actual CT-10 quote observations through `SourceObservationBoundary`, persists the SQS input to the immutable raw CT-11 room, opens a fresh `EvidenceStore`, and reopens the typed artifact plus cited CT-10 rows. Its artifact identity, source refs and calendar are preserved. These are explicit local conformance observations, not provider quotes. |
| Identity, refit and conditioning | PASS within positive/source review. Key, tagged spread, optional dispersion, session/statistic/refit-series, policy fingerprint and official calendar form the preserved canonical input content. The row and nested envelope recompute their identities and compare complete source/calendar/conditioning fields with the reference. No supplied statistic is inferred from the sources. |
| Writer nominal validation | PASS by source and existing controls. Exact artifact/key/venue/instrument/PriceDelta/calendar types are rebuilt through official constructors before persistence. Wrong instrument/key and demo conditioning refuse. Source refs are canonical, unique and require at least two observations. |
| Row/version/receipt/readback | PASS by source and positive execution. Exact row/envelope versions exclude booleans; body JSON must match canonical bytes and its fingerprint. Successful writes require an exact LIVE immutable-archive Parquet receipt with evidence/retained flags true, version 1, typed outcome and no stream/rebuild metadata, followed by actual physical readback and full body/lineage comparison. Underlying raw-store reads recompute the archived row identity. `retained_forever` is the official raw-room contract/receipt fact, not an independent host-retention or recovery drill. |
| Source-world and metadata checks | PASS for the valid path/static checks. Sources are read explicitly in/for LIVE and revalidated by the official CT-10 boundary; both bid and ask, correct venue and symbol and actual price facts are required. Missing refs and changed inner artifact identity refuse in existing tests. Matching session/statistic/calendar declarations do not attest a source-derived statistical fit. |
| Reader key environment | FAIL. A pre-existing demo-key envelope with actual LIVE quote refs is accepted despite the writer's LIVE-only rule. |
| Incomplete shakedown page | PASS refusal. The current exact `ShakedownEvidence` lacks a typed resolved CT-27 BMS identity and checked CT-28 capability-satisfaction receipt. `persist_shakedown_signature_page` refuses instead of converting binding strings/booleans into those proofs. It does not persist a complete AD-32 page or add CT-13 promotion fields. |

The explicit `unverified-input-artifact` status and `PersistedSqsBaseline.derivation_verified=False` are preserved. This helper persists a supplied statistic and checked quote citations; it does not establish that the statistic was computed/refit from those quotes, that they cover the declared market-hours/session window, or that the resulting value can satisfy a live binding/admission gate. The current complete-page dependency remains unavailable. These named limits are required and are not defects to erase.

## Preserved diagnostics and pending work

Archive `/workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics` retains the reproducible program, result and exact argv/source notes. Temporary local fixtures were removed on normal completion.

| Artifact | SHA-256 |
| --- | --- |
| `review_qmn_admission_artifact_environment.py` | `2f31066aaa03f22006f1bc9a244f94ced2949ec053743e54b900a4e786cda3ed` |
| `qmn-admission-artifact-environment-results.json` | `378e63d7f3db6c4cf7c5a049c2615d91bc9a18e4ab21412091d350d79b143bcc` |
| `QMN_ADMISSION_ARTIFACT_REVIEW_ARGV_SOURCE_NOTES.json` | `4c189b214b416e18f7000ee54e72a0b6f33d357445aacf55a3cd90fe5d43a084` |
| `SHA256.json` at completion | `4d62838350c2d2efd80c799aef576fb9e1e03b3d6c3b10175b7f608a78f27bdb` |

Repair/re-review of the P2, new admission joins, source-derived baseline evidence, full coupled QMA, normal configured execution, final installed release checks, provider and security review remain separate pending work. No complete candidate acceptance or factory/coverage waiver is implied.
