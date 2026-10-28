"""Which copies a place keeps (design 62 C2, E-M5): counts of the newest buckets that hold a
copy, never windows back from the clock."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from qmx_home.backup.keep import kept, released
from qmx_home.backup.plan import PC_KEEP, STORAGE_KEEP, Keep

START = datetime(2026, 1, 1, 3, 0, tzinfo=UTC)


def stamps(moments: list[datetime]) -> list[str]:
    return [moment.strftime("%Y%m%dT%H%M%S%fZ") for moment in moments]


def test_sixty_daily_copies_keep_fourteen_days_eight_weeks_and_each_month() -> None:
    daily = stamps([START + timedelta(days=n) for n in range(60)])

    found = sorted(kept(daily, STORAGE_KEEP))

    assert len(found) == 21
    assert found[-14:] == daily[-14:]
    assert found[:7] == [
        "20260111T030000000000Z",
        "20260118T030000000000Z",
        "20260125T030000000000Z",
        "20260131T030000000000Z",
        "20260201T030000000000Z",
        "20260208T030000000000Z",
        "20260215T030000000000Z",
    ]


def test_a_two_year_gap_or_a_clock_jump_keeps_the_newest_buckets_that_hold_copies() -> None:
    old = stamps([START + timedelta(days=n) for n in range(30)])
    after_gap = stamps([START + timedelta(days=760)])

    found = kept([*old, *after_gap], STORAGE_KEEP)

    assert after_gap[0] in found
    assert set(old[-13:]) <= found
    assert len(found) == 16
    assert {old[3], old[10]} <= found


def test_the_newest_and_the_newest_drilled_copy_are_always_kept() -> None:
    hourly = stamps([START + timedelta(hours=n) for n in range(24 * 10)])

    nothing = kept(hourly, Keep(), drilled=hourly[3], held=[hourly[5]])
    quick = kept(hourly, PC_KEEP)

    assert nothing == {hourly[-1], hourly[3], hourly[5]}
    assert len(quick) == 52
    assert hourly[-48] in quick and hourly[-49] not in quick


def test_a_held_copy_goes_once_a_whole_copy_made_after_it_reached_another_disk() -> None:
    made = START

    assert not released(made, [START - timedelta(days=1)])
    assert released(made, [START - timedelta(days=1), START + timedelta(minutes=5)])
