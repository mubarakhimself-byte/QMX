"""The `agent` node over a fake harness port: every chat gets `compact_at` and hooks, hook and
block tool calls become child spans, a refused `compact_at` falls back to a summary and a fresh
chat, the chat of an attempt the engine died in is picked up again, and the modes that need H11
are refused."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fake_port import CARD, FakePort, agent, agent_files, drive, events_of
from flows import edge, folder, node

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.agent import RESUMED, SUMMARISE
from qmx_engine.ports.harness_adapter import ToolCall, Turn
from qmx_engine.ports.inbox import InboxPort
from qmx_engine.runner import Engine
from qmx_engine.settings import DEFAULTS

FAST_RETRY = {"retry.backoff": (0, 0, 0)}


def one_agent(root: Path, **parameters: object) -> Path:
    built = folder(
        root,
        [node("start", "trigger"), agent("read", **parameters)],  # type: ignore[arg-type]
        {"start": {"main": [edge("read")]}},
        {},
    )
    return agent_files(built)


def test_a_chat_gets_compact_at_and_hooks_and_every_tool_call_becomes_a_child_span(
    tmp_path: Path,
) -> None:
    async def turn(port: FakePort, chat: str) -> Turn:
        hooks = port.hooks[chat]
        assert hooks.post_tool_use is not None and hooks.pre_compact is not None
        await hooks.post_tool_use({"tool_use_id": "t1", "tool_name": "Read", "duration_ms": 12})  # type: ignore[arg-type]
        await hooks.pre_compact({"trigger": "auto"})  # type: ignore[arg-type]
        return Turn(CARD, tools=(ToolCall("t1", "Read"), ToolCall("t2", "Grep", "no match")))

    port = FakePort(turn)
    outcome = asyncio.run(drive(one_agent(tmp_path / "wf"), tmp_path / "home", port))
    events = events_of(tmp_path / "home", outcome.run_id)
    with Reader.open(tmp_path / "home") as reader:
        spans = reader.spans(outcome.run_id)

    attempt = next(s for s in spans if s.node_id == "read" and s.kind == "node")
    tools = sorted(
        (s.name, s.duration_ms, s.error, s.parent_span_id) for s in spans if s.kind == "tool"
    )
    order = [e.kind for e in events if e.kind in ("memory_written", "compacted")]
    assert outcome.status == "passed"
    assert port.chats[0]["compact_at"] == 0.4 and port.chats[0]["hooks"] is True
    assert tools == [
        ("Grep", None, "no match", attempt.span_id),
        ("Read", 12, None, attempt.span_id),
    ]
    assert order == ["memory_written", "compacted"]
    assert attempt.events == [{"compacted": {"trigger": "auto", "at_fraction": None}}]


def test_a_refused_compact_at_restarts_the_attempt_in_a_chat_seeded_with_its_summary(
    tmp_path: Path,
) -> None:
    port = FakePort(
        Turn("not json", context=180_000),
        Turn("I counted a and b; nothing is left."),
        CARD,
        refuse_compact=True,
    )

    outcome = asyncio.run(drive(one_agent(tmp_path / "wf"), tmp_path / "home", port))
    events = events_of(tmp_path / "home", outcome.run_id)

    compacted = [e.data for e in events if e.kind == "compacted"]
    lines = [e.data for e in events if e.kind == "log" and e.data.get("fallback") == "restart"]
    assert outcome.status == "passed"
    assert [c.get("compact_at") for c in port.chats] == [None, None]
    assert [(chat, text == SUMMARISE) for chat, text in port.sent] == [
        ("chat-1", False),
        ("chat-1", True),
        ("chat-2", False),
    ]
    assert "~~~~\nI counted a and b; nothing is left.\n~~~~" in port.sent[2][1]
    assert [(c["trigger"], c["at_fraction"]) for c in compacted] == [("restart", 0.9)]
    assert [e.kind for e in events].count("memory_written") == 1
    assert len(lines) == 1 and lines[0]["level"] == "info"


def test_the_engine_dying_mid_attempt_retries_once_on_the_same_chat_with_no_inbox_item(
    tmp_path: Path,
) -> None:
    home, root = tmp_path / "home", one_agent(tmp_path / "wf")
    found = checked(root)
    assert not isinstance(found, list)

    async def hang(port: FakePort, chat: str) -> Turn:
        await asyncio.Event().wait()
        raise AssertionError("unreachable")

    async def die() -> None:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings=DEFAULTS, harness=FakePort(hang))
            run = engine.start(root, found[1], mode="test", inputs=None, run_id="run-died")
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(run, 1)

    asyncio.run(die())
    port = FakePort(CARD)

    async def again() -> str:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings={**DEFAULTS, **FAST_RETRY}, harness=port)
            outcome = await engine.resume("run-died")
            inbox: InboxPort = engine.inbox
            return f"{outcome.status} {len(inbox.list_items(open_only=False))}"

    ended = asyncio.run(again())
    events = events_of(home, "run-died")

    chats = [
        (e.data["attempt"], e.data["session_id"])
        for e in events
        if e.kind == "heartbeat" and "session_id" in e.data
    ]
    unknown = [e.data for e in events if e.kind == "node_failed"]
    info = [e.data for e in events if e.kind == "log" and e.data.get("level") == "info"]
    assert ended == "passed 0"
    assert chats == [(1, "chat-1"), (2, "chat-1")]
    assert (port.chats, port.sent) == ([], [("chat-1", RESUMED)])
    assert [(u["code"], u["effect_state"]) for u in unknown] == [("interrupted", "unknown")]
    assert len(info) == 1 and info[0]["idempotency_key"] == "run-died:read:0:1"
    assert "run-died:read:0:1" in str(info[0]["line"])


def test_tool_calls_past_max_tool_calls_interrupt_the_chat_and_pause_the_run(
    tmp_path: Path,
) -> None:
    async def busy(port: FakePort, chat: str) -> Turn:
        hook = port.hooks[chat].post_tool_use
        assert hook is not None
        for n in range(3):
            await hook({"tool_use_id": f"t{n}", "tool_name": "Read"})  # type: ignore[arg-type]
        await asyncio.sleep(0)
        return Turn(None)

    port = FakePort(busy)
    root = one_agent(tmp_path / "wf", max_tool_calls=2)

    outcome = asyncio.run(drive(root, tmp_path / "home", port))
    events = events_of(tmp_path / "home", outcome.run_id)

    waiting = [e.data["reason"] for e in events if e.kind == "node_waiting"]
    assert (outcome.status, outcome.reason) == ("waiting", "runaway")
    assert port.interrupted == ["chat-1"]
    assert waiting == ["runaway"]


@pytest.mark.parametrize("mode", ["cli_inside", "host_harness"])
def test_the_modes_that_need_relay_run_passes_are_refused_at_dispatch(
    tmp_path: Path, mode: str
) -> None:
    port = FakePort()
    root = one_agent(tmp_path / "wf", agent_mode=mode)

    outcome = asyncio.run(drive(root, tmp_path / "home", port))
    events = events_of(tmp_path / "home", outcome.run_id)

    codes = sorted({str(e.data["code"]) for e in events if e.kind == "node_failed"})
    assert codes == ["mode_not_available"]
    assert (outcome.status, port.chats) == ("failed", [])
