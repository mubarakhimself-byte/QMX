from __future__ import annotations

import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest

LAUNCHER = Path(sys.executable).parent / (
    "qma-cli-launcher.exe" if os.name == "nt" else "qma-cli-launcher"
)

FAKE_CLI = """\
import json, os, subprocess, sys
from pathlib import Path

report, code, record = sys.argv[1], int(sys.argv[2]), sys.argv[3]
seen = {
    "qma": sorted(n for n in os.environ if n.upper().startswith("QMA_")),
    "record": json.loads(Path(record).read_text()) if Path(record).exists() else None,
}
Path(report).write_text(json.dumps(seen))
heavy = "chunks = []\\nwhile True: chunks.append(bytearray(64 * 2**20))"
children = []
for line in sys.stdin:
    if line.strip() == "ping":
        print("pong", flush=True)
    elif line.strip() == "heavy":
        subprocess.run([sys.executable, "-c", heavy])
    elif line.strip() == "heavy-self":
        chunks = []
        try:
            while True:
                chunks.append(bytearray(64 * 2**20))
        except MemoryError:
            os._exit(9)
    elif line.strip() == "child":
        sleeper = [sys.executable, "-c", "import time; time.sleep(600)"]
        children.append(subprocess.Popen(sleeper))
        print(children[-1].pid, flush=True)
sys.exit(code)
"""

Launch = Callable[..., subprocess.Popen[str]]


@pytest.fixture
def procs_dir(tmp_path: Path) -> Path:
    return tmp_path / "procs"


@pytest.fixture
def launch(tmp_path: Path, procs_dir: Path) -> Launch:
    """Starts `qma-cli-launcher` over a fake CLI that reports what it saw to
    `<tmp>/<chat>.seen.json`, answers `ping`, runs a memory-heavy child on `heavy`, allocates
    in its own process until refused on `heavy-self`, and on `child` starts a sleeping child
    and prints its pid."""
    script = tmp_path / "fake_cli.py"
    script.write_text(FAKE_CLI, encoding="utf-8")

    def start(chat: str, *, code: int = 0, cap: str = "", **inputs: str) -> subprocess.Popen[str]:
        env = {name: value for name, value in os.environ.items() if not name.startswith("QMA_")}
        env |= {
            "QMA_REAL_CLI": sys.executable,
            "QMA_CHAT_ID": chat,
            "QMA_PROC_DIR": str(procs_dir),
            "QMA_CAP": cap,
        } | inputs
        args = [str(script), str(tmp_path / f"{chat}.seen.json"), str(code)]
        args.append(str(procs_dir / f"{chat}.json"))
        return subprocess.Popen(
            [str(LAUNCHER), *args],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    return start


def wait_for(check: Callable[[], bool], seconds: float = 20.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(0.05)
    return check()
