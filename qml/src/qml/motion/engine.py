"""Calibrated motion as a pure function of the unit's own closed trades (AD-103, L0 AD-22).

A calibrated number moves only at its cadence: after every ``every`` closed trades it has read
(the dummy's 20). Each run hands the trades read so far to the number's rule block, which
answers nothing below the number's ``min_count`` and otherwise a value at most ``step_limit``
steps away, shrunk toward the default by n/(n+k) and inside the range. A run that is due while
the unit holds a position waits for the first flat instant, so a number never moves
mid-position.

The state carries everything the rule needs (the trades read, as their stamp and R) and a
watermark, so a host feeds ``own_journal`` only the trades this run or deployment closed and a
restored unit reads each trade once.
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
    "SlowNumber",
    "SlowState",
    "TradeRange",
    "calibrate",
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
    """A calibrated number as compiled: its rule, the entry stamp the rule reads, its cadence."""

    name: str
    rule_pin: str
    stamp: str
    every: int


@dataclass(frozen=True, slots=True)
class SlowState:
    value: Decimal
    read: tuple[tuple[str, Decimal, Decimal], ...] = ()
    """``(trade_id, stamp, r_after_costs)`` of every trade read, in watermark order."""
    watermark: tuple[int, str] | None = None
    """``(closed_at ns, trade_id)`` of the last trade read."""
    read_at_last_run: int = 0


@dataclass(frozen=True, slots=True)
class TradeRange:
    from_trade_id: str
    to_trade_id: str
    count: int


@dataclass(frozen=True, slots=True)
class Move:
    """What one cadence run answered: the old and new value and the trades it read."""

    old: Decimal
    new: Decimal
    read_trades: TradeRange
    watermark: Instant


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
    return replace(state, read=state.read + rows, watermark=_key(fresh[-1]))


def calibrate(
    number: SlowNumber,
    rule: Instance,
    state: SlowState,
    trades: Sequence[ClosedTrade],
    *,
    instant: Instant,
    flat: bool,
) -> tuple[SlowState, Move | None]:
    """Read the trades knowable at ``instant`` and, when the cadence is due and the unit is
    flat, run the rule once. A trade without the stamp the rule reads is passed over."""
    state = _read(number, state, trades, instant)
    due = len(state.read) - state.read_at_last_run >= number.every
    if not due or not flat:
        return state, None
    answer = rule.update(
        {
            "trades": [{"strength": stamp, "r": r} for _, stamp, r in state.read],
            "current": state.value,
        }
    )
    ran = replace(state, read_at_last_run=len(state.read))
    if not isinstance(answer, Decimal) or state.watermark is None:
        return ran, None
    move = Move(
        old=state.value,
        new=answer,
        read_trades=TradeRange(state.read[0][0], state.read[-1][0], len(state.read)),
        watermark=Instant(state.watermark[0]),
    )
    return replace(ran, value=answer), move
