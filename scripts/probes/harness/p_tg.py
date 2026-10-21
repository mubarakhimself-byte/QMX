"""P-TG (H47 fallback, run only when P-PK fails both ways). One in-process server per toolset,
switched with `toggle_mcp_server`, with the review 48 cases.

Chat 1 on workspace W launches with `qmx` (tool `core_ping`) and `pack_x` (tool `x_ping`), and
switches `pack_x` off at once, while it is still connecting: the server is "registered off".

- off holds: the switch-off sent during connect holds (status `disabled`, `x_ping` not
  offered on the first request).
- on answers: toggled on mid-session, `x_ping` answers on the next request.
- off fails: toggled off again, a call to `x_ping` fails (the model is not offered it).
- second chat: with `pack_x` left off in chat 1, a second chat on W reports it `connected`.
- resume: a relaunch of chat 1 by resume reports it `connected`.
- forty: a launch with 40 in-process servers settles (every one `connected`) within 10 s.

PASS when every case holds. Fail: pack tools join at the next turn by resume.

    <venv>/Scripts/python.exe p_tg.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from typing import Any, Final

from common import (
    PLAN_MODEL,
    Case,
    Log,
    QmxServer,
    Verdict,
    answers,
    fresh,
    lane_lock,
    plan_env,
    scrub_process_env,
    ship_settings_hash,
    turn,
)

FALLBACK: Final = "pack tools join at the next turn by resume"
SETTLE_S: Final = 10.0
SERVERS_AT_LAUNCH: Final = 40
CALL: Final = (
    "Call the tool mcp__pack_x__x_ping once with no arguments and reply with exactly the text it "
    "returned. If no tool of that name is offered to you, reply with NO-TOOL and call nothing."
)


async def statuses(client: Any) -> dict[str, str]:
    status = await client.get_mcp_status()
    return {str(s.get("name")): str(s.get("status")) for s in status.get("mcpServers", [])}


async def settle(
    client: Any, names: set[str], seconds: float = SETTLE_S
) -> tuple[dict[str, str], float]:
    """Poll until no named server is `pending`, or `seconds` pass. Returns the last statuses and
    the time taken."""
    started = time.perf_counter()
    while True:
        found = await statuses(client)
        if all(found.get(name, "pending") != "pending" for name in names):
            break
        if time.perf_counter() - started > seconds:
            break
        await asyncio.sleep(0.1)
    return found, round(time.perf_counter() - started, 2)


def options(slug: str, workspace: Any, servers: dict[str, QmxServer], **more: Any) -> Any:
    from claude_agent_sdk import (  # noqa: PLC0415
        ClaudeAgentOptions,
        PermissionResultAllow,
        PermissionResultDeny,
    )

    async def probe_tools_only(tool: str, _input: dict[str, Any], _ctx: Any) -> Any:
        if tool.startswith("mcp__"):
            return PermissionResultAllow()
        return PermissionResultDeny(message="probe allows only its MCP tools")

    return ClaudeAgentOptions(
        env=plan_env(slug),
        cwd=str(workspace),
        model=PLAN_MODEL,
        setting_sources=[],
        strict_mcp_config=True,
        tools=[],
        mcp_servers={name: server.config for name, server in servers.items()},  # type: ignore[misc]
        can_use_tool=probe_tools_only,
        **more,
    )


def offered(seen: Any) -> list[str]:
    return sorted(t for t in seen.init.get("tools", []) if str(t).startswith("mcp__"))


def pair() -> dict[str, QmxServer]:
    return {
        "qmx": QmxServer({"core_ping": answers("CORE-RAN")}, name="qmx"),
        "pack_x": QmxServer({"x_ping": answers("X-RAN")}, name="pack_x"),
    }


async def run(say: Log) -> dict[str, Any]:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    workspace = fresh("tg-ws")
    servers = pair()
    found: dict[str, Any] = {}
    async with ClaudeSDKClient(options("tg", workspace, servers)) as client:
        at_connect = await statuses(client)
        await client.toggle_mcp_server("pack_x", False)
        found["off_during_connect"] = {"status_when_sent": at_connect.get("pack_x")}
        found["off_during_connect"]["settled"], _ = await settle(client, {"qmx", "pack_x"})
        first = await turn(client, CALL, say)
        found["off_during_connect"] |= {"offered": offered(first), "reply": first.text()}
        await client.toggle_mcp_server("pack_x", True)
        on_status, _ = await settle(client, {"pack_x"})
        second = await turn(client, CALL, say)
        found["on"] = {
            "status": on_status.get("pack_x"),
            "offered": offered(second),
            "reply": second.text(),
            "calls": list(servers["pack_x"].calls),
        }
        await client.toggle_mcp_server("pack_x", False)
        off_status, _ = await settle(client, {"pack_x"})
        third = await turn(client, CALL, say)
        found["off"] = {
            "status": off_status.get("pack_x"),
            "offered": offered(third),
            "reply": third.text(),
            "calls": list(servers["pack_x"].calls),
        }
        session = first.session_id
        found["model_turns"] = first.num_turns + second.num_turns + third.num_turns
    async with ClaudeSDKClient(options("tg-second", workspace, pair())) as client:
        found["second_chat"], _ = await settle(client, {"qmx", "pack_x"})
    async with ClaudeSDKClient(options("tg", workspace, pair(), resume=session)) as client:
        found["resumed"], _ = await settle(client, {"qmx", "pack_x"})
    many = {
        f"tg{n:02d}": QmxServer({"ping": answers(f"R{n}")}, name=f"tg{n:02d}")
        for n in range(SERVERS_AT_LAUNCH)
    }
    started = time.perf_counter()
    async with ClaudeSDKClient(options("tg-forty", fresh("tg-forty-ws"), many)) as client:
        connected_at = time.perf_counter() - started
        forty, waited = await settle(client, set(many), seconds=30.0)
    found["forty"] = {
        "connect_s": round(connected_at, 2),
        "settle_after_connect_s": waited,
        "total_s": round(connected_at + waited, 2),
        "connected": sum(1 for v in forty.values() if v == "connected"),
        "statuses": sorted(set(forty.values())),
    }
    for key, value in found.items():
        say(f"[{key}] {json.dumps(value, default=str)}")
    return found


def verdict(observation: dict[str, Any]) -> Verdict:
    off_first, on, off = observation["off_during_connect"], observation["on"], observation["off"]
    forty = observation["forty"]
    cases = (
        Case(
            "a switch-off sent while the server connects holds",
            off_first["settled"].get("pack_x") == "disabled"
            and "mcp__pack_x__x_ping" not in off_first["offered"],
            off_first,
        ),
        Case(
            "toggled on mid-session, the server answers on the next request",
            "mcp__pack_x__x_ping" in on["offered"] and "X-RAN" in on["reply"],
            on,
        ),
        Case(
            "toggled off, a call to it fails",
            "mcp__pack_x__x_ping" not in off["offered"] and "X-RAN" not in off["reply"],
            off,
        ),
        Case(
            "a switch-off in one chat leaves the server on in a second chat on the workspace",
            observation["second_chat"].get("pack_x") == "connected",
            observation["second_chat"],
        ),
        Case(
            "a switch-off does not disable the server after a resume",
            observation["resumed"].get("pack_x") == "connected",
            observation["resumed"],
        ),
        Case(
            f"a launch with {SERVERS_AT_LAUNCH} servers settles within {SETTLE_S:.0f} s",
            forty["connected"] == SERVERS_AT_LAUNCH and forty["total_s"] <= SETTLE_S,
            forty,
        ),
    )
    return Verdict("P-TG", cases, FALLBACK)


def main() -> int:
    removed = scrub_process_env(os.environ)
    say = Log("prb-h-tg")
    say(f"scrubbed {len(removed)} names from the process env (names only)")
    before = ship_settings_hash()
    say(f"ship settings.toml sha256 before {before}")
    with lane_lock(say):
        say("lane lock taken")
        observation = asyncio.run(run(say))
    after = ship_settings_hash()
    say(f"ship settings.toml sha256 after {after}, unchanged={before == after}")
    observation["plan_turns"] = observation["model_turns"]
    say(f"haiku plan model turns: {observation['plan_turns']}")
    say.save(observation)
    return say.verdict(verdict(observation))


if __name__ == "__main__":
    sys.exit(main())
