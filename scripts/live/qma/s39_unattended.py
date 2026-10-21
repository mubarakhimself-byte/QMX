"""S39, unattended asks end. Key chats on the fake model in a throwaway home, with
`max_live_chats` = 2 and `unattended_ask_seconds` = 5.

Two Background chats each reach a Bash call that asks (`mkdir`, default mode) and nobody
answers. PASS when both asks are rejected and their blocks show `expired`, neither Bash call ran,
both chats finish their turns, and an Interactive chat then connects at the cap.

    s39_unattended.py
"""

from __future__ import annotations

import asyncio
import sys

from common import (
    SCRATCH,
    Log,
    Session,
    boot,
    put_providers,
    session_blocks,
    throwaway_home,
    use_fake_home,
    use_fake_key,
    wait_turn,
)
from fake_model import FakeModel, Turn, text, tool_use
from money_lane import direct_row
from s31_chat_cap import live, put_budgets

ASK_S = 5
WORKSPACE = SCRATCH / "hp11-s39-ws"


async def run(log: Log) -> None:
    from qma.harness import InjectedText, NewChat, OperatorText, TestMode  # noqa: PLC0415
    from qma.harness.launch import Background  # noqa: PLC0415

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    made = {name: WORKSPACE / f"s39-{name}" for name in ("a", "b")}
    for folder in made.values():
        if folder.exists():
            folder.rmdir()
    fake = FakeModel(
        [],
        routes={
            f"CHAT-{name.upper()}": [
                Turn([tool_use("Bash", {"command": f"mkdir {folder.as_posix()}"})]),
                Turn([text(f"{name} finished")]),
            ]
            for name, folder in made.items()
        }
        | {"CHAT-I": [Turn([text("interactive here")])]},
    ).start()
    root = throwaway_home("hp11-s39")
    put_providers(root, {"fake": direct_row(fake.url)})
    put_budgets(root, max_live_chats=2, interactive_reserve=0, unattended_ask_seconds=ASK_S)
    session = await Session.start(
        root,
        model="opus",
        workspace=WORKSPACE,
        title="s39 interactive",
        test=TestMode(loopback_http_provider=True),
        profile="fake",
        mode="default",
        tools=["Bash"],
    )
    try:
        background = {
            name: await session.harness.start_chat(
                NewChat(
                    title=f"s39 {name}",
                    model="opus",
                    workspace=WORKSPACE,
                    profile="fake",
                    kind=Background(),
                )
            )
            for name in made
        }
        for name, chat in background.items():
            await session.harness.send(chat, InjectedText(f"CHAT-{name.upper()} make the folder."))
        records = await asyncio.gather(
            *(wait_turn(session.home, chat, ASK_S + 60) for chat in background.values())
        )
        for (name, chat), record in zip(background.items(), records, strict=True):
            asks = [
                block["content"]
                for block in session_blocks(session.control, chat)
                if block["type"] == "permission"
            ]
            log(f"{name}: turn {record.turn}, permission blocks {asks}")
            states = [ask.get("state") for ask in asks]
            log.check(
                f"{name}: the ask was rejected and shows expired",
                states == ["asking", "expired"],
                states,
            )
            log.check(f"{name}: the Bash call never ran", not made[name].exists(), made[name])
            texts = [
                str(block["content"])
                for block in session_blocks(session.control, chat)
                if block["type"] == "text"
            ]
            log.check(
                f"{name}: the chat finished its turn",
                record.turn == "idle" and any(f"{name} finished" in t for t in texts),
                (record.turn, texts),
            )
        log(f"live before the Interactive send: {len(live(session))}")
        await session.harness.send(session.chat, OperatorText("CHAT-I hello."))
        record = await wait_turn(session.home, session.chat, 60)
        log.check(
            "the Interactive chat connects at the cap",
            record.turn == "idle" and session.chat in live(session) and len(live(session)) == 2,
            (record.turn, len(live(session))),
        )
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp11-s39")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
