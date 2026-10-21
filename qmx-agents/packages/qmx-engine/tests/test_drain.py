"""Drain and pause (AD-9): a model node held at a usage limit drains the run. Scripts go on, no new
model node starts, the run pauses once nothing runs and returns `waiting`, and the ticker resumes
it after the reset with nobody asked, at once when the drain outlasted the reset. A refusal no
reset lifts is not a limit wait. A send that waits for a harness slot is a recorded wait too."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fake_port import CARD, OPEN, FakePort, agent, agent_files, events_of
from flows import edge, folder, node

from qmx_engine.admission import Admission
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.store import Ledger
from qmx_engine.nodes.base import Failed
from qmx_engine.ports.harness_adapter import PlanUse
from qmx_engine.ports.settings import StaticSettings
from qmx_engine.roles import Candidate
from qmx_engine.runner import Engine, Outcome
from qmx_engine.service.api import EngineService
from qmx_engine.settings import DEFAULTS
from qmx_engine.triggers.ticker import Scheduler

TICK_S = 0.25

SLOW = """
import json, time
time.sleep({seconds})
print(json.dumps("scripted"))
"""


@pytest.mark.parametrize(
    ("reset_in", "script_seconds"),
    [(2, 0.5), (1, 4)],
    ids=["reset-after-the-drain", "drain-outlasts-the-reset"],
)
def test_a_limit_drains_the_run_then_the_ticker_resumes_it_after_the_reset(
    tmp_path: Path, reset_in: float, script_seconds: float
) -> None:
    root = agent_files(
        folder(
            tmp_path / "wf",
            [
                node("start", "trigger"),
                agent("first"),
                node("slow", "script", script="scripts/slow.py"),
                agent("after"),
            ],
            {"start": {"main": [edge("first"), edge("slow")]}, "slow": {"main": [edge("after")]}},
            {"slow": SLOW.format(seconds=script_seconds)},
        )
    )
    reset = (datetime.now(UTC) + timedelta(seconds=reset_in)).isoformat()
    port = FakePort(CARD, CARD, uses=[PlanUse(1.0, reset, reset, None), OPEN])

    outcome, ticks = asyncio.run(ticked(root, tmp_path / "home", port))
    events = events_of(tmp_path / "home", outcome.run_id)

    def at(kind: str, node_id: str | None = None) -> list[int]:
        return [
            i
            for i, e in enumerate(events)
            if e.kind == kind and (node_id is None or e.data.get("node_id") == node_id)
        ]

    waited = [e.data for e in events if e.kind == "node_waiting"]
    (paused,), (resumed,) = at("run_paused"), at("run_resumed")
    assert (outcome.status, events[-1].kind, events[-1].data["status"]) == (
        "waiting",
        "run_finished",
        "passed",
    )
    assert 1 <= ticks <= reset_in / TICK_S + 3
    assert events[resumed].data == {"reason": "limit"}
    assert [(w["node_id"], w["reason"], w["resume_at"]) for w in waited] == [
        ("first", "limit", reset)
    ]
    assert at("node_finished", "slow")[0] < paused < resumed
    assert min(at("node_scheduled", "after")) > resumed
    assert events[paused].data == {"reason": "limit", "resume_at": reset}
    assert [chat for chat, _ in port.sent] == ["chat-1", "chat-2"]


async def ticked(root: Path, home: Path, port: FakePort) -> tuple[Outcome, int]:
    """Start the run, then tick every `TICK_S` until it ends; the start's outcome and the ticks."""
    found = checked(root)
    assert not isinstance(found, list), found
    settings = StaticSettings({**DEFAULTS, "limits.slack": 0})
    with EngineService.open(home, settings=settings, harness=port) as svc:
        outcome = await svc.ctx.engine.start(root, found[1], mode="live", inputs=None)
        ticker = Scheduler(svc.ctx)
        for ticks in range(1, 40):
            await ticker.tick()
            await ticker.settle()
            if events_of(home, outcome.run_id)[-1].kind == "run_finished":
                return outcome, ticks
            await asyncio.sleep(TICK_S)
    raise AssertionError("the ticker never resumed the run")


def test_a_refusal_no_reset_lifts_fails_unavailable_instead_of_waiting() -> None:
    haiku = Candidate("claude", "haiku", None, 200_000, test_only=False)
    gate = Admission(FakePort(uses=[PlanUse(None, None, None, None)]), DEFAULTS)

    found = asyncio.run(gate.refused(haiku, "there is no reading of the plan's five-hour window"))

    assert isinstance(found, Failed)
    assert (found.code, found.retryable) == ("unavailable", True)


class SlotWait(FakePort):
    """The first send waits in the harness slot table for `seconds` before it is sent."""

    def __init__(self, seconds: float) -> None:
        super().__init__(CARD)
        self.seconds = seconds
        self.waiting: set[str] = set()
        self.priorities: list[int] = []

    async def send(self, chat: str, text: str, *, priority: int = 0) -> None:
        self.priorities.append(priority)
        self.waiting.add(chat)
        await asyncio.sleep(self.seconds)
        self.waiting.discard(chat)
        await super().send(chat, text, priority=priority)

    def queued(self, chat: str) -> bool:
        return chat in self.waiting


def test_a_send_waiting_for_a_harness_slot_is_never_judged_idle(tmp_path: Path) -> None:
    root = agent_files(
        folder(
            tmp_path / "wf",
            [node("start", "trigger"), agent("read")],
            {"start": {"main": [edge("read")]}},
            {},
        )
    )
    port = SlotWait(seconds=3)
    quick = {"scheduler.tick": 0.05, "timeout.agent.idle": 1, "timeout.grace": 0.5}

    async def go() -> Outcome:
        found = checked(root)
        assert not isinstance(found, list), found
        with Ledger.open(tmp_path / "home") as ledger:
            engine = Engine(tmp_path / "home", ledger, settings={**DEFAULTS, **quick}, harness=port)
            return await engine.start(root, found[1], mode="test", inputs=None, priority=4)

    outcome = asyncio.run(go())
    events = events_of(tmp_path / "home", outcome.run_id)

    assert outcome.status == "passed"
    assert [e.kind for e in events if e.kind in ("log", "node_failed")] == []
    assert port.priorities == [4]
    assert port.interrupted == []
