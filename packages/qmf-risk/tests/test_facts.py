"""One fact surface: a value, its age, its source, its supply and its fail mode (AD-15)."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

from qmf.core.chrono import Instant
from qmf.risk.facts import Fact, rate_name


def test_a_rate_past_rate_stale_s_is_stale_and_one_inside_it_is_not() -> None:
    read_at = Instant(1_000_000_000_000)
    rate = Fact(value=Fraction(1, 150), ts=read_at, fail_mode="open", source="node", state="ok")

    assert rate.is_stale(Instant(read_at.value_ns + 30_000_000_000), Decimal("30")) is False
    assert rate.is_stale(Instant(read_at.value_ns + 30_000_000_001), Decimal("30")) is True


def test_the_rate_fact_is_named_after_the_quote_currency() -> None:
    assert rate_name("JPY") == "market.rate:JPY"
