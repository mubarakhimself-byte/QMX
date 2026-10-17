"""A `HarnessPort` that runs no model: each turn's answer comes from a list, and every chat it
starts and every text it is sent is kept for the test to read. Also an `agent` node for workflow
folders, with its brief and schema files."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any

from flows import node
from pydantic import JsonValue
from qma.harness import ChatHooks

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.harness_adapter import CompactRefused, PlanUse, Turn
from qmx_engine.runner import Engine, Mode, Outcome
from qmx_engine.settings import DEFAULTS

TOKENS = {"in": 10, "out": 5, "cache_read": 100, "cache_write": 0}
OPEN = PlanUse(0.1, "2026-10-17T12:00:00+00:00", None, None)
CARD = '{"seen": 2}'


def agent(name: str, **parameters: JsonValue) -> dict[str, Any]:
    found: dict[str, JsonValue] = {
        "brief_ref": "prompts/read.md",
        "output_schema_ref": "schemas/card.json",
        "tools": ["Read", "Grep"],
        "skills": ["paper-question-battery"],
        "max_turns": 12,
        **parameters,
    }
    return node(name, "agent", **found) | {"role": "reader"}


def agent_files(root: Path) -> Path:
    (root / "prompts").mkdir(parents=True, exist_ok=True)
    (root / "prompts" / "read.md").write_text("Count the items you are given.", "utf-8")
    (root / "schemas").mkdir(exist_ok=True)
    schema = {"type": "object", "required": ["seen"], "properties": {"seen": {"type": "integer"}}}
    (root / "schemas" / "card.json").write_text(json.dumps(schema), "utf-8")
    return root


async def drive(
    root: Path,
    home: Path,
    port: FakePort,
    inputs: JsonValue = None,
    *,
    mode: Mode = "test",
    settings: Mapping[str, object] | None = None,
) -> Outcome:
    found = checked(root)
    assert not isinstance(found, list), found
    with Ledger.open(home) as ledger:
        engine = Engine(home, ledger, settings={**DEFAULTS, **(settings or {})}, harness=port)
        return await engine.start(root, found[1], mode=mode, inputs=inputs)


def events_of(home: Path, run_id: str) -> list[Event]:
    with Reader.open(home) as reader:
        return reader.events(run_id)


type Answer = Turn | str | Callable[[FakePort, str], Awaitable[Turn]]


class FakePort:
    def __init__(
        self, *answers: Answer, uses: list[PlanUse] | None = None, refuse_compact: bool = False
    ) -> None:
        self.answers = list(answers)
        self.uses = uses or [OPEN]
        """Each `plan_use` reading in turn; the last one repeats."""
        self.refuse_compact = refuse_compact
        self.chats: list[dict[str, object]] = []
        self.hooks: dict[str, ChatHooks] = {}
        self.sent: list[tuple[str, str]] = []
        self.interrupted: list[str] = []

    def profiles(self) -> frozenset[str]:
        return frozenset({"claude", "openrouter"})

    def max_live_chats(self) -> int:
        return 4

    async def plan_use(self) -> PlanUse:
        return self.uses.pop(0) if len(self.uses) > 1 else self.uses[0]

    async def start_chat(
        self,
        *,
        title: str,
        profile: str,
        model: str,
        effort: str | None,
        workspace: Path,
        compact_at: float | None = None,
        hooks: ChatHooks | None = None,
    ) -> str:
        if self.refuse_compact and (compact_at is not None or hooks is not None):
            raise CompactRefused("compact_at and hooks are for Background and Child chats only")
        chat = f"chat-{len(self.chats) + 1}"
        found: dict[str, object] = {"title": title, "profile": profile, "model": model}
        if compact_at is not None or hooks is not None:
            found |= {"compact_at": compact_at, "hooks": hooks is not None}
        self.chats.append(found)
        if hooks is not None:
            self.hooks[chat] = hooks
        return chat

    async def send(self, chat: str, text: str) -> None:
        self.sent.append((chat, text))

    async def wait_turn(self, chat: str, *, timeout: float, idle: float | None = None) -> Turn:
        found = self.answers.pop(0)
        if isinstance(found, Turn):
            return found
        if isinstance(found, str):
            return Turn(found, dict(TOKENS))
        return await found(self, chat)

    async def interrupt(self, chat: str) -> None:
        self.interrupted.append(chat)

    def context(self, chat: str) -> int | None:
        return None
