"""Plan windows, the overage stop and the usage page.

Per-turn tokens and cost live in each chat's run journal as `model_call` rows. A plan chat
writes one per turn from its `ResultMessage` through `plan_row`; a relayed chat's rows come from
the relay. This module keeps what belongs to the account rather than to a chat: the plan's
rate-limit windows, the readings of how much of them is used, and the overage stop.

Many chats report the same account's windows. Each report is a timestamped fact and `record`
keeps the newest per window, so the merge is commutative and idempotent. Everything runs on the
harness's event loop, so there is no lock.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import asdict, astuple, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, Literal

from qma.harness.home import DoctorLine, QmxHome, SessionId
from qma.harness.profiles import PLAN
from qma.harness.project import (
    STATUSES,
    WINDOWS,
    Limits,
    PlanFact,
    PlanMeter,
    Reading,
    TurnUsage,
    UnreadableLimits,
    Window,
)

EXTRA_USAGE_ON: Final = (
    "extra usage is on for this account; switch it off at claude.ai so the plan can never bill"
)
TOKEN_FIELDS: Final = ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens")


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
class Totals:
    """A CLI process's running usage totals, summed over models."""

    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @classmethod
    def of(cls, turn: TurnUsage) -> Totals:
        models = list(turn.model_usage.values())

        def total(key: str) -> int:
            return sum(int(model.get(key, 0)) for model in models)

        cost = turn.total_cost_usd
        if cost is None:
            cost = sum(float(model.get("costUSD", 0)) for model in models)
        return cls(
            cost_usd=cost,
            input_tokens=total("inputTokens"),
            output_tokens=total("outputTokens"),
            cache_read_tokens=total("cacheReadInputTokens"),
            cache_write_tokens=total("cacheCreationInputTokens"),
        )

    def since(self, base: Totals) -> Totals:
        """What was spent after `base`. A process that did not carry `base` over reports less
        than it, and then all it reports is new."""
        now, before = astuple(self), astuple(base)
        if any(value < held for value, held in zip(now, before, strict=True)):
            return self
        cost = round(self.cost_usd - base.cost_usd, 12)
        tokens = (value - held for value, held in zip(now[1:], before[1:], strict=True))
        return Totals(cost, *tokens)


def plan_row(turn: TurnUsage, base: Totals) -> tuple[dict[str, Any] | None, Totals]:
    """The `model_call` payload for one plan turn and the new running totals. None when the
    turn spent nothing, as a local command such as `/usage` does."""
    totals = Totals.of(turn)
    spent = totals.since(base)
    if spent == Totals():
        return None, totals
    payload: dict[str, Any] = {
        "agent": "primary",
        "model": ",".join(sorted(turn.model_usage)),
        "profile": PLAN,
        "path": "result",
        "input_tokens": spent.input_tokens,
        "output_tokens": spent.output_tokens,
        "cache_read_tokens": spent.cache_read_tokens,
        "cache_write_tokens": spent.cache_write_tokens,
        "metadata": {"cost": spent.cost_usd},
        "running_totals": asdict(totals),
    }
    return payload, totals


def journal_path(home: QmxHome, session: SessionId) -> Path:
    return home.root / "runs" / session / "journal.jsonl"


def plan_base(journal: Path) -> Totals:
    """The running totals after the last plan turn journaled for this chat. A resumed CLI
    starts from the session's earlier totals (measured, CLI 2.1.299)."""
    if not journal.exists():
        return Totals()
    base = Totals()
    for line in journal.read_bytes().splitlines():
        if b'"running_totals"' in line:
            payload = json.loads(line)["payload"]
            base = Totals(**payload["running_totals"])
    return base


def token_sums(runs: Path, chat: str = "*") -> dict[str, dict[str, int]]:
    """`model_call` rows summed per profile over every chat's run journal, or one `chat`'s,
    with a row count."""
    sums: dict[str, dict[str, int]] = {}
    for journal in sorted(runs.glob(f"{chat}/journal.jsonl")):
        for line in journal.read_bytes().splitlines():
            if b'"model_call"' not in line:
                continue
            try:
                record = json.loads(line)
                payload = record["payload"]
                if record["event"] != "model_call":
                    continue
                row = {key: int(payload.get(key) or 0) for key in TOKEN_FIELDS}
                profile = str(payload.get("profile", "unknown"))
            except ValueError, KeyError, TypeError:
                continue
            held = sums.setdefault(profile, dict.fromkeys((*TOKEN_FIELDS, "calls"), 0))
            for key, value in row.items():
                held[key] += value
            held["calls"] += 1
    return sums


@dataclass(frozen=True)
class UsagePage:
    """What `Harness.usage()` returns and `GET /api/usage` serves."""

    windows: tuple[WindowView, ...]
    readings: tuple[ReadingView, ...]
    tokens: Mapping[str, Mapping[str, int]]
    """Per profile: input, output, cache read and cache write tokens, and `calls`."""
    hard_stop: str | None
    extra_usage_on: bool | None

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
) -> UsagePage:
    return UsagePage(
        windows=ledger.windows(),
        readings=ledger.readings(),
        tokens=tokens,
        hard_stop=ledger.hard_stop(),
        extra_usage_on=ledger.extra_usage_on(),
    )


def usage_lines(ledger: UsageLedger) -> list[DoctorLine]:
    stop = ledger.hard_stop()
    on = ledger.extra_usage_on()
    detail = {
        True: EXTRA_USAGE_ON,
        False: "extra usage is off for this account",
        None: "no plan reading yet",
    }[on]
    return [
        DoctorLine("plan overage stop", stop is None, stop or "no stop"),
        DoctorLine("plan extra usage", on is not True, detail),
    ]
