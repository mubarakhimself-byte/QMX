"""An actual subprocess app used to exercise the host boundary."""

from __future__ import annotations

import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from fastmcp import FastMCP
from pydantic import JsonValue

mcp = FastMCP("Supervisor boundary fixture")


@mcp.tool()
def ping() -> dict[str, JsonValue]:
    return {"pong": True}


@mcp.tool()
def environment() -> dict[str, JsonValue]:
    return {
        "declared_matches": os.environ.get("DECLARED_SECRET") == "declared-fixture",
        "undeclared_present": "QMX_UNDECLARED_SECRET" in os.environ,
        "cwd": str(Path.cwd()),
        "home": os.environ.get("USERPROFILE"),
        "pythonpath_present": "PYTHONPATH" in os.environ,
    }


@mcp.tool()
def write(path: str) -> dict[str, JsonValue]:
    Path(path).write_text("probe", encoding="utf-8")
    return {"written": True}


@mcp.tool()
def write_database(path: str) -> dict[str, JsonValue]:
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("CREATE TABLE probe (id INTEGER)")
    return {"written": True}


@mcp.tool()
def print_secret() -> dict[str, JsonValue]:
    print(os.environ.get("DECLARED_SECRET", ""), file=sys.stderr)
    return {"printed": True}


@mcp.tool()
def freeze_heartbeat() -> dict[str, JsonValue]:
    for path in Path("data").glob("heartbeat-*.json"):
        path.unlink()
        path.mkdir()
    return {"frozen": True}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
