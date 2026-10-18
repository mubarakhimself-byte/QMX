"""Admission of engine chats: the operator's reserve, a refusal mapped to a limit wait, and the plan
account's background share read from the harness's settings."""

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
KIMI = Candidate("openrouter", "moonshotai/kimi-k2.5", None, 200_000, test_only=True)
RESETS = "2026-10-17T12:00:00+00:00"


class Plan:
    def __init__(self, use: PlanUse, max_live_chats: int = 4) -> None:
        self.use = use
        self.cap = max_live_chats

    def max_live_chats(self) -> int:
        return self.cap

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


@pytest.mark.parametrize(("cap", "parks_at", "runs_at"), [(0.5, 0.5, 0.49), (0.9, 0.9, 0.6)])
def test_the_plan_share_from_settings_parks_at_its_value(
    tmp_path: Path, cap: float, parks_at: float, runs_at: float
) -> None:
    (tmp_path / "settings.toml").write_text(f"[budgets]\nbackground_cap = {cap}\n", "utf-8")
    settings = ControlSettings(ControlService(tmp_path)).values()

    def check(used: float) -> Waiting | None:
        gate = Admission(Plan(PlanUse(used, RESETS, None, None)), settings)  # type: ignore[arg-type]
        return asyncio.run(gate.check(HAIKU))

    parked = check(parks_at)

    assert settings["pool.accounts.claude.background_share"] == cap
    assert parked is not None
    assert (parked.reason, parked.resume_at) == ("limit", "2026-10-17T12:01:00+00:00")
    assert check(runs_at) is None
