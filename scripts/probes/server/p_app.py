"""P-APP (AD-64): an app server started on Contabo from a bundle fetched by hash, and a volume
lease handed from the PC to Contabo with a snapshot and a restore.

Run it on the PC with no arguments. It builds a small fixture app, installs and starts it here,
writes the state its job reads, snapshots the instance and hands the lease to Contabo, copies the
bundle and the snapshot there over ssh, and then on Contabo fetches the bundle by hash, installs
it, restores the snapshot, takes the handed lease, starts the app and runs its job. Each half
prints its own PASS or FAIL line and the driver prints the last one.

The bundle's source is the PC store's `definitions/` folder, which is where a published pack's
image is content-addressed by hash; the Library artifact that wraps it is LIB4's, and this probe
runs before those routes exist.

    <repo python> scripts/probes/server/p_app.py
    <server python> p_app.py --server <app> <snapshot_id> <hash> <generation>
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

LANE = "/srv/qmx/bld/app2b"
SERVER = "root@qmx-server"
APP = "app2b-macro"
JOB = "daily.py"
REPO = Path(__file__).resolve().parents[3]
STORE = Path("D:/QMX-worktrees/qma-ship/build/evidence/app2b")

FIXTURE = {
    "server.py": '''"""The fixture app's MCP server: one tool that reads the bias this instance wrote."""

from __future__ import annotations

import json
from pathlib import Path

from fastmcp import FastMCP
from pydantic import JsonValue

mcp = FastMCP("app2b macro fixture")


@mcp.tool()
def bias() -> dict[str, JsonValue]:
    """Read the latest persisted daily bias."""
    return json.loads((Path("data") / "bias.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
''',
    "daily.py": '''"""The fixture app's job: read the state the PC wrote and say which machine ran this."""

from __future__ import annotations

import json
import platform
from pathlib import Path


def run() -> None:
    data = Path("data")
    state = json.loads((data / "bias.json").read_text(encoding="utf-8"))
    (data / "run.json").write_text(
        json.dumps({"host": platform.node(), "state": state}), encoding="utf-8"
    )
''',
    "app.toml": '''id = "app2b-macro"
name = "APP2b macro fixture"
version = "1.0.0"
risk = "shows"
kind = "headless"

[entrypoints]
mcp = "server.py"
jobs = ["daily.py"]

[suggested_trigger]
kind = "interval"
seconds = 86400

[capabilities]
network = []
data_reads = []

[operations.bias]
description = "Read the latest persisted daily bias."
''',
    "pyproject.toml": '''[project]
name = "app2b-macro-app"
version = "1.0.0"
requires-python = ">=3.14,<3.15"
dependencies = ["fastmcp==4.0.11"]

[tool.uv]
package = false

[tool.uv.workspace]
members = []
''',
}

RUN_SERVER = f"""#!/bin/bash
set -u
cd /srv/qmx/bld/app2b || exit 2
export HOME={LANE}/home
export UV_CACHE_DIR={LANE}/uv-cache
export UV_PYTHON_INSTALL_DIR={LANE}/python
export TMPDIR={LANE}/tmp
export PATH=/usr/local/bin:/usr/bin:/bin
export PYTHONPATH=$(find {LANE}/code -maxdepth 4 -type d -name src | tr '\\n' ':')
mkdir -p "$UV_CACHE_DIR" "$UV_PYTHON_INSTALL_DIR" "$TMPDIR"
exec {LANE}/env/bin/python {LANE}/p_app.py "$@"
"""


def say(ok: bool, line: str) -> bool:
    print(("PASS " if ok else "FAIL ") + line, flush=True)
    return ok


def fixture(root: Path) -> Path:
    """A fixture app whose dependencies install anywhere, with its lock resolved here."""
    root.mkdir(parents=True, exist_ok=True)
    for name, text in FIXTURE.items():
        (root / name).write_text(text, encoding="utf-8")
    lock = subprocess.run(
        ["uv", "lock", "--project", str(root)], capture_output=True, text=True, check=False
    )
    if lock.returncode:
        raise SystemExit(f"FAIL p_app fixture: uv lock failed: {lock.stderr[-400:]}")
    return root


def pc_half(work: Path) -> dict[str, object]:
    """Install, start and run the instance here, then snapshot it and hand its lease away."""
    from qmx_apps.manifest import Definition  # noqa: PLC0415
    from qmx_apps.supervisor import Supervisor  # noqa: PLC0415
    from qmx_apps.volume import VolumeLease  # noqa: PLC0415

    home = work / "pc"
    supervisor = Supervisor(home, placement="pc")
    source = fixture(work / "app")
    digest = Definition.load(source).hash
    supervisor.install(source, trust="first_party")
    started = supervisor.start(APP)
    say(started.get("status") == "running", f"p_app pc: app server started here from {digest[:12]}")
    data = home / "apps" / APP / "data"
    (data / "bias.json").write_text(
        json.dumps({"pair": "EURUSD", "bias": "long"}), encoding="utf-8"
    )
    ran = supervisor.run_job(APP, JOB)
    say(ran.get("job") == JOB, f"p_app pc: job {JOB} ran here before the move")
    moved = supervisor.snapshot_instance(APP, to="contabo")
    say(moved.files > 0, f"p_app pc: snapshot {moved.snapshot_id} holds {moved.files} files")
    try:
        VolumeLease(home, APP, holder="pc", expect=moved.lease)
    except Exception as error:  # noqa: BLE001 - the refusal is the assertion
        code = getattr(error, "code", "")
        say(
            code in {"lease_handed_over", "volume_busy"},
            f"p_app pc: the lease is no longer this machine's ({code})",
        )
    else:
        say(False, "p_app pc: this machine could take back a volume it handed away")
    return {
        "app": APP,
        "hash": digest,
        "snapshot_id": moved.snapshot_id,
        "folder": str(moved.folder),
        "generation": moved.generation,
    }


def ssh_key() -> str:
    return os.environ.get("QMX_SSH_KEY") or str(Path.home() / ".ssh" / "qmx_server")


def ssh(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ssh", "-i", ssh_key(), "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", SERVER, command],
        capture_output=True,
        text=True,
        check=False,
    )


def scp(source: Path, target: str) -> None:
    done = subprocess.run(
        ["scp", "-q", "-i", ssh_key(), str(source), f"{SERVER}:{target}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode:
        raise SystemExit(f"FAIL p_app: scp {source.name}: {done.stderr[-400:]}")


def server_half(work: Path, moved: dict[str, object]) -> bool:
    """The whole Contabo half, over ssh, as the unprivileged user."""
    archive = work / "move.tgz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(
            work / "pc" / "definitions" / str(moved["hash"]),
            arcname=f"definitions/{moved['hash']}",
        )
        tar.add(str(moved["folder"]), arcname="snapshot")
        # The head's own qmx_apps, so Contabo runs the code this probe is proving.
        tar.add(
            str(REPO / "qmx-agents/packages/qmx-apps/src/qmx_apps"),
            arcname="code/qmx-agents/packages/qmx-apps/src/qmx_apps",
        )
    for name, text in (
        ("move.tgz", None),
        ("p_app.py", Path(__file__).read_text(encoding="utf-8")),
        ("run-server.sh", RUN_SERVER),
    ):
        if name == "move.tgz":
            scp(archive, f"{LANE}/move.tgz")
        else:
            local = work / name
            local.write_text(text or "", encoding="utf-8", newline="\n")
            scp(local, f"{LANE}/{name}")
    arguments = " ".join(
        str(moved[key]) for key in ("app", "snapshot_id", "hash", "generation")
    )
    arguments = f"--server {arguments}"
    done = ssh(
        f"cd {LANE} && chown -R prbs:prbs {LANE} && "
        f"runuser -u prbs -- bash {LANE}/run-server.sh {arguments}"
    )
    print(done.stdout, end="", flush=True)
    if done.stderr.strip():
        print(done.stderr[-3000:], file=sys.stderr, flush=True)
    return done.returncode == 0 and "FAIL" not in done.stdout


def server_main(argv: list[str]) -> int:
    """On Contabo: fetch the bundle by hash, install, restore, start, and run the job here."""
    app, snapshot_id, digest, generation = (part.strip() for part in argv)
    lane = Path(LANE)
    for name in ("snapshot", "definitions"):
        shutil.rmtree(lane / name, ignore_errors=True)
    with tarfile.open(lane / "move.tgz") as tar:
        tar.extractall(lane, filter="data")
    # The tar carries this head's qmx_apps, so the import follows the extraction.
    from qmx_apps import bundle  # noqa: PLC0415
    from qmx_apps.supervisor import Supervisor  # noqa: PLC0415

    home = lane / "papp-home"
    shutil.rmtree(home, ignore_errors=True)
    supervisor = Supervisor(home, placement="contabo")
    folder = bundle.fetch(home, digest, [lane / "definitions"])
    ok = say(bundle.present(home, digest), f"p_app server: bundle {digest[:12]} fetched by hash")
    supervisor.install(folder, trust="first_party", expected_id=app)
    restored = supervisor.restore_instance(app, snapshot_id, folder=lane / "snapshot")
    ok &= say(
        str(restored["generation"]) == generation,
        f"p_app server: lease generation {generation} taken from the handover",
    )
    started = supervisor.start(app)
    ok &= say(started.get("status") == "running", "p_app server: app server started here")
    supervisor.run_job(app, JOB)
    ran = json.loads((home / "apps" / app / "data" / "run.json").read_text(encoding="utf-8"))
    ok &= say(
        ran["state"] == {"pair": "EURUSD", "bias": "long"},
        "p_app server: the job read the state the PC wrote",
    )
    ok &= say(str(ran["host"]).startswith("vmi"), f"p_app server: the job ran on {ran['host']}")
    supervisor.stop(app)
    return 0 if ok else 1


def run_job_main(argv: list[str]) -> int:
    """On Contabo: start the moved instance here and run one job in it, as the home would."""
    app = argv[0].strip()
    from qmx_apps.supervisor import Supervisor  # noqa: PLC0415

    supervisor = Supervisor(Path(LANE) / "papp-home", placement="contabo")
    supervisor.start(app)
    try:
        ran = supervisor.run_job(app, JOB)
    finally:
        supervisor.stop(app)
    print(json.dumps(ran))
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--server":
        return server_main(argv[1:])
    if argv and argv[0] == "--job":
        return run_job_main(argv[1:])
    work = Path(tempfile.mkdtemp(prefix="app2b-papp-", dir=os.environ.get("TMP", "D:/Temp")))
    moved = pc_half(work)
    if not server_half(work, moved):
        say(False, "P-APP: the Contabo half did not pass")
        return 1
    say(
        True,
        f"P-APP: app server started on Contabo from bundle {str(moved['hash'])[:12]} by hash, "
        f"lease generation {moved['generation']} handed from pc to contabo with a snapshot and a "
        "restore",
    )
    store = Path(os.environ.get("QMX_EVIDENCE_DIR", STORE))
    store.mkdir(parents=True, exist_ok=True)
    (store / "owner-papp-move.json").write_text(json.dumps(moved, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
