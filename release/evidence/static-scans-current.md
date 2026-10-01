# Intermediate static scans

2026-10-01, release worktree after `44ddcc3a`, with active uncommitted Book/replay/optimization repairs. These are intermediate source checks, not final candidate attestations.

Each command exited 0:

- `.venv/bin/python tools/money_path_scan.py`: `/workspace/qmx-money_path_scan-current.log`
- `.venv/bin/python tools/ambient_scan.py`: `/workspace/qmx-ambient_scan-current.log`
- `.venv/bin/python tools/mock_data_scan.py`: `/workspace/qmx-mock_data_scan-current.log`
- `.venv/bin/python tools/secret_scan.py`: `/workspace/qmx-secret_scan-current.log`

A clean static secret scan does not complete security verification. Final immutable candidate gates and independent review remain pending.
