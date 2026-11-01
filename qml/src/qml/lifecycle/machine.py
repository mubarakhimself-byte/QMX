"""One lifecycle per unit version per market, as a fold over events (Part A AD-115, CONTRACTS.md
section 8, standing order 7).

His clicks, the judge's verdicts and risk stops are events written by three writers on their own
partitions. ``fold`` orders them by ``(at, writer, sequence)`` and applies each through one
transition table. A move it refuses is kept as a rejected event with a typed reason, never
dropped. Only his click with principal ``operator`` moves toward paper or live; the one
exception is the judge's tested to paper, and only while ``lifecycle.auto_paper`` is on.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Final

__all__ = [
    "OPERATOR",
    "TRANSITIONS",
    "Actor",
    "ActorKind",
    "Event",
    "Folded",
    "MarketKey",
    "Refusal",
    "Rejected",
    "State",
    "Transition",
    "fold",
]

OPERATOR: Final = "operator"
"""His principal (``qmx_engine.service.context.Caller.principal`` of the user caller)."""


class State(StrEnum):
    DRAFT = "draft"
    TESTED = "tested"
    PARKED = "parked"
    PAPER = "paper"
    LIVE = "live"
    STOPPED = "stopped"
    RETIRED = "retired"


TRADING: Final = frozenset({State.PAPER, State.LIVE})


class ActorKind(StrEnum):
    JUDGE = "judge"
    HIS_CLICK = "his_click"
    RISK_RULE = "risk_rule"
    SYSTEM = "system"


@dataclass(frozen=True)
class Actor:
    kind: ActorKind
    principal: str


@dataclass(frozen=True)
class MarketKey:
    unit_id: str
    version_ref: str
    market_id: str


@dataclass(frozen=True)
class Event:
    """The ``qmx.lifecycle/1`` body, plus the journal's writer and sequence ``fold`` orders by."""

    event_id: str
    unit_id: str
    version_ref: str
    compiled_fingerprint: str
    market_id: str
    from_state: State
    to_state: State
    by: Actor
    reason: str
    evidence_ref: str | None
    at: datetime
    writer: str
    sequence: int
    clears: str | None = None
    """The stop event a move out of ``stopped`` clears; it must be the latest stop."""

    @property
    def key(self) -> MarketKey:
        return MarketKey(self.unit_id, self.version_ref, self.market_id)


@dataclass(frozen=True)
class Transition:
    from_state: State
    to_state: State
    actor: ActorKind
    needs_auto_paper: bool = False


def _rows() -> tuple[Transition, ...]:
    click, judge, risk = ActorKind.HIS_CLICK, ActorKind.JUDGE, ActorKind.RISK_RULE
    s = State
    named = (
        Transition(s.DRAFT, s.TESTED, judge),
        Transition(s.DRAFT, s.PARKED, judge),
        Transition(s.TESTED, s.PAPER, click),
        Transition(s.TESTED, s.PAPER, judge, needs_auto_paper=True),
        Transition(s.PAPER, s.LIVE, click),
        Transition(s.PAPER, s.STOPPED, risk),
        Transition(s.LIVE, s.STOPPED, risk),
        Transition(s.STOPPED, s.STOPPED, risk),
        Transition(s.STOPPED, s.PAPER, click),
        Transition(s.STOPPED, s.LIVE, click),
        Transition(s.LIVE, s.PARKED, click),
        Transition(s.PAPER, s.PARKED, click),
    )
    retire = tuple(Transition(state, s.RETIRED, click) for state in s if state is not s.RETIRED)
    return named + retire


TRANSITIONS: Final = _rows()
"""Who may cause each move. A stop on a stopped market records the newer stop. Paper to parked
is his click, so admitting a new version can park the one on paper in the same click (UT-23)."""


class Refusal(StrEnum):
    NOT_OPERATOR = "not_operator"
    """A click, or any move toward paper or live, whose principal is not ``operator``."""
    NOT_IN_TABLE = "not_in_table"
    AUTO_PAPER_OFF = "auto_paper_off"
    FROM_MISMATCH = "from_mismatch"
    STOP_NOT_CLEARED = "stop_not_cleared"
    SECOND_VERSION = "second_version"


@dataclass(frozen=True)
class Rejected:
    event: Event
    refusal: Refusal
    message: str


@dataclass(frozen=True)
class Folded:
    states: Mapping[MarketKey, State] = field(default_factory=dict[MarketKey, State])
    latest_stop: Mapping[MarketKey, str] = field(default_factory=dict[MarketKey, str])
    applied: tuple[Event, ...] = ()
    rejected: tuple[Rejected, ...] = ()

    def state(self, key: MarketKey) -> State:
        """A version with no event yet is a draft."""
        return self.states.get(key, State.DRAFT)


def _refusal(
    event: Event,
    current: State,
    folded: Folded,
    states: Mapping[MarketKey, State],
    auto_paper: bool,
) -> tuple[Refusal, str] | None:
    to, actor = event.to_state, event.by
    if actor.kind is ActorKind.HIS_CLICK and actor.principal != OPERATOR:
        return Refusal.NOT_OPERATOR, f"a click by {actor.principal!r} is not his click"
    judge_auto = actor.kind is ActorKind.JUDGE and current is State.TESTED and auto_paper
    if to in TRADING and actor.principal != OPERATOR and not (judge_auto and to is State.PAPER):
        return Refusal.NOT_OPERATOR, f"only his click moves a unit to {to}"
    is_stop = actor.kind is ActorKind.RISK_RULE and to is State.STOPPED
    if not is_stop and event.from_state is not current:
        return Refusal.FROM_MISMATCH, f"the market is {current}, not {event.from_state}"
    rows = [
        r for r in TRANSITIONS if (r.from_state, r.to_state, r.actor) == (current, to, actor.kind)
    ]
    if not rows:
        return Refusal.NOT_IN_TABLE, f"{actor.kind} cannot move {current} to {to}"
    if all(r.needs_auto_paper for r in rows) and not auto_paper:
        return (
            Refusal.AUTO_PAPER_OFF,
            "lifecycle.auto_paper is off, so tested to paper is his click",
        )
    if current is State.STOPPED and to is not State.STOPPED:
        latest = folded.latest_stop.get(event.key)
        if event.clears != latest:
            return Refusal.STOP_NOT_CLEARED, f"the latest stop is {latest}, not {event.clears}"
    if to in TRADING:
        for key, state in states.items():
            same = (key.unit_id, key.market_id) == (event.unit_id, event.market_id)
            if same and key.version_ref != event.version_ref and state in TRADING:
                return Refusal.SECOND_VERSION, (
                    f"{key.version_ref} is {state} on {key.market_id}; park or retire it first"
                )
    return None


def _apply(folded: Folded, event: Event, auto_paper: bool) -> Folded:
    states = dict(folded.states)
    current = folded.state(event.key)
    refused = _refusal(event, current, folded, states, auto_paper)
    if refused is not None:
        rejected = Rejected(event, *refused)
        return Folded(
            folded.states, folded.latest_stop, folded.applied, (*folded.rejected, rejected)
        )
    states[event.key] = event.to_state
    stops = dict(folded.latest_stop)
    if event.to_state is State.STOPPED:
        stops[event.key] = event.event_id
    return Folded(states, stops, (*folded.applied, event), folded.rejected)


def fold(events: Iterable[Event], *, auto_paper: bool = False) -> Folded:
    """The current state of every unit version on every market, and every refused move.

    An event id seen twice is applied once, so a replayed journal folds to the same answer."""
    seen: set[str] = set()
    folded = Folded()
    for event in sorted(events, key=lambda e: (e.at, e.writer, e.sequence)):
        if event.event_id in seen:
            continue
        seen.add(event.event_id)
        folded = _apply(folded, event, auto_paper)
    return folded
