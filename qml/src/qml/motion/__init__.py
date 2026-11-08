"""The motion engine: how a unit's calibrated numbers move from its own closed trades (AD-103).

Derived numbers move every bar inside the compiled closure; this package owns the slow speed.
"""

from __future__ import annotations

from qml.motion.engine import (
    MIN_TRADES,
    SHRINK_K,
    SLOW_CADENCE_TRADES,
    ClosedTrade,
    Move,
    SlowNumber,
    SlowState,
    TradeRange,
    calibrate,
)

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
