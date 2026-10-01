# Current QML source coverage measurement

Intermediate FAIL, not final-candidate evidence. QML source is the independently reviewed footprint/generation corrections through `6ae34954`; no QML source changes occurred during this run. Working candidate at start: `7de89439` (other product surfaces still under repair).

```text
COVERAGE_FILE=/workspace/qmx-qml-current-measurement uv run --no-sync pytest -q qml/tests qmb/tests/test_ql7_host.py qmb/tests/test_sandbox.py --cov=qml/src --cov-branch --cov-report=json:/workspace/qmx-current-qml-coverage.json --cov-report=term --cov-fail-under=80
```

372 tests passed; coverage gate failed at 78.09% against the unchanged 80% requirement. Trace: `/workspace/qmx-current-qml-coverage.log`; exact source-only counters: `/workspace/qmx-current-qml-coverage.json`. This scoped run is diagnostic and does not replace the full root gate or its package/contract checks. Independent review identified further meaningful public conformance, footprint-resolution, lifecycle and declared-confluence journeys to characterize; padding, source exclusions and floor changes are not authorized fixes.

## Public-contract characterization measurement

Test-only commit `0e87c49682485c4858b9e5622691cf7c4238bc85` adds real public factory/absence/future-knowability, foreign-frame, callback/refusal, confluence identity and producer-template budget/binding controls. Six focused cases pass. QML product source remains unchanged from the reviewed corrections.

```text
COVERAGE_FILE=/workspace/qmx-qml-expanded-measurement uv run --no-sync pytest -q qml/tests qmb/tests/test_ql7_host.py qmb/tests/test_sandbox.py --cov=qml/src --cov-branch --cov-report=json:/workspace/qmx-expanded-qml-coverage.json --cov-report=term --cov-fail-under=80
```

Result: **378 tests PASS; coverage FAIL 78.4022796501916%**. Exact source-only numerator is 7,979 covered line/branch units out of 10,177; another 163 are needed to reach the unchanged 80% floor. Trace `/workspace/qmx-expanded-qml-coverage.log`, counters `/workspace/qmx-expanded-qml-coverage.json`. This is meaningful behavior characterization with a remaining gate failure, not acceptance or a replacement for the full root and package gates.

## Recovery and canonical-persistence expansion

After the seventh public-contract characterization and actual host canonical persistence/graduation controls, root ran `COVERAGE_FILE=/workspace/qmx-qml-current-recovery-measurement uv run --no-sync pytest -q qml/tests qmb/tests/test_ql7_host.py qmb/tests/test_sandbox.py qmb/tests/test_research_host_store.py qmb/tests/test_ql7_graduation_recovery.py --cov=qml/src --cov-branch --cov-report=json:/workspace/qmx-qml-current-recovery-coverage.json --cov-report=term --cov-fail-under=80`. **395 passed; coverage gate FAIL**, exit 1. Covered units 7,980 / 10,177 = **78.4121057%**, still short by 162 units for 80%. Trace `/workspace/qmx-qml-current-recovery-coverage.log`; JSON as named above. QML source did not change for this measurement; mutable unrelated QMA/projection edits were present and this remains an intermediate source-only measurement, not final candidate acceptance. Host persistence behavior and independent security approval are separate from coverage success.
