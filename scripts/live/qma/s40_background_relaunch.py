"""S40, a relaunch names background work, on the fake model. One turn of a key chat starts a
background Bash (`sleep 300`), runs a foreground `sleep 8`, then starts a second background Bash.
During the foreground sleep the chat quotes a switch from row `fake` to row `fake2`. After the
turn ends it applies that quote, then quotes again and applies.

PASS when the first warning names 1 background task, the first apply raises `QuoteStale` with 2
tasks running, the second quote names 2, and the second apply relaunches: a second CLI is live on
`fake2`, resuming the same session, and both background `sleep` processes are gone.

    s40_background_relaunch.py
"""

from __future__ import annotations

import asyncio
import contextlib
import sys
import time

from common import Log, boot, use_fake_home, use_fake_key, wait_turn
from fake_model import Turn, text, tool_use
from switch_lane import apply, fake_pair, quote


def bash(command: str, *, background: bool) -> Turn:
    tool_input = {"command": command, "description": command, "run_in_background": background}
    return Turn([tool_use("Bash", tool_input)])


SCRIPT = [
    bash("sleep 300", background=True),
    bash("sleep 8", background=False),
    bash("sleep 301", background=True),
    Turn([text("two background jobs started")]),
]


def sleepers() -> set[int]:
    """Pids of this process's descendants running either background `sleep`."""
    import psutil  # noqa: PLC0415

    found: set[int] = set()
    for proc in psutil.Process().children(recursive=True):
        with contextlib.suppress(psutil.Error):
            line = " ".join(proc.cmdline())
            if "sleep 300" in line or "sleep 301" in line:
                found.add(proc.pid)
    return found


def running(pids: set[int]) -> list[int]:
    import psutil  # noqa: PLC0415

    return sorted(pid for pid in pids if psutil.pid_exists(pid))


async def until(check: object, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if callable(check) and check():
            return True
        await asyncio.sleep(0.1)
    return False


async def run(log: Log) -> None:
    from qma.harness import OperatorText, QuoteStale  # noqa: PLC0415

    fake, session, launched = await fake_pair(
        log, "hp12-s40", SCRIPT, tools=["Bash"], mode="bypassPermissions"
    )
    chat = session.harness._chat(session.chat)
    try:
        await session.harness.send(session.chat, OperatorText("Start the jobs."))
        await until(lambda: len(chat._tasks) == 1, 60)
        first = await quote(log, session, profile="fake2")
        log.check(
            "the first warning names one background task",
            first.background_tasks == 1 and "stops 1 background task" in str(first.warning),
            first.warning,
        )
        await wait_turn(session.home, session.chat, 60)
        await until(lambda: len(chat._tasks) == 2, 30)
        log(f"tasks running after the turn: {sorted(chat._tasks)}")
        try:
            await apply(log, session, first.id)
            stale = "applied"
        except QuoteStale as error:
            stale = f"QuoteStale: {error}"
        log.check(
            "the first apply raises QuoteStale",
            stale.startswith("QuoteStale") and len(launched) == 1,
            stale,
        )
        before = sleepers()
        log(f"background sleep processes before the relaunch: {before}")
        second = await quote(log, session, profile="fake2")
        log.check(
            "the second warning names two background tasks",
            second.background_tasks == 2 and "stops 2 background tasks" in str(second.warning),
            second.warning,
        )
        await apply(log, session, second.id)
        relaunched = launched[-1].options
        log.check(
            "the second apply relaunches on fake2 with resume",
            len(launched) == 2
            and relaunched.resume == session.chat
            and chat.is_live
            and chat.record.config.profile == "fake2",
            (len(launched), relaunched.resume, chat.is_live, chat.record.config.profile),
        )
        await until(lambda: not running(before), 10)
        after = running(before)
        log.check(
            "the relaunch stopped both background jobs",
            len(before) >= 2 and not after and not chat._tasks,
            (sorted(before), after, sorted(chat._tasks)),
        )
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp12-s40")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
