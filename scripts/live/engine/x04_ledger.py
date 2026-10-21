"""EP4's live lanes and perf probe: the run ledger's one writer thread, on throwaway homes.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x04_ledger.py [--base REV] [--trunk REV] [lane]`
Lanes are `regression burst kill second-writer write-error migrate spans memo stats reader perf
keys`; none named runs all. Each lane writes
`evidence/ep4/<ENGINE_LOG_PREFIX>ep4-<lane>.log`, and the script exits 1 if any lane failed. No
lane needs a model, a key or the ship home.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import statistics
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Final

from common import Log, throwaway_home
from ep2_lanes import AGENTS, GIT, REPO, clean_env, git
from qmx_engine.ledger import memo
from qmx_engine.ledger.events import KINDS
from qmx_engine.ledger.memo import MemoKey
from qmx_engine.ledger.store import (
    Ledger,
    LedgerWriteError,
    Reader,
    Transaction,
    ledger_path,
)

HARNESS: Final = "qmx-agents/packages/qma-harness"
THREADS: Final = 8
APPENDS: Final = 500
RUNS: Final = 4
P95_BUDGET_MS: Final = 20.0
WALL_BUDGET_S: Final = 10.0
PERF_ROUNDS: Final = 3
KILL_AFTER: Final = 1500
SCRIPT: Final = Path(__file__).resolve()
AT: Final = "2026-10-17T09:00:00+00:00"


def contiguous(reader: Reader, runs: int) -> dict[str, tuple[int, bool]]:
    found: dict[str, tuple[int, bool]] = {}
    for r in range(runs):
        seqs = [event.seq for event in reader.events(f"run-{r}")]
        found[f"run-{r}"] = (len(seqs), seqs == list(range(1, len(seqs) + 1)))
    return found


class Burst:
    """`THREADS` threads, each appending `APPENDS` events to run `thread % RUNS`."""

    def __init__(self, ledger: Ledger) -> None:
        self.ledger = ledger
        self.latencies_ms: list[float] = []
        self.errors: list[str] = []
        self._mutex = threading.Lock()

    def worker(self, thread: int) -> None:
        mine: list[float] = []
        for i in range(APPENDS):
            started = time.perf_counter()
            try:
                self.ledger.append(f"run-{thread % RUNS}", "log", {"t": thread, "i": i}, at=AT)
            except Exception as error:
                with self._mutex:
                    self.errors.append(f"{type(error).__name__}: {error}")
                continue
            mine.append((time.perf_counter() - started) * 1000)
        with self._mutex:
            self.latencies_ms += mine

    def run(self) -> float:
        threads = [threading.Thread(target=self.worker, args=(t,)) for t in range(THREADS)]
        started = time.perf_counter()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return time.perf_counter() - started


def p95(values: list[float]) -> float:
    return statistics.quantiles(values, n=100)[94]


def burst_once(log: Log, slug: str) -> tuple[float, float]:
    home = throwaway_home("ep4", slug)
    with Ledger.open(home) as ledger:
        burst = Burst(ledger)
        wall = burst.run()
    with Reader.open(home) as reader:
        total = reader.stats().events
        runs = contiguous(reader, RUNS)
    log.check(f"{THREADS * APPENDS} events landed", total == THREADS * APPENDS, total)
    log.check(
        "seq is contiguous 1..N in every run",
        all(ok for _, ok in runs.values()) and {n for n, _ in runs.values()} == {1000},
        runs,
    )
    locked = [error for error in burst.errors if "database is locked" in error]
    log.check("no append failed", burst.errors == [], burst.errors[:3])
    log.check("no `database is locked`", locked == [], len(locked))
    tail = p95(burst.latencies_ms)
    log(
        f"burst: wall {wall:.2f} s, append p50 {statistics.median(burst.latencies_ms):.2f} ms,"
        f" p95 {tail:.2f} ms, max {max(burst.latencies_ms):.2f} ms over {len(burst.latencies_ms)}"
    )
    return tail, wall


def regression(log: Log, base: str, trunk: str) -> None:
    on_trunk = subprocess.run(
        [
            GIT,
            "cat-file",
            "-e",
            f"{trunk}:qmx-agents/packages/qmx-engine/src/qmx_engine/ledger/store.py",
        ],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    log.check("trunk has no ledger to compare against", on_trunk.returncode != 0, trunk)
    diff = subprocess.run(
        [GIT, "diff", "--quiet", base, "HEAD", "--", HARNESS], cwd=REPO, check=False
    )
    log.check("qma-harness byte-identical to the harness base", diff.returncode == 0, base)
    burst_once(log, "regression")


def burst(log: Log) -> None:
    burst_once(log, "burst")


def child_burst(home: Path) -> None:
    """The writer the kill lane kills: prints its pid, then `run seq` after each committed append.
    The pid matters because a venv `python.exe` on Windows is a launcher with the interpreter as
    its child, so killing the launcher alone leaves the writer running."""
    with Ledger.open(home) as ledger:
        sys.stdout.write(f"{os.getpid()}\n")
        sys.stdout.flush()
        lock = threading.Lock()

        def worker(thread: int) -> None:
            for i in range(100_000):
                event = ledger.append(f"run-{thread % RUNS}", "log", {"t": thread, "i": i}, at=AT)
                with lock:
                    sys.stdout.write(f"{event.run_id} {event.seq}\n")
                    sys.stdout.flush()

        threads = [threading.Thread(target=worker, args=(t,), daemon=True) for t in range(THREADS)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()


KILLED: Final = 9


def hard_kill(pid: int) -> int:
    """Terminate `pid` at once, wait until it is gone, and return its exit code."""
    if sys.platform != "win32":
        os.kill(pid, 9)
        while Path(f"/proc/{pid}").exists():
            time.sleep(0.01)
        return KILLED
    import ctypes  # noqa: PLC0415

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(0x0001 | 0x0400 | 0x00100000, False, pid)
    if not handle:
        raise SystemExit(f"cannot open writer pid {pid}")
    try:
        kernel32.TerminateProcess(handle, KILLED)
        kernel32.WaitForSingleObject(handle, 10_000)
        code = ctypes.c_ulong()
        kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        return code.value
    finally:
        kernel32.CloseHandle(handle)


def kill(log: Log) -> None:
    home = throwaway_home("ep4", "kill")
    child = subprocess.Popen(
        [sys.executable, str(SCRIPT), "_child-burst", str(home)],
        stdout=subprocess.PIPE,
        text=True,
        env=clean_env(),
        cwd=AGENTS,
    )
    if child.stdout is None:
        raise SystemExit("the child writer has no stdout")
    writer = int(child.stdout.readline())
    committed: list[tuple[str, int]] = []
    for line in child.stdout:
        run_id, seq = line.split()
        committed.append((run_id, int(seq)))
        if len(committed) >= KILL_AFTER:
            break
    code = hard_kill(writer)
    child.kill()
    child.wait()
    log(f"writer pid {writer} killed after {len(committed)} confirmed appends, exit {code}")
    log.check("the writer was killed mid-burst", code == KILLED, code)
    with Ledger.open(home) as ledger:
        log("reopened as the writer: the dead writer's lock was released by the OS")
        last = {f"run-{r}": 0 for r in range(RUNS)}
        with Reader.open(home) as reader:
            for run_id in last:
                events = reader.events(run_id)
                last[run_id] = len(events)
                bad = [
                    e.seq
                    for e in events
                    if e.kind not in KINDS or set(e.data) != {"t", "i"} or e.at != AT
                ]
                log.check(f"{run_id}: no partial or malformed event", bad == [], bad[:5])
            runs = contiguous(reader, RUNS)
            stored = {(run_id, e.seq) for run_id in last for e in reader.events(run_id)}
        missing = [pair for pair in committed if pair not in stored]
        log.check("every confirmed append reads back", missing == [], missing[:5])
        log.check("seq has no gap in any run", all(ok for _, ok in runs.values()), runs)
        log(f"events stored past the last confirmation: {len(stored) - len(committed)}")
        after = ledger.append("run-0", "log", {"t": -1, "i": -1}, at=AT)
        log.check("the next append continues the run", after.seq == last["run-0"] + 1, after.seq)


SECOND_WRITER: Final = """
import sys
from pathlib import Path
from qmx_engine.ledger.store import Ledger, Reader, WriterRefused
home = Path(sys.argv[1])
try:
    Ledger.open(home)
    print("OPENED")
except WriterRefused as refused:
    print(f"REFUSED {refused.pid} {refused}")
with Reader.open(home) as reader:
    print(f"READ {reader.stats().events}")
"""


def second_writer(log: Log) -> None:
    home = throwaway_home("ep4", "second-writer")
    with Ledger.open(home) as ledger:
        for i in range(10):
            ledger.append("run-0", "log", {"i": i}, at=AT)
        log(f"holder pid {os.getpid()} holds the writer")
        child = subprocess.run(
            [sys.executable, "-c", SECOND_WRITER, str(home)],
            capture_output=True,
            text=True,
            env=clean_env(),
            cwd=AGENTS,
            check=False,
        )
        for line in (child.stdout + child.stderr).splitlines():
            log(f"  | {line}")
        lines = child.stdout.splitlines()
        log.check(
            "the second writer is refused naming the holder's pid",
            len(lines) == 2
            and lines[0].startswith(f"REFUSED {os.getpid()} ")
            and f"pid {os.getpid()}" in lines[0],
            lines[:1],
        )
        log.check("its reader still reads", lines[1:] == ["READ 10"], lines[1:])
        later = ledger.append("run-0", "log", {"i": 10}, at=AT)
        log.check("the holder keeps writing", later.seq == 11, later.seq)


def write_error(log: Log) -> None:
    home = throwaway_home("ep4", "write-error")

    def read_only(txn: Transaction) -> None:
        txn.connection.execute("PRAGMA query_only = 1")

    ledger = Ledger.open(home)
    ledger.append("run-0", "log", {"i": 0}, at=AT)
    ledger.write(read_only)
    log("writer connection made read-only (PRAGMA query_only), so every later write is refused")
    errors: list[str] = []
    for attempt in range(3):
        try:
            ledger.append("run-0", "log", {"secret": "sk-not-echoed", "n": attempt}, at=AT)
        except LedgerWriteError as error:
            errors.append(str(error))
    log.check("each of three appends raises LedgerWriteError", len(errors) == 3, errors)
    log.check("no error names a value", all("sk-not-echoed" not in e for e in errors), errors[0])
    started = time.perf_counter()
    ledger.close()
    log.check(
        "the writer thread stayed alive: it took the close order and exited",
        time.perf_counter() - started < 5,
        f"{time.perf_counter() - started:.3f} s",
    )
    with Ledger.open(home) as reopened:
        after = reopened.append("run-0", "log", {"i": 1}, at=AT)
    log.check("after reopen seq has no gap", after.seq == 2, after.seq)


def migrate(log: Log) -> None:
    home = throwaway_home("ep4", "migrate")
    schemas: list[list[tuple[str, str]]] = []
    for attempt in (1, 2):
        with Ledger.open(home) as ledger:
            log(f"open {attempt}: applied steps {ledger.applied}")
            applied = ledger.applied
        with Reader.open(home) as reader:
            schemas.append(
                reader.connection.execute(
                    "SELECT name, sql FROM sqlite_master ORDER BY name"
                ).fetchall()
            )
            version = reader.stats().schema_version
        log.check(f"open {attempt}: schema_version is 2", version == 2, version)
        log.check(
            f"open {attempt}: steps applied", applied == ([1, 2] if attempt == 1 else []), applied
        )
    log.check("the second run changed no table or index", schemas[0] == schemas[1], len(schemas[1]))


def spans_lane(log: Log) -> None:
    home = throwaway_home("ep4", "spans")
    with Ledger.open(home) as ledger:
        ledger.append("run-0", "run_created", {"mode": "test"}, at=AT)
        endings = ("node_finished", "node_failed", "node_finished")
        for attempt, ending in enumerate(endings, start=1):
            key = {"node_id": "triage", "iteration": 0, "partition": None, "attempt": attempt}
            ledger.append("run-0", "node_started", key, at=f"2026-10-17T09:0{attempt}:00+00:00")
            ledger.append("run-0", ending, key, at=f"2026-10-17T09:0{attempt}:0{attempt * 2}+00:00")
    with Reader.open(home) as reader:
        found = [(s.attempt, s.status, s.duration_seconds) for s in reader.spans("run-0")]
    log(f"spans: {found}")
    log.check(
        "three span rows with durations",
        sorted(found) == [(1, "ok", 2.0), (2, "failed", 4.0), (3, "ok", 6.0)],
        found,
    )


MEMO_KEY: Final = """
from qmx_engine.ledger.memo import MemoKey
key = MemoKey.of("run-0", "triage", 0, "2", {"ids": [3, 1, 2], "q": "llm"}, {"type": "llm"})
print(key.fingerprint)
"""


def memo_lane(log: Log) -> None:
    keys = [
        subprocess.run(
            [sys.executable, "-c", MEMO_KEY],
            capture_output=True,
            text=True,
            env=clean_env(),
            cwd=AGENTS,
            check=True,
        ).stdout.strip()
        for _ in range(2)
    ]
    log.check("two processes compute one memo key", keys[0] == keys[1] and len(keys[0]) == 64, keys)
    home = throwaway_home("ep4", "memo")
    key = MemoKey.of("run-0", "triage", 0, "2", {"ids": [3, 1, 2], "q": "llm"}, {"type": "llm"})
    with Ledger.open(home) as ledger:
        memo.record(ledger, key, {"main": ["card"]})
    with Reader.open(home) as reader:
        log.check(
            "the memo under that key holds its outputs",
            memo.has(reader, key) and memo.outputs(reader, key) == {"main": ["card"]},
            key.fingerprint == keys[0],
        )


TWO_NODES: Final = (
    AGENTS / "packages" / "qmx-engine" / "tests" / "fixtures" / "workflows" / "script-chain"
)
KEYS: Final = ("node_id", "iteration", "partition", "attempt")


def keys_lane(log: Log) -> None:
    """BUG2 lane 3: every node event of a real run carries its attempt key (AD-15, B-18), and the
    ledger refuses an ending without one (L-29)."""
    import asyncio  # noqa: PLC0415

    from qmx_engine.definition.validate import checked  # noqa: PLC0415
    from qmx_engine.runner import Engine  # noqa: PLC0415
    from qmx_engine.settings import DEFAULTS  # noqa: PLC0415

    home = throwaway_home("ep4", "keys")
    found = checked(TWO_NODES)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: script-chain does not validate: {found}")

    async def go() -> str:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings=DEFAULTS)
            outcome = await engine.start(TWO_NODES, found[1], mode="test", inputs=None)
            return outcome.run_id

    run_id = asyncio.run(go())
    with Reader.open(home) as reader:
        events = reader.events(run_id)
        spans = reader.spans(run_id)
    node_events = [e for e in events if "node_id" in e.data]
    kinds = sorted({e.kind for e in node_events})
    missing = [(e.seq, e.kind) for e in node_events if not all(k in e.data for k in KEYS)]
    scheduled = [e.data.get("input_hash") for e in node_events if e.kind == "node_scheduled"]
    log(f"run {run_id}: {len(node_events)} node events of kinds {kinds}, {len(spans)} spans")
    log.check(
        "every node event carries node_id, iteration, partition and attempt", not missing, missing
    )
    log.check(
        "every node_scheduled carries its input hash",
        len(scheduled) == 4 and all(isinstance(h, str) and len(h) == 64 for h in scheduled),
        scheduled,
    )
    log.check(
        "one span per attempt, each ok",
        sorted((s.node_id, s.status) for s in spans)
        == [("double", "ok"), ("numbers", "ok"), ("start", "ok"), ("total", "ok")],
        [(s.node_id, s.status) for s in spans],
    )
    with Ledger.open(home) as ledger:
        try:
            ledger.append(run_id, "node_finished", {"node_id": "total", "attempt": 1}, at=AT)
            refused = "stored"
        except ValueError as error:
            refused = str(error)
    log.check(
        "an ending without its full key is refused",
        refused.startswith("node_finished needs"),
        refused,
    )


def stats(log: Log) -> None:
    home = throwaway_home("ep4", "stats")
    with Ledger.open(home) as ledger:
        for i in range(3):
            ledger.append("run-0", "log", {"i": i}, at=AT)
    done = subprocess.run(
        [sys.executable, "-m", "qmx_engine", "ledger", "stats", "--home", str(home)],
        capture_output=True,
        text=True,
        env=clean_env(),
        cwd=AGENTS,
        check=False,
    )
    log(f"$ python -m qmx_engine ledger stats --home {home}")
    for line in done.stdout.splitlines():
        log(f"  | {line}")
    log.check(
        "stats prints the schema version, the SQLite version and the event count",
        done.returncode == 0
        and done.stdout.splitlines()
        == ["schema_version 2", f"sqlite_version {sqlite3.sqlite_version}", "events 3"],
        done.returncode,
    )


def reader(log: Log) -> None:
    home = throwaway_home("ep4", "reader")
    with Ledger.open(home) as ledger:
        ledger.append("run-0", "log", {"i": -1}, at=AT)
        stop = threading.Event()
        reads: list[float] = []

        def read_loop() -> None:
            with Reader(ledger_path(home)) as ro:
                while not stop.is_set():
                    started = time.perf_counter()
                    ro.connection.execute("SELECT count(*), max(seq) FROM events").fetchone()
                    reads.append((time.perf_counter() - started) * 1000)

        readers = [threading.Thread(target=read_loop) for _ in range(2)]
        for thread in readers:
            thread.start()
        burst = Burst(ledger)
        burst.run()
        stop.set()
        for thread in readers:
            thread.join()
    worst = max(burst.latencies_ms)
    log(f"{len(reads)} reads during the burst, read p95 {p95(reads):.2f} ms")
    log.check("no append failed", burst.errors == [], burst.errors[:3])
    log.check(
        "no append waited more than 100 ms while readers read", worst <= 100, f"{worst:.2f} ms"
    )


def perf(log: Log) -> None:
    results = [burst_once(log, f"perf-{r}") for r in range(PERF_ROUNDS)]
    tails = [tail for tail, _ in results]
    walls = [wall for _, wall in results]
    log(
        f"perf: append p95 per round {[round(t, 2) for t in tails]} ms,"
        f" burst wall per round {[round(w, 2) for w in walls]} s"
    )
    log.check(
        f"append p95 at most {P95_BUDGET_MS:.0f} ms in every round",
        max(tails) <= P95_BUDGET_MS,
        f"{max(tails):.2f} ms",
    )
    log.check(
        f"the {THREADS * APPENDS}-event burst at most {WALL_BUDGET_S:.0f} s in every round",
        max(walls) <= WALL_BUDGET_S,
        f"{max(walls):.2f} s",
    )


def main() -> int:
    if sys.argv[1:2] == ["_child-burst"]:
        child_burst(Path(sys.argv[2]))
        return 0
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/engine/hg2")
    parser.add_argument("--trunk", default="origin/engine/ep3")
    parser.add_argument("lanes", nargs="*")
    args = parser.parse_args()
    base, trunk = git("rev-parse", args.base), git("rev-parse", args.trunk)
    lanes: dict[str, Callable[[Log], None]] = {
        "regression": lambda log: regression(log, base, trunk),
        "burst": burst,
        "kill": kill,
        "second-writer": second_writer,
        "write-error": write_error,
        "migrate": migrate,
        "spans": spans_lane,
        "memo": memo_lane,
        "stats": stats,
        "reader": reader,
        "perf": perf,
        "keys": keys_lane,
    }
    failed: list[str] = []
    for name in args.lanes or list(lanes):
        log = Log("ep4", f"ep4-{name}")
        log(f"lane {name} at head {git('rev-parse', 'HEAD')}, harness base {base}")
        log(f"python {sys.version.split()[0]}, sqlite {sqlite3.sqlite_version}")
        lanes[name](log)
        if log.verdict():
            failed.append(name)
    print(f"failed lanes: {failed}" if failed else "all lanes passed", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
