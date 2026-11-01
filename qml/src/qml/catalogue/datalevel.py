"""The data-level vocabulary ``qmx.data-level/1`` (Part A AD-113, CONTRACTS.md section 5.2).

A block's entry declares the level each input needs, an instrument record declares what a market
offers, and layer D compares the two in this one vocabulary. Inputs the host supplies itself (a
position, the account, the instrument record, the unit's own trades, a number's current value)
come from no market feed, so they carry no data level.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import IntEnum, StrEnum
from typing import Final, cast

__all__ = [
    "HOST_FACTS",
    "SPLITS",
    "DataLevel",
    "Depth",
    "DerivativesClock",
    "History",
    "Volume",
    "level_of",
    "split_problems",
]


class DataLevel(IntEnum):
    CALENDAR = 0
    BARS = 1
    QUOTE_TICKS = 2
    DEPTH = 3
    TRADE_TAPE = 4
    DERIVATIVES = 5
    OUTSIDE = 6


class Volume(StrEnum):
    EXCHANGE = "exchange"
    TAKER_SPLIT = "taker_split"
    TICK_COUNT = "tick_count"
    VENUE = "venue"


class Depth(StrEnum):
    TOP = "top"
    BY_PRICE = "by_price"
    BY_ORDER = "by_order"


class DerivativesClock(StrEnum):
    END_OF_DAY = "end_of_day"
    FIVE_MINUTES = "five_minutes"
    LIVE = "live"


class History(StrEnum):
    COMPLETE = "complete"
    SAMPLED = "sampled"
    PROVIDER_LIMITED = "provider_limited"


SPLITS: Final[Mapping[str, tuple[DataLevel, type[StrEnum]]]] = {
    "volume": (DataLevel.BARS, Volume),
    "depth": (DataLevel.DEPTH, Depth),
    "derivatives_clock": (DataLevel.DERIVATIVES, DerivativesClock),
    "history": (DataLevel.DERIVATIVES, History),
}
"""Each split, the level it refines and its words. ``licence`` is free text on any level."""

HOST_FACTS: Final[frozenset[str]] = frozenset({"position", "account", "record", "trades", "number"})


def level_of(value: object) -> DataLevel | None:
    """``value`` as a data level, or None when it is not a whole number from 0 to 6."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    try:
        return DataLevel(value)
    except ValueError:
        return None


def split_problems(level: DataLevel, splits: object) -> list[tuple[str, str]]:
    """Each wrong split as ``(key, message)``: a split must refine the declared level and use
    its own words."""
    if not isinstance(splits, Mapping):
        return [("", "splits is an object of split names")]
    found: list[tuple[str, str]] = []
    for key, value in cast("Mapping[str, object]", splits).items():
        if key == "licence":
            if not isinstance(value, str) or not value:
                found.append((key, "licence names the data's licence as text"))
            continue
        split = SPLITS.get(key)
        if split is None:
            found.append((key, f"{key} is no split; the splits are {', '.join(SPLITS)}, licence"))
            continue
        refines, words = split
        if refines is not level:
            found.append(
                (key, f"{key} refines level {int(refines)}, and this input is {int(level)}")
            )
        elif value not in {w.value for w in words}:
            found.append((key, f"{key} is one of {', '.join(w.value for w in words)}"))
    return found
