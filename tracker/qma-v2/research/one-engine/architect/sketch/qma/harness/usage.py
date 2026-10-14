"""Plan windows, the background cap and the usage page.

Per-turn tokens and cost are not kept here. They go to the run journal as `model_call`
events, which qmx-control's `RunIndex` already sums. Each profile has exactly one source:
`ResultMessage` for plan chats (client-side estimates, 02a section 9), the relay for key
providers (read from the provider's own stream) and for GPT (the translator's local count;
the ChatGPT side has no usage API, 02b F). This module keeps only the facts that are per
account, not per chat: the plan's rate-limit windows and the overage stop.

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

    def hard_stop(self) -> str | None:
        """A reason when the plan must stop for every chat, else None. Hard rule 1 (no API
        spend, ever): any `overage` window whose status is not `rejected` (the account is
        drawing paid extra usage) or any `credits_required` fact. Lasts until that fact's
        `resets_at` passes. Plan chats refuse sends and running ones are interrupted."""
        raise NotImplementedError


@dataclass(frozen=True)
class BackgroundCap:
    """Background chats stop at this share of the plan's five-hour window (R6, default 0.5).
    UI-editable in settings.toml [budgets]."""

    fraction: float

    def allows(self, ledger: UsageLedger) -> bool:
        """False when the plan's last seen five_hour utilization is at or above `fraction`,
        or when the plan is `rejected`. Unknown utilization allows.

        Best effort between `RateLimitEvent` transitions, stated to the operator on the
        usage page: the event fires only when a status changes (02a section 9, 02b F), so
        the cap acts on the last reading, which can lag the real 50% until the next
        transition (03 GB-9). A `rejected` status is itself a transition and is always seen.
        If check S10 shows `/usage` reaches Python, a meter chat that is not verbatim sends
        it on a timer for a fresher reading; Background chats never send it."""
        raise NotImplementedError


@dataclass(frozen=True)
class UsagePage:
    """What `Harness.usage()` returns and `GET /api/usage` serves. One read, no joins in
    the route."""

    windows: Mapping[ProfileName, tuple[WindowView, ...]]
    tokens: Mapping[ProfileName, Mapping[str, int]]
    """RunIndex sums per profile: input, output, cache read, cache write."""
    background_cap: float
    background_cap_note: str
    """Plain words: the cap acts on the last plan reading, not a live 50%."""
    hard_stop: str | None
    posture: MoneyPosture
    exposure: ExposureReport | None
    """None until the first probe ran. The page names each reachable secret in plain words,
    provider keys and `qmx/chatgpt` included."""
