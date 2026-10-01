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
