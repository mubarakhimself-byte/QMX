"""Admission of engine chats (rulings 26, 27, 90, 106; SOLUTION-DESIGN 7.4; AD-9, AD-40, AD-58).

The engine keeps `limits.interactive_reserve` of the harness's slot table for the operator: at most
`max_live_chats - reserve` engine chats run a turn at once, and an attempt waits for a free one.
`max_live_chats` is the harness slot table's size, read through the settings port; chat slots are
machine capacity, not usage. QMX sets no usage limit of its own: there is no background share and
no budget, so a plan attempt waits only when a plan window is used up, as
`waiting(limit, resume_at)` with the window's reset time plus `limits.slack`, and a refused send
waits the same way. Nothing here asks the operator (ruling 27).

A limit wait always names when it ends, so the run can wake itself. A refusal that no reset lifts
(the overage stop, a refused key row) is not a limit wait: the attempt fails `unavailable` and the
failure ladder takes it.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timedelta

from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import Failed, Waiting
from qmx_engine.ports.harness_adapter import HarnessPort, PlanUse
from qmx_engine.ports.settings import HARNESS_SLOTS, MAX_LIVE_CHATS
from qmx_engine.roles import PLAN, Candidate

type Held = Waiting | Failed


def setting(settings: Mapping[str, object], key: str, default: float) -> float:
    found = settings.get(key)
    return (
        float(found) if isinstance(found, int | float) and not isinstance(found, bool) else default
    )


def engine_slots(settings: Mapping[str, object]) -> int:
    slots = int(setting(settings, MAX_LIVE_CHATS, HARNESS_SLOTS))
    reserve = int(setting(settings, "limits.interactive_reserve", 2))
    return max(slots - reserve, 0)


def later(instant: str, seconds: float) -> str:
    return (datetime.fromisoformat(instant) + timedelta(seconds=seconds)).isoformat()


def held(resume_at: str, why: str) -> Waiting:
    return Waiting("limit", resume_at, span={"detail": why})


def unavailable(why: str, *, retryable: bool) -> Failed:
    return Failed("unavailable", why, signature("unavailable", why), retryable)


def limit_wait(use: PlanUse, slack: float) -> Held | None:
    """What a plan attempt does now: wait for a reset, fail, or None to run."""
    if use.stopped is not None:
        return unavailable(f"plan use is stopped: {use.stopped}", retryable=False)
    if use.blocked_until is not None:
        return held(later(use.blocked_until, slack), "a plan window is used up")
    return None


class Admission:
    def __init__(self, harness: HarnessPort, settings: Mapping[str, object]) -> None:
        self.harness = harness
        self.settings = settings
        self.live = 0
        self.peak = 0
        self.changed = asyncio.Condition()

    def cap(self) -> int:
        return engine_slots(self.settings)

    def slack(self) -> float:
        return setting(self.settings, "limits.slack", 60)

    async def check(self, candidate: Candidate) -> Held | None:
        """A plan candidate's wait or failure, or None. Key rows are never held here."""
        if self.cap() == 0:
            return unavailable("the operator's reserve takes every live chat", retryable=False)
        if candidate.profile != PLAN:
            return None
        return limit_wait(await self.harness.plan_use(), self.slack())

    async def refused(self, candidate: Candidate, reason: str) -> Held:
        """A refused send waits for the plan window that holds it, or fails when no reset lifts
        the refusal."""
        if candidate.profile == PLAN:
            wait = limit_wait(await self.harness.plan_use(), self.slack())
            if isinstance(wait, Waiting):
                return replace(wait, span={"detail": reason})
            if wait is not None:
                return wait
        return unavailable(reason, retryable=True)

    async def acquire(self) -> None:
        """Take one engine chat slot for a turn, waiting while all are busy."""
        async with self.changed:
            await self.changed.wait_for(lambda: self.live < self.cap())
            self.live += 1
            self.peak = max(self.peak, self.live)

    async def release(self) -> None:
        async with self.changed:
            self.live -= 1
            self.changed.notify_all()
