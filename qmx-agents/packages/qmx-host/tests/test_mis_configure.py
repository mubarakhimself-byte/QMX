"""The MIS is told the source that holds each market's bars, not the venue its record lists (p34-2).

A real Library on a throwaway folder holds the instrument records the node's C-34 answer lands,
through the same `land` the host runs. A real market store holds three months of `dukascopy`
`bar-m1/bid` bars for EURUSD and none for gold, and the market door reads it. The MIS is the app's
own core over its own volume, so both sides of the crossing are the shipped code: the job builds
the document, and the MIS parses it, reads the store and publishes.
"""

from __future__ import annotations

import importlib
import json
import random
import sys
import time
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from qmf.core import is_refusal
from qmf.data.series import BAR_KIND, SeriesKey, SeriesStore
from qmx_library.store import Store
from test_venue_records import ANSWER

from qmx_host.host import open_store, register_checkers
from qmx_host.market_data import MarketDoor
from qmx_host.mis_configure import MisConfigure, arguments, markets
from qmx_host.venue_records import land, records_of

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps" / "mis"))

mis_core: Any = importlib.import_module("mis_core")
"""The app's own core, loaded from its folder as the supervisor's bootstrap loads it."""

MONTHS = ((2025, 1), (2025, 2), (2025, 3))
"""Three whole months of one-minute bars, enough for the day-tier reading's 1,000 H1 bars."""
SOURCE = "dukascopy"
"""The source the downloader writes bars under, which is never the venue the record names."""
FACTS: dict[str, object] = {"placement": "this-pc", "holdout": {"on": False}}


def _ms(year: int, month: int) -> int:
    return int(datetime(year, month, 1, tzinfo=UTC).timestamp()) * 1_000


def _next(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def write_bars(market: Path) -> None:
    """EURUSD's three months under the source that downloaded them, as the store's writer lands
    them. A seeded walk, so the same bars reach every machine."""
    store = SeriesStore(market / "series")
    walk = random.Random(7)  # noqa: S311 - a seeded walk, so every machine reads the same
    price = 108_000
    for year, month in MONTHS:
        rows: list[tuple[object, ...]] = []
        for t in range(_ms(year, month), _ms(*_next(year, month)), 60_000):
            opened = price
            price += walk.randint(-12, 12)
            high, low = max(opened, price) + 3, min(opened, price) - 3
            rows.append((t, opened, high, low, price, 1.0))
        key = SeriesKey.try_create(SOURCE, "EURUSD", BAR_KIND, year, month, "bid")
        assert not is_refusal(key), key
        committed = store.commit(key.value, rows)
        assert not is_refusal(committed), committed


def write_facts(volume: Path) -> None:
    """The host facts as the host writes them in an app volume, with the holdout off."""
    path = volume / "road" / "host" / "facts.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(FACTS), "utf-8")


@dataclass(frozen=True)
class Rig:
    store: Store
    door: MarketDoor
    mis: Any
    job: MisConfigure


@pytest.fixture
def rig(tmp_path: Path) -> Iterator[Rig]:
    home = tmp_path / "QMX"
    with open_store(home, home / "library", serving=False, floor=0) as store:
        register_checkers(store)
        land(store, records_of(ANSWER))
        market = home / "market"
        write_bars(market)
        door = MarketDoor.open(market, {})
        assert not is_refusal(door), door
        volume = home / "apps" / "mis"
        write_facts(volume)
        mis: Any = mis_core.Mis(volume, market, clock=time.time_ns, boot="r18")

        def call(operation: str, given: Mapping[str, object]) -> Mapping[str, object]:
            return cast("Mapping[str, object]", mis.call(operation, given))

        job = MisConfigure(call, store, door.value, every_s=86_400)
        try:
            yield Rig(store, door.value, mis, job)
        finally:
            mis.close()


def test_a_market_with_bars_under_a_source_is_configured_and_publishes(rig: Rig) -> None:
    attempt = rig.job.round()
    published = rig.mis.call("round", {})["value"]["published"]

    assert attempt.answer == {"ok": True, "value": {"configured": 2, "refused": []}}
    assert {market.market_id: market.source for market in attempt.named} == {
        "eurusd": "dukascopy",
        "gold": None,
    }
    assert [(row["market_id"], row["reading"]) for row in published] == [
        ("eurusd", "cusum-change-point@1"),
        ("eurusd", "efficiency-ratio@1"),
        ("eurusd", "variance-ratio@1"),
        ("eurusd", "hurst-exponent@1"),
    ]


def test_running_twice_does_nothing_and_a_market_with_no_bars_is_named(rig: Rig) -> None:
    first = rig.job.round()
    before = rig.mis.plan
    again = rig.job.round()
    status = rig.mis.call("status", {})["value"]

    assert again.answer == first.answer
    assert rig.mis.plan is before, "a second pass over the same universe configured again"
    assert rig.mis.plan.op_id == arguments(markets(rig.store, rig.door))["op_id"]
    assert status["state"] == "configured"
    assert {market["market_id"]: market["source"] for market in status["markets"]} == {
        "eurusd": "dukascopy",
        "gold": None,
    }
