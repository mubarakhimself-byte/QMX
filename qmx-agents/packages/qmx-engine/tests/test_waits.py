"""Waits: a `wait` node is held until the recorded clock reaches its `resume_at`, or until its
named event arrives, and never starts before."""

from __future__ import annotations

from pathlib import Path

from flows import Flow, Script, edge, node, of, workflow
from pydantic import JsonValue

from qmx_engine.definition.model import Workflow


def waiting(**spec: JsonValue) -> Workflow:
    return workflow(
        [node("start", "trigger"), node("pause", "wait", **spec), node("after", "script")],
        {"start": {"main": [edge("pause")]}, "pause": {"main": [edge("after")]}},
    )


def test_a_30_second_wait_resumes_on_the_first_tick_past_resume_at_and_not_before(
    tmp_path: Path,
) -> None:
    flow = Flow(tmp_path, waiting(seconds=30), {"script": Script()})

    first = flow.start({"topic": "q-fin"})
    early = flow.tick("2026-10-17T09:00:29+00:00")
    started_early = of(flow.events, "node_started", "pause")
    late = flow.tick("2026-10-17T09:00:31+00:00")

    assert (first.status, first.reason) == ("waiting", "waiting on pause")
    assert [e["resume_at"] for e in of(flow.events, "node_waiting", "pause")] == [
        "2026-10-17T09:00:30+00:00"
    ]
    assert (early.status, early.reason) == ("waiting", "waiting on pause")
    assert started_early == []
    assert (late.status, late.outputs) == ("passed", {"after": {"main": {"topic": "q-fin"}}})


def test_an_event_wait_resumes_only_on_its_named_event(tmp_path: Path) -> None:
    flow = Flow(tmp_path, waiting(event="paper.published"), {"script": Script()})
    flow.start({"topic": "q-fin"})

    other = flow.receive("paper.withdrawn")
    named = flow.receive("paper.published")

    assert (other.status, other.reason) == ("waiting", "waiting on pause")
    assert (named.status, named.outputs) == ("passed", {"after": {"main": {"topic": "q-fin"}}})
