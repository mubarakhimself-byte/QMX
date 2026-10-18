"""S32, reaping spares busy chats, and HP11 lane 8. Key chats on the fake model in a throwaway
home with `idle_reap_seconds` = 4.

Chat a starts a background Bash (`sleep 40`, `run_in_background`) and ends its turn. Chat b ends
a plain turn. PASS when, well past `idle_reap_seconds`, b is closed and a is still live with its
background task running; when a send to b then resumes the same session id; and when a is
reaped only after its background task finishes.

    s32_reaping.py
"""

from __future__ import annotations

import asyncio
import sys
import time

from common import Log, boot, use_fake_home, use_fake_key, wait_turn
from fake_model import FakeModel, Turn, text, tool_use
from s31_chat_cap import another, fake_session, live, turn

REAP_S = 4
SLEEP_S = 40


async def run(log: Log) -> None:
    from qma.harness import OperatorText  # noqa: PLC0415

    background = {
        "command": f"sleep {SLEEP_S}",
        "description": "long job",
        "run_in_background": True,
    }
    fake = FakeModel(
        [],
        routes={
            "CHAT-A": [Turn([tool_use("Bash", background)]), Turn([text("job started")])],
            "CHAT-B": [Turn([text("b done")]), Turn([text("b again")])],
        },
    ).start()
    session, launched = await fake_session(log, "hp11-s32", fake, idle_reap_seconds=REAP_S)
    try:
        worker, idle = session.chat, await another(session, "s32 b")
        names = {worker: "a", idle: "b"}
        await turn(session, worker, "CHAT-A start the long job in the background.")
        await turn(session, idle, "CHAT-B hello.")
        chat = session.harness._chat(worker)
        log(f"a's running tasks after its turn: {sorted(chat._tasks)}")
        await asyncio.sleep(REAP_S * 3)
        now = live(session)
        log(f"live {REAP_S * 3} s later: {sorted(names[s] for s in now)}")
        log.check(
            "a, with a running background Bash, is not reaped",
            worker in now and bool(chat._tasks) and session.harness._deps.procs.alive(worker),
            (sorted(names[s] for s in now), sorted(chat._tasks)),
        )
        log.check("b, idle past idle_reap_seconds, was reaped", idle not in now, sorted(now))
        record = await turn(session, idle, "CHAT-B are you back?")
        resumed = launched[-1].options.resume
        log.check(
            "lane 8: the send to the reaped chat resumes the same session id",
            resumed == idle and record.turn == "idle",
            (resumed, record.turn),
        )
        deadline = time.monotonic() + SLEEP_S + 30
        while worker in live(session) and time.monotonic() < deadline:
            await asyncio.sleep(1)
        await wait_turn(session.home, worker, 30)
        log.check(
            "a is reaped once its background task ends",
            worker not in live(session),
            sorted(names[s] for s in live(session)),
        )
        await session.harness.send(worker, OperatorText("CHAT-A done?"))
        await wait_turn(session.home, worker, 60)
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp11-s32")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
