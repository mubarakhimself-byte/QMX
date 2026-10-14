"""Plan windows and the background cap.

Per-turn tokens and cost are not kept here. They go to the run journal as `model_call`
events, which qmx-control's `RunIndex` already sums. This module keeps only the facts that
are per account, not per chat: the rate-limit windows.

Shared state check (separate-before-serializing): many chats report the same account's
windows. Each report is an independent timestamped fact, and `record` keeps the newest per
(profile, window). The merge is commutative and idempotent, and everything runs on one event
loop, so there is no lock.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from qma.harness.profiles import ProfileName
from qma.harness.project import Limits


@dataclass(frozen=True)
class WindowView:
    profile: ProfileName
    limits: Limits
    as_of: datetime
    """When QMA last heard it. `RateLimitEvent` fires only on transitions (02a section 9),
    so the UI labels it "as of the last QMX turn"."""


class UsageLedger:
    def record(self, profile: ProfileName, limits: Limits, at: datetime) -> None:
        """Keep the newest fact per (profile, window). A replayed or older fact is a no-op."""
        raise NotImplementedError

    def windows(self) -> Mapping[ProfileName, tuple[WindowView, ...]]:
        """Facts whose `resets_at` has passed are dropped on read, not by a timer."""
        raise NotImplementedError


@dataclass(frozen=True)
class BackgroundCap:
    """Background chats stop at this share of the plan's five-hour window (R6, default 0.5).
    UI-editable in settings.toml [budgets]."""

    fraction: float

    def allows(self, ledger: UsageLedger) -> bool:
        """False when the plan's five_hour utilization is at or above `fraction`, or when
        the plan is `rejected`. Unknown utilization allows (best effort until check S10
        shows whether `/usage` reaches Python as a backstop)."""
        raise NotImplementedError
