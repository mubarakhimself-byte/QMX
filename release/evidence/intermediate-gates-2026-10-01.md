# Intermediate integration gates — 2026-10-01

These commands ran against the active release working tree while bounded Luna
repairs were in progress. They are diagnostic evidence, not final immutable
candidate or installed-product acceptance. The release gate remains fail-closed.

| Check | Result | Trace |
|---|---|---|
| Root product tests and branch coverage | FAIL: 14 failed, 5,386 passed, 7 skipped; aggregate 78.34% | `/workspace/qmx-full-source-intermediate.log` |
| Root per-package coverage | FAIL: QMB 75.26%, QML 77.41%, QMN 74.39%; active operator source not yet tracked | `/workspace/qmx-intermediate-coverage.json` |
| Nested QMA tests and branch coverage | FAIL: 2 failed, 1,681 passed, 2 skipped; aggregate 78.95% | `/workspace/qmx-nested-intermediate.log` |
| Root strict types | FAIL: 104 errors, including unfinished trusted-source callsites and test/example protocol typing | `/workspace/qmx-root-types-intermediate.log` |
| Independent QA suites, isolated by epic | 21 PASS, 2 FAIL across 23 suites | `/workspace/qmx-qa-epics-intermediate.json` |
| QA-13 before later active source changes | PASS: 43 tests, with the root environment on PATH | `/workspace/qmx-qa13-current.log` |
| Book signed financing correction | PASS: 25 tests; independent Sol debit/credit and recovery approval at `80647b97` | `/workspace/qmx-signed-financing-correction.log`; `partial-financing-review.md` |

The root product command was the complete `poe test` package/extension/QML/QMB/QMN
selection and all declared source roots, with branch coverage and the unchanged
80% aggregate threshold. Its report was written to the absolute intermediate
coverage path above. The nested command selected `packages tests` and all three
QMA source roots, also with branch coverage and the unchanged 80% threshold.

Root failures identified node failure-register/readiness and venue import-boundary
violations. The configured node owner is correcting them without relaxing the
architecture checks. Nested failures identified coordinated query fixtures and an
example that no longer supply the required positive delegated attempt identity.
QA-18 independently found a provider refusal creating a new replay namespace;
the intake owner is restoring the no-partial-ingest behavior. The later QA-13 run
observed incomplete trusted-source callsites during the ongoing integrity repair.

The combined QA command cannot safely collect all epic directories in one Python
process: repeated module names and local helper imports collide. The diagnostic
runner `/workspace/qmx-run-qa-epics.py` runs each existing epic directory in a
separate process and records its exact command, exit code and trace. It changes
no assertions. All failed checks must be rerun after their source corrections,
then final acceptance must bind one immutable commit and its actual artifacts.

Independent review findings for altered replay price paths/request references and
mutable callback evidence remain open in their dedicated review records. Passing
local economic fixtures do not supersede those failures or establish provider
connectivity. Native Windows, the separately owned reviewed UI contribution,
external integrations, and incomplete security verification remain pending.

## Active receipt and CLI typing diagnostics

Root ran `uv run --no-sync poe types` during active receipt integration. First trace `/workspace/qmx-current-receipt-integration-types.log`: **FAIL, 15 errors**, including necessary malformed nominal-field guards typed too narrowly and an untyped test JournalWriter wrapper. Numeric corrected those boundaries without removing runtime validation. Second trace `/workspace/qmx-corrected-receipt-integration-types.log`: **FAIL, 18 errors**, all in the newly active `qmb/tests/test_operator_alternative_cli_journey.py`; the earlier QMN diagnostics are absent. The CLI test owner is correcting imports, optional narrowing and path typing while establishing its actual product-child positive. These are mutable intermediate checks, not final source-gate results. No ignore or configuration waiver was applied by root.

Root's corrected protection-source/plan behavior selection `uv run --no-sync pytest -q qmn/tests/test_qmn_protection_state.py qmn/tests/test_qmn_live.py qmn/tests/test_qmn_data.py qmn/tests/test_qmn_loop.py qmn/tests/test_qmn_protection_plan.py` produced **36 PASS, 1 SKIP in 1.06 seconds**, trace `/workspace/qmx-qmn-protection-source-corrected-root.log`. The skip explicitly requires a Spotware sandbox token and does not prove provider connectivity. Subsequent independent persisted-join review still fails as recorded in `qmn-protection-source-review.md`; these passing tests do not approve that source snapshot. Archived independent probes and their SHA256 inventory are at `/workspace/qmx-independent-review-archive/qmn-protection-source-diagnostics/manifest.json`.


## Checkpoint continuation root typing

After checkpoint remote `01fed525af621173cf58929801d9b58fc316d870`, root ran `uv run --no-sync poe types` from `/workspace/QMX-release`: **PASS, exit 0; 0 errors, 0 warnings, 0 informations**. Exact trace `/workspace/qmx-checkpoint-continuation-types.log`. Observed local HEAD during the run was `a2801f7f` with active working changes; this is a mutable integration diagnostic, not a final candidate gate or a frozen-source review. The declared root scope is `packages`, `extensions`, `qml`, `qmb`, `qmn`, `tools` in `pyproject.toml`; nested `qmx-agents` has its own quality surface and is not covered by this result. No floor, exclusion, assertion, ignore or typing configuration was changed.

Root separately repeated the documented optimize descriptor owner's command from `qmx-agents/packages/qma-core`: `uv run --no-sync python -m pytest -q -p no:cacheprovider tests/test_operation_descriptor.py` — **13 PASS in 0.12s**. That two-file implementation is awaiting independent review and does not implement the CLI/worker optimization path.

Root combined the corrected artifact reader and new private AD-32 lineage tests: `uv run --no-sync pytest -q -p no:cacheprovider qmn/tests/test_qmn_admission_artifacts.py qmn/tests/test_qmn_admission_evidence.py` — **8 PASS in 1.50s**, trace `/workspace/qmx-qmn-admission-corrected-lineage-root.log`. Focused four-path Pyright also returned zero errors. Exact held hashes are in their upcoming separate independent reports; completion, fresh capability checks, derived LIVE baselines and provider readiness remain unproved.
