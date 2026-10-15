"""S35u, an external MCP tool runs unasked only when the operator allow-listed it. A stdio
server `weather` exposes `get_weather`, which writes a marker file when it runs. Three key chats
on the fake model each make one `mcp__weather__get_weather` call through the real CLI:

- bypass, `[claude] external_tools_unattended` empty: PASS when the gate denies the call
  naming the allow-list, and the marker stays absent.
- bypass, the list holds `weather/get_weather`: PASS when the call runs and the marker exists.
- default mode, the list empty: PASS when the gate lets the CLI ask (the hook input carries the
  mode), the operator's reject through `POST /api/approvals` resolves the ask, and the marker
  stays absent.

    s35u_unattended_external.py
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from approval_lane import Answerer, Host, always, answered_turn, reject
from common import (
    SCRATCH,
    Log,
    Session,
    boot,
    put_providers,
    session_blocks,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from fake_model import FakeModel
from money_lane import Call, Outcome, direct_row, fake_for, outcome_of, results, run_calls

WEATHER = """\
import pathlib, sys
from fastmcp import FastMCP
marker = pathlib.Path(sys.argv[1])
server = FastMCP("weather")
@server.tool
def get_weather(city: str = "x") -> str:
    \"\"\"The weather in a city.\"\"\"
    marker.write_text(city)
    return "sunny"
server.run()
"""

CALL = Call("weather call", "mcp__weather__get_weather", {"city": "Paris"})
LANES: list[tuple[str, str, list[str], str]] = [
    ("bypass, not allow-listed", "bypassPermissions", [], "hook"),
    ("bypass, allow-listed", "bypassPermissions", ["weather/get_weather"], "ran"),
    ("default, not allow-listed", "default", [], "asked"),
]


async def rejected_by_operator(
    log: Log, root: Any, title: str
) -> tuple[Session, FakeModel, dict[str, tuple[Outcome, str]], Answerer]:
    """`run_calls` in default mode, with each ask rejected through the approvals route."""
    from qma.harness import TestMode  # noqa: PLC0415

    fake = fake_for([CALL], in_agent=False).start()
    put_providers(root, {"fake": direct_row(fake.url)})
    session = await Session.start(
        root,
        model="opus",
        workspace=SCRATCH / "workspace",
        title=title,
        test=TestMode(loopback_http_provider=True),
        profile="fake",
        mode="default",
        tools=["Read"],
    )
    async with Host(session) as host:
        answerer = await answered_turn(
            log, host, session.chat, always(reject("s35u: no")), "Run the scripted checks."
        )
    outcomes = {CALL.label: outcome_of(CALL, results(fake))}
    return session, fake, outcomes, answerer


async def lane(log: Log, label: str, mode: str, allowed: list[str], want: str) -> None:
    from qma.harness import QmxHome, TestMode  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    slug = label.replace(",", "").replace(" ", "-")
    root = throwaway_home(f"hp8-s35u-{slug}")
    servers = SCRATCH / "hp8-s35u-servers"
    servers.mkdir(parents=True, exist_ok=True)
    script, marker = servers / "weather.py", servers / f"ran-{slug}.txt"
    script.write_text(WEATHER, encoding="utf-8")
    marker.unlink(missing_ok=True)
    control = control_service(QmxHome(root))
    control.settings_put(
        "mcp_servers", {"weather": {"command": sys.executable, "args": [str(script), str(marker)]}}
    )
    control.settings_put("claude", {"external_tools_unattended": allowed})
    log(f"lane {label}: mode {mode}, allow-list {allowed}")
    answerer = None
    if want == "asked":
        session, fake, outcomes, answerer = await rejected_by_operator(log, root, f"s35u {label}")
    else:
        session, fake, outcomes = await run_calls(
            log,
            root,
            [CALL],
            test=TestMode(loopback_http_provider=True),
            mode=mode,
            tools=["Read"],
            title=f"s35u {label}",
        )
    try:
        kind, said = outcomes[CALL.label]
        ran = marker.exists()
        offered = sorted(
            {
                tool["name"]
                for seen in fake.requests
                for tool in seen.json.get("tools", [])
                if "weather" in tool["name"]
            }
        )
        log.check(f"{label}: the model is offered the weather tool", offered != [], offered)
        match want:
            case "hook":
                log.check(
                    f"{label}: the gate denies it naming the allow-list",
                    kind == "hook" and "external_tools_unattended" in said and not ran,
                    (kind, said[:160], ran),
                )
            case "ran":
                log.check(f"{label}: the tool runs", kind == "ran" and ran, (kind, said[:160], ran))
            case _:
                permissions: list[Any] = [
                    block["content"]
                    for block in session_blocks(session.control, session.chat)
                    if block["type"] == "permission"
                ]
                answers = [(a.tool, a.status) for a in answerer.answered] if answerer else []
                log.check(
                    f"{label}: the gate passes and the operator's reject resolves the CLI's ask",
                    kind != "hook" and bool(answers) and not ran,
                    (kind, said[:160], ran, answers, permissions),
                )
    finally:
        await session.harness.close()
        fake.stop()
        marker.unlink(missing_ok=True)


async def run(log: Log) -> None:
    for label, mode, allowed, want in LANES:
        await lane(log, label, mode, allowed, want)


def main() -> int:
    log = Log("hp8-s35u")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
