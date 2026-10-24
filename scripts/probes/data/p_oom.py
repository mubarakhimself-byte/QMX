"""P-OOM (W4; F39, D-11; engine AD-30, AD-58), acceptance: a memory limit takes a child process,
never `qmx_host`.

The W4 half. Two processes, and which one is where is the point:

* **The observer** is this probe. It sits outside every limit: it creates the scope, watches the
  children through `/proc`, and reads the host stand-in's answers. If the kernel killed the observer
  the probe could never say what happened, which is exactly how its first version failed on the
  server: systemd stops a scope whose member was OOM-killed, and that SIGTERM took the driver with
  it before it could write a result.
* **The host stand-in** is one small process inside the scope that answers every 50 ms and starts
  the children: three synthetic memory-heavy children, each growing without a bound, and two
  node-like children holding a fixed block, standing in for two agent nodes until DR7 adds Docling
  and DR3B the door read. Its answers stand in for the Library and the door.

The scope takes `MemoryMax` below what the three heavy children together need, `MemorySwapMax=0`
so the kernel must free memory rather than swap, and `OOMPolicy=continue` so a kill does not stop
the scope and take the rest with it.

PASS is 55's line: the kernel kills a child by signal, never the host, and the host stand-in still
answers after that kill. FAIL: the host stand-in was killed, or it stopped answering, or nothing
was killed at all. The probe does not tune the limit to make anything pass.

The host stand-in has to sit inside the scope, or "the host is killed" could never be observed;
that is the one thing this shape departs from the scope holding only the children.

    uv run --no-sync --project qmx-agents python scripts/probes/data/p_oom.py

Scratch goes to `D:/Temp/prb-dp/oom/` and is removed before the probe exits. Windows has no cgroup,
so the probe prints SKIP there and the server lane is where it runs.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROBE = "P-OOM"
SCRATCH = Path(os.environ.get("QMX_PROBE_SCRATCH", "D:/Temp/prb-dp")) / "oom"
LIMIT_MB = 256
"""One limit below the three heavy children's combined need, and above one of them."""
HEAVY_MB = 128
"""What one synthetic heavy child holds before the three together have outgrown the limit."""
NODE_MB = 32
"""What one node-like child holds while it works."""
HEAVY = 3
NODES = 2
SECONDS = 25.0
POLL_S = 0.1
BEAT_S = "0.05"
PROC = Path("/proc")

HELPER = r"""
import json, os, subprocess, sys, time
from pathlib import Path

answers = Path(sys.argv[1])
outcome = Path(sys.argv[2])
heavy_mb, node_mb, heavy, nodes, seconds, beat_s = (
    int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]),
    float(sys.argv[7]), float(sys.argv[8]),
)
HEAVY = (
    "import time\n"
    "block = bytearray(%d * 1024 * 1024)\n"
    "held = []\n"
    "while True:\n"
    "    held.append(bytearray(16 * 1024 * 1024))\n"
    "    time.sleep(0.005)\n"
)
NODE = "import time\nblock = bytearray(%d * 1024 * 1024)\nwhile True:\n    time.sleep(0.05)\n"
kids = []
for _ in range(heavy):
    kids.append(("heavy", subprocess.Popen([sys.executable, "-c", HEAVY % heavy_mb])))
for _ in range(nodes):
    kids.append(("node", subprocess.Popen([sys.executable, "-c", NODE % node_mb])))
Path(str(answers) + ".pids").write_text(
    json.dumps({"host": os.getpid(), "children": [{"kind": k, "pid": c.pid} for k, c in kids]})
)
started = time.time()
beats = 0
while time.time() - started < seconds:
    answers.write_text(str(beats))
    beats += 1
    time.sleep(beat_s)
ended = []
for kind, child in kids:
    code = child.poll()
    if code is None:
        child.kill()
        child.wait()
        ended.append({"kind": kind, "pid": child.pid, "ending": "survived"})
    else:
        ended.append({"kind": kind, "pid": child.pid, "ending": code})
answers.write_text(str(beats))
outcome.write_text(json.dumps({"beats": beats, "host": os.getpid(), "children": ended}))
"""


def helper_argv(answers: Path, outcome: Path) -> list[str]:
    return [
        sys.executable,
        "-c",
        HELPER,
        str(answers),
        str(outcome),
        str(HEAVY_MB),
        str(NODE_MB),
        str(HEAVY),
        str(NODES),
        str(SECONDS),
        BEAT_S,
    ]


def scope(argv: list[str], unit: str) -> tuple[list[str], str]:
    """The command that runs `argv` inside one memory limit, and the mechanism it names."""
    systemd = shutil.which("systemd-run")
    if systemd is None:
        return argv, ""
    return (
        [
            systemd,
            "--user",
            "--scope",
            "--quiet",
            f"--unit=qmx-po-{unit}",
            "-p",
            f"MemoryMax={LIMIT_MB}M",
            "-p",
            "MemorySwapMax=0",
            "-p",
            "OOMPolicy=continue",
            "--",
            *argv,
        ],
        "systemd-run --user --scope",
    )


def read_text(path: Path) -> str:
    try:
        return path.read_text()
    except OSError:
        return ""


def alive(pid: int) -> bool:
    """Whether a process is still running: a killed child of the stand-in stays a zombie until the
    stand-in reaps it at the end, so its `/proc` entry alone would go on saying it is alive."""
    try:
        stat = (PROC / str(pid) / "stat").read_text()
    except OSError:
        return False
    return stat.rsplit(") ", 1)[-1][:1] != "Z"


def pids_of(path: Path) -> dict[int, str]:
    try:
        found = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return {int(row["pid"]): str(row["kind"]) for row in found.get("children", [])}


def linux(problems: list[str]) -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    answers = SCRATCH / "answers.txt"
    outcome = SCRATCH / "outcome.json"
    listing = SCRATCH / "answers.txt.pids"
    for stale in (answers, outcome, listing):
        stale.unlink(missing_ok=True)
    argv, mechanism = scope(helper_argv(answers, outcome), str(os.getpid()))
    print(f"limit {LIMIT_MB} MB, {HEAVY} heavy children of {HEAVY_MB} MB, {NODES} node children")
    if not mechanism:
        print("no cgroup mechanism here: systemd-run is missing")
        return
    print(f"mechanism: {mechanism}, OOMPolicy=continue")
    started = time.time()
    driver = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    children: dict[int, str] = {}
    death: tuple[float, int, str] | None = None
    beats_at_death = -1
    while driver.poll() is None and time.time() - started < SECONDS + 60:
        children = pids_of(listing) or children
        for pid, kind in children.items():
            if death is None and not alive(pid):
                death = (time.time() - started, pid, kind)
                beats_at_death = int(read_text(answers) or 0)
        time.sleep(POLL_S)
    _, stderr = driver.communicate(timeout=30)
    found = read_text(outcome)
    final_beats = int(read_text(answers) or 0)
    print(f"host stand-in answered {final_beats} times, driver ended {driver.returncode}")
    if death is not None:
        at, pid, kind = death
        print(f"first child to go: {kind} {pid} at {at:.1f} s, answers then {beats_at_death}")
    else:
        print("no child left the table while the driver ran")
    if not found:
        problems.append(
            f"the scope left no outcome (driver exit {driver.returncode}): {stderr.strip()[-300:]}"
        )
        return
    reading = json.loads(found)
    for row in reading["children"]:
        print(f"  child {row['kind']} {row['pid']} ended {row['ending']}")
    if driver.returncode < 0:
        problems.append(f"the host stand-in was killed by signal {-driver.returncode}")
    killed = [
        row for row in reading["children"] if isinstance(row["ending"], int) and row["ending"] < 0
    ]
    if not killed:
        problems.append("no child ended by a signal, so the limit forced nothing")
    if death is not None and final_beats <= beats_at_death:
        problems.append("the host stand-in stopped answering at the kill")


def main() -> int:
    if sys.platform == "win32":
        print(f"{PROBE} SKIP: Windows has no cgroup; the server lane runs this")
        return 0
    problems: list[str] = []
    try:
        linux(problems)
    finally:
        shutil.rmtree(SCRATCH.parent, ignore_errors=True)
    for problem in problems:
        print(f"  problem: {problem}")
    if problems:
        print(f"{PROBE} FAIL")
        return 1
    print(f"{PROBE} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
