"""Node-level replay (AD-7): resume reruns the failed node and what follows it, never a finished
node, and an edited definition reruns only the nodes whose input hash changed."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flows import LATER, Flow
from pydantic import JsonValue

from qmx_engine.definition.model import Workflow
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok


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


def chain(edits: dict[str, dict[str, JsonValue]] | None = None, *, held: bool = False) -> Workflow:
    """N1 to N5, and with `held` a last node waiting on an event, so the run stays open."""
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
    last = 5
    if held:
        nodes.append(
            {
                "id": "n6",
                "name": "N6",
                "type": "wait",
                "typeVersion": 1,
                "parameters": {"event": "go"},
            }
        )
        last = 6
    return Workflow.model_validate(
        {
            "schema": "qmx.workflow/1",
            "id": "chain",
            "name": "chain",
            "nodes": nodes,
            "connections": {
                f"N{i}": {"main": [[{"node": f"N{i + 1}", "port": "in", "map": "one"}]]}
                for i in range(1, last)
            },
        }
    )


def since(flow: Flow, mark: int, kind: str, **match: JsonValue) -> list[str]:
    return [
        str(e.data["node_id"])
        for e in flow.events[mark:]
        if e.kind == kind and all(e.data.get(k) == v for k, v in match.items())
    ]


def test_resume_after_node_3_fails_reruns_3_to_5_and_reuses_1_and_2(tmp_path: Path) -> None:
    script = Script(failing={"n3"})
    flow = Flow(tmp_path, chain(), {"script": script}, run_id="run-e2")

    first = flow.start({"topic": "q-fin"})
    mark = len(flow.events)
    ended = flow.resume(LATER)

    assert (first.status, first.reason) == ("failed", "node n3 failed: boom: planted failure")
    assert ended.status == "passed"
    assert since(flow, mark, "node_started") == ["n3", "n4", "n5"]
    assert since(flow, mark, "node_finished", memo=True) == ["n1", "n2"]
    assert [e.data["attempt"] for e in flow.events[mark:] if e.kind == "node_started"] == [2, 1, 1]
    assert script.calls == ["n2", "n3", "n3", "n4", "n5"]


def test_an_edited_prompt_reruns_the_node_and_only_the_nodes_its_output_reached(
    tmp_path: Path,
) -> None:
    flow = Flow(tmp_path, chain(held=True), {"script": Script()}, run_id="run-edit")
    flow.start({"topic": "q-fin"})

    mark = len(flow.events)
    flow.write(chain({"n4": {"prompt": "prompt 4, sharper"}}, held=True))
    flow.resume(LATER)
    assert since(flow, mark, "node_started") == ["n4", "n5"]
    assert since(flow, mark, "node_finished", memo=True) == ["n1", "n2", "n3"]

    mark = len(flow.events)
    flow.write(chain({"n4": {"prompt": "prompt 4, sharper", "note": "unread"}}, held=True))
    flow.resume(LATER)
    assert since(flow, mark, "node_started") == ["n4"]
    assert since(flow, mark, "node_finished", memo=True) == ["n1", "n2", "n3", "n5"]


def test_resuming_a_finished_run_calls_no_executor(tmp_path: Path) -> None:
    script = Script()
    flow = Flow(tmp_path, chain(), {"script": script}, run_id="run-done")
    flow.start({"topic": "q-fin"})
    calls = len(script.calls)

    mark = len(flow.events)
    ended = flow.resume(LATER)

    assert (ended.status, ended.reason) == ("passed", "the run already ended passed")
    assert len(script.calls) == calls
    assert since(flow, mark, "node_started") == []
