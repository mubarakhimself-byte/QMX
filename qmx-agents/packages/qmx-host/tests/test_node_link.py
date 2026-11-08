"""The node link on This PC (Part C AD-303): where a node app is homed, how `app_op` reaches it
(Level 0 `br11_app_op_remote.py` rerun as a test), and the outbox that holds a change while its
node is down. The far host is a recorded transport here; `test_host_route.py` runs a real one."""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import JsonValue
from qmx_apps.errors import AppError
from qmx_control.models import Document
from qmx_control.service import ControlService
from qmx_engine.nodes.app_op import AppOp
from qmx_engine.nodes.base import Failed, NodeJob, Ok, Waiting
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.service.forward import PASS_HEADER, verify_host_pass

from qmx_host.node_link import NodeLink, Unreachable

KEY = "recorded-pairing-key"
ROWS: dict[str, object] = {
    "placement.ldn-1.kind": "owned",
    "placement.ldn-1.engine_url": "http://ldn-1.example:8765",
    "placement.ldn-1.apps": ("trading-node",),
}


class FarHost:
    """The far host's route as this PC's link reaches it: down until `up`, then recording."""

    def __init__(self, clock: list[float]) -> None:
        self.clock = clock
        self.up = False
        self.asked: list[dict[str, Any]] = []

    def __call__(
        self,
        url: str,
        body: Mapping[str, JsonValue],
        headers: Mapping[str, str],
        _timeout: float | None,
    ) -> JsonValue:
        if not self.up:
            raise Unreachable("ConnectError: recorded refusal")
        held = verify_host_pass(
            {"pc": KEY}, headers[PASS_HEADER], target="ldn-1", now=self.clock[0]
        )
        self.asked.append({"url": url, "principal": held.principal, **dict(body)})
        return {"schema_version": "qmx.host.forward/1", "ok": True, "value": {"verb": body["verb"]}}


@pytest.fixture
def control(tmp_path: Path) -> Iterator[ControlService]:
    found = ControlService(tmp_path / "pc")
    try:
        yield found
    finally:
        found.close()


def link_of(control: ControlService, far: FarHost) -> NodeLink:
    return NodeLink(
        control.home,
        here="pc",
        apps=control.app_runtime(),
        settings=lambda: ROWS,
        pass_keys=lambda: {"ldn-1": KEY},
        clock=lambda: far.clock[0],
        post=far,
    )


def job(app: str) -> NodeJob:
    return NodeJob(
        run_id="r1",
        node_id="a",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="k",
        node_definition={"type": "app_op", "parameters": {"app": app, "job": "status"}},
        inputs={},
        now=None,
    )


def test_an_app_homed_here_keeps_the_local_path(control: ControlService) -> None:
    far = FarHost([1_000.0])
    link = link_of(control, far)
    calls: list[tuple[str, ...]] = []

    def run_job(app: str, name: str) -> Document:
        calls.append(("local", app, name))
        return {"ran": "local", "app": app, "job": name}

    bare = asyncio.run(AppOp(run_job).run(job("trading-node")))
    placed = AppOp(run_job, placements=link.placements())
    here = asyncio.run(placed.run(job("qmb")))
    down = asyncio.run(placed.run(job("trading-node")))
    far.up = True
    link.heartbeats("ldn-1", principal="host:pc")
    remote = asyncio.run(placed.run(job("trading-node")))

    assert isinstance(bare, Ok)
    assert bare.outputs["main"] == {"ran": "local", "app": "trading-node", "job": "status"}
    assert isinstance(here, Ok)
    assert here.outputs["main"] == {"ran": "local", "app": "qmb", "job": "status"}
    assert isinstance(down, Failed)
    assert down.code == "placement_unreachable"
    assert isinstance(remote, Ok)
    assert remote.outputs["main"] == {"verb": "apps.job"}
    assert calls == [("local", "trading-node", "status"), ("local", "qmb", "status")]
    assert [(a["verb"], a["args"]) for a in far.asked] == [
        ("heartbeats", {}),
        ("apps.job", {"app": "trading-node", "job": "status"}),
    ]
    far.up = False
    with pytest.raises(AppError, match="did not answer"):
        link.heartbeats("ldn-1", principal="host:pc")
    waits = asyncio.run(placed.run(job("trading-node")))
    assert isinstance(waits, Waiting)
    assert waits.reason == "placement"


def test_the_place_rows_come_from_his_settings(control: ControlService) -> None:
    (control.home / "settings.toml").write_text(
        '[engine.placement.ldn-1]\nkind = "owned"\nengine_url = "http://ldn-1.example:8765"\n'
        'apps = ["trading-node", "mis"]\n',
        encoding="utf-8",
    )
    link = NodeLink(
        control.home,
        here="pc",
        apps=control.app_runtime(),
        settings=ControlSettings(control).values,
        pass_keys=dict,
    )
    assert (link.home_of("trading-node"), link.home_of("mis"), link.home_of("qmb")) == (
        "ldn-1",
        "ldn-1",
        "pc",
    )
    assert link.set_up() is True


def test_no_trading_node_reads_as_none_and_no_row_reaches_a_change(
    control: ControlService,
) -> None:
    link = NodeLink(
        control.home, here="pc", apps=control.app_runtime(), settings=dict, pass_keys=dict
    )
    assert link.read("status", {}, principal="agent:x") is None
    with pytest.raises(AppError, match="pause is not one of the node's reads"):
        link.read("pause", {}, principal="agent:x")


def test_a_change_waits_while_its_node_is_down_and_applies_once(control: ControlService) -> None:
    clock = [1_000.0]
    far = FarHost(clock)
    link = link_of(control, far)
    first = link.change(
        "trading-node", "pause", {"scope": {"all": True}}, principal="operator", op_id="op-1"
    )
    second = link.change(
        "trading-node", "resume", {"scope": {"all": True}}, principal="operator", op_id="op-2"
    )
    repeated = link.change("trading-node", "kill", {}, principal="operator", op_id="op-1")
    waits = [link.tick() for _ in range(2)]

    assert (first.state, first.issued_at, first.arguments) == (
        "waiting",
        "1970-01-01T00:16:40+00:00",
        {"scope": {"all": True}, "op_id": "op-1", "issued_at": "1970-01-01T00:16:40+00:00"},
    )
    assert (repeated.operation, second.state) == ("pause", "waiting")
    assert link.seen["ldn-1"].delay == 20.0
    assert waits == [20.0, 20.0]
    far.up = True
    clock[0] += 60.0
    link.tick()
    link.tick()
    assert [(a["verb"], a.get("op_id"), a["principal"]) for a in far.asked] == [
        ("heartbeats", None, "host:pc"),
        ("apps.ask", "op-1", "operator"),
        ("apps.ask", "op-2", "operator"),
    ]
    applied = cast(Any, link.outbox.get("op-1"))
    assert (applied.state, applied.answer) == ("applied", {"verb": "apps.ask"})
    assert link.outbox.waiting("ldn-1") == []


class RecordingSupervisor:
    """The local supervisor of a node host whose trading node is homed here."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def call(
        self, app: str, operation: str, arguments: Document, *, pin: Document | None
    ) -> Document:
        self.calls.append((app, operation))
        return {"result": {"paused": True}}


def test_a_change_on_a_node_homed_here_answers_only_to_the_operator(tmp_path: Path) -> None:
    supervisor = RecordingSupervisor()
    link = NodeLink(
        tmp_path, here="ldn-1", apps=cast(Any, supervisor), settings=dict, pass_keys=dict
    )
    for principal, op_id in (("agent:x", "L1"), ("run:r1", "L2")):
        with pytest.raises(AppError, match=f"only to the operator, not {principal}") as refused:
            link.change("trading-node", "pause", {}, principal=principal, op_id=op_id)
        assert refused.value.code == "refused_principal"
        assert link.outbox.get(op_id) is None

    assert supervisor.calls == []
    assert link.outbox.places() == []
    first = link.change("trading-node", "pause", {}, principal="operator", op_id="L3")
    again = link.change("trading-node", "pause", {}, principal="operator", op_id="L3")
    assert (first.state, first.answer, again.state) == ("applied", {"paused": True}, "applied")
    assert supervisor.calls == [("trading-node", "pause")]


def test_deploy_waits_until_every_file_is_staged_from_this_library(tmp_path: Path) -> None:
    supervisor = RecordingSupervisor()
    supervisor.home = tmp_path  # type: ignore[attr-defined]
    block, weights = b"def block(): ...\n", bytes(range(256)) * 4096
    held = {"sha256:" + hashlib.sha256(block).hexdigest(): block}
    link = NodeLink(
        tmp_path,
        here="ldn-1",
        apps=cast(Any, supervisor),
        settings=dict,
        pass_keys=dict,
        blobs=lambda fingerprint: None if fingerprint not in held else [held[fingerprint]],
    )
    files: list[JsonValue] = [
        {"path": path, "fingerprint": "sha256:" + hashlib.sha256(raw).hexdigest()}
        for path, raw in (("blocks/ema@1/block.py", block), ("weights/model.bin", weights))
    ]
    document: Document = {"deployment": {"deployment_id": "dep-1", "files": files}}
    staged = tmp_path / "apps" / "trading-node" / "data" / "deployments" / "dep-1" / "in"

    waiting = link.change("trading-node", "deploy", document, principal="operator", op_id="D1")
    first = (waiting.state, list(supervisor.calls), sorted(p.name for p in staged.rglob("*.*")))
    held["sha256:" + hashlib.sha256(weights).hexdigest()] = weights
    link.flush("ldn-1")

    assert first == ("waiting", [], ["block.py"])
    assert (staged / "blocks/ema@1/block.py").read_bytes() == block
    assert (staged / "weights/model.bin").read_bytes() == weights
    assert supervisor.calls == [("trading-node", "deploy")]
    assert cast(Any, link.outbox.get("D1")).state == "applied"
