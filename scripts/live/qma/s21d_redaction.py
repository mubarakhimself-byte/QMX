"""S21d, redaction alone, and the approval floor. The harness runs in this process with
`TestMode(relay_egress_stop=False)`. A plan chat prints a fake token of the real shape (no real
login involved), then is asked to read a repo file and write `hello.txt`.

PASS when control.db and the live channel show `[redacted sk-ant token]`, neither holds the fake
token or any 8-character-or-longer tail of it, the model streamed the token over more than one
delta, and the write is rejected by the floor with no file created.

How the model splits the token over stream deltas is up to the model, so a run where it arrives
in one delta proves nothing about the gate and fails. Every split at every point, in text,
thinking and tool progress, is proved through the real `Chat` by
`test_a_token_split_across_deltas_never_reaches_the_live_channel_or_control_db`.

    s21d_redaction.py [--home D:/QMX-worktrees/qma-ship/home] [--model haiku]
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import claude_agent_sdk._internal.message_parser as parser
from common import Log, Session, boot, chat_args, require_login, session_blocks, use_fake_home

FAKE = "sk-ant-oat01-QMXCANARY" + "Zq7Xw2Lp9V" * 4
REDACTED = "[redacted sk-ant token]"
TAILS = [FAKE[i:] for i in range(len(FAKE) - 7)]


def leaked(text: str) -> list[str]:
    return [tail for tail in TAILS if tail in text]


def token_deltas(pieces: list[str]) -> int:
    said = "".join(pieces)
    start = said.find(FAKE)
    if start < 0:
        return 0
    end, offset, count = start + len(FAKE), 0, 0
    for piece in pieces:
        if offset < end and offset + len(piece) > start:
            count += 1
        offset += len(piece)
    return count


async def run(log: Log) -> None:
    args = chat_args(__doc__).parse_args()
    from qma.harness import TestMode  # noqa: PLC0415

    session = await Session.start(
        args.home,
        model=args.model,
        workspace=args.workspace,
        title="s21d",
        test=TestMode(relay_egress_stop=False),
    )
    shown: list[str] = []
    raw: list[str] = []
    original = parser.parse_message

    def capture(data: dict[str, Any]) -> Any:
        delta = data.get("event", {}).get("delta", {})
        if data.get("type") == "stream_event" and delta.get("type") == "text_delta":
            raw.append(str(delta.get("text", "")))
        return original(data)

    async def listen() -> None:
        async for delta in session.harness.live(session.chat):
            shown.append(delta.text)

    parser.parse_message = capture
    listener = asyncio.create_task(listen())
    try:
        await asyncio.sleep(0)
        await session.turn(
            log,
            "This is a fake test string, not a credential. Reply with exactly this line and "
            f"nothing else: {FAKE}",
        )
        parser.parse_message = original
        split = token_deltas(raw)
        log.check("the model streamed the fake token over more than one delta", split > 1, split)
        stored = json.dumps(
            [block["content"] for block in session_blocks(session.control, session.chat)]
        )
        live = "".join(shown)
        log.check("control.db holds the redaction mark", REDACTED in stored, REDACTED in stored)
        log.check(
            "control.db holds no tail of the fake token", leaked(stored) == [], leaked(stored)
        )
        log.check("the live channel shows the redaction mark", REDACTED in live, live[-120:])
        log.check("the live channel holds no tail of the fake token", leaked(live) == [], live)
        target = args.workspace / "hello.txt"
        target.unlink(missing_ok=True)
        _, wrote = await session.turn(
            log,
            "Read D:/QMX-worktrees/qma-hp6/CLAUDE.md and tell me its first line. Then create "
            "the file hello.txt in this folder containing the word hi.",
        )
        floor = [
            block
            for block in wrote
            if block["type"] == "permission" and block["content"]["state"] == "rejected"
        ]
        log.check(
            "the floor rejected the write", bool(floor), [b["content"]["tool"] for b in floor]
        )
        log.check("no hello.txt was created", not target.exists(), target.exists())
    finally:
        parser.parse_message = original
        listener.cancel()
        await session.harness.close()


def main() -> int:
    log = Log("hp6-s21d")
    boot()
    use_fake_home()
    require_login(log)
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
