# Independent Study and projection review

Reviewed checkout: `C:/Users/Mubarak/Documents/Codex/2026-10-04/task-20/study-public`, with HEAD `5acb4a6483567976be771880d57b30482da4ec6b` and the current uncommitted focused implementation. Reviewer made no production or test-source edits.

No remaining blocking correctness or authority findings in the reviewed source. Final commit and aggregate integration results remain the parent's responsibility.

## Contract and authority checks

- Exclusive descriptor presence chooses Book, Alternative, or AlternativeStudy. Malformed/conflicting descriptors refuse instead of falling through. Study execution and verification retain the complete preflight descriptor pin and reconstruct the Study through registered typed ports.
- Study verification refuses incomplete history and foreign occurrence identity before creating trials or an occurrence witness. Complete verification reopens durable history and produces identical result bytes without source writes.
- QMA retains the admitted TaskAgent, deployment receipt, worker acceptance, Task payload hash, exact attempt, grant, and post-preflight authority checks. The seven-field Study result is interpreted in its own format branch and matched to durable expected context and QMB source readback.
- Public DONE reads authenticate the originating owned ProductSession and require immutable expected context, exactly one checked COMPLETE proof, and fresh QMB verify-only equality.
- Public projection resolves one owned DONE Book using its declared result run_fp1, then freshly reopens that selected source. Unavailable unrelated Study history does not block an otherwise valid Book. Query authority returns a content-addressed saved-view body without publishing or creating a projection JobHandle.
- Existing public v1 has run_fp1/as_of and no predicate field. The existing canonical identity predicate `exclude: []` retains all source trades. Saved-view fp1 hashes the returned body.
- Windows qmb.exe receives production preflight. Default cancel paths are isolated by transport namespace and hashed job ID, preventing stale sentinels from another daemon root affecting an equal job ID.

## Independent validation

- Final exact Book integration case passed: `test_qma_registered_replay.py::test_authenticated_ct40_run_grant_reaches_real_registered_qmb_child[False-None]`, **1 passed in 83.01 seconds**. It exercises the real registered QMB child, durable DONE, fresh public readback, projection source/body/read-only assertions, separate read grant, duplicate rejection, reconnect, and fresh DaemonProcess restart. Durable test files are under `pytest-final-book3` beside this report.
- Latest targeted regression group: **7 passed in 7.61 seconds**, covering production CLI preflight, Study transport/format, and expected context. Earlier focused independent group: **17 passed** across Study, occurrence, transport, and durable context.
- `study-readonly-1/review-proof.json` records incomplete verification refusal without writes, complete verification equality without writes, foreign-attempt refusal without witness, conflicting descriptor refusal, two durable trials, terminal artifacts, and occurrence result.
- `nested_cli_resolution_probe.json` records the independently reproduced nested Windows PATH failure and successful runtime Scripts PATH prefix. This explained the fixture restart WinError2; no domain or authority bypass was introduced.
- Direct regressions passed for Windows qmb.exe recognition, distinct cancel paths for equal job IDs in different transports, stable cancel paths within a transport, and canonical acceptance of the identity predicate.

## Runnable final Book regression

Run from task-20, choose a fresh basetemp directory:

```powershell
. .\setup-runtime.ps1
@'
import os, sys
from pathlib import Path
os.environ['PATH'] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', '')
import pytest
raise SystemExit(pytest.main([
    'study-public/qa/integration/test_qma_registered_replay.py::test_authenticated_ct40_run_grant_reaches_real_registered_qmb_child[False-None]',
    '-q', '--basetemp=C:/Users/Mubarak/Documents/Codex/2026-10-04/task-20/review-artifacts/pytest-final-book-repeat',
    '-p', 'no:cacheprovider',
]))
'@ | & $lanePython -
```

Prior review findings were fixed and checked: incompatible projection response shape, overbroad fresh-source scan, Book composition-class comparison, unpinned test restart invocation, nested child PATH, default cancel collision, identity predicate, projection child deadline, and test socket deadlines. Production source verification remains bounded at 30 seconds; final fresh-read fixture uses a 90-second complete-frame socket deadline. The provider and Alternative interpreter remain explicitly synthetic offline fixtures; reviewer did not make live provider calls or claim a paid/model execution.

## Final metadata review outcome (recorded by the primary agent)

`study_review` subsequently reviewed the handoff, unapplied canonical-documentation
patch, sourceproof script and final evidence manifest. It reported no blocking
findings and independently verified eleven artifact byte counts/SHA256 values,
fifteen current source SHA256 values and staged Git blob IDs, exact sourceproof
manifest equality, actual authoring receipt, seven-field Study result, restart,
QMB byte snapshot, same admitted TaskAgent, one executed provider request and
projection fields. It confirmed synthetic/actor/grant-ceiling/platform boundaries.
No source files were edited and no suite was rerun for this metadata review.
