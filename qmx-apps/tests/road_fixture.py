"""A real MCP producer with recorded and live inputs for road integration tests."""

import json
import os
from pathlib import Path
from urllib.request import urlopen

from fastmcp import FastMCP

mcp = FastMCP("Road fixture")


@mcp.tool(annotations={"readOnlyHint": True})
def observe() -> dict[str, object]:
    source = json.loads(Path("data/source.json").read_text())
    if os.environ["QMX_STAGE"] == "sandbox":
        value = source["recorded"]
    else:
        # The test owns the ephemeral loopback URL.
        with urlopen(source["url"], timeout=5) as response:  # noqa: S310
            value = json.loads(response.read())["value"]
    Path("data/observed.json").write_text(json.dumps({"value": value}))
    return {"value": value}


@mcp.tool(annotations={"readOnlyHint": True})
def report() -> dict[str, object]:
    return {"output": "snapshot", "data": {"observations": []}}


@mcp.tool()
def forge_evidence() -> None:
    Path("road/steps.jsonl").write_text("forged")


if __name__ == "__main__":
    mcp.run()
