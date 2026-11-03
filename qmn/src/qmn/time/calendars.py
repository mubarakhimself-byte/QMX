"""Three named calendar kinds and the activation day-boundary seam (TN-14).

Never a bare ``calendar``. Market-hours, account-scoped day-boundary (accounting),
and news calendars are distinct identities; local time and broker server time
never substitute for them (DEC-0106, DEC-0199). Activation takes effect at the
next day boundary of the account-scoped day-boundary calendar (DEC-0261) — the
full period runner is Epic 26 / TN-25; this module owns the named seam.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from functools import cache
from pathlib import Path
from types import MappingProxyType
from typing import Final, Protocol, cast

from qmb.data.gap_check import OpenTime, open_time
from qmf.core import CalendarIdentity, Instant, Ok, Result, TradingDate
from qmf.core.refusal import is_refusal

from qmn.time._refuse import clean_token, invalid, policy

__all__ = [
    "BANNED_BARE_CALENDAR",
    "BANNED_TIME_SUBSTITUTES",
    "CALENDAR_IDENTITIES",
    "CALENDAR_TIMER_KINDS",
    "CALENDAR_WARN_DAYS",
    "NAMED_TIME_RULES",
    "ActivationSchedule",
    "CalendarKind",
    "DayBoundaryCalendarPort",
    "MarketCalendar",
    "activation_effective_trading_date",
    "calendar_identities",
    "calendar_kind_from_token",
    "market_calendars",
    "named_time_rules",
    "refuse_bare_calendar_token",
    "refuse_time_substitute",
]

EXTENSIONS: Final = Path(__file__).resolve().parents[4] / "extensions"
"""The checkout's ``extensions/``, where each ``qmf-calendar-*`` package ships its market-hours
calendars as ``qmx.calendar/1`` files, read from the checkout the node runs from as QMB reads
them."""
CALENDAR_WARN_DAYS: Final = 30
"""How close to the last day its data covers a market-hours calendar shows on the node's status:
30 days, the starting default of `[node] calendar_warn_days`. The node reads no settings file
yet, so this value holds until one does; the host doctor reads its own
`clock.calendar_warn_days`."""

BANNED_BARE_CALENDAR: Final[str] = "calendar"
BANNED_TIME_SUBSTITUTES: Final[frozenset[str]] = frozenset(
    {
        "local time",
        "local-time",
        "local_time",
        "broker server time",
        "broker-server-time",
        "broker_server_time",
        "host local time",
        "host-local-time",
    }
)

CALENDAR_IDENTITIES: Final[tuple[str, ...]] = (
    "market_hours_calendar",
    "day_boundary_calendar",
    "news_calendar",
)

# Qualified timer names — never a bare "calendar timer" without its kind.
CALENDAR_TIMER_KINDS: Final[tuple[str, ...]] = (
    "news_calendar_timer",
    "accounting_calendar_timer",
    "trading_calendar_timer",
    "market_hours_calendar_timer",
)

NAMED_TIME_RULES: Final[tuple[str, ...]] = (
    "news calendar",
    "accounting calendar",
    "trading calendar",
    "market-hours calendar",
    "calendar timer",
    "day-boundary calendar",
)


class CalendarKind(StrEnum):
    """The three TN-14 / AD-8 calendar kinds — never conflated."""

    MARKET_HOURS = "market_hours_calendar"
    DAY_BOUNDARY = "day_boundary_calendar"
    NEWS = "news_calendar"


class DayBoundaryCalendarPort(Protocol):
    """Account-scoped day-boundary calendar — Epic 26 fills the period runner."""

    def trading_date_for(self, instant: Instant) -> Result[TradingDate]:
        """Map an Instant onto the account day-boundary TradingDate."""
        ...

    def next_boundary_after(self, instant: Instant) -> Result[Instant]:
        """Next day-boundary Instant after ``instant`` (activation effective-at)."""
        ...

    @property
    def identity(self) -> CalendarIdentity:
        """In-band calendar identity carried on every TradingDate."""
        ...


@dataclass(frozen=True, slots=True)
class ActivationSchedule:
    """Activation deferred to the next account day-boundary (DEC-0261).

    A mid-day promote/activate does not trade until the next trading day under
    the account-scoped day-boundary calendar. Epic 26 consumes this seam.
    """

    binding_id: str
    signed_at: Instant
    effective_at: Instant
    day_boundary_calendar: CalendarIdentity
    calendar_kind: CalendarKind = CalendarKind.DAY_BOUNDARY

    def as_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "binding_id": self.binding_id,
                "signed_at_ns": self.signed_at.value_ns,
                "effective_at_ns": self.effective_at.value_ns,
                "calendar_kind": self.calendar_kind.value,
                "day_boundary_rule_set": self.day_boundary_calendar.rule_set,
                "day_boundary_rule_set_version": self.day_boundary_calendar.rule_set_version,
                "tzdata_version": self.day_boundary_calendar.tzdata_version,
            }
        )


def calendar_identities() -> tuple[str, ...]:
    """The three named calendar identities; never a bare calendar."""
    return CALENDAR_IDENTITIES


def named_time_rules() -> tuple[str, ...]:
    """Qualified time-rule names allowed in configuration and prose."""
    return NAMED_TIME_RULES


def refuse_bare_calendar_token(token: object) -> Result[str]:
    """Refuse a bare ``calendar``; accept only a named calendar kind."""
    raw = clean_token(token)
    if raw is None:
        return invalid(
            "token",
            "a calendar kind token is a non-empty named identity",
            given=repr(token),
        )
    normalized = raw.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {BANNED_BARE_CALENDAR, "calendars"}:
        return policy(
            "calendar",
            "never a bare calendar — name market-hours, day-boundary/accounting, "
            "or news (DEC-0106)",
            given=raw,
            allowed=list(CALENDAR_IDENTITIES),
        )
    return Ok(raw)


def refuse_time_substitute(label: object) -> Result[str]:
    """Refuse local time / broker server time as a calendar or stamp substitute."""
    raw = clean_token(label)
    if raw is None:
        return invalid("label", "a time-rule label is a non-empty string", given=repr(label))
    normalized = raw.strip().lower().replace("_", " ").replace("-", " ")
    # Collapse repeated spaces for matching.
    collapsed = " ".join(normalized.split())
    banned_collapsed = {
        " ".join(item.replace("_", " ").replace("-", " ").split())
        for item in BANNED_TIME_SUBSTITUTES
    }
    if collapsed in banned_collapsed:
        return policy(
            "time_substitute",
            "local time and broker server time never substitute for a named "
            "calendar or the injected VPS clock (DEC-0199)",
            given=raw,
        )
    return Ok(raw)


def calendar_kind_from_token(token: object) -> Result[CalendarKind]:
    """Map a named token onto one of the three calendar kinds."""
    checked = refuse_bare_calendar_token(token)
    if is_refusal(checked):
        return checked
    raw = checked.value
    normalized = raw.strip().lower().replace("-", "_").replace(" ", "_")
    aliases: dict[str, CalendarKind] = {
        "market_hours_calendar": CalendarKind.MARKET_HOURS,
        "market_hours": CalendarKind.MARKET_HOURS,
        "trading_calendar": CalendarKind.MARKET_HOURS,
        "trading": CalendarKind.MARKET_HOURS,
        "day_boundary_calendar": CalendarKind.DAY_BOUNDARY,
        "day_boundary": CalendarKind.DAY_BOUNDARY,
        "accounting_calendar": CalendarKind.DAY_BOUNDARY,
        "accounting": CalendarKind.DAY_BOUNDARY,
        "news_calendar": CalendarKind.NEWS,
        "news": CalendarKind.NEWS,
    }
    kind = aliases.get(normalized)
    if kind is None:
        return invalid(
            "token",
            "calendar kind is market_hours_calendar | day_boundary_calendar | news_calendar",
            given=raw,
            allowed=list(CALENDAR_IDENTITIES),
        )
    return Ok(kind)


def activation_effective_trading_date(
    *,
    binding_id: object,
    signed_at: object,
    day_boundary: object,
) -> Result[ActivationSchedule]:
    """Schedule activation at the next account day-boundary (DEC-0261 / FR-073).

    ``day_boundary`` is a :class:`DayBoundaryCalendarPort`. Epic 26 owns the
    period runner; this story only disciplines the named seam.
    """
    bid = clean_token(binding_id)
    if bid is None:
        return invalid(
            "binding_id",
            "activation is scoped to a non-empty binding id",
            given=repr(binding_id),
        )
    if not isinstance(signed_at, Instant):
        return invalid(
            "signed_at",
            "activation signs at an Instant from the injected clock",
            given=repr(type(signed_at).__name__),
        )
    if not _looks_like_day_boundary(day_boundary):
        return invalid(
            "day_boundary",
            "activation uses the account-scoped day-boundary calendar port "
            "(never market-hours or news)",
            given=repr(type(day_boundary).__name__),
        )
    port = cast("DayBoundaryCalendarPort", day_boundary)
    identity = port.identity
    effective: Result[Instant] = port.next_boundary_after(signed_at)
    if is_refusal(effective):
        return effective
    boundary = effective.value
    if boundary.value_ns <= signed_at.value_ns:
        return policy(
            "effective_at",
            "activation effective_at must be strictly after signed_at at the "
            "next day-boundary of the account-scoped day-boundary calendar",
            signed_at_ns=signed_at.value_ns,
            effective_at_ns=boundary.value_ns,
        )
    return Ok(
        ActivationSchedule(
            binding_id=bid,
            signed_at=signed_at,
            effective_at=boundary,
            day_boundary_calendar=identity,
            calendar_kind=CalendarKind.DAY_BOUNDARY,
        )
    )


@dataclass(frozen=True, slots=True)
class MarketCalendar:
    """One shipped market-hours calendar: its open time, and the last day its data covers
    (``issued`` plus ``max_age_days``), after which its weekly sessions still hold but no closure
    is known."""

    hours: OpenTime
    last_day: date

    def open_at(self, at_ns: int) -> bool:
        return self.hours.open_at(at_ns)

    def note(self, now_ns: int, warn_days: int = CALENDAR_WARN_DAYS) -> str | None:
        """A status line when ``now_ns`` is within ``warn_days`` of the last day, or past it."""
        today = datetime.fromtimestamp(now_ns / 1e9, UTC).date()
        left = (self.last_day - today).days
        if left > warn_days:
            return None
        ref, last = self.hours.ref, self.last_day.isoformat()
        if left < 0:
            return (
                f"The market calendar {ref} ended on {last}, {-left} days ago; its weekly "
                "sessions still hold, but no closure after it is known."
            )
        return f"The market calendar {ref} covers days up to {last}, {left} days from now."


@cache
def market_calendars(folder: Path = EXTENSIONS) -> Mapping[str, MarketCalendar]:
    """Every market-hours calendar the ``qmf-calendar-*`` packages ship, by ref. A file that
    cannot be read is left out, named once on stderr, so the node starts and reads it as
    missing."""
    found: dict[str, MarketCalendar] = {}
    for path in sorted(folder.glob("qmf-calendar-*/src/qmf/calendar_*/calendars/*.json")):
        try:
            calendar = _market_calendar(path)
        except (OSError, ValueError, KeyError, TypeError) as error:
            note = {"event": "calendar_unreadable", "file": path.name}
            print(json.dumps({**note, "error": type(error).__name__}), file=sys.stderr)
            continue
        if calendar is not None:
            found[calendar.hours.ref] = calendar
    return MappingProxyType(found)


def _market_calendar(path: Path) -> MarketCalendar | None:
    document = cast("Mapping[str, object]", json.loads(path.read_text(encoding="utf-8")))
    ref, issued, age = document["calendar_ref"], document["issued"], document["max_age_days"]
    hours = open_time(str(ref))
    if hours is None or not isinstance(issued, str) or not isinstance(age, int):
        return None
    return MarketCalendar(hours, date.fromisoformat(issued) + timedelta(days=age))


def _looks_like_day_boundary(port: object) -> bool:
    return (
        hasattr(port, "trading_date_for")
        and hasattr(port, "next_boundary_after")
        and hasattr(port, "identity")
        and callable(getattr(port, "trading_date_for", None))
        and callable(getattr(port, "next_boundary_after", None))
    )
