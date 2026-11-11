"""Calibrated motion as a pure function of the unit's own closed trades (AD-103, L0 AD-22).

A calibrated number moves only at its cadence: after every ``every`` closed trades it has read
(the dummy's 20). Each run hands the trades read so far to the number's rule block, which
answers nothing below the number's ``min_count`` and otherwise a value at most ``step_limit``
steps away, shrunk toward the default by n/(n+k) and inside the range. A run that is due while
the unit holds a position waits for the first flat instant, so a number never moves
mid-position.

The state carries everything the rule needs (the trades read, as their stamp and R) and a
watermark, so a host feeds ``own_journal`` only the trades this run or deployment closed and a
restored unit reads each trade once. A number that states a ``window`` keeps only its newest
trades, so the engine's memory is the number's own bound and never the journal's length; each
trade reaches the rule under ``stamp`` beside ``strength``, so a rule bound to a risk number reads
the risk number's own value in force at entry.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Final

from qmf.core.chrono import Instant

from qml.blocks.api import Instance
from qml.unit.model import Side

__all__ = [
    "MIN_TRADES",
    "SHRINK_K",
    "SLOW_CADENCE_TRADES",
    "ClosedTrade",
    "Move",
    "ScaledNumber",
    "SlowNumber",
    "SlowState",
    "TradeRange",
    "calibrate",
    "scale",
]

MIN_TRADES: Final[int] = 60
"""Starting default of the ``min_trades`` setting, for a number that declares no ``min_count``."""
SHRINK_K: Final[int] = 100
"""Starting default of the ``shrink_k`` setting."""
SLOW_CADENCE_TRADES: Final[int] = 20
"""Starting default of the ``slow_cadence`` setting's trade count."""


@dataclass(frozen=True, slots=True)
class ClosedTrade:
    """One ``own_journal`` row (CONTRACTS.md section 4.5), knowable at ``closed_at``."""

    trade_id: str
    opened_at: Instant
    closed_at: Instant
    side: Side
    market_id: str
    world: str
    r_after_costs: Decimal
    entry_stamps: Mapping[str, Decimal]


@dataclass(frozen=True, slots=True)
class SlowNumber:
    """A calibrated number as compiled: its rule, the entry stamp the rule reads, its cadence,
    the trades it must have read before it runs, and the most it keeps."""

    name: str
    rule_pin: str
    stamp: str
    every: int
    min_trades: int = MIN_TRADES
    window: int | None = None
    """The most trades the rule reads: ``None`` keeps every trade, as before AD-14's window."""


@dataclass(frozen=True, slots=True)
class SlowState:
    value: Decimal
    read: tuple[tuple[str, Decimal, Decimal], ...] = ()
    """``(trade_id, stamp, r_after_costs)`` of the newest trades read, at most ``window`` deep."""
    watermark: tuple[int, str] | None = None
    """``(closed_at ns, trade_id)`` of the last trade read."""
    read_total: int = 0
    """Every stamped trade this number has read, the ones a window dropped included."""
    read_at_last_run: int = 0
    """``read_total`` when the rule last ran, so a bounded read still knows its cadence."""


@dataclass(frozen=True, slots=True)
class ScaledNumber:
    """A ``scaled`` number as compiled: the fact it follows, the multiple it applies, and its own
    range, so a fact outside the range cannot carry the number out of it (AD-14's track)."""

    name: str
    fact: str
    multiple: Decimal
    low: Decimal
    high: Decimal


@dataclass(frozen=True, slots=True)
class TradeRange:
    from_trade_id: str
    to_trade_id: str
    count: int


@dataclass(frozen=True, slots=True)
class Move:
    """What one cadence run answered: the old and new value, the trades it read, and their mean R
    and mean stamp, signed as stamped."""

    old: Decimal
    new: Decimal
    read_trades: TradeRange
    watermark: Instant
    mean_r: Decimal
    mean_stamp: Decimal


def scale(number: ScaledNumber, fact: Decimal | None) -> Decimal | None:
    """The number's value on a bar whose fact reads ``fact``: the fact times the multiple, held
    inside the number's range. A fact no reader supplied answers nothing, so the number keeps the
    value it already had."""
    if fact is None:
        return None
    return min(number.high, max(number.low, number.multiple * fact))


def _key(trade: ClosedTrade) -> tuple[int, str]:
    return (trade.closed_at.value_ns, trade.trade_id)


def _read(
    number: SlowNumber, state: SlowState, trades: Sequence[ClosedTrade], instant: Instant
) -> SlowState:
    fresh = sorted(
        (
            t
            for t in trades
            if t.closed_at.value_ns <= instant.value_ns
            and (state.watermark is None or _key(t) > state.watermark)
        ),
        key=_key,
    )
    if not fresh:
        return state
    rows = tuple(
        (t.trade_id, t.entry_stamps[number.stamp], t.r_after_costs)
        for t in fresh
        if number.stamp in t.entry_stamps
    )
    read = state.read + rows
    if number.window is not None:
        read = read[-number.window :]
    return replace(
        state, read=read, watermark=_key(fresh[-1]), read_total=state.read_total + len(rows)
    )


def calibrate(
    number: SlowNumber,
    rule: Instance,
    state: SlowState,
    trades: Sequence[ClosedTrade],
    *,
    instant: Instant,
    flat: bool,
) -> tuple[SlowState, Move | None]:
    """Read the trades knowable at ``instant`` and, when the cadence is due, the number has read
    ``min_trades`` and the unit is flat, run the rule once. A trade without the stamp the rule
    reads is passed over, and the rule reads only the newest ``window`` of them."""
    state = _read(number, state, trades, instant)
    due = (
        state.read_total - state.read_at_last_run >= number.every
        and state.read_total >= number.min_trades
    )
    if not due or not flat:
        return state, None
    answer = rule.update(
        {
            "trades": [{"stamp": stamp, "strength": stamp, "r": r} for _, stamp, r in state.read],
            "current": state.value,
        }
    )
    ran = replace(state, read_at_last_run=state.read_total)
    if not isinstance(answer, Decimal) or state.watermark is None or not state.read:
        return ran, None
    move = Move(
        old=state.value,
        new=answer,
        read_trades=TradeRange(state.read[0][0], state.read[-1][0], len(state.read)),
        watermark=Instant(state.watermark[0]),
        mean_r=sum((r for _, _, r in state.read), Decimal(0)) / len(state.read),
        mean_stamp=sum((stamp for _, stamp, _ in state.read), Decimal(0)) / len(state.read),
    )
    return replace(ran, value=answer), move
