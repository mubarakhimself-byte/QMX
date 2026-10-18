"""Workflow builders and planted executors shared by the fan-out, join, loop and wait tests."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from pydantic import JsonValue

from qmx_engine.core.simulate import Entry, Simulation
from qmx_engine.definition.model import Workflow
from qmx_engine.nodes.base import Executor, Failed, NodeJob, NodeResult, Ok, step
from qmx_engine.nodes.join import Join
from qmx_engine.nodes.loop import Loop
from qmx_engine.nodes.trigger import Trigger
from qmx_engine.nodes.wait import Wait, resume_at
from qmx_engine.settings import DEFAULTS

NOW = "2026-10-17T09:00:00+00:00"
LATER = "2026-10-17T10:00:00+00:00"


def node(name: str, type_: str, **parameters: JsonValue) -> dict[str, Any]:
    return {"id": name, "name": name, "type": type_, "typeVersion": 1, "parameters": parameters}


def edge(target: str, map_: str = "one", port: str = "in", **extra: JsonValue) -> dict[str, Any]:
    return {"node": target, "port": port, "map": map_, **extra}


def workflow(nodes: list[dict[str, Any]], connections: dict[str, dict[str, Any]]) -> Workflow:
    return Workflow.model_validate(
        {
            "schema": "qmx.workflow/1",
            "id": "flow",
            "name": "flow",
            "nodes": nodes,
            "connections": {
                source: {port: [targets] for port, targets in ports.items()}
                for source, ports in connections.items()
            },
        }
    )


type Planted = tuple[str, int, int | None]
"""A slot as `(node_id, iteration, partition)`."""


class Script:
    """Applies `fn` to the slot's `in` value (only on node `only` when given; the others pass it
    through). A slot in `failing` fails once; a `(node, partition)` in `slow` starts and is left in
    flight. `tokens` are reported on each finished attempt. `calls` lists every slot it ran."""

    def __init__(
        self,
        fn: Callable[[NodeJob, JsonValue], JsonValue] = lambda _, value: value,
        *,
        failing: set[Planted] | None = None,
        slow: set[tuple[str, int | None]] | None = None,
        tokens: int = 0,
        only: str | None = None,
    ) -> None:
        self.fn = fn
        self.only = only
        self.failing: set[Planted] = set(failing or ())
        self.slow = set(slow or ())
        self.tokens = tokens
        self.calls: list[Planted] = []

    def run(self, job: NodeJob) -> NodeResult:
        self.calls.append((job.node_id, job.iteration, job.partition))
        slot: Planted = (job.node_id, job.iteration, job.partition)
        if slot in self.failing:
            self.failing.discard(slot)
            return Failed("boom", "planted failure", "planted", retryable=True)
        ports = job.inputs if isinstance(job.inputs, dict) else {}
        value = ports.get("in")
        return Ok({"main": self.fn(job, value) if self.only in (None, job.node_id) else value})


def simulation(
    definition: Workflow,
    script: Script,
    *,
    settings: Mapping[str, object] = DEFAULTS,
    run_id: str = "run-1",
) -> Simulation:
    executors: dict[str, Executor] = {
        "trigger": Trigger(),
        "script": script,
        "join": Join(),
        "loop": Loop(),
        "wait": Wait(),
    }
    run = step(executors)

    def stepped(command: Any) -> list[tuple[str, dict[str, JsonValue]]]:
        drafts = run(command)
        if (command.node_id, command.partition) in script.slow:
            return drafts[:1]
        kind, data = drafts[-1]
        if script.tokens and kind == "node_finished":
            data["tokens"] = {"out": script.tokens}
        return drafts

    return Simulation(definition, run_id, stepped, settings=settings, clock=resume_at)


def finish(sim: Simulation, node_id: str, partition: int, outputs: dict[str, JsonValue]) -> Any:
    """Deliver the ending of a slow partition's attempt, as a worker would, and drive on."""
    sim.append(
        "node_finished",
        {
            "node_id": node_id,
            "iteration": 0,
            "partition": partition,
            "attempt": 1,
            "outputs": outputs,
        },
    )
    return sim.drive()


def of(events: list[Entry], kind: str, node_id: str) -> list[dict[str, JsonValue]]:
    return [e.data for e in events if e.kind == kind and e.data.get("node_id") == node_id]
