# Installed recorded replay, intermediate immutable candidate

Candidate: `1c4c73b1e51e9194464601830e7543ecd1108b6d`.
Host: Debian 13 x86-64, CPython 3.14.7. This is intermediate execution
and packaging evidence, not final full-product acceptance.

| Check | Result | Command or evidence |
| --- | --- | --- |
| Immutable registered worktree build, 38 artifacts | PASS | `python tools/build_release.py /workspace/qmx-bundle-replay-candidate`; `/workspace/qmx-replay-build.log` |
| Independent repeat build, all 38 artifacts plus acceptance inventory byte identical | PASS | `/workspace/qmx-replay-build-repeat.log`; `/workspace/qmx-reproducibility-replay.json` |
| Installer rejects unsupported default CPython 3.12 before installation | PASS negative control | `/workspace/qmx-replay-install.log` |
| CPython 3.14 hash-locked installation of all 14 non-editable product wheels, pip dependency check | PASS | `/workspace/QMX-release/.venv/bin/python /workspace/qmx-bundle-replay-candidate/install.py /workspace/qmx-installed-replay-candidate`; `/workspace/qmx-replay-install-python314.log` |
| Actual installed QMB child `backtest run`, trusted context and persisted CT-06 Bot/Book/BMS, CT-10/12 request | PASS | `/workspace/qmx-installed-replay-smoke.py`; `/workspace/qmx-installed-replay-smoke.log` |
| Installed-package durable confirmation-ledger reopen and exact economic assertions | PASS | `/workspace/qmx-installed-replay-candidate/venv/bin/python /workspace/qmx-installed-replay-readback.py`; `/workspace/qmx-installed-replay-economic-readback.log` |
| Full source/type/coverage/release acceptance of final candidate | NOT RUN here | Separate gates, same final candidate required |

The fixture driver uses frozen-snapshot test helpers to construct recorded
inputs and operator configuration. It passes no checkout import path or test
helper to the child. The actual child is
`/workspace/qmx-installed-replay-candidate/venv/bin/qmb`, runs from `/workspace`,
and imports installed QMB/QML/QMN modules from that installation's site-packages;
module paths are recorded. The durable ledger is subsequently reopened in a
separate process using that installation's Python and product packages.

The selected bot emits entry, Book closes the actual fill, and the persisted
CT-32 fingerprint matches the terminal LedgerLine. Assertions verify one
trade, USD 2 fees, USD -106 net profit, USD 10,000 starting equity and USD 9,894
ending equity. State remains at `/workspace/qmx-installed-replay-evidence`.

Recorded quotes, a no-rollover calendar and named ZERO slippage are explicit
fixture conditions. This does not prove external provider connectivity,
live trading, actual QMA worker routing, browser journeys, full ATC,
Windows installation, Ubuntu installation or complete security verification.
Independent review found additional callback-evidence and virtual-ledger
receipt holes in this intermediate snapshot. Their repairs and independent
rechecks must be included in the final candidate; successful installed replay
does not override those blockers.
