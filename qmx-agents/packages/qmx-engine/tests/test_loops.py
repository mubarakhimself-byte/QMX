"""Loops: the body runs once per iteration until a typed stop fires, and the stop is decided from
the ledger, so a resumed loop picks up at the iteration that failed."""

from __future__ import annotations

from flows import LATER, NOW, Script, edge, node, of, simulation, workflow
from pydantic import JsonValue

from qmx_engine.core.commands import Finish
from qmx_engine.core.simulate import Terminal
from qmx_engine.definition.model import Workflow
from qmx_engine.nodes.base import NodeJob


def looped(**stops: JsonValue) -> Workflow:
    return workflow(
        [
            node("start", "trigger"),
            node("again", "loop", **stops),
            node("step", "script"),
            node("after", "script"),
        ],
        {
            "start": {"main": [edge("again")]},
            "again": {"body": [edge("step")], "done": [edge("after")]},
            "step": {"main": [edge("again", port="next")]},
        },
    )


def scored(*scores: float) -> Script:
    """Each body run adds 1 to `n` and reports the next score."""

    def advance(_: NodeJob, value: JsonValue) -> JsonValue:
        n = value.get("n", 0) if isinstance(value, dict) else 0
        assert isinstance(n, int)
        return {"n": n + 1, "score": scores[min(n, len(scores) - 1)]}

    return Script(advance, only="step")


def run(script: Script, **loop: JsonValue) -> tuple[list[JsonValue], Terminal | None, Script]:
    """The loop's plan on each `node_scheduled`, how the run ended, and the script."""
    sim = simulation(looped(**loop), script)
    ended = sim.start({"n": 0}, NOW)
    return [e["plan"] for e in of(sim.events, "node_scheduled", "again")], ended, script


def test_max_iterations_runs_the_body_that_many_times() -> None:
    plans, ended, script = run(scored(1.0), max_iterations=3)

    assert [c for c in script.calls if c[0] == "step"] == [("step", k, None) for k in range(3)]
    assert plans == [
        {"loop": {"iteration": 0, "stop": None}},
        {"loop": {"iteration": 1, "stop": None}},
        {"loop": {"iteration": 2, "stop": None}},
        {"loop": {"iteration": 3, "stop": "max_iterations"}},
    ]
    assert ended == Finish({"after": {"main": {"n": 3, "score": 1.0}}})


def test_budget_stops_once_the_body_reported_that_many_tokens() -> None:
    script = scored(1.0)
    script.tokens = 400

    plans, ended, _ = run(script, max_iterations=10, budget=1000)

    assert plans[-1] == {"loop": {"iteration": 3, "stop": "budget"}}
    assert ended == Finish({"after": {"main": {"n": 3, "score": 1.0}}})


def test_predicate_stops_on_the_last_value_handed_back() -> None:
    plans, ended, _ = run(scored(1.0), max_iterations=10, predicate="items.n >= 2")

    assert plans[-1] == {"loop": {"iteration": 2, "stop": "predicate"}}
    assert ended == Finish({"after": {"main": {"n": 2, "score": 1.0}}})


def test_no_progress_rounds_stops_after_the_second_flat_round() -> None:
    plans, ended, _ = run(
        scored(1.0, 2.0, 2.0, 2.0, 3.0), max_iterations=20, no_progress_rounds=2, metric="score"
    )

    assert plans[-1] == {"loop": {"iteration": 4, "stop": "no_progress_rounds"}}
    assert ended == Finish({"after": {"main": {"n": 4, "score": 2.0}}})


def test_a_resumed_loop_reruns_only_from_the_iteration_that_failed() -> None:
    script = scored(1.0)
    script.failing.add(("step", 2, None))
    sim = simulation(looped(max_iterations=4), script)
    sim.start({"n": 0}, NOW)
    mark = len(sim.events)

    ended = sim.resume(LATER)

    started = [
        (e["iteration"], e["attempt"]) for e in of(sim.events[mark:], "node_started", "step")
    ]
    assert started == [(2, 2), (3, 1)]
    assert ended == Finish({"after": {"main": {"n": 4, "score": 1.0}}})
