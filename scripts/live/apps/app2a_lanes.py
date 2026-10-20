"""APP2a's live lanes: the regression comparison, E61, the contract gate and profiles (AD-19,
AD-64).

Each lane runs at the PR head on this machine, needs no model, and opens no ship home, so it takes
no lane lock. Homes and fixtures go under `--work` (the store's `homes/app2a-<lane>`); logs go to
`--evidence` as `owner-app2a-<lane>.log`.

    python app2a_lanes.py --lane 1 2 3 4

Lane 1. The touched suites with `-n 2` at the parent and at the head. PASS when the head fails
nothing the parent passes, except the pins named in `EXEMPT` (there are none today, and the lane
prints whichever it used).
Lane 2. E61: `e61_app_check.py`, on its own log.
Lane 3. The producer lands an output through its own operation, the consumer reads it, then the
producer publishes a changed `provides` schema. PASS when the landing reads fresh, the consumer
accepts it, and the publish fails naming the consumer.
Lane 4. Two profiles of one fixture app write data. PASS when each profile's file is apart, and a
run pins its profile and version.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Final

ROOT = Path(__file__).resolve().parents[3]
SELF = Path(__file__).resolve()
EVIDENCE: Final = Path("D:/QMX-worktrees/qma-ship/build/evidence/app2a")
WORK: Final = Path("D:/QMX-worktrees/qma-ship/build/homes/app2a")
PARENT: Final = Path("D:/Temp/app2a-check")
EXEMPT: Final = ()
"""Tests the head may fail that the parent passes: a test that pinned `emits` or the artifacts
database. Nothing pinned either, so any head-only failure is a lane 1 failure."""

APPS_SUITE: Final = ("tests",)
CONTROL_SUITE: Final = (
    "tests/test_catalog.py",
    "tests/test_app2a_catalog.py",
    "tests/test_context.py",
)
ENGINE_SUITE: Final = ("tests/test_app_op.py", "tests/test_app2a_app_op.py")

SERVER: Final = '''
from __future__ import annotations

import json
import os
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("APP2a fixture")


@mcp.tool()
def snapshot() -> dict[str, object]:
    """Land the observation the fixture declares, under the snapshot output."""
    data = {
        "observations": [
            {"exchange": "fixture", "status": "degraded", "observed_at": "2026-10-20T00:00:00Z"}
        ]
    }
    (Path(os.environ["QMX_DATA_DIR"]) / "snapshot.json").write_text(json.dumps(data))
    return {"output": "snapshot", "data": data}


@mcp.tool()
def mark(note: str) -> dict[str, object]:
    """Write this profile's own file, so two profiles are told apart on disk."""
    target = Path(os.environ["QMX_DATA_DIR"]) / "mark.txt"
    target.write_text(f"{os.environ.get('QMX_PROFILE', '')}:{note}", encoding="utf-8")
    return {"written": str(target), "profile": os.environ.get("QMX_PROFILE", "")}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
'''

MANIFEST: Final = """
id = "app2a-fixture"
name = "APP2a fixture"
version = "1.0.0"
risk = "shows"
kind = "headless"

[entrypoints]
mcp = "server.py"
jobs = ["job.py"]

[profiles]
schema = { type = "object" }

[operations.snapshot]
description = "Land the observation under the snapshot output."
approval = "read"
returns = "artifact"

[operations.mark]
description = "Write this profile's own file."
approval = "domain_write"

[provides.snapshot]
stale_after = 3600

[provides.snapshot.schema]
type = "object"
required = ["observations"]
additionalProperties = false

[provides.snapshot.schema.properties.observations]
type = "array"
"""


def log_of(evidence: Path, name: str) -> tuple[list[str], Path]:
    return [], evidence / f"owner-app2a-{name}.log"


def write(lines: list[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def python_of(checkout: Path) -> Path:
    return (
        checkout
        / "qmx-agents"
        / ".venv"
        / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    )


def run_suites(checkout: Path, packages: list[str]) -> dict[str, list[str]]:
    """Every touched suite's failing test ids, by package, at `checkout`. A suite file the
    checkout does not hold is named and left out: the parent cannot run a test this PR adds."""
    found: dict[str, list[str]] = {}
    for package, suite in (
        ("qmx-apps", APPS_SUITE),
        ("qmx-control", CONTROL_SUITE),
        ("qmx-engine", ENGINE_SUITE),
    ):
        if package not in packages:
            continue
        folder = checkout / "qmx-agents" / "packages" / package
        present = [item for item in suite if (folder / item).exists()]
        if not present:
            print(f"  {package}: nothing to run at {checkout.name}")
            found[package] = []
            continue
        result = subprocess.run(
            [
                str(python_of(checkout)),
                "-m",
                "pytest",
                *present,
                "-n",
                "2",
                "-q",
                "-p",
                "no:cacheprovider",
            ],
            cwd=folder,
            capture_output=True,
            text=True,
            check=False,
            timeout=3600,
        )
        found[package] = sorted(
            line.split(" - ", 1)[0].removeprefix("FAILED ").strip()
            for line in result.stdout.splitlines()
            if line.startswith("FAILED ")
        )
        found[package] = [f"{package}:{item}" for item in found[package]]
        tail = result.stdout.strip().splitlines()
        missing = sorted(set(suite) - set(present))
        note = f" (absent here: {', '.join(missing)})" if missing else ""
        print(f"  {package}: {tail[-1] if tail else 'no output'}{note}")
    return found


def lane_one(evidence: Path, work: Path, packages: list[str]) -> bool:
    chosen = ("qmx-apps", "qmx-control", "qmx-engine")
    name = (
        "regression"
        if list(packages) == list(chosen)
        else "regression-" + "-".join(package.removeprefix("qmx-") for package in packages)
    )
    lines, path = log_of(evidence, name)
    parent_root = globals()["PARENT"]
    if not (parent_root / "qmx-agents").is_dir():
        lines += [f"FAIL  no parent checkout at {parent_root}", "APP2A-LANE-1 FAIL"]
        write(lines, path)
        return False
    lines += ["# Lane 1: the touched suites at the parent and at the head (pytest -n 2)", ""]
    lines += [f"parent {parent_root}", f"head   {ROOT}", f"packages {', '.join(packages)}", ""]
    print("parent suites")
    parent = run_suites(parent_root, packages)
    print("head suites")
    head = run_suites(ROOT, packages)
    regressed: list[str] = []
    for package in parent:
        new = [item for item in head[package] if item not in parent[package]]
        kept = [item for item in new if not any(name in item for name in EXEMPT)]
        regressed += kept
        lines.append(
            f"{package}: parent fails {len(parent[package])}, head fails {len(head[package])}"
        )
        for item in parent[package]:
            lines.append(f"  parent FAIL {item}")
        for item in head[package]:
            lines.append(f"  head FAIL   {item}")
        lines.append(f"  head-only, not exempt: {len(kept)}")
        for item in kept:
            lines.append(f"    REGRESSED {item}")
    passed = not regressed
    lines += ["", f"APP2A-LANE-1 {'PASS' if passed else 'FAIL'}"]
    write(lines, path)
    return passed


def app_of(work: Path, *, profiles: bool) -> Path:
    folder = work / "definition"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    (folder / "server.py").write_text(SERVER, encoding="utf-8")
    (folder / "job.py").write_text(
        "import os\nfrom pathlib import Path\n\n\n"
        "def run():\n"
        "    Path(os.environ['QMX_DATA_DIR']).joinpath('job.txt').write_text("
        "'ran', encoding='utf-8')\n",
        encoding="utf-8",
    )
    table = (
        MANIFEST
        if profiles
        else MANIFEST.replace('[profiles]\nschema = { type = "object" }\n\n', "")
    )
    (folder / "app.toml").write_text(table, encoding="utf-8")
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(ROOT / "examples" / "apps" / "exchange-status" / name, folder / name)
    return folder


def library(store: Path) -> Any:
    """The Library sink the host closes over: one `artifact` object per landing, on `main`."""
    sys.path.insert(0, str(ROOT / "qmx-agents" / "packages" / "qmx-library" / "src"))
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_library.port import Draft  # noqa: PLC0415
    from qmx_library.principal import Principal  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415

    opened = Store.open(store, redactor=redact)
    operator = Principal.parse("operator")

    def land(landing: Any) -> str:
        item = f"{landing.app_id}-{landing.output}"
        head = opened.head(item, "main")
        draft = Draft(
            kind="artifact",
            item=item,
            title=f"{landing.app_id}: {landing.output}",
            fields=dict(landing.fields),
            blobs={"content": json.dumps(landing.data, sort_keys=True).encode()},
        )
        return opened.put(
            operator, draft, on="main", expected_head=None if head is None else head[0]
        ).object_id

    return land, opened


def prove(owner: Any, image: Any) -> None:
    """The road's tests, sandbox and shadow evidence, so a publish attempt reaches its gate."""
    from qmx_apps.road.history import history  # noqa: PLC0415
    from qmx_apps.road.models import Evidence  # noqa: PLC0415

    for stage in ("tests", "sandbox", "shadow"):
        with history(owner.home, image.manifest.id) as state:
            state.append(
                Evidence(
                    definition_hash=image.hash,
                    version=image.manifest.version,
                    stage=stage,
                    passed=True,
                    inputs={"fixture": True},
                    versions={"definition": image.hash},
                    results={"passed": True},
                    duration_seconds=0.0,
                )
            )


def lane_three(evidence: Path, work: Path) -> bool:
    lines, path = log_of(evidence, "contract")
    sys.path.insert(0, str(ROOT / "qmx-agents" / "packages" / "qmx-apps" / "src"))
    from qmx_apps.errors import AppError  # noqa: PLC0415
    from qmx_apps.manifest import Definition  # noqa: PLC0415
    from qmx_apps.supervisor import Supervisor  # noqa: PLC0415

    home = work / "home"
    shutil.rmtree(home, ignore_errors=True)
    shutil.rmtree(work / "library", ignore_errors=True)
    folder = app_of(work, profiles=False)
    land, store = library(work / "library")
    owner = Supervisor(home, secret_getter=lambda service, user: None, library=land)
    lines += ["# Lane 3: the producer lands, the consumer reads, a changed schema is refused", ""]
    passed = True
    try:
        owner.install(folder, trust="first_party")
        started = owner.start("app2a-fixture")
        lines.append(
            f"started {started['app_id']} {started['status']} version {started['version']}"
        )
        landed = owner.call("app2a-fixture", "snapshot", {})
        ref = landed["artifact_ref"]
        fresh = owner.read_output("app2a-fixture", "snapshot")
        stale = fresh["stale"] is False and fresh["stale_after"] == 3600
        passed = passed and stale
        lines.append(
            f"{'PASS' if stale else 'FAIL'}  landing {ref['output']} sha {ref['sha256'][:12]} "
            f"reads stale={fresh['stale']} stale_after={fresh['stale_after']}"
        )
        from qmx_host.sessions import StoreReads  # noqa: PLC0415

        reads = StoreReads(store)
        found = reads.outputs("app2a-fixture", "snapshot")
        named = len(found) == 1 and reads.get(found[0]).fields.get("type") == "snapshot"
        passed = passed and named
        lines.append(
            f"{'PASS' if named else 'FAIL'}  the Library holds it as a snapshot artifact "
            f"({found[0][:24] if found else 'nothing'}), which is what @app reads"
        )
        consumer = ROOT / "examples" / "apps" / "weekend-watcher"
        owner.install(consumer, trust="first_party")
        accepted = owner.artifacts.accept(Definition.load(consumer), "snapshot", ref)
        lines.append(f"PASS  weekend-watcher accepted it at {accepted['path']}")

        owner.stop("app2a-fixture")
        changed = work / "changed"
        shutil.rmtree(changed, ignore_errors=True)
        shutil.copytree(folder, changed)
        table = (changed / "app.toml").read_text(encoding="utf-8")
        narrowed = table.replace(
            'type = "array"',
            'type = "string"',
            1,
        ).replace('version = "1.0.0"', 'version = "1.1.0"')
        (changed / "app.toml").write_text(narrowed, encoding="utf-8")
        wider = Definition.load(changed)
        owner.install(
            changed,
            trust="first_party",
            expected_id="app2a-fixture",
            expected_hash=owner.get("app2a-fixture")["definition_hash"],
        )
        prove(owner, wider)
        try:
            owner.road.publish(
                "app2a-fixture", wider.hash, owner.road.active_revision("app2a-fixture")
            )
        except AppError as error:
            named_consumer = error.code == "contract_changed" and "weekend-watcher" in str(error)
            passed = passed and named_consumer
            lines.append(
                f"{'PASS' if named_consumer else 'FAIL'}  publish refused {error.code}: {error}"
            )
        else:
            passed = False
            lines.append("FAIL  the publish was not refused")
    finally:
        owner.close()
        store.close()
    lines += ["", f"APP2A-LANE-3 {'PASS' if passed else 'FAIL'}"]
    write(lines, path)
    return passed


def lane_four(evidence: Path, work: Path) -> bool:
    lines, path = log_of(evidence, "profiles")
    sys.path.insert(0, str(ROOT / "qmx-agents" / "packages" / "qmx-apps" / "src"))
    from qmx_apps.supervisor import Supervisor  # noqa: PLC0415

    home = work / "home"
    shutil.rmtree(home, ignore_errors=True)
    folder = app_of(work, profiles=True)
    lines += ["# Lane 4: two profiles of one fixture app write their own data", ""]
    passed = True
    owner = Supervisor(home, secret_getter=lambda service, user: None)
    try:
        owner.install(folder, trust="first_party")
        marks: dict[str, str] = {}
        for profile in ("research", "markets"):
            started = owner.start("app2a-fixture", profile=profile)
            lines.append(
                f"profile {profile}: version {started['version']} partition {started['data']}"
            )
            answer = owner.call("app2a-fixture", "mark", {"note": profile})["result"]
            marks[profile] = str(answer["written"])
            job = owner.run_job("app2a-fixture", "job.py", profile=profile)
            lines.append(f"  run pinned {job['version']} profile {job['profile']}")
            passed = passed and (job["version"], job["profile"]) == ("1.0.0", profile)
            owner.stop("app2a-fixture")
        apart = len(set(marks.values())) == 2
        passed = passed and apart
        for profile, file in marks.items():
            body = Path(file).read_text(encoding="utf-8")
            lines.append(
                f"{'PASS' if profile in body else 'FAIL'}  {profile} wrote {body!r} at {file}"
            )
        lines.append(
            f"{'PASS' if apart else 'FAIL'}  the two partitions are apart: "
            + ", ".join(Path(file).parent.relative_to(home).as_posix() for file in marks.values())
        )
    finally:
        owner.close()
    lines += ["", f"APP2A-LANE-4 {'PASS' if passed else 'FAIL'}"]
    write(lines, path)
    return passed


def lane_two(evidence: Path) -> bool:
    result = subprocess.run(
        [sys.executable, str(SELF.with_name("e61_app_check.py")), "--evidence", str(evidence)],
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    print(result.stdout)
    return result.returncode == 0 and "E61 PASS" in result.stdout


PARENT_PROBE: Final = """
import json, shutil, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "packages" / "qmx-apps" / "src"))
from qmx_apps.artifacts import Artifacts
from qmx_apps.manifest import Definition
from qmx_apps.volume import Volume
home = Path(sys.argv[2]); shutil.rmtree(home, ignore_errors=True); home.mkdir(parents=True)
artifacts = Artifacts(home)
definition = Definition.load(Path(sys.argv[3]))
Volume(home, definition.manifest.id).create(agents=False)
data = {"observations": []}
times = []
for _ in range(5):
    started = time.perf_counter()
    ref = artifacts.save(definition, "snapshot", data)
    (home / "apps" / definition.manifest.id / "blobs" / (ref["sha256"] + ".json")).read_bytes()
    times.append((time.perf_counter() - started) * 1000)
print(json.dumps(times))
"""


def lane_perf(evidence: Path, work: Path) -> bool:
    """Time from an app's landing to the artifact being readable: five landings, and the parent's
    artifacts.db write beside them. No fail rule (Override 4): the number is the trail."""
    lines, path = log_of(evidence, "perf")
    sys.path.insert(0, str(ROOT / "qmx-agents" / "packages" / "qmx-apps" / "src"))
    from qmx_apps.supervisor import Supervisor  # noqa: PLC0415

    home = work / "home"
    shutil.rmtree(home, ignore_errors=True)
    folder = app_of(work, profiles=False)
    owner = Supervisor(home, secret_getter=lambda service, user: None)
    head: list[float] = []
    lines += ["# Perf: ms from an app's landing to the artifact being readable", ""]
    try:
        owner.install(folder, trust="first_party")
        owner.start("app2a-fixture")
        for _ in range(5):
            started = time.perf_counter()
            owner.call("app2a-fixture", "snapshot", {})
            fresh = owner.read_output("app2a-fixture", "snapshot")
            if fresh["data"] is None:
                raise SystemExit("the landing never became readable")
            head.append((time.perf_counter() - started) * 1000)
    finally:
        owner.close()
    parent = subprocess.run(
        [
            str(python_of(globals()["PARENT"])),
            "-c",
            PARENT_PROBE,
            str(globals()["PARENT"] / "qmx-agents" / "packages"),
            str(work / "parent-home"),
            str(ROOT / "examples" / "apps" / "exchange-status"),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    if parent.returncode != 0:
        lines.append(f"head: all {', '.join(f'{value:.1f}' for value in head)} ms")
        lines += [f"FAIL  the parent probe did not run: {parent.stderr.strip()[-400:]}"]
        write(lines, path)
        return False
    older = [float(value) for value in json.loads(parent.stdout.strip().splitlines()[-1])]
    for name, times in (("head", head), ("parent", older)):
        ordered = sorted(times)
        lines.append(
            f"{name}: median {ordered[2]:.1f} ms, min {ordered[0]:.1f}, max {ordered[-1]:.1f}, "
            f"all {', '.join(f'{value:.1f}' for value in times)}"
        )
    lines += [
        "",
        "Metric. Time from an app's landing to the artifact being readable, in ms.",
        "Probe. Lane 3's landing, five times, through the app's own operation.",
        "Baseline. The parent's artifacts.db write, five times.",
        "Rule. No fail rule (Override 4). The number is for the trail.",
        "",
        "APP2A-PERF PASS",
    ]
    write(lines, path)
    print("\n".join(lines))
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane", type=int, nargs="+", default=[])
    parser.add_argument("--perf", action="store_true", help="record the perf block's number")
    parser.add_argument("--packages", nargs="+", default=["qmx-apps", "qmx-control", "qmx-engine"])
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    parser.add_argument("--work", type=Path, default=WORK)
    parser.add_argument("--parent", type=Path, default=PARENT)
    args = parser.parse_args(argv)
    globals()["PARENT"] = args.parent
    if not args.lane and not args.perf:
        raise SystemExit("name a lane, or --perf, or both")
    args.evidence.mkdir(parents=True, exist_ok=True)
    results: dict[int, bool] = {}
    started = time.monotonic()
    for lane in args.lane:
        if lane == 1:
            results[1] = lane_one(args.evidence, args.work, args.packages)
        elif lane == 2:
            results[2] = lane_two(args.evidence)
        elif lane == 3:
            results[3] = lane_three(args.evidence, args.work / "lane3")
        elif lane == 4:
            results[4] = lane_four(args.evidence, args.work / "lane4")
        else:
            raise SystemExit(f"lane {lane} is not an APP2a proving lane")
        print(f"lane {lane}: {'PASS' if results[lane] else 'FAIL'}")
    if args.perf:
        results[0] = lane_perf(args.evidence, args.work / "perf")
        print(f"perf: {'PASS' if results[0] else 'FAIL'}")
    print(f"{time.monotonic() - started:.1f}s")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
