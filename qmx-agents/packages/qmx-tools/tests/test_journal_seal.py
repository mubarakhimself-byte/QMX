"""`journal_query` keeps to the door's Settings default holdout (triage-6, LD-08).

An agent's read names no study, so the default is the only seal that can apply. The rows sit in the
store as the records job files them: a closed December 2024 and an open January 2025.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qmf.core import is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_writer import JournalWriter, WriterScope
from qmf.data.series import SeriesKey, SeriesStore
from qmn.app.feed_keeper import FeedKeeper, Quote, RecordedSource, Recording

from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext, MarketPort, unwrap

DECEMBER = datetime(2024, 12, 30, 8, tzinfo=UTC)
JANUARY = datetime(2025, 1, 2, 8, tzinfo=UTC)


def filed(root: Path, year: int, month: int, at: datetime, reason: str) -> None:
    key = SeriesKey.try_create("journal-unit", "dummy", "signal", year, month, "paper.this-pc")
    assert not is_refusal(key)
    record = {
        "kind": "signal",
        "record_id": f"node@this-pc/signal-{year}-{month}",
        "world": "paper",
        "machine": "this-pc",
        "unit_id": "dummy",
        "market_id": "fx.eurusd",
        "backfilled": False,
        "body": {"outcome": "skipped", "reason": reason},
    }
    row = (int(at.timestamp()) * 1_000, 0, json.dumps(record))
    assert not is_refusal(SeriesStore(root / "market" / "series").commit(key.value, [row]))


@pytest.fixture
def context(tmp_path: Path) -> Iterator[DomainContext]:
    from qmx_host.market_data import MarketDoor  # pyright: ignore[reportMissingTypeStubs]

    data = {"holdout": True, "holdout_boundary": "2025-01"}
    door = cast("MarketPort", unwrap(MarketDoor.open(tmp_path / "market", data)))
    filed(tmp_path, 2024, 12, DECEMBER, "in_the_open_month")
    filed(tmp_path, 2025, 1, JANUARY, "in_the_sealed_month")
    made = DomainContext(root=tmp_path, market=door)
    yield made
    made.control.close()


def test_journal_query_keeps_to_the_default_holdout(context: DomainContext) -> None:
    query = domain_functions(context)["research"]["journal_query"]

    opened = query(stream="unit", window={"start": "2024-12-30T00:00:00Z", "end": "2025-01-01"})
    with pytest.raises(ValueError) as refused:
        query(stream="unit", window={"start": "2024-12-30T00:00:00Z", "end": "2025-01-03"})

    assert [row["body"]["reason"] for row in opened["result"]] == ["in_the_open_month"]
    assert opened["data_stops_at"] == "2024-12-30T08:00:00.000Z"
    assert str(refused.value) == (
        "the door's holdout seals journal history; this window reaches "
        "journal-unit/dummy/signal/paper.this-pc/2025-01, so it is refused, never answered "
        "empty; ask for a window that ends before the holdout"
    )


def test_the_0800_question_reads_the_0800_minute(context: DomainContext) -> None:
    from qmx_host.market_data import MarketDoor  # pyright: ignore[reportMissingTypeStubs]
    from qmx_host.records import (  # pyright: ignore[reportMissingTypeStubs]
        Cadence,
        Harvester,
        append_roots,
    )

    home = context.root
    journal = home / "apps" / "trading-node" / "data" / "journal"
    eight = int(datetime(2024, 12, 18, 8, tzinfo=UTC).timestamp()) * 1_000_000_000
    now = [eight]

    def opened(stream: JournalStream, subject: str) -> JournalWriter:
        scope = WriterScope(stream, subject, JournalWorld.DEMO, "pc", "node", "0.1.0")
        made = JournalWriter.open(journal, scope, clock=lambda: now[0], boot_epoch_id="b1")
        assert not is_refusal(made)
        return made.value

    market, unit = opened(JournalStream.MARKET, "demo-tag"), opened(JournalStream.UNIT, "dummy")
    source = RecordedSource([])
    feed = FeedKeeper("ctrader", "demo", source, ("fx.eurusd",), lambda: now[0], Recording(market))

    def quote(second: int, ask: str) -> None:
        now[0] = eight + second * 1_000_000_000
        source.play([Quote("fx.eurusd", now[0], Decimal("1.08000"), Decimal(ask), "both")])
        feed.pump()

    quote(10, "1.08020")
    now[0] = eight + 30 * 1_000_000_000
    body = {
        "row_id": "decision-0800",
        "instant": now[0],
        "market_id": "fx.eurusd",
        "outcome": "skipped",
        "reason": "spread_wide",
    }
    facts = RowFacts(ts_recv=now[0], clock_ok=True, unit_id="dummy", market_id="fx.eurusd")
    assert not is_refusal(unit.append("signal", body, facts))
    quote(59, "1.08012")
    quote(61, "1.08090")
    quote(121, "1.08090")
    market.close()
    unit.close()
    door = cast("MarketDoor", context.market)
    Harvester(lambda: append_roots(home), door, home / "records", journals_open=True).round(
        datetime(2024, 12, 18, 9, tzinfo=UTC), Cadence()
    )
    query = domain_functions(context)["research"]["journal_query"]

    answer = query(
        stream="unit",
        window={"start": "2024-12-18T08:00:00Z", "end": "2024-12-18T08:01:00Z"},
        filters={"unit_id": "dummy"},
        view="trades_with_context",
    )

    [row] = answer["result"]
    assert row["body"]["reason"] == "spread_wide"
    assert row["market_minute"]["body"] == {
        "market_id": "fx.eurusd",
        "minute": "2024-12-18T08:00:00Z",
        "spread": "0.00012",
    }
