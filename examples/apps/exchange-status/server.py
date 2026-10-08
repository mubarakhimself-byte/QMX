"""Recorded observations only: this example never fabricates live exchange health."""

from __future__ import annotations

import html
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP
from fastmcp.apps import AppConfig
from pydantic import JsonValue

mcp = FastMCP("Exchange status")
VIEW = "ui://exchange-status/view.html"


def observations() -> list[dict[str, JsonValue]]:
    with closing(sqlite3.connect("app.db")) as db, db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS observations "
            "(exchange TEXT PRIMARY KEY, status TEXT NOT NULL, observed_at TEXT NOT NULL)"
        )
        rows = db.execute(
            "SELECT exchange,status,observed_at FROM observations ORDER BY exchange"
        ).fetchall()
    return [{"exchange": row[0], "status": row[1], "observed_at": row[2]} for row in rows]


@mcp.tool()
def record(
    exchange: str,
    status: Literal["operational", "degraded", "unavailable", "unknown"],
    observed_at: str,
) -> dict[str, JsonValue]:
    """Record an explicitly supplied observation, without contacting an exchange."""
    observations()
    with closing(sqlite3.connect("app.db")) as db, db:
        db.execute(
            "INSERT INTO observations VALUES(?,?,?) ON CONFLICT(exchange) "
            "DO UPDATE SET status=excluded.status,observed_at=excluded.observed_at",
            (exchange, status, observed_at),
        )
    return {"recorded": True}


@mcp.tool(app=AppConfig(resource_uri=VIEW))
def snapshot() -> dict[str, JsonValue]:
    """Return a typed snapshot that the supervisor saves as an immutable artifact."""
    return {"output": "snapshot", "data": {"observations": list(observations())}}


@mcp.resource(VIEW)
def view() -> str:
    """Re-read persisted state each time the MCP App panel opens."""
    rows = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(row[key]))}</td>"
            for key in ("exchange", "status", "observed_at")
        )
        + "</tr>"
        for row in observations()
    )
    if not rows:
        rows = '<tr><td colspan="3">No recorded observations.</td></tr>'
    return (
        (Path(__file__).parent / "ui/view.html")
        .read_text(encoding="utf-8")
        .replace("{{rows}}", rows)
    )


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
