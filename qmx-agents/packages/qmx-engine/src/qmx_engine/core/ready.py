"""Readiness over the graph and `next_commands(state) -> list[Command]`.

A node is ready when every inbound source has settled and at least one inbound edge carried
output; when every source settled and none carried output (a `rule` routed the other way), the
node is skipped, and so is everything that only it feeds. The entry is the `trigger` node, which
takes the run's inputs. Edge mapping `one` is the only mapping this core runs (EP5).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Final

from pydantic import JsonValue

from qmx_engine.core.commands import Command, Finish, Park, Pause, Wait
from qmx_engine.core.replay import dispatch
from qmx_engine.core.state import JsonObject, Plan, Ready, State
from qmx_engine.definition.model import Edge, Node, Workflow, edges

PAUSING: Final = frozenset({"limit", "runaway"})


def inbound(workflow: Workflow) -> dict[str, list[Edge]]:
    found: dict[str, list[Edge]] = defaultdict(list)
    for edge in edges(workflow):
        found[edge.target.node].append(edge)
    return found


def topological(workflow: Workflow, into: dict[str, list[Edge]]) -> list[Node]:
    """Nodes upstream first, ties in definition order. A node on a cycle is left out."""
    waiting = {
        node.name: len({e.source for e in into.get(node.name, [])}) for node in workflow.nodes
    }
    feeds: dict[str, set[str]] = defaultdict(set)
    for edge in edges(workflow):
        feeds[edge.source].add(edge.target.node)
    order: list[Node] = []
    frontier = [node for node in workflow.nodes if waiting[node.name] == 0]
    by_name = {node.name: node for node in workflow.nodes}
    position = {node.name: i for i, node in enumerate(workflow.nodes)}
    while frontier:
        node = frontier.pop(0)
        order.append(node)
        released: list[Node] = []
        for target in feeds[node.name]:
            if target in waiting:
                waiting[target] -= 1
                if waiting[target] == 0:
                    released.append(by_name[target])
        frontier = sorted([*frontier, *released], key=lambda n: position[n.name])
    return order


def plan(state: State) -> Plan:
    workflow = state.definition
    into = inbound(workflow)
    by_name = {node.name: node for node in workflow.nodes}
    skipped: set[str] = set()
    ready: list[Ready] = []
    for node in topological(workflow, into):
        if node.id in state.nodes:
            continue
        edges_in = into.get(node.name, [])
        if not edges_in:
            if node.type == "trigger":
                ready.append(Ready(node, state.inputs))
            else:
                skipped.add(node.id)
            continue
        delivered: dict[str, list[JsonValue]] = defaultdict(list)
        settled = True
        for edge in edges_in:
            source = by_name[edge.source]
            run = state.nodes.get(source.id)
            if source.id in skipped:
                continue
            if run is None or run.phase != "finished" or run.outputs is None:
                settled = False
                break
            if edge.port in run.outputs:
                delivered[edge.target.port].append(run.outputs[edge.port])
        if not settled:
            continue
        if not delivered:
            skipped.add(node.id)
            continue
        inputs: JsonObject = {
            port: values[0] if len(values) == 1 else values for port, values in delivered.items()
        }
        ready.append(Ready(node, inputs))
    return Plan(ready, frozenset(skipped))


def _earliest(times: list[str | None]) -> str | None:
    known = [t for t in times if t is not None]
    return min(known) if known else None


def next_commands(state: State) -> list[Command]:
    if state.unfoldable is not None:
        return [] if state.ended == "parked" else [Park(state.unfoldable)]
    if state.ended is not None:
        return []
    for edge in edges(state.definition):
        if edge.target.map != "one":
            return [Park(f"edge map {edge.target.map!r} at {edge.path} is not run by this core")]
    for node_id, run in state.nodes.items():
        if run.phase == "failed":
            return [Park(f"node {node_id} failed: {run.error}")]
    found = plan(state)
    commands: list[Command] = [*dispatch(state, found.ready)]
    if commands or any(run.phase in ("scheduled", "started") for run in state.nodes.values()):
        return commands
    waiting = {i: run for i, run in state.nodes.items() if run.phase == "waiting"}
    if waiting:
        resume_at = _earliest([run.resume_at for run in waiting.values()])
        reasons = sorted({run.reason or "" for run in waiting.values()})
        if set(reasons) <= PAUSING:
            return [Pause(" ".join(reasons), resume_at)]
        return [Wait(tuple(waiting), resume_at)]
    workflow = state.definition
    unsettled = [
        n.id
        for n in workflow.nodes
        if n.id not in found.skipped
        and (n.id not in state.nodes or state.nodes[n.id].phase != "finished")
    ]
    if unsettled:
        return [Park(f"no node can start; unsettled: {' '.join(unsettled)}")]
    sources = {edge.source for edge in edges(workflow)}
    return [
        Finish(
            {
                n.id: state.nodes[n.id].outputs
                for n in workflow.nodes
                if n.name not in sources and n.id in state.nodes
            }
        )
    ]
