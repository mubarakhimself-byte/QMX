"""S15, the event wire and answers, on the fake model. Every answer goes through
`POST /api/approvals/{ask_id}` on a loopback host of the harness routes.

    wire        One turn with text, a TodoWrite, a sub-agent and a Bash call that asks. The
                check reads `GET /api/events/sessions` as SSE. PASS when `text`, `tool`, `plan`,
                `agents` and `permission` blocks arrive in that order, an answer without the
                operator credential gets 401, the answer with it is `resolved`, and a second
                answer is `already_answered`.
    restart     A chat asks, the harness closes and a new harness opens on the same home.
                PASS when the open ask's call is denied and the answer after the restart is
                `expired`.
    concurrent  Three chats each make parallel Bash calls that ask. PASS when the check fires
                one answer per ask at once, 50 in all, and every answer is `resolved`.
    question    The fake model calls AskUserQuestion. PASS when the `question` block resolves
                with `Answers` and the next model request carries the chosen answer.

    s15_event_wire.py wire|restart|concurrent|question
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from approval_lane import ALLOW_ONCE, PROMPT, Host, fake_session, new_chat
from common import (
    SCRATCH,
    Log,
    Session,
    boot,
    session_blocks,
    use_fake_home,
    use_fake_key,
    wait_turn,
)
from fake_model import Turn, text, tool_use
from money_lane import results

AGENT_PROMPT = "QMA sub-agent: say done."
ORDER = ["text", "tool", "plan", "agents", "permission"]
ASK_WAIT_S = 120.0


def bash(command: str) -> dict[str, Any]:
    return tool_use("Bash", {"command": command, "description": "scripted"})


def open_asks(session: Session, chat: str) -> list[dict[str, Any]]:
    blocks = session_blocks(session.control, chat)
    settled = {block["content"].get("ask") for block in blocks}
    return [
        block
        for block in blocks
        if block["content"].get("state") == "asking" and block["seq"] not in settled
    ]


async def asks_open(
    session: Session, chat: str, count: int = 1, skip: frozenset[int] = frozenset()
) -> list[dict[str, Any]]:
    """The open asks of `chat` not in `skip` once at least `count` are open, or what is open at
    the wait."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + ASK_WAIT_S
    while True:
        found = [
            ask
            for ask in await asyncio.to_thread(open_asks, session, chat)
            if ask["seq"] not in skip
        ]
        if len(found) >= count or loop.time() > deadline:
            return found
        await asyncio.sleep(0.05)


async def send(session: Session, chat: str, prompt: str = PROMPT) -> asyncio.Task[Any]:
    from qma.harness import OperatorText  # noqa: PLC0415

    await session.harness.send(chat, OperatorText(prompt))
    return asyncio.create_task(wait_turn(session.home, chat))


async def wire(log: Log) -> None:
    todo = tool_use(
        "TodoWrite",
        {"todos": [{"content": "check", "status": "pending", "activeForm": "checking"}]},
    )
    agent = tool_use(
        "Agent",
        {
            "description": "Say done",
            "prompt": AGENT_PROMPT,
            "subagent_type": "general-purpose",
            "run_in_background": False,
        },
    )
    script = [
        Turn([text("starting"), todo]),
        Turn([agent]),
        Turn([bash("touch s15.txt")]),
        Turn([text("done")]),
    ]
    _, fake, session = await fake_session(
        "hp9-s15-wire",
        script,
        tools=["TodoWrite", "Agent", "Bash"],
        routes={AGENT_PROMPT: [Turn([text("agent done")])]},
    )
    seen: list[str] = []
    try:
        async with Host(session) as host:

            async def read() -> None:
                async for _, event in host.stream(session.chat):
                    data = event.get("data", event)
                    if data.get("type") == "block":
                        seen.append(data["block"]["type"])

            reader = asyncio.create_task(read())
            turn = await send(session, session.chat)
            [ask] = await asks_open(session, session.chat)
            ask_id = f"{session.chat}.{ask['seq']}"
            bare = await host.answer_without_credential(ask_id, ALLOW_ONCE)
            first = await host.answer(ask_id, ALLOW_ONCE)
            second = await host.answer(ask_id, ALLOW_ONCE)
            record = await turn
            await asyncio.sleep(0.5)
            reader.cancel()
    finally:
        await session.harness.close()
        fake.stop()
    log(f"  block types on the stream: {seen}")
    firsts = [seen.index(kind) if kind in seen else -1 for kind in ORDER]
    log.check(
        "text, tool, plan, agents and permission arrived in order",
        -1 not in firsts and firsts == sorted(firsts),
        dict(zip(ORDER, firsts, strict=True)),
    )
    log.check("an answer without the operator credential is refused", bare == 401, bare)
    log.check("the answer is resolved", first == "resolved", first)
    log.check("a second answer is already_answered", second == "already_answered", second)
    log.check("the turn ended", record.turn == "idle", record.turn)


async def restart(log: Log) -> None:
    from qma.harness import Harness, TestMode  # noqa: PLC0415

    script = [Turn([bash("touch s15-restart.txt")]), Turn([text("done")])]
    _, fake, session = await fake_session("hp9-s15-restart", script, tools=["Bash"])
    try:
        turn = await send(session, session.chat)
        [ask] = await asks_open(session, session.chat)
        ask_id = f"{session.chat}.{ask['seq']}"
        await session.harness.close()
        turn.cancel()
        settled = session_blocks(session.control, session.chat)[-3:]
        log(f"  last blocks: {[(b['type'], b['content']) for b in settled]}")
        session.harness = await Harness.open(
            session.home, control=session.control, test=TestMode(loopback_http_provider=True)
        )
        async with Host(session) as host:
            after = await host.answer(ask_id, ALLOW_ONCE)
    finally:
        await session.harness.close()
        fake.stop()
    log.check(
        "the open ask was settled as expired when its process ended",
        any(b["content"] == {"ask": ask["seq"], "state": "expired"} for b in settled),
        settled,
    )
    log.check("the answer after the restart is expired", after == "expired", after)


CHATS = 3
PER_CHAT = (17, 17, 16)


async def concurrent(log: Log) -> None:
    def turn_of(chat: int) -> Turn:
        return Turn([bash(f"touch c{chat}-{i}.txt") for i in range(PER_CHAT[chat])])

    routes = {f"chat-{i}": [turn_of(i), Turn([text("done")])] for i in range(CHATS)}
    _, fake, session = await fake_session("hp9-s15-concurrent", [], tools=["Bash"], routes=routes)
    statuses: list[str] = []
    widest = 0
    try:
        chats = [session.chat]
        for index in range(1, CHATS):
            chats.append(
                await new_chat(session, f"s15 concurrent {index}", SCRATCH / f"hp9-s15-c{index}")
            )
        async with Host(session) as host:
            turns = [
                await send(session, chat, f"{PROMPT} chat-{index}")
                for index, chat in enumerate(chats)
            ]
            left = dict(zip(chats, PER_CHAT, strict=True))
            answered: dict[str, frozenset[int]] = dict.fromkeys(chats, frozenset())
            while any(left.values()):
                waiting = [chat for chat, count in left.items() if count]
                found = await asyncio.gather(
                    *(asks_open(session, chat, skip=answered[chat]) for chat in waiting)
                )
                ids = [
                    f"{chat}.{ask['seq']}"
                    for chat, open_ in zip(waiting, found, strict=True)
                    for ask in open_
                ]
                log(f"  round: {[len(open_) for open_ in found]} open")
                if not ids:
                    break
                widest = max(widest, len(ids))
                statuses += await asyncio.gather(
                    *(host.answer(ask_id, ALLOW_ONCE) for ask_id in ids)
                )
                for chat, open_ in zip(waiting, found, strict=True):
                    left[chat] -= len(open_)
                    answered[chat] |= {ask["seq"] for ask in open_}
            records = await asyncio.gather(*turns)
    finally:
        await session.harness.close()
        fake.stop()
    log(f"  at most {widest} asks were open at once; the CLI asks one call at a time per chat")
    log.check(
        f"{sum(PER_CHAT)} answers fired in rounds across {CHATS} chats all resolved",
        statuses == ["resolved"] * sum(PER_CHAT),
        {status: statuses.count(status) for status in set(statuses)},
    )
    log.check(
        "every chat's turn ended", all(r.turn == "idle" for r in records), [r.turn for r in records]
    )


QUESTION = "Which colour?"


async def question(log: Log) -> None:
    from qma.harness import TestMode  # noqa: PLC0415

    ask_input = {
        "questions": [
            {
                "question": QUESTION,
                "header": "Colour",
                "options": [
                    {"label": "red", "description": "Red"},
                    {"label": "blue", "description": "Blue"},
                ],
                "multiSelect": False,
            }
        ]
    }
    script = [Turn([tool_use("AskUserQuestion", ask_input)]), Turn([text("done")])]
    _, fake, session = await fake_session(
        "hp9-s15-question",
        script,
        tools=["AskUserQuestion"],
        test=TestMode(loopback_http_provider=True),
    )
    try:
        async with Host(session) as host:
            turn = await send(session, session.chat)
            [ask] = await asks_open(session, session.chat)
            ask_id = f"{session.chat}.{ask['seq']}"
            wrong = await host.answer(ask_id, ALLOW_ONCE)
            status = await host.answer(
                ask_id, {"decision": "answers", "answers": {QUESTION: "blue"}}
            )
            record = await turn
        blocks = session_blocks(session.control, session.chat)
    finally:
        await session.harness.close()
        fake.stop()
    log.check("the ask is a question block", ask["type"] == "question", ask["type"])
    log.check("a tool answer to a question is invalid", wrong == "invalid", wrong)
    log.check("Answers resolved it", status == "resolved", status)
    log.check(
        "the question block shows answered",
        any(b["content"] == {"ask": ask["seq"], "state": "answered"} for b in blocks),
        [b["content"] for b in blocks[-3:]],
    )
    [(_, _, is_error, said)] = results(fake).values()
    log.check(
        "the next request carries the chosen answer",
        not is_error and f'"{QUESTION}"="blue"' in said,
        said,
    )
    log.check("the turn ended", record.turn == "idle", record.turn)


LANES = {"wire": wire, "restart": restart, "concurrent": concurrent, "question": question}


def main() -> int:
    lane = sys.argv[1] if len(sys.argv) > 1 else ""
    if lane not in LANES:
        raise SystemExit(f"usage: s15_event_wire.py {'|'.join(LANES)}")
    log = Log(f"hp9-s15-{lane}")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(LANES[lane](log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
