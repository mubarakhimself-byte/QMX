"""The harness adapter at its edge: every prompt goes out as `InjectedText`, never
`OperatorText`; an ask raised mid-turn is rejected at once; the turn ends on the chat
record's `idle`."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

from qma.harness import AskId, Harness, InjectedText, OperatorText, QmxHome, Reject

from qmx_engine.ports.harness_adapter import HarnessAdapter, Turn

CHAT = "s1"


class Control:
    def __init__(self) -> None:
        self.blocks: list[dict[str, Any]] = []

    def settings_get(self, section: str) -> dict[str, Any]:
        return {"openrouter": {}} if section == "providers" else {}

    def events(self, topic: str, after: int, subject: str, limit: int) -> list[dict[str, Any]]:
        rows = [
            {"id": i + 1, "data": {"type": "block", "block": block}}
            for i, block in enumerate(self.blocks)
        ]
        return [row for i, row in enumerate(rows) if i + 1 > after][:limit]


class StubHarness:
    """Records what the adapter hands the harness. A send raises an ask, then a text block, then
    marks the chat idle, the way a Background turn that tries a write ends."""

    def __init__(self, root: Path) -> None:
        self.home = QmxHome(root)
        self.control = Control()
        self.prompts: list[object] = []
        self.answers: list[tuple[AskId, object]] = []
        self.home.chats_dir.mkdir(parents=True)
        (root / "runs" / CHAT).mkdir(parents=True)

    async def send(self, chat: str, prompt: object) -> None:
        self.prompts.append(prompt)
        self.control.blocks.append(
            {"type": "permission", "seq": 7, "content": {"state": "asking", "tool": "Write"}}
        )
        self.record("running")

    def answer(self, ask: AskId, answer: object) -> str:
        self.answers.append((ask, answer))
        self.control.blocks.append({"type": "text", "seq": 9, "content": {"text": "{}"}})
        row = {"event": "model_call", "payload": {"input_tokens": 3, "output_tokens": 2}}
        (self.home.root / "runs" / CHAT / "journal.jsonl").write_text(json.dumps(row) + "\n")
        self.record("idle")
        return "resolved"

    def record(self, turn: str) -> None:
        (self.home.chats_dir / f"{CHAT}.json").write_text(json.dumps({"turn": turn}))


def test_a_prompt_goes_out_as_injected_text_and_an_ask_is_rejected_at_once(
    tmp_path: Path,
) -> None:
    stub = StubHarness(tmp_path)
    adapter = HarnessAdapter(cast(Harness, stub))

    async def turn() -> Turn:
        await adapter.send(CHAT, "Reply with {}.")
        return await adapter.wait_turn(CHAT, timeout=5)

    found = asyncio.run(turn())

    assert [type(p) for p in stub.prompts] == [InjectedText]
    assert not any(isinstance(p, OperatorText) for p in stub.prompts)
    assert stub.answers == [(AskId(cast(Any, CHAT), 7), Reject("unattended run"))]
    assert (found.text, found.asks_rejected) == ("{}", 1)
    assert found.tokens == {"in": 3, "out": 2, "cache_read": 0, "cache_write": 0}
    assert adapter.profiles() == frozenset({"claude", "openrouter"})
