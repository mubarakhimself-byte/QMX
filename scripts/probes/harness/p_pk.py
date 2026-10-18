"""P-PK (H47, AD-61; restored by review 48 H6). One in-process `qmx` server whose tool list
changes mid-session.

For each path, a chat on its own workspace starts with the tool `alpha` and calls it. The
harness then swaps the list to `beta` and tells the CLI:

- (a) `notifications/tools/list_changed`, sent on the session the CLI listed on, through the
  pinned SDK's bridge;
- (b) `reconnect_mcp_server("qmx")`;
- control: nothing, so a CLI that re-lists every turn on its own is told apart from (a).

Then one haiku turn asks for `beta`. A path holds when `beta` answers on that request, `alpha`
is gone from the offered tools, and nothing is written to the workspace's MCP state (the
`projects` entry for the workspace in the config folder's `.claude.json`, and no `.mcp.json` or
`.claude/` in the workspace). A second chat on the same workspace and a relaunch by resume, each
with its own list, must see only their own tools. The cache read on the request after the
change is recorded.

PASS when (a) or (b) holds. Both fail: run P-TG with the review 48 cases.

    <venv>/Scripts/python.exe p_pk.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Final

from common import (
    PLAN_CONFIG_DIR,
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

FALLBACK: Final = "run P-TG with the review 48 cases (both P-PK paths failed)"
PATHS: Final = ("a_list_changed", "b_reconnect", "control_no_signal")
CALL: Final = (
    "Call the tool mcp__qmx__{tool} once with no arguments and reply with exactly the text it "
    "returned. If no tool of that name is offered to you, reply with NO-TOOL and call nothing."
)


def mcp_state(workspace: Path) -> dict[str, Any]:
    """The MCP keys of the workspace's entry in the plan config's `.claude.json`, and whether
    the workspace holds MCP files. No other key of that file is read."""
    config = PLAN_CONFIG_DIR / ".claude.json"
    projects = json.loads(config.read_text(encoding="utf-8")).get("projects", {}) if config.exists() else {}
    wanted = {str(workspace).replace("\\", "/").lower(), str(workspace).lower()}
    entry = next(
        (value for key, value in projects.items() if key.replace("\\", "/").lower() in wanted), {}
    )
    return {
        "entry_mcp_keys": {k: v for k, v in entry.items() if "mcp" in k.lower()},
        "mcp_json": (workspace / ".mcp.json").exists(),
        "dot_claude": (workspace / ".claude").exists(),
    }


async def status_tools(client: Any, settle_s: float = 10.0) -> list[str]:
    """The `qmx` server's tools as `get_mcp_status` reports them (bare names), once it reports
    `connected` or after `settle_s`."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + settle_s
    while True:
        status = await client.get_mcp_status()
        qmx = [s for s in status.get("mcpServers", []) if s.get("name") == "qmx"]
        if (qmx and qmx[0].get("status") == "connected") or loop.time() > deadline:
            return sorted(str(t.get("name")) for s in qmx for t in s.get("tools", []) or [])
        await asyncio.sleep(0.25)


def options(slug: str, workspace: Path, server: QmxServer, **more: Any) -> Any:
    from claude_agent_sdk import (  # noqa: PLC0415
        ClaudeAgentOptions,
        PermissionResultAllow,
        PermissionResultDeny,
    )

    async def qmx_only(tool: str, _input: dict[str, Any], _ctx: Any) -> Any:
        if tool.startswith("mcp__qmx__"):
            return PermissionResultAllow()
        return PermissionResultDeny(message="probe allows only qmx tools")

    return ClaudeAgentOptions(
        env=plan_env(slug),
        cwd=str(workspace),
        model=PLAN_MODEL,
        setting_sources=[],
        strict_mcp_config=True,
        tools=[],
        mcp_servers={"qmx": server.config},  # type: ignore[dict-item]
        can_use_tool=qmx_only,
        **more,
    )


def offered(seen: Any) -> list[str]:
    return sorted(t for t in seen.init.get("tools", []) if str(t).startswith("mcp__qmx__"))


async def one_path(say: Log, path: str) -> dict[str, Any]:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    workspace = fresh(f"pk-{path}-ws")
    state_before = mcp_state(workspace)
    server = QmxServer({"alpha": answers("ALPHA-RAN")})
    row: dict[str, Any] = {"path": path}
    async with ClaudeSDKClient(options(f"pk-{path}", workspace, server)) as client:
        first = await turn(client, CALL.format(tool="alpha"), say)
        lists_before = server.list_calls
        server.tools = {"beta": answers("BETA-RAN")}
        if path == "a_list_changed":
            row["signal"] = await server.send_list_changed()
            await asyncio.sleep(1.0)
        elif path == "b_reconnect":
            try:
                await client.reconnect_mcp_server("qmx")
                row["signal"] = "reconnected"
            except Exception as error:  # noqa: BLE001
                row["signal"] = f"raised {type(error).__name__}: {error}"
        else:
            row["signal"] = "none"
        row["relists_after_signal"] = server.list_calls - lists_before
        row["status_after_change"] = await status_tools(client)
        second = await turn(client, CALL.format(tool="beta"), say)
    row |= {
        "session": first.session_id,
        "before": {"offered": offered(first), "reply": first.text()},
        "after": {
            "offered": offered(second),
            "reply": second.text(),
            "cache_read": int(second.usage.get("cache_read_input_tokens") or 0),
            "cache_write": int(second.usage.get("cache_creation_input_tokens") or 0),
        },
        "server_calls": list(server.calls),
        "list_calls": server.list_calls,
        "model_turns": first.num_turns + second.num_turns,
    }

    other = QmxServer({"gamma": answers("GAMMA-RAN")})
    async with ClaudeSDKClient(options(f"pk-{path}-second", workspace, other)) as client:
        row["second_chat_tools"] = await status_tools(client)
    resumed = QmxServer({"delta": answers("DELTA-RAN")})
    resume_opts = options(f"pk-{path}", workspace, resumed, resume=first.session_id)
    async with ClaudeSDKClient(resume_opts) as client:
        row["resumed_chat_tools"] = await status_tools(client)
    row["state_before"], row["state_after"] = state_before, mcp_state(workspace)
    say(f"[{path}] {json.dumps({k: v for k, v in row.items() if k != 'before'}, default=str)}")
    return row


def holds(row: dict[str, Any]) -> dict[str, bool]:
    after = row["after"]
    return {
        "new tool answers on the next request": "beta" in row["server_calls"]
        and "BETA-RAN" in after["reply"],
        "removed tool is gone": "mcp__qmx__alpha" not in after["offered"]
        and "mcp__qmx__beta" in after["offered"],
        "nothing written to the workspace's MCP state": row["state_before"] == row["state_after"],
        "a second chat on the workspace sees its own list": row["second_chat_tools"]
        == ["gamma"],
        "a resumed chat sees its own list": row["resumed_chat_tools"] == ["delta"],
    }


def verdict(observation: dict[str, Any]) -> Verdict:
    paths = observation["paths"]
    cases = []
    for path in ("a_list_changed", "b_reconnect"):
        checks = holds(paths[path])
        cases.append(Case(f"path {path}", all(checks.values()), checks | {"cache_read_after": paths[path]["after"]["cache_read"]}))
    either = Case("(a) or (b) holds", any(c.ok for c in cases), [c.name for c in cases if c.ok])
    control = paths.get("control_no_signal")
    recorded = Case(
        "the no-signal control is recorded",
        control is not None,
        holds(control) if control else None,
    )
    return Verdict("P-PK", (either, recorded, *[Case(f"record: {c.name}", True, c.seen) for c in cases]), FALLBACK)


async def run(say: Log) -> dict[str, Any]:
    paths = {path: await one_path(say, path) for path in PATHS}
    return {"paths": paths, "plan_turns": sum(row["model_turns"] for row in paths.values())}


def main() -> int:
    slug = sys.argv[1] if len(sys.argv) > 1 else "prb-h-pk"
    removed = scrub_process_env(os.environ)
    say = Log(slug)
    say(f"scrubbed {len(removed)} names from the process env (names only)")
    before = ship_settings_hash()
    say(f"ship settings.toml sha256 before {before}")
    with lane_lock(say):
        say("lane lock taken")
        observation = asyncio.run(run(say))
    after = ship_settings_hash()
    say(f"ship settings.toml sha256 after {after}, unchanged={before == after}")
    say(f"haiku plan model turns: {observation['plan_turns']}")
    for path, row in observation["paths"].items():
        say(f"FINDING {path}: {holds(row)}")
    say.save(observation)
    return say.verdict(verdict(observation))


if __name__ == "__main__":
    sys.exit(main())
