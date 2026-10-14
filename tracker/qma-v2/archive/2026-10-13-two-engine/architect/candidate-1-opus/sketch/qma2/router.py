"""Route whole threads (never single requests) across accounts.

Pure. The thread actor calls `pick` only at turn boundaries: when a thread starts, when
the operator switches with a quote, and when a background thread hits a lockout or the
spare-window cap. A running request is never moved.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from qma2.model import Account, AccountId, Effort, LimitSnapshot, Origin, Route


@dataclass(frozen=True, slots=True)
class RouterPolicy:
    """UI-editable (qmx-control settings section `router`)."""

    background_claude_cap: float = 0.50  # background may use Claude only below 50% of 5h
    prefer: tuple[AccountId, ...] = ()  # operator's order; capable before cheap
    default_model: str = "claude-opus-5-5"
    default_effort: Effort = Effort.MEDIUM


@dataclass(frozen=True, slots=True)
class Need:
    origin: Origin
    model: str | None  # explicit model or None (profile/policy default)
    min_context: int
    needs_tools: bool = True
    needs_reasoning: bool = False


@dataclass(frozen=True, slots=True)
class AccountState:
    account: Account
    limits: Sequence[LimitSnapshot]
    healthy: bool  # last call did not fail auth; Claude preflight passed
    models: Sequence[str]  # served models with capabilities (OpenRouter supported_parameters)


@dataclass(frozen=True, slots=True)
class NoRoute:
    reason: str  # "claude window above background cap and no API account serves tools"
    retry_at: datetime | None


def pick(need: Need, accounts: Sequence[AccountState], policy: RouterPolicy, now: datetime) -> Route | NoRoute:
    """# TODO pseudocode
    # candidates = accounts that are healthy, not locked out, serve `need.model`
    #              (or any capable model when None) with tools + context
    # if need.origin is not OPERATOR: drop the Claude subscription when its five_hour
    #     utilization >= policy.background_claude_cap (unknown utilization counts as
    #     allowed only while the last snapshot status is "allowed")
    # order by policy.prefer, then capability, then most window left
    # return first as ClaudeRoute/OpenAIRoute, else NoRoute(reason, earliest reset)
    """
    raise NotImplementedError


def window_left(limits: Sequence[LimitSnapshot]) -> Mapping[str, float]:
    raise NotImplementedError
