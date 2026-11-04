"""C-17: the trading-node kind on a server, run on the shipped step runner against a simulated
server host on loopback.

The server host is a real control service on its own throwaway QMX folder, served on a loopback
port with a bearer made here, and homed under the place name `london-1`. Its app secrets come from
its own vault, as a server host's do (`vault_secrets`). The SSH seam is the compute kind's fake
(`test_connect_compute.Server`) for the shipped server steps; every script the node's steps send
runs here for real, with the server's paths and port mapped onto that folder, so the setup's
loopback calls, his keys window and his signature window reach the server host itself.

What stands in: the road's three proofs (as in C-11), the server's clock probe (fixed facts), its
chrony and OpenObserve installs (the scripts are kept, not run), and the venues, which are a
loopback port that takes every handshake. Every key and token is made at runtime.
"""

from __future__ import annotations

import dataclasses
import json
import os
import secrets
import shlex
import socket
import subprocess
import sys
import threading
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import pytest
from qml.compile.compiler import CompileContext, CompiledUnit, compile_unit
from qmx_apps.supervisor import Supervisor
from qmx_control import node
from qmx_control.server import create_app
from qmx_control.service import ControlService
from qmx_home import Layout
from qmx_tools.gather import gather, template
from test_connect import Store, qmx_folder, world
from test_connect_compute import (
    ADDRESS,
    TAILNET,
    TAILSCALE,
    Server,
    engine,
    no_wait,
    source,
)
from test_connect_node import CLOCK, stand_in_proof
from test_host_route import Served, free_port

from qmx_host import connect_compute
from qmx_host.connect import KINDS, Kind, Run, Step, World, run_kind
from qmx_host.connect_logs import monitoring_script
from qmx_host.connect_node import (
    CLOCK as CLOCK_PROBE,
)
from qmx_host.connect_node import (
    MIS_APP,
    NODE_APP,
    NODE_KEYS,
    SERVER_APPS,
    SERVER_KIND,
    ServerPorts,
    Venue,
    on_a_server,
    server_setups,
)
from qmx_host.host import vault_secrets
from qmx_host.first_start import FIRST_PARTY
from qmx_host.jobs import Jobs, Stopped
from qmx_host.vault_acl import owner_only

PLACE = "london-1"
CLIENT_ID = "fixture-client-id"
TYPED_VALUE = "fixture-app-value"
REVISION = "b" * 40
SERVER_FOLDER = node.SERVER_FOLDER
APPS = Path(__file__).resolve().parents[3] / "apps"
AS_QMX = f"set -eu\nrunuser -u qmx -- {node.SERVER_VENV}/bin/python -I -c "
"""How every script the node's steps send to the server starts (`connect_node.as_qmx`)."""


class Simulated(Server):
    """The server as the setup reaches it over SSH: the compute kind's fake for the shipped
    steps, and for the node's steps a real run of what is sent, as `qmx` on the server host's
    folder. chrony's and OpenObserve's installs are kept as sent."""

    def __init__(self, far: Far) -> None:
        super().__init__()
        self.far = far
        self.chrony = False
        self.programs = True
        self.monitoring = False

    def __call__(self, command: list[str], stdin: str | None) -> str:
        line = command[-1]
        script = stdin or ""
        if line == "sudo bash -s" and script.startswith(AS_QMX):
            self.sent.append((list(command), stdin))
            return self.far.run_as_qmx(script)
        if line == "sudo bash -s" and node.SERVER_VENV not in script and "chrony.conf" in script:
            self.sent.append((list(command), stdin))
            self.chrony = True
            return ""
        if line == "sudo bash -s" and "otelcol.yaml" in script:
            self.sent.append((list(command), stdin))
            if not self.programs:
                raise RuntimeError("ssh failed (3); inspect the node logs.")
            self.monitoring = True
            return ""
        if line == "systemctl is-active chrony":
            if not self.chrony:
                raise RuntimeError("ssh failed (3); inspect the node logs.")
            return "active\n"
        if line == "systemctl is-active openobserve otelcol || true":
            return "active\nactive\n" if self.monitoring else "inactive\ninactive\n"
        return super().__call__(command, stdin)


class Window:
    """His terminal on This PC. The password window gives the server QMX's key, as his typing
    does; a window on the server runs there with what he types on its input."""

    def __init__(self, server: Simulated) -> None:
        self.server = server
        self.typed = f"{CLIENT_ID}\n{TYPED_VALUE}\n"
        self.titles: list[str] = []
        self.shown: list[str] = []

    def open(self, command: Sequence[str], title: str) -> None:
        self.titles.append(title)
        if connect_compute.COPY_KEY in command:
            self.server.authorized = True
            return
        remote = shlex.split(command[-1])
        assert remote[:5] == ["sudo", "runuser", "-u", "qmx", "--"], remote
        self.shown.append(self.server.far.execute(remote[5:], self.typed))

    def signature(self) -> str:
        return self.shown[-1].split("\n\n")[1].strip()


class Far:
    """The server host: a control service on its own QMX folder, homed `london-1`, its vault the
    reader of its apps' secrets, served on a loopback port with a bearer made here."""

    def __init__(self, layout: Layout, envs: Path) -> None:
        self.layout = layout
        self.envs = envs
        self.token = secrets.token_urlsafe(32)
        keys = layout.root / "keys"
        keys.mkdir(parents=True, exist_ok=True)
        (keys / "control-token").write_text(self.token + "\n", encoding="utf-8")
        owner_only(layout.home / "vault")
        self.port = free_port()
        self.control = self._control()
        self.served = Served(create_app(self.control, self.token), self.port)

    def _control(self) -> ControlService:
        control = ControlService(
            self.layout.home, secret_getter=vault_secrets(self.layout.home / "vault")
        )
        control.place = PLACE
        control.app_runtime().environments = self.envs
        return control

    @property
    def apps(self) -> Supervisor:
        return self.control.app_runtime()

    def close(self) -> None:
        self.served.close()
        self.control.close()

    def on_disk(self, text: str) -> str:
        return (
            text.replace(SERVER_FOLDER, self.layout.root.as_posix())
            .replace(SERVER_APPS, APPS.as_posix())
            .replace(node.SERVER_VENV + "/bin/python", Path(sys.executable).as_posix())
        )

    def execute(self, argv: list[str], given: str | None) -> str:
        """One `python -I -c <script> <args>` the server runs as `qmx`. The clock probe answers
        the fixed facts; the host's port 8766 is this host's loopback port."""
        python, isolated, flag, script, *args = argv
        assert (isolated, flag) == ("-I", "-c"), argv
        if script == CLOCK_PROBE:
            return CLOCK.model_dump_json() + "\n"
        port = str(node.host_port(node.host_unit()))
        args = [str(self.port) if arg == port else self.on_disk(arg) for arg in args]
        ran = subprocess.run(
            [self.on_disk(python), "-I", "-c", script, *args],
            input=None if given is None else self.on_disk(given),
            capture_output=True,
            text=True,
            check=False,
            timeout=1200,
        )
        if ran.returncode:
            raise RuntimeError(f"ssh failed ({ran.returncode}); {ran.stderr[-800:]}")
        return ran.stdout

    def run_as_qmx(self, shell: str) -> str:
        """The one `runuser -u qmx --` line of an `as_qmx` script, with its heredoc input."""
        body = shell.removeprefix("set -eu\n")
        line, marked, rest = body.partition(" <<'QMXIN'\n")
        given = rest.removesuffix("\nQMXIN\n") if marked else None
        argv = shlex.split(line)
        assert argv[:4] == ["runuser", "-u", "qmx", "--"], argv[:4]
        return self.execute(argv[4:], given)

    def keys_document(self) -> dict[str, Any] | None:
        path = self.layout.home / "vault" / NODE_KEYS.removeprefix("qmx/")
        return (
            cast("dict[str, Any]", json.loads(path.read_text("utf-8"))) if path.is_file() else None
        )


@pytest.fixture(scope="module")
def envs(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One locked environment per app, shared by every server here."""
    return tmp_path_factory.mktemp("envs")


@pytest.fixture(scope="module")
def venue() -> Iterator[int]:
    """A loopback port that takes every handshake, standing in for both venues."""
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


class Setup:
    """This PC's dialog and the server host it sets up."""

    def __init__(self, root: Path, envs: Path, venue: int) -> None:
        self.far = Far(qmx_folder(root / "server"), envs)
        self.server = Simulated(self.far)
        self.window = Window(self.server)
        self.keys = Store()
        self.layout = qmx_folder(root / "pc")
        self.pc = world(self.layout, keys=self.keys)
        self.ports = ServerPorts(
            prove=lambda _apps, app, digest: stand_in_proof(self.far.apps, app, digest),
            venues=(
                Venue("ctrader", "demo", "127.0.0.1", venue),
                Venue("hyperliquid", "testnet", "127.0.0.1", venue),
            ),
            now=lambda: 1_793_620_800.0,
        )
        self.kind = on_a_server(self.ports)
        self.dialog = self._world()
        self.said: list[str] = []
        """Every line every run said, in order."""

    def _world(self) -> World:
        compute = connect_compute.Ports(
            shell=self.server,
            terminal=self.window,
            sleep=no_wait,
            revision=lambda: REVISION,
            archive=source,
            post=engine,
        )
        return dataclasses.replace(self.pc, jobs=Jobs(), remembered={}, compute=compute)

    def restart(self) -> None:
        """This PC's host died and came back: what the dialog remembered is gone."""
        self.dialog = self._world()

    def run(self, answer: dict[str, object] | None = None, kind: Kind | None = None) -> Any:
        def quiet(step: str, *, done: int = 0, total: int = 0, **counts: int) -> None:
            del step, done, total, counts

        ended = run_kind(kind or self.kind, PLACE, answer or {}, report=quiet, world=self.dialog)
        self.said.extend(cast("list[str]", ended["lines"]))
        return ended

    def answer(self, card: str) -> dict[str, object]:
        """What he answers each card with: his server's cards, then the node's."""
        if card == "secret":
            self.keys.replace(f"qmx/connect/{PLACE}/tailscale", TAILSCALE)
        if card == "signature":
            return {"fields": {"signature": self.window.signature()}}
        fields = {
            "choose": {"chosen": "yes"},
            "address": {"address": ADDRESS},
            "secret": {},
            "password": {},
            "firewall": {"approve": "yes"},
            "ctrader-app": {"approved": "yes"},
        }[card]
        return {"fields": fields}

    def through(self, kind: Kind | None = None) -> dict[str, Any]:
        """Run the kind, answering each card as he does, until only his sign-in waits."""
        ended = cast("dict[str, Any]", self.run(kind=kind))
        for _ in range(20):
            needs = cast("dict[str, Any] | None", ended.get("needs"))
            if needs is None or needs["card"] == "sign-in":
                return ended
            ended = cast("dict[str, Any]", self.run(self.answer(needs["card"]), kind))
        raise AssertionError(f"the setup still asks: {ended.get('needs')}")

    def rows(self) -> dict[str, Any]:
        control = cast("ControlService", self.pc.control)
        engine_section = control.settings_get(cast("Any", "engine"))
        return cast("dict[str, Any]", engine_section.get("placement") or {})

    def node_status(self) -> dict[str, Any]:
        called = self.far.apps.call(NODE_APP, "status", {})
        return cast("dict[str, Any]", cast("dict[str, Any]", called["result"])["value"])

    def close(self) -> None:
        self.far.close()
        cast("ControlService", self.pc.control).close()


@pytest.fixture
def setup(tmp_path: Path, envs: Path, venue: int) -> Iterator[Setup]:
    made = Setup(tmp_path, envs, venue)
    try:
        yield made
    finally:
        made.close()


def sent_with(server: Simulated, mark: str) -> list[str]:
    return [stdin or "" for _command, stdin in server.sent if mark in (stdin or "")]


def files_holding(root: Path, value: str) -> list[str]:
    """Every file under `root` holding `value`. A lock file a running store holds open on Windows
    cannot be read, and holds no value."""
    found: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix == ".lock":
            continue
        if value.encode() in path.read_bytes():
            found.append(path.relative_to(root).as_posix())
    return found


def test_a_server_is_set_up_with_the_node_and_the_mis_homed_under_its_own_name(
    setup: Setup,
) -> None:
    ended = setup.through()

    assert ended["needs"]["card"] == "sign-in"
    assert ended["step"] == "waiting"
    row = setup.rows()[PLACE]
    assert (row["provider"], row["kind"], row["apps"]) == ("ssh", "owned", [NODE_APP, MIS_APP])
    assert row["host"] == f"root@{TAILNET}"
    assert setup.far.apps.home_of(NODE_APP) == PLACE
    assert setup.far.apps.status(NODE_APP)["status"] == "running"
    assert setup.far.apps.status(MIS_APP)["status"] == "running"
    assert json.loads((setup.far.layout.home / FIRST_PARTY).read_text("utf-8")) == {
        "enable": [NODE_APP, MIS_APP]
    }
    assert setup.node_status()["headline"] == "Ready, no units yet"
    lines = setup.said
    assert "enable: the trading node runs on london-1" in lines
    assert "enable: mis runs beside it" in lines
    assert f"row: {PLACE} is home to {NODE_APP}, {MIS_APP} in your machines" in lines
    assert setup.window.titles == [
        f"QMX: sign in to {PLACE}",
        f"QMX: sign the trading node on {PLACE}",
        f"QMX: {PLACE}'s cTrader trading app",
    ]


def test_his_keys_are_typed_on_the_server_and_never_reach_this_pc(setup: Setup) -> None:
    setup.through()

    assert setup.far.keys_document() == {
        "schema_version": "qmx.node.keys/1",
        "ctrader": {"client_id": CLIENT_ID, "client_secret": TYPED_VALUE},
    }
    vault = setup.far.layout.home / "vault" / "trading-node-keys"
    if os.name == "posix":
        assert vault.stat().st_mode & 0o777 == 0o600
    assert setup.keys.read(NODE_KEYS) is None
    assert files_holding(setup.layout.root, TYPED_VALUE) == []
    assert all(TYPED_VALUE not in (stdin or "") for _command, stdin in setup.server.sent)
    assert files_holding(setup.far.layout.root, TYPED_VALUE) == ["data/vault/trading-node-keys"]
    read = vault_secrets(setup.far.layout.home / "vault")(NODE_KEYS, "trading-node")
    assert json.loads(read or "null")["ctrader"]["client_id"] == CLIENT_ID


def test_chrony_openobserve_and_the_round_trip_run_on_the_server(setup: Setup) -> None:
    ended = setup.through()

    assert sent_with(setup.server, "chrony.conf")[0].count("iburst\n") == 4
    assert (
        "server 0.pool.ntp.org iburst\nserver 1.pool.ntp.org iburst\n"
        "server 2.pool.ntp.org iburst\nserver 3.pool.ntp.org iburst\n"
    ) in sent_with(setup.server, "chrony.conf")[0]
    monitoring = sent_with(setup.server, "otelcol.yaml")
    assert monitoring == [monitoring_script(TAILNET)]
    assert f"Environment=ZO_HTTP_ADDR={TAILNET}\n" in monitoring[0]
    assert f"Environment=OO_OTLP_ENDPOINT=http://{TAILNET}:5080/api/default\n" in monitoring[0]
    assert "0.0.0.0" not in monitoring[0].split("otelcol.yaml <<")[0]  # noqa: S104
    passport_file = setup.layout.home / f"trading-node-passport.{PLACE}.json"
    passport = json.loads(passport_file.read_text(encoding="utf-8"))
    assert [(r["venue"], r["environment"], r["samples"]) for r in passport["round_trip"]] == [
        ("ctrader", "demo", 8),
        ("hyperliquid", "testnet", 8),
    ]
    assert [(c["name"], c["ok"], c["value"]) for c in passport["checks"][:1]] == [
        ("clock band", True, "ok")
    ]
    trips = [line for line in ended["lines"] if line.startswith("round trip: ")]
    assert [line.endswith("over 8 of 8 handshakes, measured on london-1") for line in trips] == [
        True,
        True,
    ]
    assert f"clock: {PLACE} Clock 3 ms off fixture (round trip 10 ms), band ok" in " | ".join(
        ended["lines"]
    )


def test_a_wrong_signature_publishes_nothing_and_he_is_asked_again(setup: Setup) -> None:
    first = setup.run()
    while first["needs"]["card"] != "signature":
        first = setup.run(setup.answer(first["needs"]["card"]))

    refused = setup.run({"fields": {"signature": "0" * 64}})

    assert refused["needs"]["card"] == "signature"
    assert refused["needs"]["line"].endswith("That signature is not this version's; sign it again.")
    assert setup.far.apps.status(NODE_APP)["status"] != "running"
    ended = setup.through()
    assert ended["needs"]["card"] == "sign-in"
    assert setup.far.apps.status(NODE_APP)["status"] == "running"


NODE_STEPS = [step.step.name for step in server_setups(ServerPorts())]


class Killed(BaseException):
    """This PC's host dying right after a step did its work."""


def killing(kind: Kind, at: str) -> Kind:
    """`kind` with the host dying right after step `at` does its work, before the runner goes on."""

    def died(do: Any) -> Any:
        def done(run: Run) -> Any:
            do(run)
            raise Killed(at)

        return done

    steps = tuple(
        Step(s.name, s.who, s.check, died(s.do)) if s.name == at else s for s in kind.steps
    )
    return dataclasses.replace(kind, steps=steps)


def test_a_kill_after_each_node_step_and_a_rerun_converge_on_one_place_row(setup: Setup) -> None:
    killed: list[str] = []
    for at in NODE_STEPS:
        try:
            setup.through(killing(setup.kind, at))
        except Killed:
            killed.append(at)
        setup.restart()

    ended = setup.through()
    again = setup.through()

    assert killed == NODE_STEPS
    assert [ended["needs"]["card"], again["needs"]["card"]] == ["sign-in", "sign-in"]
    assert list(setup.rows()) == [PLACE]
    assert setup.rows()[PLACE]["apps"] == [NODE_APP, MIS_APP]
    listed = cast("list[dict[str, Any]]", setup.far.apps.list())
    assert sorted(row["definition"]["id"] for row in listed) == [MIS_APP, NODE_APP]
    assert len(setup.far.apps.versions(NODE_APP)) == 1
    assert setup.far.keys_document() == {
        "schema_version": "qmx.node.keys/1",
        "ctrader": {"client_id": CLIENT_ID, "client_secret": TYPED_VALUE},
    }
    assert setup.node_status()["headline"] == "Ready, no units yet"
    assert len(sent_with(setup.server, "chrony.conf")) == 1


def test_openobserve_binds_only_a_tailscale_address() -> None:
    rendered = monitoring_script("100.101.102.103")
    assert "Environment=ZO_HTTP_ADDR=100.101.102.103\n" in rendered
    assert "Environment=ZO_GRPC_ADDR=100.101.102.103\n" in rendered
    assert "@TAILNET_ADDRESS@" not in rendered
    for wrong in ("0.0.0.0", ADDRESS, "127.0.0.1", "london-1"):  # noqa: S104
        with pytest.raises(Stopped) as refused:
            monitoring_script(wrong)
        assert refused.value.line == (
            f"the server's tailnet address reads {wrong!r}, which is not a Tailscale address; "
            "check `tailscale ip -4` there, then connect its deep logs again"
        )


def test_the_dummy_compiles_to_one_fingerprint_from_a_windows_or_a_linux_checkout() -> None:
    document = template()
    context = gather(None, document).context
    lf = {pin: code.replace(b"\r\n", b"\n") for pin, code in context.sources.items()}
    crlf = {pin: code.replace(b"\n", b"\r\n") for pin, code in lf.items()}
    found = {
        name: compile_unit(document, CompileContext(sources, context.entries, context.records))
        for name, sources in (("lf", lf), ("crlf", crlf))
    }

    assert all(isinstance(unit, CompiledUnit) for unit in found.values()), found
    prints = {cast("CompiledUnit", unit).compiled_fingerprint.value for unit in found.values()}
    assert len(prints) == 1
    assert prints.pop().startswith("fp1:sha256:")


def test_the_server_kind_is_registered_after_this_pcs() -> None:
    assert list(KINDS)[-2:] == ["trading-node-pc", SERVER_KIND]
    assert [step.name for step in KINDS[SERVER_KIND].steps][-14:] == [*NODE_STEPS, "waiting"]
    assert NODE_STEPS == [
        "ctrader-app",
        "keys",
        "chrony",
        "clock",
        "openobserve",
        "install",
        "signature",
        "enable",
        "sign-in",
        "round-trip",
        "self-test",
        "passport",
        "apps-row",
    ]
