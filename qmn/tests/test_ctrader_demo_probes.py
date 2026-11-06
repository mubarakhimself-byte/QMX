"""The cTrader demo probes' rehearsal (R24, C-15, `EXTERNAL.md` section 2).

`run.py --rehearsal` runs every mark over the real node code and the fake broker, one PASS line
each. `--fault <mark>` runs the same crossing with that mark's fault in, and must read FAIL. The
marks also run one after another over a single rig, as the demo run has one account for all six.
No network, no account and no grant is reached: the marks' demo half waits for G-DEMO.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROBES = Path(__file__).resolve().parents[1] / "probes" / "ctrader_demo"
MARKS = (
    "label_survives",
    "partial_keeps_label",
    "repeated_client_order_id",
    "attribution",
    "network_cut",
    "refresh",
)


def probe(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PROBES / "run.py"), *args],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )


def verdicts(done: subprocess.CompletedProcess[str]) -> list[str]:
    return [line[:4] for line in done.stdout.splitlines() if line.startswith(("PASS ", "FAIL "))]


def test_each_mark_passes_in_rehearsal_and_fails_when_its_fault_is_injected() -> None:
    rehearsal = probe("--rehearsal")
    assert rehearsal.returncode == 0, rehearsal.stdout + rehearsal.stderr
    assert verdicts(rehearsal) == ["PASS"] * len(MARKS), rehearsal.stdout
    assert [
        line.split()[1] for line in rehearsal.stdout.splitlines() if line.startswith("PASS ")
    ] == list(MARKS)

    for name in MARKS:
        fault = probe("--rehearsal", "--fault", name)
        assert fault.returncode == 1, (name, fault.stdout + fault.stderr)
        assert verdicts(fault) == ["FAIL"], (name, fault.stdout + fault.stderr)
        assert fault.stdout.split()[1] == name, fault.stdout


def test_the_marks_share_one_session_and_leave_nothing_open() -> None:
    shared = probe("--rehearsal", "--shared")
    assert shared.returncode == 0, shared.stdout + shared.stderr
    assert verdicts(shared) == ["PASS"] * len(MARKS), shared.stdout
    assert [
        line.split()[1] for line in shared.stdout.splitlines() if line.startswith("PASS ")
    ] == list(MARKS)
