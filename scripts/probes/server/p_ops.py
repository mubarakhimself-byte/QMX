"""P-OPS, Contabo half (engine AD-65, SOLUTION-DESIGN 28.5 and 28.8, review 48 M11): heartbeat
volume for 20 agents at the 30 s interval on his server.

The limits, the row's insert path and the verdict come from `scripts/probes/library/p_ops.py` by
path, so the server is judged on the bar the PC was judged on. Only the row producer is the
server's, because the library's labels the host `pc` and reads `D:/` for free disk, and this host
labels itself `server` and reads its root filesystem.

Runs in the throwaway venv, which has psutil:

    HOME=/srv/qmx/check/prb-s/homes/prb-s \
        /srv/qmx/check/prb-s/homes/prb-s/venv/bin/python scripts/probes/server/p_ops.py [seconds]
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import sys
import time
from collections.abc import Sequence
from typing import Any

from common import PROBE_HOME, Log, free_mb, library, total_mb

OPS = library("p_ops")
Verdict = OPS.Verdict
HOST = "server"
DISK_ROOT = "/"


def row(run_id: str | None, process: Any, claims: Sequence[str]) -> dict[str, Any]:
    """One heartbeat (SOLUTION-DESIGN 28.5): the host row has no `run_id`, an agent row has one.
    The fields are the library row's; the host name and the disk root are this host's."""
    cpu = process.cpu_times()
    disk = shutil.disk_usage(DISK_ROOT)
    return {
        "host": HOST,
        "run_id": run_id,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "cpu_seconds": round(cpu.user + cpu.system, 3),
        "rss_mb": round(process.memory_info().rss / 2**20, 1),
        "machine_minutes": round((time.time() - process.create_time()) / 60, 2),
        "capacity_in_use": {"cpu": 3, "chat": 2, "container": 1, "gpu": 0},
        "claims": list(claims),
        "qmx_version": "0.9.0+prb-s",
        "kinds_digest": hashlib.sha256(" ".join(OPS.KINDS).encode()).hexdigest(),
        "autonomy_paused": False,
        "blob_cache": {"count": 1834, "bytes": 912_345_678, "digest": "sha256:" + "0" * 64},
        "free_disk_mb": disk.free // 2**20,
    }


def tick(db: sqlite3.Connection, process: Any, claims: list[list[str]]) -> int:
    """One interval's rows through the library's insert path, with this host's row."""
    OPS.row = row
    return OPS.tick(db, process, claims)


def main() -> None:
    import psutil  # noqa: PLC0415

    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else OPS.DURATION_S
    log = Log("prb-s-ops")
    PROBE_HOME.mkdir(parents=True, exist_ok=True)
    store = PROBE_HOME / "p_ops.db"
    store.unlink(missing_ok=True)
    db = sqlite3.connect(store)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE heartbeats(host TEXT, run_id TEXT, at TEXT, body TEXT)")
    process = psutil.Process()
    claims = [
        [hashlib.sha256(f"{n}-{k}".encode()).hexdigest() for k in range(OPS.CLAIMS_PER_AGENT)]
        for n in range(OPS.AGENTS)
    ]
    log.say(
        f"P-OPS on {HOST}: {OPS.AGENTS} agents, every {OPS.INTERVAL_S:.0f} s, for {seconds:.0f} s; "
        f"{free_mb()} MB free of {total_mb()} MB, load {os.getloadavg()}"
    )
    started = time.monotonic()
    cpu_start = time.process_time()
    tick_wall, largest, ticks = 0.0, 0, 0
    while True:
        due = started + ticks * OPS.INTERVAL_S
        if due - started >= seconds:
            break
        time.sleep(max(0.0, due - time.monotonic()))
        before = time.perf_counter()
        largest = max(largest, tick(db, process, claims))
        tick_wall += time.perf_counter() - before
        ticks += 1
    time.sleep(max(0.0, started + seconds - time.monotonic()))
    wall = time.monotonic() - started
    work_cpu = max(time.process_time() - cpu_start, tick_wall)
    rows = db.execute("SELECT count(*) FROM heartbeats").fetchone()[0]
    db.close()
    log.say(
        f"  {rows} rows, work (larger of process CPU and tick wall) {work_cpu * 1000:.1f} ms; "
        f"tick wall {tick_wall * 1000:.1f} ms over {wall:.0f} s, "
        f"store {store.stat().st_size / 1e3:.0f} KB, load {os.getloadavg()}"
    )
    log.verdict(OPS.verdict(largest, 100 * work_cpu / wall, ticks, wall))


if __name__ == "__main__":
    main()
