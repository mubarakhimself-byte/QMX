"""The variant tester's one operation, so the supervisor has a process to keep running."""

from __future__ import annotations

from fastmcp import FastMCP
from pydantic import JsonValue

mcp = FastMCP("QMB, money cut down to the cent")


@mcp.tool()
def capabilities() -> dict[str, JsonValue]:
    """The tester's contract and run kinds."""
    return {"contract": "qmb/1", "run_kinds": ["backtest", "conformance"]}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
