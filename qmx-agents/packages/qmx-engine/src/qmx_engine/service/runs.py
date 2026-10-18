"""`runs.start`, `runs.get` and `runs.list` (SOLUTION-DESIGN 13), and the one path every run takes,
a live run of a version or a test run of a draft.

Each run gets its own folder `<home>/engine/runs/<run_id>/workflow/`, written from the Library's
bundle, so no two runs share files. A run's status is read from its ledger events with
SOLUTION-DESIGN 3.1's words; nothing stores it beside them.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import cast

from pydantic import JsonValue

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Reader, ledger_path
from qmx_engine.ports.library import (
    MAIN,
    Bundle,
    JsonObject,
    Mode,
    RunStatus,
    RunSummary,
    Stored,
)
from qmx_engine.runner import Outcome, new_run_id
from qmx_engine.runner import Refused as EngineRefused
from qmx_engine.service.context import Caller, Context, Refused, State, require
from qmx_engine.trace_export import export

SUBGRAPH_ENTRY = "subgraph-input"
NODE_KINDS = frozenset({"node_scheduled", "node_started", "node_finished", "node_failed"})


@dataclass(frozen=True, slots=True)
class RunState:
    status: RunStatus
    reason: str | None = None
    detail: str | None = None


def status_of(events: list[Event]) -> RunState:
    """The run's status from its events, current pass only (a `run_resumed` opens a new one)."""
    ended: RunState | None = None
    paused: RunState | None = None
    started = False
    slots: dict[tuple[JsonValue, ...], tuple[str, str | None]] = {}
    for event in events:
        data = event.data
        slot = (data.get("node_id"), data.get("iteration", 0), data.get("partition"))
        match event.kind:
            case "run_resumed":
                ended = paused = None
                slots = {}
            case "run_finished":
                ended = RunState("passed")
            case "run_cancelled":
                ended = RunState("stopped", str(data.get("reason") or "operator"))
            case "run_paused":
                paused = RunState("waiting", str(data.get("reason")))
            case "ladder_step" if data.get("step") == "park":
                ended = RunState("failed", "parked", str(data.get("reason")))
            case "ladder_step" if data.get("step") == "retry":
                slots[slot] = ("waiting", "retry")
            case "node_waiting":
                slots[slot] = ("waiting", str(data.get("reason")))
            case kind if kind in NODE_KINDS:
                started |= kind == "node_started"
                slots[slot] = (
                    "active" if kind in ("node_scheduled", "node_started") else "done",
                    None,
                )
            case _:
                pass
    if ended is not None:
        return ended
    if paused is not None:
        return paused
    if any(phase == "active" for phase, _ in slots.values()):
        return RunState("running")
    waits = sorted({str(why) for phase, why in slots.values() if phase == "waiting"})
    if waits:
        return RunState("waiting", " ".join(waits))
    return RunState("running" if started else "queued")


def induced(bundle: Bundle, node_ids: list[str]) -> Bundle:
    """The draft cut to the selected nodes and the edges between them. A selected node that read
    from an unselected one reads the run's inputs instead, through one added `trigger`."""
    definition = copy.deepcopy(bundle.definition)
    nodes = cast(list[JsonObject], definition.get("nodes") or [])
    names = {str(n["id"]): str(n["name"]) for n in nodes}
    unknown = sorted(set(node_ids) - set(names))
    if unknown:
        raise Refused("unknown_nodes", f"the draft has no nodes {unknown}")
    kept = {names[i] for i in node_ids}
    connections = cast(
        dict[str, dict[str, list[list[JsonObject]]]], definition.get("connections") or {}
    )
    cut: dict[str, dict[str, list[list[JsonObject]]]] = {}
    entries: list[JsonObject] = []
    for source, ports in connections.items():
        for port, groups in ports.items():
            for group in groups:
                inside = [t for t in group if t.get("node") in kept]
                if source in kept:
                    cut.setdefault(source, {}).setdefault(port, []).append(inside)
                else:
                    entries += [t for t in inside if t not in entries]
    definition["nodes"] = [n for n in nodes if n["name"] in kept]
    if entries:
        entry: JsonObject = {
            "id": SUBGRAPH_ENTRY,
            "name": SUBGRAPH_ENTRY,
            "type": "trigger",
            "typeVersion": 1,
            "parameters": {"kinds": ["manual"]},
        }
        definition["nodes"] = [entry, *cast(list[JsonValue], definition["nodes"])]
        cut[SUBGRAPH_ENTRY] = {"main": [entries]}
    definition["connections"] = cast(JsonValue, cut)
    return Bundle(definition, bundle.files)


async def run_bundle(
    ctx: Context,
    bundle: Bundle,
    *,
    object_id: str,
    item: str,
    mode: Mode,
    inputs: JsonValue,
    subgraph: list[str] | None,
    caller: Caller,
    fake: bool = False,
    run_id: str | None = None,
) -> tuple[Outcome, Stored]:
    run_id = run_id or new_run_id(ctx.clock.now())
    if subgraph is not None:
        bundle = induced(bundle, subgraph)
    root = bundle.write(ctx.home / "engine" / "runs" / run_id / "workflow")
    found = checked(root)
    if isinstance(found, list):
        codes = " ".join(sorted({p.code for p in found}))
        raise Refused("not_runnable", f"the workflow does not run: {codes}")
    try:
        outcome = await ctx.engine.start(
            root, found[1], mode=mode, inputs=inputs, run_id=run_id, fake=fake
        )
    except EngineRefused as refused:
        raise Refused("engine_refused", str(refused)) from refused
    await ctx.engine.settle()
    return outcome, summarize(ctx, outcome, item, object_id, mode, caller.principal)


def summarize(
    ctx: Context, outcome: Outcome, item: str, object_id: str, mode: Mode, started_by: str
) -> Stored:
    with Reader.open(ctx.home) as reader:
        state = status_of(reader.events(outcome.run_id))
    return export(
        ctx.home,
        outcome.run_id,
        ctx.library,
        workflow_item=item,
        object_id=object_id,
        mode=mode,
        status=outcome.status,
        reason=state.reason,
        started_by=started_by,
    )


def summarize_again(ctx: Context, outcome: Outcome) -> Stored | None:
    """A new summary for a run that was resumed, from its last one; None when it has none."""
    found = ctx.library.objects(outcome.run_id, "workflow-run")
    if not found:
        return None
    last = found[-1].fields
    mode: Mode = "live" if last.get("mode") == "live" else "test"
    return summarize(
        ctx,
        outcome,
        str(last.get("workflow_item")),
        str(last.get("object_id")),
        mode,
        str(last.get("started_by")),
    )


@dataclass(frozen=True, slots=True)
class RunView:
    run_id: str
    mode: Mode
    status: RunStatus
    reason: str | None
    detail: str | None
    object_id: str | None


class Runs:
    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx

    def version_state(self, version: Stored) -> State:
        """Published means on `main` (AD-11, L-51); any other ref, a run's own included, is a
        draft."""
        if version.ref != MAIN:
            return "draft"
        found = self.ctx.library.annotation(version.object_id, "state")
        return cast(State, found) if found in ("enabled", "disabled", "archived") else "published"

    def pinned(self, object_id: str, follow_champion: bool) -> Stored:
        """The pinned version, or its champion when the caller follows it and the champion
        descends from the pinned one through `replaces` or `variant-of` (AD-10, L3)."""
        library = self.ctx.library
        version = library.get(object_id)
        champion = library.champion(version.item) if follow_champion else None
        if champion is not None and self.descends(champion, object_id):
            return library.get(champion)
        return version

    def descends(self, child: str, ancestor: str) -> bool:
        seen, frontier = {child}, [child]
        while frontier:
            here = frontier.pop()
            if here == ancestor:
                return True
            for edge in self.ctx.library.edges(here):
                if edge.edge in ("replaces", "variant-of") and edge.to_id not in seen:
                    seen.add(edge.to_id)
                    frontier.append(edge.to_id)
        return False

    async def start(
        self,
        object_id: str,
        *,
        caller: Caller,
        inputs: JsonValue = None,
        subgraph: list[str] | None = None,
        follow_champion: bool = False,
        run_id: str | None = None,
    ) -> RunView:
        """A live run of a published version. A draft never runs live; `tests.run` tests it."""
        version = self.pinned(object_id, follow_champion)
        if version.kind != "workflow":
            raise Refused("not_a_version", f"{object_id} is a {version.kind}")
        require(self.version_state(version), "run", f"workflow object {version.object_id}")
        outcome, _ = await run_bundle(
            self.ctx,
            self.ctx.library.get_object(version.object_id),
            object_id=version.object_id,
            item=version.item,
            mode="live",
            inputs=inputs,
            subgraph=subgraph,
            caller=caller,
            run_id=run_id,
        )
        return self.get(outcome.run_id)

    def get(self, run_id: str) -> RunView:
        if not ledger_path(self.ctx.home).exists():
            raise Refused("unknown_run", f"no run {run_id}")
        with Reader.open(self.ctx.home) as reader:
            events = reader.events(run_id)
        if not events or events[0].kind != "run_created":
            raise Refused("unknown_run", f"no run {run_id}")
        state = status_of(events)
        mode: Mode = "live" if events[0].data.get("mode") == "live" else "test"
        summaries = self.ctx.library.objects(run_id, "workflow-run")
        found = summaries[-1].fields.get("object_id") if summaries else None
        object_id = found if isinstance(found, str) else None
        return RunView(run_id, mode, state.status, state.reason, state.detail, object_id)

    def list(self, workflow_item: str, object_id: str | None = None) -> list[RunSummary]:
        return self.ctx.library.list_runs(workflow_item, object_id)
