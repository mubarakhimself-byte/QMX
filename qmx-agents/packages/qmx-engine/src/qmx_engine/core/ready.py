"""Readiness over the graph and `next_commands(state) -> list[Command]`.

The planner walks the nodes upstream first and works out, for each node in its current iteration,
its partitions (its shape) and which of its slots may start. A slot is ready when every source
slot it reads has settled, every inbound edge marked `required` carried output, and at least one
inbound edge carried output; in a loop body an edge from outside the loop is context and never
makes a slot ready on its own (AD-5). Otherwise the slot is skipped (a `rule` routed the other
way), and so is what only it feeds. The entry is the `trigger` node, which takes the run's inputs.

Shapes: a node fed by a fanning edge (`core.edges`) runs one slot per partition. A node fed by
`one` edges from a source that fanned out runs one slot per source partition, each starting as soon
as its own source partition finishes. A `join` collects every partition of its one source into
one slot (`core.joins`). A `loop` runs one slot per iteration (`core.loops`), and the nodes of its
body run at the loop's latest iteration. A `wait` slot starts only once its hold is due
(`core.waits`). Nested fan-out, a partitioned loop and a loop inside a loop body are refused by
validation (`nesting_unsupported`); a run of an unvalidated definition still parks naming them.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Final

from pydantic import JsonValue, ValidationError

from qmx_engine.core.commands import Command, Finish, Hold, Park, Pause, Wait
from qmx_engine.core.edges import MAPS, FanError, fan
from qmx_engine.core.joins import Fired, JoinSpec, Unmet, close
from qmx_engine.core.ladder import admit, climb
from qmx_engine.core.loops import LoopError, LoopSpec, stop
from qmx_engine.core.partitions import ChunkError
from qmx_engine.core.replay import dispatch
from qmx_engine.core.state import JsonObject, Plan, Ready, Slot, State
from qmx_engine.core.waits import WaitSpec, due
from qmx_engine.definition.model import Edge, Node, Workflow, edges
from qmx_engine.definition.registry import LOOP_BACK_PORT, REGISTRY

PAUSING: Final = frozenset({"limit"})

type Shape = int | None
"""A node's partition count in one iteration; None when it runs as one slot."""


def kind(node: Node) -> str:
    found = REGISTRY.kind(node.type)
    return found.name if found is not None else node.type


class Stuck(Exception):
    """The run cannot go on; the message is the park reason."""


@dataclass(frozen=True, slots=True)
class Graph:
    order: list[Node]
    """Upstream first, ties in definition order, loop-back edges left out."""
    by_name: dict[str, Node]
    into: dict[str, list[Edge]]
    """Inbound edges by target name, loop-back edges left out."""
    consumers: dict[str, list[Node]]
    by_id: dict[str, Node]
    loop_of: dict[str, str]
    """Body node name to its loop's name."""
    back: dict[str, Edge]
    """Loop name to the edge that hands each iteration's value back."""
    body: dict[str, frozenset[str]]


def topological(workflow: Workflow, links: list[Edge]) -> list[Node]:
    """Nodes upstream first, ties in definition order. A node on a cycle is left out."""
    waiting = {
        node.name: len({e.source for e in links if e.target.node == node.name})
        for node in workflow.nodes
    }
    feeds: dict[str, set[str]] = defaultdict(set)
    for edge in links:
        feeds[edge.source].add(edge.target.node)
    by_name = {node.name: node for node in workflow.nodes}
    position = {node.name: i for i, node in enumerate(workflow.nodes)}
    order: list[Node] = []
    frontier = [node for node in workflow.nodes if waiting[node.name] == 0]
    while frontier:
        node = frontier.pop(0)
        order.append(node)
        for target in feeds[node.name]:
            if target in waiting:
                waiting[target] -= 1
                if waiting[target] == 0:
                    frontier.append(by_name[target])
        frontier.sort(key=lambda n: position[n.name])
    return order


def graph(workflow: Workflow) -> Graph:
    by_name = {node.name: node for node in workflow.nodes}
    links: list[Edge] = []
    back: dict[str, Edge] = {}
    for edge in edges(workflow):
        target = by_name.get(edge.target.node)
        if target is not None and kind(target) == "loop" and edge.target.port == LOOP_BACK_PORT:
            if edge.target.node in back:
                raise Stuck(f"loop {target.id} has more than one edge into {LOOP_BACK_PORT}")
            back[edge.target.node] = edge
        else:
            links.append(edge)
    into: dict[str, list[Edge]] = defaultdict(list)
    consumers: dict[str, list[Node]] = defaultdict(list)
    for edge in links:
        into[edge.target.node].append(edge)
        consumers[edge.source].append(by_name[edge.target.node])
    loop_of: dict[str, str] = {}
    body: dict[str, frozenset[str]] = {}
    for loop in (n for n in workflow.nodes if kind(n) == "loop"):
        reached: set[str] = set()
        frontier = [e.target.node for e in links if e.source == loop.name and e.port == "body"]
        while frontier:
            name = frontier.pop()
            if name not in reached and name != loop.name:
                reached.add(name)
                frontier.extend(e.target.node for e in links if e.source == name)
        for name in reached:
            if kind(by_name[name]) == "loop" or name in loop_of:
                raise Stuck(f"loop {loop.id} holds another loop; nested loops are not run yet")
            loop_of[name] = loop.name
        if reached and loop.name not in back:
            raise Stuck(f"loop {loop.id} has no edge into {LOOP_BACK_PORT}")
        body[loop.name] = frozenset(reached)
    by_id = {node.id: node for node in workflow.nodes}
    return Graph(topological(workflow, links), by_name, into, consumers, by_id, loop_of, back, body)


@dataclass
class Planner:
    state: State
    graph: Graph
    shape: dict[tuple[str, int], Shape] = field(default_factory=dict[tuple[str, int], Shape])
    skipped: set[Slot] = field(default_factory=set[Slot])
    ready: list[Ready] = field(default_factory=list[Ready])
    holds: list[Hold] = field(default_factory=list[Hold])
    held: list[tuple[Slot, str | None]] = field(default_factory=list[tuple[Slot, str | None]])

    def phase(self, slot: Slot) -> str:
        if slot in self.skipped:
            return "skipped"
        run = self.state.nodes.get(slot)
        return "pending" if run is None else run.phase

    def outputs(self, slot: Slot) -> JsonObject:
        run = self.state.nodes.get(slot)
        return run.outputs or {} if run is not None else {}

    def latest(self, loop: Node) -> int | None:
        found = [s.iteration for s in self.state.nodes if s.node_id == loop.id]
        return max(found) if found else None

    def slots(self, node: Node, iteration: int) -> list[Slot]:
        """The node's slots in one iteration; empty while its shape is unknown."""
        if (node.name, iteration) not in self.shape:
            return []
        count = self.shape[(node.name, iteration)]
        if count is None:
            return [Slot(node.id, iteration)]
        return [Slot(node.id, iteration, p) for p in range(count)]

    def context(self, node: Node) -> int | None:
        """The iteration the node runs at now; None while its loop has not reached it. A body node
        whose loop is skipped or done is skipped at that iteration."""
        name = self.graph.loop_of.get(node.name)
        if name is None:
            return 0
        loop = self.graph.by_name[name]
        k = self.latest(loop)
        if k is None:
            if Slot(loop.id) in self.skipped:
                self.skip(node, 0)
                return 0
            return None
        if self.phase(Slot(loop.id, k)) != "finished":
            return None
        if "body" not in self.outputs(Slot(loop.id, k)):
            self.skip(node, k)
        return k

    def skip(self, node: Node, iteration: int) -> None:
        self.shape[(node.name, iteration)] = None
        self.skipped.add(Slot(node.id, iteration))

    def source_iteration(self, source: Node, node: Node, iteration: int) -> int | None:
        """The iteration of `source` that `node` at `iteration` reads; None while pending."""
        loop_of = self.graph.loop_of
        if loop_of.get(node.name) == source.name:
            return iteration
        if kind(source) == "loop":
            k = self.latest(source)
            if k is None:
                return 0 if Slot(source.id) in self.skipped else None
            done = self.phase(Slot(source.id, k)) == "finished" and "done" in self.outputs(
                Slot(source.id, k)
            )
            return k if done else None
        inside = loop_of.get(source.name)
        if inside == loop_of.get(node.name):
            return iteration
        if inside is None:
            return 0
        raise Stuck(f"edge from {source.id} leaves its loop body other than through done")

    def offer(self, node: Node, slot: Slot, inputs: JsonObject, plan: JsonObject | None) -> None:
        if slot in self.state.nodes:
            return
        walk = self.state.walks.get(slot)
        if walk is not None and walk.retry_at is not None:
            now = self.state.now
            if now is None or now < walk.retry_at:
                self.held.append((slot, walk.retry_at))
                return
        if kind(node) == "wait":
            held = self.state.holds.get(slot)
            if held is None:
                spec = parse(WaitSpec, node)
                self.holds.append(Hold(*slot, spec.seconds, spec.until, spec.event))
                return
            if not due(held, self.state.now, self.state.received):
                self.held.append((slot, held.resume_at))
                return
        self.ready.append(Ready(node, inputs, slot.iteration, slot.partition, plan))

    def visit(self, node: Node) -> None:
        if kind(node) == "loop":
            self.visit_loop(node)
            return
        iteration = self.context(node)
        if iteration is None or (node.name, iteration) in self.shape:
            return
        into = self.graph.into.get(node.name, [])
        if not into:
            if kind(node) != "trigger":
                self.skip(node, iteration)
                return
            self.shape[(node.name, iteration)] = None
            if Slot(node.id) not in self.state.nodes:
                self.ready.append(Ready(node, self.state.inputs))
            return
        sources: list[tuple[Edge, Node, int]] = []
        for edge in into:
            source = self.graph.by_name[edge.source]
            at = self.source_iteration(source, node, iteration)
            if at is None or (source.name, at) not in self.shape:
                return
            sources.append((edge, source, at))
        if kind(node) == "join":
            self.visit_join(node, iteration, sources)
        elif any(edge.target.map in MAPS for edge, _, _ in sources):
            self.visit_fan(node, iteration, sources)
        else:
            self.visit_mirror(node, iteration, sources)

    def visit_mirror(
        self, node: Node, iteration: int, sources: list[tuple[Edge, Node, int]]
    ) -> None:
        counts = {n for _, s, at in sources if (n := self.shape[(s.name, at)]) is not None}
        if len(counts) > 1:
            raise Stuck(f"node {node.id} reads sources fanned out to {sorted(counts)} partitions")
        count = counts.pop() if counts else None
        self.shape[(node.name, iteration)] = count
        for partition in [None] if count is None else range(count):
            delivered: dict[str, list[JsonValue]] = defaultdict(list)
            carried: list[Edge] = []
            for edge, source, at in sources:
                own = partition if self.shape[(source.name, at)] is not None else None
                slot = Slot(source.id, at, own)
                phase = self.phase(slot)
                if phase == "skipped":
                    continue
                if phase != "finished":
                    break
                if edge.port in (found := self.outputs(slot)):
                    delivered[edge.target.port].append(found[edge.port])
                    carried.append(edge)
            else:
                slot = Slot(node.id, iteration, partition)
                if not self.runs_on(node, [edge for edge, _, _ in sources], carried):
                    self.skipped.add(slot)
                    continue
                inputs: JsonObject = {
                    port: values[0] if len(values) == 1 else values
                    for port, values in delivered.items()
                }
                self.offer(node, slot, inputs, None)

    def runs_on(self, node: Node, into: list[Edge], carried: list[Edge]) -> bool:
        """AD-5 readiness, once every source has settled: every `required` edge carried output and
        at least one edge did. In a loop body, an edge from outside the loop is context, so at
        least one edge from inside the body must carry (B-24, B-87)."""
        if any(edge.target.required and edge not in carried for edge in into):
            return False
        loop = self.graph.loop_of.get(node.name)
        if loop is None:
            return bool(carried)
        return any(e.source == loop or self.graph.loop_of.get(e.source) == loop for e in carried)

    def visit_fan(self, node: Node, iteration: int, sources: list[tuple[Edge, Node, int]]) -> None:
        constants: JsonObject = {}
        fanning: list[tuple[Edge, JsonValue]] = []
        for edge, source, at in sources:
            if self.shape[(source.name, at)] is not None:
                raise Stuck(f"node {node.id} fans out what {source.id} already fanned out")
            phase = self.phase(Slot(source.id, at))
            if phase not in ("finished", "skipped"):
                return
            found = self.outputs(Slot(source.id, at)) if phase == "finished" else {}
            if edge.target.map in MAPS:
                if edge.port not in found:
                    self.skip(node, iteration)
                    return
                fanning.append((edge, found[edge.port]))
            elif edge.port in found:
                constants[edge.target.port] = found[edge.port]
            elif edge.target.required:
                self.skip(node, iteration)
                return
        try:
            parts = fan([(edge.target, value) for edge, value in fanning], self.state.settings)
        except (FanError, ChunkError) as error:
            raise Stuck(f"node {node.id}: {error}") from None
        self.shape[(node.name, iteration)] = len(parts)
        for partition, part in enumerate(parts):
            plan = part.plan | {"of": len(parts)}
            self.offer(node, Slot(node.id, iteration, partition), constants | part.inputs, plan)

    def visit_join(self, node: Node, iteration: int, sources: list[tuple[Edge, Node, int]]) -> None:
        if len(sources) != 1 or sources[0][0].target.map != "one":
            raise Stuck(f"join {node.id} takes exactly one one-edge")
        ((edge, source, at),) = sources
        self.shape[(node.name, iteration)] = None
        slot = Slot(node.id, iteration)
        if slot in self.state.nodes:
            return
        spec = parse(JoinSpec, node)
        runs = [s for s in self.slots(source, at) if self.phase(s) != "skipped"]
        if not runs:
            self.skipped.add(slot)
            return
        ids = {s.partition or 0: s for s in runs}
        finished = sorted(
            (s for s in runs if self.phase(s) == "finished"), key=lambda s: self.state.nodes[s].seq
        )
        failed = [s.partition or 0 for s in runs if self.phase(s) == "failed"]
        held = self.state.holds.get(slot)
        timed_out = held is not None and due(held, self.state.now, self.state.received)
        fired = self.state.joins.get(slot)
        if fired is not None:
            if any(p not in ids or self.phase(ids[p]) != "finished" for p in fired):
                return
            closing: Fired | Unmet | None = Fired(fired, tuple(p for p in ids if p not in fired))
        else:
            closing = close(
                spec, list(ids), [s.partition or 0 for s in finished], failed, timed_out=timed_out
            )
        if isinstance(closing, Fired):
            merged = [self.outputs(ids[p]) for p in closing.merged]
            values: list[JsonValue] = [found[edge.port] for found in merged if edge.port in found]
            plan: JsonObject = {
                "join": {
                    "mode": spec.mode,
                    "expected": len(ids),
                    "merged": list[JsonValue](closing.merged),
                    "late": list[JsonValue](closing.late),
                }
            }
            self.ready.append(Ready(node, {"in": values}, iteration, None, plan))
        elif closing is not None:
            raise Stuck(f"join {node.id} {closing.code}: {closing.message}")
        elif spec.timeout_seconds is not None:
            if held is None:
                self.holds.append(Hold(node.id, iteration, None, spec.timeout_seconds))
            else:
                self.held.append((slot, held.resume_at))

    def visit_loop(self, loop: Node) -> None:
        k = self.latest(loop)
        for iteration in range(k + 1 if k is not None else 0):
            self.shape[(loop.name, iteration)] = None
        if k is None:
            self.first_iteration(loop)
            return
        if self.phase(Slot(loop.id, k)) != "finished" or "body" not in self.outputs(
            Slot(loop.id, k)
        ):
            return
        back = self.graph.back[loop.name]
        handed = self.outputs(Slot(self.graph.by_name[back.source].id, k))
        if back.port in handed:
            self.iterate(loop, k + 1, handed[back.port])

    def first_iteration(self, loop: Node) -> None:
        self.shape[(loop.name, 0)] = None
        delivered: JsonObject = {}
        for edge in self.graph.into.get(loop.name, []):
            source = self.graph.by_name[edge.source]
            at = self.source_iteration(source, loop, 0)
            if at is None or (source.name, at) not in self.shape:
                return
            if self.shape[(source.name, at)] is not None:
                raise Stuck(f"loop {loop.id} reads {source.id}, which fanned out; it runs once")
            phase = self.phase(Slot(source.id, at))
            if phase not in ("finished", "skipped"):
                return
            if phase == "finished" and edge.port in (found := self.outputs(Slot(source.id, at))):
                delivered[edge.target.port] = found[edge.port]
        if "in" not in delivered:
            self.skipped.add(Slot(loop.id))
            return
        self.iterate(loop, 0, delivered["in"])

    def iterate(self, loop: Node, k: int, value: JsonValue) -> None:
        spec = parse(LoopSpec, loop)
        handed: list[JsonValue] = []
        if k:
            back = self.graph.back[loop.name]
            source = self.graph.by_name[back.source]
            handed = [self.outputs(Slot(source.id, j)).get(back.port) for j in range(k)]
        body = {self.graph.by_name[name].id for name in self.graph.body[loop.name]}
        spent = sum(n for s, n in self.state.spent.items() if s.node_id in body and s.iteration < k)
        try:
            reason = stop(spec, k, handed, spent)
        except LoopError as error:
            raise Stuck(f"loop {loop.id}: {error}") from None
        plan: JsonObject = {"loop": {"iteration": k, "stop": reason}}
        self.offer(loop, Slot(loop.id, k), {"in": value, "stop": reason}, plan)

    def settled(self, node: Node) -> bool:
        iteration = self.context(node)
        if kind(node) == "loop":
            k = self.latest(node)
            if k is None:
                return Slot(node.id) in self.skipped
            return self.phase(Slot(node.id, k)) == "finished" and "done" in self.outputs(
                Slot(node.id, k)
            )
        if iteration is None or (node.name, iteration) not in self.shape:
            return False
        return all(
            self.phase(s) in ("finished", "skipped")
            or (self.phase(s) == "failed" and tolerated(self.graph, s))
            for s in self.slots(node, iteration)
        )

    def sink(self, node: Node) -> JsonValue:
        iteration = self.context(node) or 0
        if self.shape.get((node.name, iteration)) is None:
            slot = Slot(node.id, iteration)
            return self.outputs(slot) if self.phase(slot) == "finished" else None
        return [self.outputs(s) for s in self.slots(node, iteration) if self.phase(s) == "finished"]


def parse[T: WaitSpec | JoinSpec | LoopSpec](spec: type[T], node: Node) -> T:
    try:
        return spec.model_validate(node.parameters)
    except ValidationError as error:
        problems = "; ".join(f"{'.'.join(map(str, e['loc']))} {e['msg']}" for e in error.errors())
        raise Stuck(f"node {node.id} parameters: {problems}") from None


def tolerated(graph: Graph, slot: Slot) -> bool:
    """A failed partition that only joins read: each join decides whether it can still fire."""
    readers = graph.consumers.get(graph.by_id[slot.node_id].name, [])
    return slot.partition is not None and bool(readers) and all(kind(n) == "join" for n in readers)


def plan(state: State, shape: Graph) -> Plan:
    try:
        planner = Planner(state, shape)
        for node in planner.graph.order:
            planner.visit(node)
        unsettled = [n.id for n in planner.graph.order if not planner.settled(n)]
    except Stuck as stuck:
        return Plan(park=str(stuck))
    workflow = state.definition
    sources = {edge.source for edge in edges(workflow)}
    sinks: JsonObject = {
        n.id: found
        for n in workflow.nodes
        if n.name not in sources and (found := planner.sink(n)) is not None
    }
    return Plan(planner.ready, planner.holds, planner.held, unsettled, sinks)


def _earliest(times: list[str | None]) -> str | None:
    known = [t for t in times if t is not None]
    return min(known) if known else None


def describe(slot: Slot) -> str:
    where = "" if slot.partition is None else f" partition {slot.partition}"
    return f"node {slot.node_id}{where}" + (
        f" iteration {slot.iteration}" if slot.iteration else ""
    )


def next_commands(state: State) -> list[Command]:
    if state.unfoldable is not None:
        return [] if state.ended == "parked" else [Park(state.unfoldable)]
    if state.ended is not None:
        return []
    try:
        shape = graph(state.definition)
    except Stuck as stuck:
        return [Park(str(stuck))]
    failed = [
        (slot, run)
        for slot, run in state.nodes.items()
        if run.phase == "failed" and not tolerated(shape, slot)
    ]
    if failed:
        slot, run = min(failed, key=lambda found: found[1].seq)
        reason = f"{describe(slot)} failed: {run.error}"
        return climb(state, shape.by_id[slot.node_id], slot, run, reason)
    found = plan(state, shape)
    if found.park is not None:
        return [Park(found.park)]
    wanted: list[Command] = [*found.holds, *dispatch(state, found.ready)]
    commands, detail = admit(state, wanted)
    inflight = any(run.phase in ("scheduled", "started") for run in state.nodes.values())
    if commands or inflight:
        return commands
    waiting = {s: run for s, run in state.nodes.items() if run.phase == "waiting"}
    if detail is not None and (len(commands) < len(wanted) or waiting or found.held):
        return [Pause("limits", None, detail)]
    if waiting or found.held:
        times = [run.resume_at for run in waiting.values()] + [at for _, at in found.held]
        reasons = {run.reason or "" for run in waiting.values()}
        if waiting and not found.held and reasons <= PAUSING:
            return [Pause(" ".join(sorted(reasons)), _earliest(times))]
        ids = dict.fromkeys(s.node_id for s in [*waiting, *(s for s, _ in found.held)])
        return [Wait(tuple(ids), _earliest(times))]
    if found.unsettled:
        return [Park(f"no node can start; unsettled: {' '.join(found.unsettled)}")]
    return [Finish(found.sinks)]
