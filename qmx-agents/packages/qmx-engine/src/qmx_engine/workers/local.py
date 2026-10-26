"""The in-process worker on the PC (SOLUTION-DESIGN 5.2, AD-20).

The runner reaches every worker through `WorkerPort`: `run(job, emit)` and `cancel(key, reason)`.
No executor crosses the port (L-42): this local adapter holds each run's executor table, which the
runner hands it with `serve` while the run is driven, and a remote adapter resolves executors on
its own side.

`run` carries out one attempt: it takes the capacity its kind uses from the host's table
(`admission.Capacity`, AD-58), waiting by priority then age, writes `node_started`, opens the
attempt's overlay for a script-family node, runs the executor while a `heartbeat` goes out every
10 s, and returns the result. An `ok` attempt commits its declared
outputs into the run's shared zone and records `zone_committed`; any other ending deletes the
overlay, which is the reversible undo (AD-8, AD-51). The runner writes the ending event, so a
result lands in the ledger before the core sees it. Pure kinds take no slot, so a rule or join
never waits behind a script; a `subworkflow` attempt only waits on its child, whose own nodes take
slots, so a parent can never starve its child.
`cancel` stops an attempt, and the executor kills its process tree on the way out.

Every script process sits in the engine's Job object, which kills it when the engine dies
(AD-24 lifetime, B-31). Its process id is also kept under the run's zone, so a resume stops a
script that escaped the Job object.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import json
import os
import platform
import signal
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Final, Literal, Protocol, cast

import psutil

from qmx_engine.admission import Capacity
from qmx_engine.definition.model import Outputs
from qmx_engine.definition.registry import REGISTRY
from qmx_engine.ledger.events import EventKind, JsonObject
from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import (
    AsyncExecutor,
    Executor,
    Failed,
    NodeJob,
    NodeResult,
    Ok,
    where_ran,
)
from qmx_engine.settings import DEFAULTS
from qmx_engine.watchdog import STALLED, STALLED_MESSAGE
from qmx_engine.workers import effects
from qmx_engine.workers.zones import Overlay, RunZone, ZoneError, slot_name

HEARTBEAT_SECONDS: Final = 10.0
WRITERS: Final = frozenset({"script", "grader", "monitor"})
"""The kinds whose attempt runs a script and so gets an overlay."""
CHILD_PROCESS: Final = frozenset({"script", "grader", "monitor", "rlm"})
"""The heavy kinds: an attempt of one does its work in a child process of this host, never in the
host's own address space, so a kernel out-of-memory kill takes the attempt and `qmx_host` keeps
answering (F39, P-OOM). The script family's `python -I` child is that process (AD-24); an `rlm`
kernel, extraction and a big market-data read join this set as their executors ship."""
RESOLVED: Final = ("role", "profile", "model", "effort", "candidate", "test_only", "unresolved")
"""What `node_started` records of the candidate the runner resolved, so the span names it."""

type Emit = Callable[[EventKind, JsonObject], None]
type AnyExecutor = Executor | AsyncExecutor
type CancelReason = Literal["stop", "stalled"]


class WorkerPort(Protocol):
    """Where an attempt runs (AD-20). `emit` is the sink for the attempt's `node_started`, `log`,
    `heartbeat`, `tool_called` and commit events; the result is its ending."""

    async def run(self, job: NodeJob, emit: Emit) -> NodeResult: ...

    def cancel(self, idempotency_key: str, reason: CancelReason = "stop") -> bool: ...


def kill_tree(pid: int) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],  # noqa: S607
            capture_output=True,
            check=False,
        )
    else:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(pid, signal.SIGKILL)


if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    KILL_ON_JOB_CLOSE: Final = 0x2000
    EXTENDED_LIMITS: Final = 9
    SET_QUOTA_AND_TERMINATE: Final = 0x0101

    class _BasicLimits(ctypes.Structure):
        _fields_ = (
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        )

    class _ExtendedLimits(ctypes.Structure):
        _fields_ = (
            ("BasicLimitInformation", _BasicLimits),
            ("IoInfo", ctypes.c_uint64 * 6),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        )

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    _kernel32.CreateJobObjectW.argtypes = (wintypes.LPVOID, wintypes.LPCWSTR)
    _kernel32.SetInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _kernel32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    _kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _job: list[int] = []
    """The engine's one Job object handle. It is never closed: the OS closes it when the engine
    dies, and with `KILL_ON_JOB_CLOSE` that close kills every process in it."""

    def contain(pid: int) -> bool:
        """Put the process in the engine's Job object; the processes it starts follow it in."""
        if not _job:
            handle = _kernel32.CreateJobObjectW(None, None)
            if not handle:
                return False
            limits = _ExtendedLimits()
            limits.BasicLimitInformation.LimitFlags = KILL_ON_JOB_CLOSE
            if not _kernel32.SetInformationJobObject(
                handle, EXTENDED_LIMITS, ctypes.byref(limits), ctypes.sizeof(limits)
            ):
                _kernel32.CloseHandle(handle)
                return False
            _job.append(handle)
        process = _kernel32.OpenProcess(SET_QUOTA_AND_TERMINATE, False, pid)
        if not process:
            return False
        try:
            return bool(_kernel32.AssignProcessToJobObject(_job[0], process))
        finally:
            _kernel32.CloseHandle(process)

else:

    def contain(pid: int) -> bool:
        """No Job object off Windows; the pid record and the resume sweep stand in for it."""
        return False


def record(zone: RunZone, job: NodeJob, pid: int) -> None:
    """Keep the script's id and start time under the run's zone, so a resume can stop it."""
    try:
        created = psutil.Process(pid).create_time()
    except psutil.Error:
        return
    zone.pids.mkdir(parents=True, exist_ok=True)
    (zone.pids / f"{slot_name(job)}.json").write_text(
        json.dumps({"pid": pid, "created": created}), encoding="utf-8"
    )


def forget(zone: RunZone, job: NodeJob) -> None:
    (zone.pids / f"{slot_name(job)}.json").unlink(missing_ok=True)


def sweep(zone: RunZone) -> list[int]:
    """Stop every recorded script still alive with the start time it was recorded with, and
    forget every record. Returns the ids it stopped."""
    stopped: list[int] = []
    if not zone.pids.is_dir():
        return stopped
    for path in sorted(zone.pids.glob("*.json")):
        found = json.loads(path.read_text(encoding="utf-8"))
        pid, created = int(found["pid"]), float(found["created"])
        try:
            alive = psutil.Process(pid).create_time() == created
        except psutil.Error:
            alive = False
        if alive:
            kill_tree(pid)
            stopped.append(pid)
        path.unlink()
    return stopped


def declared_outputs(job: NodeJob) -> Outputs:
    found = job.node_definition.get("outputs")
    return Outputs.model_validate(found) if isinstance(found, dict) else Outputs()


def attempt_keys(job: NodeJob) -> JsonObject:
    return {
        "node_id": job.node_id,
        "iteration": job.iteration,
        "partition": job.partition,
        "attempt": job.attempt,
    }


class LocalWorker:
    def __init__(
        self, capacity: Capacity | None = None, *, heartbeat_seconds: float = HEARTBEAT_SECONDS
    ) -> None:
        self.capacity = capacity or Capacity.of(DEFAULTS)
        self.heartbeat_seconds = heartbeat_seconds
        self.running: dict[str, asyncio.Task[object]] = {}
        self.cancelled: dict[str, Failed] = {}
        """Key to the failure a cancelled attempt ends with."""
        self.tables: dict[str, Mapping[str, AnyExecutor]] = {}
        """Run id to the executor of each kind its attempts run on."""

    def serve(self, run_id: str, executors: Mapping[str, AnyExecutor]) -> None:
        self.tables[run_id] = executors

    def release(self, run_id: str) -> None:
        self.tables.pop(run_id, None)

    async def run(self, job: NodeJob, emit: Emit) -> NodeResult:
        kind = REGISTRY.kind(str(job.node_definition.get("type")))
        name = kind.name if kind is not None else ""
        executor = self.tables.get(job.run_id, {}).get(name)
        if executor is None:
            message = f"no executor serves kind {name or 'unknown'} for this run"
            return Failed(
                "executor_missing", message, signature("executor_missing", message), False
            )
        refused = self.capacity.admit(job.idempotency_key, job.node_definition)
        if refused is not None:
            return Failed("memory", refused, signature("memory", refused), True)
        task = asyncio.current_task()
        if task is not None:
            self.running[job.idempotency_key] = cast(asyncio.Task[object], task)
        try:
            async with self.capacity.held(name, job.placement, job.priority):
                return await self.attempt(job, executor, emit)
        except asyncio.CancelledError:
            failure = self.cancelled.pop(job.idempotency_key, None)
            if failure is None:
                raise
            return replace(failure, effect_state="before")
        finally:
            self.running.pop(job.idempotency_key, None)
            self.capacity.memory.give(job.idempotency_key)

    def cancel(self, idempotency_key: str, reason: CancelReason = "stop") -> bool:
        """Stop the attempt with this key; False when it is not running here. A stalled attempt
        fails `stalled` and retryable, so the ladder takes it (SOLUTION-DESIGN 10.3). A stop's
        outcome is unknown, and the runner never retries it (B-37)."""
        task = self.running.get(idempotency_key)
        if task is None:
            return False
        if reason == "stalled":
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
        kind = REGISTRY.kind(str(job.node_definition.get("type")))
        name = kind.name if kind is not None else ""
        emit(
            "node_started",
            attempt_keys(job)
            | {key: resolved[key] for key in RESOLVED if key in resolved}
            | {
                "idempotency_key": job.idempotency_key,
                "effect": effect,
                "placement": "pc",
                "process": "child" if name in CHILD_PROCESS else "host",
            }
            | where_ran(job, platform.node()),
        )
        zone = None
        if job.workspace is not None and kind is not None and kind.name in WRITERS:
            zone = RunZone(Path(job.workspace))
        overlay = zone.open(job) if zone is not None else None
        beat = asyncio.create_task(self.beat(job, emit))
        try:
            outcome = executor.run(job)
            result = await outcome if inspect.isawaitable(outcome) else outcome
        except asyncio.CancelledError:
            failure = self.cancelled.pop(job.idempotency_key, None)
            if failure is None:
                if zone is not None and overlay is not None:
                    zone.discard(overlay.path)
                raise
            result = failure
        except Exception as error:
            message = f"the executor raised {type(error).__name__}"
            result = Failed("executor_error", message, signature("executor_error", message), False)
        finally:
            beat.cancel()
        if zone is None or overlay is None:
            return result
        try:
            if isinstance(result, Ok):
                result = self.commit(zone, job, overlay, result, emit)
        finally:
            zone.discard(overlay.path)
        return result

    def commit(
        self, zone: RunZone, job: NodeJob, overlay: Overlay, result: Ok, emit: Emit
    ) -> NodeResult:
        """Commit without awaiting, so no other commit or ledger write of this engine runs in
        between."""
        try:
            done = zone.commit(
                job, overlay, declared_outputs(job).files, result.artifacts, attempt_keys(job)
            )
        except ZoneError as error:
            return Failed(error.code, error.message, signature(error.code, error.message), False)
        if done.sha256 or done.deleted:
            emit("zone_committed", done.data())
        zone.finish(done)
        return result

    async def beat(self, job: NodeJob, emit: Emit) -> None:
        while True:
            await asyncio.sleep(self.heartbeat_seconds)
            emit("heartbeat", attempt_keys(job) | {"note": "running"})
