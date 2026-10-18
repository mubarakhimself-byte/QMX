"""Cron occurrences in an IANA zone across both DST changes of `Europe/London`, in UTC."""

from __future__ import annotations

from datetime import UTC, datetime
from itertools import islice

from qmx_engine.triggers.cron import Cron, after, stamp


def test_a_daily_cron_runs_once_on_each_dst_change_in_london() -> None:
    daily = Cron("30 1 * * *", "Europe/London")

    spring = [stamp(o) for o in islice(after(daily, datetime(2026, 3, 28, 12, tzinfo=UTC)), 2)]
    autumn = [stamp(o) for o in islice(after(daily, datetime(2026, 10, 24, 12, tzinfo=UTC)), 2)]

    assert spring == ["2026-03-29T01:00:00.000000+00:00", "2026-03-30T00:30:00.000000+00:00"]
    assert autumn == ["2026-10-25T00:30:00.000000+00:00", "2026-10-26T01:30:00.000000+00:00"]


def test_an_hourly_cron_keeps_both_one_oclocks_of_the_autumn_change() -> None:
    hourly = Cron("0 * * * *", "Europe/London")

    found = [stamp(o) for o in islice(after(hourly, datetime(2026, 10, 24, 23, tzinfo=UTC)), 3)]

    assert found == [
        "2026-10-25T00:00:00.000000+00:00",
        "2026-10-25T01:00:00.000000+00:00",
        "2026-10-25T02:00:00.000000+00:00",
    ]
