"""The one fact surface's type (AD-15): a value, its age, its source, its supply, its fail mode.

Every fact reads the same way in both hosts: ``value`` in the unit its reader expects, ``ts``
the instant it was read, ``source`` who supplied it, ``fail_mode`` what a missing value means
for the market, and ``state`` how good the supply is. One naming function keeps the two host
adapters on one key (``market.rate:<quote>``), so one fact is never computed under two names.

This module imports ``qmf-core`` only. Nothing here runs a block (AD-21).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Final, Literal

from qmf.core import Instant, is_refusal

__all__ = ["RATE_PREFIX", "Fact", "rate_name"]

RATE_PREFIX: Final[str] = "market.rate:"
"""The fact-name prefix of a market's rate into the account's currency (AD-10, AD-15)."""

_NANOS_PER_SECOND: Final[int] = 1_000_000_000


def rate_name(quote: str) -> str:
    """The fact name for one unit of ``quote`` in the account's currency."""
    return f"{RATE_PREFIX}{quote}"


@dataclass(frozen=True, slots=True)
class Fact:
    """One value from one source, with its age and the supply it has right now.

    ``state`` says how good the supply is: ``ok`` read as written, ``stale`` past its reader's
    limit, ``absent`` never supplied, ``uncalibrated`` measured but not yet trusted. ``fail_mode``
    says what a missing value means for the market: ``open`` keeps trading, ``closed`` stops
    entries, ``neutral`` treats it as absent without a fault.
    """

    value: Decimal | Fraction | None
    ts: Instant | None
    fail_mode: Literal["open", "closed", "neutral"]
    source: str
    state: Literal["ok", "stale", "absent", "uncalibrated"] = "ok"

    def is_stale(self, now: Instant, stale_s: Decimal) -> bool:
        """True when this fact was read more than ``stale_s`` seconds before ``now``.

        A fact with no read time cannot be shown fresh, so it reads stale.
        """
        if self.ts is None:
            return True
        span = now.difference(self.ts)
        if is_refusal(span):
            return True
        age = Fraction(span.value.value_ns)
        return age > Fraction(*stale_s.as_integer_ratio()) * _NANOS_PER_SECOND
