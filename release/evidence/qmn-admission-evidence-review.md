# QMN private admission evidence2 independent review — FAIL

2026-10-01. Independent Sol ordinary durable-content/typed-lineage review of exactly two held files. No product/test edits, commits, credentials, providers, or security testing. Existing incomplete status is intentional and does not establish AD-32 completion, fresh capability evidence, SQS derivation, live readiness, or promotion.

Held hashes, verified at entry and finite diagnostic exit:

```text
2df8fadaeeb2179be02e2602d99b94c1743f2cea2d166760e93e67d656996506 qmn/src/qmn/host/admission_evidence.py
d449e0936b5d202e5f195e19c91650a5da933d319774b4681dc8b0baccc9b227 qmn/tests/test_qmn_admission_evidence.py
```

## Findings

**P2 — body version accepts boolean true as integer 1.** `read_admission_evidence` requires `type(row.format_version) is int` for the raw row, but its body identity condition compares only `body.format_version != 1`. The actual correctly rehashed immutable CT-11 envelope with body `format_version=true` and genuine row version 1 is accepted. The reference, raw archive fingerprint and body canonical JSON/outer fingerprint all correctly match; this reaches the body type boundary rather than failing on a stale hash. Require exact integer type for the inner version as well. Version meaning must not change by Python's boolean/integer equality.

**P2 — reopened page identity is not recomputed.** The writer computes `page_fp1` from the actual `page.as_mapping()`, but the reader checks only canonical enclosing body identity, class/version/status. A pre-existing row copied from the genuine writer body, retaining the actual page but replacing `page_fp1` with a different valid canonical fingerprint and correctly recomputing the envelope/archive/reference identities, is accepted. The returned envelope therefore asserts page lineage that its actual page does not satisfy. Recompute page fingerprint and validate its exact nested schema/identity fields before returning success; apply the same consistency discipline to stored registered-record identities, binding and registry-as-of joins rather than equating a correct enclosing fingerprint with valid nested lineage. The finite finding is specifically the mismatched page identity; broader hypothetical malformed-lineage cases were not probed.

Both controls return `status=incomplete`; no gate promotion or complete evidence was observed. These are ordinary correctness failures in the public reader's promised checked envelope and exact identity contract. The official raw CT-11 store was used to model pre-existing content, not to assert that the semantic writer admitted this business content.

## Passed controls and limited claims

From `/workspace/QMX-release`: `uv run --no-sync pytest -q -p no:cacheprovider qmn/tests/test_qmn_admission_evidence.py` — **3 passed in 1.15s**.

The positive uses actual locally persisted registry records from `fixture_deployment`, a genuine `assess_configured_runtime` result, and the existing typed demo shakedown/page API. It persists the private wrapper in LIVE CT-11 raw-room storage, creates a fresh EvidenceStore and reopens it. This is local conformance data/descriptor material, not provider execution, actual registry deployment or fresh venue capability acquisition. The foreign-venue page refuses. The declared BMS rank adapter positive builds all four official exact COUNT rows; absent rank section refuses instead of supplying defaults.

Static writer review confirms exact assessment/page/LoadedRecord and official CT-22/27/28/33 nominal types are required; CT-06 record identity is recomputed including kind, versions, parents and full body, persisted/stable IDs agree, typed Book/BMS bodies compare canonically, Bot reconstructs through its official mint, and binding reconstructs against Book/BMS fingerprints. Binding is LIVE and the page's typed SQS venue agrees. Page source/binding joins beyond that venue are explicitly missing evidence, not completed proof. The derived rank table comes only from declared exact count variables; absent/unavailable rank remains visible.

The store receipt is checked for exact StoreReceipt type, expected archived row fingerprint, LIVE, immutable raw Parquet, evidence/retained flags, exact integer format 1, typed WriteOutcome and absent stream/rebuild metadata. Writer success requires exact physical raw readback. This proves the local room/receipt/readback contract, not an independent retention, backup, or deployment recovery drill.

The envelope intentionally records `status=incomplete` and missing CT-22 typed capability requirements, CT-28 fresh CT-18 check, derived live SQS, deployment rung baseline, shakedown/source/binding join and operator signature occurrence. If ranks are unavailable, it adds that blocker. No new CT-13 promotion fields are minted. Supplied shakedown booleans and decoded capability fields must not be upgraded into the named missing proofs; assessment activation/provider flags remain false in the positive. Exact full admission and normal configured host readiness remain pending separately.

## Reproducible finite controls

Command: `PYTHONPATH=/workspace/QMX-release/qmn/tests uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_qmn_admission_evidence_reader.py` — exit 0. The program reuses the existing genuine writer/fresh-read fixture, changes one field at a time, computes canonical bytes/full envelope/archive/reference identities via official APIs, and records actual outcomes. Both invalid bodies were accepted; genuine unchanged envelope succeeded. All files/hashes above were checked before and after. No product or test source was altered.

Execution/coordinator/Data were informed that this exact freeze fails; owner repair must be reviewed under new hashes. All diagnostic source, results, argv/source notes and SHA manifest are retained in the shared local diagnostics archive. This bounded report does not approve full candidate, coupled QMA, configured execution, fitted SQS or complete security.

Diagnostic SHA-256: program `33e51bb810a3508ec038caa66455c788a075eaf01aab799ac9f8048ce277369f`; results `a4fa47d9a7db6bbc2cfb53d9616afe1aebdf389f23063dc2b927e25bedd8a285`; argv/source notes `8cbb501f4ad279a72a058693e4a45c9f1df24abe337449c6d1a07cfd3daa620a`; archive SHA manifest at completion `05e5e1176d030102a5747c887ed4b5329607aaa8115595d1244cc8630a13a26f`.
