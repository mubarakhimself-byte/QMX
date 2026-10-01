# Sensitivity3 bounded independent review — PASS fold and source review

2026-10-01. Independent Sol ordinary pure-fold/Alternative adapter source review. Held entry/end and parity diagnostic checks matched:

```text
1e6e6355ddb1b1b1eaa767878d46acbef9f3ffdd841414b04e5185ad3c1d91f5 qmb/src/qmb/optimize/sensitivity.py
8ab96c0a0be14cc5c1b06533121290839f9288333651a9748f3c675e75fe784c qmb/src/qmb/optimize/alternative_sensitivity.py
20cb2ea673102b2e0c8a43187aad33e3d512741d809bfc5c6c651b88a30011af qmb/tests/test_alternative_sensitivity.py
```

Main governing `c3e8ec5` QMB B-8/DEC-0169 requires sensitivity slices, good-region clustering and isolated-spike analysis as data in the optimization deliverable; ATC adoption DEC-0436 cannot require fabricated Book/CT-32 evidence. These changes provide an exact typed sample entry point into the existing report fold and a read-time adapter over actual Alternative terminal evidence. They add no public operation, financial threshold, default finance, LedgerLine or CT-32 result for ATC.

## Passed bounded contracts

- Both Book and generic sample paths call the same `_assemble_report`: distribution, parameter slices, neighbourhood graph, good-region clusters and winner stability use the existing schema and identity. A finite equivalent USD sample/control built from the existing explicit local Book LedgerLine fixture confirmed **full report canonical identities and fingerprints equal**. This parity control is pure fixture evidence, not a stored CT-32 proof.
- Generic samples are exact typed values and are reconstructed at fold entry; boolean/float objectives are refused, Money must be representable at official storage scale, non-money carries no currency, parameter assignments are canonical, optimistic taint is mandatory and each trial ID occurs once. World/role and objective units/currency cannot be silently mixed. Existing tests cover invalid world/currency/taint, duplicate identity, binary float parameter, mixed parameter spaces, aborted roles and undeclared direction.
- Existing Book excluded-trial reasons remain preserved for aborted/refused, missing/undefined objective and unmapped assignment. The non-Book entry takes already attributed completed samples; it does not convert failures into zeros. ATC's adapter requires the complete declared budget and each trial exactly once before analysis, refusing incomplete history.
- Statistics stay exact except the existing named square-root conversion boundary, whose fixed scale/rounding is recorded in distribution identity. Raw binary float is not stored as identity. Report explicitly makes no edge claim, search-quality verdict or invented threshold; median-based good regions remain descriptive analysis. Exact numerical correctness/refusals and reproducible schema are covered by the existing Book tests.
- Static Alternative adapter review verifies actual terminal reopening through CT-13/CT-07-backed store, exact admitted plan reconstruction, canonical labels/assignments and unique generation/ask coordinates. It reconstructs candidate PolicyPair/config from every assignment, compares source/split/role/interpreter registration and journal writer/stream, reads the declared exact persisted objective with its units/currency, checks complete history through resume_stepper, then uses the shared fold. The wrapper identity includes plan, exact terminal artifact refs and report identity. It does not execute trials or manufacture monetary values.

The adapter currently selects trial labels using the operational plan fingerprint. This is coupled to the already reported Study computation/occurrence identity issue; it needs coordinated re-review when that owner repair changes the plan/Study identity. This report does not approve that separate identity defect.

## Commands and proof boundary

From `/workspace/QMX-release`:

```sh
uv run --no-sync pytest -q -p no:cacheprovider qmb/tests/test_optimize_sensitivity.py qmb/tests/test_alternative_sensitivity.py -k 'not operator_adapter'
```

**30 passed, 1 deselected in 0.75s.** These are the frozen fold/schema and relevant Book controls. The full two-file command initially also passed **31 tests in 0.90s**, including the adapter's actual persisted local trial-history positive/incomplete refuser. That test imports the actively changing Study adapter/fixture, which are outside this three-file freeze; its result is supplementary read-time observation, **not frozen Study integration approval**. Neither that test nor the owner's broader 55-test run is counted as closed Study proof here. A coordinated held Study plus sensitivity freeze must rerun the actual durable journey and assert the Study deliverable contains this report; that additional integration assertion remains pending.

Finite pure parity command: `uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_sensitivity_book_sample_parity.py` — exit 0, all three held hashes checked entry/end. The first version of this diagnostic accidentally compared bound `fingerprint` methods instead of calling them, after canonical-body parity had already succeeded; it was corrected to compare the returned fingerprint values. That diagnostic error changed no product/test source or runtime evidence and is preserved in archive notes.

No product/test edits, commits, credentials, provider calls or security testing. Actual CLI/QMA operation route, one-run occupancy, complete Study artifact delivery, durable producer occurrence, restart/cancel/reuse semantics and installed release remain pending. This bounded PASS concerns the frozen pure fold, schema parity and adapter source checks; it is not complete candidate or security approval.
