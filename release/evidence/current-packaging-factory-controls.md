# Current packaging and factory controls

This is mutable-worktree diagnostic evidence, not final candidate acceptance. Base HEAD before execution was `59ed4268`; active QMA, projection and research-store edits were present. Product artifacts still belong to the earlier frozen candidate recorded in CANDIDATE_STATUS.md.

- `uv run --no-sync pytest -q tools/tests/test_release_gate.py tools/tests/test_release_install.py` — **PASS**, 130 tests, `/workspace/qmx-current-packaging-controls.log`. Installer positive controls use labeled mocked venv/pip; real installation evidence remains separate. Release gate negative controls retain all 17 required categories and reject stale, missing, blocked and malformed evidence.
- `uv run --no-sync pytest -q tools/tests adws/tests` — **FAIL**, 573 passed, 1 failed, `/workspace/qmx-current-factory-controls.log`. The actual-workspace ambient scanner detects `uuid.uuid4()` in the in-progress research-store repair below the composition root. Numeric owner is repairing temporary-name creation while preserving exclusive/no-clobber behavior. The scan is unchanged; this run is not reported as factory PASS.

Final immutable source must rerun these controls after all reviewed repairs. No factory dependencies are added to product runtime environments.
