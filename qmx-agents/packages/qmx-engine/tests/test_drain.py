"""Drain and pause (AD-9): a model node held at a usage limit drains the run. Scripts go on, no new
model node starts, the run pauses once nothing runs, and its own timer resumes it after the reset
with nobody asked. A refusal no reset lifts is not a limit wait."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fake_port import CARD, OPEN, FakePort, agent, agent_files, drive, events_of
from flows import edge, folder, node

from qmx_engine.admission import Admission
from qmx_engine.nodes.base import Failed
from qmx_engine.ports.harness_adapter import PlanUse
from qmx_engine.roles import Candidate
from qmx_engine.settings import DEFAULTS

SLOW = """
import json, time
time.sleep(0.5)
print(json.dumps("scripted"))
"""


def test_a_limit_drains_the_run_then_its_timer_resumes_it_after_the_reset(tmp_path: Path) -> None:
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
            {"slow": SLOW},
        )
    )
    reset = (datetime.now(UTC) + timedelta(seconds=2)).isoformat()
    port = FakePort(CARD, CARD, uses=[PlanUse(1.0, reset, reset, None), OPEN])

    outcome = asyncio.run(
        drive(root, tmp_path / "home", port, mode="live", settings={"limits.slack": 0})
    )
    events = events_of(tmp_path / "home", outcome.run_id)

    def at(kind: str, node_id: str | None = None) -> list[int]:
        return [
            i
            for i, e in enumerate(events)
            if e.kind == kind and (node_id is None or e.data.get("node_id") == node_id)
        ]

    waited = [e.data for e in events if e.kind == "node_waiting"]
    (paused,), (resumed,) = at("run_paused"), at("run_resumed")
    assert outcome.status == "passed"
    assert [(w["node_id"], w["reason"], w["resume_at"]) for w in waited] == [
        ("first", "limit", reset)
    ]
    assert at("node_finished", "slow")[0] < paused < resumed
    assert min(at("node_scheduled", "after")) > resumed
    assert events[paused].data == {"reason": "limit", "resume_at": reset}
    assert [chat for chat, _ in port.sent] == ["chat-1", "chat-2"]


def test_a_refusal_no_reset_lifts_fails_unavailable_instead_of_waiting() -> None:
    haiku = Candidate("claude", "haiku", None, 200_000, test_only=False)
    gate = Admission(FakePort(uses=[PlanUse(None, None, None, None)]), DEFAULTS)

    found = asyncio.run(gate.refused(haiku, "there is no reading of the plan's five-hour window"))

    assert isinstance(found, Failed)
    assert (found.code, found.retryable) == ("unavailable", True)
