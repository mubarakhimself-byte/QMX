"""S12, interrupt. The harness runs in this process.

Long-reply case (default): a plan chat starts a long reply; on the first streamed text the
check interrupts it.

Bash case (`--bash`): a key chat on the fake model calls Bash `sleep 30 && touch s12.txt`. The
CLI runs a bare `sleep` without asking, so the `touch` makes it ask. The operator allows it
through `POST /api/approvals/{ask_id}`, and once the command runs under the CLI the check
interrupts the turn.

PASS when the turn ends (record "idle", the `TurnEnded` path) within 5 s of the interrupt and
the chat's CLI has no child process left.

    s12_interrupt.py [--home D:/QMX-worktrees/qma-ship/home] [--model haiku]
    s12_interrupt.py --bash
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time

import psutil
from approval_lane import ALLOW_ONCE, PROMPT, Answerer, Host, always, fake_session
from common import (
    Log,
    Session,
    boot,
    chat_args,
    require_login,
    use_fake_home,
    use_fake_key,
    wait_turn,
)
from fake_model import Turn, text, tool_use

LIMIT_S = 5.0
SLEEP_WAIT_S = 60.0


def cli_children(session: Session) -> list[str]:
    from qma.launcher import pid_path, read_pid_record  # noqa: PLC0415

    record = read_pid_record(pid_path(session.home.procs_dir, session.chat))
    if record is None:
        return []
    try:
        return [child.name() for child in psutil.Process(record.cli_pid).children(recursive=True)]
    except psutil.NoSuchProcess:
        return []


def sleeps() -> set[int]:
    """Every `sleep` process on the machine. Git Bash's `sleep.exe` has no live parent once
    started (measured), so it never shows among the CLI's children."""
    return {
        proc.pid
        for proc in psutil.process_iter(["name"])
        if str(proc.info["name"]).lower().startswith("sleep")
    }


async def ended_in_time(log: Log, session: Session) -> None:
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


async def reply_case(log: Log, args: argparse.Namespace) -> None:
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
        await ended_in_time(log, session)
    finally:
        listener.cancel()
        await session.harness.close()


async def bash_case(log: Log) -> None:
    from qma.harness import OperatorText  # noqa: PLC0415

    script = [
        Turn([tool_use("Bash", {"command": "sleep 30 && touch s12.txt", "description": "wait"})]),
        Turn([text("done")]),
    ]
    _, fake, session = await fake_session("hp9-s12", script, tools=["Bash"])
    try:
        async with Host(session) as host:
            answerer = Answerer(host, session.chat, always(ALLOW_ONCE), log).start()
            await session.harness.send(session.chat, OperatorText(PROMPT))
            deadline = time.monotonic() + SLEEP_WAIT_S
            while not answerer.answered and time.monotonic() < deadline:
                await asyncio.sleep(0.05)
            before = sleeps()
            ours: set[int] = set()
            while not ours and time.monotonic() < deadline:
                await asyncio.sleep(0.2)
                ours = sleeps() - before
            log.check(
                "the approved sleep ran",
                [a.status for a in answerer.answered] == ["resolved"] and bool(ours),
                f"{[a.status for a in answerer.answered]}, sleep pids {sorted(ours)}",
            )
            await ended_in_time(log, session)
            await answerer.stop()
            await asyncio.sleep(LIMIT_S)
            left = sleeps() & ours
            log.check(
                f"no sleep process left {LIMIT_S:.0f} s after the interrupt", left == set(), left
            )
    finally:
        await session.harness.close()
        fake.stop()
    log(f"  sleep processes left after the harness closed: {sorted(sleeps() & ours)}")


def main() -> int:
    parser = chat_args(__doc__)
    parser.add_argument("--bash", action="store_true", help="the Bash case, on the fake model")
    args = parser.parse_args()
    log = Log("hp9-s12" if args.bash else "hp6-s12")
    boot()
    use_fake_home()
    if args.bash:
        use_fake_key()
        asyncio.run(bash_case(log))
    else:
        require_login(log)
        asyncio.run(reply_case(log, args))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
