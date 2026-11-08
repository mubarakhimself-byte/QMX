"""The MIS's MCP entry: `configure`, `status`, `round` and `board`, and a round every `round_s`.

Each tool hands its raw arguments to `Mis.call`, which answers every call, so a bad argument is
an answer `ok = false` and never a tool error that counts toward the supervisor's breaker. The
tools declare an open input schema for the same reason. `status` and `board` are marked
read-only, which is what lets the road's shadow stage call them.

The rounds run on a thread of this process once a configuration exists. The supervisor's
breaker restarts the app by back-off after a crash; the journal tells the new process what was
already published.
"""

from __future__ import annotations

import asyncio
import os
import threading
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.tools import Tool, ToolResult
from mcp_types import ToolAnnotations

from mis_core import OPERATIONS, READS, SETTINGS, Mis

market_root = os.environ.get("QMX_MARKET_ROOT")
mis = Mis(
    Path(os.environ["QMX_VOLUME"]),
    None if market_root is None else Path(market_root),
    clock=time.time_ns,
    boot=str(time.time_ns()),
)
mcp = FastMCP("MIS")
stopping = threading.Event()


class MisOperation(Tool):
    """One MIS operation; the MIS itself checks the arguments."""

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        answer = await asyncio.to_thread(mis.call, self.name, arguments)
        return ToolResult(structured_content=answer)


for operation in OPERATIONS:
    mcp.add_tool(
        MisOperation(
            name=operation,
            parameters={"type": "object"},
            annotations=ToolAnnotations(read_only_hint=operation in READS),
        )
    )


def rounds() -> None:
    while True:
        current = mis.plan
        wait = SETTINGS["round_s"] if current is None else current.settings["round_s"]
        if stopping.wait(wait):
            return
        if mis.plan is not None:
            mis.call("round", {})


if __name__ == "__main__":
    threading.Thread(target=rounds, name="mis-rounds", daemon=True).start()
    try:
        mcp.run(transport="stdio", show_banner=False)
    finally:
        stopping.set()
        mis.close()
