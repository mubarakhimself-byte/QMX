"""The CME calendars are dated, versioned files in their market's zone, with Globex's daily break
and its two full closures written as data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from zoneinfo import ZoneInfo

CALENDARS = Path(__file__).resolve().parents[1] / "src" / "qmf" / "calendar_cme" / "calendars"


def load(ref: str) -> dict[str, object]:
    return cast(dict[str, object], json.loads((CALENDARS / f"{ref}.json").read_text("utf-8")))


def test_every_file_is_a_dated_calendar_named_by_its_ref_in_a_real_zone() -> None:
    found = {path.stem: load(path.stem) for path in CALENDARS.glob("*.json")}

    assert sorted(found) == [
        "cme-crypto@1",
        "cme-energy@1",
        "cme-equity@1",
        "cme-fx@1",
        "cme-grains@1",
        "cme-metals@1",
        "cme-rates@1",
        "metals-24x5@1",
    ]
    assert {ref: ZoneInfo(str(doc["zone"])).key for ref, doc in found.items()} == {
        **{ref: "America/Chicago" for ref in found},
        "metals-24x5@1": "America/New_York",
    }
    assert {(doc["schema"], doc["issued"], doc["max_age_days"]) for doc in found.values()} == {
        ("qmx.calendar/1", "2026-11-03", 423)
    }
    assert all(doc["calendar_ref"] == ref for ref, doc in found.items())


def test_globex_opens_sunday_evening_and_breaks_each_day_from_16_to_17_chicago() -> None:
    assert load("cme-equity@1")["sessions"] == [
        {"open": "sun 17:00", "close": "mon 16:00"},
        {"open": "mon 17:00", "close": "tue 16:00"},
        {"open": "tue 17:00", "close": "wed 16:00"},
        {"open": "wed 17:00", "close": "thu 16:00"},
        {"open": "thu 17:00", "close": "fri 16:00"},
    ]


def test_grains_keep_their_morning_pause_and_gold_cfds_keep_comex_hours_in_new_york() -> None:
    grains = cast(list[dict[str, str]], load("cme-grains@1")["sessions"])
    gold = cast(list[dict[str, str]], load("metals-24x5@1")["sessions"])

    assert (grains[0], grains[5], len(grains)) == (
        {"open": "sun 19:00", "close": "mon 07:45"},
        {"open": "mon 08:30", "close": "mon 13:20"},
        10,
    )
    assert (gold[0], gold[4]) == (
        {"open": "sun 18:00", "close": "mon 17:00"},
        {"open": "thu 18:00", "close": "fri 17:00"},
    )


def test_gold_cfds_halt_at_14_30_new_york_on_the_us_monday_holidays() -> None:
    def early(day: str, why: str) -> dict[str, str]:
        return {"from": f"{day}T14:30", "to": f"{day}T18:00", "why": f"{why} early close"}

    assert load("metals-24x5@1")["closures"] == [
        early("2025-01-20", "Martin Luther King Jr. Day"),
        early("2025-02-17", "Presidents' Day"),
        early("2026-01-19", "Martin Luther King Jr. Day"),
        early("2026-02-16", "Presidents' Day"),
        {"from": "2026-12-24T17:00", "to": "2026-12-27T18:00", "why": "Christmas Day"},
        {"from": "2026-12-31T17:00", "to": "2027-01-03T18:00", "why": "New Year's Day"},
        early("2027-01-18", "Martin Luther King Jr. Day"),
        early("2027-02-15", "Presidents' Day"),
    ]


def test_globex_is_shut_from_the_break_before_christmas_and_new_year_to_the_sunday_open() -> None:
    assert load("cme-metals@1")["closures"] == [
        {"from": "2026-12-24T16:00", "to": "2026-12-27T17:00", "why": "Christmas Day"},
        {"from": "2026-12-31T16:00", "to": "2027-01-03T17:00", "why": "New Year's Day"},
    ]
