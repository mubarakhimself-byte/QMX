"""C-33 reproducer: enable a fixture app with a suggested trigger again and again on a control
service and engine door wired as `qmx_host` wires them, and dump every thread's stack when one
enable outlasts its bound.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../tools/lanes/app_enable_hang.py --log <file> [--runs 200] [--timeout 30]`

Each run stops the app, then enables it: the first enable drafts, test-runs, publishes and creates
the trigger, every later one starts the app and enables the existing trigger. The app's heartbeat
writes an app event four times a second while it runs, so every enable races those events. One
throwaway QMX folder under `D:/Temp` holds everything and is removed at the end. No model, no key.
Exit 0 when every run finished inside its bound, 1 otherwise. The first hang ends the lane: the
dump goes to the log, the app processes this script started are stopped by PID, and the process
exits, because a deadlocked service cannot be closed.
"""

from __future__ import annotations

import argparse
import asyncio
import faulthandler
import os
import shutil
import stat
import statistics
import sys
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Final, TextIO

REPO: Final = Path(__file__).resolve().parents[2]
APP: Final = "exchange-status"
JOB: Final = (
    "from pathlib import Path\n"
    "def run():\n"
    "    path = Path('data/job.txt')\n"
    "    path.write_text(str(int(path.read_text()) + 1) if path.exists() else '1')\n"
)
TRIGGER: Final = '\n[suggested_trigger]\nkind = "interval"\nseconds = 60\n'


class Log:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.file: TextIO = path.open("w", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped, flush=True)
        self.file.write(stamped + "\n")
        self.file.flush()

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= ok


def writable(remove: Callable[..., Any], path: str, _: object) -> None:
    os.chmod(path, stat.S_IWRITE)
    remove(path)


def fixture_app(root: Path) -> Path:
    target = root / "app-source"
    shutil.copytree(
        REPO / "examples/apps" / APP, target, ignore=shutil.ignore_patterns(".venv", "__pycache__")
    )
    shutil.copyfile(
        REPO / "qmx-agents/packages/qmx-apps/tests/fixture_server.py", target / "server.py"
    )
    (target / "job.py").write_text(JOB, encoding="utf-8")
    manifest = target / "app.toml"
    text = manifest.read_text(encoding="utf-8").replace(
        'mcp = "server.py"', 'mcp = "server.py"\njobs = ["job.py"]'
    )
    manifest.write_text(text + TRIGGER, encoding="utf-8")
    return target


@contextmanager
def engine(control: Any) -> Iterator[Any]:
    """The engine door on its own loop thread with the host's Library adapter, acting as the
    operator, as `qmx_host` opens it."""
    from qmx_engine.control_door import EngineDoor  # noqa: PLC0415
    from qmx_engine.service.context import OPERATOR  # noqa: PLC0415
    from qmx_library.adapter import EngineLibraryAdapter  # noqa: PLC0415

    opened: list[Any] = []
    ready, stop = threading.Event(), threading.Event()

    async def main() -> None:
        library = EngineLibraryAdapter(control.library.store)
        async with EngineDoor.open(control, library=library, principal=lambda: OPERATOR) as door:
            opened.append(door)
            ready.set()
            while not stop.is_set():
                await asyncio.sleep(0.05)

    thread = threading.Thread(target=asyncio.run, args=(main(),), name="engine-loop")
    thread.start()
    if not ready.wait(60):
        raise SystemExit("FAIL the engine door did not open in 60 s")
    try:
        yield opened[0]
    finally:
        stop.set()
        thread.join(60)


def stop_children(log: Log) -> None:
    import psutil  # noqa: PLC0415

    for child in psutil.Process(os.getpid()).children(recursive=True):
        log(f"stopping child pid {child.pid} {child.name()}")
        child.kill()


def bounded(work: Callable[[], object], seconds: float) -> tuple[str, float]:
    """Run `work` on its own thread: `ok`, `error: ...` or `timeout`, with elapsed ms."""
    outcome: list[str] = []

    def target() -> None:
        try:
            work()
            outcome.append("ok")
        except Exception as error:  # noqa: BLE001
            outcome.append(f"error: {type(error).__name__}: {error}")

    started = time.perf_counter()
    thread = threading.Thread(target=target, name="enable", daemon=True)
    thread.start()
    thread.join(seconds)
    elapsed = (time.perf_counter() - started) * 1000
    return (outcome[0] if outcome else "timeout"), elapsed


def lane(log: Log, root: Path, runs: int, seconds: float) -> None:
    from qmx_control import ControlService  # noqa: PLC0415

    control = ControlService(root / "qmx")
    control.apps_create(str(fixture_app(root)), trust="first_party")
    log(f"pid {os.getpid()} home {control.home}")
    enabled: list[float] = []
    with engine(control):

        def once() -> None:
            control.apps_stop(APP)
            found = control.apps_enable(APP)
            if not isinstance(found.get("trigger"), dict):
                raise RuntimeError(f"enable answered no trigger: {found}")

        for run in range(1, runs + 1):
            outcome, elapsed = bounded(once, seconds)
            if outcome == "timeout":
                log(f"FAIL run {run} did not finish in {seconds:.0f} s; every thread's stack:")
                faulthandler.dump_traceback(log.file, all_threads=True)
                log.file.flush()
                log.passed = False
                stop_children(log)
                log("FAIL")
                os._exit(1)
            if outcome != "ok":
                log.check(f"run {run} answered", False, outcome)
                continue
            enabled.append(elapsed)
            if run % 20 == 0:
                log(f"run {run} ok, {elapsed:.0f} ms")
        triggers = control.workflow_triggers_list(f"{APP}-schedule")
    control.close()
    log.check(
        f"{runs} enables finished inside {seconds:.0f} s each",
        len(enabled) == runs,
        f"{len(enabled)} of {runs}",
    )
    log.check(
        "exactly one enabled trigger at the end",
        [(t["kind"], t["enabled"]) for t in triggers] == [("interval", True)],
        [(t["kind"], t["enabled"]) for t in triggers],
    )
    if enabled:
        log(
            f"PERF ms per enable: first {enabled[0]:.0f}, median of the rest "
            f"{statistics.median(enabled[1:] or enabled):.0f}, max {max(enabled):.0f}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    log = Log(args.log)
    root = Path("D:/Temp") / f"c33-hang-{os.getpid()}"
    root.mkdir(parents=True)
    try:
        lane(log, root, args.runs, args.timeout)
    finally:
        shutil.rmtree(root, onexc=writable, ignore_errors=False)
    log("PASS" if log.passed else "FAIL")
    return 0 if log.passed else 1


if __name__ == "__main__":
    sys.exit(main())
