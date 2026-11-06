"""The edges of his promote click (R17): a deploy the supervisor could not get an answer for
waits and lands once, a click after a refused deploy deploys again, and a park after that
redeploy withdraws it.

The first test runs a real supervisor over a real MCP app process that serves the node's three
tools and holds its first deploy past the supervisor's ask, which is how the real node behaves
when it is slow (`S/evidence/r03/owner-timeout-probe.log`). The app's deployment document is the
promoter's own, staged by the real node link. The other two tests use the recording conformance
node from `test_promote.py`, with the `deployments` read added.
"""

from __future__ import annotations

import json
import shutil
import stat
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmf.core import is_refusal
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qml.compile import CompiledUnit, compile_unit
from qmx_apps.errors import AppError
from qmx_apps.supervisor import Supervisor
from qmx_control.models import Document
from qmx_engine.control_door import PRINCIPAL
from qmx_engine.service.context import Caller
from qmx_library.port import JsonObject
from qmx_library.principal import Principal
from qmx_tools.gather import FIXTURE_RECORDS, gather
from starlette.types import ASGIApp, Receive, Scope, Send
from test_promote import CLICKED, DUMMY, HIM, TAG, ConformanceNode, g_report, judged, put

from qmx_host.first_start import land_dummy
from qmx_host.host import HostStore, LanderLibrary, open_store, register_checkers
from qmx_host.lifecycle import LifecycleWriter
from qmx_host.node_link import NodeLink
from qmx_host.promote import ROUTE, Promoter, harvested_calibrations, promote_router

OPERATOR = Principal("operator")
EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
APP = "trading-node"
STALL_S = 25.0
"""Past the supervisor's 20 s MCP ask and inside its 30 s one, so the answer is `tool_failed`."""
UV_SHIM = """\
import os
from pathlib import Path

Path(os.environ["UV_PROJECT_ENVIRONMENT"]).mkdir(parents=True, exist_ok=True)
"""
NODE_SERVER = '''\
"""The node's three tools over real MCP, for the promote-edge test. Its first deploy holds past
the supervisor's ask and keeps its deployment, as the real node does when it is slow."""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.tools import Tool, ToolResult
from mcp_types import ToolAnnotations

DATA = Path(os.environ["QMX_DATA_DIR"])
KEPT = DATA / "deployments"
STALLED = DATA / "deploy-stalled"
RELEASED = DATA / "deploy-released"
STALL_S = 25.0


def answer(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "deploy":
        document = arguments["deployment"]
        deployment_id = str(document["deployment_id"])
        KEPT.mkdir(parents=True, exist_ok=True)
        if not STALLED.is_file():
            STALLED.write_text(deployment_id, encoding="utf-8")
            time.sleep(STALL_S)
            RELEASED.write_text(deployment_id, encoding="utf-8")
        (KEPT / f"{deployment_id}.json").write_text(json.dumps(document), encoding="utf-8")
        return {"ok": True, "value": {"deployment_id": deployment_id, "state": "accepted"}}
    if name == "withdraw":
        found = KEPT / f"{arguments['deployment_id']}.json"
        if not found.is_file():
            return {"ok": False, "code": "unknown_deployment", "message": "no such deployment"}
        found.unlink()
        return {"ok": True, "value": {"state": "accepted"}}
    KEPT.mkdir(parents=True, exist_ok=True)
    return {
        "ok": True,
        "value": [
            {
                "deployment_id": found.stem,
                "unit": json.loads(found.read_text(encoding="utf-8"))["unit"],
                "state": "trading",
                "detail": "",
                "accepted_at": None,
            }
            for found in sorted(KEPT.glob("*.json"))
        ],
    }


def run(arguments: dict[str, Any], name: str) -> ToolResult:
    return ToolResult(structured_content=answer(name, arguments))


class NodeOperation(Tool):
    """One node operation over the JSON object the node link sends."""

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        return await asyncio.to_thread(run, arguments, self.name)


node = FastMCP("Promote edge node")
for operation in ("deploy", "withdraw", "deployments"):
    node.add_tool(
        NodeOperation(
            name=operation,
            parameters={"type": "object"},
            annotations=ToolAnnotations(read_only_hint=operation == "deployments"),
        )
    )


if __name__ == "__main__":
    node.run(transport="stdio", show_banner=False)
'''


@dataclass
class Recording(ConformanceNode):
    """The conformance node plus the `deployments` read and a down switch."""

    down: bool = False

    def call(
        self, app: str, operation: str, arguments: Document, *, pin: Document | None = None
    ) -> Document:
        if self.down:
            raise AppError("not_running", "the node is not running", 409)
        if operation == "deployments":
            self.calls.append((operation, arguments))
            return {
                "result": {
                    "ok": True,
                    "value": [
                        {
                            "deployment_id": deployment_id,
                            "unit": cast(Document, document["unit"]),
                            "state": "trading",
                            "detail": "",
                            "accepted_at": None,
                        }
                        for deployment_id, document in self.held.items()
                    ],
                }
            }
        return super().call(app, operation, arguments, pin=pin)


@dataclass
class Library:
    home: Path
    store: HostStore
    writer: LifecycleWriter
    unit: str
    compiled: CompiledUnit


@dataclass
class Rig:
    home: Path
    store: HostStore
    lifecycle: LifecycleWriter
    node: Any
    app: FastAPI
    unit: str
    compiled: CompiledUnit
    promoter: Promoter

    def click(self, caller: Caller = HIM, **body: Any) -> tuple[int, dict[str, Any]]:
        sent: dict[str, Any] = {
            "schema_version": "qmx.units.promote/1",
            "unit": {"id": DUMMY, "version": self.unit},
            "market_id": "fx.eurusd",
            "node": {"tag": TAG},
            "account": {"id": "demo-1"},
            **body,
        }
        answer = TestClient(as_caller(self.app, caller)).post(ROUTE, json=sent)
        return answer.status_code, answer.json()

    def moves(self) -> list[tuple[str, str, str, dict[str, object]]]:
        found: list[tuple[str, str, str, dict[str, object]]] = []
        for folder in stream_folders(self.home / "journals"):
            lines = read_committed(folder)
            assert not is_refusal(lines)
            for line in lines.value:
                if isinstance(line, JournalLine):
                    body = cast(dict[str, object], line.record["body"])
                    found.append(
                        (
                            str(body["market_id"]),
                            str(body["from"]),
                            str(body["to"]),
                            cast(dict[str, object], body["by"]),
                        )
                    )
        return found

    def deployments(self) -> list[Document]:
        answer = self.promoter.nodes.read("deployments", {}, principal="operator")
        return cast("list[Document]", cast(Document, answer)["value"])

    def live(self) -> list[str]:
        """The deployment ids the node itself holds, without the host's refused rows."""
        return [
            str(row["deployment_id"]) for row in self.deployments() if row["state"] != "refused"
        ]


def as_caller(app: ASGIApp, caller: Caller) -> ASGIApp:
    async def served(scope: Scope, receive: Receive, send: Send) -> None:
        token = PRINCIPAL.set(caller)
        try:
            await app(scope, receive, send)
        finally:
            PRINCIPAL.reset(token)

    return served


@pytest.fixture
def library(tmp_path: Path) -> Iterator[Library]:
    home = tmp_path / "QMX"
    home.mkdir()
    with open_store(home, home / "library", serving=False, floor=0) as store:
        register_checkers(store)
        writer = LifecycleWriter(home / "journals", "pc", "test")
        store.lifecycle = writer
        for name in ("eurusd", "xauusd"):
            record = json.loads((FIXTURE_RECORDS / f"{name}.json").read_text("utf-8"))
            record.pop("record_version")
            put(store, "instrument", f"instrument-{name}", record)
        for account_id, world in (("demo-1", "demo"), ("live-1", "live")):
            account: JsonObject = {
                "venue": "icmarkets-ctrader",
                "account_id": account_id,
                "world": world,
            }
            put(store, "account", f"account-{account_id}", account)
        unit = cast(str, land_dummy(store))
        document = store.get(OPERATOR, unit).fields
        compiled = compile_unit(document, gather(store, document).context)
        assert isinstance(compiled, CompiledUnit), compiled
        judged(writer, unit, compiled.compiled_fingerprint.value, "fx.eurusd")
        judged(writer, unit, compiled.compiled_fingerprint.value, "metal.xauusd")
        try:
            yield Library(home, store, writer, unit, compiled)
        finally:
            writer.close()


def rig_of(library: Library, node: Any) -> Rig:
    link = NodeLink(
        library.home,
        here="pc",
        apps=node,
        settings=dict,
        pass_keys=dict,
        blobs=lambda fingerprint: [library.store.read_blob(fingerprint)],
    )
    promoter = Promoter(
        library.store,
        library.writer,
        link,
        LanderLibrary(library.store),
        calibrations=harvested_calibrations(library.home, lambda: time.time_ns() + 10**12),
        trading_profile=lambda _place: False,
        now=lambda: CLICKED,
    )
    app = FastAPI()
    app.include_router(promote_router(promoter))
    return Rig(
        library.home,
        library.store,
        library.writer,
        node,
        app,
        library.unit,
        library.compiled,
        promoter,
    )


def recording_uv(root: Path) -> Path:
    """A real executable named uv that makes the env folder and answers 0."""
    script = root / "record_call.py"
    script.write_text(UV_SHIM, "utf-8")
    if sys.platform == "win32":
        program = root / "uv.cmd"
        program.write_text(f'@"{sys.executable}" "{script}"\n', "utf-8")
    else:
        program = root / "uv"
        program.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}"\n', "utf-8")
        program.chmod(program.stat().st_mode | stat.S_IEXEC)
    return program


def app_folder(tmp_path: Path) -> Path:
    """A shipped-style app folder whose server serves the node's three tools over real MCP."""
    folder = tmp_path / "trading-node"
    shutil.copytree(EXAMPLE, folder, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    (folder / "server.py").write_text(NODE_SERVER, "utf-8")
    manifest = (folder / "app.toml").read_text("utf-8")
    manifest = manifest.replace('id = "exchange-status"', f'id = "{APP}"')
    manifest += '\n[breaker]\nrestart = "backoff"\nmax_errors = 100\n'
    (folder / "app.toml").write_text(manifest, "utf-8")
    return folder


@pytest.fixture
def supervised(library: Library, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Rig]:
    """A real supervisor over a real app process, and the promoter over it."""
    program = recording_uv(tmp_path)
    found = shutil.which

    def which(name: str) -> str | None:
        return str(program) if name == "uv" else found(name)

    def this_interpreter(_self: Supervisor, _definition_hash: str) -> Path:
        return Path(sys.executable)

    monkeypatch.setattr(shutil, "which", which)
    monkeypatch.setattr(Supervisor, "python", this_interpreter)
    supervisor = Supervisor(library.home / "data", restart_wait=lambda _s, _c: False)
    try:
        supervisor.install(app_folder(tmp_path), trust="first_party")
        supervisor.start(APP)
        yield rig_of(library, supervisor)
    finally:
        supervisor.close()


def until(check: Any, what: str) -> None:
    deadline = time.monotonic() + 60
    while not check():
        assert time.monotonic() < deadline, what
        time.sleep(0.05)


def papers(rig: Rig) -> int:
    """How many of his moves into paper the journal holds."""
    return sum(1 for move in rig.moves() if move[1:3] == ("tested", "paper"))


def test_a_timed_out_deploy_waits_and_lands_once(supervised: Rig) -> None:
    g_report(supervised.store, supervised.compiled.compiled_fingerprint.value)
    data = supervised.home / "data" / "apps" / APP / "data"

    started = time.monotonic()
    status, answer = supervised.click(op_id="click-1", to="paper")
    elapsed = time.monotonic() - started

    assert (status, answer.get("code")) == (200, None), answer
    deployment = answer["value"]["deployment_id"]
    assert answer["value"]["node_answer"] == "queued"
    assert elapsed >= 20, "the supervisor's ask gave up inside the node's stall"
    assert supervised.moves()[-1][1:3] == ("tested", "paper")

    until((data / "deploy-released").is_file, "the node's first deploy never returned")
    supervised.promoter.nodes.flush("pc")

    settled = supervised.promoter.nodes.outbox.get(deployment)
    assert settled is not None
    assert settled.state == "applied"
    assert supervised.live() == [deployment]
    assert papers(supervised) == 1

    status, again = supervised.click(op_id="click-1", to="paper")

    assert (status, again["value"]["node_answer"]) == (200, "accepted")
    assert (papers(supervised), supervised.live()) == (1, [deployment])

    status, fresh = supervised.click(op_id="click-2", to="paper")

    assert (status, fresh["code"], fresh["message"]) == (
        409,
        "illegal_move",
        "not_in_table: his_click cannot move paper to paper",
    )
    assert (papers(supervised), supervised.live()) == (1, [deployment])


def test_a_click_after_a_refused_deploy_deploys_again(library: Library) -> None:
    node = Recording(library.home)
    rig = rig_of(library, node)
    g_report(rig.store, rig.compiled.compiled_fingerprint.value)
    node.down = True

    status, queued = rig.click(op_id="click-1", to="paper")

    refused_id = queued["value"]["deployment_id"]
    paper_event = queued["value"]["lifecycle_event_id"]
    assert (status, queued["value"]["node_answer"]) == (200, "queued")
    node.down = False
    node.refuse_deploy = "identity_unconfirmed"
    rig.promoter.nodes.flush("pc")
    settled_refusal = rig.promoter.nodes.outbox.get(refused_id)
    assert settled_refusal is not None
    assert settled_refusal.state == "refused"
    moves = rig.moves()

    node.refuse_deploy = None
    status, answer = rig.click(op_id="click-2", to="paper")

    assert (status, answer.get("code")) == (200, None), answer
    deployed = answer["value"]["deployment_id"]
    assert (answer["ok"], answer["value"]["node_answer"]) == (True, "accepted")
    assert answer["value"]["lifecycle_event_id"] == paper_event
    assert deployed != refused_id
    assert rig.node.deploys()[-1]["lifecycle_event"] == paper_event
    assert set(rig.node.held) == {deployed}
    assert len(rig.node.deploys()) == 2
    assert rig.moves() == moves

    node.down = True
    status, refused = rig.click(op_id="click-3", to="paper")

    assert (status, refused["code"], refused["message"]) == (
        409,
        "illegal_move",
        "not_in_table: his_click cannot move paper to paper",
    )
    assert (len(rig.node.deploys()), rig.moves()) == (2, moves)


def test_a_park_after_a_redeploy_withdraws_it(library: Library) -> None:
    node = Recording(library.home)
    rig = rig_of(library, node)
    g_report(rig.store, rig.compiled.compiled_fingerprint.value)
    node.down = True
    _, queued = rig.click(op_id="click-euro", to="paper")
    refused_id = queued["value"]["deployment_id"]
    node.down = False
    node.refuse_deploy = "identity_unconfirmed"
    rig.promoter.nodes.flush("pc")
    node.refuse_deploy = None
    status, redeployed = rig.click(op_id="click-euro-again", to="paper")
    assert (status, redeployed.get("code")) == (200, None), redeployed
    redeploy_id = redeployed["value"]["deployment_id"]
    _, gold = rig.click(op_id="click-gold", to="paper", market_id="metal.xauusd")
    gold_id = gold["value"]["deployment_id"]
    assert set(rig.node.held) == {redeploy_id, gold_id}

    status, parked = rig.click(op_id="click-park", to="parked", node=None, account=None)

    assert (status, parked["value"]["node_answer"]) == (200, "accepted")
    assert sorted(rig.node.withdraws()) == sorted([refused_id, redeploy_id])
    assert set(rig.node.held) == {gold_id}
    assert rig.live() == [gold_id]

    node.down = True
    status, queued_park = rig.click(
        op_id="click-park-gold", to="parked", node=None, account=None, market_id="metal.xauusd"
    )

    assert (status, queued_park["value"]["node_answer"]) == (200, "queued")
    node.down = False
    rig.promoter.nodes.flush("pc")

    assert (rig.node.held, rig.live()) == ({}, [])
