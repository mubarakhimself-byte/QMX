"""Runs on the real runner and ledger with planted in-process executors, for the ladder, inbox and
watchdog tests. A workflow may hold `llm` or `agent` nodes, which validation still refuses until
their executors land, so the run is started from the parsed definition, not from `checked`."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from flows import workflow

from qmx_engine.definition.model import Workflow
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.inbox_table import InboxTable, inbox_path
from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok
from qmx_engine.ports.inbox import Item
from qmx_engine.runner import Engine, Outcome
from qmx_engine.settings import DEFAULTS

T0 = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)

type Answer = NodeResult | Callable[[NodeJob], NodeResult]


def fails(message: str, *, code: str = "boom", retryable: bool = True) -> Failed:
    return Failed(code, message, signature(code, message), retryable)


OK = Ok({"main": "done"})


class Planted:
    """Answers attempt n with `answers[n - 1]`, the last one repeating, and keeps every job."""

    def __init__(self, *answers: Answer) -> None:
        self.answers = answers
        self.jobs: list[NodeJob] = []

    def run(self, job: NodeJob) -> NodeResult:
        self.jobs.append(job)
        answer = self.answers[min(len(self.jobs), len(self.answers)) - 1]
        return answer(job) if callable(answer) else answer


class Clock:
    def __init__(self, now: datetime = T0) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def move(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


@dataclass
class Flow:
    """A workflow folder on disk and its parsed definition."""

    root: Path
    definition: Workflow
    home: Path
    engine_args: dict[str, Any] = field(default_factory=dict[str, Any])

    def engine(self, ledger: Ledger, settings: Mapping[str, object] | None = None) -> Engine:
        return Engine(
            self.home, ledger, settings={**DEFAULTS, **(settings or {})}, **self.engine_args
        )

    def start(self, settings: Mapping[str, object] | None = None) -> Outcome:
        async def go() -> Outcome:
            with Ledger.open(self.home) as ledger:
                engine = self.engine(ledger, settings)
                return await engine.start(self.root, self.definition, mode="test", inputs=None)

        return asyncio.run(go())

    def resume(self, run_id: str) -> Outcome:
        async def go() -> Outcome:
            with Ledger.open(self.home) as ledger:
                return await self.engine(ledger).resume(run_id)

        return asyncio.run(go())

    def events(self, run_id: str) -> list[Event]:
        with Reader.open(self.home) as reader:
            return reader.events(run_id)

    def items(self) -> list[Item]:
        if not inbox_path(self.home).exists():
            return []
        with InboxTable.open(self.home) as inbox:
            return inbox.list_items(open_only=False)


def flow(
    tmp: Path,
    nodes: list[dict[str, Any]],
    connections: dict[str, dict[str, Any]],
    *,
    runaway: dict[str, Any] | None = None,
    **engine_args: Any,
) -> Flow:
    root = tmp / "wf"
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    for node in nodes:
        script = node.get("parameters", {}).get("script")
        if script:
            (root / script).write_text("print(1)\n", encoding="utf-8")
    document = workflow(nodes, connections).model_dump(mode="json", by_alias=True)
    if runaway is not None:
        document["settings"] = {"runaway": runaway}
    (root / "definition.json").write_text(json.dumps(document), encoding="utf-8")
    return Flow(root, Workflow.model_validate(document), tmp / "home", engine_args)


def steps(events: list[Event]) -> list[str]:
    return [str(e.data["step"]) for e in events if e.kind == "ladder_step"]


def of_kind(events: list[Event], kind: str) -> list[dict[str, Any]]:
    return [e.data for e in events if e.kind == kind]
