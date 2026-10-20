"""Plan windows, the readings of how much of them is used, the overage stop and the usage page.

These belong to the account rather than to a chat. A plan chat's CLI reports them as rate-limit
events and `/usage` text, which `qma.harness.project` reads into the facts below.

Many chats report the same account's windows. Each report is a timestamped fact and `record`
keeps the newest per window, so the merge is commutative and idempotent. Everything runs on the
harness's event loop, so there is no lock.

Per account (AD-12, RTR4). `UsagePage.accounts` carries every pool account as the Accounts
screen reads it: its state, the leases it holds now, the reading the provider last gave it and
the models it is cooling for. A plan window belongs to one plan account; a key account has no
window, so its reading is the provider's own or absent.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, Literal, get_args

from qmx_router.pool import AccountView
from qmx_router.profiles import PLAN

type LimitStatus = Literal["allowed", "allowed_warning", "rejected"]
type Window = Literal[
    "five_hour",
    "seven_day",
    "seven_day_opus",
    "seven_day_sonnet",
    "seven_day_overage_included",
    "overage",
]
"""The `rateLimitType` values in Claude Code 2.1.296's `rate_limit_info` schema."""
STATUSES: Final[frozenset[str]] = frozenset(get_args(LimitStatus.__value__))
WINDOWS: Final[frozenset[str]] = frozenset(get_args(Window.__value__))


@dataclass(frozen=True)
class Reading:
    """How much of a plan window is used, as a fraction from 0 to 1."""

    window: str
    utilization: float
    resets_at: datetime | None


@dataclass(frozen=True)
class Limits:
    """From `RateLimitEvent`. Every field the SDK's `RateLimitInfo` models, plus what the CLI
    sends in `raw` that the SDK does not model."""

    window: Window | None
    status: LimitStatus
    utilization: float | None
    resets_at: datetime | None
    overage_status: LimitStatus | None
    overage_resets_at: datetime | None
    overage_disabled_reason: str | None
    using_overage: bool | None
    """True if `raw["isUsingOverage"]` or `raw["overageInUse"]` is True; None when both are
    absent."""
    overage_enabled: bool | None
    """`raw["overageEnabled"]`."""
    credits_required: bool
    """`raw["errorCode"]` is `credits_required`, or `raw` has a `credits_required` key."""
    readings: tuple[Reading, ...] = ()
    """`raw["unifiedWindows"]`: the five-hour and weekly use the CLI reports on any window's
    event."""


@dataclass(frozen=True)
class UnreadableLimits:
    """A rate-limit event this code cannot read. The overage stop treats it as paid use."""

    reason: str


@dataclass(frozen=True)
class PlanMeter:
    """The plan's use as the CLI's `/usage` text states it: the session as `five_hour`, the
    all-models week as `seven_day`."""

    readings: tuple[Reading, ...]


type PlanFact = Limits | UnreadableLimits | PlanMeter


EXTRA_USAGE_ON: Final = (
    "extra usage is on for this account; switch it off at claude.ai so the plan can never bill"
)


def overage_rule(limits: Limits) -> str | None:
    """The first overage rule this fact breaks, named, or None. Hard rule 1: no paid use.
    1. `using_overage` is True: the account is drawing paid extra usage now.
    2. A plan window is `rejected` and `overage_status` is not `rejected`: the next request
       could draw paid extra usage. A missing `overage_status` counts, since nothing says
       extra usage is off.
    3. An `overage` window that is not `rejected`, unless the same fact says `using_overage`
       is False.
    4. The CLI reports credits required.
    A plan window `rejected` with `overage_status` `rejected` is no stop: the CLI refuses
    natively and the page shows the window and its reset."""
    name = limits.window or "unnamed"
    if limits.using_overage is True:
        return f"rule 1: the plan is drawing paid extra usage ({name} window)"
    if (
        limits.window != "overage"
        and limits.status == "rejected"
        and limits.overage_status != "rejected"
    ):
        extra = limits.overage_status or "not reported"
        return (
            f"rule 2: the {name} window is used up and paid extra usage is {extra}, "
            "so the next request could bill"
        )
    if (
        limits.window == "overage"
        and limits.status != "rejected"
        and limits.using_overage is not False
    ):
        return f"rule 3: the overage window is {limits.status}"
    if limits.credits_required:
        return f"rule 4: the CLI reports that credits are required ({name} window)"
    return None


def _ends(limits: Limits) -> datetime | None:
    stamps = [stamp for stamp in (limits.resets_at, limits.overage_resets_at) if stamp is not None]
    return max(stamps) if stamps else None


@dataclass(frozen=True)
class WindowView:
    limits: Limits
    as_of: datetime
    """When QMA heard it. The CLI sends a rate-limit event when a status changes, so the UI
    labels it "as of the last QMX turn"."""


@dataclass(frozen=True)
class ReadingView:
    reading: Reading
    as_of: datetime
    source: Literal["rate_limit_event", "usage_command"]


def _now() -> datetime:
    return datetime.now(UTC)


class UsageLedger:
    """`path`, when given, keeps the window facts and the unreadable mark across restarts, so a
    restart never lifts a stop. A saved file that cannot be read stops the plan."""

    def __init__(self, clock: Callable[[], datetime] = _now, path: Path | None = None) -> None:
        self.clock = clock
        self.path = path
        self._windows: dict[Window | None, WindowView] = {}
        self._readings: dict[str, ReadingView] = {}
        self._unreadable: tuple[str, datetime] | None = None
        if path is not None:
            self._load(path)

    def _load(self, path: Path) -> None:
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            windows = [
                WindowView(_saved_limits(view["limits"]), datetime.fromisoformat(view["as_of"]))
                for view in saved["windows"]
            ]
            mark = saved["unreadable"]
            unreadable = None if mark is None else (str(mark[0]), datetime.fromisoformat(mark[1]))
        except FileNotFoundError:
            return
        except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
            reason = f"the saved plan usage at {path} could not be read ({type(error).__name__})"
            self._unreadable = (reason, self.clock())
            return
        self._windows = {view.limits.window: view for view in windows}
        self._unreadable = unreadable
        for view in windows:
            self._read(_readings_of(view.limits), view.as_of, "rate_limit_event")

    def _save(self) -> None:
        if self.path is None:
            return
        saved = {
            "windows": [
                {
                    "limits": _plain(asdict(view.limits), keep_readings=True),
                    "as_of": view.as_of.isoformat(),
                }
                for view in self._windows.values()
            ],
            "unreadable": None
            if self._unreadable is None
            else [self._unreadable[0], self._unreadable[1].isoformat()],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        draft = self.path.with_suffix(".tmp")
        draft.write_text(json.dumps(saved), encoding="utf-8")
        draft.replace(self.path)

    def record(self, fact: PlanFact, at: datetime) -> None:
        """Keep the newest fact per window. A replayed or older fact changes nothing. An
        unreadable event stops the plan until a newer readable event arrives: every event
        carries the account's overage fields, whatever its window."""
        match fact:
            case UnreadableLimits(reason=reason):
                newest = max((view.as_of for view in self._windows.values()), default=None)
                held = self._unreadable
                if (newest is None or newest < at) and (held is None or held[1] < at):
                    self._unreadable = (reason, at)
                    self._save()
                return
            case Limits():
                held_view = self._windows.get(fact.window)
                if held_view is not None and held_view.as_of >= at:
                    return
                self._windows[fact.window] = WindowView(fact, at)
                if self._unreadable is not None and self._unreadable[1] < at:
                    self._unreadable = None
                self._save()
                self._read(_readings_of(fact), at, "rate_limit_event")
            case PlanMeter(readings=readings):
                self._read(readings, at, "usage_command")

    def _read(
        self,
        readings: tuple[Reading, ...],
        at: datetime,
        source: Literal["rate_limit_event", "usage_command"],
    ) -> None:
        for reading in readings:
            held = self._readings.get(reading.window)
            if held is None or held.as_of < at:
                self._readings[reading.window] = ReadingView(reading, at, source)

    def windows(self) -> tuple[WindowView, ...]:
        """A fact whose latest reset has passed is dropped on read, not by a timer."""
        now = self.clock()
        live = [view for view in self._windows.values() if _live(_ends(view.limits), now)]
        return tuple(sorted(live, key=lambda view: view.limits.window or ""))

    def readings(self) -> tuple[ReadingView, ...]:
        now = self.clock()
        live = [view for view in self._readings.values() if _live(view.reading.resets_at, now)]
        return tuple(sorted(live, key=lambda view: view.reading.window))

    def reading(self, window: str) -> ReadingView | None:
        return next((view for view in self.readings() if view.reading.window == window), None)

    def hard_stop(self) -> str | None:
        """Why every plan chat must stop now, or None. The stop lasts until a newer fact for
        that window clears it or the latest of its resets passes."""
        if self._unreadable is not None:
            return self._unreadable[0]
        return next((rule for view in self.windows() if (rule := overage_rule(view.limits))), None)

    def rejected(self) -> bool:
        """A plan window is used up. A `rejected` overage window means paid extra use is
        refused, the safe state, so it does not count."""
        return any(
            view.limits.status == "rejected" and view.limits.window != "overage"
            for view in self.windows()
        )

    def extra_usage_on(self) -> bool | None:
        """From the newest plan fact: True when `overage_enabled` is True or `overage_status`
        is `allowed` or `allowed_warning`. None when no fact says. Informational; the stop is
        `hard_stop`."""
        views = self.windows()
        if not views:
            return None
        newest = max(views, key=lambda view: view.as_of).limits
        if newest.overage_enabled is None and newest.overage_status is None:
            return None
        return newest.overage_enabled is True or newest.overage_status in {
            "allowed",
            "allowed_warning",
        }


def _readings_of(limits: Limits) -> tuple[Reading, ...]:
    """The readings a rate-limit fact carries, its own window's included."""
    own = (
        (Reading(limits.window, limits.utilization, limits.resets_at),)
        if limits.window is not None and limits.utilization is not None
        else ()
    )
    return limits.readings + own


def _live(ends: datetime | None, now: datetime) -> bool:
    return ends is None or now < ends


@dataclass(frozen=True)
class UsagePage:
    """What `Harness.usage()` returns and `GET /api/usage` serves."""

    windows: tuple[WindowView, ...]
    readings: tuple[ReadingView, ...]
    tokens: Mapping[str, Mapping[str, int]]
    """Per profile: input, output, cache read and cache write tokens, and `calls`."""
    hard_stop: str | None
    extra_usage_on: bool | None
    accounts: tuple[AccountView, ...] = ()
    """Every pool account, by provider: its state, live leases and last reading (AD-12)."""

    def document(self) -> dict[str, Any]:
        return {
            "windows": {
                PLAN: [
                    {**_plain(asdict(view.limits)), "as_of": view.as_of.isoformat()}
                    for view in self.windows
                ]
            },
            "readings": {
                PLAN: [
                    {
                        **_plain(asdict(view.reading)),
                        "as_of": view.as_of.isoformat(),
                        "source": view.source,
                    }
                    for view in self.readings
                ]
            },
            "tokens": {profile: dict(sums) for profile, sums in self.tokens.items()},
            "hard_stop": self.hard_stop,
            "extra_usage_on": self.extra_usage_on,
            "extra_usage_note": EXTRA_USAGE_ON if self.extra_usage_on else None,
            "accounts": [view.document() for view in self.accounts],
        }


def _plain(fields: dict[str, Any], *, keep_readings: bool = False) -> dict[str, Any]:
    plain = {
        key: value.isoformat() if isinstance(value, datetime) else value
        for key, value in fields.items()
        if key != "readings"
    }
    if keep_readings:
        plain["readings"] = [_plain(reading) for reading in fields["readings"]]
    return plain


def _moment(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(value)
    return datetime.fromisoformat(value)


def _one_of(value: object, allowed: frozenset[str], *, optional: bool) -> Any:
    if (value is None and optional) or (isinstance(value, str) and value in allowed):
        return value
    raise ValueError(value)


def _saved_limits(saved: dict[str, Any]) -> Limits:
    """A `Limits` written by `_save`, checked as strictly as a CLI event."""
    flags = [saved[key] for key in ("using_overage", "overage_enabled")]
    if any(flag is not None and not isinstance(flag, bool) for flag in flags):
        raise TypeError(flags)
    if not isinstance(saved["credits_required"], bool):
        raise TypeError(saved["credits_required"])
    return Limits(
        window=_one_of(saved["window"], WINDOWS, optional=True),
        status=_one_of(saved["status"], STATUSES, optional=False),
        utilization=None if saved["utilization"] is None else float(saved["utilization"]),
        resets_at=_moment(saved["resets_at"]),
        overage_status=_one_of(saved["overage_status"], STATUSES, optional=True),
        overage_resets_at=_moment(saved["overage_resets_at"]),
        overage_disabled_reason=saved["overage_disabled_reason"],
        using_overage=flags[0],
        overage_enabled=flags[1],
        credits_required=saved["credits_required"],
        readings=tuple(
            Reading(str(r["window"]), float(r["utilization"]), _moment(r["resets_at"]))
            for r in saved["readings"]
        ),
    )


def usage_page(
    ledger: UsageLedger,
    tokens: Mapping[str, Mapping[str, int]],
    accounts: Iterable[AccountView] = (),
) -> UsagePage:
    """The page: the plan's windows and readings, the token sums, and every account's row."""
    return UsagePage(
        windows=ledger.windows(),
        readings=ledger.readings(),
        tokens=tokens,
        hard_stop=ledger.hard_stop(),
        extra_usage_on=ledger.extra_usage_on(),
        accounts=tuple(accounts),
    )
