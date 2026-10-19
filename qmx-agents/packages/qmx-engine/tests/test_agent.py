"""The `agent` node over a fake harness port: every chat gets exactly its declared tools and
`compact_at`, hook and turn tool calls become child spans, the chat of an attempt the engine died
in is picked up again and gets its whole task when it never had it (B-69), and the modes that need
H11 are refused."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fake_port import CARD, FakePort, agent, agent_files, drive, events_of
from flows import edge, folder, node

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.agent import RESUMED, STUCK_SUMMARY
from qmx_engine.ports.harness_adapter import Activity, ToolCall, ToolStep, Turn
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


def test_a_chat_gets_its_declared_tools_and_every_tool_call_becomes_a_child_span(
    tmp_path: Path,
) -> None:
    async def turn(port: FakePort, chat: str) -> Turn:
        await port.hook(chat, "PostToolUse", tool_use_id="t1", tool_name="Read", duration_ms=12)
        await port.hook(chat, "PreCompact", trigger="auto")
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
    assert (port.chats[0]["tools"], port.chats[0]["compact_at"]) == (("Read", "Grep"), 0.4)
    assert tools == [
        ("Grep", None, "no match", attempt.span_id),
        ("Read", 12, None, attempt.span_id),
    ]
    assert order == ["memory_written", "compacted"]
    assert attempt.events == [{"compacted": {"trigger": "auto", "at_fraction": None}}]


TASK_START = "Skills to apply: paper-question-battery.\n\nCount the items you are given."


@pytest.mark.parametrize("held", [True, False])
def test_the_engine_dying_mid_attempt_retries_once_on_the_same_chat_with_no_inbox_item(
    tmp_path: Path, held: bool
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
    port = FakePort(CARD, holds_task=held)

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
    [(chat, sent)] = port.sent
    assert (port.chats, chat) == ([], "chat-1")
    if held:
        assert sent == RESUMED
    else:
        assert sent.startswith(TASK_START) and sent.endswith('Input:\n{"in": null}')
    assert [(u["code"], u["effect_state"]) for u in unknown] == [("interrupted", "unknown")]
    assert len(info) == 1 and info[0]["idempotency_key"] == "run-died:read:0:1"
    assert "run-died:read:0:1" in str(info[0]["line"])


QUICK = {"scheduler.tick": 0.05}
SUMMARY = "I read a.txt again and again and it never changed."


def read_steps(count: int, *, same: bool) -> tuple[ToolStep, ...]:
    return tuple(
        ToolStep(
            f"t{n}",
            "Read",
            {"path": "a.txt" if same else f"page-{n}.txt"},
            f"text {n * (not same)}",
        )
        for n in range(count)
    )


def test_a_looping_agent_is_stopped_and_parks_stalled_loop_with_its_summary(
    tmp_path: Path,
) -> None:
    async def loops(port: FakePort, chat: str) -> Turn:
        port.activities[chat] = Activity(10, read_steps(5, same=True), running=True)
        await port.halted(chat).wait()
        return Turn(None)

    port = FakePort(loops, SUMMARY)
    root = one_agent(tmp_path / "wf")

    outcome = asyncio.run(drive(root, tmp_path / "home", port, settings=QUICK))
    events = events_of(tmp_path / "home", outcome.run_id)

    [failed] = [e.data for e in events if e.kind == "node_failed"]
    assert (failed["code"], failed["stalled"], failed["output"]) == ("stalled", "loop", SUMMARY)
    assert outcome.status == "failed"
    assert outcome.reason is not None and "the agent was looping" in outcome.reason
    assert port.interrupted == ["chat-1"]
    assert port.sent[-1] == ("chat-1", STUCK_SUMMARY)


def test_an_agent_making_progress_runs_on_past_hundreds_of_tool_calls(tmp_path: Path) -> None:
    async def pages(port: FakePort, chat: str) -> Turn:
        for n in range(300):
            port.activities[chat] = Activity(n, read_steps(n, same=False), running=True)
            await port.hook(chat, "PostToolUse", tool_use_id=f"t{n}", tool_name="Read")
            await asyncio.sleep(0.001)
        return Turn(CARD)

    port = FakePort(pages)
    root = one_agent(tmp_path / "wf")

    outcome = asyncio.run(drive(root, tmp_path / "home", port, settings=QUICK))
    events = events_of(tmp_path / "home", outcome.run_id)

    assert outcome.status == "passed"
    assert sum(1 for e in events if e.kind == "tool_called") == 300
    assert port.interrupted == []


def test_held_chunks_start_only_after_the_first_chunk_ends_its_turn(tmp_path: Path) -> None:
    root = agent_files(
        folder(
            tmp_path / "wf",
            [node("start", "trigger"), agent("read"), node("all", "join")],
            {
                "start": {"main": [edge("read", "chunk", chunk={"by": "items", "size": 1})]},
                "read": {"main": [edge("all")]},
            },
            {},
        )
    )
    home = tmp_path / "home"
    started_during_first_turn: list[int] = []

    async def slow(port: FakePort, chat: str) -> Turn:
        await asyncio.sleep(0.3)
        with Reader.open(home) as reader:
            query = "SELECT COUNT(*) FROM events WHERE kind = 'node_started'"
            started_during_first_turn.append(reader.connection.execute(query).fetchone()[0])
        return Turn(CARD)

    port = FakePort(slow, CARD, CARD)

    outcome = asyncio.run(drive(root, home, port, ["a", "b", "c"], settings=QUICK))

    events = events_of(home, outcome.run_id)
    started = [e.data["partition"] for e in events if e.kind == "node_started"]
    assert outcome.status == "passed"
    assert started_during_first_turn == [2]
    assert sorted(p for p in started if isinstance(p, int)) == [0, 1, 2]
    assert [e for e in events if e.kind == "node_failed"] == []


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
