"""Headless research app: scheduled work with read-only MCP inspection."""

import json
import os
from pathlib import Path
from typing import Any

from collector import RUN_LOCK, Store
from fastmcp import FastMCP

store = Store(Path(os.environ["QMX_VOLUME"]))
mcp = FastMCP("mql5-articles")


@mcp.tool(annotations={"readOnlyHint": True})
def status() -> dict[str, int]:
    """Count seeded, available and unpublished articles without making web requests."""
    return store.status()


@mcp.tool
def seed_library(limit: int = 500) -> dict[str, int]:
    """Import the old archive from this instance's data/seed directory, offline."""
    if not 1 <= limit <= 1000:
        raise ValueError("Use a limit between 1 and 1000.")
    if not RUN_LOCK.acquire(blocking=False):
        raise RuntimeError("Article work is already running.")
    try:
        return {"imported": store.seed(limit), **store.status()}
    finally:
        RUN_LOCK.release()


@mcp.tool(annotations={"readOnlyHint": True})
def article(article_id: int) -> dict[str, Any]:
    """Read a locally available article; never fetch a missing article."""
    with store.db() as db:
        row = db.execute(
            "SELECT metadata,markdown FROM articles WHERE id=?", (article_id,)
        ).fetchone()
    if row is None or not row["markdown"]:
        return {"available": False}
    return {
        "available": True,
        "metadata": json.loads(row["metadata"]),
        "markdown": (store.root / row["markdown"]).read_text(encoding="utf-8"),
    }


if __name__ == "__main__":
    mcp.run()
