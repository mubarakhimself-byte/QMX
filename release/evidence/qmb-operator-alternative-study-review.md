# Private operator Alternative Study2 review — FAIL identity separation

2026-10-01. Independent Sol ordinary fixed-budget Study adapter review. Current owner-confirmed freeze:

```text
571f0e7e130b7cd570039562f9c65d879a6829e6559d2fd23c40f8db6f3f38dc qmb/src/qmb/host/operator_alternative_study.py
e4368cb188c660db997ff77f98aab230d440e123f606a59fdfdeb0afd69eaa30 qmb/tests/test_operator_alternative_study.py
```

Original test freeze was `50d0b2794c708c8e313e95da46aa838d5a5355dd456be2fb591f2dd9022ef95a`; entry initially matched and its 3 tests passed in 0.98s. A later finite diagnostic stopped at its initial hash assertion before fixtures/effects. Root stopped review probes until Data provided a fresh explicit hold; Data explained the test delta is one blank line left after removing an unexecuted assertion. Product bytes remained unchanged. Current diagnostics bind to the new exact hash and check both at entry/end. No mutable-byte PASS was assumed.

## P2 — operational plan fingerprint is reused as computational Study fingerprint

`_base_identity` includes `qma_occurrence.job_id`, `attempt_id`, delegated environment/occupancy, and physical roots/writer identities. `OperatorAlternativeStudyPlan.try_create` fingerprints that entire base binding into its full plan identity. `stepper()` then uses the same plan fingerprint as `study_fp` in domain trial labels. Thus identical computation under another delegated job/attempt obtains another computational Study identity, and completed domain history cannot be reused under a new occurrence without treating it as a different Study.

Main governing `c3e8ec5` QMB B-8 defines seeded history-based reproducible generations/trial Study labels; QMB B-14/registry computational identity law excludes occurrence facts from content identity. The earlier explicit interface diagnosis separated job/attempt producer occurrence from complete computation Study content. A full operational plan fingerprint is useful for exact delegated context refusal, but it is a different identity from the reproducible Study computation. Data confirmed this current behavior means conservative no cross-job reuse and agrees a stable computation Study fingerprint plus separate producer occurrence is required; no owner fix is assumed in this review.

Keep a full operational/context binding fingerprint for exact callback and occurrence checks. Derive computational Study identity from complete parameter space/seed/direction/rounding/batch/fixed total budget/objective/units/bindings, base PolicyPair/config, exact source/split/role, interpreter and initial-state content. Declare identity inclusions/exclusions explicitly. New job/attempt must have its own checked producer occurrence evidence and explicit reuse admission policy; do not rewrite old terminal labels or pretend cached trial history was produced by that job. A changed input remains a different computation. This is an ordinary reproducibility/identity issue, not a provider or security finding.

## Passed bounded behavior

The full current plan includes complete space fingerprint, seed, direction, **exact RoundingMode**, batch, total generation count, objective identity/unit/currency, explicit unique PolicyPair bindings, sampler identity/provenance and complete trusted base context. Runtime reconstructs all those fields and compares both fresh and declared fingerprints before reading/running. Unsupported parameter types are typed-refused; it does not invent financing, R, Book/BMS/Bot or CT-32 content. The internally owned callback evaluates the registered Alternative interpreter, not an arbitrary user trial function.

The actual local fixture produces materialized CT-10 data through the official boundary with a CT-12 split/role. Its PolicyPair/interpreter are registered typed APIs, not hardcoded default financial policy. The QMA context/descriptor/spec/evidence refs in this adapter fixture are explicitly generated fixture identifiers; they are not genuine public QMA/descriptor persistence or authorization proof.

Finite current-freeze controls independently confirmed:

- Changing the declared rounding mode changes plan identity. A malformed string rounding mode and a foreign delegated job used with the old plan each refuse before any interpreter call or file census change.
- A fixed total budget of two generations/batch two evaluates exactly four trials. Every reopened terminal is checked against reconstructed candidate PolicyPair/config, source fingerprint, split/role and registered interpreter identity before objective conditioning. Final return requires all fixed-budget generations and each full batch.
- Fresh JournalStore, resumed JournalWriter, fresh AlternativeTerminalStore and RegistryPersistence reopen return the exact same four terminal identities, with **zero additional interpreter calls and byte-identical file census** on a second invocation. The driver receives remaining generations, not the total budget again.
- The held cancellation test stops after the first actual durable terminal; resumption evaluates only the missing second trial. This is cancellation during the local adapter call, not terminal QMA cancellation or automatic acceptance of a future new job.
- A separate local refusal injected immediately after durable trial reservation and before execution leaves one pending intent. Restart returns typed `trial_recovery` unavailable-dependency, with zero interpreter calls, because no durable decision frontier exists. This is an explicit safe blocker, **not successful recovery from every post-ask interruption**. Recovery from partially executed/unknown effects, cancellation after a durable reservation and normal QMA reconciliation policy remain separately required. No pending intent was relabeled or silently dispatched twice.

## Commands, archive and limits

From `/workspace/QMX-release`, current test command: `uv run --no-sync pytest -q -p no:cacheprovider qmb/tests/test_operator_alternative_study.py qmb/tests/test_optimize_replay_study.py qmb/tests/test_optimize_resume.py`. Exact final result is recorded below. An initial mistaken attempt named nonexistent `qmb/tests/test_alternative_study.py`; pytest refused collection with no tests run. It was corrected without changing source/tests.

Finite command: `PYTHONPATH=/workspace/QMX-release/qmb/tests uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_operator_study_fixed_budget_frozen.py` — exit 0; all current held hashes matched entry/end. It reuses the existing actual local fixture, official persistence/sampling APIs and the registered local interpreter, and explicitly injects a local before-execution typed refusal for one reservation control. Original stopped diagnostic plus exact argv/source-hash notes and results are retained in the shared archive.

No product/test edits, commits, credentials, network/provider calls or security testing. CLI/private descriptor selection, normal public registered QMA ingress, actual one-run occupancy, expected whole Study artifact/JobHandle lifecycle, complete producer witness, sensitivity deliverable, durable cross-invocation reuse and installed entrypoint integration remain **unaccepted**. A library adapter positive does not prove those unfinished routes. This report neither grants complete security approval nor approves the candidate release.

Final current-freeze suite result: **20 passed in 6.48s**. Both current held source/test hashes still matched at completion.

Archive SHA-256: frozen finite program `ced5d5aa3baa9291270b9e095549aa08bb8e5eb1ecbd7fa2f0d7ba9ec127eab0`; results `07c86c58ec2ea0cd3b819210941c92904c0dbfbbf662f2a6fc145f4612f307fe`; argv/source notes `1c7edb5fbfba00e5edc649e326abb789aafe162700e04cef063e68239f131ba1`; archive manifest at completion `b37023489611496845af49888a243a95d171686af93ee65e7df2921ec0691aa6`.

## Corrected Study/protocol8 re-review — bounded PASS

2026-10-01. Independent Sol ordinary library identity/lifecycle/persistence review. Data confirmed complete eight-path stable hold after its last reserve-readback correction. The final terminal-store hash `692fed…` superseded `052fa…` before this review; all eight final hashes below matched entry, finite diagnostic exit and final report census. No source/test edits, commits, providers, credentials or security testing. Original FAIL evidence remains intact.

The prior computational/occurrence identity P2 is corrected in the supported path. Plan construction now fingerprints the complete computational base separately from its operational binding. Stable StudyFP still includes source/list identity, split/role, resolved config/PolicyPair, interpreter registration, initial state, epoch, spec/evidence refs, pinned registry context, typed space/seed/direction/rounding/batch/fixed total generation budget/objective/bindings/sampler provenance. Operational fingerprint separately binds job/attempt/environment/occupancy, runtime descriptor, writers/streams and roots. `run_operator_alternative_study` recomputes both from current nominal trusted inputs before effects. A plan from another job/attempt cannot be borrowed; its fresh valid plan can legally reuse the same computation while producing a distinct current occurrence.

**Executed frozen command:** root cwd, `uv run --no-sync pytest -q -p no:cacheprovider qmb/tests/test_operator_alternative_study.py qmb/tests/test_alternative_terminal_phases.py qmb/tests/test_alternative_execution.py qmb/tests/test_optimize_sensitivity.py qmb/tests/test_alternative_sensitivity.py` — **60 passed in 2.64s**. This joint run includes actual stored-trial sensitivity integration under the same freeze, resolving the previous pure-fold-only integration limit. It does not add CLI/QMA availability.

The rebound original finite meaningful fixture control exercises two generations × batch two: exactly four actual local registered interpreter calls, four durable checked terminal artifacts, then fresh JournalStore/JournalWriter/TerminalStore/RegistryPersistence instances return the same whole history without file changes or evaluator calls. Changing rounding changes computational identity; malformed rounding and foreign context with the old plan refuse with zero calls and unchanged file census. A separately constructed second job/attempt/environment/occupancy plan retains StudyFP, changes operational fingerprint, returns the exact old terminal fingerprints without changing trial ledger bytes or evaluating again, and writes a distinct actual occurrence witness. No historical terminal/job label is rewritten.

**Versioned durable phase controls:** protocol-v1 reservation is written and exact-row reread before start; start matches reserved label/candidate/source/split and is physically reread before evaluator entry. A fresh reopened store with reservation but no start safely starts and completes the two-trial fixed budget (zero original calls, total two). A started ask with no complete checked CT-13 effect chain remains unavailable/unknown and never evaluates again (zero calls in the injected pre-executor interruption). A local failure after actual evaluation/complete CT-13 chain but before terminal append leaves one started intent; fresh stores reconstruct the actual receipt/physical chain and append terminal evidence without replaying that trial, then execute only the remaining trial (one original call, total two). Terminal-written-but-ACK-lost is separately covered by the frozen test and likewise skips completed work. Removing phase_protocol from an actual reserved row makes it legacy; fresh reopen blocks with zero calls because absence of start is no longer proof of no evaluation. These are readback-supported positives/refusers, not inference from exit code.

Cancellation after the first durable terminal produces an incomplete/refused Study barrier and preserves that terminal; continuation completes only the remaining trial. Full return requires every frozen generation/batch coordinate exactly once, deterministic resume of the sampler and exact source/PolicyPair/candidate/interpreter/objective identity. No fresh generations are added on repeated invocation and no partial/cancelled history is presented as a complete Study. `recover_alternative_run_receipt` is an existing dependency used by the new protocol path; this review exercises it through genuine local persisted CT-13 and typed source/registration controls rather than approving all unchanged recovery implementation independently.

**Sensitivity delivery:** `build_operator_alternative_sensitivity` reopens the completed exact terminal history, validates candidate/assignment/source/split/interpreter/writer and exact objective/unit/currency, reconstructs fixed-budget resume/barrier and feeds the existing shared sample fold. The finite positive with four checked trials returns matching terminal fingerprints without file changes or evaluator calls. Joint frozen tests cover the report adapter, pure fold and existing Book parity. The report is the truthful generic B-8 objective landscape, without fake CT-32/LedgerLine, Book/BMS keys, R, winner threshold or financial default. This is a library report artifact; its complete expected-result/CLI/QMA publication/join remains pending.

A variation changing the bound CT-13 boot writer while keeping an already witnessed second job/attempt refuses the immutable occurrence mismatch; sensitivity also refuses historical-writer mismatch. That is a changed operational-binding refuser, not a claim of general writer/boot migration support. The positive physical restart above restores the exact pinned evidence writers. Arbitrary writer migration/concurrent ownership recovery is outside this bounded acceptance.

No actionable finding remains in the frozen supported library slice. Actual source observations/splits, terminal/CT-07 persistence and occurrence witnesses in these controls are real local fixture evidence; the registered interpreter is an explicit local policy double and QMA spec/evidence/context references are fixture labels. This does not prove genuine normal public optimize.run/CT-47 ingress, actual occupancy/JobHandle expected artifact and producer verification, normal cardgraph publication, complete coupled QMA persistence, provider behavior, strict factory coverage or complete security/release acceptance.

### Exact source and diagnostic binding

```text
692fed1823137fc83f55977b673194ba7f7e98dfe773a6f5e9af8442f25c890b qmb/src/qmb/execution/alternative_terminal.py
e7c11ff7da89152ee5285d4447ede82bf418e36fdb6ed5cd01990cc2ed028ae7 qmb/src/qmb/host/operator_alternative_study.py
52b4e25a2e2ac526108dba5be9f11b84554d3c9a9c548076338140d704bcecbe qmb/src/qmb/optimize/alternative_sensitivity.py
64bcf7b56e142f291f98c47635d2eabe4307fc6bb46f62d081bb0205aa063131 qmb/src/qmb/optimize/alternative_study.py
1e6e6355ddb1b1b1eaa767878d46acbef9f3ffdd841414b04e5185ad3c1d91f5 qmb/src/qmb/optimize/sensitivity.py
20cb2ea673102b2e0c8a43187aad33e3d512741d809bfc5c6c651b88a30011af qmb/tests/test_alternative_sensitivity.py
379632a18f192e594e678c00044583bb1c3656f6b1901dc17f089c6026b86bcf qmb/tests/test_alternative_terminal_phases.py
c5f999557dacfed6bd3e34c6e53441c911f130481d7af09ceaf791bbacefcf21 qmb/tests/test_operator_alternative_study.py
```

Diagnostic command, root cwd: `uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_operator_study_phase_corrected.py` — exit 0. Program checks all eight sources at entry/exit; full argv/source notes and results retained:

```text
b0e96df5a7915290ac54e423a8fc393b0a6e7310690bc0806fb15faad7026518 review_operator_study_phase_corrected.py
0e5d7e4cc868a0290c1b7f5f25c2eaecacf677e7c4b15420c80b2f3dd004bead review_operator_study_phase_corrected.results.json
a7ef0ec9f1d4f58f2447142f67f3a26bd8c162f6238d2e2616de169ce0467fc5 review_operator_study_phase_corrected.notes.json
```

Owner/coordinator receive the completed verdict. Further product changes require a new freeze and re-review; the previous original FAIL scope is preserved.
