"""Waits: a `wait` node is held until the recorded clock reaches its `resume_at`, or until its
named event arrives, and never starts before."""

from __future__ import annotations

from flows import NOW, Script, edge, node, of, simulation, workflow
from pydantic import JsonValue

from qmx_engine.core.commands import Finish, Wait
from qmx_engine.definition.model import Workflow


def waiting(**spec: JsonValue) -> Workflow:
    return workflow(
        [node("start", "trigger"), node("pause", "wait", **spec), node("after", "script")],
        {"start": {"main": [edge("pause")]}, "pause": {"main": [edge("after")]}},
    )


def test_a_30_second_wait_resumes_on_the_first_tick_past_resume_at_and_not_before() -> None:
    sim = simulation(waiting(seconds=30), Script())

    first = sim.start({"topic": "q-fin"}, NOW)
    early = sim.tick("2026-10-17T09:00:29+00:00")
    started_early = of(sim.events, "node_started", "pause")
    late = sim.tick("2026-10-17T09:00:31+00:00")

    assert first == Wait(("pause",), "2026-10-17T09:00:30+00:00")
    assert early == Wait(("pause",), "2026-10-17T09:00:30+00:00")
    assert started_early == []
    assert late == Finish({"after": {"main": {"topic": "q-fin"}}})


def test_an_event_wait_resumes_only_on_its_named_event() -> None:
    sim = simulation(waiting(event="paper.published"), Script())
    sim.start({"topic": "q-fin"}, NOW)

    other = sim.receive("paper.withdrawn")
    named = sim.receive("paper.published")

    assert other == Wait(("pause",), None)
    assert named == Finish({"after": {"main": {"topic": "q-fin"}}})
