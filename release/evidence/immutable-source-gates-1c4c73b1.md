# Immutable intermediate source gate results

Exact candidate: `1c4c73b1e51e9194464601830e7543ecd1108b6d`, registered
`/workspace/QMX-package-replay` worktree, its own locked non-editable-tooling
workspace environment (product packages editable only for source tests).
Debian 13 x86-64, CPython 3.14.7. No active release-worktree changes were
measured in this report.

| Gate | Result | Evidence |
| --- | --- | --- |
| Locked dependency setup | PASS | `/workspace/qmx-replay-snapshot-setup.log` |
| Full source pytest and coverage: `uv run --no-sync poe test` | FAIL coverage; 5,424 tests PASS, 7 SKIP, 2 warnings; 384.92 seconds | `/workspace/qmx-replay-snapshot-source-gates.log` |
| Aggregate coverage floor 80% | FAIL, 79.00% | `/workspace/QMX-package-replay/coverage.json` |
| Per-package coverage: `uv run --no-sync poe cov-report` | FAIL: QMB 76.28%, QML 77.64%, QMN 74.74% | `/workspace/qmx-replay-snapshot-package-coverage.log` |
| Full strict Pyright | PASS, zero errors/warnings | `/workspace/qmx-replay-snapshot-types.log` |
| Root Ruff lint | PASS | `/workspace/qmx-replay-snapshot-lint.log` |
| Root Ruff formatting | FAIL, nine source files; corrected later by AST-identical `43bc79f8` | `/workspace/qmx-replay-snapshot-format.log` |
| Money, ambient, fabricated-data and secret static scans | PASS | `/workspace/qmx-replay-snapshot-{money,ambient,mock,secret}-scan.log` |

Source coverage remains incomplete; no thresholds, exclusions or counters were
changed. The per-package gate measured QMB 36,013/47,209, QML 7,788/10,031,
and QMN 37,454/50,111 combined line/branch units. Exact-core contract branch
checks did not report a violation. Passing source tests and static scans do
not establish security completion, provider connectivity or full product
acceptance. Independent review found further QML and node ledger defects in
this intermediate candidate; follow-up source fixes require review and final
same-candidate verification. See `installed-recorded-replay.md` for the
separate reproducible build and actual non-editable economic execution.
