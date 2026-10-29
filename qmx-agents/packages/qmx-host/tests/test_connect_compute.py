"""The compute kinds (design 06 section 9): his server through five cards and `qmx node setup`'s
own checked steps against a fake shell, keeping copies there, and Modal and E2B by key."""

from __future__ import annotations

import dataclasses
import shutil
import socket
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from pydantic import JsonValue
from qmx_control import node
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.roles import Candidate
from qmx_engine.service.forward import owned_instances, placement_rows
from qmx_engine.settings import places
from qmx_engine.triggers.preflight import placement_kind, plan_on_provider
from test_connect import Store, qmx_folder, world

from qmx_host.connect import KINDS, Run, World, run_kind
from qmx_host.connect_compute import Ports
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
        self.kill = kill
        self.secrets: list[str] = []

    def __call__(self, command: list[str], stdin: str | None) -> str:
        line = command[-1]
        if "qmx-tailscale-key" in line and "cat >" in line:
            self.secrets.append(stdin or "")
            self.sent.append((list(command), None))
            return ""
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
            return ""
        if line.startswith("sudo cat "):
            return "pairing-code\n"
        if line.endswith("firewall status"):
            return "firewall    on: only SSH, Tailscale and QMX's containers get in  PASS"
        if line.endswith(f"{node.RECOVER} status || true"):
            return (
                "host        qmx-host is running  PASS\n"
                "firewall    on: only SSH, Tailscale and QMX's containers get in  PASS\n"
                "monitoring  openobserve is not installed on this server  FAIL"
            )
        return "PASS host"

    def scripts(self) -> list[str]:
        return [stdin or "" for command, stdin in self.sent if command[-1] == "sudo bash -s"]


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


def ports_for(server: Server, **changed: Any) -> Ports:
    return Ports(
        shell=server,
        terminal=Window(server),
        sleep=lambda _s: None,
        revision=lambda: REVISION,
        archive=lambda _r: b"the source",
        post=engine,
        **changed,
    )


def at(tmp_path: Path, server: Server, keys: Store | None = None, **changed: Any) -> World:
    found = world(qmx_folder(tmp_path / "QMX"), keys=keys or Store())
    return dataclasses.replace(found, compute=ports_for(server, **changed))


def once(there: World, kind: str, answer: Mapping[str, object]) -> Mapping[str, Any]:
    return run_kind(KINDS[kind], PLACE, answer, report=lambda *_a, **_k: None, world=there)


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
        elif "qmx_engine run" in script:
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


def test_the_tailscale_key_reaches_the_server_in_a_file_and_never_in_a_command_line(
    tmp_path: Path,
) -> None:
    server = Server()
    there = at(tmp_path, server)
    through_the_cards(there)

    joined = [s for s in server.scripts() if "tailscale up" in s]
    assert joined == [
        f"set -eu\ntrap 'rm -f {node.TAILSCALE_KEY}' EXIT\n"
        f"tailscale up --auth-key=file:{node.TAILSCALE_KEY}\n"
    ]
    assert server.secrets == [TAILSCALE]
    assert not [command for command, stdin in server.sent if TAILSCALE in " ".join(command)]
    assert not [stdin for _command, stdin in server.sent if stdin and TAILSCALE in stdin]


def test_the_password_window_runs_ssh_with_qmxs_public_key_and_no_secret(tmp_path: Path) -> None:
    server = Server()
    there = at(tmp_path, server)
    through_the_cards(there)
    window = cast("Window", cast("Ports", there.compute).terminal)

    [command] = window.opened
    public = there.layout.keys / f"{PLACE}-ssh.pub"
    assert command[4:6] == [str(public), "ssh"]
    assert command[-2:] == [LOGIN, "umask 077; mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"]
    assert public.read_text("utf-8").startswith("ssh-ed25519 ")
    assert TAILSCALE not in " ".join(command)


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
            report=lambda *_a, **_k: None,
            world=dataclasses.replace(there, compute=ports_for(Server(), probe=lambda _u, _h: 200)),
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


@needs_rclone
def test_keeping_copies_on_the_server_adds_keep_with_its_remote_type_and_root_to_its_row(
    tmp_path: Path,
) -> None:
    store = tmp_path / "server-disk"
    store.mkdir()
    server = Server()

    def local(_row: Mapping[str, object], _key: Path) -> tuple[str, dict[str, str]]:
        return "rclone", {"type": "local", "root": str(store)}

    there = at(tmp_path, server, keep_as=local)
    through_the_cards(there)
    synced: list[str] = []
    keeping = dataclasses.replace(there, first_sync=lambda ident: synced.append(ident) or "started")
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
