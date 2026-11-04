"""C-17 lane 3: two QMX hosts on one Linux machine, This PC's side and a server's, each its own
process on its own loopback port and throwaway QMX folder, sharing one pairing key made here.

From `qmx-agents/` with the agents venv, on Linux (WSL, or the server in a throwaway folder):
`uv run --no-sync python ../tools/lanes/two_hosts.py --root <empty folder> --log <file>
[--place ldn-1] [--wait 180]`

The server host is started as `python -m qmx_host serve --home <h> --port <p> --role server
--place <name>`, This PC's as `--role pc`. The lane installs a fixture app named `trading-node` on
the server through that host's own loopback routes (a `status` read, a `manage` pause, and the
deployment staging the node link does before `deploy`), seeds the server's market store with two
months of fixture bars, then checks, one PASS or FAIL line each:

- heartbeats: the server host's route answers its own heartbeat row to a pass minted here;
- apps.ask status: the route answers the app's read;
- a queued pause: with the server host stopped, This PC's node link keeps a pause in its outbox,
  and once the host is back the pause applies exactly once and the outbox is empty;
- a run pass: a pass This PC's authority mints reads the server's data, and one minted under
  another key is refused (Part C `BLAST-RADIUS.md` C9).

On Windows a host keeps its bearer in Credential Manager, which this lane never touches, so it
refuses to run there. Every key is made at runtime and no value is printed. Exit 0 when every
check passed, 1 otherwise; the processes it started are stopped by PID and the folder is removed.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, TextIO, cast


def agents(module: str) -> Any:
    """A module of the agents venv, which the root type check cannot see."""
    return importlib.import_module(module)


httpx: Any = agents("httpx")

REPO: Final = Path(__file__).resolve().parents[2]
EXAMPLE: Final = REPO / "qmx-agents/examples/apps/exchange-status"
APP: Final = "trading-node"
SCHEMA: Final = "qmx.host.forward/1"
SERIES: Final = "dukascopy/EURUSD/bar-m1/-"
DAY_NS: Final = 86_400 * 1_000_000_000
MANIFEST: Final = """id = "trading-node"
name = "trading-node"
version = "1.0.0"
risk = "runs"
kind = "headless"

[entrypoints]
mcp = "server.py"

[capabilities]
network = []
data_reads = []

[operations.status]
approval = "domain_write"
state = "instance"

[operations.pause]
approval = "manage"
state = "instance"
"""
SERVER: Final = """from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("C-17 lane fixture")
PAUSES = Path("data/pauses.txt")


@mcp.tool()
def status() -> dict:
    found = PAUSES.read_text().split() if PAUSES.exists() else []
    return {"ok": True, "value": {"pauses": found}}


@mcp.tool()
def pause(op_id: str, issued_at: str, scope: dict) -> dict:
    with PAUSES.open("a") as file:
        file.write(op_id + "\\n")
    return {"ok": True, "value": {"state": "paused", "scope": scope}}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
"""


class Log:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.file: TextIO = path.open("w", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        self.file.write(line + "\n")
        self.file.flush()
        print(line, flush=True)

    def check(self, name: str, ok: bool, detail: str) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        self.passed = self.passed and ok


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class Host:
    """One `python -m qmx_host serve` process on its own folder and port."""

    def __init__(self, root: Path, port: int, role: str, place: str, log: Log) -> None:
        self.root, self.port, self.role, self.place, self.log = root, port, role, place, log
        self.process: subprocess.Popen[bytes] | None = None
        self.url = f"http://127.0.0.1:{port}"

    def start(self, wait: float) -> None:
        argv = [sys.executable, "-m", "qmx_host", "serve", "--home", str(self.root)]
        argv += ["--port", str(self.port), "--role", self.role]
        if self.role != "pc":
            argv += ["--place", self.place]
        output = (self.root.parent / f"{self.place}-host.out").open("ab")
        self.process = subprocess.Popen(argv, stdout=output, stderr=subprocess.STDOUT)
        self.log(f"started {self.place} as {self.role} on port {self.port}, pid {self.process.pid}")
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(f"{self.place} exited {self.process.returncode}; read its .out")
            with contextlib.suppress(OSError, httpx.HTTPError, RuntimeError):
                if self.get("/api/health").status_code == 200:
                    return
            time.sleep(0.5)
        raise RuntimeError(f"{self.place} did not answer its health route in {wait:.0f} s")

    def stop(self) -> None:
        if self.process is None or self.process.poll() is not None:
            return
        self.process.send_signal(signal.SIGTERM)
        try:
            self.process.wait(30)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(10)
        self.log(f"stopped {self.place}, pid {self.process.pid}")

    def bearer(self) -> str:
        return (self.root / "keys" / "control-token").read_text(encoding="utf-8").strip()

    def get(self, path: str) -> Any:
        headers = {"Authorization": f"Bearer {self.bearer()}"}
        return httpx.get(self.url + path, headers=headers, timeout=60)

    def post(self, path: str, **given: Any) -> Any:
        headers = {"Authorization": f"Bearer {self.bearer()}"}
        return httpx.post(self.url + path, headers=headers, timeout=900, **given)


def fixture_app(root: Path) -> Path:
    target = root / "fixture-app"
    shutil.copytree(EXAMPLE, target, ignore=shutil.ignore_patterns(".venv", "__pycache__", "ui"))
    (target / "app.toml").write_text(MANIFEST, encoding="utf-8")
    (target / "server.py").write_text(SERVER, encoding="utf-8")
    return target


def seed_market(home: Path) -> tuple[int, int]:
    """Two months of fixture bars committed to the server's market store, as its host opens it."""
    is_refusal = agents("qmf.core").is_refusal
    series_key = agents("qmf.data.series").SeriesKey
    writer = agents("qmf.data.store.engines.typed").TypedWriter
    market = agents("qmx_host.market_data")

    opened = market.MarketDoor.open(home / "market", {}, placement=market.Placement.SERVER)
    if is_refusal(opened):
        raise RuntimeError(f"the server's market store did not open: {opened.category}")
    staging = home.parent / "staging"
    january = int(datetime(2026, 1, 1, tzinfo=UTC).timestamp()) * 1_000_000_000
    months = ((1, (january + DAY_NS, january + 4 * DAY_NS)), (2, (january + 32 * DAY_NS,)))
    staged: list[Path] = []
    for month, times in months:
        key = series_key.try_create("dukascopy", "EURUSD", "bar-m1", 2026, month).value
        path = staging / key.series / f"2026-{month:02d}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [(ns // 1_000_000, 1, 2, 0, 2, 1.0) for ns in times]
        writer(path, key.text, key.rule.columns).add(rows).finish()
        staged.append(path)
    landed = opened.value.commit(staged, staging=staging)
    if is_refusal(landed):
        raise RuntimeError(f"the fixture bars did not commit: {landed.category}")
    return january, january + 31 * DAY_NS


def ask(host: Host, key: str, verb: str, args: dict[str, Any], **extra: Any) -> tuple[int, Any]:
    forward = agents("qmx_engine.service.forward")
    held = forward.mint_host_pass(key, source="pc", target=host.place, principal="operator")
    body = {"schema_version": SCHEMA, "verb": verb, "args": args, **extra}
    answer = httpx.post(
        f"{host.url}/api/host/forward", json=body, headers={forward.PASS_HEADER: held}, timeout=60
    )
    return answer.status_code, answer.json()


@contextlib.contextmanager
def hosts(root: Path, place: str, log: Log, wait: float) -> Generator[tuple[Host, Host, str]]:
    resolve = agents("qmx_home").resolve
    key = secrets.token_hex(32)
    made: list[Host] = []
    for name, role in (("pc", "pc"), (place, "server")):
        layout = resolve(root / name, create=True)
        vault = layout.home / "vault"
        vault.mkdir(mode=0o700, parents=True, exist_ok=True)
        handle = os.open(vault / "pairing-key", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(handle, "w", encoding="utf-8") as written:
            written.write(key + "\n")
        made.append(Host(layout.root, free_port(), role, name, log))
    pc, far = made
    try:
        yield pc, far, key
    finally:
        for host in made:
            host.stop()


def run(root: Path, place: str, log: Log, wait: float) -> None:
    node_link = agents("qmx_host.node_link")
    passes = agents("qmx_router.passes")
    began = time.perf_counter()
    with hosts(root, place, log, wait) as (pc, far, key):
        start, end = seed_market(far.root / "data")
        far.start(wait)
        pc.start(wait)
        log.check(
            "bearer file",
            (far.root / "keys/control-token").is_file(),
            "the server host keeps its bearer in keys/, owner-only, never a keyring",
        )
        installed = far.post(
            "/api/apps", params={"path": str(fixture_app(root)), "trust": "first_party"}
        )
        started = far.post(f"/api/apps/{APP}/start")
        log(f"installed {APP} on {place}: {installed.status_code}, started: {started.status_code}")

        deadline = time.monotonic() + wait
        status, beats = ask(far, key, "heartbeats", {"subjects": [f"host:{place}"]})
        while time.monotonic() < deadline and not beats.get("value", {}).get("latest"):
            time.sleep(2)
            status, beats = ask(far, key, "heartbeats", {"subjects": [f"host:{place}"]})
        latest = cast("dict[str, Any]", beats.get("value", {}).get("latest") or {})
        log.check(
            "heartbeats",
            status == 200 and beats.get("schema_version") == SCHEMA and f"host:{place}" in latest,
            f"{status}, rows {sorted(latest)}",
        )

        status, read = ask(far, key, "apps.ask", {"app": APP, "operation": "status"})
        log.check(
            "apps.ask status",
            status == 200 and read.get("value") == {"ok": True, "value": {"pauses": []}},
            f"{status}, {json.dumps(read.get('value'))}",
        )

        rows = {
            f"placement.{place}.kind": "owned",
            f"placement.{place}.engine_url": far.url,
            f"placement.{place}.apps": (APP,),
        }
        link_home = root / "pc-link"
        link_home.mkdir()
        link = node_link.NodeLink(
            link_home,
            here="pc",
            apps=agents("qmx_apps.supervisor").Supervisor(link_home / "apps"),
            settings=lambda: rows,
            key=lambda: key,
        )
        far.stop()
        change = link.change(
            APP, "pause", {"scope": {"all": True}}, principal="operator", op_id="op-c17-pause"
        )
        queued = (change.state, change.document().get("detail"))
        far.start(wait)
        for _ in range(int(wait)):
            link.tick()
            if not link.outbox.waiting(place):
                break
            time.sleep(1)
        again = link.change(APP, "pause", {"scope": {}}, principal="operator", op_id="op-c17-pause")
        _, after = ask(far, key, "apps.ask", {"app": APP, "operation": "status"})
        pauses = cast("list[str]", after.get("value", {}).get("value", {}).get("pauses") or [])
        log.check(
            "queued pause",
            queued == ("waiting", f"waiting for {place}")
            and again.state == "applied"
            and pauses == ["op-c17-pause"]
            and link.outbox.waiting(place) == [],
            f"queued {queued}, then {again.state}, pauses {pauses}",
        )

        authority = passes.PassAuthority.for_home(pc.root / "data")
        _, token = authority.mint(run="run-c17", placement=place, data_scope=(SERIES,))
        body = {"series": SERIES, "start_ns": start, "end_ns": end}
        paired = httpx.post(
            f"{far.url}/api/data/read",
            json=body,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        _, forged = passes.PassAuthority().mint(
            run="run-c17", placement=place, data_scope=(SERIES,)
        )
        unpaired = httpx.post(
            f"{far.url}/api/data/read",
            json=body,
            headers={"Authorization": f"Bearer {forged}"},
            timeout=60,
        )
        rows_read = len(paired.json().get("rows") or []) if paired.status_code == 200 else 0
        log.check(
            "run pass",
            paired.status_code == 200 and rows_read == 2 and unpaired.status_code == 401,
            f"minted on pc: {paired.status_code} with {rows_read} rows; another key: "
            f"{unpaired.status_code}",
        )
    log(f"METRIC two-host lane seconds {time.perf_counter() - began:.1f} (loopback, one machine)")


def main() -> int:
    parser = argparse.ArgumentParser(prog="two_hosts.py")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--place", default="ldn-1")
    parser.add_argument("--wait", type=float, default=180.0)
    args = parser.parse_args()
    log = Log(args.log)
    if os.name == "nt":
        log.check(
            "linux", False, "a Windows host keeps its bearer in Credential Manager; run on Linux"
        )
        return 1
    root = args.root.resolve()
    if root.exists() and any(root.iterdir()):
        log.check("root", False, f"{root} is not empty; name a throwaway folder")
        return 1
    root.mkdir(parents=True, exist_ok=True)
    try:
        run(root, args.place, log, args.wait)
    except (RuntimeError, OSError, httpx.HTTPError) as failed:
        log.check("lane", False, f"{type(failed).__name__}: {failed}")
        for output in sorted(root.glob("*-host.out")):
            log(f"--- last lines of {output.name}")
            for line in output.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]:
                log(f"    {line}")
    finally:
        shutil.rmtree(root, ignore_errors=True)
        log(f"removed {root}: {not root.exists()}")
    return 0 if log.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
