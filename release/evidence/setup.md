# Source and early installed execution

Remote inspected: origin https://github.com/MubarakHimself/QMX.git.
`git fetch origin '+refs/heads/*:refs/remotes/origin/*'` PASS.
Current backend a0e8769772e469bf54bd312cc1e27e7995e16c3b,
UI f6ffaddf3f78c6c14d32daa136fadf15e7748c14,
docs c3e8ec5ef33d0b38cdf7f5dbdd48a6fc70ac33cf match audit pins.
Original /workspace/QMX remained clean at work branch; new backend worktree
/workspace/QMX-release on release/rc-2026-10-01. No protected branch changed.

All three uploads downloaded; DOCX extracted once to /workspace/qmx-audit-inputs/audit.txt;
packets and reproductions extracted once into packets/. PDF is the accompanying rendition.
Source authority is the user's task, not attached proposal permissions.

`uv sync --locked` PASS, CPython 3.14.7. Factory dependencies are development only.
`uv build --all-packages --out-dir /workspace/qmx-artifacts-early` PASS 11 root wheels+sdists.
Initial name-based `uv pip install ... qml` selected unrelated PyPI qml 0.4.0.27
and FAILed build without numpy; setup corrected by explicit wheel paths.
`uv pip install --python /workspace/qmx-installed-early/bin/python /workspace/qmx-artifacts-early/*.whl` PASS.
Installed root imports and actual `/workspace/qmx-installed-early/bin/qmb --help` PASS
from /workspace (outside checkout). This first install used resolved registry versions,
not the release runtime lock; final candidate rebuild/install remains required.

UI baseline build first attempted a source archive; git metadata required by its build
caused FAIL. Corrected via registered detached worktree /workspace/QMX-ui-baseline
at f6ffaddf. Declared Node 22.12.0/Pnpm 10.18.3 frozen dependency setup, check,
lint, 46 unit tests and static build PASS. Recording transport remains in baseline;
this does not prove browser-to-daemon execution. No apps/qmx-ui implementation edits.

`python -m pytest tools/tests -q` PASS 551.
`python -m mypy adws` PASS 36 source files.
`python -m pytest adws/tests -q` PASS 4.
These are intermediate candidate checks, not final release certification.

Authority reconciliation: initial combined pytest collection FAILed because two QA
epic suites have the same filename/module; reran the suites independently.
QA epic08 proto checks 11 PASS; epic15 ownership checks 8 PASS; epic16 thin-door checks
7 PASS with a socket-only lifecycle exception negative control. Ratified DEC-0141
scopes protobuf to qmf-venue distribution; DEC-0494 authorizes only QMB host-control
spawn/socket use. Domain HTTP/storage/fingerprint restrictions remain enforced.
QMN containment disclosure suite 9 PASS after restoring deferred GAP-0054 and
compensating-control disclosures in latest-main security, QML and incident docs.
This does not close GAP-0054 or security verification.

Governing corpus correction: commit a14c1213 aligns the complete `_docwork` and
`_bmad-output` roots to published main c3e8ec5, in addition to the `docs` root.
The archived Sept-16 `query_hermes_sessions.py` then exposed four factory lint
findings. Candidate repair removes an unused import, simplifies its guard,
parameterizes search values and correctly escapes schema identifiers. Only a
synthetic temporary SQLite database was opened for a positive ordinary-name
control and an embedded-quote/SQL-text identifier control; both PASS. The
referenced personal Hermes database was not accessed. Architecture prose and
ratification status remain unchanged by this script repair.

Intermediate current checks: `uv run --no-sync ruff check .` PASS;
`uv run --no-sync pyright --pythonpath .venv/bin/python` PASS (0 diagnostics).
Logs `/workspace/qmx-factory-lint-current.log` and
`/workspace/qmx-root-types-current.log`. Concurrent implementation continues;
these are not final same-candidate certification.

Full intermediate source run (`uv run --no-sync poe test`) FAIL: 5313 passed,
7 skipped, 10 failed in 310.55s. Six failures were invalid config fixtures,
corrected in ad36bb6b (independent Sol diff approval, unchanged assertions;
49 affected tests PASS). Remaining failing examples/vocabulary are owned by
execution; clock-boundary test is owned by node. Aggregate coverage FAIL
78.45%; per-package FAIL QMB 76.94%, QML 76.97%, QMN 74.07%. Mutable/untracked
Book handler also triggered tracked-inventory refusal, as expected for this
intermediate run. No floors lowered. Logs `/workspace/qmx-full-source-test-current.log`
and `/workspace/qmx-perpackage-source-current.log`.

Independent QA runner FAIL in epic11/12/13/15/18. Epic12's historical Silent
substitution fixture was replaced with a real manifest-bound source factory
in 86dc5a27; 73 tests PASS. Epic15's two fake config identities were made
canonical in the same commit; 50 tests PASS. Assertions and failure controls
remain unchanged. Directly linting excluded QA files reported pre-existing
QA lint findings; ordinary factory scope remains the required lint lane.
Epic11 still refuses unratified extra QML homes; epic13 owned source vocabulary/
types fixes and epic18 durable QMF intake authority implementation continue.
This is not a final whole-run PASS. Logs `/workspace/qmx-qa-current.log`,
`/workspace/qmx-qa12-corrected.log`, `/workspace/qmx-qa15-corrected.log`.

Factory/tool lanes after wire/example changes: `uv run --no-sync poe test-tools`
PASS 563 tests with 98.48% coverage over its declared factory scanner/helper
modules; `uv run --no-sync mypy adws` PASS 36 source files;
`uv run --no-sync pytest -q adws/tests` PASS 4 tests. Logs
`/workspace/qmx-tools-source-coverage-current.log`,
`/workspace/qmx-factory-mypy-current.log`, `/workspace/qmx-factory-tests-current.log`.
These checks do not certify continuing product edits or close product coverage.
