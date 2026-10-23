"""Broker fills land as partitions and round trips as `trade` items, exactly and once (W20, AD-31).

The three providers are read from literal rows of the shape they give, so the test proves the
adapter and the round trip together: no network, no broker.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from qmf.core import is_ok
from qmf.data.importers.journal import (
    Fill,
    JournalStatement,
    from_ccxt,
    from_ctrader,
    from_mt5,
    import_journal,
    round_trips,
)
from qmf.data.series import SeriesStore

JANUARY = datetime(2026, 2, 10, tzinfo=UTC)
"""After 2026-01-31 plus the fill kind's two-day settlement, so a fill month freezes at once."""


class Clock:
    def __init__(self, at: datetime) -> None:
        self.now = at

    def __call__(self) -> datetime:
        self.now += timedelta(minutes=1)
        return self.now


@pytest.fixture
def store(tmp_path: Path) -> SeriesStore:
    return SeriesStore(tmp_path / "series", wall=Clock(JANUARY))


def dealt(position: str, price: str, at: str, *, deal: str, profit: str = "0") -> dict[str, object]:
    return {
        "dealId": deal,
        "positionId": position,
        "accountId": "A-1042",
        "symbolName": "EURUSD",
        "tradeSide": "BUY",
        "volume": "0.5",
        "executionPrice": price,
        "executionTime": at,
        "commission": "-1.25",
        "swap": "0.10",
        "netProfit": profit,
    }


def statement(
    *rows: dict[str, object], money_digits: int = 2, price_digits: int = 5
) -> JournalStatement:
    """One cTrader statement of account A-1042 from the rows given."""
    return JournalStatement(
        "ctrader",
        "A-1042",
        from_ctrader(rows, account="A-1042", money_digits=money_digits, price_digits=price_digits),
        broker="IC Markets via cTrader",
        world="demo",
        money_digits=money_digits,
        price_digits=price_digits,
    )


def test_an_import_twice_adds_nothing_the_second_time(store: SeriesStore) -> None:
    written = statement(
        dealt("P-1", "1.10000", "2026-01-05T09:30:00Z", deal="D-1", profit="25.50"),
        dealt("P-1", "1.10300", "2026-01-05T11:00:00Z", deal="D-2", profit="25.50"),
    )
    first = import_journal(store, written)
    assert is_ok(first)
    again = import_journal(store, written, held={draft.item for draft in first.value.added})

    assert is_ok(again)
    assert [draft.item for draft in first.value.added] == ["trade/A-1042/P-1"]
    assert [receipt.key.text for receipt in first.value.partitions] == [
        "ctrader/A-1042/fill/-/2026-01"
    ]
    assert first.value.fills_written == 2
    assert again.value.added == ()
    assert again.value.held == ("trade/A-1042/P-1",)
    assert again.value.fills_written == 2
    assert again.value.idempotent is True


def test_money_keeps_its_exact_integers(store: SeriesStore) -> None:
    written = JournalStatement(
        "ctrader",
        "A-1042",
        from_ctrader(
            (
                dealt("P-9", "1.10000", "2026-01-05T09:30:00Z", deal="D-9", profit="0.1"),
                dealt("P-9", "1.10001", "2026-01-05T09:31:00Z", deal="D-10", profit="0.2"),
            ),
            account="A-1042",
            money_digits=4,
        ),
        money_digits=4,
    )
    imported = import_journal(store, written)

    assert is_ok(imported)
    fields = imported.value.added[0].fields

    assert fields["net_result"] == 3000
    assert fields["money_digits"] == 4
    assert fields["fees"] == -25000
    assert fields["swap"] == 2000
    assert isinstance(fields["net_result"], int)


def test_a_round_trip_is_one_trade_with_its_fills_in_observation_order(
    store: SeriesStore,
) -> None:
    written = statement(
        dealt("P-2", "1.10300", "2026-01-06T16:00:00Z", deal="D-4"),
        dealt("P-2", "1.10000", "2026-01-06T08:00:00Z", deal="D-3"),
    )
    imported = import_journal(store, written)

    assert is_ok(imported)
    fields = imported.value.added[0].fields

    assert fields["entry_price"] == 110000
    assert fields["exit_price"] == 110300
    assert fields["holding_ns"] == 8 * 3_600 * 1_000_000_000
    assert fields["volume"] == "1"
    assert list(fields["broker_ids"]) == ["D-3", "D-4"]  # type: ignore[arg-type]
    assert fields["world"] == "demo"
    assert "initial_risk" not in fields and "r" not in fields


def test_each_provider_reads_its_own_row_shape() -> None:
    ct = from_ctrader([dealt("P-1", "1.10000", "2026-01-05T09:30:00Z", deal="D-1")], account="A")
    mt = from_mt5(
        [{"Deal": 7, "Position": 3, "Symbol": "EURUSD", "Type": 1, "Volume": "0.25",
          "Price": "1.10000", "Time": "2026-01-05T09:30:00Z", "Commission": "-0.5",
          "Swap": "0", "Profit": "0"}],
        account="A",
    )  # fmt: skip
    cc = from_ccxt(
        [{"id": "t-1", "order": "o-1", "symbol": "BTC/USDT", "side": "sell", "amount": "0.5",
          "price": "60000.5", "timestamp": 1767605400000, "fee": {"cost": "1.5"},
          "info": {"positionId": "pos-42"}}],
        account="A",
    )  # fmt: skip

    assert (ct[0].provider, ct[0].broker_id, ct[0].position_id) == ("ctrader", "D-1", "P-1")
    assert (mt[0].side, mt[0].position_id, mt[0].fee) == ("sell", "3", -50)
    assert (cc[0].position_id, cc[0].broker_id, cc[0].side) == ("pos-42", "t-1", "sell")
    assert (cc[0].price_minor, cc[0].money_digits) == (6_000_050_000_000, 8)
    assert all(isinstance(fill.at_ns, int) for fill in (*ct, *mt, *cc))


def test_a_position_with_one_fill_is_not_yet_a_round_trip() -> None:
    trip, opened = round_trips(
        [
            Fill("ctrader", "A", "D-1", "P-1", "EURUSD", "buy", "1", 110000, 5, 2, 1),
            Fill("ctrader", "A", "D-2", "P-2", "EURUSD", "buy", "1", 110000, 5, 2, 2),
            Fill("ctrader", "A", "D-3", "P-2", "EURUSD", "sell", "1", 110100, 5, 2, 3),
        ]
    )

    assert [one.position_id for one in trip] == ["P-2"]
    assert opened == ("P-1",)
