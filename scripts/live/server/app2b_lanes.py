"""APP2b's owner lanes: the regression pair, P-APP, the move with its state, and the placement
wait. Plus the move's timing for a 100 MB volume.

Run from the worktree root:

    <repo python> scripts/live/server/app2b_lanes.py 1 2 3 4

Each lane writes its own log to the store's `evidence/app2b/` and prints one PASS or FAIL line, so
a lane's log is never the shell's own redirect. Lane 3 also writes the perf line.
"""

from __future__ import annotations

import hashlib
import asyncio
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
STORE = Path(os.environ.get("QMX_EVIDENCE_DIR", "D:/QMX-worktrees/qma-ship/build/evidence/app2b"))
PARENT = "0ab06fe283ce2ef2fd4211db01d83106ca6a1dcb"
PARENT_TREE = Path("D:/Temp/app2b-parent")
SUITES = {"qmx-apps": "qmx-agents/packages/qmx-apps", "qmx-engine": "qmx-agents/packages/qmx-engine"}


sys.path.insert(0, str(REPO / "scripts/live/server"))
import p_app  # noqa: E402

APP = p_app.APP
LANE = p_app.LANE
BLOB_MB = 100


def run(name: str, body: Callable[[list[str]], bool]) -> bool:
    """Run one lane with its output both printed and saved to its own log."""
    lines: list[str] = []
    console = sys.stdout

    class Echo(io.StringIO):
        def write(self, text: str) -> int:
            lines.append(text)
            console.write(text)
            return len(text)

    started = time.monotonic()
    with contextlib.redirect_stdout(Echo()):
        try:
            ok = body(lines)
        except Exception as error:  # noqa: BLE001 - a lane never dies silently
            print(f"FAIL {name}: {type(error).__name__}: {error}")
            ok = False
    seconds = round(time.monotonic() - started, 1)
    log = STORE / f"owner-app2b-{name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("".join(lines) + f"\n--- lane {name} took {seconds}s ---\n", encoding="utf-8")
    print(f"{'PASS' if ok else 'FAIL'} lane {name} ({seconds}s) log: {log}")
    return ok


def pytest_failures(tree: Path, package: str) -> tuple[set[str], str]:
    """The failing test ids of one package in one tree, and its tail."""
    env = dict(os.environ)
    env.update({"TMP": "D:/Temp", "TEMP": "D:/Temp", "UV_CACHE_DIR": "D:/Caches/uv"})
    done = subprocess.run(
        [
            str(tree / "qmx-agents/.venv/Scripts/python.exe"),
            "-m",
            "pytest",
            "tests",
            "-q",
            "-n",
            "2",
            "-p",
            "no:cacheprovider",
        ],
        cwd=tree / SUITES[package],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    failed = {
        line.split()[1]
        for line in done.stdout.splitlines()
        if line.startswith("FAILED") and len(line.split()) > 1
    }
    return failed, done.stdout[-1200:]


def lane_1(_: list[str]) -> bool:
    """The qmx-apps and qmx-engine suites at the parent and at the head, compared."""
    if not PARENT_TREE.exists():
        add = subprocess.run(
            ["git", "worktree", "add", "--detach", str(PARENT_TREE), PARENT],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        if add.returncode:
            print(f"FAIL lane 1: worktree add: {add.stderr[-400:]}")
            return False
        sync = subprocess.run(
            ["uv", "sync", "--frozen", "--all-packages", "--all-groups"],
            cwd=PARENT_TREE / "qmx-agents",
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "UV_CACHE_DIR": "D:/Caches/uv", "TMP": "D:/Temp", "TEMP": "D:/Temp"},
        )
        print(f"parent sync exit {sync.returncode}: {sync.stderr[-300:]}")
    ok = True
    for package in SUITES:
        parent_failed, parent_tail = pytest_failures(PARENT_TREE, package)
        head_failed, head_tail = pytest_failures(REPO, package)
        new = sorted(head_failed - parent_failed)
        print(f"--- {package} parent fails {len(parent_failed)}, head fails {len(head_failed)}")
        print("parent tail:", parent_tail.splitlines()[-1] if parent_tail.splitlines() else "")
        print("head tail  :", head_tail.splitlines()[-1] if head_tail.splitlines() else "")
        print(f"head fails that the parent passed: {new}")
        ok &= not new
    return ok


def lane_2(_: list[str]) -> bool:
    """P-APP, the app server on Contabo from a bundle by hash and the handed lease."""
    done = subprocess.run(
        [sys.executable, str(REPO / "scripts/live/server/p_app.py")],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO,
    )
    print(done.stdout)
    if done.stderr.strip():
        print(done.stderr[-1500:])
    return done.returncode == 0 and "PASS P-APP" in done.stdout


def blob(path: Path, megabytes: int) -> str:
    block = os.urandom(1024 * 1024)
    digest = hashlib.sha256()
    with path.open("wb") as file:
        for _ in range(megabytes):
            file.write(block)
            digest.update(block)
    return digest.hexdigest()


def lane_3(lines: list[str]) -> bool:
    """Move the fixture instance to Contabo with its state, and time a 100 MB volume."""
    from qmx_apps.manifest import Definition  # noqa: PLC0415
    from qmx_apps.supervisor import Supervisor  # noqa: PLC0415

    work = Path(tempfile.mkdtemp(prefix="app2b-move-", dir="D:/Temp"))
    home = work / "pc"
    supervisor = Supervisor(home, placement="pc")
    supervisor.install(p_app.fixture(work / "app"), trust="first_party")
    digest = Definition.load(p_app.fixture(work / "app")).hash
    supervisor.start(APP)
    data = home / "apps" / APP / "data"
    (data / "bias.json").write_text(json.dumps({"pair": "EURUSD", "bias": "long"}))
    (data / "run.json").unlink(missing_ok=True)
    blobs = home / "apps" / APP / "blobs"
    blobs.mkdir(parents=True, exist_ok=True)
    wanted = blob(blobs / "big.bin", BLOB_MB)
    print(f"volume: {BLOB_MB} MB blob written under the app's volume")

    started = time.monotonic()
    moved = supervisor.snapshot_instance(APP, to="contabo")
    snapshot_seconds = round(time.monotonic() - started, 2)
    print(f"snapshot: {moved.files} files in {snapshot_seconds}s")
    payload = {
        "app": APP,
        "hash": digest,
        "snapshot_id": moved.snapshot_id,
        "folder": str(moved.folder),
        "generation": moved.generation,
    }
    ok = p_app.server_half(work, payload)
    move_seconds = round(time.monotonic() - started, 2)
    print(f"PERF move_seconds={move_seconds} volume_mb={BLOB_MB} snapshot_seconds={snapshot_seconds}")
    remote = p_app.ssh(
        f"sha256sum {LANE}/papp-home/apps/{APP}/blobs/big.bin 2>&1 | cut -d' ' -f1"
    )
    got = remote.stdout.strip()
    print(f"blob: pc {wanted[:16]} contabo {got[:16]}")
    ok &= got == wanted
    ran = p_app.ssh(f"cat {LANE}/papp-home/apps/{APP}/data/run.json")
    state = json.loads(ran.stdout or "{}")
    print(f"state on contabo: {json.dumps(state)}")
    ok &= state.get("state") == {"pair": "EURUSD", "bias": "long"}
    ok &= str(state.get("host", "")).startswith("vmi")
    lines.append(f"PERF move_seconds={move_seconds} volume_mb={BLOB_MB}\n")
    (STORE / "owner-app2b-perf.json").write_text(
        json.dumps(
            {
                "metric": "move time for a 100 MB volume",
                "seconds": move_seconds,
                "snapshot_seconds": snapshot_seconds,
                "volume_mb": BLOB_MB,
                "rule": "no fail rule (Override 4); recorded for the trail",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ok


def lane_4(_: list[str]) -> bool:
    """A state: instance operation with the home unreachable waits placement, then resumes."""
    from qmx_engine.nodes.app_op import AppOp, Placements  # noqa: PLC0415
    from qmx_engine.nodes.base import JsonObject, NodeJob, Ok, Waiting  # noqa: PLC0415

    away = {"on": True}

    def reachable(placement: str) -> bool:
        """A real connection probe: an unroutable address while the home is away, else Contabo."""
        host = "203.0.113.7" if away["on"] else "root@qmx-server"
        probe = subprocess.run(
            ["ssh", "-i", p_app.ssh_key(), "-o", "BatchMode=yes", "-o", "ConnectTimeout=3", host, "true"],
            capture_output=True,
            text=True,
            check=False,
        )
        return probe.returncode == 0

    def door(placement: str, app: str, name: str, pin: object, profile: object) -> object:
        done = p_app.ssh(f"runuser -u prbs -- bash {LANE}/run-server.sh --job {app}")
        if done.returncode:
            raise RuntimeError(done.stderr[-300:])
        return json.loads(done.stdout.strip().splitlines()[-1])

    def run_job(app: str, name: str) -> object:
        raise RuntimeError(f"{app} must not run here; it is homed on contabo")

    placements = Placements(
        state_of=lambda app, op: "instance",
        home_of=lambda app: "contabo",
        here="pc",
        reachable=reachable,
        remote=door,
    )
    node = AppOp(run_job, placements=placements)
    definition: JsonObject = {"type": "app_op", "parameters": {"app": APP, "job": p_app.JOB}}
    job = NodeJob(
        run_id="r",
        node_id="a",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="k",
        node_definition=definition,
        inputs={},
        now=None,
    )
    first = asyncio.run(node.run(job))
    print(f"away: {type(first).__name__} reason={getattr(first, 'reason', '')}")
    ok = isinstance(first, Waiting) and first.reason == "placement"
    away["on"] = False
    print("home returns: reachability probe now answers", reachable("contabo"))
    second = asyncio.run(node.run(job))
    print(f"resumed: {type(second).__name__} {getattr(second, 'outputs', {})}")
    ok &= isinstance(second, Ok)
    outputs = second.outputs.get("main") if isinstance(second, Ok) else None
    ok &= isinstance(outputs, dict) and str(outputs.get("job")) == p_app.JOB
    return ok


LANES: dict[str, Callable[[list[str]], bool]] = {
    "1": lane_1,
    "2": lane_2,
    "3": lane_3,
    "4": lane_4,
}


def main(argv: list[str]) -> int:
    wanted = argv or list(LANES)
    results = [run(name, LANES[name]) for name in wanted]
    print("LANES " + " ".join(f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in zip(wanted, results)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
