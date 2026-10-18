"""Admission of engine chats (ruling 26, 27, 90; SOLUTION-DESIGN 7.4; AD-9).

The engine keeps `limits.interactive_reserve` of the harness's `max_live_chats` for the operator:
at most `max_live_chats - reserve` engine chats run a turn at once, and an attempt waits for a free
one. There is no fixed background cap in engine code. Each account's background share is a
setting, `pool.accounts.<account>.background_share` (Claude's default 0.5); with one plan account
until the pool packet (L2), its share is the harness's `[budgets] background_cap`, which
`ControlSettings` reads. A plan attempt whose account is at its share or used up waits as
`waiting(limit, resume_at)` with the window's reset time plus `limits.slack`, and a refused send
waits the same way. Nothing here asks the operator (ruling 27).

A limit wait always names when it ends, so the run can wake itself. A refusal that no reset lifts
(the overage stop, no five-hour reading even after a meter turn, a refused key row) is not a limit
wait: the attempt fails `unavailable` and the failure ladder takes it.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timedelta

from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import Failed, Waiting
from qmx_engine.ports.harness_adapter import HarnessPort, PlanUse
from qmx_engine.roles import PLAN, Candidate

type Held = Waiting | Failed


def setting(settings: Mapping[str, object], key: str, default: float) -> float:
    found = settings.get(key)
    return (
        float(found) if isinstance(found, int | float) and not isinstance(found, bool) else default
    )


def share(settings: Mapping[str, object], account: str) -> float:
    own = settings.get(f"pool.accounts.{account}.background_share")
    if isinstance(own, int | float) and not isinstance(own, bool):
        return float(own)
    return setting(settings, "pool.accounts.*.background_share", 0.5)


def engine_cap(max_live_chats: int, settings: Mapping[str, object]) -> int:
    reserve = int(setting(settings, "limits.interactive_reserve", 2))
    return max(max_live_chats - reserve, 0)


def later(instant: str, seconds: float) -> str:
    return (datetime.fromisoformat(instant) + timedelta(seconds=seconds)).isoformat()


def held(resume_at: str, why: str) -> Waiting:
    return Waiting("limit", resume_at, span={"detail": why})


def unavailable(why: str, *, retryable: bool) -> Failed:
    return Failed("unavailable", why, signature("unavailable", why), retryable)


def limit_wait(use: PlanUse, account_share: float, slack: float) -> Held | None:
    """What a plan attempt does now: wait for a reset, fail, or None to run."""
    if use.stopped is not None:
        return unavailable(f"plan use is stopped: {use.stopped}", retryable=False)
    if use.blocked_until is not None:
        return held(later(use.blocked_until, slack), "a plan window is used up")
    if use.five_hour is not None and use.five_hour >= account_share and use.resets_at is not None:
        why = (
            f"the plan account is at {use.five_hour:.0%}, its background share {account_share:.0%}"
        )
        return held(later(use.resets_at, slack), why)
    return None


class Admission:
    def __init__(self, harness: HarnessPort, settings: Mapping[str, object]) -> None:
        self.harness = harness
        self.settings = settings
        self.live = 0
        self.peak = 0
        self.changed = asyncio.Condition()

    def cap(self) -> int:
        return engine_cap(self.harness.max_live_chats(), self.settings)

    def slack(self) -> float:
        return setting(self.settings, "limits.slack", 60)

    async def check(self, candidate: Candidate) -> Held | None:
        """A plan candidate's wait or failure, or None. Key rows are never held here."""
        if self.cap() == 0:
            return unavailable("the operator's reserve takes every live chat", retryable=False)
        if candidate.profile != PLAN:
            return None
        use = await self.harness.plan_use()
        return limit_wait(use, share(self.settings, PLAN), self.slack())

    async def refused(self, candidate: Candidate, reason: str) -> Held:
        """A refused send waits for the plan window that holds it, or fails when no reset lifts
        the refusal."""
        if candidate.profile == PLAN:
            use = await self.harness.plan_use()
            wait = limit_wait(use, share(self.settings, PLAN), self.slack())
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
