"""Machine-wide locks (FACTORY-DESIGN 11.6), all under `<factory_home>/run/`: one merge per project at a time
with a queue, one Fable worker at a time, and the worker pool.

Every lock is the same pattern as `state.locked`: a file made with create-exclusive holding the pid and
its creation time, taken over when its holder is gone. A holder is gone when its pid no longer names
the process that wrote it, or the file was written before the machine last started (D-L14).

- `FileLock(path)`: `try_take()`, `release()`, and a blocking context manager.
- `MergeLock(project, settings)`: `ask(program, stop)` joins the queue and takes the lock only when it is
  free and the asker is the oldest live waiter (row 49: the one that waited longest goes next).
  Waiters are named by program, since each `ship merge` is a fresh process the conveyor starts again
  next tick: a waiter stays live while it asked within `merge_queue_stale_s`.
- `fable_lock(settings)`: the one Fable seat.
- `Pool(settings, size)`: at most `size` slot files `pool/<pid>-<n>.slot`; a slot whose owner and worker
  are both gone is deleted.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import time
from pathlib import Path
from typing import Iterator

from ship import clock
from ship.proc import boot_time, created as proc_created, pid_alive, same_process
from ship.settings import Settings


def run_dir(settings: Settings) -> Path:
    from ship.launch import factory_home

    return factory_home(settings) / "run"


def _alive(pid: int | None, created: float | None) -> bool:
    if not pid:
        return False
    return same_process(pid, created) if created is not None else pid_alive(pid)


def _before_boot(path: Path) -> bool:
    try:
        return path.stat().st_mtime < boot_time() - 1
    except OSError:
        return False


def _read(path: Path) -> dict:
    try:
        body = json.loads(path.read_text("utf-8") or "{}")
        return body if isinstance(body, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(path: Path, body: dict) -> None:
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(body, indent=2), "utf-8")
    os.replace(tmp, path)


class FileLock:
    """Create-exclusive, pid inside, taken over when its holder (and its worker, when named) is gone."""

    def __init__(self, path: Path):
        self.path = path
        self.mine = False

    def holder(self) -> dict:
        return _read(self.path)

    def held_by_live(self) -> bool:
        body = self.holder()
        if not body:
            young = self.path.exists() and time.time() - self.path.stat().st_mtime < 10
            return young  # being written right now
        if _before_boot(self.path):
            return False
        return _alive(body.get("pid"), body.get("created")) or _alive(body.get("worker"), body.get("worker_created"))

    def try_take(self, **extra) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(3):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if self.held_by_live():
                    return False
                self.path.unlink(missing_ok=True)
                continue
            body = {"pid": os.getpid(), "created": proc_created(os.getpid()),
                    "since": clock.now().isoformat(timespec="seconds"), **extra}
            os.write(fd, json.dumps(body).encode())
            os.close(fd)
            self.mine = True
            return True
        return False

    def note_worker(self, pid: int) -> None:
        """Name the worker the lock is held for, so a dead owner with a live worker still holds it."""
        if self.mine:
            body = self.holder()
            body.update({"worker": pid, "worker_created": proc_created(pid)})
            _write(self.path, body)

    def release(self) -> None:
        if self.mine and int(self.holder().get("pid") or 0) == os.getpid():
            self.path.unlink(missing_ok=True)
        self.mine = False

    @contextlib.contextmanager
    def held(self, poll_s: float = 0.1, timeout_s: float = 120) -> Iterator["FileLock"]:
        end = time.monotonic() + timeout_s
        while not self.try_take():
            if time.monotonic() > end:
                raise TimeoutError(f"{self.path} is held by {self.holder()}")
            time.sleep(poll_s)
        try:
            yield self
        finally:
            self.release()


class MergeLock:
    """`merge-<project>.lock`: {pid, created, program, stop, since, queue: [{program, pid, since, seen}]}."""

    def __init__(self, project: str, settings: Settings):
        self.settings = settings
        self.path = run_dir(settings) / f"merge-{project}.lock"
        self.guard = FileLock(self.path.with_name(self.path.name + ".guard"))
        self.mine = False
        self.program = ""

    def read(self) -> dict:
        return _read(self.path)

    def _live_waiter(self, row: dict, now: dt.datetime) -> bool:
        if _alive(row.get("pid"), row.get("created")):
            return True
        try:
            seen = dt.datetime.fromisoformat(row.get("seen") or row.get("since") or "")
        except ValueError:
            return False
        return (now - seen).total_seconds() < self.settings.merge_queue_stale_s

    def ask(self, program: str, stop: str) -> bool:
        """Join the queue (or refresh the place in it) and take the lock when it is this program's turn."""
        now = clock.now()
        stamp = now.isoformat(timespec="seconds")
        with self.guard.held():
            body = self.read()
            holder_live = bool(body.get("program")) and (
                _alive(body.get("pid"), body.get("created")) and not _before_boot(self.path))
            if body.get("program") == program and body.get("pid") == os.getpid():
                self.mine, self.program = True, program
                return True
            queue = [r for r in body.get("queue", []) if self._live_waiter(r, now)]
            row = next((r for r in queue if r.get("program") == program), None)
            if row is None:
                row = {"program": program, "since": stamp}
                queue.append(row)
            row.update({"pid": os.getpid(), "created": proc_created(os.getpid()), "seen": stamp})
            first = queue[0].get("program") == program
            if holder_live or not first:
                _write(self.path, {**({k: body[k] for k in ("pid", "created", "program", "stop", "since")
                                       if k in body} if holder_live else {}), "queue": queue})
                return False
            queue = [r for r in queue if r.get("program") != program]
            _write(self.path, {"pid": os.getpid(), "created": proc_created(os.getpid()), "program": program,
                               "stop": stop, "since": stamp, "queue": queue})
            self.mine, self.program = True, program
            return True

    def release(self) -> None:
        if not self.mine:
            return
        with self.guard.held():
            body = self.read()
            if body.get("program") == self.program and body.get("pid") == os.getpid():
                _write(self.path, {"queue": body.get("queue", [])})
        self.mine = False

    def waiting(self) -> list[str]:
        return [r.get("program", "") for r in self.read().get("queue", [])]


def merge_lock(project: str, settings: Settings) -> MergeLock:
    return MergeLock(project, settings)


def fable_lock(settings: Settings) -> FileLock:
    return FileLock(run_dir(settings) / "fable.lock")


class Slot:
    def __init__(self, path: Path):
        self.path = path

    def note_worker(self, pid: int) -> None:
        body = _read(self.path)
        body.update({"worker": pid, "worker_created": proc_created(pid)})
        _write(self.path, body)

    def release(self) -> None:
        self.path.unlink(missing_ok=True)


class Pool:
    """At most `size` headless workers at once on this machine, across every program."""

    def __init__(self, settings: Settings, size: int):
        self.dir = run_dir(settings) / "pool"
        self.size = max(1, int(size))

    def live(self) -> list[Path]:
        out = []
        for path in sorted(self.dir.glob("*.slot")) if self.dir.is_dir() else []:
            body = _read(path)
            gone = _before_boot(path) or not (_alive(body.get("pid"), body.get("created"))
                                              or _alive(body.get("worker"), body.get("worker_created")))
            young = not body and time.time() - path.stat().st_mtime < 10 if path.exists() else False
            if gone and not young:
                path.unlink(missing_ok=True)
                continue
            out.append(path)
        return out

    def take(self) -> Slot | None:
        self.dir.mkdir(parents=True, exist_ok=True)
        guard = FileLock(self.dir / "pool.guard")
        with guard.held():
            if len(self.live()) >= self.size:
                return None
            n = 0
            while True:
                path = self.dir / f"{os.getpid()}-{n}.slot"
                try:
                    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    break
                except FileExistsError:
                    n += 1
            os.write(fd, json.dumps({"pid": os.getpid(), "created": proc_created(os.getpid()),
                                     "since": clock.now().isoformat(timespec="seconds")}).encode())
            os.close(fd)
            return Slot(path)
