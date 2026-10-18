"""EP7 lane 3 (E4 on an external step): the engine process is killed while a script node marked
`irreversible_external` runs, then the run is resumed by a fresh engine process.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e04_unknown_outcome.py`
Writes `evidence/ep7/<ENGINE_LOG_PREFIX>ep7-e04.log`. The step only appends a line to a file outside
the run; nothing leaves the PC. The engine's pid is read from the ledger's writer lock, so the kill
hits the engine itself and not the venv's launcher, and leaves the step's process running, as a
crash would. No model and no ship home.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Final

from common import Log, throwaway_home
from ep2_lanes import AGENTS, clean_env
from qmx_engine.ledger.store import Reader, ledger_path
from x07_nodes import ENGINE, alive, cli, edge, events, node, of, write_folder

POST: Final = """
    import os, time
    from pathlib import Path
    with Path(r"MARKS").open("a") as marks:
        marks.write(f"sent {os.getpid()}\\n")
    time.sleep(120)
"""
WAIT_S: Final = 60.0


def wait_for(what: str, ready: object, log: Log) -> None:
    deadline = time.monotonic() + WAIT_S
    while not ready():  # type: ignore[operator]
        if time.monotonic() > deadline:
            raise SystemExit(f"BLOCKED: {what} did not happen in {WAIT_S:.0f} s")
        time.sleep(0.1)
    log(f"{what}")


def kill(pid: int) -> None:
    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, check=False)  # noqa: S607


def main() -> int:
    log = Log("ep7", "ep7-e04")
    home = throwaway_home("ep7", "e04")
    marks = home / "marks.txt"
    post = node("post", "script", script="scripts/post.py")
    post["effect"] = "irreversible_external"
    root = write_folder(
        home / "wf-post",
        [node("start", "trigger"), post],
        {"start": {"main": [edge("post")]}},
        {"post": POST.replace("MARKS", str(marks))},
    )
    run_id = "run-ep7-e04"
    engine = subprocess.Popen(
        [*ENGINE, "run", str(root), "--home", str(home), "--run-id", run_id],
        cwd=AGENTS,
        env=clean_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    lock = Path(f"{ledger_path(home)}.lock")

    def started() -> bool:
        if not ledger_path(home).exists() or not marks.exists():
            return False
        with Reader.open(home) as reader:
            return bool(of(reader.events(run_id), "node_started", "post"))

    wait_for("the external step started and wrote its mark", started, log)
    writer = int(lock.read_text().strip())
    step = int(marks.read_text().split()[1])
    log(
        f"killing the engine pid {writer} (from the writer lock); the step pid {step} keeps running"
    )
    kill(writer)
    wait_for("the engine is gone", lambda: not alive(writer), log)
    engine.wait(timeout=30)
    code, lines = cli(log, "resume", run_id, "--home", str(home))
    found = events(home, run_id)
    gates = [e.data for e in found if e.kind == "gate_opened"]
    attempts = of(found, "node_started", "post")
    waiting = of(found, "node_waiting", "post")
    log(f"post attempts started: {len(attempts)}; gate items: {gates}")
    log(f"post's waiting event: {waiting}")
    log(f"marks file: {marks.read_text().splitlines()}")
    key = f"{run_id}:post:0:1"
    log.check(
        "the resumed run waits instead of retrying",
        code == 2 and "waiting" in lines[-1],
        lines[-1:],
    )
    log.check(
        "no automatic retry: one attempt of the external step", len(attempts) == 1, len(attempts)
    )
    log.check(
        "the step ran once in all", len(marks.read_text().splitlines()) == 1, marks.read_text()
    )
    log.check(
        "one irreversible_external item carries the idempotency key",
        [(g["category"], g["idempotency_key"]) for g in gates] == [("irreversible_external", key)],
        gates,
    )
    log.check(
        "the step's waiting event says effect_state unknown",
        [w.get("effect_state") for w in waiting] == ["unknown"],
        waiting,
    )
    code, lines = cli(log, "resume", run_id, "--home", str(home))
    found = events(home, run_id)
    again = (
        len(of(found, "node_started", "post")),
        len([e for e in found if e.kind == "gate_opened"]),
    )
    log.check(
        "an operator resume keeps the step waiting: still one attempt and one item",
        code == 2 and again == (1, 1),
        again,
    )
    if alive(step):
        kill(step)
        log(f"stopped the orphaned step pid {step}")
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
