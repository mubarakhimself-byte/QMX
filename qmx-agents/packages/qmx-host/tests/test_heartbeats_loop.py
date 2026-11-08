"""The heartbeat task never waits on the supervisor's lock on the host's loop.

An install holds that lock through `uv sync` and, at its end, hops onto the loop for the UI's
totals. A beat that took the lock on the loop froze every route and deadlocked the install.
"""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from qmx_host import host


class Log:
    def __init__(self, *_args: object) -> None:
        pass

    def write(self, _rows: object) -> None:
        pass

    def prune(self, _now: object) -> None:
        pass


def test_the_loop_runs_on_while_a_beat_waits_for_the_supervisors_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(host, "HeartbeatLog", Log)
    monkeypatch.setattr(host, "floor_bytes", lambda *_args: 0)
    monkeypatch.setattr(host, "free_bytes", lambda *_args: 0)
    monkeypatch.setattr(host, "make_room", lambda *_args: None)
    monkeypatch.setattr(host, "probe_from", lambda *_args: None)
    monkeypatch.setattr(host, "beat", lambda *_args, **_kwargs: "row")
    waiting, lock_free = threading.Event(), threading.Event()
    freed_in_time: list[bool] = []

    def rows() -> list[dict[str, object]]:
        waiting.set()
        freed_in_time.append(lock_free.wait(3.0))
        return []

    runtime = SimpleNamespace(heartbeats=rows)
    control = SimpleNamespace(app_runtime=lambda: runtime)
    core = SimpleNamespace(settings={}, paused=False)
    engine = SimpleNamespace(svc=SimpleNamespace(ctx=SimpleNamespace(engine=core)))

    async def run() -> None:
        beats = asyncio.create_task(
            host.heartbeats(tmp_path, "pc", cast(Any, control), cast(Any, None), cast(Any, engine))
        )
        while not waiting.is_set():
            await asyncio.sleep(0.01)
        lock_free.set()
        while not freed_in_time:
            await asyncio.sleep(0.01)
        beats.cancel()
        await asyncio.gather(beats, return_exceptions=True)

    asyncio.run(run())

    assert freed_in_time == [True]
