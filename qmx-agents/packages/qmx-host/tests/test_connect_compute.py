"""The compute kinds (design 06 section 9): his server through five cards and `qmx node setup`'s
own checked steps against a fake shell, keeping copies there, and Modal and E2B by key."""

from __future__ import annotations

import dataclasses
import http.server
import json
import os
import shlex
import shutil
import socket
import subprocess
import sys
import threading
import tomllib
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar, cast

import pytest
from pydantic import JsonValue
from qmx_control import node
from qmx_engine.ledger.store import Ledger
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.roles import Candidate
from qmx_engine.service.forward import owned_instances, placement_rows
from qmx_engine.settings import places
from qmx_engine.triggers.preflight import placement_kind, plan_on_provider
from qmx_home.files import plain
from test_connect import Store, qmx_folder, world

from qmx_host import connect_compute
from qmx_host.connect import KINDS, Run, World, run_kind
from qmx_host.connect_compute import SMOKE_FOLDER, Ports
from qmx_host.host import remote_worker
from qmx_host.jobs import Stopped

REVISION = "a" * 40
PLACE = "myserver"
ADDRESS = "203.0.113.7"
TAILNET = "100.64.0.9"
TAILSCALE = "tskey-auth-planted-5531"
LOGIN = f"root@{ADDRESS}"
needs_rclone = pytest.mark.skipif(shutil.which("rclone") is None, reason="rclone is not on PATH")


class Killed(BaseException):
    """The host process dying in the middle of a step."""


class Server:
    """A fresh Ubuntu server as the setup reaches it over ssh: what it was sent, what it holds,
    and what it answers. `kill` names a step whose script kills the host as it is sent."""

    def __init__(self, kill: str = "") -> None:
        self.sent: list[tuple[list[str], str | None]] = []
        self.marks: set[str] = set()
        self.joined = False
        self.authorized = False
        self.running = False
        self.closed = False
        self.kill = kill

    def __call__(self, command: list[str], stdin: str | None) -> str:
        line = command[-1]
        self.sent.append((list(command), stdin))
        if line == "true":
            if not self.authorized:
                raise RuntimeError("ssh failed (255); inspect the node logs.")
            return ""
        if line.startswith(f"sudo ls {node.SETUP_MARKS}/"):
            return "\n".join(sorted(self.marks))
        if f"touch {node.SETUP_MARKS}/" in line:
            self.marks.add(line.rsplit("/", 1)[1].rstrip("'"))
            return ""
        if line == "tailscale ip -4":
            if not self.joined:
                raise RuntimeError("tailscale failed (1); inspect the node logs.")
            return f"{TAILNET}\n"
        if line == "sudo bash -s":
            script = stdin or ""
            if self.kill and self.kill in script:
                raise Killed
            if "tailscale up --auth-key=file:" in script:
                self.joined = True
            if "systemctl enable --now qmx-host" in script:
                self.running = True
            if f"{node.RECOVER} firewall close" in script:
                self.closed = True
            if SMOKE in script:
                return self.smoke(script)
            return ""
        if line == "systemctl is-active qmx-host":
            if not self.running:
                raise RuntimeError("ssh failed (3); inspect the node logs.")
            return "active\n"
        if line.startswith("sudo cat "):
            return "pairing-code\n"
        if line.endswith("firewall status"):
            if not self.closed:
                return "firewall    off: every port is open  FAIL"
            return "firewall    on: only SSH, Tailscale and QMX's containers get in  PASS"
        if line.endswith(f"{node.RECOVER} status || true"):
            return (
                "host        qmx-host is running  PASS\n"
                "firewall    on: only SSH, Tailscale and QMX's containers get in  PASS\n"
                "monitoring  openobserve is not installed on this server  FAIL"
            )
        return "PASS host"

    def smoke(self, script: str) -> str:
        del script
        return "run-smoke\n"

    def scripts(self) -> list[str]:
        return [stdin or "" for command, stdin in self.sent if command[-1] == "sudo bash -s"]


SMOKE = SMOKE_FOLDER
"""What names the smoke's script among the scripts a server is sent."""


class Hosted(Server):
    """A server whose host is up and holds the engine's ledger: its smoke script runs here as the
    server runs it, its folders under `root` and its venv's python this one."""

    def __init__(self, root: Path) -> None:
        super().__init__()
        self.root = root

    def on_disk(self, text: str) -> str:
        text = text.replace(f"{node.SERVER_VENV}/bin/python", Path(sys.executable).as_posix())
        for top in ("/var/lib/qmx", "/srv/qmx"):
            text = text.replace(top, (self.root / top.lstrip("/")).as_posix())
        return text

    def smoke(self, script: str) -> str:
        lines = iter(self.on_disk(script).splitlines())
        said = ""
        for line in lines:
            if line.startswith("cat > ") and "<<'" in line:
                target, mark = line[len("cat > ") :].split(" <<'")
                body = "\n".join(iter(lambda: next(lines), mark.rstrip("'")))
                Path(target).parent.mkdir(parents=True, exist_ok=True)
                Path(target).write_text(body + "\n", encoding="utf-8")
            elif line.startswith("runuser -u qmx -- "):
                ran = subprocess.run(
                    shlex.split(line.removeprefix("runuser -u qmx -- ")),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if ran.returncode:
                    raise RuntimeError(f"ssh failed ({ran.returncode}): {ran.stderr[-600:]}")
                said += ran.stdout
        return said


class Door(http.server.BaseHTTPRequestHandler):
    """The server's host on its loopback: it takes the smoke's draft and test with its bearer and
    answers the run it started."""

    calls: ClassVar[list[tuple[str, str, str, bytes]]] = []

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def reply(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        Door.calls.append((self.command, self.path, self.headers.get("Authorization", ""), body))
        answer = {"run": {"run_id": "run-on-the-server", "status": "passed"}}
        text = json.dumps(answer).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(text)))
        self.end_headers()
        self.wfile.write(text)

    do_PUT = do_POST = reply


class Window:
    """His terminal: opening it is his typing the password, which gives the server QMX's key."""

    def __init__(self, server: Server) -> None:
        self.server = server
        self.opened: list[list[str]] = []

    def open(self, command: Sequence[str], title: str) -> None:
        del title
        self.opened.append(list(command))
        self.server.authorized = True


def engine(url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str]) -> JsonValue:
    del url, headers
    args = cast("dict[str, JsonValue]", body["args"])
    return {"ok": True, "value": {"run_id": args["run_id"], "status": "passed"}}


def no_wait(_seconds: float) -> None:
    pass


def source(_revision: str) -> bytes:
    return b"the source"


def ports_for(server: Server, **changed: Any) -> Ports:
    given: dict[str, Any] = {
        "shell": server,
        "terminal": Window(server),
        "sleep": no_wait,
        "revision": lambda: REVISION,
        "archive": source,
        "post": engine,
    }
    return Ports(**(given | changed))


def at(tmp_path: Path, server: Server, keys: Store | None = None, **changed: Any) -> World:
    found = world(qmx_folder(tmp_path / "QMX"), keys=keys or Store())
    return dataclasses.replace(found, compute=ports_for(server, **changed))


def quiet(step: str, *, done: int = 0, total: int = 0, **counts: int) -> None:
    del step, done, total, counts


def answered(_url: str, _headers: Mapping[str, str]) -> int:
    return 200


def once(there: World, kind: str, answer: Mapping[str, object]) -> Mapping[str, Any]:
    return run_kind(KINDS[kind], PLACE, answer, report=quiet, world=there)


def through_the_cards(there: World) -> list[str]:
    """Answer his five cards in order; the cards he saw."""
    seen: list[str] = []
    answers: list[Mapping[str, object]] = [
        {},
        {"fields": {"chosen": "yes"}},
        {"fields": {"address": ADDRESS}},
        {"key": f"qmx/connect/{PLACE}/tailscale"},
        {},
        {"fields": {"approve": "yes"}},
    ]
    for answer in answers:
        if answer.get("key"):
            there.keys.replace(str(answer["key"]), TAILSCALE)
        ended = once(there, "server", answer)
        needs = ended.get("needs")
        if needs is None:
            return seen
        seen.append(cast("dict[str, Any]", needs)["card"])
    raise AssertionError(f"the server job still asks after {seen}")


def names(server: Server, revision: str = REVISION) -> list[str]:
    """Which setup step each script the server got belongs to."""
    by_script = {
        step.script: step.name
        for step in node.setup_steps(revision, machine=PLACE, pc_name=socket.gethostname().lower())
    }
    found: list[str] = []
    for script in server.scripts():
        if script in by_script:
            found.append(by_script[script])
        elif "tailscale up --auth-key=file:" in script:
            found.append("join the tailnet")
        elif SMOKE in script:
            found.append("smoke")
        else:
            found.append(script[:40])
    return found


def stored(there: World) -> dict[str, Any]:
    return tomllib.loads((there.layout.home / "settings.toml").read_text(encoding="utf-8"))


def test_the_server_kind_and_qmx_node_setup_send_one_list_and_make_the_same_pc_writes(
    tmp_path: Path,
) -> None:
    kind_server = Server()
    there = at(tmp_path / "kind", kind_server)
    cards = through_the_cards(there)
    cli_server = Server()
    cli_server.authorized = True
    cli_home = tmp_path / "cli"
    cli_home.mkdir()
    done = node.setup(
        LOGIN,
        cli_home,
        machine=PLACE,
        revision=REVISION,
        call=cli_server,
        say=lambda _line: None,
        sleep=lambda _s: None,
        auth_key=lambda: TAILSCALE,
    )

    assert cards == ["choose", "address", "secret", "password", "firewall"]
    assert done == 0
    assert [n for n in names(kind_server) if n != "smoke"] == names(cli_server)
    assert names(cli_server) == [step.name for step in node.setup_steps(REVISION, machine=PLACE)]
    kind_home = there.layout.home
    key = "vault/pairing-key"
    assert (kind_home / key).read_text("utf-8") == (cli_home / key).read_text("utf-8")
    twin = "bin/qmx-recover.conf"
    assert (kind_home / twin).read_text("utf-8").splitlines()[:3] == [
        f"TARGET={LOGIN}",
        f"SERVER_TAILNET={TAILNET}",
        "SERVER_HOME=/srv/qmx/home/.qmx/data",
    ]
    assert (cli_home / twin).read_text("utf-8").splitlines()[:3] == (
        (kind_home / twin).read_text("utf-8").splitlines()[:3]
    )
    assert stored(there)["library"] == {"hub_url": f"http://{TAILNET}:8766"}
    with (cli_home / "settings.toml").open("rb") as cli_settings:
        assert tomllib.load(cli_settings)["library"] == stored(there)["library"]


def test_the_server_row_reaches_the_forwarder_and_the_provider_worker_and_reads_healthy(
    tmp_path: Path,
) -> None:
    server = Server()
    there = at(tmp_path, server)
    through_the_cards(there)
    ended = once(there, "server", {})
    control = there.control
    assert control is not None
    row = stored(there)["engine"]["placement"][PLACE]
    settings = ControlSettings(control).values()

    assert {k: v for k, v in row.items() if k != "id"} == {
        "provider": "ssh",
        "kind": "owned",
        "host": f"root@{TAILNET}",
        "login": LOGIN,
        "root": "/srv/qmx/home",
        "engine_url": f"http://{TAILNET}:8766",
        "gateway_url": f"http://{TAILNET}:8766",
        "attempt_cpus": 2,
        "attempt_timeout": "2h",
        "can": ["run"],
    }
    assert [i.name for i in owned_instances(placement_rows(settings), home="pc")] == [PLACE]
    worker = remote_worker(
        there.layout.home, cast("Any", SimpleNamespace(settings=settings)), cast("Any", None)
    )
    assert worker is not None and set(worker.providers) == {PLACE}
    lines = cast("list[str]", ended["lines"])
    assert (
        f"{PLACE}: available → configured → authorized → reachable → healthy: it is healthy"
        in lines
    )
    assert lines[-3:] == [
        f"{PLACE}: host: qmx-host is running",
        f"{PLACE}: firewall: on: only SSH, Tailscale and QMX's containers get in",
        f"{PLACE}: monitoring: openobserve is not installed on this server (this needs you)",
    ]


@contextmanager
def door() -> Generator[int]:
    Door.calls = []
    served = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Door)
    threading.Thread(target=served.serve_forever, daemon=True).start()
    try:
        yield int(served.server_address[1])
    finally:
        served.shutdown()
        served.server_close()


def test_the_smoke_runs_through_the_servers_own_host_while_it_holds_the_engines_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    server = Hosted(tmp_path / "server")
    folder = qmx_folder(server.root / node.SERVER_FOLDER.lstrip("/"))
    folder.keys.mkdir(parents=True, exist_ok=True)
    (folder.keys / "control-token").write_text("the-servers-bearer\n", encoding="utf-8")
    asked: list[Mapping[str, JsonValue]] = []

    def read_back(url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str]) -> JsonValue:
        asked.append(body)
        return engine(url, body, headers)

    with door() as port, Ledger.open(folder.home):

        def door_port(_unit: str) -> int:
            return port

        monkeypatch.setattr(node, "host_port", door_port)
        there = at(tmp_path / "pc", server, post=read_back)
        through_the_cards(there)
        Door.calls.clear()
        asked.clear()
        ended = once(there, "server", {})

    assert [(c[0], c[1], c[2]) for c in Door.calls] == [
        ("PUT", "/api/settings/engine", "Bearer the-servers-bearer"),
        ("PUT", "/api/workflows/qmx-smoke/draft", "Bearer the-servers-bearer"),
        ("POST", "/api/workflows/qmx-smoke/test?fake=true", "Bearer the-servers-bearer"),
    ]
    assert json.loads(Door.calls[0][3]) == {"placement": {PLACE: {"kind": "owned"}}}
    assert json.loads(Door.calls[1][3]) == {
        "schema": "qmx.workflow/1",
        "id": "qmx-smoke",
        "name": "QMX smoke test",
        "nodes": [
            {
                "id": "start",
                "name": "start",
                "type": "trigger",
                "typeVersion": 1,
                "runs_on": PLACE,
                "parameters": {"kinds": ["manual"]},
            }
        ],
        "connections": {},
    }
    assert asked == [{"verb": "runs.get", "args": {"run_id": "run-on-the-server"}}]
    assert (
        f"{PLACE}: a one-node workflow ran on the server's engine and passed (run-on-the-server)"
        in cast("list[str]", ended["lines"])
    )


@pytest.mark.parametrize(
    "killed", [step.name for step in node.setup_steps(REVISION, machine=PLACE)]
)
def test_a_rerun_after_a_kill_at_any_step_sends_only_what_did_not_finish_and_writes_one_row(
    tmp_path: Path, killed: str
) -> None:
    script = next(
        step.script or "tailscale up"
        for step in node.setup_steps(REVISION, machine=PLACE, pc_name=socket.gethostname().lower())
        if step.name == killed
    )
    server = Server(kill=script)
    there = at(tmp_path, server)
    with pytest.raises(Killed):
        through_the_cards(there)
    before = len(server.scripts())
    server.kill = ""
    fresh = dataclasses.replace(there, remembered={}, compute=ports_for(server))
    ended = once(
        fresh, "server", {"fields": {"chosen": "yes", "address": ADDRESS, "approve": "yes"}}
    )
    second = names(server)[before:]

    every = [step.name for step in node.setup_steps(REVISION, machine=PLACE)]
    assert ended["needs"] is None
    assert second == [*every[every.index(killed) :], "smoke"]
    assert list(stored(there)["engine"]["placement"]) == [PLACE]


@pytest.mark.parametrize(
    ("undone", "rerun"), [("running", "start the host"), ("closed", "close the firewall")]
)
def test_a_rerun_at_the_same_revision_does_again_a_step_undone_since_it_ran(
    tmp_path: Path, undone: str, rerun: str
) -> None:
    server = Server()
    there = at(tmp_path, server)
    through_the_cards(there)
    before = len(server.scripts())
    setattr(server, undone, False)
    ended = once(there, "server", {})

    assert ended["needs"] is None
    assert names(server)[before:] == [rerun, "smoke"]


def test_the_tailscale_key_reaches_the_server_in_a_file_and_never_in_a_command_line(
    tmp_path: Path,
) -> None:
    server = Server()
    there = at(tmp_path, server)
    through_the_cards(there)

    holding = [(command, stdin) for command, stdin in server.sent if TAILSCALE in (stdin or "")]
    assert holding == [
        (
            [*holding[0][0][:-1], "sudo bash -s"],
            "set -eu\n"
            "umask 077\n"
            "trap 'rm -f /run/qmx-tailscale-key' EXIT\n"
            "IFS= read -r key\n"
            f"{TAILSCALE}\n"
            '[ -n "$key" ]\n'
            "printf '%s\\n' \"$key\" > /run/qmx-tailscale-key\n"
            "unset key\n"
            "tailscale up --auth-key=file:/run/qmx-tailscale-key\n",
        )
    ]
    assert not [command for command, _stdin in server.sent if TAILSCALE in " ".join(command)]


def test_the_password_window_runs_ssh_with_qmxs_public_key_and_no_secret(tmp_path: Path) -> None:
    server = Server()
    there = at(tmp_path, server)
    through_the_cards(there)
    window = cast("Window", cast("Ports", there.compute).terminal)

    [command] = window.opened
    public = there.layout.keys / f"{PLACE}-ssh.pub"
    assert command[4:6] == [str(public), "ssh"]
    assert command[-2:] == [
        LOGIN,
        "umask 077; mkdir -p ~/.ssh && touch ~/.ssh/authorized_keys && key=$(cat) && "
        '{ grep -qxF "$key" ~/.ssh/authorized_keys || printf \'%s\\n\' "$key" >> '
        "~/.ssh/authorized_keys; }",
    ]
    assert public.read_text("utf-8").startswith("ssh-ed25519 ")
    assert TAILSCALE not in " ".join(command)


@pytest.mark.skipif(os.name != "nt", reason="the key's owner-only ACL is set by icacls on Windows")
def test_a_key_windows_will_not_make_owner_only_is_removed_and_the_job_stops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("USERNAME", "")
    there = at(tmp_path, Server())
    with pytest.raises(Stopped) as stopped:
        through_the_cards(there)

    assert stopped.value.line == (
        f"{PLACE}: Windows would not make QMX's key in {plain(there.layout.keys)} readable by "
        "you alone, so QMX removed it; check you own that folder, then answer again"
    )
    assert not (there.layout.keys / f"{PLACE}-ssh").exists()


class Mistyped(Window):
    """His window, where the password he typed was wrong each time."""

    def open(self, command: Sequence[str], title: str) -> None:
        del title
        self.opened.append(list(command))


def test_a_login_that_still_fails_reopens_the_window_only_when_he_asks(tmp_path: Path) -> None:
    server = Server()
    there = at(tmp_path, server)
    window = Mistyped(server)
    there.compute = dataclasses.replace(cast("Ports", there.compute), terminal=window)
    answers: list[Mapping[str, object]] = [
        {"fields": {"chosen": "yes"}},
        {"fields": {"address": ADDRESS}},
        {},
        {},
        {"fields": {"again": "yes"}},
    ]
    there.keys.replace(f"qmx/connect/{PLACE}/tailscale", TAILSCALE)
    asked = [cast("dict[str, Any]", once(there, "server", a)["needs"]) for a in answers]

    assert [needs["card"] for needs in asked] == ["address", *["password"] * 4]
    assert len(window.opened) == 2
    assert (
        asked[2]["line"]
        == asked[3]["line"]
        == (
            f"{PLACE}: QMX still cannot sign in with its own key. If the window said it did not "
            "work, answer yes and QMX opens it once more"
        )
    )
    assert asked[4]["line"].startswith(f"{PLACE}: type the server's password in the window")


def test_a_server_name_that_cannot_be_a_tailnet_name_is_refused_before_anything_runs(
    tmp_path: Path,
) -> None:
    there = at(tmp_path, Server())
    refusal = KINDS["server"].refusal
    assert refusal is not None
    assert refusal(Run(KINDS["server"], "My_Server", {}, there)) == (
        "'My_Server' cannot name a server: a server's name is also its tailnet name, so use "
        "lowercase letters, digits and -"
    )


def provider_check(good: dict[str, str]) -> Any:
    seen: list[tuple[str, dict[str, str]]] = []

    def probe(url: str, headers: Mapping[str, str]) -> int:
        seen.append((url, dict(headers)))
        return 200 if all(headers.get(k) == v for k, v in good.items()) else 401

    probe.seen = seen  # type: ignore[attr-defined]
    return probe


@pytest.mark.parametrize(
    ("kind", "keys", "header", "provider_kind"),
    [
        (
            "modal",
            {"qmx/modal-token-id": "ak-planted", "qmx/modal-token-secret": "as-planted"},
            {"x-modal-token-id": "ak-planted", "x-modal-token-secret": "as-planted"},
            "serverless",
        ),
        ("e2b", {"qmx/e2b": "e2b-planted"}, {"X-API-Key": "e2b-planted"}, "managed_agent_host"),
    ],
)
def test_a_key_kind_asks_for_its_keys_tests_them_once_and_writes_a_provider_row(
    tmp_path: Path,
    kind: str,
    keys: dict[str, str],
    header: dict[str, str],
    provider_kind: str,
) -> None:
    probe = provider_check(header)
    there = at(tmp_path, Server(), probe=probe, urls={kind: "http://127.0.0.1:1/check"})
    cards: list[str] = []
    for name, value in keys.items():
        needs = once(there, kind, {})["needs"]
        cards.append(needs["key"])
        there.keys.replace(name, value)
    ended = once(there, kind, {})
    row = stored(there)["engine"]["placement"][PLACE]

    assert cards == list(keys)
    assert ended["needs"] is None
    assert probe.seen == [("http://127.0.0.1:1/check", header)]
    assert {k: v for k, v in row.items() if k != "id"} == {
        "provider": kind,
        "kind": provider_kind,
        "attempt_cpus": 2,
        "attempt_timeout": "2h",
        "can": ["run"],
    }
    text = (there.layout.home / "settings.toml").read_text(encoding="utf-8")
    assert not any(value in text for value in keys.values())


def test_a_bad_key_stops_with_one_line_and_writes_no_row(tmp_path: Path) -> None:
    probe = provider_check({"X-API-Key": "the-right-one"})
    there = at(tmp_path, Server(), probe=probe)
    there.keys.replace("qmx/e2b", "a-wrong-one")

    with pytest.raises(Stopped) as stopped:
        once(there, "e2b", {})

    assert stopped.value.line == f"{PLACE}: E2B did not take the key; check it and write it again"
    assert PLACE not in stored(there).get("engine", {}).get("placement", {})


def test_the_provider_worker_builds_for_the_server_modal_and_e2b_and_a_plan_login_is_refused(
    tmp_path: Path,
) -> None:
    there = at(tmp_path, Server())
    through_the_cards(there)
    for kind, keys in (
        ("modal", ("qmx/modal-token-id", "qmx/modal-token-secret")),
        ("e2b", ("qmx/e2b",)),
    ):
        for name in keys:
            there.keys.replace(name, "planted")
        run_kind(
            KINDS[kind],
            f"my{kind}",
            {},
            report=quiet,
            world=dataclasses.replace(there, compute=ports_for(Server(), probe=answered)),
        )
    control = there.control
    assert control is not None
    settings = ControlSettings(control).values()
    worker = remote_worker(
        there.layout.home, cast("Any", SimpleNamespace(settings=settings)), cast("Any", None)
    )
    plan = Candidate("claude", "haiku", None, 200_000, False)
    kinds = {name: placement_kind(settings, name) for name in places(settings)}

    assert worker is not None and set(worker.providers) == {PLACE, "mymodal", "mye2b"}
    refused = plan_on_provider("n1", "triage", "mymodal", [plan], kinds)
    assert refused is not None and refused.code == "plan_on_provider"


def test_keeping_copies_somewhere_other_than_the_servers_own_root_is_refused(
    tmp_path: Path,
) -> None:
    def elsewhere(_row: Mapping[str, object], _key: Path) -> tuple[str, dict[str, str]]:
        return "rclone", {"type": "local", "root": "/mnt/elsewhere"}

    there = at(tmp_path, Server(), keep_as=elsewhere)
    through_the_cards(there)
    with pytest.raises(Stopped) as stopped:
        once(there, "server-keep", {})

    assert stopped.value.line == (
        f"{PLACE}: the server keeps copies under /srv/qmx/home, the folder its work runs in, and "
        "one row holds one folder; QMX does not keep them at /mnt/elsewhere instead"
    )
    assert stored(there)["engine"]["placement"][PLACE]["root"] == "/srv/qmx/home"


@needs_rclone
def test_keeping_copies_on_the_server_adds_keep_with_its_remote_type_and_root_to_its_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = tmp_path / "server-disk"
    store.mkdir()
    server = Server()
    monkeypatch.setattr(connect_compute, "NODE_ROOT", str(store))

    def local(_row: Mapping[str, object], _key: Path) -> tuple[str, dict[str, str]]:
        return "rclone", {"type": "local", "root": str(store)}

    there = at(tmp_path, server, keep_as=local)
    through_the_cards(there)
    synced: list[str] = []

    def first_sync(ident: str) -> str:
        synced.append(ident)
        return "started"

    keeping = dataclasses.replace(there, first_sync=first_sync)
    while (ended := once(keeping, "server-keep", {}))["needs"] is not None:
        needs = ended["needs"]
        assert needs["card"] == "question", needs
        once(keeping, "server-keep", {"state": needs["state"], "result": ""})
    row = stored(there)["engine"]["placement"][PLACE]
    again = once(keeping, "server-keep", {})

    assert row["can"] == ["run", "keep"]
    assert (row["via"], row["type"], row["root"]) == ("rclone", "local", str(store))
    assert str(row["remote"]).startswith("qmx_")
    assert row["provider"] == "ssh" and row["engine_url"] == f"http://{TAILNET}:8766"
    assert synced == [row["id"]]
    assert again["lines"] == [
        "storage: already done, skipped",
        "keep: already done, skipped",
        "first-sync: already done, skipped",
    ]
