"""S31, the live-chat cap, and the HP11 perf probe. Key chats on the fake model in a throwaway
home, so no plan turn and no provider credit is spent.

    s31_chat_cap.py idle   cap 2, three chats with two idle. The third send closes the least
                           recently used one. A send to the closed chat then resumes it, and
                           the model gets the earlier conversation back (recall intact).
    s31_chat_cap.py busy   cap 2, two chats mid-turn on a sleeping Bash call. A third send
                           through the turn route returns 409, and the third chat shows a
                           `needs_you` block naming both busy chats.
    s31_chat_cap.py perf   five evict-and-connect sends at the cap against five plain connects
                           below it. FAIL when the evict-and-connect median is more than 2 s
                           over the plain median. Trunk has no cap.
"""

from __future__ import annotations

import asyncio
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from approval_lane import Host
from common import (
    SCRATCH,
    Log,
    Session,
    boot,
    capture_launches,
    put_providers,
    session_blocks,
    throwaway_home,
    use_fake_home,
    use_fake_key,
    wait_turn,
)
from fake_model import FakeModel, Turn, text, tool_use
from money_lane import direct_row

WORKSPACE = SCRATCH / "hp11-s31-ws"
CODEWORD = "PLUMTREE"
PERF_LIMIT_S = 2.0
CYCLES = 5


def put_budgets(root: Path, **values: object) -> None:
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    control_service(QmxHome(root)).settings_put("budgets", dict(values))


async def fake_session(
    log: Log, slug: str, fake: FakeModel, **budgets: object
) -> tuple[Session, list[Any]]:
    from qma.harness import TestMode  # noqa: PLC0415

    root = throwaway_home(slug)
    put_providers(root, {"fake": direct_row(fake.url)})
    put_budgets(root, **budgets)
    log(f"home {root}, budgets {budgets}")
    launched = capture_launches()
    session = await Session.start(
        root,
        model="opus",
        workspace=WORKSPACE,
        title=f"{slug} a",
        test=TestMode(loopback_http_provider=True),
        profile="fake",
        mode="bypassPermissions",
        tools=["Bash"],
    )
    return session, launched


async def another(session: Session, title: str) -> str:
    from qma.harness import NewChat  # noqa: PLC0415

    return await session.harness.start_chat(
        NewChat(
            title=title, model="opus", workspace=WORKSPACE, profile="fake", mode="bypassPermissions"
        )
    )


async def turn(session: Session, chat: str, words: str) -> Any:
    from qma.harness import OperatorText  # noqa: PLC0415

    await session.harness.send(chat, OperatorText(words))
    return await wait_turn(session.home, chat, 120)


def live(session: Session) -> set[str]:
    return {sid for sid, chat in session.harness._chats.items() if chat.is_live}


def requests_for(fake: FakeModel, marker: str) -> list[str]:
    """The bodies of scripted requests whose first message holds `marker`."""
    return [
        seen.body.decode("utf-8", "replace")
        for seen in fake.requests
        if seen.scripted and marker in seen.body.decode("utf-8", "replace")
    ]


async def idle_case(log: Log) -> None:
    fake = FakeModel(
        [],
        routes={
            "CHAT-A": [Turn([text("noted")]), Turn([text("recalled")])],
            "CHAT-B": [Turn([text("b done")])],
            "CHAT-C": [Turn([text("c done")])],
        },
    ).start()
    session, launched = await fake_session(log, "hp11-s31-idle", fake, max_live_chats=2)
    try:
        first = session.chat
        second, third = await another(session, "s31 b"), await another(session, "s31 c")
        names = {first: "a", second: "b", third: "c"}
        log(f"chats {names}")
        await turn(session, first, f"CHAT-A remember the codeword {CODEWORD}.")
        await turn(session, second, "CHAT-B hello.")
        log(f"live before the third send: {sorted(names[s] for s in live(session))}")
        await turn(session, third, "CHAT-C hello.")
        now = live(session)
        alive = session.harness._deps.procs.alive(first)
        log.check(
            "the least recently used idle chat (a) closed when c connected",
            now == {second, third} and not alive,
            (sorted(names[s] for s in now), f"a's CLI alive {alive}"),
        )
        record = await turn(session, first, "CHAT-A what was the codeword?")
        resumed = [client.options.resume for client in launched][-1]
        log.check("the send to a resumed the same session", resumed == first, resumed)
        back = requests_for(fake, "CHAT-A")
        log.check(
            "a's resumed request carries the earlier conversation",
            len(back) >= 2 and CODEWORD in back[-1] and "what was the codeword" in back[-1],
            f"{len(back)} requests, codeword in last: {bool(back) and CODEWORD in back[-1]}",
        )
        texts = [
            str(block["content"])
            for block in session_blocks(session.control, first)
            if block["type"] == "text"
        ]
        log.check(
            "a answered after resuming", record.turn == "idle" and "recalled" in texts[-1], texts
        )
        log(f"live at the end: {sorted(names[s] for s in live(session))}")
    finally:
        await session.harness.close()
        fake.stop()


async def busy_case(log: Log) -> None:
    sleep = {"command": "sleep 25", "description": "wait"}
    fake = FakeModel(
        [],
        routes={
            "CHAT-A": [Turn([tool_use("Bash", sleep)]), Turn([text("a done")])],
            "CHAT-B": [Turn([tool_use("Bash", sleep)]), Turn([text("b done")])],
            "CHAT-C": [Turn([text("c done")])],
        },
    ).start()
    session, _ = await fake_session(log, "hp11-s31-busy", fake, max_live_chats=2)
    try:
        from qma.harness import OperatorText  # noqa: PLC0415

        first = session.chat
        second, third = await another(session, "s31 b"), await another(session, "s31 c")
        names = {first: "a", second: "b", third: "c"}
        log(f"chats {names}")
        await session.harness.send(first, OperatorText("CHAT-A run the sleep."))
        await session.harness.send(second, OperatorText("CHAT-B run the sleep."))
        await asyncio.sleep(3)
        async with Host(session) as host:
            answer = await host.http.post(
                f"/api/sessions/{third}/turns", json={"text": "CHAT-C hello."}
            )
        body = answer.json()
        log(f"third send: {answer.status_code} {body}")
        log.check(
            "the third send returns 409 chat_table_full",
            answer.status_code == 409 and body["error"]["code"] == "chat_table_full",
            (answer.status_code, body.get("error", {}).get("code")),
        )
        needs = [
            block["content"]
            for block in session_blocks(session.control, third)
            if block["type"] == "needs_you"
        ]
        log(f"c's needs_you blocks: {needs}")
        log.check(
            "c shows a needs_you block naming both busy chats",
            len(needs) == 1 and sorted(needs[0].get("busy", [])) == sorted([first, second]),
            needs,
        )
        log.check(
            "nothing queued: c never started a CLI", third not in live(session), live(session)
        )
        records = await asyncio.gather(
            wait_turn(session.home, first, 120), wait_turn(session.home, second, 120)
        )
        log(f"a and b after their sleeps: {[record.turn for record in records]}")
        record = await turn(session, third, "CHAT-C hello.")
        log.check("c connects once a chat is idle", record.turn == "idle", record.turn)
    finally:
        await session.harness.close()
        fake.stop()


async def perf_case(log: Log) -> None:
    fake = FakeModel([], every_request=False).start()
    session, _ = await fake_session(log, "hp11-s31-perf", fake, max_live_chats=1)
    try:
        await turn(session, session.chat, "warm up")
        evict: list[float] = []
        evictions = 0
        for n in range(CYCLES):
            before = live(session)
            chat = await another(session, f"evict {n}")
            started = time.perf_counter()
            await turn_send(session, chat)
            evict.append(time.perf_counter() - started)
            evictions += len(before) == 1 and live(session) == {chat}
            await wait_turn(session.home, chat, 120)
        log.check("every evict cycle closed the one live chat", evictions == CYCLES, evictions)
        put_budgets(session.home.root, max_live_chats=CYCLES + 4)
        plain: list[float] = []
        for n in range(CYCLES):
            chat = await another(session, f"plain {n}")
            started = time.perf_counter()
            await turn_send(session, chat)
            plain.append(time.perf_counter() - started)
            await wait_turn(session.home, chat, 120)
        evicted, connected = statistics.median(evict), statistics.median(plain)
        log("trunk: no live-chat cap, so no eviction path to compare")
        log(f"evict-and-connect s: {[round(t, 2) for t in evict]} median {evicted:.2f}")
        log(f"plain connect s:     {[round(t, 2) for t in plain]} median {connected:.2f}")
        log.check(
            f"evict-and-connect median within {PERF_LIMIT_S} s of plain connect",
            evicted - connected <= PERF_LIMIT_S,
            f"{evicted - connected:+.2f} s",
        )
    finally:
        await session.harness.close()
        fake.stop()


async def turn_send(session: Session, chat: str) -> None:
    from qma.harness import OperatorText  # noqa: PLC0415

    await session.harness.send(chat, OperatorText("hello"))


PARTS = {"idle": idle_case, "busy": busy_case, "perf": perf_case}


def main() -> int:
    part = sys.argv[1] if len(sys.argv) > 1 else ""
    if part not in PARTS:
        raise SystemExit(f"usage: s31_chat_cap.py {{{'|'.join(PARTS)}}}")
    log = Log(f"hp11-s31-{part}")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(PARTS[part](log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
