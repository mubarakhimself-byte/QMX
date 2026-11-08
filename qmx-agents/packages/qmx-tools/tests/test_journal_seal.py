"""`journal_query` keeps to the door's Settings default holdout (triage-6, LD-08).

An agent's read names no study, so the default is the only seal that can apply. The rows sit in the
store as the records job files them: a closed December 2024 and an open January 2025.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest
from qmf.core import is_refusal
from qmf.data.series import SeriesKey, SeriesStore

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
