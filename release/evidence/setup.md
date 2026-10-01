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
