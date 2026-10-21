"""`Harness.run_turn`: the handle's events and result, a send that waits for a slot, a turn cut
by a restart, and the stuck rules run over a turn's events."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
import test_chat
from claude_agent_sdk import (
    AssistantMessage,
    Message,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)
from test_chat import FakeClient, blocks, result, run, settle, turn_of
from test_table import budgets

import qma.harness.harness
from qma.harness import (
    Background,
    Compaction,
    Harness,
    InjectedText,
    NewChat,
    Projected,
    QmxHome,
    Queued,
    SessionId,
    ToolCall,
    TurnEvent,
    TurnTokens,
    watch_turn,
)

home = test_chat.home

USAGE = {
    "input_tokens": 4,
    "cache_creation_input_tokens": 100,
    "cache_read_input_tokens": 2000,
    "output_tokens": 50,
    "output_tokens_details": {"thinking_tokens": 30},
}


@pytest.fixture(autouse=True)
def big_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(qma.harness.harness, "machine_ram_mb", lambda: 65536)


def reply(*content: Any, message_id: str, usage: dict[str, Any] = USAGE) -> AssistantMessage:
    return AssistantMessage(
        content=list(content), model="haiku", usage=usage, message_id=message_id
    )


def one_tool_turn(_text: str) -> list[Message]:
    return [
        reply(ToolUseBlock("toolu_1", "Glob", {"pattern": "*.py"}), message_id="m1"),
        UserMessage(content=[ToolResultBlock("toolu_1", "a.py")]),
        reply(TextBlock("found a.py"), message_id="m2"),
        result(result="found a.py"),
    ]


async def background(harness: Harness, title: str) -> SessionId:
    return await harness.start_chat(NewChat(title=title, model="haiku", kind=Background()))


async def drain(events: Any) -> list[TurnEvent]:
    return [event async for event in events]


def kinds(events: list[TurnEvent]) -> list[str]:
    return [
        f"{type(e).__name__}:{e.block.type}" if isinstance(e, Projected) else type(e).__name__
        for e in events
    ]


def test_a_turns_result_equals_its_blocks(home: QmxHome) -> None:
    FakeClient.script = one_tool_turn

    async def body(harness: Harness) -> None:
        chat = await background(harness, "one tool")
        handle = await harness.run_turn(chat, InjectedText("list the python files"))
        FakeClient.made[0].go.set()
        events = await drain(handle.events())
        done = await handle.result()
        stored = blocks(home, chat)
        assert stored[0] == ("user", {"text": "list the python files"})
        assert [(b.type, b.content) for b in done.blocks] == stored[1:]
        assert kinds(events) == [
            "Started",
            "WaitingOnModel",
            "WaitingOnModel",
            "Projected:tool",
            "ToolStarted",
            "Projected:tool",
            "ToolFinished",
            "WaitingOnModel",
            "WaitingOnModel",
            "Projected:text",
        ]
        assert (done.status, done.text, done.terminal_reason) == ("ok", "found a.py", "completed")
        assert done.tools == (ToolCall("toolu_1", "Glob", {"pattern": "*.py"}, "a.py", False),)
        assert done.usage == TurnTokens(8, 100, 4000, 200, 60)
        assert done.context == 2104
        assert done.compactions == ()
        assert turn_of(home, chat) == "idle"

    run(body, home)


def test_a_send_waiting_for_a_slot_is_queued_then_runs(home: QmxHome) -> None:
    budgets(home, max_live_chats=1)

    async def body(harness: Harness) -> None:
        busy, waiting = await background(harness, "busy"), await background(harness, "waiting")
        first = await harness.run_turn(busy, InjectedText("long"))
        second = await harness.run_turn(waiting, InjectedText("next"))
        assert await second.next_event() == Queued()
        assert (len(FakeClient.made), blocks(home, waiting)) == (1, [])
        FakeClient.made[0].go.set()
        assert (await first.result()).status == "ok"
        await settle(lambda: len(FakeClient.made) == 2)
        FakeClient.made[1].go.set()
        done = await asyncio.wait_for(second.result(), 2)
        assert (done.status, done.text) == ("ok", None)
        assert [b.content for b in done.blocks] == [{"text": "echo next"}]

    run(body, home)


def test_a_turn_cut_by_a_restart_is_unknown_and_flagged_at_the_next_open(home: QmxHome) -> None:
    async def cut(harness: Harness) -> None:
        chat = await background(harness, "cut")
        handle = await harness.run_turn(chat, InjectedText("long job"))
        await harness.close()
        done = await handle.result()
        assert (done.status, done.text, done.blocks) == ("unknown", None, ())
        cut_chats.append(chat)

    async def reopened(_: Harness) -> None:
        return None

    cut_chats: list[SessionId] = []
    run(cut, home)
    run(reopened, home)
    assert blocks(home, cut_chats[0])[-1] == (
        "needs_you",
        {"reason": "the last turn ended with an unknown outcome; send a message to continue"},
    )


def test_a_compaction_reaches_the_turns_events_and_result(home: QmxHome) -> None:
    FakeClient.script = lambda _: [
        SystemMessage(subtype="compact_boundary", data={"compact_metadata": {"trigger": "auto"}}),
        reply(TextBlock("done"), message_id="m1"),
        result(result="done"),
    ]

    async def body(harness: Harness) -> None:
        chat = await background(harness, "compacting")
        handle = await harness.run_turn(chat, InjectedText("work"))
        FakeClient.made[0].go.set()
        events = await drain(handle.events())
        done = await handle.result()
        assert Compaction("auto") in events
        assert done.compactions == ("auto",)
        assert [b.type for b in done.blocks] == ["changed", "text"]

    run(body, home)


def test_the_stuck_rules_interrupt_a_turn_that_loops(home: QmxHome) -> None:
    def looping(_text: str) -> list[Message]:
        messages: list[Message] = []
        for n in range(6):
            call = f"toolu_{n}"
            messages += [
                reply(ToolUseBlock(call, "Bash", {"command": "pytest"}), message_id=f"m{n}"),
                UserMessage(content=[ToolResultBlock(call, "FAILED t.py::x", is_error=True)]),
            ]
        return messages

    FakeClient.script = looping

    async def body(harness: Harness) -> None:
        chat = await background(harness, "looping")
        handle = await harness.run_turn(chat, InjectedText("fix it"))
        FakeClient.made[0].go.set()
        verdict = await watch_turn(handle, lambda: harness.interrupt(chat))
        done = await handle.result()
        assert verdict == "loop"
        assert (done.status, len(done.tools)) == ("interrupted", 6)

    run(body, home)
