# QMB runtime ledger amendment - DRAFT for the integrator

This is an amendment proposal to the single backend integration ledger, not a
replacement work ledger. Base is `33165e84146b2a6da32c7e536b698c4fa609be3f`.
The clean combined fourteen-failure observation is authoritative. The mixed-source
quality twenty-six-failure run was not used for acceptance or repair decisions.
Candidate-only baseline reproduced thirteen failures; corrected Click already passed.

| Original cluster | Final disposition | Local root-cause commit | Evidence |
|---|---|---|---|
| Windows research store (5) | Repaired; native cause captured first; atomic no-follow publication and durable retry acknowledgement retained | `2f7eb957` | native-{cause,open-existing,access}.txt; store-reviewed: 26 passed / 5 existing skips |
| Scaffold contracts (3) | Immutable native declarations/sentinel; narrowly proven CLI claim read and StoreReceipt vocabulary | `c5107b0f` | structural-reviewed: 74 passed / 4 existing skips; strict types zero errors |
| Durable analysis examples (2) | Explicit operator source and durable reader locator; genuine persisted replay fixtures | `9406004b` | analysis-reviewed: 47 passed; source integrity refusals retained |
| Escaped Windows diagnostic assertion (1) | Assert actual reason text rather than mapping repr | `9e335fbe` | structural-reviewed |
| Host filesystem adapter versus bot structural assertion (1) | Runner/worker execution-boundary assertion; native filesystem ctypes is independent of bot confinement | `2f190f26` | structural-reviewed; no confinement claim or settings changes |
| Mixed Click pin (1) | Correct pinned candidate/child environment passes; no source change needed | base/environment | baseline-clusters and full QMB provenance: Click 8.4.2 |
| Alternative Study ingress (1) | Unresolved integrator CT47 dispatch/envelope/result-schema seam; registered owner/spec/source probe isolates it | `423241e5` (diagnosis only) | study-real-registered-command-recorded; original characterization remains red |

Full QMB: **1460 passed, 19 skipped, 1 failed** in 940.45 seconds. The only
failure is the original Alternative Study characterization. The nineteen skips
are existing Windows symlink/chmod/POSIX-descriptor guards; no new skips/xfails
were added. Full QMB was run at `9406004b` with a clean working tree. Subsequent
commits are documentation only; the thirteen changed Python files are identical.

Final QMB Ruff lint passes, strict Pyright reports zero errors/warnings, and all
thirteen changed Python files pass Ruff formatting. Whole QMB format check is
still red on five byte-identical base files: analysis/project.py,
execution/alternative.py, execution/alternative_terminal.py, host/book_handler.py,
host/operator_alternative_study.py. `format-inheritance.json` records git diff
exit zero for those files. No public projection implementation was changed.

This is bounded runtime verification, not a full workspace coverage/release gate
or fresh frozen dependency-install claim. Focused and full tests used --no-cov;
no coverage floors were changed or represented as passed. Intake locking was
not reopened. QMA/QMN/UI/manifests/locks/shared public projection/CT47 files
remain untouched. No push, merge, provider/exchange/live-money actions occurred.

The review is an explicit self-review against source, negative regressions,
native OS evidence and primary documentation; no independent peer review is claimed.
Each root-cause commit includes its scope and evidence review draft. Canonical
documentation patch is unapplied and passes git apply --check --unidiff-zero.
The zero-context draft avoids trailing whitespace from nested diff context. The final task-16
handoff, source/evidence hashes, binary diff and commit bundle are the deliverables.
