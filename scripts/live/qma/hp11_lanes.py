"""HP11 lanes 7, 9 and 10. Plan turns run on the ship home's login on haiku; its
`[budgets]` are restored as found, and lane 10 ends on a clean fact so the home holds no stop.

    hp11_lanes.py cap        lane 7, the S10 cap part. An Interactive plan turn gives a
                             five-hour reading; `background_cap` is set below it. PASS when a
                             Background send is refused with a `needs_you` block naming the cap
                             and an Interactive send still runs.
    hp11_lanes.py options    lane 9, fake model. PASS when only the Background chat's options set
                             `verbatim_prompts`, `max_turns` and `max_budget_usd`.
    hp11_lanes.py hardstop   lane 10, in-process. A Background plan chat runs `sleep 40`; a rule 2
                             overage fact is fed. PASS when the chat's CLI ends, it shows a
                             `needs_you` block naming the rule, and a clean fact then leaves no
                             stop in the saved ledger.
"""

from __future__ import annotations

import asyncio
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from common import (
    MODEL,
    SCRATCH,
    SHIP_HOME,
    Log,
    Session,
    boot,
    last_event,
    require_login,
    session_blocks,
    use_fake_home,
    use_fake_key,
    wait_turn,
)
from fake_model import FakeModel, Turn, text
from s10_usage import CLEAN, STOPS, feed, until_tool
from s31_chat_cap import WORKSPACE as FAKE_WS
from s31_chat_cap import fake_session

WORKSPACE = SCRATCH / "hp11-lanes-ws"


@asynccontextmanager
async def ship_budgets(session: Session, log: Log, **values: object) -> AsyncIterator[None]:
    control = session.control
    found = dict(control.settings_get("budgets"))
    control.settings_put("budgets", found | values)
    log(f"ship home [budgets] {found} -> {found | values}")
    try:
        yield
    finally:
        control.settings_put("budgets", found)
        log(f"ship home [budgets] restored to {dict(control.settings_get('budgets'))}")


async def background(session: Session, title: str) -> str:
    from qma.harness import NewChat  # noqa: PLC0415
    from qma.harness.launch import Background  # noqa: PLC0415

    return await session.harness.start_chat(
        NewChat(
            title=title,
            model=MODEL,
            workspace=WORKSPACE,
            kind=Background(),
            mode="bypassPermissions",
        )
    )


async def cap(log: Log) -> None:
    from qma.harness import InjectedText, LaunchRefused  # noqa: PLC0415

    session = await Session.start(
        SHIP_HOME, model=MODEL, workspace=WORKSPACE, title="hp11 lane 7 operator", tools=[]
    )
    try:
        await session.turn(log, "Reply with the single word FIRSTOK.")
        reading = session.harness._ledger.reading("five_hour")
        log(f"five-hour reading after the Interactive turn: {reading}")
        if reading is None or reading.reading.utilization <= 0:
            log.check("a five-hour reading above 0 exists to set the cap under", False, reading)
            return
        used = reading.reading.utilization
        async with ship_budgets(session, log, background_cap=round(used / 2, 4)):
            news = await background(session, "hp11 lane 7 news")
            try:
                await session.harness.send(news, InjectedText("Reply with NEWSOK."))
                refused = None
            except LaunchRefused as error:
                refused = str(error)
            log(f"Background send: {refused or 'sent'}")
            needs = [
                block["content"]["reason"]
                for block in session_blocks(session.control, news)
                if block["type"] == "needs_you"
            ]
            log.check(
                "the Background send is refused naming the cap",
                refused is not None and "background cap" in refused and needs == [refused],
                (refused, needs),
            )
            log.check(
                "the refused Background chat started no CLI",
                not session.harness._chat(news).is_live,
                session.harness._chat(news).is_live,
            )
            _, found = await session.turn(log, "Reply with the single word SECONDOK.")
            texts = [str(b["content"]) for b in found if b["type"] == "text"]
            log.check("an Interactive send still runs", any("SECONDOK" in t for t in texts), texts)
    finally:
        await session.harness.close()


async def options(log: Log) -> None:
    from qma.harness import InjectedText, OperatorText  # noqa: PLC0415

    fake = FakeModel(
        [], routes={"CHAT-I": [Turn([text("i")])], "CHAT-B": [Turn([text("b")])]}
    ).start()
    session, launched = await fake_session(log, "hp11-options", fake)
    try:
        from qma.harness import NewChat  # noqa: PLC0415
        from qma.harness.launch import Background  # noqa: PLC0415

        news = await session.harness.start_chat(
            NewChat(
                title="news", model="opus", workspace=FAKE_WS, profile="fake", kind=Background()
            )
        )
        await session.harness.send(session.chat, OperatorText("CHAT-I hello"))
        await wait_turn(session.home, session.chat, 60)
        await session.harness.send(news, InjectedText("CHAT-B hello"))
        await wait_turn(session.home, news, 60)
        seen: dict[str, tuple[Any, ...]] = {}
        for name, client in zip(("interactive", "background"), launched, strict=True):
            opts = client.options
            seen[name] = (opts.verbatim_prompts, opts.max_turns, opts.max_budget_usd)
            log(
                f"{name}: verbatim_prompts={opts.verbatim_prompts} max_turns={opts.max_turns} "
                f"max_budget_usd={opts.max_budget_usd} permission_mode={opts.permission_mode}"
            )
        log.check(
            "only the Background chat sets verbatim_prompts, max_turns and max_budget_usd",
            seen == {"interactive": (False, None, None), "background": (True, 50, 5.0)},
            seen,
        )
    finally:
        await session.harness.close()
        fake.stop()


async def hardstop(log: Log) -> None:
    from qma.harness import InjectedText  # noqa: PLC0415
    from qma.harness.usage import UsageLedger  # noqa: PLC0415

    rule, info, clear = STOPS["overage"][0]
    session = await Session.start(
        SHIP_HOME, model=MODEL, workspace=WORKSPACE, title="hp11 lane 10", tools=["Bash"]
    )
    try:
        async with ship_budgets(session, log, background_cap=1):
            feed(session, log, {**CLEAN, "rateLimitType": "five_hour", "utilization": 0.1})
            news = await background(session, "hp11 lane 10 news")
            session.chat = news
            mark = last_event(session.control, news)
            await session.harness.send(
                news, InjectedText("Run this exact Bash command, then reply done: sleep 40")
            )
            log.check(
                "a Background plan turn is running a tool", await until_tool(session, mark), True
            )
            fed = time.monotonic()
            feed(session, log, info)
            record = await wait_turn(session.home, news, 30)
            took = time.monotonic() - fed
            await asyncio.sleep(3)
            found = session_blocks(session.control, news, mark)
            reasons = [b["content"]["reason"] for b in found if b["type"] == "needs_you"]
            log(f"needs_you after the feed: {reasons}")
            alive = session.harness._deps.procs.alive(news)
            log.check(
                "the Background chat was interrupted, its CLI ended",
                record.turn == "idle" and took < 30 and not alive,
                (record.turn, f"{took:.1f} s", f"CLI alive {alive}"),
            )
            log.check(
                "it shows a needs_you block with the reason",
                any(rule in reason and "plan use stopped" in reason for reason in reasons),
                reasons,
            )
            feed(session, log, clear)
            held = session.harness._ledger.hard_stop()
            saved = UsageLedger(path=session.home.state_dir / "plan-usage.json").hard_stop()
            log.check(
                "a clean fact leaves no stop, in memory or in the saved ledger",
                held is None and saved is None,
                (held, saved),
            )
    finally:
        await session.harness.close()


PARTS = {"cap": cap, "options": options, "hardstop": hardstop}


def main() -> int:
    part = sys.argv[1] if len(sys.argv) > 1 else ""
    if part not in PARTS:
        raise SystemExit(f"usage: hp11_lanes.py {{{'|'.join(PARTS)}}}")
    log = Log(f"hp11-{part}")
    boot()
    use_fake_home()
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    if part == "options":
        use_fake_key()
    else:
        require_login(log)
    asyncio.run(PARTS[part](log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
