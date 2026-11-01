"""The `market_open:<market_id>` precheck reads each market's own calendar in its own zone: crypto
is open on Saturday, CME breaks every afternoon in Chicago time, holidays shut, and every session
lands at its local hour through the weeks when London, New York and Chicago change clocks apart."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import pytest
from scheduled import Clock, Flags, enabled, fires_of

from qmx_engine.service.context import OPERATOR
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Cron
from qmx_engine.triggers.preflight import (
    Blocked,
    Shut,
    market_shut,
    parse_calendar,
    shipped_calendars,
)
from qmx_engine.triggers.ticker import Scheduler

MARKETS = {
    "market.btc.calendar": "crypto-24x7@1",
    "market.sp500.calendar": "cme-equity@1",
    "market.eurusd.calendar": "fx-24x5@1",
    "market.uk100.calendar": "uk-index-cfd@1",
    "market.aapl.calendar": "nyse@1",
    "market.tsla.calendar": "nasdaq@9",
}
SUMMER = {
    "America/Chicago": (-6, date(2026, 3, 8), date(2026, 11, 1)),
    "America/New_York": (-5, date(2026, 3, 8), date(2026, 11, 1)),
    "Europe/London": (0, date(2026, 3, 29), date(2026, 10, 25)),
    "Europe/Berlin": (1, date(2026, 3, 29), date(2026, 10, 25)),
    "Asia/Tokyo": (9, date.max, date.max),
}
"""Each zone's standard UTC offset in hours and the local days its summer hour runs, written out
by hand so the sweep does not grade zoneinfo with zoneinfo."""
MISMATCH_DAYS = [date(2026, 3, 8) + timedelta(days=n) for n in range(22)] + [
    date(2026, 10, 25) + timedelta(days=n) for n in range(8)
]


def utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


def check(market: str, at: datetime) -> Shut | Blocked | None:
    return market_shut(at, f"market_open:{market}", "UTC", MARKETS)


def test_every_shipped_calendar_loads_beside_the_built_in_forex_week() -> None:
    assert sorted(shipped_calendars()) == [
        "cme-crypto@1",
        "cme-energy@1",
        "cme-equity@1",
        "cme-fx@1",
        "cme-grains@1",
        "cme-metals@1",
        "cme-rates@1",
        "crypto-24x7@1",
        "de-index-cfd@1",
        "fx-24x5@1",
        "jp-index-cfd@1",
        "metals-24x5@1",
        "nyse@1",
        "uk-index-cfd@1",
        "us-index-cfd@1",
    ]


def test_crypto_is_open_on_saturday_while_cme_waits_for_sunday_evening_in_chicago() -> None:
    saturday = utc(2026, 3, 14, 12)

    assert check("btc", saturday) is None
    assert check("btc", utc(2026, 3, 15, 3)) is None
    assert check("sp500", saturday) == Shut(
        utc(2026, 3, 15, 22), "sp500 is shut on its calendar cme-equity@1 in America/Chicago"
    )


def test_cmes_daily_break_is_16_to_17_chicago_whichever_utc_hour_that_is() -> None:
    winter, summer = date(2026, 3, 4), date(2026, 3, 11)

    def at(day: date, hours: int, minutes: int) -> datetime:
        return datetime.combine(day, time(hours, minutes), UTC)

    assert check("sp500", at(winter, 21, 30)) is None
    assert check("sp500", at(winter, 22, 30)) == Shut(
        at(winter, 23, 0), "sp500 is shut on its calendar cme-equity@1 in America/Chicago"
    )
    assert check("sp500", at(summer, 21, 30)) == Shut(
        at(summer, 22, 0), "sp500 is shut on its calendar cme-equity@1 in America/Chicago"
    )
    assert check("sp500", at(summer, 22, 30)) is None


def test_forex_closes_at_17_new_york_and_the_ftse_opens_at_01_london_across_both_changes() -> None:
    fx = "eurusd is shut on its calendar fx-24x5@1 in America/New_York"
    uk = "uk100 is shut on its calendar uk-index-cfd@1 in Europe/London"

    assert check("eurusd", utc(2026, 3, 6, 21, 30)) is None
    assert check("eurusd", utc(2026, 3, 13, 21)) == Shut(utc(2026, 3, 15, 21), fx)
    assert check("eurusd", utc(2026, 10, 30, 21)) == Shut(utc(2026, 11, 1, 22), fx)
    assert check("uk100", utc(2026, 3, 16, 0, 30)) == Shut(utc(2026, 3, 16, 1), uk)
    assert check("uk100", utc(2026, 3, 30, 0, 30)) is None
    assert check("uk100", utc(2026, 10, 26, 0, 30)) == Shut(utc(2026, 10, 26, 1), uk)


def test_every_session_opens_and_closes_at_its_local_hour_on_each_mismatch_day() -> None:
    misses: list[str] = []
    checked = 0
    for calendar in shipped_calendars().values():
        if calendar.sessions is None:
            continue
        standard, starts, ends = SUMMER[calendar.zone.key]
        for day in MISMATCH_DAYS:
            offset = timedelta(hours=standard + (1 if starts <= day < ends else 0))
            for opens, closes in calendar.sessions:
                for minute, is_open in ((opens, True), (closes, False)):
                    if minute // 1440 != day.weekday():
                        continue
                    local = datetime.combine(day, time(minute % 1440 // 60, minute % 60))
                    edge = (local - offset).replace(tzinfo=UTC)
                    before = calendar.open_at(edge - timedelta(minutes=1))
                    if (calendar.open_at(edge), before) != (is_open, not is_open):
                        misses.append(f"{calendar.ref} {local:%a %Y-%m-%d %H:%M} = {edge:%H:%M}Z")
                    checked += 1

    assert misses == []
    assert checked == 628
    crypto = shipped_calendars()["crypto-24x7@1"]
    hours = [datetime.combine(day, time(h), UTC) for day in MISMATCH_DAYS for h in range(24)]
    assert all(crypto.open_at(hour) for hour in hours)


def test_holidays_shut_until_the_next_session_and_a_stale_calendar_says_so() -> None:
    assert check("aapl", utc(2026, 11, 26, 15)) == Shut(
        utc(2026, 11, 27, 14, 30), "aapl is shut on its calendar nyse@1 in America/New_York"
    )
    assert check("sp500", utc(2026, 12, 24, 22, 30)) == Shut(
        utc(2026, 12, 27, 23),
        "sp500 is shut on its calendar cme-equity@1 in America/Chicago"
        " (the calendar is 21 days past its 31-day maximum age)",
    )


def test_a_market_with_no_calendar_row_or_an_unshipped_one_is_a_configuration_fault() -> None:
    assert check("gold", utc(2026, 3, 14, 12)) == Blocked(
        "config", "market_unknown", "gold: no market.gold.calendar row names its calendar"
    )
    assert check("tsla", utc(2026, 3, 14, 12)) == Blocked(
        "config", "calendar_unknown", "tsla: calendar nasdaq@9 is not shipped"
    )


def test_a_calendar_with_an_unknown_key_is_refused_and_one_shut_for_years_never_opens() -> None:
    shut = parse_calendar(
        {
            "schema": "qmx.calendar/1",
            "calendar_ref": "halted@1",
            "zone": "UTC",
            "issued": "2026-11-02",
            "max_age_days": 31,
            "sessions": "always",
            "closures": [{"from": "2026-01-01T00:00", "to": "2028-01-01T00:00"}],
        }
    )

    assert (shut.open_at(utc(2026, 11, 2)), shut.next_open(utc(2026, 11, 2))) == (False, None)
    assert shut.next_open(utc(2027, 12, 1)) == utc(2028, 1, 1)
    with pytest.raises(ValueError, match=r"^unknown calendar keys: \['holidays'\]$"):
        parse_calendar({"schema": "qmx.calendar/1", "holidays": []})


def test_a_saturday_crypto_fire_runs_and_a_cme_fire_is_held_until_sunday_evening(
    tmp_path: Path,
) -> None:
    saturday = Clock(datetime(2026, 10, 17, 9, 0, tzinfo=UTC))
    flags = Flags(**MARKETS)
    with enabled(tmp_path, saturday, settings=flags) as (svc, version):
        made = {
            market: rows.create(
                svc.ctx.engine.ledger,
                workflow_item=svc.versions.get(version).item,
                pinned_object=version,
                spec=Cron("0 * * * *", "UTC"),
                caller=OPERATOR,
                now=saturday.now(),
                precheck_ref=f"market_open:{market}",
            )
            for market in ("btc", "sp500")
        }
        saturday.move(hours=1)
        ticker = Scheduler(svc.ctx)

        async def go() -> None:
            await ticker.tick()
            await ticker.settle()

        asyncio.run(go())
        verdict = ticker.explain(made["sp500"].id)["verdict"]
        found = {market: fires_of(tmp_path, made[market].id) for market in made}

    held = (
        "sp500 is shut on its calendar cme-equity@1 in America/Chicago"
        " until 2026-10-18T22:00:00.000000+00:00"
    )
    assert [(f.status, f.run_id is not None) for f in found["btc"]] == [("ok", True)]
    assert [(f.status, f.detail, f.run_id) for f in found["sp500"]] == [("held", held, None)]
    assert verdict == f"held: {held}"
