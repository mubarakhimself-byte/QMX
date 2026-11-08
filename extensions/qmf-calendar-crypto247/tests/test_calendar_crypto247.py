"""The crypto calendar is always open, dated and versioned, and carries each venue's funding clock."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

CALENDAR = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "qmf"
    / "calendar_crypto247"
    / "calendars"
    / "crypto-24x7@1.json"
)


def test_crypto_trades_around_the_clock_with_no_closure_in_utc() -> None:
    doc = cast(dict[str, object], json.loads(CALENDAR.read_text("utf-8")))

    assert {key: doc[key] for key in ("schema", "calendar_ref", "zone", "sessions", "closures")} == {
        "schema": "qmx.calendar/1",
        "calendar_ref": "crypto-24x7@1",
        "zone": "UTC",
        "sessions": "always",
        "closures": [],
    }
    assert (doc["issued"], doc["max_age_days"]) == ("2026-11-03", 423)


def test_hyperliquid_funds_hourly_and_the_big_venues_every_eight_hours_from_midnight() -> None:
    doc = cast(dict[str, object], json.loads(CALENDAR.read_text("utf-8")))

    assert doc["funding"] == [
        {"venue": "hyperliquid", "every": "PT1H", "anchor": "00:00"},
        {"venue": "binance", "every": "PT8H", "anchor": "00:00"},
        {"venue": "bybit", "every": "PT8H", "anchor": "00:00"},
        {"venue": "okx", "every": "PT8H", "anchor": "00:00"},
    ]
