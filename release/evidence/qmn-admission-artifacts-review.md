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

## Corrected artifact2 re-review — runtime PASS, regression-test FAIL

2026-10-01. Held runtime SHA `38f4d6d326988acb0bc75947a3b628289ff91b0d8d667c897980dfa22df83006`; held test SHA `d535769137d54f3bb63b4307db1ac234330c2a0ff2b5282e65c3dee5c27a9e4a`. Both matched at entry and diagnostic exit. No product/test edits, commits, provider calls or security testing. Disjoint admission_evidence is reviewed separately.

The repaired `_decode_sqs_baseline` now returns `_revalidate_sqs_baseline` rather than a nominal artifact directly; the shared exact-type validator's LIVE key rule is therefore applied to both generic and typed reader paths. `uv run --no-sync pytest -q -p no:cacheprovider qmn/tests/test_qmn_admission_artifacts.py` passed **5 tests in 1.31s**.

The existing archived finite diagnostic was copied, rebound to the new source hashes and extended to assert both readers refuse specifically at `environment`. Command from release root: `PYTHONPATH=/workspace/QMX-release/qmn/tests uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_qmn_admission_artifact_environment_corrected.py` — exit 0. It reuses genuine LIVE writer/readback positive, changes the pre-existing envelope to DEMO, recomputes the inner artifact fingerprint **and full envelope/row/reference fingerprints**, and uses actual LIVE bid/ask refs. Both readers refused with `field=environment`, reason `LIVE baseline uses the live conditioning key`; all reader file hashes/census were unchanged. This meaningfully verifies the original failure is fixed. Unverified-input/derivation false and unavailable complete shakedown page limits remain required.

**P2 — new regression refuses at the wrong boundary.** `test_sqs_reader_refuses_correctly_fingerprinted_demo_key_row` sets its row/reference `artifact_fp1` to `fingerprint(demo_baseline.fp1_identity())`, the inner artifact fingerprint. `read_admission_artifact` instead compares that reference to `fingerprint(full envelope body)` before calling the baseline decoder. These different identities cause an earlier `artifact_fp1` refusal; the test's generic `is_refusal` assertion passes even if the repaired LIVE decoder rule is absent. The test title's correctly-fingerprinted claim does not hold for the full envelope. Preserve inner body `artifact_fp1` as the baseline fingerprint, compute a separate full-body fingerprint for row/reference, and assert both refusals reach `environment`. The independent rebound diagnostic demonstrates the correct construction without editing the test. Root and Data were notified; the test correction needs a new freeze.

Verdict is **PASS for the bounded runtime repair and FAIL for the held regression's meaningful coverage**. This does not approve complete admission evidence, computed/refitted statistics, configured/live readiness, whole release, or security. Original failure/evidence above are retained.

Corrected archive SHA-256: program `d6bf4af2a5358b984f52abd1da41c27339f6153ddf48095e64ac10b501eb11e2`; results `2c0d462c3bd6eef0af392e942dc311a9a23ff8f724b378afa5606710dc0853a0`; argv/source notes `47622aaef55512d973be0a46bf1cb55a490a674b86f4963a03dc33b4b5255379`; archive SHA manifest at completion `140c2af1d8428bc48eba72722cda5f7316767745647d6ab90a74128f0ce09209`.

## Corrected regression re-review — bounded PASS

2026-10-01. Runtime remains SHA `38f4d6d326988acb0bc75947a3b628289ff91b0d8d667c897980dfa22df83006`; corrected test SHA `8a6358c1f1440631b67be9fa6d43492a514a588e8d0d21a1fc6524517cbb3540`. Held entry/end checks passed. The repository test now keeps the inner baseline fingerprint separately and correctly uses the full envelope fingerprint for row and reference. Consequently the persisted DEMO row reaches the repaired shared LIVE reader validator rather than refusing on a mismatched enclosing identity.

From release root, `uv run --no-sync pytest -q -p no:cacheprovider qmn/tests/test_qmn_admission_artifacts.py qmn/tests/test_qmn_admission_evidence.py` — **10 passed in 1.26s** (5 artifact tests and 5 separately reviewed evidence tests). The existing environment diagnostic was copied/rebound to this test hash: `PYTHONPATH=/workspace/QMX-release/qmn/tests uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_qmn_admission_artifact_environment_final.py` — exit 0, genuine LIVE positive succeeds, both correctly fingerprinted DEMO readers refuse specifically `field=environment`, and physical file census is unchanged.

This exact artifact2 now **PASSES its bounded runtime and meaningful regression scope**. Prior FAIL records remain historical against their held bytes. This does not upgrade supplied SQS statistics into source-derived fits, incomplete pages into CT-27/28 complete proof, or stand-down/metadata into configured/live readiness. The separate admission_evidence correction has a new genuine nonempty-section read failure and is not approved by this artifact PASS. No product/test edits, commits, provider or security activity occurred.
