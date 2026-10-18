"""Node-level replay (AD-7): resume reruns the failed node and what follows it, never a finished
node, and an edited definition reruns only the nodes whose input hash changed."""

from __future__ import annotations

from typing import Any

from pydantic import JsonValue

from qmx_engine.core.commands import Finish, Park
from qmx_engine.core.simulate import Simulation
from qmx_engine.definition.model import Workflow
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok, step
from qmx_engine.nodes.trigger import Trigger

NOW = "2026-10-17T09:00:00+00:00"
LATER = "2026-10-17T10:00:00+00:00"


class Script:
    """Outputs its node id, its `prompt` parameter and what reached it; fails the nodes in
    `failing` once each."""

    def __init__(self, failing: set[str] | None = None) -> None:
        self.failing = set(failing or ())
        self.calls: list[str] = []

    def run(self, job: NodeJob) -> NodeResult:
        self.calls.append(job.node_id)
        if job.node_id in self.failing:
            self.failing.discard(job.node_id)
            return Failed("boom", "planted failure", "sig", retryable=True)
        parameters = job.node_definition.get("parameters")
        prompt = parameters.get("prompt") if isinstance(parameters, dict) else None
        return Ok({"main": {"node": job.node_id, "prompt": prompt, "upstream": job.inputs}})


def chain(edits: dict[str, dict[str, JsonValue]] | None = None) -> Workflow:
    nodes: list[dict[str, Any]] = [
        {"id": "n1", "name": "N1", "type": "trigger", "typeVersion": 1},
        *(
            {
                "id": f"n{i}",
                "name": f"N{i}",
                "type": "script",
                "typeVersion": 1,
                "parameters": {"prompt": f"prompt {i}"} | (edits or {}).get(f"n{i}", {}),
            }
            for i in range(2, 6)
        ),
    ]
    return Workflow.model_validate(
        {
            "schema": "qmx.workflow/1",
            "id": "chain",
            "name": "chain",
            "nodes": nodes,
            "connections": {
                f"N{i}": {"main": [[{"node": f"N{i + 1}", "port": "in", "map": "one"}]]}
                for i in range(1, 5)
            },
        }
    )


def since(simulation: Simulation, mark: int, kind: str, **match: JsonValue) -> list[str]:
    return [
        str(e.data["node_id"])
        for e in simulation.events[mark:]
        if e.kind == kind and all(e.data.get(k) == v for k, v in match.items())
    ]


def test_resume_after_node_3_fails_reruns_3_to_5_and_reuses_1_and_2() -> None:
    script = Script(failing={"n3"})
    simulation = Simulation(chain(), "run-e2", step({"trigger": Trigger(), "script": script}))

    assert simulation.start({"topic": "q-fin"}, NOW) == Park(
        "node n3 failed: boom: planted failure", "n3", attempt=1
    )
    mark = len(simulation.events)
    ended = simulation.resume(LATER)

    assert isinstance(ended, Finish)
    assert since(simulation, mark, "node_started") == ["n3", "n4", "n5"]
    assert since(simulation, mark, "node_finished", memo=True) == ["n1", "n2"]
    assert since(simulation, mark, "node_started", node_id="n3") == ["n3"]
    assert [e.data["attempt"] for e in simulation.events[mark:] if e.kind == "node_started"] == [
        2,
        1,
        1,
    ]
    assert script.calls == ["n2", "n3", "n3", "n4", "n5"]


def test_an_edited_prompt_reruns_the_node_and_only_the_nodes_its_output_reached() -> None:
    script = Script()
    simulation = Simulation(chain(), "run-edit", step({"trigger": Trigger(), "script": script}))
    simulation.start({"topic": "q-fin"}, NOW)

    mark = len(simulation.events)
    simulation.resume(LATER, chain({"n4": {"prompt": "prompt 4, sharper"}}))
    assert since(simulation, mark, "node_started") == ["n4", "n5"]
    assert since(simulation, mark, "node_finished", memo=True) == ["n1", "n2", "n3"]

    mark = len(simulation.events)
    simulation.resume(LATER, chain({"n4": {"prompt": "prompt 4, sharper", "note": "unread"}}))
    assert since(simulation, mark, "node_started") == ["n4"]
    assert since(simulation, mark, "node_finished", memo=True) == ["n1", "n2", "n3", "n5"]


def test_resuming_a_finished_run_calls_no_executor() -> None:
    script = Script()
    simulation = Simulation(chain(), "run-done", step({"trigger": Trigger(), "script": script}))
    simulation.start({"topic": "q-fin"}, NOW)
    calls = len(script.calls)

    mark = len(simulation.events)
    assert isinstance(simulation.resume(LATER), Finish)
    assert len(script.calls) == calls
    assert since(simulation, mark, "node_started") == []
    assert since(simulation, mark, "node_finished", memo=True) == ["n1", "n2", "n3", "n4", "n5"]
