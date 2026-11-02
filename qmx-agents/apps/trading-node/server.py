"""The trading node's MCP entry: every operation of `qmn.app` served as one tool.

Each tool hands its raw arguments to `Node.call`, which answers every call and never raises, so
a bad argument is an answer `ok = false` and never a tool error that counts toward the
supervisor's breaker. The tools declare an open input schema for the same reason: FastMCP would
otherwise refuse a mistyped argument before the node could answer it. The node declares no job.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import FastMCP
from fastmcp.tools import Tool, ToolResult
from qmn.app.server import OPERATIONS, from_environment

node = from_environment()
mcp = FastMCP("Trading node")


class NodeOperation(Tool):
    """One node operation; the node itself checks the arguments."""

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        answer = await asyncio.to_thread(node.call, self.name, arguments)
        return ToolResult(structured_content=answer)


for operation in OPERATIONS:
    mcp.add_tool(NodeOperation(name=operation, parameters={"type": "object"}))


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
