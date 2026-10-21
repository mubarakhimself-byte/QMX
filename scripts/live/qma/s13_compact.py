"""S13, compaction. The harness runs in this process. A plan chat gets one turn, then the
operator text `/compact`, then a question only the QMX rules in the system prompt `append`
answer.

PASS when the `/compact` turn's result names its compaction and the answer afterwards still
states QMX's money rule. Each turn ends through `Harness.run_turn`'s `result()`. The raw
`compact_boundary` message is logged for the projection fixtures.

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
TURN_S = 300.0


async def turn(log: Log, session: Session, text: str) -> Any:
    from qma.harness import OperatorText  # noqa: PLC0415

    log(f"turn: {text}")
    handle = await session.harness.run_turn(session.chat, OperatorText(text))
    done = await asyncio.wait_for(handle.result(), TURN_S)
    log(f"result: status={done.status} compactions={done.compactions} text={done.text!r:.200}")
    return done


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
        await turn(log, session, "Remember the codeword PLUM for later. Reply with ok.")
        compacted = await turn(log, session, "/compact")
        log.check("the /compact turn compacted", bool(compacted.compactions), compacted.compactions)
        answer = await turn(
            log,
            session,
            "Without using tools: what do your QMX rules say about placing broker orders? "
            "One sentence.",
        )
        text = " ".join(
            str(b.content.get("text", "")) for b in answer.blocks if b.type == "text"
        ).lower()
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
