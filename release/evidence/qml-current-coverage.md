# Current QML source coverage measurement

Intermediate FAIL, not final-candidate evidence. QML source is the independently reviewed footprint/generation corrections through `6ae34954`; no QML source changes occurred during this run. Working candidate at start: `7de89439` (other product surfaces still under repair).

```text
COVERAGE_FILE=/workspace/qmx-qml-current-measurement uv run --no-sync pytest -q qml/tests qmb/tests/test_ql7_host.py qmb/tests/test_sandbox.py --cov=qml/src --cov-branch --cov-report=json:/workspace/qmx-current-qml-coverage.json --cov-report=term --cov-fail-under=80
```

372 tests passed; coverage gate failed at 78.09% against the unchanged 80% requirement. Trace: `/workspace/qmx-current-qml-coverage.log`; exact source-only counters: `/workspace/qmx-current-qml-coverage.json`. This scoped run is diagnostic and does not replace the full root gate or its package/contract checks. Independent review identified further meaningful public conformance, footprint-resolution, lifecycle and declared-confluence journeys to characterize; padding, source exclusions and floor changes are not authorized fixes.
