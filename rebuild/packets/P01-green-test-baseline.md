# P01: Green test baseline

## Goal
Every Python test suite on `rebuild/base` either passes or is explicitly marked with a reason, so later packets can tell a regression from old breakage. Make the suite fast enough to run on every packet.

## Known state (verified 2026-10-07, see `research/audit-code.md` §3)
- `qmx-agents/packages/qma-daemon/tests`: 1,868 tests.
  - 2 files fail at collection: `test_combined_backend_composition.py` and `test_spot_daemon_binding.py` import `test_spot_paper_slice` from `qmn/tests/`.
- 4 tests fail reproducibly; a request stays `running` past a `time.monotonic()` deadline:
  - `test_canonical_request_join.py::test_host_admitted_request_has_canonical_owner…`
  - `test_canonical_request_join.py::test_second_request_cannot_claim_same_canonical_task_attempt`
  - `test_canonical_request_join.py::test_two_canonical_tasks_retain_behavioral_memory…`
  - `test_composed_capabilities.py::test_selected_harness_joined_callback_and_memory[allowed]`
- 1 flaky test under load: `test_deep_agent_actor::test_one_selected_specialist_two_jobs`.
- 4 LangMem tests fail with `ModuleNotFoundError` (optional extra not installed). P04 deletes LangMem; for now make them skip.
- The serial run takes about 50 minutes. `pytest-xdist` is not installed.
- `qmx-agents/.venv` in old checkouts is broken. Build a fresh one with `uv sync --frozen`.
- Other suites (QMF packages, qml, qmb, qmn, adws) have not been run since the audit.

## Steps
1. Fresh environment: `uv sync --frozen` at the repo root and in `qmx-agents/`. Record the exact commands in the PR.
2. Run every suite once and record pass/fail/skip counts per suite: `uv run poe test` at the root, plus the qmx-agents suites.
3. **Collection errors.** Move the shared helper out of `qmn/tests/test_spot_paper_slice.py` into a small importable test-support module (for example `qmn/src/qmn/testing/spot_paper.py`, or a `conftest.py` fixture), and import it from both places. Test files must not import other packages' test files.
4. **LangMem tests.** `pytest.importorskip("langmem")` at the top of the file.
5. **The 4 deadline failures.** Time-box diagnosis to 2 hours.
   - If the root cause is a test-side timing assumption or a small code bug, fix it.
   - If the fix needs a redesign of `canonical_join.py` (scheduled for removal in P16), mark the tests `@pytest.mark.xfail(strict=True, reason="canonical join retired in P16; <one-line cause>")` and describe the cause in the PR.
6. **Flaky test.** Find the wall-clock dependency. Replace it with an event or condition wait, or a longer deadline that comes from a test constant. Do not just retry.
7. **Speed.** Add `pytest-xdist` to the dev group. Make the default run `-n auto` where the suites are parallel-safe. Mark tests that are not safe with `@pytest.mark.serial` and run them in a second pass. Target: the full qma-daemon suite under 15 minutes on the operator's laptop.
8. Add a root `just test-all` (or `poe test-all`) that runs every suite in the right environment and prints one summary table.

## Done when
- `just test-all` exits 0, apart from the strict-xfail tests listed in the PR.
- The PR shows a table: suite, passed, failed, skipped, xfailed, duration.
- No threshold lowered, no test deleted (except moving the shared helper).

## Out of scope
Coverage gate (P02), refactoring production code beyond a minimal bug fix.
