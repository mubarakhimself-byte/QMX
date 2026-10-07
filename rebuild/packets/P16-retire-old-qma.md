# P16: Retire the old QMA runtime

## Goal
Delete the parts of `qma-daemon`, `qma-core` and `qma-wire` that the new packages replace, once nothing calls them.

## Read first
The P05 survival map (verdict "replace" or "delete"), updated with what P06–P15 actually built.

## Steps
1. For each module marked replace or delete, confirm it has zero production callers outside the old daemon. Move any remaining callers (QMB, QMN, UI) onto the new packages first, one PR per caller if large.
2. Delete in slices, one PR per area:
   - task graph and canonical join
   - hooks
   - proxy and native sessions
   - bus
   - old memory
   - old transport (`process.py` server parts, `pairing.py`, `http_pair.py`)
3. Remove the strict-xfail tests from P01 together with the code they covered.
4. Update `pyproject` workspaces and the lock file.

## Done when
- `just test-all` is green.
- The PR shows LOC removed.
- QMB and QMN suites are unaffected.
- The daemon process is either gone or reduced to a thin host for the parts marked keep.
