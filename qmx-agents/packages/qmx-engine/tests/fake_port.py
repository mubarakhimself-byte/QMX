"""A `HarnessPort` that runs no model: each turn's answer comes from a list, and every chat it
starts and every text it is sent is kept for the test to read. Also an `agent` node for workflow
folders, with its brief and schema files."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any

from flows import node
from pydantic import JsonValue

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.harness_adapter import Activity, PlanUse, Turn
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.runner import Engine, Mode, Outcome
from qmx_engine.settings import DEFAULTS
from qmx_engine.sink import Listener

TOKENS = {"in": 10, "out": 5, "cache_read": 100, "cache_write": 0}
OPEN = PlanUse(0.1, "2026-10-17T12:00:00+00:00", None, None)
CARD = '{"seen": 2}'


def agent(name: str, **parameters: JsonValue) -> dict[str, Any]:
    found: dict[str, JsonValue] = {
        "brief_ref": "prompts/read.md",
        "output_schema_ref": "schemas/card.json",
        "tools": ["Read", "Grep"],
        **parameters,
    }
    declared = {"role": "reader", "toolsets": ["library"], "skills": ["paper-question-battery"]}
    return node(name, "agent", **found) | declared


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
    with Ledger.open(home) as ledger, LibraryFake.open(home) as library:
        engine = Engine(
            home, ledger, settings={**DEFAULTS, **(settings or {})}, harness=port, library=library
        )
        return await engine.start(root, found[1], mode=mode, inputs=inputs)


def events_of(home: Path, run_id: str) -> list[Event]:
    with Reader.open(home) as reader:
        return reader.events(run_id)


type Answer = Turn | str | Callable[[FakePort, str], Awaitable[Turn]]


class FakePort:
    def __init__(
        self, *answers: Answer, uses: list[PlanUse] | None = None, holds_task: bool = True
    ) -> None:
        self.answers = list(answers)
        self.uses = uses or [OPEN]
        """Each `plan_use` reading in turn; the last one repeats."""
        self.chats: list[dict[str, object]] = []
        self.listeners: dict[str, Listener] = {}
        self.sent: list[tuple[str, str]] = []
        self.interrupted: list[str] = []
        self.activities: dict[str, Activity] = {}
        """What each chat shows the stuck detector; a running turn with nothing to show else."""
        self.halts: dict[str, asyncio.Event] = {}
        """Set when the chat is interrupted, so an answer can wait for it."""
        self.task_held = holds_task

    def profiles(self) -> frozenset[str]:
        return frozenset({"claude", "openrouter"})

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
        tools: tuple[str, ...] = (),
        toolsets: tuple[str, ...] = (),
        skills: tuple[str, ...] = (),
        system: str | None = None,
        compact_at: float | None = None,
    ) -> str:
        chat = f"chat-{len(self.chats) + 1}"
        self.chats.append(
            {
                "title": title,
                "profile": profile,
                "model": model,
                "tools": tools,
                "toolsets": toolsets,
                "skills": skills,
                "system": system,
                "compact_at": compact_at,
            }
        )
        return chat

    def surface_digest(self, chat: str) -> str | None:
        return f"digest-of-{chat}"

    def listen(self, chat: str, listener: Listener | None) -> None:
        if listener is None:
            self.listeners.pop(chat, None)
        else:
            self.listeners[chat] = listener

    async def hook(self, chat: str, event: str, **data: object) -> None:
        await self.listeners[chat]({"hook_event_name": event, **data})

    def holds_task(self, chat: str) -> bool:
        return self.task_held

    async def send(self, chat: str, text: str, *, priority: int = 0) -> None:
        self.sent.append((chat, text))

    def queued(self, chat: str) -> bool:
        return False

    async def wait_turn(self, chat: str, *, timeout: float | None = None) -> Turn:
        found = self.answers.pop(0)
        if isinstance(found, Turn):
            return found
        if isinstance(found, str):
            return Turn(found, dict(TOKENS))
        return await found(self, chat)

    async def interrupt(self, chat: str) -> None:
        self.interrupted.append(chat)
        self.halted(chat).set()

    async def close(self, chat: str) -> None: ...

    def halted(self, chat: str) -> asyncio.Event:
        return self.halts.setdefault(chat, asyncio.Event())

    def context(self, chat: str) -> int | None:
        return None

    def activity(self, chat: str) -> Activity:
        return self.activities.get(chat, Activity(0, running=True))
