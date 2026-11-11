"""The roll-up from an account feed's base bars to one unit's stream (AD-25).

RC-30's first two seams. ``roll_up`` takes the base bars of one bucket and answers the closed
stream bar, both quote sides, or nothing when the bucket is not whole. The seam is the function
itself, which is what both hosts call.
"""

from __future__ import annotations

from decimal import Decimal

from qmf.core.chrono import Instant
from qml.feed import roll_up
from qml.protocol.unit import OHLC, QuoteBar

START = 1_742_500_800_000_000_000
"""2025-03-20 19:46:40 UTC, a whole 15-minute bucket's start."""
MINUTE_NS = 60_000_000_000
M15_NS = 900_000_000_000


def _bar(at: int, open_: str, high: str, low: str, close: str) -> QuoteBar:
    side = OHLC(Decimal(open_), Decimal(high), Decimal(low), Decimal(close))
    return QuoteBar(Instant(at), side, side)


def _minute(index: int, *, high: str = "1.1005", low: str = "1.0995") -> QuoteBar:
    """One bar of the bucket the test rolls: 1.1000 open, 1.1010 close, both sides."""
    close = "1.1010" if index == 14 else "1.1000"
    return _bar(START + (index + 1) * MINUTE_NS, "1.1000", high, low, close)


def test_rolled_bars_equal_direct_bars() -> None:
    base_bars = [
        _minute(
            index,
            high="1.1020" if index == 7 else "1.1005",
            low="1.0990" if index == 3 else "1.0995",
        )
        for index in range(15)
    ]

    rolled = roll_up(base_bars, 900)

    assert rolled is not None, "fifteen one-minute bars make one fifteen-minute bar"
    assert rolled.knowable_at == Instant(START + M15_NS), "the bucket closes at its own end"
    expected = OHLC(Decimal("1.1000"), Decimal("1.1020"), Decimal("1.0990"), Decimal("1.1010"))
    assert rolled.bid == expected, "the bid side rolls open, high, low, close"
    assert rolled.ask == expected, "the ask side rolls the same way"


def test_a_partial_bucket_is_never_emitted() -> None:
    """A feed joining at minute 3 has no bar for the bucket it joined, and the next one whole."""
    joined = [_minute(index) for index in range(3, 15)]

    assert roll_up(joined, 900) is None, "the bucket was not seen from its start"

    whole = [
        _bar(
            START + M15_NS + (index + 1) * MINUTE_NS,
            "1.1000",
            "1.1010",
            "1.0995",
            "1.1005" if index == 14 else "1.1000",
        )
        for index in range(15)
    ]
    rolled = roll_up(whole, 900)
    assert rolled is not None, "the next bucket is whole and closes"
    assert rolled.knowable_at == Instant(START + 2 * M15_NS)
    assert (rolled.bid.open, rolled.bid.close) == (Decimal("1.1000"), Decimal("1.1005"))
