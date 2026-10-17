"""One catch-up run per trigger after downtime: four missed hourly occurrences become one fire
for the latest and three `skipped: downtime` rows (ruling 54)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scheduled import Clock, enabled, fires_of

from qmx_engine.ledger.store import Reader
from qmx_engine.service.context import OPERATOR
from qmx_engine.triggers import rows
from qmx_engine.triggers.catchup import collapse
from qmx_engine.triggers.cron import Cron
from qmx_engine.triggers.ticker import Scheduler

T0 = datetime(2026, 10, 17, 9, 30, tzinfo=UTC)


def test_four_missed_occurrences_collapse_into_one_fire_for_the_latest() -> None:
    missed = [datetime(2026, 10, 17, hour, tzinfo=UTC) for hour in (10, 11, 12, 13)]

    found = collapse(missed, datetime(2026, 10, 17, 13, 30, tzinfo=UTC), timedelta(minutes=15))

    assert found.fire == datetime(2026, 10, 17, 13, tzinfo=UTC)
    assert [(o.hour, why) for o, why in found.skipped] == [
        (10, "downtime"),
        (11, "downtime"),
        (12, "downtime"),
    ]


def test_the_ticker_after_downtime_runs_one_catch_up_and_records_three_skips(
    tmp_path: Path,
) -> None:
    clock = Clock(T0)
    with enabled(tmp_path, clock) as (svc, version):
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=Cron("0 * * * *", "UTC"),
            caller=OPERATOR,
            now=clock.now(),
        )
        clock.move(hours=4)
        ticker = Scheduler(svc.ctx)

        async def go() -> int:
            tick = await ticker.tick()
            await ticker.settle()
            return len(tick.claimed)

        claimed = asyncio.run(go())
        with Reader.open(tmp_path) as reader:
            (after,) = rows.triggers(reader.connection)
        found = fires_of(tmp_path, trigger.id)
        ran = svc.runs.get(str(found[-1].run_id))

    assert claimed == 1
    assert [(f.occurrence_at[11:16], f.status, f.detail) for f in found] == [
        ("10:00", "skipped", "downtime"),
        ("11:00", "skipped", "downtime"),
        ("12:00", "skipped", "downtime"),
        ("13:00", "ok", None),
    ]
    assert (ran.mode, ran.status) == ("live", "passed")
    assert (after.next_fire_at, after.last_status) == ("2026-10-17T14:00:00.000000+00:00", "ok")
