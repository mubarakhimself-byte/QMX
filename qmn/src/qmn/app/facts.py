"""The node's rate facts, from the feed's own record of each conversion market (AD-10, AD-15).

Same formula, same ``provided`` list and same conversion lookup as QMB: all three are imported
from ``qmb.host.facts`` rather than spelled again, so one fact is never computed two ways. The
node reads the newest bar its recording kept for the conversion market, and never a bar knowable
after the instant being priced.

A ``ConversionRef`` names the market by its record's id; this node keys its feed and its
recording by the deployment's market id, so ``refs`` maps one to the other once, when the port is
built.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from qmf.core.chrono import Instant
from qmf.risk.facts import Fact
from qml.numbers import ConversionRef, InstrumentRecord
from qml.protocol.unit import ACCOUNT_CURRENCY, QuoteBar

from qmb.host.facts import RATE_ABSENT, conversions, provided, rate_fact

__all__ = [
    "RATE_ABSENT",
    "FeedRates",
    "RecordedBars",
    "conversions",
    "provided",
    "rate_fact",
    "refs",
]


class RecordedBars(Protocol):
    """The bars this node's feed kept, newest last, as ``Recording`` answers them."""

    def recent(
        self, market: str, count: int, before_ns: int | None = None
    ) -> tuple[QuoteBar, ...]: ...


def refs(
    records: Mapping[str, InstrumentRecord], currency: str = ACCOUNT_CURRENCY
) -> dict[str, ConversionRef]:
    """Each quote's conversion market by the market id this node keys its feed with."""
    by_record = {record.market_id: market for market, record in records.items()}
    return {
        quote: ConversionRef(by_record.get(ref.market_id, ref.market_id), ref.invert)
        for quote, ref in conversions(records.values(), currency).items()
    }


@dataclass(frozen=True, slots=True)
class FeedRates:
    """The rate each quote currency converts at, from the feed's last closed bar.

    ``refs`` is keyed by quote currency, with each market named as this node keys it. A market
    the feed has not closed a bar on yet answers nothing, which the converter names
    ``rate_absent``; a bar older than the converter's ``rate_stale_s`` is ``rate_stale``.
    """

    recording: RecordedBars
    refs: Mapping[str, ConversionRef]
    currency: str = ACCOUNT_CURRENCY

    def rate(self, record: InstrumentRecord, instant: Instant) -> Fact | None:
        ref = self.refs.get(record.currency)
        if ref is None:
            return None
        bars = self.recording.recent(ref.market_id, 1, instant.value_ns + 1)
        if not bars:
            return None
        return rate_fact(bars[-1], ref.invert, "node:feed")
