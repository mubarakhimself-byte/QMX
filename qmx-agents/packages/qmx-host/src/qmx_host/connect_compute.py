"""The compute kinds of the connect dialog (design 06 section 9): his own server, a storage on it,
and Modal and E2B by key.

A server connects in two halves. First his five cards, all before anything runs: choose and pay
for it, its address, a one-off Tailscale key, the server password typed in a terminal window QMX
opens (QMX never sees it; the window copies a key QMX made in `keys/` onto the server), and his
approval of the firewall step. Then QMX's checked steps: the source sent over, the steps of `qmx
node setup` and its PC half (`qmx_control.node`, the one list both run), the place row, a one-node
smoke run on the server's own engine, the status ladder and the server's own recovery check. A
rerun skips every step whose check passes, so a kill at any step converges on one row (I12).

"Keep copies on your server" is its own kind, run once the server is up: it runs the `sftp`
storage kind's steps with the server's address and key, and adds `keep`, `via = "rclone"`, the
remote and its `type` to the server's row, so the sync always has a way to that storage.

A key kind (Modal, E2B) takes his key through the key route, makes one call to the provider with
it, and writes a row with the provider's `kind`, which keeps his plan login off that machine.
"""

from __future__ import annotations

import base64
import dataclasses
import os
import re
import socket
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Protocol, cast

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import JsonValue
from qmx_control import node
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.service.forward import Forwarder, ForwardRefused, Instance, post_json
from qmx_engine.triggers.preflight import PLACEMENT_STATES, placement_state
from qmx_home.files import plain

from qmx_host.connect import Card, Kind, Rows, Run, Step, placement, run_kind, write_row
from qmx_host.connect_storage import STORAGE, mint
from qmx_host.jobs import Stopped

USER: Final = "root"
NODE_ROOT: Final = "/srv/qmx/home"
"""The folder work runs under on a server, its `root` (Target); copies kept there go under it."""
ATTEMPT_CPUS: Final = 2
ATTEMPT_TIMEOUT: Final = "2h"
"""What an attempt reads a machine's row for (`NEEDS`); both are his to edit in Settings."""
SMOKE_FLOW: Final = (
    '{"schema": "qmx.workflow/1", "id": "qmx-smoke", "name": "QMX smoke test", "nodes": [{"id": '
    '"start", "name": "start", "type": "trigger", "typeVersion": 1, "parameters": {"kinds": '
    '["manual"]}}], "connections": {}}'
)
"""A one-node workflow every engine runs: its trigger alone."""
SMOKE_FOLDER: Final = "/var/lib/qmx/smoke"
SMOKE_RUN: Final = (
    "import json, sys, urllib.request\n"
    "port, token, flow = sys.argv[1:]\n"
    "with open(token, encoding='utf-8') as held:\n"
    "    bearer = held.read().strip()\n"
    "with open(flow, 'rb') as held:\n"
    "    definition = held.read()\n"
    "def call(method, path, body):\n"
    "    asked = urllib.request.Request(\n"
    "        f'http://127.0.0.1:{port}/api/workflows/qmx-smoke{path}', data=body, method=method,\n"
    "        headers={'Authorization': f'Bearer {bearer}', 'Content-Type': 'application/json'})\n"
    "    with urllib.request.urlopen(asked, timeout=120) as answer:\n"
    "        return json.load(answer)\n"
    "call('PUT', '/draft', definition)\n"
    "print(call('POST', '/test?fake=true', None)['run']['run_id'])\n"
)
"""What the server runs as `qmx` for the smoke: it saves the one-node workflow as a draft on the
server's running host and tests it there on fake models, through the host's loopback door with
the bearer the host keeps in `keys/`, so the host stays the engine's one writer. It prints the
run's id."""
STATUS_LINE: Final = re.compile(r"^(\S+)\s+(.*?)\s+(PASS|FAIL)$")


COPY_KEY: Final = (
    "import subprocess, sys\n"
    "with open(sys.argv[1], 'rb') as key:\n"
    "    code = subprocess.run(sys.argv[2:], stdin=key, check=False).returncode\n"
    "print('Done. Close this window and answer the card.' if code == 0 else\n"
    "      'That did not work. Close this window and answer the card to try again.')\n"
    "input()\n"
)
"""What his window runs: ssh with QMX's public key on its input, so the password he types there
goes to the server alone."""


class Terminal(Protocol):
    def open(self, command: Sequence[str], title: str) -> None:
        """Open a window on this PC that runs `command`, for him to type into."""
        ...


class Console:
    """A new console window on his desktop."""

    def open(self, command: Sequence[str], title: str) -> None:
        if os.name == "nt":
            subprocess.Popen(list(command), creationflags=subprocess.CREATE_NEW_CONSOLE)
            return
        subprocess.Popen(["x-terminal-emulator", "-T", title, "-e", *command])  # noqa: S607


def ssh_call(command: list[str], stdin: str | None) -> str:
    return node.run(command, input_text=stdin)


def source_revision() -> str:
    """The commit this QMX runs from, which the server is set up at."""
    try:
        found = node.run(["git", "-C", str(Path(node.__file__).parent), "rev-parse", "HEAD"])
    except OSError, RuntimeError:
        found = ""
    if not re.fullmatch(r"[0-9a-f]{40}", found):
        raise Stopped(
            "this QMX does not run from its source repository, so it cannot send itself to a "
            "server yet; set the server up from a QMX source checkout with: qmx node setup"
        )
    return found


def source_archive(revision: str) -> bytes:
    folder = Path(node.__file__).parent
    top = node.run(["git", "-C", str(folder), "rev-parse", "--show-toplevel"])
    return node.source_archive("git", top, revision)


type Probe = Callable[[str, Mapping[str, str]], int]
"""One GET with headers; answers the HTTP status, raises OSError when nothing answered."""


def http_probe(url: str, headers: Mapping[str, str]) -> int:
    try:
        return httpx.get(url, headers=dict(headers), timeout=20).status_code
    except httpx.HTTPError as error:
        raise OSError(str(error)) from None


def sftp_keep(row: Mapping[str, object], key_file: Path) -> tuple[str, dict[str, str]]:
    """The storage kind that keeps copies on the server, and its first card's answers."""
    user, _, host = str(row.get("host", "")).rpartition("@")
    return "sftp", {
        "host": host,
        "user": user or USER,
        "key_file": str(key_file),
        "root": str(row.get("root") or NODE_ROOT),
    }


@dataclass(frozen=True, slots=True)
class Ports:
    """What the compute kinds reach outside this process. Tests and lanes pass fakes."""

    shell: node.Call = ssh_call
    terminal: Terminal = field(default_factory=Console)
    sleep: Callable[[float], None] = time.sleep
    revision: Callable[[], str] = source_revision
    archive: Callable[[str], bytes] = source_archive
    probe: Probe = http_probe
    post: Callable[[str, Mapping[str, JsonValue], Mapping[str, str]], JsonValue] = post_json
    """How the smoke step reads the server's engine back."""
    keep_as: Callable[[Mapping[str, object], Path], tuple[str, dict[str, str]]] = sftp_keep
    urls: Mapping[str, str] = field(default_factory=dict[str, str])
    """A provider's check address, by kind id, in place of its own."""


def ports(run: Run) -> Ports:
    return run.world.compute or Ports()


def _rows(run: Run) -> Rows:
    control = run.world.control
    return {} if control is None else placement(control)


def _fields_card(name: str, line: str, *fields: tuple[str, str]) -> Card:
    return Card(
        name,
        line,
        tuple({"Name": n, "Help": h, "Examples": [], "Type": "string"} for n, h in fields),
    )


def _write(run: Run, row: Mapping[str, object], refusal: Callable[[Rows], str | None]) -> None:
    control = run.world.control
    if control is None:
        raise Stopped(f"{run.place}: a machine is connected from a running QMX, not the card")
    held = placement(control).get(run.place)
    if held is not None and held.get("id"):
        row = {**row, "id": held["id"]}
    wrote = write_row(control, run.place, row, refusal)
    run.say(f"{run.place}: added to your machines" if wrote else f"{run.place}: already there")


# His server.


CHOOSE: Final = (
    "choose a server and pay for it at a provider such as Hetzner or Contabo, with Ubuntu on it "
    "and any size you like; answer yes once it is running"
)
FIREWALL: Final = (
    "QMX will switch the server's firewall on, so only SSH and Tailscale get in. It keeps it on "
    "only after a fresh login works, and it switches itself off within five minutes if that "
    "login fails. Answer yes to approve"
)


def _tailscale_key(place: str) -> str:
    return f"qmx/connect/{place}/tailscale"


def server_row(run: Run) -> dict[str, object] | None:
    found = _rows(run).get(run.place)
    return found if found is not None and found.get("provider") == "ssh" else None


def _answered(name: str) -> Callable[[Run], bool]:
    def check(run: Run) -> bool:
        return run.fields().get(name, "").casefold() == "yes" or server_row(run) is not None

    return check


def _choose(run: Run) -> Card:
    return _fields_card("choose", f"{run.place}: {CHOOSE}", ("chosen", "yes, once it is running"))


def _addressed(run: Run) -> bool:
    return bool(run.fields().get("address")) or server_row(run) is not None


def _address_card(run: Run) -> Card:
    return _fields_card(
        "address",
        f"{run.place}: give the server's address from your provider's page",
        ("address", "Its IP address or name, such as 203.0.113.7"),
        ("user", "The user to sign in as; root unless your provider says otherwise"),
    )


def _keyed(run: Run) -> bool:
    return run.world.keys.read(_tailscale_key(run.place)) is not None or (
        server_row(run) is not None
    )


def _tailscale_card(run: Run) -> Card:
    name = _tailscale_key(run.place)
    return Card(
        "secret",
        f"{run.place}: make a one-off auth key in the Tailscale admin console (Settings, Keys, "
        f"Generate auth key) and write it to the key {name}; QMX hands it to the server in a "
        "file that is removed after, never in a command line",
        key=name,
    )


def _key_file(run: Run) -> Path:
    return run.world.layout.keys / f"{run.place}-ssh"


def _known_hosts(run: Run) -> Path:
    return run.world.layout.keys / f"{run.place}-known-hosts"


def _target(run: Run) -> str:
    held = server_row(run)
    fields = run.fields()
    if "address" in fields:
        return f"{fields.get('user') or USER}@{fields['address']}"
    host = str((held or {}).get("login") or "")
    if not host:
        raise Stopped(f"{run.place}: QMX has no address for this server; connect it again")
    return host


def _ssh(run: Run) -> tuple[str, ...]:
    return (
        "ssh",
        "-i",
        str(_key_file(run)),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"UserKnownHostsFile={_known_hosts(run)}",
        _target(run),
    )


def _key_made(run: Run) -> bool:
    return _key_file(run).is_file() and _key_file(run).with_suffix(".pub").is_file()


def _make_key(run: Run) -> Card | None:
    """A key pair for QMX's own logins to this server, with no passphrase (nothing to remember):
    the private half stays in `keys/`, owner-only, and never travels."""
    made = Ed25519PrivateKey.generate()
    private = made.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.OpenSSH,
        serialization.NoEncryption(),
    )
    public = made.public_key().public_bytes(
        serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH
    )
    path = _key_file(run)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(private)
    if not owner_only(path):
        path.unlink(missing_ok=True)
        raise Stopped(
            f"{run.place}: Windows would not make QMX's key in {plain(path.parent)} readable by "
            "you alone, so QMX removed it; check you own that folder, then answer again"
        )
    path.with_suffix(".pub").write_bytes(public + f" qmx {run.place}\n".encode())
    run.say(f"{run.place}: QMX made its own key for this server in {plain(path.parent)}")
    return None


def owner_only(path: Path) -> bool:
    """Only this user may read `path`, which ssh insists on for a key file. False when Windows
    did not take that, or no user is named to give it to."""
    if os.name != "nt":
        path.chmod(0o600)
        return True
    user = os.environ.get("USERNAME", "")
    if not user:
        return False
    done = subprocess.run(
        ["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:F"],  # noqa: S607
        capture_output=True,
        check=False,
    )
    return done.returncode == 0


def _logs_in(run: Run) -> bool:
    if server_row(run) is not None and _key_made(run):
        return True
    try:
        ports(run).shell([*_ssh(run), "true"], None)
    except RuntimeError:
        return False
    return True


AUTHORIZE: Final = (
    "umask 077; mkdir -p ~/.ssh && touch ~/.ssh/authorized_keys && key=$(cat) && "
    '{ grep -qxF "$key" ~/.ssh/authorized_keys || printf \'%s\\n\' "$key" >> '
    "~/.ssh/authorized_keys; }"
)
"""What the window's ssh runs on the server: QMX's key, read from its input, added once."""


def _password(run: Run) -> Card:
    again = cast("dict[str, object]", run.answer.get("fields") or {}).get("again") == "yes"
    if not run.memory.get("window") or again:
        public = _key_file(run).with_suffix(".pub")
        ssh = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            f"UserKnownHostsFile={_known_hosts(run)}",
            _target(run),
            AUTHORIZE,
        ]
        command = [sys.executable, "-I", "-c", COPY_KEY, str(public), *ssh]
        ports(run).terminal.open(command, f"QMX: sign in to {run.place}")
        run.memory["window"] = True
        return Card(
            "password",
            f"{run.place}: type the server's password in the window QMX opened. It goes straight "
            "to the server, and QMX never sees it; the window gives the server QMX's own key, so "
            "you type it this once. Then answer this card",
        )
    return _fields_card(
        "password",
        f"{run.place}: QMX still cannot sign in with its own key. If the window said it did not "
        "work, answer yes and QMX opens it once more",
        ("again", "yes, to open the window again"),
    )


def _firewall(run: Run) -> Card:
    return _fields_card("firewall", f"{run.place}: {FIREWALL}", ("approve", "yes"))


def server_of(run: Run) -> node.Server:
    """The server as `qmx node setup` reaches it, built once per run."""
    found = run.facts.get("server")
    if isinstance(found, node.Server):
        return found
    control = run.world.control
    keys = run.world.keys
    name = _tailscale_key(run.place)

    def hub(_home: Path, url: str) -> None:
        if control is not None:
            control.settings_update(
                cast("Any", "library"), lambda section: {**section, "hub_url": url}
            )

    built = node.Server(
        _ssh(run),
        run.world.layout.home,
        run.place,
        ports(run).revision(),
        ports(run).shell,
        say=lambda line: run.say(f"{run.place}: {line}"),
        sleep=ports(run).sleep,
        auth_key=lambda: keys.read(name),
        hub=hub,
    )
    run.facts["server"] = built
    return built


SHIPPED: Final = "send the source"


def _shipped(run: Run) -> bool:
    return node.done(server_of(run), SHIPPED)


def _ship(run: Run) -> Card | None:
    server = server_of(run)
    archive = base64.b64encode(ports(run).archive(server.revision)).decode("ascii")
    server.send(
        "sudo sh -c 'umask 077; install -d -m 700 /opt/qmx-deploy; "
        "base64 -d > /opt/qmx-deploy/source.tar'",
        archive,
    )
    node.mark(server, SHIPPED)
    run.say(f"{run.place}: QMX's source at {server.revision[:8]} is on the server")
    return None


def _setup(run: Run) -> list[node.NodeStep]:
    """`qmx node setup`'s two lists, at the server's own revision, built once per run."""
    found = run.facts.get("setup")
    if isinstance(found, list):
        return cast("list[node.NodeStep]", found)
    built = [
        *node.setup_steps(
            server_of(run).revision,
            machine=run.place,
            hindsight=node.hindsight_enabled(run.world.layout.home),
            pc_name=socket.gethostname().lower(),
        ),
        *node.pc_steps(),
    ]
    run.facts["setup"] = built
    return built


def _node_step(name: str) -> Step:
    def found(run: Run) -> node.NodeStep:
        return next(step for step in _setup(run) if step.name == name)

    def check(run: Run) -> bool:
        return found(run).check(server_of(run))

    def do(run: Run) -> Card | None:
        try:
            found(run).do(server_of(run))
        except node.SetupStopped as stopped:
            raise Stopped(f"{run.place}: {stopped.line}") from None
        except RuntimeError as failed:
            raise Stopped(f"{run.place}: {name} did not finish ({failed})") from None
        return None

    return Step(name, "qmx", check, do)


SETUP_NAMES: Final = tuple(
    step.name for step in [*node.setup_steps("0" * 40, machine="x"), *node.pc_steps()]
)
"""The names of `qmx node setup`'s steps, which depend on no server and no revision."""


def _engine_url(run: Run) -> str:
    return f"http://{node.address(server_of(run))}:{node.host_port(node.host_unit())}"


def _row(run: Run) -> dict[str, object]:
    server = server_of(run)
    url = _engine_url(run)
    held = server_row(run) or {}
    return {
        "id": str(held.get("id") or mint()),
        "provider": "ssh",
        "kind": "owned",
        "host": f"{_target(run).partition('@')[0]}@{node.address(server)}",
        "login": server.ssh[-1],
        "root": NODE_ROOT,
        "engine_url": url,
        "gateway_url": url,
        "attempt_cpus": ATTEMPT_CPUS,
        "attempt_timeout": ATTEMPT_TIMEOUT,
        "can": ["run"],
    }


def _row_written(run: Run) -> bool:
    held = server_row(run)
    return held is not None and held.get("engine_url") == _engine_url(run)


def _write_row(run: Run) -> Card | None:
    def refusal(rows: Rows) -> str | None:
        held = rows.get(run.place)
        if held is not None and held.get("provider") != "ssh":
            return (
                f"the name {run.place} is taken by another place in Settings; choose another "
                "name for this server"
            )
        return None

    _write(run, _row(run), refusal)
    return None


def _never(_run: Run) -> bool:
    return False


def _forwarder(run: Run) -> Forwarder:
    key = (run.world.layout.home / "vault" / node.PAIRING_KEY).read_text(encoding="utf-8")
    return Forwarder(
        Instance(run.place, _engine_url(run)),
        key=key.strip(),
        source="pc",
        principal="operator",
        post=ports(run).post,
    )


def smoke_script() -> str:
    folder = SMOKE_FOLDER
    return (
        "set -eu\n"
        f"install -d -o qmx -g qmx -m 750 {folder}\n"
        f"cat > {folder}/definition.json <<'QMXFLOW'\n{SMOKE_FLOW}\nQMXFLOW\n"
        f"cat > {folder}/smoke.py <<'QMXSMOKE'\n{SMOKE_RUN}QMXSMOKE\n"
        f"chown qmx:qmx {folder}/definition.json {folder}/smoke.py\n"
        f"runuser -u qmx -- {node.SERVER_VENV}/bin/python -I {folder}/smoke.py "
        f"{node.host_port(node.host_unit())} {node.SERVER_KEYS}/control-token "
        f"{folder}/definition.json\n"
    )


def _smoke(run: Run) -> Card | None:
    """Run a one-node workflow on the server's own engine, through its running host, then read
    the run back from it the way this PC's runs view does."""
    server = server_of(run)
    try:
        said = server.send("sudo bash -s", smoke_script()).split()
    except RuntimeError as failed:
        raise Stopped(
            f"{run.place}: the server's host did not run the smoke workflow ({failed}); check it "
            f"is running with: sudo {node.RECOVER} status"
        ) from None
    if not said:
        raise Stopped(f"{run.place}: the server's host started no smoke run; read its log there")
    run_id = said[-1]
    try:
        found = _forwarder(run).read("runs.get", {"run_id": run_id})
    except (ForwardRefused, OSError) as refused:
        raise Stopped(
            f"{run.place}: the smoke run {run_id} ran on the server, but this PC could not read "
            f"it back ({refused}); check the server's host is running"
        ) from None
    status = cast("dict[str, object]", found).get("status") if isinstance(found, dict) else None
    run.facts["reached"] = True
    if status != "passed":
        raise Stopped(f"{run.place}: the smoke run {run_id} ended {status}; read it on the server")
    run.facts["healthy"] = True
    run.say(f"{run.place}: a one-node workflow ran on the server's engine and passed ({run_id})")
    return None


def _ladder(run: Run) -> Card | None:
    control = run.world.control
    if control is None:
        return None
    reached = {run.place} if run.facts.get("reached") else set[str]()
    healthy = {run.place} if run.facts.get("healthy") else set[str]()
    state = placement_state(
        ControlSettings(control).values(), run.place, seen=reached, healthy=healthy
    )
    rungs = " → ".join(PLACEMENT_STATES)
    run.say(f"{run.place}: {rungs}: it is {state}")
    return None


def _recovery(run: Run) -> Card | None:
    """The server's own check, `qmx-recover status`, in plain words."""
    shown = server_of(run).send(f"sudo {node.RECOVER} status || true")
    for row in shown.splitlines():
        found = STATUS_LINE.match(row.strip())
        if found is None:
            continue
        part, text, verdict = found.groups()
        after = "" if verdict == "PASS" else " (this needs you)"
        run.say(f"{run.place}: {part}: {text}{after}")
    return None


def _server_refusal(run: Run) -> str | None:
    if not node.PLACE.fullmatch(run.place):
        return (
            f"{run.place!r} cannot name a server: a server's name is also its tailnet name, so "
            "use lowercase letters, digits and -"
        )
    return None


SERVER: Final = Kind(
    "server",
    "Your own server",
    ("run",),
    False,
    (
        Step("choose", "his", _answered("chosen"), _choose),
        Step("address", "his", _addressed, _address_card),
        Step("tailscale", "his", _keyed, _tailscale_card),
        Step("key", "qmx", _key_made, _make_key),
        Step("password", "his", _logs_in, _password),
        Step("firewall", "his", _answered("approve"), _firewall),
        Step(SHIPPED, "qmx", _shipped, _ship),
        *(_node_step(name) for name in SETUP_NAMES),
        Step("row", "qmx", _row_written, _write_row),
        Step("smoke", "qmx", _never, _smoke),
        Step("ladder", "qmx", _never, _ladder),
        Step("recovery", "qmx", _never, _recovery),
    ),
    refusal=_server_refusal,
)


# Keep copies on his server.


def _a_server(run: Run) -> dict[str, object]:
    held = server_row(run)
    if held is None:
        raise Stopped(
            f"{run.place}: connect {run.place} as your server first, then keep copies there"
        )
    return held


def _kept(run: Run) -> bool:
    held = _a_server(run)
    can = held.get("can")
    return isinstance(can, list) and "keep" in can and held.get("via") == "rclone"


def _kept_before(run: Run) -> bool:
    found = _kept(run)
    if found:
        run.facts["before"] = True
    return found


def _quiet(step: str, *, done: int = 0, total: int = 0, **counts: int) -> None:
    del step, done, total, counts


def _keep_storage(run: Run) -> Card | None:
    """The storage kind's own steps, up to its test, with no row of its own: the server's row is
    the one that gains `keep`."""
    held = _a_server(run)
    kind_id, fields = ports(run).keep_as(held, _key_file(run))
    storage = next(kind for kind in STORAGE if kind.id == kind_id)
    world = dataclasses.replace(run.world, control=None, first_sync=None)
    typed = run.answer.get("fields")
    given = {**fields, **(cast("dict[str, object]", typed) if isinstance(typed, dict) else {})}
    root = str(held.get("root") or NODE_ROOT)
    if str(given.get("root") or root) != root:
        raise Stopped(
            f"{run.place}: the server keeps copies under {root}, the folder its work runs in, "
            f"and one row holds one folder; QMX does not keep them at {given['root']} instead"
        )
    ended = run_kind(
        storage,
        run.place,
        {**run.answer, "fields": given},
        report=_quiet,
        world=world,
        card=True,
    )
    run.lines.extend(cast("list[str]", ended.get("lines") or []))
    needs = ended.get("needs")
    if isinstance(needs, dict):
        asked = cast("dict[str, Any]", needs)
        return Card(
            str(asked["card"]),
            str(asked["line"]),
            tuple(asked.get("fields") or ()),
            state=str(asked.get("state") or ""),
            key=str(asked.get("key") or ""),
            link=str(asked.get("link") or ""),
            job=str(asked.get("job") or ""),
        )
    source = cast("dict[str, object]", ended.get("source") or {})
    run.facts["kept"] = {"remote": source.get("remote"), "type": given.get("type") or storage.id}
    return None


def _add_keep(run: Run) -> Card | None:
    """The server's row gains `keep` and the remote that reaches it; its `root` stays the one its
    work runs in, which the storage kind's own root matched."""
    kept = cast("dict[str, object]", run.facts["kept"])
    held = _a_server(run)
    row = {**held, "can": ["run", "keep"], "via": "rclone", **kept}
    root = row.get("root")

    def refusal(rows: Rows) -> str | None:
        for name, other in rows.items():
            if name != run.place and all(
                other.get(k) == row.get(k) for k in ("via", "type", "root")
            ):
                return f"the storage {name} already keeps copies at {kept['type']}:{root}"
        return None

    _write(run, row, refusal)
    run.say(f"{run.place}: it keeps copies too now, at {root}")
    return None


def _synced(run: Run) -> bool:
    return bool(run.facts.get("before"))


def _first_sync(run: Run) -> Card | None:
    start = run.world.first_sync
    if start is not None:
        run.say(f"{run.place}: {start(str(_a_server(run)['id']))}")
    return None


KEEP: Final = Kind(
    "server-keep",
    "Keep copies on your server",
    ("keep",),
    True,
    (
        Step("storage", "qmx", _kept_before, _keep_storage),
        Step("keep", "qmx", _kept, _add_keep),
        Step("first-sync", "qmx", _synced, _first_sync),
    ),
)


# Modal and E2B, by key.


@dataclass(frozen=True, slots=True)
class Provider:
    """A compute provider reached by his key: its registry kind, the keys its worker reads, the
    address of one call that proves a key, and how the keys go in that call's headers."""

    id: str
    name: str
    kind: str
    keys: tuple[tuple[str, str], ...]
    """(key name, what his card says it is)."""
    check: str
    headers: Callable[[Sequence[str]], Mapping[str, str]]


PROVIDERS: Final[Mapping[str, Provider]] = {
    p.id: p
    for p in (
        Provider(
            "modal",
            "Modal",
            "serverless",
            (
                ("qmx/modal-token-id", "your Modal token id"),
                ("qmx/modal-token-secret", "your Modal token secret"),
            ),
            "https://api.modal.com/",
            lambda k: {"x-modal-token-id": k[0], "x-modal-token-secret": k[1]},
        ),
        Provider(
            "e2b",
            "E2B",
            "managed_agent_host",
            (("qmx/e2b", "your E2B API key"),),
            "https://api.e2b.app/sandboxes",
            lambda k: {"X-API-Key": k[0]},
        ),
    )
}
"""The provider worker reads these key names (`qmx_remote.providers`). The two check addresses
are each provider's API root; neither was tried with a real account."""


def _provider(run: Run) -> Provider:
    return PROVIDERS[run.kind.id]


def _key_step(name: str, what: str) -> Step:
    def held(run: Run) -> bool:
        return run.world.keys.read(name) is not None

    def card(run: Run) -> Card:
        return Card(
            "secret",
            f"{run.place}: write {what} to the key {name}; it stays in Credential Manager on this "
            "PC and reaches the provider only in QMX's own calls",
            key=name,
        )

    return Step(name.removeprefix("qmx/"), "his", held, card)


def _tested(run: Run) -> Card | None:
    provider = _provider(run)
    keys = [run.world.keys.read(name) or "" for name, _what in provider.keys]
    url = ports(run).urls.get(provider.id, provider.check)
    try:
        status = ports(run).probe(url, provider.headers(keys))
    except OSError:
        raise Stopped(
            f"{run.place}: {provider.name} was not reached; check this PC is online, then answer "
            "again"
        ) from None
    if status in (401, 403):
        raise Stopped(
            f"{run.place}: {provider.name} did not take the key; check it and write it again"
        )
    if not 200 <= status < 300:
        raise Stopped(f"{run.place}: {provider.name} answered {status}; try again later")
    run.say(f"{run.place}: {provider.name} took the key")
    return None


def _provider_row_written(run: Run) -> bool:
    held = _rows(run).get(run.place)
    return held is not None and held.get("provider") == _provider(run).id


def _provider_row(run: Run) -> Card | None:
    provider = _provider(run)
    held = _rows(run).get(run.place) or {}
    row = {
        "id": str(held.get("id") or mint()),
        "provider": provider.id,
        "kind": provider.kind,
        "attempt_cpus": ATTEMPT_CPUS,
        "attempt_timeout": ATTEMPT_TIMEOUT,
        "can": ["run"],
    }

    def refusal(rows: Rows) -> str | None:
        other = rows.get(run.place)
        if other is not None and other.get("provider") != provider.id:
            return f"the name {run.place} is taken by another place in Settings; choose another"
        return None

    _write(run, row, refusal)
    run.say(
        f"{run.place}: set the worker image it runs in Settings before its first run; your plan "
        "login never runs there"
    )
    return None


def _key_kind(provider: Provider) -> Kind:
    return Kind(
        provider.id,
        provider.name,
        ("run",),
        False,
        (
            *(_key_step(name, what) for name, what in provider.keys),
            Step("test", "qmx", _provider_row_written, _tested),
            Step("row", "qmx", _provider_row_written, _provider_row),
        ),
    )


COMPUTE: Final = (SERVER, KEEP, *(_key_kind(p) for p in PROVIDERS.values()))
"""The compute kinds, in the order the dialog offers them."""
