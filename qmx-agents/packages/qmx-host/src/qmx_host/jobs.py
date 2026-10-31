"""Long work the host runs in the background, read by id (loose strings P1).

A job is `running`, then `finished` with its result or `stopped` with one plain line saying why.
While it runs, its work reports where it is (`step`), how far it is in that step (`done` of
`total`) and its own counts (`progress`). Jobs live for the process's life and are never capped or
pruned (ruling 106); a reader that lost an id finds the newest job of a kind with `latest`.
"""

from __future__ import annotations

import dataclasses
import threading
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Literal, NamedTuple, Protocol

type State = Literal["running", "finished", "stopped"]


class Progress(Protocol):
    """How work says where it is. Each call replaces the step and its `done` of `total`, and
    updates the named counts."""

    def __call__(self, step: str, *, done: int = 0, total: int = 0, **counts: int) -> None: ...


type Work = Callable[[Progress], Mapping[str, object]]
"""The job's body, run on its own thread. What it returns is the finished job's result."""


class Stopped(Exception):
    """Work that ends stopped on purpose: `line` says why and what to do next, and `result` holds
    what it got done, when that is worth showing."""

    def __init__(self, line: str, result: Mapping[str, object] | None = None) -> None:
        super().__init__(line)
        self.line = line
        self.result = result


@dataclass(frozen=True, slots=True)
class Job:
    """One job as a reader sees it at one moment."""

    id: str
    kind: str
    state: State
    step: str = ""
    done: int = 0
    total: int = 0
    progress: Mapping[str, int] = field(default_factory=dict[str, int])
    line: str = ""
    """Empty while the job runs or once it finished; why it stopped otherwise."""
    result: Mapping[str, object] | None = None

    def document(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind,
            "state": self.state,
            "step": self.step,
            "done": self.done,
            "total": self.total,
            "progress": dict(self.progress),
            "line": self.line,
            "result": None if self.result is None else dict(self.result),
        }


class Started(NamedTuple):
    job: Job
    new: bool
    """False when `alone` found a job of that kind running, which `job` then is."""


class Jobs:
    """Every job this process started, by id."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, Job] = {}

    def start(self, kind: str, work: Work, *, alone: bool = True) -> Started:
        """Run `work` on a daemon thread as a new job of `kind`. With `alone`, a job of that kind
        that is still running is returned instead, and nothing new starts."""
        with self._lock:
            running = next(
                (j for j in self._jobs.values() if j.kind == kind and j.state == "running"), None
            )
            if alone and running is not None:
                return Started(running, new=False)
            job = Job(str(uuid.uuid4()), kind, "running")
            self._jobs[job.id] = job
        threading.Thread(
            target=self._run, args=(job.id, work), name=f"job-{kind}", daemon=True
        ).start()
        return Started(job, new=True)

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def latest(self, kind: str) -> Job | None:
        """The newest job of `kind`, running or ended, or None."""
        with self._lock:
            return next((j for j in reversed(self._jobs.values()) if j.kind == kind), None)

    def _run(self, job_id: str, work: Work) -> None:
        def report(step: str, *, done: int = 0, total: int = 0, **counts: int) -> None:
            with self._lock:
                job = self._jobs[job_id]
                self._jobs[job_id] = dataclasses.replace(
                    job, step=step, done=done, total=total, progress={**job.progress, **counts}
                )

        try:
            result = work(report)
        except Stopped as stopped:
            self._end(job_id, "stopped", stopped.line, stopped.result)
        except Exception as error:  # a job ends with one line, never a traceback
            why = str(error) or type(error).__name__
            self._end(job_id, "stopped", f"it stopped with an error: {why}")
        else:
            self._end(job_id, "finished", "", result)

    def _end(
        self, job_id: str, state: State, line: str, result: Mapping[str, object] | None = None
    ) -> None:
        with self._lock:
            self._jobs[job_id] = dataclasses.replace(
                self._jobs[job_id], state=state, line=line, result=result
            )
