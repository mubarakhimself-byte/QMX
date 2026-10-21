"""The harness adapter at its edge: a chat is born with its declared tools, the `engine` policy
and the `engine` sink; a prompt goes out as `InjectedText`; a turn's result maps to the `Turn`
record; and the read-only policy denies a write and an undeclared tool with its reason."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

from qma.harness import (
    AllowOnce,
    Harness,
    InjectedText,
    NewChat,
    PolicyCall,
    QmxHome,
    Reject,
    SessionId,
    TurnHandle,
)
from qma.harness.project import TurnEnded
from qmx_control.service import SessionBlock

from qmx_engine.policy import engine_policy
from qmx_engine.ports.harness_adapter import HarnessAdapter, ToolCall, Turn

CHAT = SessionId("s1")
USAGE = {
    "input_tokens": 3,
    "output_tokens": 2,
    "cache_read_input_tokens": 100,
    "cache_creation_input_tokens": 5,
}


def block(kind: str, **content: object) -> SessionBlock:
    return SessionBlock.model_validate({"type": kind, "content": content})


def ended(ok: bool, reason: str, text: str | None = None) -> TurnEnded:
    return TurnEnded(ok=ok, terminal_reason=reason, deferred_tool_use=False, result=text)


class StubHarness:
    """Keeps what the adapter hands it. A turn plays two tool calls, a denied ask and a
    compaction, then ends with `{}`, unless `hold` keeps it running until interrupted."""

    def __init__(self, root: Path, *, hold: bool = False) -> None:
        self.home = QmxHome(root)
        self.hold = hold
        self.specs: list[NewChat] = []
        self.prompts: list[object] = []
        self.sinks: dict[str, Any] = {}
        self.policies: dict[str, Any] = {}
        self.handle: TurnHandle | None = None

    def register_sink(self, name: str, sink: object) -> None:
        self.sinks[name] = sink

    def register_policy(self, name: str, policy: object) -> None:
        self.policies[name] = policy

    async def start_chat(self, spec: NewChat) -> SessionId:
        self.specs.append(spec)
        return CHAT

    async def run_turn(self, chat: SessionId, prompt: object, *, priority: int = 0) -> TurnHandle:
        self.prompts.append(prompt)
        handle = self.handle = TurnHandle("prompt")
        handle.on_started()
        if self.hold:
            return handle
        handle.on_block(block("tool", id="t1", name="Read", state="started", arguments={}))
        handle.on_block(block("tool", id="t1", state="finished", result="a"))
        handle.on_block(block("tool", id="t2", name="Grep", state="started", arguments={}))
        handle.on_block(block("tool", id="t2", state="error", result="no match"))
        handle.on_block(block("permission", ask=4, state="rejected"))
        handle.on_compaction("auto")
        handle.on_reply("m1", USAGE)
        journal = self.home.root / "runs" / chat / "journal.jsonl"
        journal.parent.mkdir(parents=True, exist_ok=True)
        row = {"event": "model_call", "payload": {"metadata": {"cost": 0.25}}}
        journal.write_text(json.dumps(row) + "\n", encoding="utf-8")
        handle.finish(ended(True, "completed", "{}"))
        return handle

    async def interrupt(self, chat: SessionId) -> None:
        assert self.handle is not None
        self.handle.finish(ended(False, "interrupted"))


def test_a_chat_is_born_with_its_tools_policy_and_sink_and_a_turn_maps_to_the_turn_record(
    tmp_path: Path,
) -> None:
    stub = StubHarness(tmp_path)
    adapter = HarnessAdapter(cast(Harness, stub))
    heard: list[object] = []

    async def listener(data: object) -> None:
        heard.append(data)

    async def turn() -> Turn:
        chat = await adapter.start_chat(
            title="run:read:0:1",
            profile="claude",
            model="haiku",
            effort=None,
            workspace=tmp_path / "wf",
            tools=("Read", "Grep"),
            compact_at=0.4,
        )
        adapter.listen(chat, listener)
        await stub.sinks["engine"](chat, {"hook_event_name": "PostToolUse"})
        await adapter.send(chat, "Reply with {}.")
        return await adapter.wait_turn(chat)

    found = asyncio.run(turn())

    [spec] = stub.specs
    assert (spec.tools, spec.compact_at, spec.hook_sink) == (("Read", "Grep"), 0.4, "engine")
    assert spec.permissions.policy == "engine"
    assert dict(spec.policy_args) == {"tools": ["Read", "Grep"]}
    assert stub.policies == {"engine": engine_policy}
    assert heard == [{"hook_event_name": "PostToolUse"}]
    assert [type(p) for p in stub.prompts] == [InjectedText]
    assert found == Turn(
        "{}",
        {"in": 3, "out": 2, "cache_read": 100, "cache_write": 5},
        cost_usd=0.25,
        asks_rejected=1,
        tools=(ToolCall("t1", "Read"), ToolCall("t2", "Grep", "no match")),
        compactions=("auto",),
        context=108,
    )
    assert adapter.running == {}


def test_a_turn_past_its_timeout_is_interrupted_and_reads_timed_out(tmp_path: Path) -> None:
    stub = StubHarness(tmp_path, hold=True)
    adapter = HarnessAdapter(cast(Harness, stub))

    async def turn() -> Turn:
        await adapter.send(CHAT, "Classify this.")
        return await adapter.wait_turn(CHAT, timeout=0.05)

    found = asyncio.run(turn())

    assert (found.text, found.timed_out, found.needs_you) == (None, True, None)


def ask(tool: str) -> PolicyCall:
    return PolicyCall(CHAT, tool, {}, {"tools": ["Read", "Write"]}, None)


def test_the_read_only_policy_allows_a_declared_read_and_denies_writes_and_undeclared_tools() -> (
    None
):
    async def answers() -> list[object]:
        return [await engine_policy(ask(tool)) for tool in ("Read", "Write", "WebFetch")]

    assert asyncio.run(answers()) == [
        AllowOnce(),
        Reject(
            "Write is refused: steps of this workflow are read-only, so no file is written and no "
            "command runs. Answer from what you can read."
        ),
        Reject("WebFetch is refused: this step declares only Read, Write. Use those."),
    ]
