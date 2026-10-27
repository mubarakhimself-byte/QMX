"""Workflow builders and planted executors shared by the fan-out, join, loop and wait tests, and
folder-backed runs for the runner tests. Every run goes through the real `Engine` and its one
ledger writer, with planted executors through its `executors=` seam."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any

from pydantic import JsonValue

from qmx_engine.definition.model import Workflow
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok, Waiting
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.runner import Engine, Outcome
from qmx_engine.settings import DEFAULTS
from qmx_engine.workers.local import AnyExecutor

NOW = "2026-10-17T09:00:00+00:00"
LATER = "2026-10-17T10:00:00+00:00"
ONE_TRY: Mapping[str, object] = {**DEFAULTS, "retry.max_tries": 1, "retry.backoff": (0,)}
"""Settings under which a failed attempt is not retried: it walks the rest of the ladder at once."""
POLL_S = 0.01


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
    through). A slot in `failing` fails once. A `(node, partition)` in `slow` stays in flight
    until the test `release`s it, and one in `waiting` ends waiting an hour on. `tokens` are
    reported on each finished attempt. `calls` lists every slot it ran."""

    def __init__(
        self,
        fn: Callable[[NodeJob, JsonValue], JsonValue] = lambda _, value: value,
        *,
        failing: set[Planted] | None = None,
        slow: set[tuple[str, int | None]] | None = None,
        waiting: set[tuple[str, int | None]] | None = None,
        tokens: int = 0,
        only: str | None = None,
    ) -> None:
        self.fn = fn
        self.only = only
        self.failing: set[Planted] = set(failing or ())
        self.slow = set(slow or ())
        self.waiting = set(waiting or ())
        self.tokens = tokens
        self.calls: list[Planted] = []
        self.gates: dict[tuple[str, int | None], asyncio.Event] = {}
        self.released: dict[tuple[str, int | None], JsonValue] = {}

    async def run(self, job: NodeJob) -> NodeResult:
        slot: Planted = (job.node_id, job.iteration, job.partition)
        self.calls.append(slot)
        if slot in self.failing:
            self.failing.discard(slot)
            return Failed("boom", "planted failure", "planted", retryable=True)
        key = (job.node_id, job.partition)
        if key in self.waiting:
            return Waiting("wait", "2026-10-17T10:00:00+00:00")
        if key in self.slow:
            await self.gates.setdefault(key, asyncio.Event()).wait()
            return Ok({"main": self.released[key]})
        ports = job.inputs if isinstance(job.inputs, dict) else {}
        value = ports.get("in")
        span: dict[str, JsonValue] = {"tokens": {"out": self.tokens}} if self.tokens else {}
        out = self.fn(job, value) if self.only in (None, job.node_id) else value
        return Ok({"main": out}, span=span)

    def release(self, node_id: str, partition: int | None, value: JsonValue) -> None:
        """End a slow slot's attempt with `value` on `main`."""
        self.released[(node_id, partition)] = value
        self.gates.setdefault((node_id, partition), asyncio.Event()).set()


class Flow:
    """One run of `definition` on the real `Engine`, on a wall clock the test moves. The folder,
    the home and the ledger are the test's own."""

    def __init__(
        self,
        tmp: Path,
        definition: Workflow,
        executors: Mapping[str, AnyExecutor],
        *,
        settings: Mapping[str, object] = ONE_TRY,
        run_id: str = "run-1",
        now: str = NOW,
    ) -> None:
        self.home = tmp / run_id / "home"
        self.root = tmp / run_id / "workflow"
        self.definition = definition
        self.executors = executors
        self.settings = settings
        self.run_id = run_id
        self.wall = datetime.fromisoformat(now)
        self.write(definition)

    def write(self, definition: Workflow) -> None:
        """The run's folder now holds `definition`: an edit, when the run already started."""
        self.definition = definition
        self.root.mkdir(parents=True, exist_ok=True)
        document = definition.model_dump(mode="json", by_alias=True, exclude_none=True)
        (self.root / "definition.json").write_text(json.dumps(document), encoding="utf-8")

    def drive[T](self, scenario: Callable[[Engine], Awaitable[T]]) -> T:
        """Run `scenario` on an engine over this flow's home, and wait for any child it left."""

        async def go() -> T:
            with (
                Ledger.open(self.home) as ledger,
                InboxTable.open(self.home) as inbox,
                LibraryFake.open(self.home) as library,
            ):
                engine = Engine(
                    self.home,
                    ledger,
                    library=library,
                    settings=self.settings,
                    wall=lambda: self.wall,
                    executors=self.executors,
                    watch_every=POLL_S,
                    inbox=inbox,
                )
                found = await scenario(engine)
                await engine.settle()
                return found

        return asyncio.run(go())

    async def started(self, engine: Engine, inputs: JsonValue) -> Outcome:
        """The run started from its folder, as a resume reads it."""
        found = checked(self.root)
        assert not isinstance(found, list), found
        return await engine.start(
            self.root, found[1], mode="test", inputs=inputs, run_id=self.run_id
        )

    def start(self, inputs: JsonValue) -> Outcome:
        return self.drive(lambda engine: self.started(engine, inputs))

    def resume(self, now: str | None = None, *, reason: str = "operator") -> Outcome:
        if now is not None:
            self.wall = datetime.fromisoformat(now)
        return self.drive(lambda engine: engine.resume(self.run_id, reason=reason))

    def tick(self, now: str) -> Outcome:
        """The ticker wakes the run at `now`."""
        return self.resume(now, reason="wake")

    def receive(self, event: str) -> Outcome:
        with Ledger.open(self.home) as ledger:
            ledger.append(self.run_id, "event_received", {"event": event}, at=self.wall.isoformat())
        return self.resume(reason="wake")

    @property
    def events(self) -> list[Event]:
        with Reader.open(self.home) as reader:
            return reader.events(self.run_id)

    async def seen(self, kind: str, node_id: str, partition: int | None = None) -> None:
        """Wait until the ledger holds `kind` for the slot."""
        while not [
            e
            for e in self.events
            if e.kind == kind
            and e.data.get("node_id") == node_id
            and e.data.get("partition") == partition
        ]:
            await asyncio.sleep(POLL_S)


def of(events: list[Event], kind: str, node_id: str) -> list[dict[str, JsonValue]]:
    return [e.data for e in events if e.kind == kind and e.data.get("node_id") == node_id]


def started_slots(events: list[Event], node_id: str) -> list[tuple[JsonValue, JsonValue]]:
    """`(partition or iteration, attempt)` of each attempt of the node that started."""
    return [
        (e["partition"] if e["partition"] is not None else e["iteration"], e["attempt"])
        for e in of(events, "node_started", node_id)
    ]


def folder(
    root: Path,
    nodes: list[dict[str, Any]],
    connections: dict[str, dict[str, Any]],
    scripts: Mapping[str, str],
    **settings: JsonValue,
) -> Path:
    """A workflow folder with `scripts/<name>.py` for each script, ready for the runner."""
    root.mkdir(parents=True, exist_ok=True)
    document = workflow(nodes, connections).model_dump(mode="json", by_alias=True)
    document["settings"] = settings
    (root / "definition.json").write_text(json.dumps(document), encoding="utf-8")
    (root / "scripts").mkdir(exist_ok=True)
    for name, text in scripts.items():
        (root / "scripts" / f"{name}.py").write_text(dedent(text), encoding="utf-8")
    return root


def run_folder(
    root: Path, home: Path, inputs: JsonValue = None, **settings: object
) -> tuple[Outcome, list[Event]]:
    """Start one run of `root` on `home`, wait for it and any child it left running, and return
    its outcome with its events."""
    found = checked(root)
    assert not isinstance(found, list), found

    async def go() -> Outcome:
        with Ledger.open(home) as ledger, LibraryFake.open(home) as library:
            engine = Engine(home, ledger, settings={**DEFAULTS, **settings}, library=library)
            outcome = await engine.start(root, found[1], mode="test", inputs=inputs)
            await engine.settle()
            return outcome

    outcome = asyncio.run(go())
    with Reader.open(home) as reader:
        return outcome, reader.events(outcome.run_id)


def events_of(home: Path, run_id: str) -> list[Event]:
    with Reader.open(home) as reader:
        return reader.events(run_id)


def kinds(events: list[Event], node_id: str) -> list[str]:
    return [e.kind for e in events if e.data.get("node_id") == node_id]


CHAIN = Path(__file__).resolve().parent / "fixtures" / "workflows" / "script-chain"
CHAIN_TOTAL = {"total": {"main": {"total": 20}}}


def edited(bundle: Bundle, script: str, text: str) -> Bundle:
    """The bundle with one script's text replaced: a real edit, so a new content hash."""
    return Bundle(bundle.definition, {**bundle.files, script: dedent(text).encode()})
