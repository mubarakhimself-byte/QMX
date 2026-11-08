"""QMB's two quick operations (Part B AD-201, CONTRACTS §1): what this tester can replay.

Runs, status, results and comparisons are never QMB operations: runs are jobs, and the rest are
the core's `backtest` rows over the core's records, so a tester never reports its own score.
"""

from __future__ import annotations

from fastmcp import FastMCP
from pydantic import JsonValue

import qmb_tester as tester

mcp = FastMCP("QMB")

RUN_KINDS = ["backtest", "behaviour_check", "conformance"]
FIDELITIES = ["bars"]
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
        "fill_models": ["next_open"],
        "cost_adapters": [],
        "carry_adapters": [],
        "margin_models": [],
        "instrument_classes": list(INSTRUMENT_CLASSES),
        "whatif_scenarios": [],
    }


@mcp.tool()
def instruments() -> dict[str, JsonValue]:
    """The instrument classes and fidelities this tester replays; it reads no Library."""
    return {"instrument_classes": list(INSTRUMENT_CLASSES), "fidelities": list(FIDELITIES)}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
