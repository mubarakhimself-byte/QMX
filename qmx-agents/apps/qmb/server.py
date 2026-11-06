"""QMB's two quick operations (Part B AD-201, CONTRACTS §1): what this tester can replay.

Runs, status, results and comparisons are never QMB operations: runs are jobs, and the rest are
the core's `backtest` rows over the core's records, so a tester never reports its own score.

QMB lowers its own process priority when it starts (QB-17, LC-B-16). Its jobs run in this same
process, so a long backtest never takes the CPU from a trading node or the host on This PC.
"""

from __future__ import annotations

import ctypes
import json
import os
import sys
from typing import Final

from fastmcp import FastMCP
from pydantic import JsonValue
from qmb.analysis.whatif import SCENARIOS

import qmb_tester as tester

PROCESS_PRIORITY: Final = "below_normal"
"""`[qmb] process_priority`: the class QMB runs at, below the live paths beside it."""
_WINDOWS_CLASS: Final = {"normal": 0x20, "below_normal": 0x4000, "idle": 0x40}
_NICENESS: Final = {"normal": 0, "below_normal": 10, "idle": 19}


def lower_priority(level: str = PROCESS_PRIORITY) -> None:
    """Set this process to ``level``; a machine that refuses says so on the app's log."""
    if sys.platform == "win32":
        from ctypes import wintypes  # noqa: PLC0415 - Windows only

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.SetPriorityClass.restype = wintypes.BOOL
        if kernel.SetPriorityClass(kernel.GetCurrentProcess(), _WINDOWS_CLASS[level]):
            return
        error = str(ctypes.WinError(ctypes.get_last_error()))
    else:
        try:
            os.nice(max(0, _NICENESS[level] - os.nice(0)))
            return
        except OSError as raised:
            error = str(raised)
    print(
        json.dumps({"event": "priority_refused", "level": level, "error": error}), file=sys.stderr
    )


lower_priority()

mcp = FastMCP("QMB")

RUN_KINDS = [
    "backtest",
    "behaviour_check",
    "conformance",
    "sweep",
    "walk_forward",
    "robustness",
    "optimize",
    "whatif",
    "replay_check",
]
FIDELITIES = ["quotes"]
INSTRUMENT_CLASSES = ["fx", "metal"]


@mcp.tool()
def capabilities() -> dict[str, JsonValue]:
    """The tester's `qmx.qmb.capabilities/1`."""
    return {
        "schema_version": 1,
        "contract": tester.CONTRACT,
        "tester": {"app": tester.TESTER["app"], "version": tester.TESTER["version"]},
        "run_kinds": list(RUN_KINDS),
        "fidelities": list(FIDELITIES),
        "fill_models": ["next_open_gap"],
        "cost_adapters": ["cost_profile"],
        "carry_adapters": ["swap", "financing", "funding", "dividend"],
        "margin_models": ["isolated_maintenance"],
        "instrument_classes": list(INSTRUMENT_CLASSES),
        "whatif_scenarios": [
            {"name": name, "direction": scenario.direction} for name, scenario in SCENARIOS.items()
        ],
    }


@mcp.tool()
def instruments() -> dict[str, JsonValue]:
    """The instrument classes and fidelities this tester replays; it reads no Library."""
    return {"instrument_classes": list(INSTRUMENT_CLASSES), "fidelities": list(FIDELITIES)}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
