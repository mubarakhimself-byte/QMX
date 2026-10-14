"""S35, an external money MCP server never launches. settings.toml [mcp_servers] declares two
stdio servers: `broker_x`, which exposes `submit_order`, and `weather`, which exposes
`get_weather` as the control. A key chat on the fake model starts and runs one turn.

PASS when `broker_x` is refused at vetting with a `needs_you` block naming it, it is absent
from the launch's `mcp_servers` and from `get_mcp_status()` before the first prompt, and
`weather` is admitted and listed. The in-process `qmx` server is served by the SDK, and the
CLI's status does not list it (measured), so the model's tool list shows it instead.

    s35_external_mcp.py
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from common import (
    SCRATCH,
    Log,
    Session,
    boot,
    capture_launches,
    session_blocks,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from fake_model import FakeModel, Turn, text
from money_lane import direct_row

SERVER = """\
from fastmcp import FastMCP
server = FastMCP("{name}")
@server.tool
def {tool}(x: int = 0) -> int:
    \"\"\"Example tool.\"\"\"
    return x
server.run()
"""


def statuses() -> list[Any]:
    """Every `get_mcp_status()` answer from now on, in order."""
    import qma.harness.chat as chat_module  # noqa: PLC0415

    seen: list[Any] = []
    base = chat_module.ClaudeSDKClient

    class Recorded(base):
        async def get_mcp_status(self) -> Any:
            found = await super().get_mcp_status()
            seen.append(found)
            return found

    chat_module.ClaudeSDKClient = Recorded
    return seen


async def run(log: Log) -> None:
    from qma.harness import TestMode  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    root = throwaway_home("hp8-s35")
    servers = SCRATCH / "hp8-s35-servers"
    servers.mkdir(parents=True, exist_ok=True)
    rows: dict[str, Any] = {}
    for name, tool in (("broker_x", "submit_order"), ("weather", "get_weather")):
        script = servers / f"{name}.py"
        script.write_text(SERVER.format(name=name, tool=tool), encoding="utf-8")
        rows[name] = {"command": sys.executable, "args": [str(script)]}
    fake = FakeModel([Turn([text("hello")])]).start()
    from qma.harness import QmxHome  # noqa: PLC0415

    control = control_service(QmxHome(root))
    control.settings_put("providers", {"fake": direct_row(fake.url)})
    control.settings_put("mcp_servers", rows)
    launches = capture_launches()
    seen = statuses()
    session = await Session.start(
        root,
        model="opus",
        workspace=SCRATCH / "workspace",
        title="s35",
        test=TestMode(loopback_http_provider=True),
        profile="fake",
        mode="default",
    )
    try:
        await session.turn(log, "Say hello.")
        blocks = session_blocks(session.control, session.chat)
        refusals = [
            str(block["content"].get("reason", ""))
            for block in blocks
            if block["type"] == "needs_you"
        ]
        log.check(
            "broker_x refused at vetting with a needs_you block",
            any("broker_x" in reason and "submit_order" in reason for reason in refusals),
            refusals,
        )
        configured = sorted(launches[-1].options.mcp_servers)
        log.check("broker_x absent from mcp_servers", configured == ["qmx", "weather"], configured)
        first = sorted(server["name"] for server in seen[0]["mcpServers"]) if seen else None
        log.check(
            "get_mcp_status before the first prompt lists weather and not broker_x",
            first is not None and "weather" in first and "broker_x" not in first,
            first,
        )
        tools = [
            tool["name"]
            for seen_request in fake.requests
            for tool in seen_request.json.get("tools", [])
            if "weather" in tool["name"] or "order" in tool["name"]
        ]
        log.check(
            "the model is offered get_weather and no submit_order",
            "mcp__weather__get_weather" in tools and not any("submit" in t for t in tools),
            sorted(set(tools)),
        )
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp8-s35")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
