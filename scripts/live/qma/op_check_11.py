"""Operator check 11 (`research/one-engine/04-baseline.md` section 4), HP13 lane 1.

In the ship home, a plan chat on haiku with the Agent, Bash, Glob and Read tools, in a scratch
folder holding three files, is asked: "Use a helper agent to count the files in this folder
while you tell me today's date." Asks are allowed once through the approval route. PASS when
an `agents` block shows the helper start and another shows it completed, and the last reply
holds the count (3) and today's date.

    op_check_11.py
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import time
from typing import Final

from approval_lane import ALLOW_ONCE, Host, always, answered_turn
from common import (
    SCRATCH,
    SHIP_HOME,
    Log,
    Session,
    boot,
    last_event,
    only_tools,
    require_login,
    session_blocks,
    show,
    use_fake_home,
)
from switch_lane import last_reply_text

PROMPT: Final = (
    "Use a helper agent to count the files in this folder while you tell me today's date."
)
FOLDER: Final = SCRATCH / "hp13-check11"
FILES: Final = ("alpha.txt", "beta.csv", "gamma.md")


def date_forms() -> tuple[str, ...]:
    now = time.localtime()
    return (
        time.strftime("%Y-%m-%d", now),
        f"{time.strftime('%B', now)} {now.tm_mday}",
        f"{now.tm_mday} {time.strftime('%B', now)}",
    )


async def check11(log: Log) -> None:
    from qma.harness import Harness, NewChat, QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    shutil.rmtree(FOLDER, ignore_errors=True)
    FOLDER.mkdir(parents=True)
    for name in FILES:
        (FOLDER / name).write_text("x\n", encoding="utf-8")

    only_tools(["Agent", "Bash", "Glob", "Read"])
    home = QmxHome(SHIP_HOME)
    control = control_service(home)
    harness = await Harness.open(home, control=control)
    chat = await harness.start_chat(
        NewChat(title="hp13 check 11", model="haiku", workspace=FOLDER, profile="claude")
    )
    session = Session(harness, home, control, chat)
    try:
        async with Host(session) as host:
            mark = last_event(control, chat)
            log(f"turn: {PROMPT}")
            await answered_turn(log, host, chat, always(ALLOW_ONCE), PROMPT)
            found = session_blocks(control, chat, mark)
        for block in found:
            show(log, block)
        agents = [b["content"] for b in found if b["type"] == "agents"]
        started = [a for a in agents if a.get("state") == "working"]
        finished = [a for a in agents if a.get("state") == "completed"]
        reply = str(last_reply_text(session.transcript()))
        log(f"last reply: {reply!r}")
        log.check(
            "an agents block shows the helper start and finish",
            bool(started) and bool(finished),
            (len(started), len(finished)),
        )
        dates = date_forms()
        has_count = "3" in reply or "three" in reply.lower()
        has_date = any(form.lower() in reply.lower() for form in dates)
        log.check(
            "the answer holds both facts (3 files and today's date)",
            has_count and has_date,
            (has_count, has_date, dates),
        )
    finally:
        await harness.close()


def main() -> int:
    log = Log("hp13-check11")
    boot()
    use_fake_home()
    require_login(log)
    asyncio.run(check11(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
