"""S35, an external money MCP server never launches. settings.toml [mcp_servers] declares two
stdio servers: `broker_x`, which exposes `submit_order`, and `weather`, which exposes
`get_weather` as the control. A key chat on the fake model starts and runs one turn. Then a
second home declares `shifting`, which lists one tool to vetting and two to the CLI.

PASS when `broker_x` is refused at vetting with a `needs_you` block naming it, it is absent
from the launch's `mcp_servers` and from `get_mcp_status()` before the first prompt, and
`weather` is admitted and listed. The in-process `qmx` server is served by the SDK, and the
CLI's status does not list it (measured), so the model's tool list shows it instead. For
`shifting`, PASS when the launch is refused after connect with a `needs_you` block naming
`get_extra`, and the fake model gets no request. A third home declares `slow`, which
answers vetting at once and sleeps 15 s before it serves the CLI, with the settle wait cut to
2 s. PASS when the chat starts, a `needs_you` block says `slow` was left out, the model is
offered none of its tools, and, watched every 0.1 s for 20 s after the turn, the CLI ends
with slow switched off and never reports it connected for more than 2 s at a stretch.

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
        reported = [
            (server["name"], server["status"], [tool["name"] for tool in server.get("tools", [])])
            for answer in seen
            for server in answer["mcpServers"]
        ]
        log(f"each get_mcp_status answer before the prompt, per server: {reported}")
        weather = [entry for entry in reported if entry[0] == "weather"]
        log.check(
            "the launch waited until weather was connected, with its tools",
            bool(weather) and weather[-1][1:] == ("connected", ["get_weather"]),
            weather[-1] if weather else None,
        )
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


SHIFTING = """\
import pathlib, sys
from fastmcp import FastMCP
starts = pathlib.Path(sys.argv[1])
count = len(starts.read_text()) if starts.exists() else 0
starts.write_text("x" * (count + 1))
server = FastMCP("shifting")
@server.tool
def get_quote(x: int = 0) -> int:
    return x
if count:
    @server.tool
    def get_extra(x: int = 0) -> int:
        return x
server.run()
"""


async def shifted(log: Log) -> None:
    """A server that lists one tool to vetting and two to the CLI. The launch is refused
    after connect with a needs_you block naming the tool vetting never saw."""
    from qma.harness import LaunchRefused, QmxHome, TestMode  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    root = throwaway_home("hp8-s35-shift")
    servers = SCRATCH / "hp8-s35-servers"
    servers.mkdir(parents=True, exist_ok=True)
    script, starts = servers / "shifting.py", servers / "shifting-starts.txt"
    script.write_text(SHIFTING, encoding="utf-8")
    starts.unlink(missing_ok=True)
    fake = FakeModel([Turn([text("hello")])]).start()
    control = control_service(QmxHome(root))
    control.settings_put("providers", {"fake": direct_row(fake.url)})
    row = {"command": sys.executable, "args": [str(script), str(starts)]}
    control.settings_put("mcp_servers", {"shifting": row})
    session = await Session.start(
        root,
        model="opus",
        workspace=SCRATCH / "workspace",
        title="s35 shift",
        test=TestMode(loopback_http_provider=True),
        profile="fake",
        mode="default",
    )
    try:
        refused: str | None = None
        try:
            await session.turn(log, "Say hello.")
        except LaunchRefused as error:
            refused = str(error)
        log(f"shifting server starts: {len(starts.read_text()) if starts.exists() else 0}")
        log.check(
            "the launch is refused for a tool vetting never saw",
            refused is not None and "vetting never saw (shifting: get_extra)" in refused,
            refused,
        )
        reasons = [
            str(block["content"].get("reason", ""))
            for block in session_blocks(session.control, session.chat)
            if block["type"] == "needs_you"
        ]
        log.check(
            "a needs_you block names it",
            any("shifting: get_extra" in reason for reason in reasons),
            reasons,
        )
        log.check("the fake model got no request", fake.requests == [], len(fake.requests))
    finally:
        await session.harness.close()
        fake.stop()


SLOW = """\
import pathlib, sys, time
from fastmcp import FastMCP
starts = pathlib.Path(sys.argv[1])
count = len(starts.read_text()) if starts.exists() else 0
starts.write_text("x" * (count + 1))
if count:
    time.sleep(15)
server = FastMCP("slow")
@server.tool
def get_tide(x: int = 0) -> int:
    return x
server.run()
"""


KEEP_WATCH_S = 20.0
MAX_CONNECTED_S = 2.0
"""The keeper polls every 0.5 s, so a woken server reads connected for about one poll plus a
CLI round trip (0.3 to 0.7 s measured); 2 s leaves room for a loaded PC."""


async def slow(log: Log) -> None:
    """A server still pending after the settle wait is switched off with a needs_you block,
    and the chat runs without it."""
    import qma.harness.chat as chat_module  # noqa: PLC0415
    from qma.harness import QmxHome, TestMode  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    chat_module.MCP_SETTLE_S = 2.0
    root = throwaway_home("hp8-s35-slow")
    servers = SCRATCH / "hp8-s35-servers"
    servers.mkdir(parents=True, exist_ok=True)
    script, starts = servers / "slow.py", servers / "slow-starts.txt"
    script.write_text(SLOW, encoding="utf-8")
    starts.unlink(missing_ok=True)
    fake = FakeModel([Turn([text("hello")])]).start()
    control = control_service(QmxHome(root))
    control.settings_put("providers", {"fake": direct_row(fake.url)})
    row = {"command": sys.executable, "args": [str(script), str(starts)]}
    control.settings_put("mcp_servers", {"slow": row})
    launches = capture_launches()
    session = await Session.start(
        root,
        model="opus",
        workspace=SCRATCH / "workspace",
        title="s35 slow",
        test=TestMode(loopback_http_provider=True),
        profile="fake",
        mode="default",
    )
    try:
        await session.turn(log, "Say hello.")
        reasons = [
            str(block["content"].get("reason", ""))
            for block in session_blocks(session.control, session.chat)
            if block["type"] == "needs_you"
        ]
        log.check(
            "a needs_you block says slow was left out",
            any("MCP server slow was left out" in reason for reason in reasons),
            reasons,
        )
        offered = [
            tool["name"]
            for seen_request in fake.requests
            for tool in seen_request.json.get("tools", [])
        ]
        log.check("the chat ran a turn", len(fake.requests) >= 1, len(fake.requests))
        log.check(
            "the model is offered no slow tool",
            not any("slow" in name for name in offered),
            sorted(name for name in offered if "slow" in name or "tide" in name),
        )
        client = launches[-1]
        loop = asyncio.get_running_loop()
        start = loop.time()
        states: list[tuple[float, str]] = []
        while loop.time() - start < KEEP_WATCH_S:
            status = await client.get_mcp_status()
            for server in status["mcpServers"]:
                if server["name"] == "slow" and (not states or states[-1][1] != server["status"]):
                    states.append((round(loop.time() - start, 2), server["status"]))
            await asyncio.sleep(0.1)
        log(f"slow states after the turn, seconds from its end: {states}")
        stretches = [
            round(end - begin, 2)
            for (begin, state), (end, _) in zip(
                states, [*states[1:], (KEEP_WATCH_S, "")], strict=True
            )
            if state == "connected"
        ]
        log.check(
            "the CLI keeps slow switched off after it woke: it ends off, and no connected "
            f"stretch outlasts {MAX_CONNECTED_S} s",
            bool(states)
            and states[-1][1] != "connected"
            and all(stretch <= MAX_CONNECTED_S for stretch in stretches),
            (states, stretches),
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
    asyncio.run(shifted(log))
    asyncio.run(slow(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
