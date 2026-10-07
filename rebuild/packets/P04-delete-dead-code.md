# P04: Delete dead code and clutter

## Goal
Remove code that nothing in production calls, test fixtures living in `src/`, and non-code clutter in the code tree. Behaviour must not change.

## Delete
| Path | Why |
|---|---|
| `qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/memory_extraction.py` and its tests | LangMem extraction, called only by its tests. LangMem is dormant upstream; memory is redone in P07 |
| `qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/authored_graphs.py` and `tests/test_authored_graphs.py` | No production caller; replaced by the workflow compiler in P10 |
| `qmx-agents/packages/qma-ui-contract/` | Empty package (only `STUB.md`) |
| `langmem` optional extra in pyproject files and `uv.lock` | Unused after the above |

## Move (from src to tests)
| Path | Where |
|---|---|
| `qma/daemon/kit_journey.py`, `kit_journey_weak.py`, `kit_journey_nested.py`, `kit_journey_retry.py` | `qma-daemon/tests/support/` (their docstrings say they are fixtures) |
| `qma/daemon/taskgraph/restart_fixture.py` | `qma-daemon/tests/support/` |

If production code imports any of these, stop and list the importers in the PR instead of moving.

## Remove from the code tree (keep in git history)
- `_docwork/` (planning extraction ledgers, about 1.8 MB of YAML)
- Evidence and delivery folders added during Oct 1–5, for example any `evidence/`, `delivery/` or `acceptance*.json` directories under `qmx-agents/`, `release/` or `workroom/` that only hold run receipts. List each removed directory in the PR.
- Root files `FINAL-REPORT.md`, `FIX-GOAL.md`, `FIX-LEDGER.md`: move to `archive/2026-10-fix-round/`.

Do not touch `docs/` or `_bmad-output/`; the documentation pass handles those later.

## Steps
1. For each target, prove it is unused: `rg` for imports and string references, including entry points and `importlib`. Put the proof (one line each) in the PR.
2. Delete or move. Fix imports in tests.
3. Run `just test-all` (from P01).

## Done when
- `just test-all` has the same pass, skip and xfail counts as P01's baseline, minus the deleted tests.
- The PR lists lines removed per area.

## Out of scope
Splitting `process.py`, merging memory modules, provider collapse. Those are replaced, not refactored (see DESIGN §3).
