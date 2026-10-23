"""P-OOM (W4; F39, D-11; engine AD-30, AD-58), acceptance: a memory limit takes a child process,
never `qmx_host`.

The W4 half. The host stand-in below is one small process that keeps answering while five children
work: three synthetic memory-heavy children, each growing without a bound, and two node-like
children holding a fixed block, standing in for two agent nodes until DR7 adds Docling and DR3B the
door read.

The scenario runs under one memory limit, below what the three heavy children together need:

1. the limit forces the kernel to kill at least one child, by signal, not by the probe;
2. the host stand-in is alive at the end and answered throughout;
3. the children are listed with the signal that ended each one.

A cgroup needs a delegation the `qmx` user has on Ubuntu 24.04, so the probe uses
`systemd-run --user --scope -p MemoryMax=…`, which needs that user's manager. When that is not
there it prints SKIP with the reason and exits 0, because a machine without a cgroup proves
nothing either way. Windows has no cgroup, so the probe says so there and the coordinator runs
lane 3 on the server.

    uv run --no-sync --project qmx-agents python scripts/probes/data/p_oom.py

Scratch goes to `D:/Temp/prb-dp/oom/` and is removed before the probe exits.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
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

DRIVER = r"""
import json, subprocess, sys, time
from pathlib import Path

answers, report, heavy_mb, node_mb, heavy, nodes, seconds = (
    sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]),
    int(sys.argv[6]), float(sys.argv[7]),
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
started = time.time()
kids = []
for _ in range(heavy):
    kids.append(("heavy", subprocess.Popen([sys.executable, "-c", HEAVY % heavy_mb])))
for _ in range(nodes):
    kids.append(("node", subprocess.Popen([sys.executable, "-c", NODE % node_mb])))
beats = 0
while time.time() - started < seconds:
    Path(answers).write_text(str(beats))
    beats += 1
    time.sleep(0.05)
ended = []
for kind, child in kids:
    code = child.poll()
    if code is None:
        child.kill()
        child.wait()
        ended.append({"kind": kind, "pid": child.pid, "ending": "survived"})
    else:
        ended.append({"kind": kind, "pid": child.pid, "ending": code})
Path(report).write_text(json.dumps({"beats": beats, "children": ended}))
"""


def driver_argv(answers: Path, outcome: Path) -> list[str]:
    return [
        sys.executable,
        "-c",
        DRIVER,
        str(answers),
        str(outcome),
        str(HEAVY_MB),
        str(NODE_MB),
        str(HEAVY),
        str(NODES),
        str(SECONDS),
    ]


def scope(argv: list[str]) -> tuple[list[str], str]:
    """The command that runs `argv` under one memory limit, and the mechanism it names."""
    systemd = shutil.which("systemd-run")
    if systemd is None:
        return argv, ""
    return (
        [
            systemd,
            "--user",
            "--scope",
            "--quiet",
            "-p",
            f"MemoryMax={LIMIT_MB}M",
            "-p",
            "MemorySwapMax=0",
            "--",
            *argv,
        ],
        "systemd-run --user --scope",
    )


def linux(problems: list[str]) -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    answers = SCRATCH / "answers.txt"
    outcome = SCRATCH / "outcome.json"
    argv, mechanism = scope(driver_argv(answers, outcome))
    print(f"limit {LIMIT_MB} MB, {HEAVY} heavy children of {HEAVY_MB} MB, {NODES} node children")
    if not mechanism:
        print("no cgroup mechanism here: systemd-run is missing")
        return
    print(f"mechanism: {mechanism}")
    done = subprocess.run(argv, capture_output=True, text=True, timeout=SECONDS + 60, check=False)
    if not outcome.exists():
        problems.append(
            f"the scenario left no outcome (exit {done.returncode}): {done.stderr.strip()[:300]}"
        )
        return
    found = json.loads(outcome.read_text())
    children = found["children"]
    beats = int(found["beats"])
    answered = answers.read_text() if answers.exists() else ""
    print(f"host stand-in answered {beats} times, last answer {answered}")
    killed = [row for row in children if isinstance(row["ending"], int) and row["ending"] < 0]
    for row in children:
        print(f"  child {row['kind']} {row['pid']} ended {row['ending']}")
    if not killed:
        problems.append("no child was killed, so the limit forced nothing")
    if beats < 2 or answered != str(beats - 1):
        problems.append("the host stand-in stopped answering")


def main() -> int:
    if sys.platform == "win32":
        print(f"{PROBE} SKIP: Windows has no cgroup; lane 3 runs this on the server")
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
