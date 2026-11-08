"""Two fixture markets in a market store, the host facts, and the MIS's journal read back.

EURUSD is an fx market that offers bars only (levels 0 and 1). XAUUSD is a metal market that
also offers quote ticks (level 2). Both hold three synthetic months of M1 bid bars, January to
March 2025, a seeded random walk every minute of every day, so every value below is the same on
every machine. They are fixtures, not evidence about any market.
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from qmf.core import is_refusal
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qmf.data.series import BAR_KIND, TICKS_KIND, SeriesKey, SeriesStore

type Json = dict[str, object]

MONTHS = ((2025, 1), (2025, 2), (2025, 3))
SOURCE = "fixture"
EURUSD: Json = {
    "venue": "fixture",
    "symbol": "EURUSD",
    "market_id": "eurusd",
    "class": "fx",
    "currency": "USD",
    "digits": 5,
    "pip": {"size": "0.0001", "source": "fixture"},
    "data_levels": {"levels": [0, 1]},
    "status": "specified",
}
XAUUSD: Json = {
    "venue": "fixture",
    "symbol": "XAUUSD",
    "market_id": "gold",
    "class": "metal",
    "currency": "USD",
    "digits": 2,
    "pip": {"size": "0.1", "source": "fixture"},
    "data_levels": {"levels": [0, 1, 2]},
    "status": "specified",
}
BLOCKS = (
    "cusum-change-point@1",
    "efficiency-ratio@1",
    "variance-ratio@1",
    "hurst-exponent@1",
)


def _ms(year: int, month: int) -> int:
    return int(datetime(year, month, 1, tzinfo=UTC).timestamp()) * 1_000


def _next(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def _key(symbol: str, kind: str, year: int, month: int, variant: str = "") -> SeriesKey:
    made = SeriesKey.try_create(SOURCE, symbol, kind, year, month, variant)
    assert not is_refusal(made), made
    return made.value


def write_markets(market_root: Path) -> None:
    """Both markets' bars, and gold's ticks for March, under `<market root>/series`."""
    store = SeriesStore(market_root / "series")
    for symbol, start, seed in (("EURUSD", 108_000, 7), ("XAUUSD", 290_000, 11)):
        walk = random.Random(seed)  # noqa: S311 - a seeded walk, so every machine reads the same
        price = start
        for year, month in MONTHS:
            rows: list[tuple[object, ...]] = []
            for t in range(_ms(year, month), _ms(*_next(year, month)), 60_000):
                opened = price
                price += walk.randint(-12, 12)
                high, low = max(opened, price) + 3, min(opened, price) - 3
                rows.append((t, opened, high, low, price, 1.0))
            committed = store.commit(_key(symbol, BAR_KIND, year, month, "bid"), rows)
            assert not is_refusal(committed), committed
    march = _ms(2025, 3)
    quotes = [
        (march + index * 1_000, 290_000 + index, 290_000 + index + 20, 1.0, 1.0)
        for index in range(5)
    ]
    committed = store.commit(_key("XAUUSD", TICKS_KIND, 2025, 3), quotes)
    assert not is_refusal(committed), committed


def write_facts(volume: Path, holdout: Json | None) -> None:
    """The host facts as the host writes them in an app volume; None leaves none there."""
    path = volume / "road" / "host" / "facts.json"
    if holdout is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    facts: Json = {
        "schema_version": "qmx.host.facts/1",
        "placement": "this-pc",
        "role": "pc",
        "trading_profile": False,
        "chats": True,
        "agent_steps": True,
        "holdout": holdout,
    }
    path.write_text(json.dumps(facts), "utf-8")


def configure_both(**extra: object) -> Json:
    return {
        "op_id": "c09-fixture",
        "markets": [
            {"market_id": "eurusd", "instrument": EURUSD, "source": SOURCE},
            {"market_id": "gold", "instrument": XAUUSD, "source": SOURCE},
        ],
        **extra,
    }


def records(volume: Path) -> list[Json]:
    """Every reading record the MIS's journal holds, in each stream's append order."""
    found: list[Json] = []
    for folder in stream_folders(volume / "data" / "journal"):
        lines = read_committed(folder)
        assert not is_refusal(lines), lines
        for line in lines.value:
            if isinstance(line, JournalLine) and line.record.get("kind") == "reading":
                found.append(cast(Json, line.record["body"]))
    return found


def pin(body: Json) -> str:
    reading = cast(Json, body["reading"])
    return f"{reading['id']}@{reading['version']}"
