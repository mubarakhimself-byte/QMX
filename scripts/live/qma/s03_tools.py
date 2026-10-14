"""S3, same tools as vanilla, compared like with like. Every side is the same bundled CLI in the
same plan home, from the same throwaway HOME and workspace, started through the SDK with
`setting_sources=[]`, strict MCP and claude.ai connectors off, so no user settings, plugins or
connectors differ. Every side asks for a model that does not exist: the CLI prints its init
message, then answers with a synthetic error, so no side spends a token or runs a tool.

    vanilla           an interactive Claude Code session: a permission callback, nothing else
    vanilla + env     the same, plus QMA's constant CLI environment (`CONSTANT_ENV`)
    QMA               a chat through `Harness.send`

Tools that the QMX home's `[claude]` deny rules name bare are left out of the comparison, since
a fully denied tool is the operator's choice. MCP tools are left out too; HP6 has no QMX
server yet. Each difference is attributed: a tool that vanilla + env shares with QMA moved
because of QMA's environment.

PASS when the QMA list differs from vanilla by exactly the entries in `EXPECTED`, each on its
named side, less the tools left out as denied. DESIGN S3 named Workflow and TodoWrite; on CLI
2.1.299 TodoWrite is the four Task tools, and nonessential traffic off also turns off the
flag-gated Monitor, DesignSync and PushNotification. The PowerShell line reads each side's raw
list, or says "denied by [claude]" when the home denies the tool, since the CLI then leaves it
out of the QMA list.

    s03_tools.py [--home D:/QMX-worktrees/qma-ship/home]
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

import claude_agent_sdk._internal.message_parser as parser
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultDeny,
    ResultMessage,
    SystemMessage,
)
from common import Log, Session, boot, chat_args, require_login, use_fake_home
from s04_vanilla import deny_rules

EXPECTED: dict[str, str] = {
    "Workflow": "only in vanilla",
    "Monitor": "only in vanilla",
    "DesignSync": "only in vanilla",
    "PushNotification": "only in vanilla",
    "TaskCreate": "only in QMA",
    "TaskGet": "only in QMA",
    "TaskList": "only in QMA",
    "TaskUpdate": "only in QMA",
}
NO_MODEL = "qmx-no-such-model"


def built_in(tools: list[str], denied: set[str]) -> set[str]:
    return {tool for tool in tools if not tool.startswith("mcp__") and tool not in denied}


async def deny(*_: Any) -> PermissionResultDeny:
    return PermissionResultDeny(message="s03 runs no tool")


async def vanilla(home: Path, workspace: Path, env: dict[str, str]) -> tuple[list[str], Any]:
    options = ClaudeAgentOptions(
        model=NO_MODEL,
        cwd=workspace,
        setting_sources=[],
        strict_mcp_config=True,
        can_use_tool=deny,
        env={
            "CLAUDE_CONFIG_DIR": str(home / "claude"),
            "ENABLE_CLAUDEAI_MCP_SERVERS": "false",
            **env,
        },
    )
    tools: list[str] = []
    spent = None
    async with ClaudeSDKClient(options) as client:
        await client.query("say ok")
        async for message in client.receive_response():
            if isinstance(message, SystemMessage) and message.subtype == "init":
                tools = list(message.data.get("tools", []))
            if isinstance(message, ResultMessage):
                spent = (message.usage or {}).get("output_tokens")
    return tools, spent


async def qma(home: Path, workspace: Path) -> tuple[list[str], Any]:
    from qma.harness import OperatorText  # noqa: PLC0415

    seen: list[list[str]] = []
    spent: list[Any] = []
    original = parser.parse_message

    def capture(data: dict[str, Any]) -> Any:
        if data.get("type") == "system" and data.get("subtype") == "init":
            seen.append(list(data.get("tools", [])))
        if data.get("type") == "result":
            spent.append((data.get("usage") or {}).get("output_tokens"))
        return original(data)

    parser.parse_message = capture
    session = await Session.start(home, model=NO_MODEL, workspace=workspace, title="s03")
    try:
        await session.harness.send(session.chat, OperatorText("say ok"))
        for _ in range(600):
            if spent:
                break
            await asyncio.sleep(0.1)
    finally:
        parser.parse_message = original
        await session.harness.close()
    return (seen[0] if seen else []), (spent[0] if spent else None)


def main() -> int:
    args = chat_args(__doc__).parse_args()
    log = Log("hp6-s03")
    boot()
    use_fake_home()
    require_login(log)
    from qma.harness.launch import CONSTANT_ENV  # noqa: PLC0415

    args.workspace.mkdir(parents=True, exist_ok=True)
    denied = {rule for rule in deny_rules(args.home) if "(" not in rule}
    log(f"model {NO_MODEL}; left out as fully denied by [claude]: {sorted(denied)}")
    raw = {
        "vanilla": asyncio.run(vanilla(args.home, args.workspace, {})),
        "vanilla + env": asyncio.run(vanilla(args.home, args.workspace, dict(CONSTANT_ENV))),
        "QMA": asyncio.run(qma(args.home, args.workspace)),
    }
    lists = {name: built_in(tools, denied) for name, (tools, _) in raw.items()}
    for name, (tools, spent) in raw.items():
        log(f"{name} tools ({len(lists[name])}), output tokens {spent}: {sorted(lists[name])}")
        powershell = "denied by [claude]" if "PowerShell" in denied else "PowerShell" in tools
        log(f"PowerShell tool in {name}: {powershell}")
    plain, with_env, harness = lists["vanilla"], lists["vanilla + env"], lists["QMA"]
    sides: dict[str, str] = {}
    for tool in sorted(harness ^ plain):
        sides[tool] = "only in QMA" if tool in harness else "only in vanilla"
        cause = "QMA's constant env" if (tool in with_env) == (tool in harness) else "the harness"
        log(f"{sides[tool]}: {tool}, moved by {cause}")
    log.check(
        "every side answered with no output tokens",
        all(spent == 0 for _, spent in raw.values()),
        [spent for _, spent in raw.values()],
    )
    log.check("the lists are not empty", all(lists.values()), [len(t) for t in lists.values()])
    expected = {tool: side for tool, side in EXPECTED.items() if tool not in denied}
    log.check(
        "the difference is exactly the expected entries, each on its side", sides == expected, sides
    )
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
