"""QMX background runs, with owned checkpoints and the control service's cancellation."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from langchain_core.tools import BaseTool, tool
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from qmx_control.models import Document
from qmx_control.service import ControlService, SessionInput

from qmx_agents.guards import RunJournal

if TYPE_CHECKING:
    from qmx_agents.spec import BuildContext


class BackgroundTasks:
    def __init__(self, paths: list[Path], ctx: BuildContext) -> None:
        from qmx_agents.spec import load_spec  # noqa: PLC0415

        self.ctx = ctx
        self.service = cast(ControlService, ctx.control)
        self.specs = {spec.name: spec for spec in map(load_spec, paths)}
        self.running: dict[str, asyncio.Task[None]] = {}

    def tools(self) -> list[BaseTool]:
        @tool
        async def start_task(name: str, description: str) -> Document:
            """Start an allowed background agent; return its run and child session references."""
            if name not in self.specs:
                raise ValueError(f"Choose an allowed background task: {', '.join(self.specs)}")
            run_id = uuid4().hex
            session = self.service.sessions_create(
                SessionInput(title=description[:200], parent_id=self.ctx.run.session_id)
            )
            loop = asyncio.get_running_loop()
            task = asyncio.create_task(self._run(run_id, name, description, str(session["id"])))
            self.running[run_id] = task

            def finished(completed: asyncio.Task[None]) -> None:
                # Cancellation can arrive before the coroutine gets its first turn.
                if completed.cancelled():
                    self.service.record_work("runs", run_id, {"status": "cancelled"})

            task.add_done_callback(finished)

            def cancel_in_loop() -> None:
                if task.done():
                    if self.service.runs_get(run_id).get("status") == "needs_you":
                        with RunJournal(
                            self.service.home / "runs" / run_id / "journal.jsonl", run_id
                        ) as journal:
                            self._finish(run_id, "cancelled", journal)
                else:
                    task.cancel()

            def cancel() -> None:
                loop.call_soon_threadsafe(cancel_in_loop)

            return self.service.record_work(
                "runs",
                run_id,
                {"name": name, "session_id": session["id"], "status": "running"},
                cancel=cancel,
            )

        @tool
        def check_task(run_id: str) -> Document:
            """Read the status and artifact references of a task started by this agent."""
            self._owned(run_id)
            return self.service.runs_get(run_id)

        @tool
        def cancel_task(run_id: str) -> Document:
            """Request cancellation through the QMX run owner."""
            self._owned(run_id)
            return self.service.runs_cancel(run_id)

        @tool
        def list_tasks() -> list[Document]:
            """List this agent's background runs, including completed runs."""
            return [self.service.runs_get(run_id) for run_id in self.running]

        return [start_task, check_task, cancel_task, list_tasks]

    def _owned(self, run_id: str) -> None:
        if run_id not in self.running:
            raise ValueError("This agent did not start that task.")

    def _finish(
        self, run_id: str, status: str, journal: RunJournal | None, *, error: str | None = None
    ) -> None:
        # Journal replay is authoritative over the service's cached run status.
        if journal is not None:
            journal.append("run_end", {"status": status})
        data: Document = {"status": status}
        if error is not None:
            data["error"] = error
        self.service.record_work("runs", run_id, data)

    async def _run(self, run_id: str, name: str, prompt: str, session_id: str) -> None:
        from qmx_agents.copilot import stream_turn  # noqa: PLC0415
        from qmx_agents.spec import build_agent  # noqa: PLC0415

        child = replace(
            self.ctx,
            run=replace(
                self.ctx.run,
                session_id=session_id,
                task_id=run_id,
                subagent=self.specs[name].model,
                workflow_id=self.ctx.run.workflow_id or self.ctx.run.session_id or run_id,
            ),
            memory=None,
            journal=None,
            memory_role="scheduled",
            memory_resources=[],
            background_resources=[],
            journal_resources=[],
        )
        path = self.service.home / "copilot" / "tasks" / run_id / "threads.db"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            child.journal = RunJournal(
                self.service.home / "runs" / run_id / "journal.jsonl", run_id
            )
            child.journal_resources.append(child.journal)
            async with AsyncSqliteSaver.from_conn_string(str(path)) as saver:
                child.checkpointer = saver
                graph = await build_agent(self.specs[name], child)
                await stream_turn(graph, self.service, session_id, prompt, context=child.run)
                state = await graph.aget_state({"configurable": {"thread_id": session_id}})
                status = "needs_you" if state.next else "completed"
                self._finish(run_id, status, child.journal)
        except asyncio.CancelledError:
            self._finish(run_id, "cancelled", child.journal)
            raise
        except Exception as error:
            self._finish(run_id, "failed", child.journal, error=type(error).__name__)
        finally:
            await child.close_memory()

    async def close(self) -> None:
        for task in self.running.values():
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.running.values(), return_exceptions=True)
