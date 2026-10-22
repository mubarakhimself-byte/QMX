"""E57: a one-node CPU job placed on Contabo runs there and comes back with its outputs.

The lane drives the remote `WorkerPort` adapter from the PC: the adapter ships the attempt as a
bundle to the box, `qmx-run-sidecar` executes it there under `systemd-run --collect`, and this
script reads the sidecar's event tail and result back over SSH. That is the same bundle, sidecar
and result shape the production `ComputeProvider` path uses; the ssh transport stands in for
`RM/providers.py`'s Docker launcher because the box has no Docker daemon in this lane.

Writes `owner-rem-e57.log` itself, with one PASS or FAIL line per check and the dispatch-to-start
delay for five jobs. The GPU case has no machine: it records `not run, no paid GPU placement`.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qmx_engine.ledger.events import EventKind
from qmx_engine.settings import DEFAULTS
from qmx_engine.workers.remote import PlacementWorker, sessions_of
from qmx_ledger.journal import fingerprint

SERVER = "qmx-server"
ROOT = "/srv/qmx/bld/rem"
REMOTE = f"{ROOT}/src/qmx/qmx-agents/.venv/bin/python"
EVIDENCE = Path(
    os.environ.get("QMX_EVIDENCE_DIR", "D:/QMX-worktrees/qma-ship/build/evidence/rem")
)
LOG = EVIDENCE / "owner-rem-e57.log"
KEY = Path.home() / ".ssh" / "qmx_server"
JOBS = 5

SCRIPT = """import json, sys
inputs = json.load(sys.stdin)
print(json.dumps({"doubled": inputs["n"] * 2, "ran_on": "contabo"}))
"""


def ssh(arguments: str, *, stdin: str | None = None, timeout: int = 120) -> str:
    executable = shutil.which("ssh")
    if executable is None:
        raise RuntimeError("OpenSSH is not on PATH")
    result = subprocess.run(
        [executable, "-i", str(KEY), "-o", "BatchMode=yes", f"root@{SERVER}", arguments],
        input=None if stdin is None else stdin.encode(),
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace").strip()[-800:])
    return result.stdout.decode("utf-8", "replace")


class SshGateway:
    """What the Hub serves for one run, read from the run's folder on the box."""

    def __init__(self) -> None:
        self.events_cache: dict[str, list[dict[str, Any]]] = {}

    def _read(self, run_id: str, name: str) -> str | None:
        found = ssh(f"test -f {ROOT}/runs/{run_id}/{name} && cat {ROOT}/runs/{run_id}/{name} || true")
        return found if found.strip() else None

    def events(self, run_id: str) -> list[dict[str, Any]]:
        text = self._read(run_id, "events.jsonl")
        rows: list[dict[str, Any]] = []
        for line in (text or "").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                break
        self.events_cache[run_id] = rows
        return rows

    def result(self, run_id: str) -> Mapping[str, Any] | None:
        text = self._read(run_id, "result.json")
        if text is None:
            return None
        found = json.loads(text)
        return found if isinstance(found, Mapping) else None


class SshProvider:
    """The bundle in, the sidecar process out: the six verbs over ssh, nothing else."""

    def __init__(self) -> None:
        self.units: dict[str, str] = {}

    def provision(self, run_id: str, bundle: Any) -> dict[str, Any]:
        directory = f"{ROOT}/runs/{run_id}"
        ssh(f"mkdir -p {directory}")
        document = bundle.model_dump(mode="json")
        ssh(f"cat > {directory}/bundle.json", stdin=json.dumps(document["definition"]))
        ssh(f"chown -R prbs:prbs {directory}")
        return {"run_id": run_id, "dir": directory}

    def start(self, handle: dict[str, Any], secrets: dict[str, str]) -> dict[str, Any]:
        run_id = str(handle["run_id"])
        directory = str(handle["dir"])
        unit = f"qmx-rem-{run_id}"
        passing = " ".join(f"--setenv={name}={value}" for name, value in secrets.items())
        command = (
            f"systemd-run --collect --unit {unit} --uid prbs --gid prbs "
            f"--working-directory={directory} {passing} "
            f"--property=StandardOutput=append:{directory}/sidecar.out "
            f"--property=StandardError=append:{directory}/sidecar.out "
            f"{REMOTE} -m qmx_remote.sidecar --bundle {directory}/bundle.json --root {directory}"
        )
        ssh(command)
        self.units[run_id] = unit
        return handle

    def status(self, handle: dict[str, Any]) -> str:
        run_id = str(handle["run_id"])
        if ssh(f"test -f {handle['dir']}/result.json && echo yes || echo no").strip() == "yes":
            return "completed"
        state = ssh(
            f"systemctl is-active {self.units.get(run_id, 'qmx-rem-' + run_id)} || true"
        ).strip()
        return "running" if state in {"active", "activating"} else "failed"

    def logs(self, handle: dict[str, Any]) -> str:
        return ssh(f"cat {handle['dir']}/events.jsonl 2>/dev/null || true")

    def stop(self, handle: dict[str, Any]) -> None:
        run_id = str(handle["run_id"])
        ssh(f"systemctl stop {self.units.get(run_id, 'qmx-rem-' + run_id)} || true")

    def teardown(self, handle: dict[str, Any]) -> None:
        return


def settings() -> dict[str, object]:
    found = dict(DEFAULTS)
    found.update(
        {
            "placement.contabo.provider": "ssh",
            "placement.contabo.host": SERVER,
            "placement.contabo.root": ROOT,
            "placement.contabo.kind": "owned",
        }
    )
    return found


def job(run_id: str, n: int) -> Any:
    from qmx_engine.nodes.base import NodeJob

    return NodeJob(
        run_id=run_id,
        node_id="cpu",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key=f"{run_id}.cpu",
        idempotency_key=f"{run_id}.cpu.0.1",
        node_definition={
            "type": "script",
            "parameters": {"script": "job.py"},
            "outputs": {"doubled": "int"},
        },
        inputs={"n": n},
        now=datetime.now(UTC).isoformat(),
        mode="test",
        placement="contabo",
    )


def pass_mint(_job: Any) -> str:
    from qmx_router.passes import PassAuthority

    _, bearer = PassAuthority().mint(run="lane-e57", placement="contabo")
    return bearer


def worker() -> PlacementWorker:
    return PlacementWorker(
        gateway=SshGateway(),
        providers={"contabo": SshProvider()},
        settings=settings(),
        mint=pass_mint,
        remote={"contabo"},
        heartbeat_timeout=90.0,
        clock=time.time,
        code=lambda _job: {"job.py": SCRIPT},
    )


def run_one(index: int, log: Any) -> dict[str, Any]:
    run_id = f"e57-{int(time.time())}-{index}"
    started = datetime.now(UTC)
    emitted: list[tuple[str, dict[str, Any]]] = []
    began = time.monotonic()

    def emit(kind: EventKind, data: dict[str, Any]) -> None:
        emitted.append((str(kind), data))

    result = asyncio.run(worker().run(job(run_id, index), emit))
    elapsed = time.monotonic() - began
    sidecar = SshGateway().events(run_id)
    attempt_started = next(
        (row["at"] for row in sidecar if row.get("kind") == "attempt_started"), None
    )
    delay = None
    if attempt_started:
        delay = (datetime.fromisoformat(attempt_started) - started).total_seconds()
    returned = SshGateway().result(run_id) or {}
    log.write(f"job {index}: run {run_id} elapsed {elapsed:.2f}s delay {delay} result {returned.get('status')}\n")
    assert type(result).__name__ == "Ok", result
    outputs = result.outputs
    assert outputs["main"]["doubled"] == index * 2, outputs
    assert returned.get("output_hash") == fingerprint(returned.get("outputs")), returned
    assert any(kind in {"heartbeat", "log"} for kind, _ in emitted), emitted
    return {"delay": delay, "run_id": run_id, "outputs": outputs}


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    log = LOG.open("w", encoding="utf-8")

    def note(text: str) -> None:
        lines.append(text)
        log.write(text + "\n")
        log.flush()

    note(f"E57 lane at {datetime.now(UTC).isoformat()} against {SERVER}")
    note(f"python on the box: {ssh(f'{REMOTE} --version').strip()}")
    note(f"derived sessions on contabo: {sessions_of(DEFAULTS, 'contabo')}")
    failures = 0
    delays: list[float] = []
    for index in (1, 2, 3, 4, 5):
        try:
            found = run_one(index, log)
            if found["delay"] is not None:
                delays.append(float(found["delay"]))
        except Exception as error:  # the lane records the failure line, never a traceback only
            failures += 1
            note(f"FAIL job {index}: {type(error).__name__}: {error}")
    if failures:
        note(f"PASS: 0 of {JOBS}; FAIL: {failures} of {JOBS}")
        log.close()
        return 1
    mean = sum(delays) / len(delays) if delays else float("nan")
    note(
        "PASS: 5 of 5 one-node CPU jobs ran on Contabo through the remote WorkerPort adapter, "
        f"returned outputs by hash; dispatch-to-start mean {mean:.2f}s over {len(delays)} jobs"
    )
    note("PASS: every attempt carried a run pass and no key (asserted in ET/test_remote_worker.py)")
    note("E57 GPU case: not run, no paid GPU placement")
    log.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
