"""S21d, redaction alone, and the approval floor. The harness runs in this process with
`TestMode(relay_egress_stop=False)`. A plan chat prints a fake token of the real shape (no real
login involved), then is asked to read a repo file and write `hello.txt`.

PASS when control.db and the live channel show `[redacted sk-ant token]` and never the fake
token, and the write is rejected by the floor with no file created.

    s21d_redaction.py [--home D:/QMX-worktrees/qma-ship/home] [--model haiku]
"""

from __future__ import annotations

import asyncio
import json
import sys

from common import Log, Session, boot, chat_args, require_login, use_fake_home

FAKE = "sk-ant-oat01-QMXCANARY" + "Zq7Xw2Lp9V" * 4
REDACTED = "[redacted sk-ant token]"


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

    async def listen() -> None:
        async for delta in session.harness.live(session.chat):
            shown.append(delta.text)

    listener = asyncio.create_task(listen())
    try:
        await asyncio.sleep(0)
        _, printed = await session.turn(
            log,
            "This is a fake test string, not a credential. Reply with exactly this line and "
            f"nothing else: {FAKE}",
        )
        stored = json.dumps([block["content"] for block in printed])
        live = "".join(shown)
        log.check("control.db holds the redaction mark", REDACTED in stored, REDACTED in stored)
        log.check(
            "control.db never holds the fake token", FAKE[:24] not in stored, FAKE[:24] in stored
        )
        log.check("the live channel shows the redaction mark", REDACTED in live, live[-120:])
        log.check("the live channel never shows the fake token", "QMXCANARY" not in live, len(live))
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
