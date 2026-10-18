"""Joins: `quorum(n)` and `any` fire on the first arrivals and record the rest late, never merged;
a watermark ends a join that can no longer fire."""

from __future__ import annotations

from flows import LATER, NOW, Planted, Script, edge, finish, node, of, simulation, workflow
from pydantic import JsonValue

from qmx_engine.core.commands import Finish, Park
from qmx_engine.core.simulate import Simulation, Terminal
from qmx_engine.definition.model import Workflow


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


def run(script: Script, **join: JsonValue) -> tuple[Simulation, Terminal | None]:
    sim = simulation(fan_in(**join), script)
    return sim, sim.start(["a", "b", "c", "d", "e"], NOW)


def test_quorum_3_of_5_fires_on_the_first_three_arrivals_and_records_the_slow_two_late() -> None:
    sim, first = run(Script(slow={("work", 0), ("work", 1)}), mode="quorum", n=3)

    assert first is None  # the slow attempts are still in flight
    assert [e["plan"] for e in of(sim.events, "node_scheduled", "gather")] == [
        {"join": {"mode": "quorum", "expected": 5, "merged": [2, 3, 4], "late": [0, 1]}}
    ]
    assert finish(sim, "work", 1, {"main": "B"}) is None
    ended = finish(sim, "work", 0, {"main": "A"})
    assert ended == Finish({"after": {"main": ["c", "d", "e"]}})
    assert len(of(sim.events, "node_started", "gather")) == 1


def test_any_fires_on_the_first_and_later_arrivals_change_nothing() -> None:
    sim, _ = run(Script(slow={("work", p) for p in (1, 2, 3, 4)}), mode="any")

    for partition in (4, 1, 3):
        finish(sim, "work", partition, {"main": partition})
    ended = finish(sim, "work", 2, {"main": 2})

    assert of(sim.events, "node_scheduled", "gather")[0]["plan"] == {
        "join": {"mode": "any", "expected": 5, "merged": [0], "late": [1, 2, 3, 4]}
    }
    assert ended == Finish({"after": {"main": ["a"]}})


def test_failed_aggregation_ends_a_join_at_once_and_all_expected_waits_for_every_partition() -> (
    None
):
    reason = "join gather join_failed: quorum join has 2 of 4 needed partitions; 2 of 5 failed"
    failing: set[Planted] = {("work", 0, 0), ("work", 0, 1)}

    _, early = run(
        Script(failing=failing, slow={("work", 4)}),
        mode="quorum",
        n=4,
        watermark="failed-aggregation",
    )
    sim, waiting = run(Script(failing=failing, slow={("work", 4)}), mode="quorum", n=4)

    assert early == Park(reason)
    assert waiting is None
    assert finish(sim, "work", 4, {"main": "E"}) == Park(
        reason.replace("2 of 4 needed", "3 of 4 needed")
    )


def test_a_timeout_watermark_ends_an_unmet_join_once_its_hold_comes_due() -> None:
    sim, first = run(
        Script(slow={("work", p) for p in (2, 3, 4)}),
        mode="quorum",
        n=3,
        watermark="timeout",
        timeout_seconds=60,
    )

    assert first is None
    assert of(sim.events, "node_waiting", "gather")[0]["resume_at"] == "2026-10-17T09:01:00+00:00"
    assert sim.tick("2026-10-17T09:00:59+00:00") is None
    assert sim.tick("2026-10-17T09:01:00+00:00") == Park(
        "join gather join_timeout: quorum join has 2 of 3 needed partitions at its timeout"
    )


def test_a_resume_keeps_the_partitions_a_fired_join_merged() -> None:
    script = Script(failing={("after", 0, None)}, slow={("work", 0), ("work", 3)})
    sim, first = run(script, mode="quorum", n=3)
    assert first == Park("node after failed: boom: planted failure")
    finish(sim, "work", 3, {"main": "d"})  # the late two report in after the park
    finish(sim, "work", 0, {"main": "a"})
    script.slow.clear()
    mark = len(sim.events)

    ended = sim.resume(LATER)

    assert of(sim.events[mark:], "node_started", "gather") == []
    assert ended == Finish({"after": {"main": ["b", "c", "e"]}})
