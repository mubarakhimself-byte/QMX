"""Two hosts on two loopback ports with one pairing key (Level 0 AD-46, Part C AD-303, AD-304).

The far host `ldn-1` serves the host route over a real supervisor with two fixture apps: a
running `runs` app shaped like the trading node, with a read, a `manage` pause and a job, and a
`money` app that is installed and never started, because a money app starts only after his signed
publish. This PC asks it through its node link, or with a pass minted here. The pairing key is a
fake made at runtime.
"""

from __future__ import annotations

import asyncio
import json
import secrets
import shutil
import socket
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
import uvicorn
from fastapi import FastAPI
from pydantic import JsonValue
from qmx_control.models import Document
from qmx_control.server import create_app
from qmx_control.service import ControlService
from qmx_engine.control_door import AsRun
from qmx_engine.heartbeat import Heartbeat, HeartbeatLog
from qmx_engine.nodes.app_op import AppOp
from qmx_engine.nodes.base import NodeJob, Ok
from qmx_engine.service.forward import PASS_HEADER, mint_host_pass

from qmx_host.door import host_pass_call
from qmx_host.host import heartbeats_read
from qmx_host.host_route import ANSWERS, Answering, Answers, host_router
from qmx_host.node_link import NodeLink

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
FAR = "ldn-1"
SCHEMA = "qmx.host.forward/1"
MANIFEST = """id = "{id}"
name = "{id}"
version = "1.0.0"
risk = "{risk}"
kind = "headless"

[entrypoints]
mcp = "server.py"
jobs = ["echo.py"]

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
SERVER = """from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("Host route fixture")
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
ECHO = "def run(inputs):\n    return {'seen': inputs}\n"


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class Served:
    """One host app answering on a loopback port in its own thread."""

    def __init__(self, app: FastAPI, port: int) -> None:
        self.url = f"http://127.0.0.1:{port}"
        self.server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
        )
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 20
        while not self.server.started:
            assert time.monotonic() < deadline, "the loopback host did not start"
            time.sleep(0.05)

    def close(self) -> None:
        self.server.should_exit = True
        self.thread.join(10)


def fixture_app(root: Path, app_id: str, risk: str) -> Path:
    target = root / app_id
    shutil.copytree(EXAMPLE, target, ignore=shutil.ignore_patterns(".venv", "__pycache__", "ui"))
    (target / "app.toml").write_text(MANIFEST.format(id=app_id, risk=risk), encoding="utf-8")
    (target / "server.py").write_text(SERVER, encoding="utf-8")
    (target / "echo.py").write_text(ECHO, encoding="utf-8")
    return target


def price_store(root: Path) -> Path:
    month = root / "series/dukascopy/EURUSD/bar-1m/-/2025-01"
    month.mkdir(parents=True)
    state = {
        "key": "dukascopy/EURUSD/bar-1m/-/2025-01",
        "fingerprint": "fp-recorded",
        "rows": 3,
        "bytes": 13,
        "gaps": [],
        "attempts": 1,
        "frozen": True,
        "frozen_once": True,
        "at": "2025-02-01T00:00:00+00:00",
    }
    (month / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (month / "fp-recorded.parquet").write_bytes(b"PAR1-recorded")
    return root / "series"


@dataclass
class Hosts:
    key: str
    far: Served
    far_home: Path
    far_control: ControlService
    far_answering: Answering
    pc: NodeLink
    rows: dict[str, object]

    def place(self, url: str) -> None:
        self.rows.update(
            {
                f"placement.{FAR}.kind": "owned",
                f"placement.{FAR}.engine_url": url,
                f"placement.{FAR}.apps": ("trading-node", "money-fixture"),
            }
        )

    def ask(
        self,
        verb: str,
        args: dict[str, Any],
        *,
        principal: str = "operator",
        target: str = FAR,
        op_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        held = mint_host_pass(self.key, source="pc", target=target, principal=principal)
        body: dict[str, Any] = {"schema_version": SCHEMA, "verb": verb, "args": args}
        if op_id is not None:
            body["op_id"] = op_id
        answer = httpx.post(
            f"{self.far.url}/api/host/forward",
            json=body,
            headers={PASS_HEADER: held},
            timeout=60,
        )
        return answer.status_code, cast(dict[str, Any], answer.json())

    def pauses(self) -> list[str]:
        found = self.far_home / "apps/trading-node/data/pauses.txt"
        return found.read_text(encoding="utf-8").split() if found.exists() else []


@pytest.fixture(scope="module")
def hosts(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Hosts]:
    root = tmp_path_factory.mktemp("hosts")
    key = secrets.token_hex(16)
    far_home = root / "far"
    far_control = ControlService(far_home)
    pc_control = ControlService(root / "pc")
    try:
        for app_id, risk in (("trading-node", "runs"), ("money-fixture", "money")):
            far_control.apps_create(str(fixture_app(root, app_id, risk)), trust="first_party")
        far_control.apps_start("trading-node")
        now = datetime.now(UTC).isoformat()
        HeartbeatLog(far_home, 1).write(
            [
                Heartbeat(
                    subject="host",
                    id=FAR,
                    at=now,
                    cpu_seconds=1.0,
                    rss_bytes=1,
                    machine_minutes=1.0,
                    qmx_version="0.1.0",
                    kinds_digest="recorded",
                    paused=False,
                )
            ]
        )
        far_link = NodeLink(
            far_home, here=FAR, apps=far_control.app_runtime(), settings=dict, key=lambda: key
        )
        store = price_store(root / "market")
        answering = Answering(
            far_link,
            key=lambda: key,
            heartbeats=lambda: heartbeats_read(far_home, FAR)({}),
            store_root=lambda: store,
            answers=Answers(far_home / ANSWERS),
        )
        far_app = FastAPI()
        far_app.include_router(host_router(answering))
        far = Served(far_app, free_port())
        rows: dict[str, object] = {}
        pc = NodeLink(
            root / "pc",
            here="pc",
            apps=pc_control.app_runtime(),
            settings=lambda: rows,
            key=lambda: key,
        )
        hosts = Hosts(key, far, far_home, far_control, answering, pc, rows)
        hosts.place(far.url)
        try:
            yield hosts
        finally:
            far.close()
    finally:
        far_control.close()
        pc_control.close()


def test_heartbeats_answer_across_two_hosts(hosts: Hosts) -> None:
    value = cast(dict[str, Any], hosts.pc.heartbeats(FAR, principal="agent:x"))
    status, answer = hosts.ask("heartbeats", {"subjects": ["host:ldn-1"]})
    assert value["latest"]["host:ldn-1"]["id"] == FAR
    assert [row["id"] for row in value["host_history"]] == [FAR]
    assert (status, answer["schema_version"], answer["ok"]) == (200, SCHEMA, True)
    assert list(answer["value"]["latest"]) == ["host:ldn-1"]


def test_an_agent_pass_on_a_manage_operation_is_refused(hosts: Hosts) -> None:
    args = {
        "app": "trading-node",
        "operation": "pause",
        "arguments": {"op_id": "op-agent", "issued_at": "2026-11-02T00:00:00+00:00", "scope": {}},
    }
    status, answer = hosts.ask("apps.ask", args, principal="agent:x", op_id="op-agent")
    assert (status, answer["schema_version"], answer["ok"], answer["code"]) == (
        403,
        SCHEMA,
        False,
        "refused_principal",
    )
    status, read = hosts.ask(
        "apps.ask", {"app": "trading-node", "operation": "status"}, principal="agent:x"
    )
    assert (status, read["value"]["ok"]) == (200, True)
    assert "op-agent" not in hosts.pauses()


def test_a_money_apps_job_answers_only_the_operator(hosts: Hosts) -> None:
    job = {"app": "money-fixture", "job": "echo.py", "inputs": {"x": 1}}
    for principal in ("agent:x", "run:r1"):
        status, answer = hosts.ask("apps.job", job, principal=principal)
        assert (status, answer["schema_version"], answer["code"]) == (
            403,
            SCHEMA,
            "refused_principal",
        )
    status, answer = hosts.ask("apps.job", job, principal="operator")
    assert (status, answer["code"]) == (409, "not_running")
    status, answer = hosts.ask("apps.job", {**job, "app": "trading-node"}, principal="agent:x")
    assert (status, answer["value"]["result"]) == (200, {"seen": {"x": 1}})


def job_of(app: str, name: str, inputs: dict[str, Any]) -> NodeJob:
    return NodeJob(
        run_id="r1",
        node_id="a",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="k",
        node_definition={
            "type": "app_op",
            "parameters": {"app": app, "job": name, "inputs": cast(JsonValue, inputs)},
        },
        inputs={},
        now=None,
    )


def test_a_workflow_runs_a_runs_apps_job_at_its_home_with_its_inputs(hosts: Hosts) -> None:
    def never(*_asked: object, **_named: object) -> Document:
        raise AssertionError("a job homed on ldn-1 never runs on This PC")

    node = AsRun(AppOp(never, dispatch=never, placements=hosts.pc.placements()))
    result = asyncio.run(node.run(job_of("trading-node", "echo.py", {"x": 1, "window": "2025-01"})))
    log = hosts.far_home / "apps/trading-node/logs/supervisor.jsonl"
    completed = [
        json.loads(line)
        for line in log.read_text(encoding="utf-8").splitlines()
        if json.loads(line)["event"] == "job_completed"
    ]
    assert isinstance(result, Ok)
    assert cast(Document, result.outputs["main"])["result"] == {
        "seen": {"x": 1, "window": "2025-01"}
    }
    assert [entry.get("principal") for entry in completed][-1] == "run:r1"


def test_a_pass_for_another_place_or_without_the_key_is_refused(hosts: Hosts) -> None:
    status, answer = hosts.ask("heartbeats", {}, target="ldn-2")
    assert (status, answer["schema_version"], answer["code"]) == (401, SCHEMA, "wrong_engine")
    forged = mint_host_pass("not-the-pairing-key", source="pc", target=FAR, principal="operator")
    refused = httpx.post(
        f"{hosts.far.url}/api/host/forward",
        json={"schema_version": SCHEMA, "verb": "heartbeats", "args": {}},
        headers={PASS_HEADER: forged},
    ).json()
    assert refused["code"] == "bad_pass"
    status, unknown = hosts.ask("apps.call", {})
    assert (status, unknown["code"]) == (400, "no_verb")


def test_a_queued_pause_applies_once_when_the_far_host_returns(hosts: Hosts) -> None:
    port = free_port()
    hosts.place(f"http://127.0.0.1:{port}")
    try:
        change = hosts.pc.change(
            "trading-node",
            "pause",
            {"scope": {"all": True}},
            principal="operator",
            op_id="op-pause-1",
        )
        assert (change.state, change.place, change.document()["detail"]) == (
            "waiting",
            FAR,
            "waiting for ldn-1",
        )
        assert change.arguments["issued_at"] == change.issued_at
        assert hosts.pauses().count("op-pause-1") == 0
        far_app = FastAPI()
        far_app.include_router(host_router(hosts.far_answering))
        returned = Served(far_app, port)
        try:
            hosts.pc.tick()
            hosts.pc.tick()
            again = hosts.pc.change(
                "trading-node", "pause", {"scope": {}}, principal="operator", op_id="op-pause-1"
            )
            repeated = hosts.ask(
                "apps.ask",
                {"app": "trading-node", "operation": "pause", "arguments": change.arguments},
                op_id="op-pause-1",
            )
        finally:
            returned.close()
    finally:
        hosts.place(hosts.far.url)
    assert (again.state, again.answer) == (
        "applied",
        {"ok": True, "value": {"state": "paused", "scope": {"all": True}}},
    )
    assert repeated[1]["value"] == again.answer
    assert hosts.pc.outbox.waiting(FAR) == []
    assert hosts.pauses().count("op-pause-1") == 1


def test_data_list_names_partitions_and_fetch_streams_one(hosts: Hosts) -> None:
    status, listed = hosts.ask("data.list", {"after": {}, "confirmed": ["fp-older"]})
    assert (status, listed["schema_version"]) == (200, SCHEMA)
    assert listed["value"] == {
        "partitions": [
            {
                "key": "dukascopy/EURUSD/bar-1m/-/2025-01",
                "fingerprint": "fp-recorded",
                "bytes": 13,
                "frozen": True,
                "born_on": FAR,
                "committed_at": "2025-02-01T00:00:00+00:00",
            }
        ],
        "watermark": {"committed_at": "2025-02-01T00:00:00+00:00"},
    }
    _, after = hosts.ask("data.list", {"after": listed["value"]["watermark"]})
    assert after["value"]["partitions"] == []
    held = mint_host_pass(hosts.key, source="pc", target=FAR, principal="run:r1")
    fetched = httpx.post(
        f"{hosts.far.url}/api/host/forward",
        json={
            "schema_version": SCHEMA,
            "verb": "data.fetch",
            "args": {"fingerprint": "fp-recorded"},
        },
        headers={PASS_HEADER: held},
    )
    assert (fetched.content, fetched.headers["X-QMX-Key"]) == (
        b"PAR1-recorded",
        "dukascopy/EURUSD/bar-1m/-/2025-01",
    )


def test_exactly_five_routes_take_a_host_pass() -> None:
    routes = [
        ("POST", "/api/venue/ctrader/begin"),
        ("POST", "/api/venue/ctrader/code"),
        ("POST", "/api/engine/forward"),
        ("GET", "/api/engine/forward/stream"),
        ("POST", "/api/data/read"),
        ("POST", "/api/apps/trading-node/call"),
        ("POST", "/api/host/forward"),
    ]

    def admitted(method: str, path: str, headers: list[tuple[bytes, bytes]]) -> bool:
        return host_pass_call({"type": "http", "method": method, "path": path, "headers": headers})

    with_pass = [route for route in routes if admitted(*route, [(b"x-qmx-host-pass", b"p")])]
    assert with_pass == [
        ("POST", "/api/venue/ctrader/begin"),
        ("POST", "/api/venue/ctrader/code"),
        ("POST", "/api/engine/forward"),
        ("GET", "/api/engine/forward/stream"),
        ("POST", "/api/host/forward"),
    ]
    assert not any(admitted(*route, []) for route in routes)


def test_the_openapi_version_is_the_package_version(tmp_path: Path) -> None:
    control = ControlService(tmp_path / "home")
    try:
        stated = create_app(control, "recorded-bearer").openapi()["info"]["version"]
    finally:
        control.close()
    assert stated == version("qmx-control") == version("qmx-host")
