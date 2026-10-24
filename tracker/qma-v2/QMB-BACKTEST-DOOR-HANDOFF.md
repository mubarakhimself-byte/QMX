# QMB backtest door: what the unit session needs to know

Written 2026-10-24 by the wrap-up coordinator. The operator ruled that the unit session owns QMB, so the wrap-up program leaves this work alone and hands it here, to avoid doing it twice.

## Where it stands

- Today, at `engine/base` `f05fc64b`, an agent's `run_backtest` refuses with "binds no qmb_backtest door". No host binds a backtest door or a Library landing (handover list A item 1).
- The wrap-up built a fix as PR 204 (`build/wu4`, head `aabb813b`). It is **open and not stacked**. Use it as a reference or a starting point, not as a finished piece.
- The design it follows is `research/methodology/60-wrapup-seams.md`, seam A (engine AD-31, Library AD-29, amended on 2026-10-24).

## What PR 204 proved works

- One function lands every backtest, `qmx_tools.service.backtest_and_land`. The copilot's tool and a workflow `app_op` node (`{app: qmb, job: backtest}`) land the same spec as one object id.
- `StoreLanding` (`qmx_library/adapter.py`) puts one `backtest-result` Draft. The `operator` principal lands on `main`, and `run:<id>` lands on `refs/runs/<id>` until the run passes.
- The replay runs in one child process. The door answers only on a clean exit with a complete report. `close()` kills live children.
- `backtest_status` and `backtest_results` read a landed `backtest-result` by its object id.

## Why it was not stacked

QMB's own house rules (`qmb/tests/test_qmb_scaffold.py`) reject it:
- QMB may import `subprocess` only under `qmb/orchestrator/` and in `qmb/host/runner.py`, and may never import `threading`. The new `qmb/host/backtest_door.py` imports both.
- The word "engine" is banned in QMB source, and the door's docstring uses it.

The mechanical fix: the child launch moves under `qmb/orchestrator/`, the thread lock goes, and the docstring is reworded.

## What QMB needs for a backtest that trades (the real gap)

PR 204's only runner is `silent`, QMB's silent slice handler. A result lands, but with no trades, no equity and no ledger line. A runner with a real bot needs three things QMB does not have:

1. **A typed-partition entry to the execution path.** The path that yields trades, equity and a terminal ledger line is `execute_recorded_replay_request` (`qmb/src/qmb/host/replay_execution.py:68`). It re-resolves a persisted CT-47 request from the CT-10 receipts under `raw_store_root` and refuses any supplied source that does not match that readback (`:120`, `:762-806`). The Library's market-data door hands typed monthly partitions, which cannot pass that check. DR4 added a reader-level typed entry (`read_typed_replay_source`, `qmb/host/replay.py:608`); the execution path needs the same.
2. **Execution inputs a recorded configuration can name.** A run needs a `BoundExecution`, a `BookAdmissionContext` (risk, order and close policy), a journal reader, a terminal ledger root and a CT-12 split fingerprint. Today the fixtures and examples build all of these in Python. Nothing turns them into data.
3. **A shipped bot that can be named by reference.** The only bots that trade are test fixtures (`qmb/tests/replay_fixture_support.py`). `qmb/examples/ql7_host_usage.py` builds its bot inline. Nothing under `qmb/src` or `qml/src` can be named by a run configuration.

## Smaller gaps found on the way

- `compare_runs` (`qmx_tools/functions.py`) reads only old `artifacts/` refs, so two landed results cannot be compared by object id.
- Run configurations are files at `<home>/backtests/<ref>.json`, not UI-editable.
- The child's memory limit applies only on POSIX, not on Windows.
- A full month of one-minute data needs about 16 GB in QMB's replay reader (P-QMBREAD). Bound runs to about 1,000 steps until the reader is windowed.
