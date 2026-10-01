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

## Layer1 and source-admission characterization

After the reviewed Layer1 diagnostic correction (source `d51f313326cdcf24cc3b1e38c27d87a7b6532690`) and the four public footprint tests (held SHA256 `57a713a5c0d3d2f93bda07fe1e65f8e0f42b845d510153841e24e8cfaabddd6c`), the implementation agent repeated the same recovery-inclusive test selection with unchanged `--cov=qml/src --cov-branch --cov-fail-under=80`. **403 passed; coverage gate FAIL**, exit 1. Exact units: 5,815 covered statements plus 2,285 covered branches = **8,100 / 10,229, 79.1866263%**, still 84 units below the unchanged 80% requirement. Raw JSON `/workspace/qmx-qml-footprint-admission-coverage.json`; trace `/workspace/qmx-qml-footprint-admission-coverage.log`. This is an intermediate source-only measurement with other components under repair, not frozen whole-candidate acceptance.

The earlier 399-test report's counters were reported by its owner (8,072/10,229, 78.9128947%) but its reused raw artifact path was overwritten by a later run; it is not retained raw evidence. The uniquely named 403-test JSON/log above are retained. Subsequent measurements use distinct paths. Independent semantic review and root focused tests are recorded separately; a passing behavioral suite does not change the coverage verdict.

## Nested confluence and nominal-time correction

The nested confluence characterization (`845b7de696ba3cce224cf75b81a039810d23b727`) yielded **406 passed; coverage FAIL 79.3234920%**, 8,114/10,229 units, 70 short. Its raw artifacts are `/workspace/qmx-qml-nested-confluence-coverage.json` and `.log`.

The actual malformed nominal-Instant refusal correction and declared-evidence characterization are committed at `724f62b57cc90d1be491c4c0a7c21971aa574f7d`. Root and independent reviewer each pass 38 protocol/admission tests; independent real reader-to-callback controls cover boolean/string/int64 overflow and valid boundary times. The implementation agent's unchanged full recovery-inclusive coverage selection yields **418 passed; coverage FAIL 79.4017010%**: 5,827 covered statements plus 2,295 branches = **8,122/10,229**, still 62 units short. Exact raw artifacts `/workspace/qmx-qml-nominal-instant-coverage.json` and `.log`; root focused trace `/workspace/qmx-nominal-instant-root.log`. Final frozen root/package gates remain required. No floor/exclusion/assertion has been changed to turn this measurement into PASS.
