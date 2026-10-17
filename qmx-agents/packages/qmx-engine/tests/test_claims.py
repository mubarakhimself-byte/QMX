"""At most one fire per occurrence: two claimants on one occurrence get one fire between them,
and a fire whose claimant stopped renewing its lease is taken over only once the lease ran out."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scheduled import Clock, enabled, fires_of

from qmx_engine.service.context import OPERATOR
from qmx_engine.triggers import rows
from qmx_engine.triggers.claims import Lease, claim_due
from qmx_engine.triggers.cron import Interval
from qmx_engine.triggers.ticker import Scheduler

T0 = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)
GRACE = timedelta(minutes=15)


def test_two_claimants_on_one_occurrence_make_one_fire(tmp_path: Path) -> None:
    clock = Clock(T0)
    with enabled(tmp_path, clock) as (svc, version):
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=Interval(60, T0),
            caller=OPERATOR,
            now=clock.now(),
        )
        clock.move(seconds=60)
        first, second = Scheduler(svc.ctx, claimant="a"), Scheduler(svc.ctx, claimant="b")

        async def go() -> list[int]:
            ticks = await asyncio.gather(first.tick(), second.tick())
            await asyncio.gather(first.settle(), second.settle())
            return [len(t.claimed) for t in ticks]

        claimed = asyncio.run(go())
        found = fires_of(tmp_path, trigger.id)

    assert sorted(claimed) == [0, 1]
    assert [(f.status, f.claimed_by in ("a", "b")) for f in found] == [("ok", True)]


def test_a_stale_lease_is_taken_over_only_after_it_runs_out(tmp_path: Path) -> None:
    clock = Clock(T0)
    with enabled(tmp_path, clock) as (svc, version):
        ledger = svc.ctx.engine.ledger
        trigger = rows.create(
            ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=rows.Manual(),
            caller=OPERATOR,
            now=T0,
        )
        rows.fire_now(ledger, trigger.id, T0, {})

        def claim(claimant: str, seconds: float) -> list[tuple[str, str | None]]:
            lease = Lease(claimant, T0 + timedelta(seconds=seconds), 300)
            found = ledger.write(claim_due(lease, grace=GRACE, home="pc"))
            return [(c.fire.status, c.fire.claimed_by) for c in found]

        taken = claim("a", 0)
        early = claim("b", 60)
        late = claim("b", 301)

    assert (taken, early, late) == ([("claimed", "a")], [], [("claimed", "b")])
