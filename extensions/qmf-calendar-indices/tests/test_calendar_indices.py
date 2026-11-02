"""The index calendars are dated, versioned files in each exchange's zone, with the NYSE holidays
and each index's own break written as data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from zoneinfo import ZoneInfo

CALENDARS = Path(__file__).resolve().parents[1] / "src" / "qmf" / "calendar_indices" / "calendars"


def load(ref: str) -> dict[str, object]:
    return cast(dict[str, object], json.loads((CALENDARS / f"{ref}.json").read_text("utf-8")))


def test_every_file_is_a_dated_calendar_named_by_its_ref_in_its_exchange_zone() -> None:
    found = {path.stem: load(path.stem) for path in CALENDARS.glob("*.json")}

    assert {ref: ZoneInfo(str(doc["zone"])).key for ref, doc in found.items()} == {
        "de-index-cfd@1": "Europe/Berlin",
        "jp-index-cfd@1": "Asia/Tokyo",
        "nyse@1": "America/New_York",
        "uk-index-cfd@1": "Europe/London",
        "us-index-cfd@1": "America/Chicago",
    }
    assert {(doc["schema"], doc["issued"], doc["max_age_days"]) for doc in found.values()} == {
        ("qmx.calendar/1", "2026-11-02", 31)
    }
    assert all(doc["calendar_ref"] == ref for ref, doc in found.items())


def test_the_nyse_day_runs_0930_to_1600_and_shuts_on_each_listed_holiday() -> None:
    nyse = load("nyse@1")
    closures = cast(list[dict[str, str]], nyse["closures"])

    assert cast(list[object], nyse["sessions"])[0] == {"open": "mon 09:30", "close": "mon 16:00"}
    assert [c["from"][:10] for c in closures] == [
        "2026-01-01",
        "2026-01-19",
        "2026-02-16",
        "2026-04-03",
        "2026-05-25",
        "2026-06-19",
        "2026-07-03",
        "2026-09-07",
        "2026-11-26",
        "2026-12-25",
        "2027-01-01",
        "2027-01-18",
        "2027-02-15",
        "2027-03-26",
    ]
    assert closures[8] == {
        "from": "2026-11-26T00:00",
        "to": "2026-11-27T00:00",
        "why": "Thanksgiving Day",
    }


def test_each_index_keeps_its_own_hours_and_osaka_keeps_its_night_session() -> None:
    def first(ref: str) -> object:
        return cast(list[object], load(ref)["sessions"])[0]

    assert [first(ref) for ref in ("uk-index-cfd@1", "de-index-cfd@1")] == [
        {"open": "mon 01:00", "close": "mon 21:00"},
        {"open": "mon 01:10", "close": "mon 22:00"},
    ]
    assert cast(list[object], load("jp-index-cfd@1")["sessions"])[8:] == [
        {"open": "fri 08:45", "close": "fri 15:45"},
        {"open": "fri 17:00", "close": "sat 06:00"},
    ]


def test_us_index_cfds_halt_at_noon_chicago_on_the_us_monday_holidays() -> None:
    def early(day: str, why: str) -> dict[str, str]:
        return {"from": f"{day}T12:00", "to": f"{day}T17:00", "why": f"{why} early close"}

    assert cast(list[object], load("us-index-cfd@1")["closures"]) == [
        early("2025-01-20", "Martin Luther King Jr. Day"),
        early("2025-02-17", "Presidents' Day"),
        early("2026-01-19", "Martin Luther King Jr. Day"),
        early("2026-02-16", "Presidents' Day"),
        {"from": "2026-12-24T16:00", "to": "2026-12-27T17:00", "why": "Christmas Day"},
        {"from": "2026-12-31T16:00", "to": "2027-01-03T17:00", "why": "New Year's Day"},
    ]
