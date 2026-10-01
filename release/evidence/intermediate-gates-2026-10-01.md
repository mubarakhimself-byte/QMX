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
