"""Summarise a supervisor-verified exchange snapshot as a recorded-data summary artifact.

The snapshot arrives as the `snapshot` feed: the supervisor checks the producer's artifact
against this app's feed schema and copies it into this volume before the call. The summary is
written from those observations alone, so it never claims live availability.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from fastmcp import FastMCP
from pydantic import JsonValue

mcp = FastMCP("Weekend watcher")


def summary(observations: list[dict[str, str]]) -> str:
    lines = [f"{row['exchange']}: {row['status']} ({row['observed_at']})" for row in observations]
    return "Recorded-data fixture: " + ("; ".join(lines) or "no observations.")


@mcp.tool()
def summarize(snapshot: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Summarise a supervisor-verified snapshot reference and emit a summary artifact."""
    payload = json.loads(Path(cast(str, snapshot["path"])).read_text(encoding="utf-8"))
    return {
        "output": "summary",
        "data": {
            "summary": summary(payload["observations"]),
            "source_sha256": snapshot["sha256"],
            "mode": "recorded_fixture",
        },
    }


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
