from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any, ClassVar, cast

import pytest
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    Message,
    PermissionResultDeny,
    ResultMessage,
    TextBlock,
)
from claude_agent_sdk.types import ToolPermissionContext

import qma.harness.chat
from qma.harness import Harness, LaunchRefused, NewChat, OperatorText, QmxHome, SessionId
from qma.harness.home import PlanAuth, read_record, write_record
from qma.harness.routes import control_service

SIGNED_IN = PlanAuth(logged_in=True, method="claude.ai", provider="firstParty", subscription="max")


class FakeClient:
    """Stands in for `ClaudeSDKClient`: answers each query with `replies`, released by `go`."""

    made: ClassVar[list[FakeClient]] = []
    commands: ClassVar[list[dict[str, Any]]] = []

    def __init__(self, options: ClaudeAgentOptions) -> None:
        self.options = options
        self.inbox: asyncio.Queue[Message | None] = asyncio.Queue()
        self.go = asyncio.Event()
        self.disconnected = False
        FakeClient.made.append(self)

    async def connect(self) -> None:
        return None

    async def get_server_info(self) -> dict[str, Any]:
        return {"commands": FakeClient.commands, "agents": [{"name": "Explore"}]}

    async def get_mcp_status(self) -> dict[str, list[dict[str, Any]]]:
        return {"mcpServers": []}

    async def query(self, text: str) -> None:
        async def answer() -> None:
            await self.go.wait()
            for reply in replies(text):
                self.inbox.put_nowait(reply)

        asyncio.get_running_loop().create_task(answer())

    async def receive_messages(self) -> AsyncIterator[Message]:
        while (message := await self.inbox.get()) is not None:
            yield message

    async def interrupt(self) -> None:
        return None

    async def disconnect(self) -> None:
        self.disconnected = True
        self.inbox.put_nowait(None)


def replies(text: str) -> list[Message]:
    return [
        AssistantMessage(content=[TextBlock(f"echo {text}")], model="haiku"),
        ResultMessage(
            subtype="success",
            duration_ms=5,
            duration_api_ms=5,
            is_error=False,
            num_turns=1,
            session_id="s",
            terminal_reason="completed",
        ),
    ]


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> QmxHome:
    for name in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(name, str(tmp_path / "throwaway"))
    monkeypatch.setattr(qma.harness.chat, "ClaudeSDKClient", FakeClient)
    monkeypatch.setattr(qma.harness.chat, "plan_auth_method", lambda *_: SIGNED_IN)  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
    FakeClient.made = []
    FakeClient.commands = [{"name": "compact", "builtin": True}, {"name": "qmx:qmx-overview"}]
    return QmxHome(tmp_path / "qmx")


def run(body: Callable[[Harness], Awaitable[None]], home: QmxHome) -> None:
    async def main() -> None:
        harness = await Harness.open(home, control=control_service(home))
        try:
            await body(harness)
        finally:
            await harness.close()

    asyncio.run(main())


def blocks(home: QmxHome, chat: str) -> list[tuple[str, dict[str, Any]]]:
    events = cast("list[dict[str, Any]]", control_service(home).events("sessions", 0, chat, 1000))
    return [
        (event["data"]["block"]["type"], event["data"]["block"]["content"])
        for event in events
        if event["data"].get("type") == "block"
    ]


async def settle(check: Callable[[], bool]) -> None:
    for _ in range(200):
        if check():
            return
        await asyncio.sleep(0.01)


def plant_transcript(home: QmxHome, chat: str) -> Path:
    path = home.plan_dir / "projects" / "D--work" / f"{chat}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"type":"user"}\n', encoding="utf-8")
    return path


def test_started_turns_true_only_on_the_first_result(home: QmxHome) -> None:
    seen: list[tuple[str, bool]] = []

    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="t", model="haiku"))
        await harness.send(chat, OperatorText("hello"))
        record = read_record(home, chat)
        assert record is not None
        seen.append((record.turn, record.started))
        FakeClient.made[0].go.set()
        await settle(lambda: getattr(read_record(home, chat), "turn", "") == "idle")
        record = read_record(home, chat)
        assert record is not None
        seen.append((record.turn, record.started))
        assert blocks(home, chat) == [("user", {"text": "hello"}), ("text", {"text": "echo hello"})]

    run(body, home)
    assert seen == [("running", False), ("idle", True)]


def test_the_resume_table_follows_the_transcript_on_disk(home: QmxHome) -> None:
    picked: list[tuple[str | None, str | None]] = []

    async def body(harness: Harness) -> None:
        fresh = await harness.start_chat(NewChat(title="fresh", model="haiku"))
        partial = await harness.start_chat(NewChat(title="partial", model="haiku"))
        plant_transcript(home, partial)
        for chat in (fresh, partial):
            await harness.send(chat, OperatorText("hi"))
        picked.extend((c.options.session_id, c.options.resume) for c in FakeClient.made)
        assert picked == [(fresh, None), (None, partial)]

    run(body, home)
    assert len(picked) == 2


def test_a_started_chat_whose_transcript_is_gone_is_refused(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="gone", model="haiku"))
        record = read_record(home, chat)
        assert record is not None
        write_record(home, record.__class__(chat, record.config, started=True, turn="idle"))
        with pytest.raises(LaunchRefused, match="transcript is gone"):
            await harness.send(chat, OperatorText("hi"))
        assert FakeClient.made == []
        assert blocks(home, chat) == [
            (
                "needs_you",
                {"reason": "this chat's transcript is gone from the plan home; start a new chat"},
            )
        ]

    run(body, home)


def test_a_record_left_running_yields_one_needs_you_block_at_open(home: QmxHome) -> None:
    holder: list[SessionId] = []

    async def first(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="crashed", model="haiku"))
        record = read_record(home, chat)
        assert record is not None
        write_record(home, record.__class__(chat, record.config, started=True, turn="running"))
        holder.append(chat)

    async def again(_: Harness) -> None:
        return None

    run(first, home)
    run(again, home)
    run(again, home)
    chat = holder[0]
    record = read_record(home, chat)
    assert (record.turn if record else None) == "idle"
    assert blocks(home, chat) == [
        (
            "needs_you",
            {"reason": "the last turn ended with an unknown outcome; send a message to continue"},
        )
    ]


def test_the_floor_rejects_every_call_that_would_ask_and_shows_it(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="floor", model="haiku"))
        await harness.send(chat, OperatorText("write a file"))
        ask = FakeClient.made[0].options.can_use_tool
        assert ask is not None
        context = ToolPermissionContext(signal=None, suggestions=[])
        answer = await ask("Write", {"file_path": "hello.txt", "content": "hi"}, context)
        assert answer == PermissionResultDeny(message="approvals are not wired yet")
        assert blocks(home, chat)[-1] == (
            "permission",
            {
                "tool": "Write",
                "input": {"file_path": "hello.txt", "content": "hi"},
                "state": "rejected",
                "reason": "approvals are not wired yet",
            },
        )

    run(body, home)


def test_a_plugin_besides_qmx_closes_the_chat_before_its_first_prompt(home: QmxHome) -> None:
    FakeClient.commands = [*FakeClient.commands, {"name": "planted:mod-check"}]

    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="planted", model="haiku"))
        with pytest.raises(LaunchRefused, match="command planted:mod-check"):
            await harness.send(chat, OperatorText("hi"))
        assert FakeClient.made[0].disconnected
        assert [kind for kind, _ in blocks(home, chat)] == ["needs_you"]

    run(body, home)


def test_a_cli_that_ends_mid_turn_leaves_an_unknown_outcome(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="dies", model="haiku"))
        await harness.send(chat, OperatorText("long job"))
        FakeClient.made[0].inbox.put_nowait(None)
        await settle(lambda: getattr(read_record(home, chat), "turn", "") == "idle")
        assert blocks(home, chat)[-1] == (
            "needs_you",
            {"reason": "the agent process ended during a turn; its outcome is unknown"},
        )
        await harness.send(chat, OperatorText("again"))
        assert len(FakeClient.made) == 2

    run(body, home)
