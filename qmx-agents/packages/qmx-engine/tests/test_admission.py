"""Admission of engine chats: the operator's reserve of the harness slot table, a refusal mapped to
a limit wait, and no QMX share or budget: a plan attempt waits only on a used-up window."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from qmx_control.service import ControlService

from qmx_engine.admission import Admission
from qmx_engine.nodes.base import Waiting
from qmx_engine.ports.harness_adapter import PlanUse
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.roles import Candidate
from qmx_engine.settings import DEFAULTS

HAIKU = Candidate("claude", "haiku", None, 200_000, test_only=False)
KIMI = Candidate("kimi", "k3", None, 200_000, test_only=False)
RESETS = "2026-10-17T12:00:00+00:00"


class Plan:
    def __init__(self, use: PlanUse) -> None:
        self.use = use

    async def plan_use(self) -> PlanUse:
        return self.use


def admission(use: PlanUse, **settings: object) -> Admission:
    return Admission(Plan(use), {**DEFAULTS, **settings})  # type: ignore[arg-type]


def test_engine_chats_stay_under_max_live_chats_less_the_reserve() -> None:
    gate = admission(PlanUse(0.1, RESETS, None, None))

    async def turn() -> None:
        await gate.acquire()
        await asyncio.sleep(0.01)
        await gate.release()

    async def six() -> None:
        await asyncio.gather(*(turn() for _ in range(6)))

    asyncio.run(six())

    assert (gate.cap(), gate.peak, gate.live) == (2, 2, 0)


def test_a_refused_plan_send_waits_for_the_used_up_window_plus_slack() -> None:
    gate = admission(PlanUse(1.0, RESETS, RESETS, None))

    waited = asyncio.run(gate.refused(HAIKU, "the background cap holds this chat"))
    used_up = asyncio.run(gate.check(HAIKU))

    assert waited == Waiting(
        "limit", "2026-10-17T12:01:00+00:00", span={"detail": "the background cap holds this chat"}
    )
    assert used_up == Waiting(
        "limit", "2026-10-17T12:01:00+00:00", span={"detail": "a plan window is used up"}
    )
    assert asyncio.run(gate.check(KIMI)) is None


def test_engine_slots_come_from_the_harness_slot_table_through_settings(tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text(
        "[budgets]\nmax_live_chats = 7\nbackground_cap = 0.5\n", "utf-8"
    )
    settings = ControlSettings(ControlService(tmp_path)).values()
    gate = Admission(Plan(PlanUse(0.1, RESETS, None, None)), settings)  # type: ignore[arg-type]

    assert (settings["max_live_chats"], gate.cap()) == (7, 5)
    assert [key for key in settings if "background_share" in key] == []


@pytest.mark.parametrize("used", [0.5, 0.9, 0.99])
def test_a_plan_attempt_runs_at_any_use_until_its_window_is_used_up(used: float) -> None:
    assert asyncio.run(admission(PlanUse(used, RESETS, None, None)).check(HAIKU)) is None
