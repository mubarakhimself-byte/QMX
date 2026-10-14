"""S3, same tools as vanilla. One `say ok` turn through a QMA chat in this process, and one
through the bundled CLI as `claude -p` with a vanilla environment (throwaway HOME, the plan
home of `--home`, no QMA options). Both init tool lists are read from the CLI's own messages.

Tools that the QMX home's `[claude]` deny rules name bare are left out of both sides, since a
fully denied tool is the operator's choice, not a harness departure. MCP tools are left out
too; HP6 has no QMX server yet.

PASS when the lists differ by DESIGN S3's named entries only (Workflow and TodoWrite), each
difference named. Whether a PowerShell tool appears is recorded.

    s03_tools.py [--home D:/QMX-worktrees/qma-ship/home] [--model haiku]
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

import claude_agent_sdk._internal.message_parser as parser
from common import Log, Session, boot, chat_args, require_login, use_fake_home
from s04_vanilla import deny_rules, vanilla

NAMED = frozenset({"Workflow", "TodoWrite"})


def built_in(tools: list[str], denied: set[str]) -> set[str]:
    return {tool for tool in tools if not tool.startswith("mcp__") and tool not in denied}


async def qma_tools(args: Any, log: Log) -> list[str]:
    seen: list[list[str]] = []
    original = parser.parse_message

    def capture(data: dict[str, Any]) -> Any:
        if data.get("type") == "system" and data.get("subtype") == "init":
            seen.append(list(data.get("tools", [])))
        return original(data)

    parser.parse_message = capture
    session = await Session.start(
        args.home, model=args.model, workspace=args.workspace, title="s03"
    )
    try:
        await session.turn(log, "say ok")
    finally:
        parser.parse_message = original
        await session.harness.close()
    return seen[0] if seen else []


def main() -> int:
    args = chat_args(__doc__).parse_args()
    log = Log("hp6-s03")
    boot()
    use_fake_home()
    require_login(log)
    denied = {rule for rule in deny_rules(args.home) if "(" not in rule}
    log(f"left out as fully denied by [claude]: {sorted(denied)}")
    qma = built_in(asyncio.run(qma_tools(args, log)), denied)
    _, lines = vanilla(args.home, args.model, args.workspace, "say ok", deny=False)
    init = next((m for m in lines if m.get("subtype") == "init"), {})
    plain = built_in(list(init.get("tools", [])), denied)
    log(f"QMA tools ({len(qma)}): {sorted(qma)}")
    log(f"vanilla tools ({len(plain)}): {sorted(plain)}")
    only_qma, only_vanilla = sorted(qma - plain), sorted(plain - qma)
    log(f"only in QMA: {only_qma}; only in vanilla: {only_vanilla}")
    log(f"PowerShell tool in QMA: {'PowerShell' in qma}; in vanilla: {'PowerShell' in plain}")
    log.check("the lists are not empty", bool(qma) and bool(plain), (len(qma), len(plain)))
    differs = set(only_qma) | set(only_vanilla)
    log.check("the difference is only DESIGN S3's named entries", differs <= NAMED, sorted(differs))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
