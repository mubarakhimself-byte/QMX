"""The motion engine: how a unit's numbers follow a fact, and move from its own closed trades
(AD-103, AD-14).

Derived numbers move every bar inside the compiled closure; a ``scaled`` number is the track job
(fact times multiple), and this package owns the slow speed.
"""

from __future__ import annotations

from qml.motion.engine import (
    MIN_TRADES,
    SHRINK_K,
    SLOW_CADENCE_TRADES,
    ClosedTrade,
    Move,
    ScaledNumber,
    SlowNumber,
    SlowState,
    TradeRange,
    calibrate,
    scale,
)

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
