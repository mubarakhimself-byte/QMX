"""P-NM (AD-61, SOLUTION-DESIGN 28.8). The pinned CLI with an in-process tool whose full name
`mcp__qmx__<tool>` is 64, 65 and 80 characters, and one with a dot: record which load and
which the API refuses.

Each name gets its own chat, so a name the API refuses cannot fail the others' requests. A
chat has no built-in tools and one tool on the in-process `qmx` server; `can_use_tool` allows
only that tool. One haiku turn asks the model to call it.

PASS when every name has a recorded load result and turn outcome, and the 64-character name
loads and answers (the AD-61 limit holds). The longest name that loaded and answered is the
length CAT's wire-name check enforces.

    <venv>/Scripts/python.exe p_nm.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Final

from common import (
    LIVE_QMA,
    PLAN_MODEL,
    Case,
    Log,
    QmxServer,
    Verdict,
    answers,
    fresh,
    home_env,
    lane_lock,
    plan_env,
    scrub_process_env,
    ship_settings_hash,
    turn,
)

sys.path.append(str(LIVE_QMA))

PREFIX: Final = "mcp__qmx__"
FALLBACK: Final = (
    "no fallback: the result sets the length CAT's wire-name check enforces "
    "(AD-61 says at most 64)"
)


def tool_name(full_length: int, stem: str) -> str:
    """A tool name that makes `mcp__qmx__<name>` exactly `full_length` characters."""
    return (stem + "_" + "x" * full_length)[: full_length - len(PREFIX)]


NAMES: Final[dict[str, str]] = {
    "64": tool_name(64, "nm64"),
    "65": tool_name(65, "nm65"),
    "80": tool_name(80, "nm80"),
    "dot": "library.search_nm",
}


def verdict(observation: dict[str, Any]) -> Verdict:
    rows: dict[str, dict[str, Any]] = observation["names"]
    cases = [
        Case(
            f"{key} ({len(PREFIX + NAMES[key])} chars) has a recorded load result and outcome",
            key in rows and "loaded" in rows[key] and "answered" in rows[key],
            {k: rows.get(key, {}).get(k) for k in ("loaded", "answered", "refused")},
        )
        for key in NAMES
    ]
    at_limit = rows.get("64", {})
    cases.append(
        Case(
            "the 64-character name loads and answers",
            bool(at_limit.get("loaded")) and bool(at_limit.get("answered")),
            {"loaded": at_limit.get("loaded"), "answered": at_limit.get("answered")},
        )
    )
    return Verdict("P-NM", tuple(cases), FALLBACK)


def longest_that_works(observation: dict[str, Any]) -> int:
    rows: dict[str, dict[str, Any]] = observation["names"]
    return max(
        (len(PREFIX + NAMES[key]) for key, row in rows.items() if row["loaded"] and row["answered"]),
        default=0,
    )


async def one(say: Log, key: str) -> dict[str, Any]:
    from claude_agent_sdk import (  # noqa: PLC0415
        ClaudeAgentOptions,
        ClaudeSDKClient,
        PermissionResultAllow,
        PermissionResultDeny,
    )

    tool = NAMES[key]
    marker = f"NM-OK-{key}"
    server = QmxServer({tool: answers(marker)})
    full = server.wire(tool)
    say(f"[{key}] full name {full!r} ({len(full)} characters)")

    async def allow_only_the_tool(name: str, _input: dict[str, Any], _ctx: Any) -> Any:
        if name == full:
            return PermissionResultAllow()
        return PermissionResultDeny(message=f"probe allows only {full}")

    options = ClaudeAgentOptions(
        env=plan_env(f"nm-{key}"),
        cwd=str(fresh(f"nm-{key}-ws")),
        model=PLAN_MODEL,
        setting_sources=[],
        strict_mcp_config=True,
        tools=[],
        mcp_servers={"qmx": server.config},  # type: ignore[dict-item]
        can_use_tool=allow_only_the_tool,
    )
    row: dict[str, Any] = {"full": full, "length": len(full)}
    try:
        async with ClaudeSDKClient(options) as client:
            status = await client.get_mcp_status()
            listed = [
                str(t.get("name"))
                for s in status.get("mcpServers", [])
                if s.get("name") == "qmx"
                for t in s.get("tools", []) or []
            ]
            row["mcp_status"] = [
                {"name": s.get("name"), "status": s.get("status"), "error": s.get("error")}
                for s in status.get("mcpServers", [])
            ]
            row["status_tools"] = listed
            seen = await turn(
                client,
                f"Call the tool named {full} once with no arguments, then reply with exactly "
                "the text it returned.",
                say,
            )
    except Exception as error:  # noqa: BLE001
        row |= {"loaded": False, "answered": False, "refused": f"{type(error).__name__}: {error}"}
        say(f"[{key}] launch failed: {row['refused']}")
        return row
    row["init_tools"] = [t for t in seen.init.get("tools", []) if str(t).startswith("mcp__")]
    row["loaded"] = len(row["init_tools"]) == 1
    row["listed_as"] = row["init_tools"][0] if row["loaded"] else None
    row["answered"] = server.calls == [tool] and marker in seen.text()
    error_text = seen.text() if seen.subtype != "success" or "API Error" in seen.text() else ""
    row["refused"] = error_text or None
    row["turn"] = seen.as_dict()
    say(
        f"[{key}] loaded={row['loaded']} (init tools {row['init_tools']}, status tools {listed}); "
        f"calls {server.calls}; answered={row['answered']}; refused={row['refused']!r}"
    )
    return row


async def on_the_wire(say: Log, key: str) -> list[str]:
    """The `qmx` tool names the CLI puts in a Messages request, read from the fake model, which
    needs no login: the plan's own requests cannot be read."""
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient  # noqa: PLC0415
    from fake_model import FAKE_KEY, MODEL, FakeModel, Turn, text  # noqa: PLC0415

    root = fresh(f"nm-{key}-fake")
    fake = FakeModel([Turn([text("done")])]).start()
    env = home_env(root / "home", root / "claude") | {
        "ANTHROPIC_BASE_URL": fake.url,
        "ANTHROPIC_API_KEY": FAKE_KEY,
    }
    server = QmxServer({NAMES[key]: answers("unused")})
    options = ClaudeAgentOptions(
        env=env,
        cwd=str(root),
        model=MODEL,
        setting_sources=[],
        strict_mcp_config=True,
        tools=[],
        mcp_servers={"qmx": server.config},  # type: ignore[dict-item]
    )
    try:
        async with ClaudeSDKClient(options) as client:
            await turn(client, "Reply with the word done.", say)
    finally:
        fake.stop()
    names = sorted(
        {
            str(tool.get("name"))
            for seen in fake.requests
            if seen.method == "POST"
            for tool in seen.json.get("tools", [])
            if str(tool.get("name", "")).startswith("mcp__")
        }
    )
    say(f"[{key}] fake model saw qmx tool names {names}")
    return names


async def run(say: Log) -> dict[str, Any]:
    names = {key: await one(say, key) for key in NAMES}
    for key, row in names.items():
        row["wire_names"] = await on_the_wire(say, key)
    return {"names": names}


def main() -> int:
    removed = scrub_process_env(os.environ)
    say = Log("prb-h-nm")
    say(f"scrubbed {len(removed)} names from the process env (names only)")
    before = ship_settings_hash()
    say(f"ship settings.toml sha256 before {before}")
    with lane_lock(say):
        say("lane lock taken")
        observation = asyncio.run(run(say))
    after = ship_settings_hash()
    say(f"ship settings.toml sha256 after {after}, unchanged={before == after}")
    observation["plan_turns"] = sum(
        int(row.get("turn", {}).get("num_turns", 0)) for row in observation["names"].values()
    )
    say(f"haiku plan model turns: {observation['plan_turns']}")
    say(f"FINDING longest full name that loaded and answered: {longest_that_works(observation)}")
    say.save(observation)
    return say.verdict(verdict(observation))


if __name__ == "__main__":
    sys.exit(main())
