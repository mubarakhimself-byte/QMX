"""S12, long-reply case. The harness runs in this process. A plan chat starts a long reply; on
the first streamed text the check interrupts it.

PASS when the turn ends (record "idle", the `TurnEnded` path) within 5 s of the interrupt and
the chat's CLI has no child process left. The Bash case runs in HP9, once approvals exist.

    s12_interrupt.py [--home D:/QMX-worktrees/qma-ship/home] [--model haiku]
"""

from __future__ import annotations

import asyncio
import sys
import time

import psutil
from common import Log, Session, boot, chat_args, require_login, use_fake_home, wait_turn

LIMIT_S = 5.0


def cli_children(session: Session) -> list[str]:
    from qma.launcher import pid_path, read_pid_record  # noqa: PLC0415

    record = read_pid_record(pid_path(session.home.procs_dir, session.chat))
    if record is None:
        return []
    try:
        return [child.name() for child in psutil.Process(record.cli_pid).children(recursive=True)]
    except psutil.NoSuchProcess:
        return []


async def run(log: Log) -> None:
    args = chat_args(__doc__).parse_args()
    from qma.harness import OperatorText  # noqa: PLC0415

    session = await Session.start(
        args.home, model=args.model, workspace=args.workspace, title="s12"
    )
    first = asyncio.Event()

    async def listen() -> None:
        async for delta in session.harness.live(session.chat):
            if delta.kind == "text":
                first.set()

    listener = asyncio.create_task(listen())
    try:
        await asyncio.sleep(0)
        await session.harness.send(
            session.chat,
            OperatorText("Write a 1500-word story about a lighthouse keeper. No tools."),
        )
        await asyncio.wait_for(first.wait(), 120)
        started = time.monotonic()
        await session.harness.interrupt(session.chat)
        record = await wait_turn(session.home, session.chat, 30)
        elapsed = time.monotonic() - started
        log.check(
            f"turn ended within {LIMIT_S} s of the interrupt",
            record.turn == "idle" and elapsed <= LIMIT_S,
            f"{elapsed:.2f} s, turn {record.turn}",
        )
        children = cli_children(session)
        log.check("no CLI child process left", children == [], children)
    finally:
        listener.cancel()
        await session.harness.close()


def main() -> int:
    log = Log("hp6-s12")
    boot()
    use_fake_home()
    require_login(log)
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
