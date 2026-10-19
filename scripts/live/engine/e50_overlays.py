"""E50 (SEC2A): attempt overlays, staged commits and the script's lifetime, on throwaway homes.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e50_overlays.py <lane>`

- `overlays` (lane 2): the sibling's committed files survive a retry, scratch files of concurrent
  attempts never collide, a second writer of one path is refused at validation, and a commit cut
  by a real crash between its renames rolls forward on resume.
- `lifetime` (lane 4): the engine is killed with `taskkill /F` during a 60 s script, and the
  script must be gone within 2 s.
- `sweep` (lane 6): a planted orphan recorded under a run's zone is stopped when the run resumes.
- `perf`: the commit time of 100 declared files, five runs.

Writes `evidence/sec2a/<ENGINE_LOG_PREFIX>sec2a-<lane>.log`. No model, no keyring, no ship home.
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path
from typing import Any, Final

import psutil
from common import Log, throwaway_home
from ep2_lanes import AGENTS, clean_env
from qmx_engine.definition.model import OutputFile
from qmx_engine.nodes.base import NodeJob
from qmx_engine.workers.zones import RunZone
from x07_nodes import ENGINE, cli, events, node, of, write_folder

CHUNK: Final = """
    import json, os, sys, time
    from pathlib import Path
    item = json.load(sys.stdin)["in"]
    counter = Path(item["counter"])
    tries = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(tries))
    mine = f"partition {item['n']} try {tries}"
    Path("script.py").write_text(mine)
    Path("out.json").write_text(mine)
    time.sleep(1.5)
    kept = Path("script.py").read_text() == mine and Path("out.json").read_text() == mine
    Path("out").mkdir()
    Path("out", f"{item['n']}.json").write_text(json.dumps({"n": item["n"], "try": tries}))
    if item["n"] == 1 and tries == 1:
        sys.exit(1)
    print(json.dumps({"n": item["n"], "kept_own_scratch": kept}))
"""
PAIR: Final = """
    from pathlib import Path
    Path("a.txt").write_text("A")
    Path("b.txt").write_text("B")
    print(1)
"""
SLEEP: Final = """
    import json, os, sys, time
    from pathlib import Path
    Path(json.load(sys.stdin)["in"]).write_text(str(os.getpid()))
    if os.environ["QMX_ATTEMPT"] == "1":
        time.sleep(60)
    print(json.dumps("done"))
"""
WITHOUT_JOB: Final = """
import sys
import qmx_engine.nodes.script as script
script.contain = lambda pid: False
from qmx_engine.__main__ import main
sys.exit(main(sys.argv[1:]))
"""
CRASH_BEFORE_B: Final = """
import os, sys
real = os.replace
def replace(source, target):
    if str(target).endswith("b.txt"):
        os._exit(9)
    return real(source, target)
os.replace = replace
from qmx_engine.__main__ import main
sys.exit(main(sys.argv[1:]))
"""


def edge(target: str, map_: str = "one") -> dict[str, Any]:
    return {"node": target, "port": "in", "map": map_}


def files_of(folder: Path) -> list[str]:
    if not folder.is_dir():
        return []
    return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())


def sibling_and_scratch(log: Log, home: Path) -> None:
    work = node("work", "script", script="scripts/chunk.py")
    work["outputs"] = {"files": [{"path": "out/<partition>.json"}]}
    work["retry"] = {"backoff_seconds": [0]}
    root = write_folder(
        home / "wf-chunks",
        [node("start", "trigger"), work],
        {"start": {"main": [edge("work", "broadcast")]}},
        {"chunk": CHUNK},
    )
    items = [{"n": n, "counter": str(home / f"tries-{n}.txt")} for n in range(3)]
    code, _ = cli(
        log, "run", str(root), "--home", str(home), "--run-id", "run-e50-chunks",
        "--inputs", json.dumps(items),
    )  # fmt: skip
    found = events(home, "run-e50-chunks")
    zone = RunZone.of(home, "run-e50-chunks")
    committed = {
        str(p): str(e.data["sha256"][p])  # type: ignore[index]
        for e in found
        if e.kind == "zone_committed"
        for p in e.data["paths"]  # type: ignore[union-attr]
    }
    now = {p: sha256((zone.work / p).read_bytes()).hexdigest() for p in files_of(zone.work)}
    outputs = [d["outputs"]["main"] for d in of(found, "node_finished", "work")]
    failed = [d["partition"] for d in of(found, "node_failed", "work")]
    log(f"work/ holds {files_of(zone.work)}; attempts left {files_of(zone.attempts)}")
    log(f"zone_committed {committed}")
    log.check("the run passed with one retry of partition 1", (code, failed) == (0, [1]), failed)
    log.check(
        "each sibling's committed file is as it was committed, after the retry",
        now == committed and sorted(now) == ["out/0.json", "out/1.json", "out/2.json"],
        now,
    )
    log.check(
        "partitions 0 and 2 ran once, 1 committed its second try",
        [json.loads((zone.work / "out" / f"{n}.json").read_text())["try"] for n in range(3)]
        == [1, 2, 1],
        "",
    )
    log.check(
        "every concurrent attempt read back its own scratch files",
        len(outputs) == 3 and all(o["kept_own_scratch"] for o in outputs),
        outputs,
    )
    log.check(
        "no scratch file and no attempt folder is left",
        "script.py" not in now and "out.json" not in now and files_of(zone.attempts) == [],
        files_of(zone.attempts),
    )


def second_writer(log: Log, home: Path) -> None:
    left = node("left", "script", script="scripts/pair.py")
    left["outputs"] = {"files": [{"path": "report.md"}]}
    right = node("right", "script", script="scripts/pair.py")
    right["outputs"] = {"files": [{"path": "report.md"}]}
    root = write_folder(
        home / "wf-two-writers",
        [node("start", "trigger"), left, right],
        {"start": {"main": [edge("left"), edge("right")]}},
        {"pair": PAIR},
    )
    code, lines = cli(log, "validate", str(root))
    refused = [line for line in lines if line.startswith("zone_writer_concurrent")]
    log.check(
        "the second writer is refused at validation", code != 0 and len(refused) == 1, refused
    )


def roll_forward(log: Log, home: Path) -> None:
    pair = node("pair", "script", script="scripts/pair.py")
    pair["outputs"] = {"files": [{"path": "*.txt"}]}
    root = write_folder(
        home / "wf-crash",
        [node("start", "trigger"), pair],
        {"start": {"main": [edge("pair")]}},
        {"pair": PAIR},
    )
    run_id = "run-e50-crash"
    log("$ engine run with os.replace cut before b.txt (the engine exits 9 mid-commit)")
    crashed = subprocess.run(
        [sys.executable, "-c", CRASH_BEFORE_B, "run", str(root), "--home", str(home),
         "--run-id", run_id],
        cwd=AGENTS, env=clean_env(), capture_output=True, text=True, check=False, timeout=300,
    )  # fmt: skip
    zone = RunZone.of(home, run_id)
    staged = files_of(zone.staging)
    log(f"  exit {crashed.returncode}; work/ {files_of(zone.work)}; staging {staged}")
    log.check(
        "the engine died between the renames",
        crashed.returncode == 9
        and (zone.work / "a.txt").is_file()
        and not (zone.work / "b.txt").is_file()
        and any(s.endswith("files/b.txt") for s in staged),
        crashed.returncode,
    )
    code, _ = cli(log, "resume", run_id, "--home", str(home))
    found = events(home, run_id)
    commits = [e.data["paths"] for e in found if e.kind == "zone_committed"]
    log(f"zone_committed after resume: {commits}")
    log.check(
        "the staged commit rolled forward on resume",
        code == 0
        and files_of(zone.work) == ["a.txt", "b.txt"]
        and commits[:1] == [["a.txt", "b.txt"]],
        files_of(zone.work),
    )


def overlays(log: Log) -> None:
    home = throwaway_home("sec2a", "e50")
    sibling_and_scratch(log, home)
    second_writer(log, home)
    roll_forward(log, home)


def sleeper(home: Path, name: str) -> Path:
    return write_folder(
        home / name,
        [node("start", "trigger"), node("sleep", "script", script="scripts/sleep.py")],
        {"start": {"main": [edge("sleep")]}},
        {"sleep": SLEEP},
    )


def start_engine(
    home: Path, root: Path, run_id: str, engine: list[str] = ENGINE
) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [
            *engine,
            "run",
            str(root),
            "--home",
            str(home),
            "--run-id",
            run_id,
            "--inputs",
            json.dumps(str(home / "pid.txt")),
        ],
        cwd=AGENTS,
        env=clean_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_for_pid(path: Path, seconds: float = 60) -> int:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.is_file() and path.read_text().strip():
            return int(path.read_text())
        time.sleep(0.1)
    raise SystemExit("BLOCKED: the script never wrote its pid")


def taskkill(*args: str) -> None:
    subprocess.run(["taskkill", *args], capture_output=True, check=False)  # noqa: S607


def kill_engine(log: Log, home: Path, engine: list[str], name: str) -> float | None:
    """Seconds until the script died after the engine was killed, or None if it outlived 10 s."""
    process = start_engine(home, sleeper(home, name), f"run-e50-{name}", engine)
    script = wait_for_pid(home / "pid.txt")
    log(f"engine pid {process.pid}, script pid {script} (alive {psutil.pid_exists(script)})")
    log(f"$ taskkill /F /PID {process.pid}  (the engine only, not its tree)")
    began = time.monotonic()
    taskkill("/F", "/PID", str(process.pid))
    while psutil.pid_exists(script) and time.monotonic() - began < 10:
        time.sleep(0.05)
    gone = time.monotonic() - began
    process.wait()
    (home / "pid.txt").unlink()
    if psutil.pid_exists(script):
        taskkill("/F", "/T", "/PID", str(script))
        return None
    return gone


def lifetime(log: Log) -> None:
    home = throwaway_home("sec2a", "lifetime")
    gone = kill_engine(log, home, ENGINE, "life")
    log.check("the script died with the engine within 2 s", gone is not None and gone < 2, gone)
    log("control: the same engine with the Job object switched off")
    control = kill_engine(log, home, [sys.executable, "-c", WITHOUT_JOB], "control")
    log.check("without the Job object the script outlives the engine", control is None, control)


def sweep(log: Log) -> None:
    home = throwaway_home("sec2a", "sweep")
    run_id = "run-e50-sweep"
    engine = start_engine(home, sleeper(home, "wf-sweep"), run_id)
    wait_for_pid(home / "pid.txt")
    taskkill("/F", "/PID", str(engine.pid))
    engine.wait()
    orphan = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )
    zone = RunZone.of(home, run_id)
    zone.pids.mkdir(parents=True, exist_ok=True)
    record = zone.pids / "sleep.0.-.1.json"
    created = psutil.Process(orphan.pid).create_time()
    record.write_text(json.dumps({"pid": orphan.pid, "created": created}), encoding="utf-8")
    log(f"planted orphan {orphan.pid} recorded at {record.name}")
    code, _ = cli(log, "resume", run_id, "--home", str(home))
    time.sleep(0.5)
    found = events(home, run_id)
    folded = [d.get("effect_state") for d in of(found, "node_failed", "sleep")]
    log.check("the resume stopped the orphan", orphan.poll() is not None, orphan.poll())
    log.check("its record is gone", not record.exists(), files_of(zone.pids))
    log.check(
        "the dead attempt folded unknown and the run passed",
        (code, folded) == (0, ["unknown"]),
        folded,
    )
    if orphan.poll() is None:
        orphan.kill()


def perf(log: Log) -> None:
    home = throwaway_home("sec2a", "perf")
    timings: list[float] = []
    for round_ in range(5):
        zone = RunZone(Path(f"{home.resolve()}.zones") / f"run-perf-{round_}")
        job = NodeJob(
            run_id=zone.root.name, node_id="many", iteration=0, partition=None, attempt=1,
            memo_key="m", idempotency_key="k", node_definition={"type": "script"}, inputs=None,
            now=None, workspace=str(zone.root),
        )  # fmt: skip
        overlay = zone.open(job)
        for n in range(100):
            (overlay.path / "out").mkdir(exist_ok=True)
            (overlay.path / "out" / f"{n}.json").write_text(json.dumps({"n": n}) * 20)
        declared = [OutputFile(path="out/*.json")]
        began = time.perf_counter()
        done = zone.commit(job, overlay, declared, (), {})
        zone.finish(done)
        timings.append((time.perf_counter() - began) * 1000)
        if len(done.sha256) != 100:
            log.check("all 100 files committed", False, len(done.sha256))
    log(f"commit of 100 declared files, ms per run: {[round(t, 1) for t in timings]}")
    log(f"PERF median {statistics.median(timings):.1f} ms, max {max(timings):.1f} ms")


LANES: Final = {"overlays": overlays, "lifetime": lifetime, "sweep": sweep, "perf": perf}


def main() -> int:
    lane = sys.argv[1] if len(sys.argv) > 1 else "overlays"
    log = Log("sec2a", f"sec2a-{'e50' if lane == 'overlays' else lane}")
    LANES[lane](log)
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
