"""Plan windows, the background cap and the usage page.

Per-turn tokens and cost are not kept here. They go to the run journal as `model_call`
events, which qmx-control's `RunIndex` already sums. Three sources feed those events:
`ResultMessage` for plan chats (client-side estimates, 02a section 9), the relay's usage
tee for key providers (authoritative, read from the provider's own stream), and the
translator's local count for GPT (the ChatGPT side has no usage API, 02b F). This module
keeps only the facts that are per account, not per chat: the plan's rate-limit windows.

Shared state check (separate-before-serializing): many chats report the same account's
windows. Each report is an independent timestamped fact, and `record` keeps the newest per
(profile, window). The merge is commutative and idempotent, and everything runs on one event
loop, so there is no lock.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from typing import TYPE_CHECKING

from qma.harness.profiles import ProfileName
from qma.harness.project import Limits

if TYPE_CHECKING:
    from qma.harness.money import ExposureReport, MoneyPosture


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
        """False when the plan's last seen five_hour utilization is at or above `fraction`,
        or when the plan is `rejected`. Unknown utilization allows.

        Best effort, and it can overshoot. `RateLimitEvent` fires only when a status
        changes (02a section 9, 02b F), so between transitions the utilization this reads
        can be stale while background chats keep spending (03 GB-9). A `rejected` status is
        itself a transition and is always seen. Check S10 records whether `/usage` reaches
        Python as a fresher backstop."""
        raise NotImplementedError


@dataclass(frozen=True)
class UsagePage:
    """What `Harness.usage()` returns and `GET /api/usage` serves. One read, no joins in
    the route."""

    windows: Mapping[ProfileName, tuple[WindowView, ...]]
    tokens: Mapping[ProfileName, Mapping[str, int]]
    """RunIndex sums per profile: input, output, cache read, cache write."""
    background_cap: float
    posture: MoneyPosture
    exposure: ExposureReport | None
    """None until the first probe ran. The page names each reachable secret in plain words."""
