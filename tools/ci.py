"""Run the same sequential Python checks locally and on the PR runners."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv is required to run CI")
    agents = ROOT / "qmx-agents"
    core = agents / "packages/qmx-agents"
    control = agents / "packages/qmx-control"
    domain = agents / "packages/qmx-tools"
    apps = agents / "packages/qmx-apps"
    broker = agents / "packages/qmx-broker"
    remote = agents / "packages/qmx-remote"
    ledger = agents / "packages/qmx-ledger"
    harness = agents / "packages/qma-harness"
    engine = agents / "packages/qmx-engine"
    host = agents / "packages/qmx-host"
    library = agents / "packages/qmx-library"
    router = agents / "packages/qmx-router"
    memory = agents / "packages/qmx-memory"
    hub = agents / "packages/qmx-hub"
    commands: list[tuple[Path, list[str]]] = [
        (ROOT, ["sync", "--frozen"]),
        (agents, ["sync", "--frozen", "--all-packages", "--all-groups"]),
    ]
    for workspace in (
        ROOT,
        agents,
        core,
        control,
        domain,
        apps,
        broker,
        remote,
        ledger,
        harness,
        engine,
        host,
        library,
        router,
        memory,
        hub,
    ):
        for task in ("fmt-check", "lint", "types"):
            commands.append((workspace, ["run", "--no-sync", "python", "-m", "poethepoet", task]))
    for task in ("money-path-scan", "secret-scan"):
        commands.append((ROOT, ["run", "--no-sync", "python", "-m", "poethepoet", task]))
    commands.append((ROOT, ["run", "--no-sync", "python", "tools/test_all.py"]))
    for workspace, command in commands:
        print(f"{workspace.name}: uv {' '.join(command)}", flush=True)
        result = subprocess.run([uv, *command], cwd=workspace, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
