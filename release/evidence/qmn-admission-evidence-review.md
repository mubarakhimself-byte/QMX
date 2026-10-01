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

## Corrected evidence2 re-review — FAIL new P2 positive read

2026-10-01. Held runtime SHA `b548894eb2331a6d5fbd9b7fb80314ecb71bec0c402c417cf94848fba6789262`; test SHA `a75ec64bb5f8aa907dbebacf40063cd4abdcd7436035dbc0954ea2d5060e03ea`. Entry and diagnostics-exit checks matched. No product/test edits, credentials/providers/security testing or commits. Prior failures above remain recorded against original bytes.

The prior boolean-body version and page identity failures are fixed. Reader now requires exact integer body version/exact body fields, recomputes page fingerprint, retains the CT-06 envelope version and all four full record bodies, recomputes record stable identities and registry-as-of set, reconstructs binding against Book/BMS, validates rank identity against declared CT-27, and checks unique named missing-evidence strings. Correctly rehashed original invalid controls now refuse at `admission_evidence_identity` and `page_fp1`; unchanged genuine fresh-store envelope succeeds.

The same finite real fixture further checks fully rehashed foreign registry-as-of, CT-06 stable identity and binding identity; these refuse at `registered_records`, `ct22_fp1`, and `binding_fp1` respectively. A claimed derived rank with the real empty CT-27 refuses at `control_rank_table`/missing. These are successful ordinary consistency controls, not fresh capability or admission proof.

**New P2 — successful legitimate writer output with a nonempty CT-27 cannot reopen.** `_decode_registered_binding` at `admission_evidence.py:395-405` passes retained JSON `sections` directly into `BookDefinition.try_create` and `BmsDefinition.try_create`. Those official constructors require each known section to be a typed `TemplateSection`, not its serialized identity mapping. Empty sections in the current positive hide this error.

The finite required positive uses the official existing rank test pattern to build all four exact COUNT TemplateVariables and TemplateSection, an actual BmsDefinition, matching derived BmsInstanceId and BookBindingRecord. It persists the changed CT-27/28 through the official RegistryPersistence and loads their actual CT-06 records, recomputes the real configured registry-as-of and binding, and passes the resulting exact assessment/page into `persist_admission_evidence`. The semantic writer **succeeds**. Fresh EvidenceStore `read_admission_evidence` then refuses `field=sections`, `key=control_rank_table`, reason `each section is a TemplateSection`. The serialized retained section is exactly the declared typed definition's official identity, not guessed content. Reader therefore fails to read its own valid retained evidence, before its rank adapter can run. Known nonempty Book sections use the same incorrect decoding path.

Decode retained template sections/variables/exact values with official typed constructors and canonical identity comparison before invoking Book/BMS constructors. Preserve valid declared counts/units and all missing-proof blockers; do not replace them with defaults. Add a real nonempty rank writer/fresh-read positive plus finite foreign/malformed rank identity refusal at the intended boundary. The current repair remains **FAIL** until that positive reopens. Root and Numeric/Data were notified and authorized to repair under a new freeze.

Commands from release root:

- `uv run --no-sync pytest -q -p no:cacheprovider qmn/tests/test_qmn_admission_artifacts.py qmn/tests/test_qmn_admission_evidence.py` — **10 passed in 1.26s**; this does not cover the nonempty read positive.
- `PYTHONPATH=/workspace/QMX-release/qmn/tests uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_qmn_admission_evidence_reader_corrected.py` — exit 0; original version/page regressions now specifically refuse, unchanged genuine positive passes.
- Same prefix plus `.../review_qmn_admission_evidence_lineage.py` — exit 0; targeted consistency controls refuse; real nonempty CT-27 writer succeeds/fresh reader fails as described. Both held hashes checked before/after. The program reports the factual failure rather than treating it as a passing positive.

All source/results/exact argv/source notes are retained. Incomplete wrapper status still does not establish fresh CT-18 capability checking, derived SQS, shakedown/source/binding completeness, operator signature, CT-13 promotion or normal configured execution. Whole coupled QMA/installed/provider/security acceptance remains separate pending work.

## Shared decoder6 correction re-review — bounded PASS

2026-10-01. The exact six-source review at `qmn-registered-template-decoder-review.md` resolves the preceding P2 genuine nonempty writer/readback failure. Admission runtime `4b90a78119db6138827819e3c050ce9da50cd1636b679b77a4affd8274684329`, admission test `6e2d94cd9faa4d0e2ae8148ff3190c84f6f86e7b8c3951a04f70fd5646e18bb6`, shared decoder `af6bd841c0a38b1f59420168d6f2bcb7e238b797beb80b9c7be3d8cc533d7896`; complete six-path source census, commands, diagnostics and limits in the new report. Focused20 PASS1.43s. Rebound archived genuine nonempty Book+BMS assessment, actual persisted CT-27/28 and fresh physical envelope read succeed; correctly rehashed registry/CT-06/binding/rank foreign controls refuse. Official tagged value/metadata and version positives/refusers pass. Earlier original failures remain unchanged above. Wrapper is still explicitly incomplete: no derived LIVE SQS/fresh CT-18 capability/CT-13 promotion/readiness/provider or whole-release acceptance.
