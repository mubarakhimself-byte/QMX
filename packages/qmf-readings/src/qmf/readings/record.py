"""The stamped reading record (Part C ``CONTRACTS.md`` section 7; spine AD-314).

One published reading is one record of kind ``reading`` in the ``journal-readings`` stream,
under Part B's envelope. ``source`` and ``machine`` sit in the body, because the envelope has
no source field. Exact numbers travel as ``{"num", "den", "unit_kind"}``, since canonical
JSON refuses binary floats. A field that is absent is an omitted key: canonical JSON has no
null.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from qmf.core import ExactRational, Fingerprint

__all__ = [
    "READING_KIND",
    "Health",
    "ReadingRecord",
    "ReadingRef",
    "ReadingSource",
    "Tier",
    "TimeBase",
    "exact_json",
]

READING_KIND: Final[str] = "reading"


class ReadingSource(StrEnum):
    """Who computed the reading: the node (tick tier on a trading machine) or the MIS app."""

    NODE = "node"
    MIS = "mis"


class Tier(StrEnum):
    """The clock a reading runs on, which decides where it runs (AD-40)."""

    TICK = "tick"
    BAR = "bar"
    SESSION = "session"
    DAY = "day"
    CALENDAR = "calendar"


class TimeBase(StrEnum):
    CLOCK = "clock"
    TICKS = "ticks"
    VOLUME = "volume"


class Health(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    DEGRADED = "degraded"
    """A fallback step was taken, or an input was unavailable."""
    THIN = "thin"
    """Too little to compute from yet."""
    SHADOW = "shadow"
    RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class ReadingRef:
    """Which reading: its id, its version and the fingerprint of the block that computed it."""

    id: str
    version: str
    fingerprint: Fingerprint


@dataclass(frozen=True, slots=True)
class ReadingRecord:
    """Every field of section 7. Times are epoch nanoseconds."""

    reading: ReadingRef
    source: ReadingSource
    machine: str
    market_id: str
    instrument: str
    tier: Tier
    time_base: TimeBase
    health: Health
    data_level: int
    fallback_step: int
    inputs_received_at: int
    computed_at: int
    stale_after_s: int
    value: ExactRational | None = None
    percentile: ExactRational | None = None
    word: str | None = None
    estimate: str | None = None
    corrects: str | None = None

    def body(self) -> dict[str, object]:
        """The record as the journal body: JSON-native values, absent fields left out."""
        body: dict[str, object] = {
            "reading": {
                "id": self.reading.id,
                "version": self.reading.version,
                "fingerprint": self.reading.fingerprint.value,
            },
            "source": self.source.value,
            "machine": self.machine,
            "market_id": self.market_id,
            "instrument": self.instrument,
            "tier": self.tier.value,
            "time_base": self.time_base.value,
            "health": self.health.value,
            "data_level": self.data_level,
            "fallback_step": self.fallback_step,
            "inputs_received_at": self.inputs_received_at,
            "computed_at": self.computed_at,
            "stale_after_s": self.stale_after_s,
        }
        optional: dict[str, object | None] = {
            "value": None if self.value is None else exact_json(self.value),
            "percentile": None if self.percentile is None else exact_json(self.percentile),
            "word": self.word,
            "estimate": self.estimate,
            "corrects": self.corrects,
        }
        body.update({name: item for name, item in optional.items() if item is not None})
        return body


def exact_json(value: ExactRational) -> dict[str, object]:
    """An exact number as canonical JSON: its reduced numerator, denominator and unit kind."""
    reduced = value.as_fraction()
    return {
        "num": reduced.numerator,
        "den": reduced.denominator,
        "unit_kind": value.unit_kind.value,
    }
