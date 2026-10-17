"""At most one fire per occurrence: two claimants on one occurrence get one fire between them,
a fire whose claimant stopped renewing its lease is taken over only once the lease ran out, and a
run that paused before its engine died is resumed once, by its wake."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fake_port import CARD, OPEN, FakePort, agent, agent_files, events_of
from flows import edge, folder, node
from scheduled import Clock, enabled, fires_of

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.store import Transaction
from qmx_engine.ports.harness_adapter import PlanUse
from qmx_engine.ports.settings import StaticSettings
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.settings import DEFAULTS
from qmx_engine.triggers import rows
from qmx_engine.triggers.claims import Lease, claim_due
from qmx_engine.triggers.cron import Interval, stamp
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


def test_a_run_paused_before_its_engine_died_is_resumed_once_by_its_wake(tmp_path: Path) -> None:
    root = agent_files(
        folder(
            tmp_path / "wf",
            [node("start", "trigger"), agent("first"), agent("after")],
            {"start": {"main": [edge("first")]}, "first": {"main": [edge("after")]}},
            {},
        )
    )
    reset = (datetime.now(UTC) + timedelta(seconds=0.5)).isoformat()
    port = FakePort(CARD, CARD, CARD, CARD, uses=[PlanUse(1.0, reset, reset, None), OPEN])
    found = checked(root)
    assert not isinstance(found, list), found
    home = tmp_path / "home"
    settings = StaticSettings({**DEFAULTS, "limits.slack": 0})

    async def go() -> tuple[str, int, int]:
        with EngineService.open(home, settings=settings, harness=port) as svc:
            paused = await svc.ctx.engine.start(root, found[1], mode="live", inputs=None)
            ledger = svc.ctx.engine.ledger
            ledger.write(
                rows.insert(
                    rows.Trigger(
                        id="trigger-x",
                        workflow_item="wf",
                        pinned_object="obj",
                        spec=rows.Manual(),
                        created_by="operator",
                        created_at=stamp(T0),
                    )
                )
            )
            past = stamp(datetime.now(UTC) - timedelta(seconds=10))

            def died_mid_fire(txn: Transaction) -> None:
                txn.connection.execute(
                    "INSERT INTO fires (id, trigger_id, occurrence_at, status, claimed_by,"
                    " claimed_at, lease_until, run_id, merged)"
                    " VALUES ('fire-x', 'trigger-x', ?, 'running', 'dead', ?, ?, ?, 0)",
                    (past, past, past, paused.run_id),
                )

            ledger.write(died_mid_fire)
            await asyncio.sleep(1.0)
            ticker = Scheduler(svc.ctx, claimant="b")
            tick = await ticker.tick()
            await ticker.settle()
            return paused.run_id, len(tick.claimed), len(tick.woken)

    run_id, claimed, woken = asyncio.run(go())
    events = events_of(home, run_id)
    (fire,) = fires_of(home, "trigger-x")

    assert (claimed, woken) == (0, 1)
    assert [e.data["reason"] for e in events if e.kind == "run_resumed"] == ["limit"]
    assert [e.kind for e in events].count("run_finished") == 1
    assert [chat for chat, _ in port.sent] == ["chat-1", "chat-2"]
    assert fire.status == "ok"
