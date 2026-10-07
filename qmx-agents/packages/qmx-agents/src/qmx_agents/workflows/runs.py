"""SQLite-backed workflow runs; cancellation stops at checkpoint boundaries."""

from __future__ import annotations

import asyncio
from contextlib import aclosing
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiosqlite
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command

from qmx_agents.workflows.compiler import Bindings, WorkflowState, compile
from qmx_agents.workflows.models import WorkflowSpec


class WorkflowRuns:
    """Own this async context in an app volume or a standalone workflow volume."""

    def __init__(self, spec: WorkflowSpec, database: Path, *, bindings: Bindings | None = None):
        self.spec = spec
        self.database = database
        self.bindings = bindings
        self.active: dict[str, asyncio.Event] = {}
        self.lock = asyncio.Lock()
        self.connection: aiosqlite.Connection | None = None
        self.graph: Any = None

    async def __aenter__(self) -> WorkflowRuns:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.connection = await aiosqlite.connect(self.database)
        saver = AsyncSqliteSaver(
            self.connection, serde=JsonPlusSerializer(allowed_msgpack_modules=None)
        )
        self.graph = compile(self.spec, saver, bindings=self.bindings)
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self.active:
            raise RuntimeError(
                "Wait for active workflow runs before closing their checkpoint database"
            )
        if self.connection is not None:
            await self.connection.close()
        self.graph = None

    def config(self, run_id: str) -> RunnableConfig:
        if self.graph is None:
            raise RuntimeError("Use WorkflowRuns inside async with")
        return {"configurable": {"thread_id": f"{self.spec.name}:{run_id}"}}

    async def start(self, inputs: dict[str, Any], *, run_id: str | None = None) -> dict[str, Any]:
        run_id = run_id or str(uuid4())
        async with self.lock:
            snapshot = await self.graph.aget_state(self.config(run_id))
            if snapshot.values or run_id in self.active:
                raise ValueError("run_id already exists; use a new ID or resume a paused run")
            self.active[run_id] = asyncio.Event()
        return await self._drive(run_id, {"inputs": inputs, "phase": "running"})

    async def resume(self, run_id: str, decision: Any) -> dict[str, Any]:
        async with self.lock:
            status = await self.status(run_id)
            if status["status"] != "paused" or run_id in self.active:
                raise ValueError("Only a paused human_gate run can resume")
            self.active[run_id] = asyncio.Event()
        return await self._drive(run_id, Command(resume=decision))

    async def _drive(self, run_id: str, value: WorkflowState | Command[Any]) -> dict[str, Any]:
        config = self.config(run_id)
        try:
            async with aclosing(self.graph.astream(value, config, stream_mode="updates")) as stream:
                async for _ in stream:
                    if self.active[run_id].is_set():
                        break
            if self.active[run_id].is_set():
                await self.graph.aupdate_state(config, {"phase": "cancelled"}, as_node="__finish__")
        finally:
            self.active.pop(run_id, None)
        return await self.status(run_id)

    async def cancel(self, run_id: str) -> dict[str, Any]:
        async with self.lock:
            status = await self.status(run_id)
            if run_id in self.active:
                self.active[run_id].set()
                return {**status, "status": "cancelling"}
            if status["status"] not in {"completed", "cancelled", "missing"}:
                await self.graph.aupdate_state(
                    self.config(run_id), {"phase": "cancelled"}, as_node="__finish__"
                )
        return await self.status(run_id)

    async def status(self, run_id: str) -> dict[str, Any]:
        snapshot = await self.graph.aget_state(self.config(run_id))
        values = snapshot.values
        errors = [str(task.error) for task in snapshot.tasks if task.error]
        gates = [item.value for task in snapshot.tasks for item in task.interrupts]
        if not values:
            phase = "running" if run_id in self.active else "missing"
        elif values.get("phase") == "cancelled":
            phase = "cancelled"
        elif errors:
            phase = "failed"
        elif gates:
            phase = "paused"
        elif run_id in self.active:
            phase = "running"
        elif values.get("phase") == "completed" and not snapshot.next:
            phase = "completed"
        else:
            phase = "interrupted"
        return {
            "run_id": run_id,
            "status": phase,
            "next": list(snapshot.next),
            "gates": gates,
            "errors": errors,
            "result": values.get("structured_response") if values else None,
        }
