"""The in-process worker on the PC (SOLUTION-DESIGN 5.2, AD-20).

`run` carries out one attempt: it waits for one of `placement.pc.concurrency` slots, writes
`node_started`, snapshots the write zone for a `reversible` node, runs the executor while a
`heartbeat` goes out every 10 s, and returns the result. The runner writes the ending event, so a
result lands in the ledger before the core sees it. A `subworkflow` attempt takes no slot: it
only waits on its child, whose own nodes take slots, so a parent can never starve its child.
`cancel` stops an attempt, and the executor kills its process tree on the way out.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Final, cast

from qmx_engine.definition.registry import REGISTRY
from qmx_engine.ledger.events import EventKind, JsonObject
from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import AsyncExecutor, Executor, Failed, NodeJob, NodeResult, Ok
from qmx_engine.watchdog import STALLED, STALLED_MESSAGE
from qmx_engine.workers import effects

HEARTBEAT_SECONDS: Final = 10.0
UNSLOTTED: Final = frozenset({"subworkflow"})
RESOLVED: Final = ("role", "profile", "model", "effort", "candidate", "test_only", "unresolved")
"""What `node_started` records of the candidate the runner resolved, so the span names it."""

type Emit = Callable[[EventKind, JsonObject], None]
type AnyExecutor = Executor | AsyncExecutor


def attempt_keys(job: NodeJob) -> JsonObject:
    return {
        "node_id": job.node_id,
        "iteration": job.iteration,
        "partition": job.partition,
        "attempt": job.attempt,
    }


class LocalWorker:
    def __init__(self, *, concurrency: int, heartbeat_seconds: float = HEARTBEAT_SECONDS) -> None:
        self.slots = asyncio.Semaphore(concurrency)
        self.heartbeat_seconds = heartbeat_seconds
        self.running: dict[str, asyncio.Task[object]] = {}
        self.cancelled: dict[str, Failed] = {}
        """Key to the failure a cancelled attempt ends with."""

    async def run(self, job: NodeJob, executor: AnyExecutor, emit: Emit) -> NodeResult:
        task = asyncio.current_task()
        if task is not None:
            self.running[job.idempotency_key] = cast(asyncio.Task[object], task)
        try:
            kind = REGISTRY.kind(str(job.node_definition.get("type")))
            if kind is not None and kind.name in UNSLOTTED:
                return await self.attempt(job, executor, emit)
            async with self.slots:
                return await self.attempt(job, executor, emit)
        except asyncio.CancelledError:
            failure = self.cancelled.pop(job.idempotency_key, None)
            if failure is None:
                raise
            return replace(failure, effect_state="before")
        finally:
            self.running.pop(job.idempotency_key, None)

    def cancel(self, idempotency_key: str, *, stalled: bool = False) -> bool:
        """Stop the attempt with this key; False when it is not running here. A stalled attempt
        fails `stalled` and retryable, so the ladder takes it (SOLUTION-DESIGN 10.3)."""
        task = self.running.get(idempotency_key)
        if task is None:
            return False
        if stalled:
            failure = Failed(STALLED, STALLED_MESSAGE, signature(STALLED, STALLED_MESSAGE), True)
        else:
            message = "the attempt was cancelled"
            failure = Failed("cancelled", message, signature("cancelled", message), False)
        self.cancelled[idempotency_key] = replace(failure, effect_state="unknown")
        task.cancel()
        return True

    async def attempt(self, job: NodeJob, executor: AnyExecutor, emit: Emit) -> NodeResult:
        effect = effects.effect_of(job.node_definition)
        resolved = job.resolved_model or {}
        emit(
            "node_started",
            attempt_keys(job)
            | {key: resolved[key] for key in RESOLVED if key in resolved}
            | {"idempotency_key": job.idempotency_key, "effect": effect, "placement": "pc"},
        )
        zone = Path(job.workspace) if job.workspace is not None else None
        if zone is not None:
            zone.mkdir(parents=True, exist_ok=True)
            if effect == "reversible":
                effects.before(zone, job)
        beat = asyncio.create_task(self.beat(job, emit))
        try:
            outcome = executor.run(job)
            result = await outcome if inspect.isawaitable(outcome) else outcome
        except asyncio.CancelledError:
            failure = self.cancelled.pop(job.idempotency_key, None)
            if failure is None:
                raise
            result = failure
        except Exception as error:
            message = f"the executor raised {type(error).__name__}"
            result = Failed("executor_error", message, signature("executor_error", message), False)
        finally:
            beat.cancel()
        if zone is not None and effect == "reversible":
            effects.after(zone, job, ok=isinstance(result, Ok))
        return result

    async def beat(self, job: NodeJob, emit: Emit) -> None:
        while True:
            await asyncio.sleep(self.heartbeat_seconds)
            emit("heartbeat", attempt_keys(job) | {"note": "running"})
