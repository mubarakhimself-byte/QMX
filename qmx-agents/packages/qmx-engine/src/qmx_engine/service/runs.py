"""`runs.start`, `runs.get` and `runs.list` (SOLUTION-DESIGN 13), and the one path every run takes,
a live run of a version or a test run of a draft.

Each run gets its own folder `<home>/engine/runs/<run_id>/workflow/`, written from the Library's
bundle, so no two runs share files. A run's status is a pure fold over its ledger events and the
engine's live attempts, with SOLUTION-DESIGN 3.1's words; nothing stores it beside them, and
`runs.list` reads it from there on every call (B-40, B-73). A live run that passed fires every
`after` trigger on its workflow, whoever started it (B-60), and, run whole on real models, marks
its version `tested-by` it, since a passed run in either mode tests its content hash (AD-11, L-56).
A test run a wake resumed gets a fresh test report beside its fresh summary (B-61). Cancelling a run
cancels every child run under it (AD-5, B-66).
"""

from __future__ import annotations

import copy
from collections.abc import Container, Mapping
from dataclasses import dataclass, replace
from typing import cast

from pydantic import JsonValue

from qmx_engine.core.replay import idempotency_key
from qmx_engine.core.state import Slot
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Operation, Reader, Transaction, ledger_path
from qmx_engine.ports.library import (
    MAIN,
    Bundle,
    JsonObject,
    Mode,
    RunStatus,
    RunSummary,
    Stored,
)
from qmx_engine.runner import Engine, Outcome, new_run_id
from qmx_engine.runner import Refused as EngineRefused
from qmx_engine.service.context import Caller, Context, Refused, State, require
from qmx_engine.trace_export import export
from qmx_engine.triggers.rows import After, fire_now, triggers

SUBGRAPH_ENTRY = "subgraph-input"


@dataclass(frozen=True, slots=True)
class RunState:
    status: RunStatus
    reason: str | None = None
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class Phase:
    """One slot's place in the current pass: `active` (scheduled or started, under `key`),
    `waiting` (with its reason) or `done`."""

    phase: str
    reason: str | None = None
    key: str = ""


def status_of(events: list[Event], live: Container[str] | None = None) -> RunState:
    """The run's status, a pure fold over its events (SOLUTION-DESIGN 3.1, B-40, B-73). A
    `run_resumed` opens a new pass that keeps only the slots waiting on an answer. `live` holds the
    idempotency keys of the attempts this engine runs now; an attempt left open outside it belongs
    to an engine that died, so the run reads `interrupted` until a resume folds it. None means the
    caller cannot see the worker, and an open attempt reads `running`."""
    ended: RunState | None = None
    paused: RunState | None = None
    answered = False
    started = False
    slots: dict[tuple[JsonValue, ...], Phase] = {}
    for event in events:
        data = event.data
        slot = (data.get("node_id"), data.get("iteration", 0), data.get("partition"))
        match event.kind:
            case "run_resumed":
                ended = paused = None
                answered = data.get("reason") == "answer"
                slots = {s: p for s, p in slots.items() if p.reason in ("gate", "skipped")}
            case "run_finished":
                ended = RunState("passed")
            case "run_cancelled":
                ended = RunState("stopped", str(data.get("reason") or "operator"))
            case "gate_resolved" if data.get("answer") == "stop":
                ended = RunState("stopped", "operator")
            case "gate_resolved":
                answered = True
                if ended is not None and ended.status == "failed":
                    ended = None
                if data.get("answer") == "resume":
                    paused = None
                if data.get("answer") == "skip_node":
                    slots[slot] = Phase("done", "skipped")
                elif data.get("answer") in ("retry", "stronger_model"):
                    slots.pop(slot, None)
            case "run_paused":
                paused = RunState("waiting", str(data.get("reason")))
            case "ladder_step" if data.get("step") == "park" and data.get("scope") != "partition":
                ended = RunState("failed", "parked", str(data.get("reason")))
            case "ladder_step" if data.get("step") == "retry":
                slots[slot] = Phase("waiting", "retry")
            case "node_waiting":
                slots[slot] = Phase("waiting", str(data.get("reason")))
            case "node_scheduled" | "node_started":
                started |= event.kind == "node_started"
                attempt = data.get("attempt")
                key = attempt_key(event.run_id, data, attempt) if isinstance(attempt, int) else ""
                slots[slot] = Phase("active", key=key)
            case "node_finished" | "node_failed":
                slots[slot] = Phase("done")
            case _:
                pass
    if ended is not None:
        return ended
    if paused is not None:
        return paused
    active = [p for p in slots.values() if p.phase == "active"]
    if live is not None and any(p.key not in live for p in active):
        return RunState("interrupted", "the engine stopped with an attempt in flight")
    if active:
        return RunState("running")
    waits = sorted({str(p.reason) for p in slots.values() if p.phase == "waiting"})
    if waits:
        return RunState("waiting", " ".join(waits))
    if answered:
        return RunState("waiting", "answered")
    return RunState("running" if started else "queued")


def attempt_key(run_id: str, data: Mapping[str, JsonValue], attempt: int) -> str:
    iteration, partition = data.get("iteration"), data.get("partition")
    slot = Slot(
        str(data.get("node_id")),
        iteration if isinstance(iteration, int) else 0,
        partition if isinstance(partition, int) else None,
    )
    return idempotency_key(run_id, slot, attempt)


def live_attempts(engine: Engine) -> frozenset[str]:
    """The idempotency keys of every attempt this engine has in flight: those its runs hold,
    queued or started, and those its worker runs."""
    held = (c.idempotency_key for run in engine.live.values() for c in run.inflight.values())
    return frozenset((*held, *engine.worker.running))


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
    pins: JsonObject | None = None,
) -> tuple[Outcome, Stored]:
    """`pins` are the firing trigger's role and effort pins (B-60)."""
    run_id = run_id or new_run_id(ctx.clock.now())
    if subgraph is not None:
        bundle = induced(bundle, subgraph)
    root = bundle.write(ctx.home / "engine" / "runs" / run_id / "workflow")
    found = checked(root)
    if isinstance(found, list):
        codes = " ".join(sorted({p.code for p in found}))
        needs = [p.message for p in found if p.code == "needs_unmet"]
        raise Refused("not_runnable", "; ".join([f"the workflow does not run: {codes}", *needs]))
    try:
        outcome = await ctx.engine.start(
            root, found[1], mode=mode, inputs=inputs, run_id=run_id, fake=fake, pins=pins
        )
    except EngineRefused as refused:
        raise Refused("engine_refused", str(refused)) from refused
    await ctx.engine.settle()
    stored = summarize(ctx, outcome, item, object_id, mode, caller.principal)
    if mode == "live":
        if outcome.status == "passed" and subgraph is None and not fake:
            principal = f"run:{outcome.run_id}"
            ctx.library.link(object_id, "tested-by", stored.object_id, principal=principal)
        fire_after(ctx, outcome, item)
    return outcome, stored


def report(
    ctx: Context, outcome: Outcome, summary: Stored, content_hash: str, fields: JsonObject
) -> Stored:
    """Write the `test-report` of a test run bound to `content_hash`, with the run's status and
    reason over `fields`, and link the draft it names `tested-by` the run when the whole draft
    passed on real models."""
    principal = f"run:{outcome.run_id}"
    written: JsonObject = fields | {
        "run_id": outcome.run_id,
        "status": outcome.status,
        "reason": summary.fields.get("reason"),
    }
    stored = ctx.library.put_test_report(content_hash, written, principal=principal)
    whole = written.get("subgraph") is None and written.get("fake") is not True
    draft = written.get("draft_object_id")
    if outcome.status == "passed" and whole and isinstance(draft, str):
        ctx.library.link(draft, "tested-by", summary.object_id, principal=principal)
    return stored


def fire_after(ctx: Context, outcome: Outcome, item: str | None = None) -> None:
    """Fire every `after` trigger on a passed live run's workflow (AD-10). Without `item`, the
    workflow and the mode are read from the run's last summary."""
    if outcome.status != "passed":
        return
    if item is None:
        found = ctx.library.objects(outcome.run_id, "workflow-run")
        if not found or found[-1].fields.get("mode") != "live":
            return
        item = str(found[-1].fields.get("workflow_item"))
    with Reader.open(ctx.home) as reader:
        listed = triggers(reader.connection, "WHERE kind = 'after' AND enabled = 1")
    upstream: dict[str, JsonValue] = {
        "run_id": outcome.run_id,
        "workflow_item": item,
        "outputs": outcome.outputs,
    }
    for trigger in listed:
        if isinstance(trigger.spec, After) and trigger.spec.workflow_item == item:
            fire_now(ctx.engine.ledger, trigger.id, ctx.clock.now(), {"upstream": upstream})


def descendants(reader: Reader, run_id: str) -> list[str]:
    """Every run started under `run_id` by a subworkflow node, nearest first."""
    found: list[str] = []
    frontier = [run_id]
    while frontier:
        parent = frontier.pop(0)
        rows = reader.connection.execute(
            "SELECT run_id FROM events WHERE seq = 1 AND kind = 'run_created'"
            " AND json_extract(data, '$.parent_run_id') = ? ORDER BY at, run_id",
            (parent,),
        ).fetchall()
        children = [str(child) for (child,) in rows if child not in found]
        found += children
        frontier += children
    return found


def drop_wake(run_id: str) -> Operation[None]:
    def operation(txn: Transaction) -> None:
        txn.connection.execute("DELETE FROM wakes WHERE run_id = ?", (run_id,))

    return operation


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
    item = str(last.get("workflow_item"))
    stored = summarize(
        ctx, outcome, item, str(last.get("object_id")), mode, str(last.get("started_by"))
    )
    reports = [
        r
        for r in ctx.library.objects(item, "test-report")
        if r.fields.get("run_id") == outcome.run_id
    ]
    if reports:
        earlier = reports[-1].fields
        kept = {k: v for k, v in earlier.items() if k not in ("content_hash", "status", "reason")}
        report(ctx, outcome, stored, str(earlier.get("content_hash")), kept)
    return stored


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
        [view] = self.views([run_id])
        return view

    def views(self, run_ids: list[str]) -> list[RunView]:
        """Each run's view, its status folded from its events now, all read through one reader."""
        if not ledger_path(self.ctx.home).exists():
            raise Refused("unknown_run", f"no run {run_ids[0] if run_ids else ''}")
        live = live_attempts(self.ctx.engine)
        with Reader.open(self.ctx.home) as reader:
            logs = [(run_id, reader.events(run_id)) for run_id in run_ids]
        found: list[RunView] = []
        for run_id, events in logs:
            if not events or events[0].kind != "run_created":
                raise Refused("unknown_run", f"no run {run_id}")
            state = status_of(events, live)
            mode: Mode = "live" if events[0].data.get("mode") == "live" else "test"
            summaries = self.ctx.library.objects(run_id, "workflow-run")
            object_id = summaries[-1].fields.get("object_id") if summaries else None
            found.append(
                RunView(
                    run_id,
                    mode,
                    state.status,
                    state.reason,
                    state.detail,
                    object_id if isinstance(object_id, str) else None,
                )
            )
        return found

    def cancel(self, run_id: str, reason: str = "operator") -> list[str]:
        """End a run and every child run under it `stopped`, whether they run here, wait or
        parked. Returns the run ids that ended."""
        if self.get(run_id).status in ("passed", "stopped"):
            raise Refused("cancel_refused", f"run {run_id} already ended")
        engine = self.ctx.engine
        with Reader.open(self.ctx.home) as reader:
            tree = [run_id, *descendants(reader, run_id)]
            ended = {rid: status_of(reader.events(rid)).status for rid in tree}
        stopped = engine.cancel(run_id, reason)
        for rid in tree:
            engine.ledger.write(drop_wake(rid))
            if rid in stopped or ended[rid] in ("passed", "stopped"):
                continue
            engine.ledger.append(rid, "run_cancelled", {"reason": reason}, at=self.ctx.at())
            stopped.append(rid)
        return stopped

    def list(self, workflow_item: str, object_id: str | None = None) -> list[RunSummary]:
        """The runs' Library summaries, each with its status and reason read from the ledger now,
        so a run resumed since its summary shows where it is."""
        listed = self.ctx.library.list_runs(workflow_item, object_id)
        live = live_attempts(self.ctx.engine)
        with Reader.open(self.ctx.home) as reader:
            states = [status_of(reader.events(found.run_id), live) for found in listed]
        return [
            replace(found, status=state.status, reason=state.reason)
            for found, state in zip(listed, states, strict=True)
        ]
