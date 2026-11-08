"""C-11: the trading-node kind of the connect dialog on This PC, run on the shipped step runner
against a real supervisor and the shipped `apps/trading-node`, in a throwaway QMX folder.

What stands in: the key store is in memory, the signing key is made here, the clock probe answers
fixed facts, and the venues are loopback ports. The road's tests, sandbox and shadow proofs are
recorded by `stand_in_proof`, because `apps/trading-node` ships no `proofs/` folder yet; every
step after them is the real one.
"""

from __future__ import annotations

import json
import secrets
import socket
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from qmx_apps.road.history import history
from qmx_apps.road.models import Evidence, Stage
from qmx_apps.supervisor import Supervisor
from qmx_control.service import ControlService
from qmx_engine.heartbeat import ClockFacts
from qmx_home import Layout
from qmx_home.rclone import Rclone
from test_connect import Store, qmx_folder

from qmx_host.connect import KINDS, Kind, World, run_kind
from qmx_host.connect_node import (
    APP_SECRET,
    MIS_APP,
    NODE_APP,
    NODE_KEYS,
    PASSPORT,
    Ports,
    Venue,
    handshake,
    on_this_pc,
)
from qmx_host.jobs import Jobs

PLACE = "this-pc"
CLIENT_ID = "fixture-client-id"
STAGED_VALUE = "fixture-app-value"
CLOCK = ClockFacts(
    zone="UTC",
    offset_ms=3,
    delay_ms=10,
    source="fixture",
    source_kind="w32time",
    synced=True,
    tzdata="2025b",
    band="ok",
    probed_at="2026-11-02T12:00:00+00:00",
)


def stand_in_proof(apps: Supervisor, app: str, definition_hash: str) -> None:
    """The road's three proofs as passed evidence, the way C-10's app test records them."""
    version = str(cast("dict[str, Any]", apps.get(app)["definition"])["version"])
    with history(apps.home, app) as state:
        for stage in ("tests", "sandbox", "shadow"):
            if state.stages.get(definition_hash) in {"shadow", "live"}:
                return
            state.append(
                Evidence(
                    definition_hash=definition_hash,
                    version=version,
                    stage=cast(Stage, stage),
                    passed=True,
                    inputs={"fixture": True},
                    versions={"definition": definition_hash},
                    results={"passed": True},
                    duration_seconds=0.1,
                )
            )


@pytest.fixture(scope="module")
def envs(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One locked environment for the app, shared by every folder here."""
    return tmp_path_factory.mktemp("envs")


@pytest.fixture(scope="module")
def venue() -> Iterator[int]:
    """A loopback port that takes every handshake."""
    with socket.socket() as listening:
        listening.bind(("127.0.0.1", 0))
        listening.listen(64)
        listening.settimeout(0.2)
        stop = threading.Event()

        def accept() -> None:
            while not stop.is_set():
                try:
                    taken, _ = listening.accept()
                except OSError:
                    continue
                taken.close()

        thread = threading.Thread(target=accept, daemon=True)
        thread.start()
        yield int(listening.getsockname()[1])
        stop.set()
        thread.join(2)


UNREACHABLE = 9
"""A venue port that refuses at once; a real refused loopback handshake takes 2 s on Windows."""


def refusing_unreachable(host: str, port: int, timeout: float) -> float:
    if port == UNREACHABLE:
        raise ConnectionRefusedError(port)
    return handshake(host, port, timeout)


class Host:
    """One QMX host on the folder: its settings, its supervisor and the dialog's world. `restart`
    is a host that died and came back: every app it ran is stopped, the keys stay."""

    def __init__(self, layout: Layout, keys: Store, envs: Path, venue: int, signing: str) -> None:
        self.layout, self.keys, self.envs, self.signing = layout, keys, envs, signing
        self.kind = on_this_pc(
            Ports(
                prove=stand_in_proof,
                clock=lambda _settings: CLOCK,
                venues=(
                    Venue("ctrader", "demo", "127.0.0.1", venue),
                    Venue("hyperliquid", "testnet", "127.0.0.1", UNREACHABLE),
                ),
                handshake=refusing_unreachable,
                now=lambda: 1_793_620_800.0,
            )
        )
        self.control = self._control()
        self.dialog = self._world()

    def _world(self) -> World:
        """The dialog's world, which remembers his answers by place until the host stops."""
        rclone = Rclone(self.layout, keys=self.keys)
        return World(self.layout, self.keys, rclone, Jobs(), self.control)

    def _control(self) -> ControlService:
        control = ControlService(
            self.layout.home, secret_getter=lambda service, _name: self.keys.read(service)
        )
        apps = control.app_runtime()
        apps.environments = self.envs
        apps.road.signing_key(self.signing)
        return control

    @property
    def apps(self) -> Supervisor:
        return self.control.app_runtime()

    def run(
        self, answer: dict[str, object] | None = None, kind: Kind | None = None
    ) -> dict[str, Any]:
        def quiet(step: str, *, done: int = 0, total: int = 0, **counts: int) -> None:
            del step, done, total, counts

        found = run_kind(kind or self.kind, PLACE, answer or {}, report=quiet, world=self.dialog)
        return dict(found)

    def through(self, kind: Kind | None = None) -> dict[str, Any]:
        """Run the kind and answer his signature card, as his click does, until it ends."""
        ended = self.run(kind=kind)
        while cast("dict[str, Any]", ended.get("needs") or {}).get("card") == "signature":
            ended = self.run({"fields": {"signature": self.signature()}}, kind)
        return ended

    def signature(self) -> str:
        """What the operator-only sign route answers for the installed version."""
        found = self.apps.get(NODE_APP)
        active = self.apps.road.active_revision(NODE_APP)
        return self.apps.road.sign(NODE_APP, str(found["definition_hash"]), active)

    def restart(self) -> None:
        self.control.close()
        self.control = self._control()
        self.dialog = self._world()

    def status(self) -> dict[str, Any]:
        called = self.apps.call(NODE_APP, "status", {})
        return cast("dict[str, Any]", cast("dict[str, Any]", called["result"])["value"])

    def rows(self) -> dict[str, Any]:
        engine = self.control.settings_get(cast("Any", "engine"))
        return cast("dict[str, Any]", engine.get("placement") or {})

    def keys_document(self) -> dict[str, Any]:
        return cast("dict[str, Any]", json.loads(self.keys.read(NODE_KEYS) or "null"))


@pytest.fixture
def host(tmp_path: Path, envs: Path, venue: int) -> Iterator[Host]:
    made = Host(qmx_folder(tmp_path / "QMX"), Store(), envs, venue, secrets.token_urlsafe(32))
    try:
        yield made
    finally:
        made.control.close()


def waits(ended: dict[str, Any]) -> list[str]:
    return [line for line in ended["lines"] if "waits for" in line or "waiting;" in line]


def test_one_click_sets_the_node_up_and_ends_on_the_app_request_with_no_sign_in(
    host: Host,
) -> None:
    first = host.run()
    assert first["needs"]["card"] == "signature"
    assert host.rows() == {}

    ended = host.through()

    assert ended["step"] == "waiting"
    assert ended["needs"]["card"] == "ctrader-app"
    assert ended["needs"]["line"].startswith("Waiting for cTrader to approve your app.")
    assert ended["needs"]["key"] == APP_SECRET
    assert waits(ended) == [
        f"ctrader-app: waiting; {ended['needs']['line']}",
        "sign-in: waits for ctrader-app",
        "self-test: waits for sign-in",
    ]
    status = host.status()
    assert status["headline"] == "Ready, no units yet"
    assert [(v["venue"], v["session"]) for v in status["venues"]] == [
        ("ctrader", "not_set_up"),
        ("hyperliquid", "not_set_up"),
    ]
    assert host.rows() == {"pc": {"apps": ["trading-node", "mis"]}}
    assert host.keys_document() == {"schema_version": "qmx.node.keys/1"}
    passport = json.loads((host.layout.home / PASSPORT).read_text(encoding="utf-8"))
    assert [(r["venue"], r["samples"]) for r in passport["round_trip"]] == [
        ("ctrader", 8),
        ("hyperliquid", 0),
    ]
    assert [(c["name"], c["ok"], c["value"]) for c in passport["checks"][:1]] == [
        ("clock band", True, "ok")
    ]
    assert passport["identity"]["tag"] == status["identity"]["tag"]


def test_pasting_the_app_id_ticks_the_waiting_step_and_its_later_steps_run(host: Host) -> None:
    host.through()
    host.keys.replace(APP_SECRET, STAGED_VALUE)

    ended = host.run({"fields": {"client_id": CLIENT_ID}})

    assert "ctrader-app: already done, skipped" in ended["lines"]
    assert ended["needs"]["card"] == "sign-in"
    assert waits(ended) == [
        f"sign-in: waiting; {ended['needs']['line']}",
        "self-test: waits for sign-in",
    ]
    assert host.keys_document() == {
        "schema_version": "qmx.node.keys/1",
        "ctrader": {"client_id": CLIENT_ID, "client_secret": STAGED_VALUE},
    }
    assert host.keys.read(APP_SECRET) is None
    assert host.rows() == {"pc": {"apps": ["trading-node", "mis"]}}
    again = host.run()
    assert "ctrader-app: already done, skipped" in again["lines"]
    assert again["needs"]["card"] == "sign-in"


class Killed(Exception):
    """The host dying in the middle of a step."""


def test_a_kill_between_folding_the_secret_and_deleting_it_leaves_no_second_copy(
    host: Host, monkeypatch: pytest.MonkeyPatch
) -> None:
    host.through()
    host.keys.replace(APP_SECRET, STAGED_VALUE)
    delete = host.keys.delete

    def killed_once(name: str) -> None:
        monkeypatch.setattr(host.keys, "delete", delete)
        raise Killed(name)

    monkeypatch.setattr(host.keys, "delete", killed_once)
    with pytest.raises(Killed):
        host.run({"fields": {"client_id": CLIENT_ID}})
    host.restart()

    ended = host.run()

    assert host.keys.read(APP_SECRET) is None
    assert host.keys_document() == {
        "schema_version": "qmx.node.keys/1",
        "ctrader": {"client_id": CLIENT_ID, "client_secret": STAGED_VALUE},
    }
    assert ended["needs"]["card"] == "sign-in"
    assert STAGED_VALUE not in json.dumps(ended)


def test_a_wrong_signature_publishes_nothing_and_a_restart_needs_no_new_one(host: Host) -> None:
    host.run()
    refused = host.run({"fields": {"signature": "0" * 64}})
    assert refused["needs"]["card"] == "signature"
    assert refused["needs"]["line"].endswith("That signature is not this version's; sign it again.")
    assert host.apps.status(NODE_APP)["status"] != "running"

    host.through()
    host.restart()
    ended = host.run()

    assert "signature: already done, skipped" in ended["lines"]
    assert "enable: the trading node runs on This PC" in ended["lines"]
    assert ended["needs"]["card"] == "ctrader-app"
    assert host.status()["headline"] == "Ready, no units yet"


STEPS = [step.name for step in on_this_pc().steps]


@pytest.mark.parametrize("killed_at", range(len(STEPS)), ids=STEPS)
def test_a_kill_at_any_step_and_a_rerun_converge_on_one_place_row(
    host: Host, killed_at: int
) -> None:
    host.keys.replace(APP_SECRET, STAGED_VALUE)
    cut = Kind(host.kind.id, host.kind.name, (), False, host.kind.steps[:killed_at])
    host.through(cut)
    host.restart()

    ended = host.run({"fields": {"client_id": CLIENT_ID}})
    if ended["needs"]["card"] == "signature":
        ended = host.through()
    again = host.run()

    assert [ended["needs"]["card"], again["needs"]["card"]] == ["sign-in", "sign-in"]
    assert host.rows() == {"pc": {"apps": ["trading-node", "mis"]}}
    assert host.keys_document()["ctrader"] == {
        "client_id": CLIENT_ID,
        "client_secret": STAGED_VALUE,
    }
    assert host.keys.read(APP_SECRET) is None
    assert host.status()["headline"] == "Ready, no units yet"
    listed = cast("list[dict[str, Any]]", host.apps.list())
    assert sorted(row["definition"]["id"] for row in listed) == [MIS_APP, NODE_APP]


def test_the_kind_is_registered_beside_the_shipped_kinds() -> None:
    assert list(KINDS)[-2] == "trading-node-pc"
    assert [step.name for step in KINDS["trading-node-pc"].steps] == [
        "ctrader-app",
        "keys",
        "clock",
        "install",
        "signature",
        "enable",
        "sign-in",
        "round-trip",
        "self-test",
        "passport",
        "row",
        "waiting",
    ]
