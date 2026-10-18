"""S13, compaction. The harness runs in this process. A plan chat gets one turn, then the
operator text `/compact`, then a question only the QMX rules in the system prompt `append`
answer.

PASS when a `compacted` block arrives after `/compact` and the answer afterwards still states
QMX's money rule. The raw `compact_boundary` message is logged for the projection fixtures.

    s13_compact.py [--home D:/QMX-worktrees/qma-ship/home] [--model haiku]
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import claude_agent_sdk._internal.message_parser as parser
from common import Log, Session, boot, chat_args, require_login, use_fake_home

RULE_WORDS = ("read-only", "read only", "never place", "propos")


async def run(log: Log) -> None:
    args = chat_args(__doc__).parse_args()
    original = parser.parse_message

    def logged(data: dict[str, Any]) -> Any:
        if data.get("subtype") == "compact_boundary":
            log(f"raw compact_boundary: {json.dumps(data)}")
        return original(data)

    parser.parse_message = logged
    session = await Session.start(
        args.home, model=args.model, workspace=args.workspace, title="s13"
    )
    try:
        await session.turn(log, "Remember the codeword PLUM for later. Reply with ok.")
        _, compacted = await session.turn(log, "/compact")
        marks = [
            b
            for b in compacted
            if b["type"] == "changed" and b["content"].get("kind") == "compacted"
        ]
        log.check("a compacted block arrived", bool(marks), [b["content"] for b in marks])
        _, answer = await session.turn(
            log,
            "Without using tools: what do your QMX rules say about placing broker orders? "
            "One sentence.",
        )
        text = " ".join(b["content"]["text"] for b in answer if b["type"] == "text").lower()
        log.check(
            "the QMX money rule is still followed", any(w in text for w in RULE_WORDS), text[:200]
        )
    finally:
        parser.parse_message = original
        await session.harness.close()


def main() -> int:
    log = Log("hp6-s13")
    boot()
    use_fake_home()
    require_login(log)
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
