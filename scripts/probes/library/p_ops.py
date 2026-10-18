"""P-OPS, PC half (engine AD-65, SOLUTION-DESIGN 28.5 and 28.8): heartbeat volume for 20 agents
at the 30 s interval (Claude's default, Appendix H) on the PC.

Each tick samples one real process per agent row (this process stands in for each agent, so the
sampling cost is real), the host's free disk, and writes one AD-65 row per agent plus one for the
host into SQLite in one transaction. The share is the whole probe process's CPU time from the
first tick to the end over the wall time, an upper bound on the heartbeat work, because Windows
counts process CPU in 15.6 ms steps, too coarse to time one tick. The ticks' own wall time is a
second upper bound, and the verdict reads the larger of the two.

    uv run --no-sync --project qmx-agents python scripts/probes/library/p_ops.py [seconds]
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import sys
import time
from collections.abc import Sequence
from typing import Any, Final

from common import HOMES, Log, Verdict

AGENTS: Final = 20
INTERVAL_S: Final = 30.0
DURATION_S: Final = 1800.0
ROW_LIMIT_BYTES: Final = 4096
CPU_LIMIT_PERCENT: Final = 1.0
CLAIMS_PER_AGENT: Final = 5
KINDS: Final = [
    "agent",
    "artifact",
    "backtest-result",
    "dataset",
    "hypothesis",
    "memory-row",
    "mini-app",
    "mini-app-instance",
    "pod",
    "session",
    "source",
    "test-report",
    "workflow",
    "workflow-run",
]
FALLBACK: Final = "OPS1 sends deltas from idle hosts at a longer interval."


def row(run_id: str | None, process: Any, claims: Sequence[str]) -> dict[str, Any]:
    """One heartbeat (SOLUTION-DESIGN 28.5): the host row has no `run_id`, an agent row has one."""
    cpu = process.cpu_times()
    disk = shutil.disk_usage("D:/")
    return {
        "host": "pc",
        "run_id": run_id,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "cpu_seconds": round(cpu.user + cpu.system, 3),
        "rss_mb": round(process.memory_info().rss / 2**20, 1),
        "machine_minutes": round((time.time() - process.create_time()) / 60, 2),
        "capacity_in_use": {"cpu": 3, "chat": 2, "container": 1, "gpu": 0},
        "claims": list(claims),
        "qmx_version": "0.9.0+prb-l",
        "kinds_digest": hashlib.sha256(" ".join(KINDS).encode()).hexdigest(),
        "autonomy_paused": False,
        "blob_cache": {"count": 1834, "bytes": 912_345_678, "digest": "sha256:" + "0" * 64},
        "free_disk_mb": disk.free // 2**20,
    }


def tick(db: sqlite3.Connection, process: Any, claims: list[list[str]]) -> int:
    """Write one interval's rows and return the largest row in bytes."""
    rows = [row(None, process, [])] + [
        row(f"run-{n:02d}", process, claims[n]) for n in range(AGENTS)
    ]
    encoded = [json.dumps(r, separators=(",", ":")) for r in rows]
    with db:
        db.executemany(
            "INSERT INTO heartbeats(host, run_id, at, body) VALUES (?, ?, ?, ?)",
            [(r["host"], r["run_id"], r["at"], e) for r, e in zip(rows, encoded, strict=True)],
        )
    return max(len(e.encode()) for e in encoded)


def verdict(row_bytes: int, cpu_percent: float, ticks: int, seconds: float) -> Verdict:
    """PASS when the largest row is at most 4 KB and the work is at most 1 % of one core."""
    numbers = {
        "max_row_bytes": row_bytes,
        "cpu_percent_one_core": round(cpu_percent, 4),
        "ticks": ticks,
        "seconds": round(seconds),
        "agents": AGENTS,
    }
    if row_bytes <= ROW_LIMIT_BYTES and cpu_percent <= CPU_LIMIT_PERCENT:
        return Verdict("P-OPS", "PASS", numbers, "a row is within 4 KB and the work within 1 %")
    over = "the row" if row_bytes > ROW_LIMIT_BYTES else "the CPU share"
    return Verdict("P-OPS", "FAIL", numbers, f"{over} is over its line", FALLBACK)


def main() -> None:
    import psutil  # noqa: PLC0415

    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else DURATION_S
    log = Log("prb-l-srch-ops")
    HOMES.mkdir(parents=True, exist_ok=True)
    store = HOMES / "p_ops.db"
    store.unlink(missing_ok=True)
    db = sqlite3.connect(store)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE heartbeats(host TEXT, run_id TEXT, at TEXT, body TEXT)")
    process = psutil.Process()
    claims = [
        [hashlib.sha256(f"{n}-{k}".encode()).hexdigest() for k in range(CLAIMS_PER_AGENT)]
        for n in range(AGENTS)
    ]
    log.say(f"P-OPS: {AGENTS} agents, every {INTERVAL_S:.0f} s, for {seconds:.0f} s")
    started = time.monotonic()
    cpu_start = time.process_time()
    tick_wall, largest, ticks = 0.0, 0, 0
    while True:
        due = started + ticks * INTERVAL_S
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
        f"store {store.stat().st_size / 1e3:.0f} KB"
    )
    log.verdict(verdict(largest, 100 * work_cpu / wall, ticks, wall))


if __name__ == "__main__":
    main()
