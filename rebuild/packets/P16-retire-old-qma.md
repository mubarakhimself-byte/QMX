# P16: Retire the old QMA runtime

## Goal
Delete the parts of `qma-daemon`, `qma-core` and `qma-wire` that the new packages replace, once nothing calls them.

## Read first
The P05 survival map (verdict "replace" or "delete"), updated with what P06–P15 actually built.

## Blast radius (hard limits)
- **In scope:** only `qmx-agents/packages/qma-daemon`, `qma-core`, `qma-wire` (the old QMA runtime), plus moving `qmx-apps/` and `qmx-control/` under `qmx-agents/packages/`.
- **Out of scope:** `packages/qmf-*`, `qml/`, `qmb/`, `qmn/` (including MIS), `extensions/`, `apps/`, `docs/`. Never delete anything there. You may only change an import line where it points at a deleted QMA module, and only to point it at its new owner.

## Two phases (separate PRs)
- **P16a, plan only.** Write `rebuild/reports/p16-deletion-plan.md`, with one row per module to delete:
  - path and LOC
  - every remaining caller anywhere in the repo, including QMB's `qmb host` CLI, tests, entry points and string/dynamic references
  - what replaces it (the new package and function)
  - the risk if it's wrong
  - an explicit "keep" list with reasons

  Merge the report and **stop**. Claude reviews it before anything is deleted.
- **P16b, delete.** The plan is approved with the rulings in DESIGN §12c (2026-10-09). Follow §12c item 7 for the slice order: one PR per slice, each with `just ci` green.

## Steps (P16b)
1. For each module marked replace or delete, confirm it has zero production callers outside the old daemon. Move any remaining callers (QMB, QMN, UI) onto the new packages first, one PR per caller if large.
2. Delete in slices, one PR per area:
   - task graph and canonical join
   - hooks
   - proxy and native sessions
   - bus
   - old memory
   - old transport (`process.py` server parts, `pairing.py`, `http_pair.py`)
3. Remove the strict-xfail tests from P01 together with the code they covered.
4. Update `pyproject` workspaces and the lock file. Move `qmx-apps/` and `qmx-control/` under `qmx-agents/packages/` and use one shared lock where possible.

## Done when
- `just test-all` is green.
- The PR shows LOC removed.
- QMB and QMN suites are unaffected.
- The daemon process is either gone or reduced to a thin host for the parts marked keep.
