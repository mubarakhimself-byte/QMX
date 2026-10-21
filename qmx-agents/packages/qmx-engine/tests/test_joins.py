"""Joins: `quorum(n)` and `any` fire on the first arrivals and record the rest late, never merged;
a watermark ends a join that can no longer fire."""

from __future__ import annotations

import asyncio
from pathlib import Path

from flows import LATER, Flow, Planted, Script, edge, node, of, workflow
from pydantic import JsonValue

from qmx_engine.definition.model import Workflow
from qmx_engine.runner import Engine, Outcome

FIVE: JsonValue = ["a", "b", "c", "d", "e"]


def fan_in(**join: JsonValue) -> Workflow:
    return workflow(
        [
            node("start", "trigger"),
            node("work", "script"),
            node("gather", "join", **join),
            node("after", "script"),
        ],
        {
            "start": {"main": [edge("work", "broadcast")]},
            "work": {"main": [edge("gather")]},
            "gather": {"main": [edge("after")]},
        },
    )


def test_quorum_3_of_5_fires_on_the_first_three_arrivals_and_records_the_slow_two_late(
    tmp_path: Path,
) -> None:
    script = Script(slow={("work", 0), ("work", 1)})
    flow = Flow(tmp_path, fan_in(mode="quorum", n=3), {"script": script})

    async def scenario(engine: Engine) -> Outcome:
        run = asyncio.create_task(flow.started(engine, FIVE))
        await flow.seen("node_finished", "after")
        script.release("work", 1, "B")
        await flow.seen("node_finished", "work", 1)
        script.release("work", 0, "A")
        return await run

    ended = flow.drive(scenario)

    assert [e["plan"] for e in of(flow.events, "node_scheduled", "gather")] == [
        {"join": {"mode": "quorum", "expected": 5, "merged": [2, 3, 4], "late": [0, 1]}}
    ]
    assert (ended.status, ended.outputs) == ("passed", {"after": {"main": ["c", "d", "e"]}})
    assert len(of(flow.events, "node_started", "gather")) == 1


def test_any_fires_on_the_first_and_later_arrivals_change_nothing(tmp_path: Path) -> None:
    script = Script(slow={("work", p) for p in (1, 2, 3, 4)})
    flow = Flow(tmp_path, fan_in(mode="any"), {"script": script})

    async def scenario(engine: Engine) -> Outcome:
        run = asyncio.create_task(flow.started(engine, FIVE))
        await flow.seen("node_finished", "after")
        for partition in (4, 1, 3, 2):
            script.release("work", partition, partition)
            await flow.seen("node_finished", "work", partition)
        return await run

    ended = flow.drive(scenario)

    assert of(flow.events, "node_scheduled", "gather")[0]["plan"] == {
        "join": {"mode": "any", "expected": 5, "merged": [0], "late": [1, 2, 3, 4]}
    }
    assert (ended.status, ended.outputs) == ("passed", {"after": {"main": ["a"]}})


def test_failed_aggregation_ends_a_join_at_once_and_all_expected_waits_for_every_partition(
    tmp_path: Path,
) -> None:
    failing: set[Planted] = {("work", 0, 0), ("work", 0, 1)}
    early = Flow(
        tmp_path,
        fan_in(mode="quorum", n=4, watermark="failed-aggregation"),
        {"script": Script(failing=failing, waiting={("work", 4)})},
        run_id="run-early",
    ).start(FIVE)
    script = Script(failing=failing, slow={("work", 4)})
    flow = Flow(tmp_path, fan_in(mode="quorum", n=4), {"script": script})

    async def scenario(engine: Engine) -> tuple[bool, Outcome]:
        run = asyncio.create_task(flow.started(engine, FIVE))
        await flow.seen("node_finished", "work", 3)
        parks = [e for e in of(flow.events, "ladder_step", "work") if e["step"] == "park"]
        while len(parks) < 2:
            await asyncio.sleep(0.01)
            parks = [e for e in of(flow.events, "ladder_step", "work") if e["step"] == "park"]
        held = not run.done()
        script.release("work", 4, "E")
        return held, await run

    held, waited = flow.drive(scenario)

    reason = "join gather join_failed: quorum join has 2 of 4 needed partitions; 2 of 5 failed"
    assert (early.status, early.reason) == ("failed", reason)
    assert held
    assert (waited.status, waited.reason) == (
        "failed",
        reason.replace("2 of 4 needed", "3 of 4 needed"),
    )


def test_a_timeout_watermark_ends_an_unmet_join_once_its_hold_comes_due(tmp_path: Path) -> None:
    flow = Flow(
        tmp_path,
        fan_in(mode="quorum", n=3, watermark="timeout", timeout_seconds=60),
        {"script": Script(waiting={("work", p) for p in (2, 3, 4)})},
    )

    first = flow.start(FIVE)
    early = flow.tick("2026-10-17T09:00:59+00:00")
    due = flow.tick("2026-10-17T09:01:00+00:00")

    assert first.status == "waiting"
    assert of(flow.events, "node_waiting", "gather")[0]["resume_at"] == "2026-10-17T09:01:00+00:00"
    assert early.status == "waiting"
    assert (due.status, due.reason) == (
        "failed",
        "join gather join_timeout: quorum join has 2 of 3 needed partitions at its timeout",
    )


def test_a_resume_keeps_the_partitions_a_fired_join_merged(tmp_path: Path) -> None:
    script = Script(failing={("after", 0, None)}, slow={("work", 0), ("work", 3)})
    flow = Flow(tmp_path, fan_in(mode="quorum", n=3), {"script": script})

    async def scenario(engine: Engine) -> Outcome:
        run = asyncio.create_task(flow.started(engine, FIVE))
        await flow.seen("node_failed", "after")
        script.release("work", 3, "d")  # the late two report in after the failure
        await flow.seen("node_finished", "work", 3)
        script.release("work", 0, "a")
        return await run

    first = flow.drive(scenario)
    mark = len(flow.events)
    ended = flow.resume(LATER)

    assert (first.status, first.reason) == ("failed", "node after failed: boom: planted failure")
    assert of(flow.events[mark:], "node_started", "gather") == []
    assert (ended.status, ended.outputs) == ("passed", {"after": {"main": ["b", "c", "e"]}})
