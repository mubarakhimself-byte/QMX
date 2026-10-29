"""Ubuntu node installation and a Tailscale-only, token-protected control service.

`qmx node setup` is the server step of the plan (LIB4, MIGRATION step 7; DATA-PLAN DR2B, DR2D;
engine AD-71): it runs the bootstrap, installs the recovery script `qmx-recover` and its settings,
closes the firewall and keeps it closed only once a fresh SSH login works, installs the host's
unit with the `server` role and the one store root `/srv/qmx/library`, stops and disables the
standalone Hub and node service, moves the pairing key and the control token into the host's home,
imports the bucket's run folders into that root as `qmx`, and only then starts `qmx-host`, the
store's one writer. On the PC it writes the pairing key, `[library] hub_url` and the recovery
script's PC twin in `<home>/bin`, never `primary`: the flip is his click (G-FLIP). `--dry-run`
prints the steps in order.

`qmx node verify` is the doctor: one `PASS`/`FAIL` line per fact, the firewall included, and the
primary store the setting names.

`qmx node rebuild` stops the services, puts a new server's Library back from the bucket and
rebuilds its catalog from what came back (MIGRATION "When the server is lost", step 3), and `qmx
node pair` writes a fresh pairing code on both ends (step 5), at `<home>/vault/pairing-key`, the
file the host and the Hub read; the server's half is `qmx-recover pair`, which takes the code on
stdin. Neither prints a key: a code is written to a file, never shown.

`qmx node vault install --ssh-host` builds the PC's vault document from Credential Manager, sealed
for the server's own public key, and installs it there; without `--ssh-host` it installs a
document it is given.

`qmx node update` drains the node before it installs anything (AD-65, Appendix F): it asks the
host to stop claiming fires, waits until no attempt is in flight, and only then runs the bootstrap
at the pinned revision and lets it restart the services. An update that cannot drain says so and
restarts nothing, so a node is never cut mid-node.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import time
import tomllib
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Final, NamedTuple, cast

import uvicorn
from qmx_home import NoQmxFolder, resolve

from qmx_control.server import create_app
from qmx_control.service import ControlService


class SessionLost(RuntimeError):
    """ssh's own exit code 255: the connection failed or dropped, whatever the command did."""


def run(command: list[str], *, input_text: str | None = None) -> str:
    # Windows text-mode pipes turn shell-script LF into CRLF, which bash rejects.
    result = subprocess.run(
        command,
        input=input_text.encode("utf-8") if input_text is not None else None,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        lost = result.returncode == 255 and Path(command[0]).stem == "ssh"
        failed = SessionLost if lost else RuntimeError
        raise failed(f"{command[0]} failed ({result.returncode}); inspect the node logs.")
    return result.stdout.decode("utf-8").strip()


def read_secret(vault: Path, service: str, username: str) -> str | None:
    if not re.fullmatch(r"qmx/[a-zA-Z0-9_-]+", service):
        raise ValueError("Node credentials must reference qmx/<name>.")
    path = vault / service.split("/", 1)[1]
    if not path.exists():
        return None
    if os.name == "posix" and path.stat().st_mode & 0o077:
        raise PermissionError("Node vault files must be owner-only (chmod 600).")
    return path.read_text(encoding="utf-8").strip()


PLAN_HOME: Final = "plan"
"""A node's own plan home, `<home>/plan`: Contabo's plan lane reads only this one (AD-38)."""
VAULT_STORE: Final = "vault-store.json"
"""The sealed entries the PC published, written here by `qmx node vault install`. The same file
name is the router's (`qmx_router.server`), which reads it when the `node` role starts; the two
packages do not depend on each other, so the name is written once on each side."""
PLAN_MARKER: Final = "home.toml"
SERVER_LIBRARY: Final = "/srv/qmx/library"
"""The server store's one root (Appendix D): `import`, `rebuild` and the host's unit all name it."""
SERVER_FOLDER: Final = "/srv/qmx/home/.qmx"
"""The server's QMX folder in the tree layout (design 62 A3, guard 4), as its unit's `--home`
names it."""
SERVER_HOME: Final = f"{SERVER_FOLDER}/data"
"""What the server's packages call its home; its `vault/pairing-key` is the pairing key."""
SERVER_KEYS: Final = f"{SERVER_FOLDER}/keys"
"""The folder the server's own commands read the host's control token from, beside its vault
key."""
NODE_STATE: Final = "/var/lib/qmx"
"""The bootstrap's folder: the bucket, `rclone.conf` and the old Hub's home."""
SERVER_VENV: Final = "/opt/qmx/qmx-agents/.venv"
"""The environment the bootstrap syncs, which the host's unit runs from."""
OLD_VAULT: Final = "/etc/qmx/vault"
"""Where the bootstrap and the old `pair` wrote the pairing key and the control token; setup and
`qmx-recover repair` move each into the host's home once."""
RECOVER: Final = "/usr/local/sbin/qmx-recover"
"""The recovery script, outside the version folders, because `/opt/qmx` can be the broken thing."""
RECOVER_CONF: Final = "/etc/qmx-recover.conf"
"""Its settings, root's alone: root acts on the paths it names, and the bootstrap gives everything
under `/etc/qmx` and `/var/lib/qmx` to `qmx`."""
UNIT_COPY: Final = "/usr/local/lib/qmx-recover/qmx-host.service"
"""Setup's copy of the host's unit, which `qmx-recover repair` puts back; root's for the same
reason."""
SERVER_UNITS: Final = ("qmx-host", "qmx-hub")
"""The services that hold the server store's writer lock."""
STANDALONE: Final = ("qmx-hub", "qmx-node")
"""The bootstrap's own services. The host replaces both: it is the Library service and the node
(engine AD-52), and `qmx-node` binds the host's port 8766 on the tailnet address."""


def plan_login(home: Path, vault: Path, machine: str) -> tuple[bool, str]:
    """`qmx node login`: give this node its own plan home.

    Nothing is copied and no token is read. The server has no browser, so a plan sign-in there is
    his act on the host itself; this command prepares the home and reports what it found. The
    vault is asked by name only (the file's presence), which is why no token can reach a log.
    """
    plan = home / PLAN_HOME
    plan.mkdir(parents=True, exist_ok=True, mode=0o700)
    (plan / PLAN_MARKER).write_text(
        f'machine = "{machine}"\nhome = "{plan.as_posix()}"\n', encoding="utf-8"
    )
    if not (vault / "plan-token").exists():
        return False, "not run, no server sign-in"
    return True, f"plan home {plan} installed"


def vault_install(home: Path, document: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """`qmx node vault install`: write the sealed entries the PC published.

    The document has a public key and one row per replicable entry; the values themselves are
    ciphertext this machine cannot open. Nothing here reads, writes or prints a key value. The
    rows are checked for shape only, because the router validates them again on the way in.
    """
    try:
        parsed: object = json.loads(document)
    except ValueError as error:
        raise RuntimeError(f"the vault document is not JSON: {error}") from error
    if not isinstance(parsed, dict):
        raise RuntimeError("the vault document needs a key and an entries list")
    data = cast("dict[str, Any]", parsed)
    rows = data.get("entries")
    if not isinstance(rows, list):
        raise RuntimeError("the vault document needs a key and an entries list")
    names: list[str] = []
    gone: list[str] = []
    for raw in cast("list[object]", rows):
        if not isinstance(raw, dict):
            continue
        row = cast("dict[str, Any]", raw)
        name = row.get("name")
        if not isinstance(name, str) or not name:
            continue
        (gone if row.get("deleted") else names).append(name)
    home.mkdir(parents=True, exist_ok=True)
    target = home / VAULT_STORE
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(parsed, sort_keys=True), encoding="utf-8")
    if os.name == "posix":
        temporary.chmod(0o600)
    temporary.replace(target)
    return tuple(sorted(names)), tuple(sorted(gone))


PLACE: Final = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
"""A server's place name, the placement its host runs under and its vault share is sealed for. No
place is assumed: setup names it."""
READ_APP: Final = "qmx/read/ctrader-app"
"""The cTrader read app WU8 files, which the server's sign-in opens from its vault copy. The PC's
document asks Credential Manager for it and for every bundled model-provider row; `--name` adds a
`qmx/read/*` or `qmx/data/*` one. Credential Manager cannot list names, so a name nobody asks for
is never sealed."""


def vault_key(home: Path, machine: str) -> str:
    """This machine's public vault key, after creating its key pair once (`<home>/.qmx/vault.key`,
    owner-only). The private half never leaves the file; the public half is not a secret."""
    from qmx_router.vault import (  # noqa: PLC0415 (the server's own key)
        VaultKey,
        as_text,
        key_file,
        read_machine_key,
        write_machine_key,
    )

    if not key_file(home).exists():
        write_machine_key(home, VaultKey.generate())
    return as_text(read_machine_key(home, machine).public_bytes())


def pc_vault_document(home: Path, server_key: str, *, machine: str, source: Any) -> str:
    """The PC's vault document: every replicable value `source` holds, sealed for this PC and for
    `machine`'s public key. Nothing is written to `source`, and no value is in the answer."""
    import base64  # noqa: PLC0415

    from qmx_router.vault import (  # noqa: PLC0415 (the PC's own seal)
        VaultKey,
        json_document,
        key_file,
        publish,
        read_machine_key,
        write_machine_key,
    )

    if not key_file(home).exists():
        write_machine_key(home, VaultKey.generate())
    own = read_machine_key(home, "pc")
    peer = VaultKey.from_public_bytes(base64.b64decode(server_key.strip()))
    return json_document(publish(source, own, machine="pc", peers={machine: peer}))


def bootstrap_script(revision: str, *, hindsight: bool = False, hub_port: int = 0) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Bootstrap needs an exact Git commit.")
    if hub_port != 0 and not 18100 <= hub_port <= 18199:
        raise ValueError("The Hub listens in 18100-18199, or on 0 for an ephemeral port.")
    return (
        Path(__file__)
        .with_name("node-bootstrap.sh")
        .read_text(encoding="utf-8")
        .replace("@REVISION@", revision)
        .replace("@HINDSIGHT@", "1" if hindsight else "0")
        .replace("@HUB_PORT@", str(hub_port))
    )


def settings(home: Path) -> dict[str, Any]:
    path = home / "settings.toml"
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        document: dict[str, Any] = tomllib.load(handle)
    return document


def library_primary(home: Path) -> str:
    """`[library] primary`, the one setting AD-19 turns on; absent means `pc`."""
    return str(cast(dict[str, Any], settings(home).get("library", {})).get("primary", "pc"))


def hub_url(home: Path) -> str | None:
    found = cast(dict[str, Any], settings(home).get("library", {})).get("hub_url")
    return None if found is None else str(found)


def hindsight_enabled(home: Path) -> bool:
    """`[memory] hindsight`: the setting PRB-S turned off (2,687 MB measured against 2,048 MB)."""
    return bool(cast(dict[str, Any], settings(home).get("memory", {})).get("hindsight", False))


def verify(
    home: Path,
    vault: Path,
    *,
    root: Path | None = None,
    state: Path = Path(NODE_STATE),
) -> dict[str, bool]:
    """The server's doctor: the host's unit, the one store root, no standalone Hub left, and the
    firewall on with incoming denied (engine AD-71)."""
    checks: dict[str, bool] = {}
    commands = {
        "docker": ["docker", "info"],
        "tailscale": ["tailscale", "ip", "-4"],
        "host": ["systemctl", "is-active", "qmx-host"],
        "shipping": ["systemctl", "is-active", "qmx-ship.timer"],
        "rclone": ["rclone", "version"],
    }
    for name, command in commands.items():
        try:
            checks[name] = bool(run(command))
        except OSError, RuntimeError:
            checks[name] = False
    checks["firewall"] = firewall_closed()
    checks["no_standalone_hub"] = all(
        _refused(["systemctl", verb, "qmx-hub"]) for verb in ("is-active", "is-enabled")
    )
    checks["node_token"] = bool(read_secret(vault, "qmx/control-token", "control-token"))
    checks["pairing_key"] = (home / "vault" / PAIRING_KEY).exists()
    checks["bucket"] = (state / "bucket").is_dir()
    checks["library_db"] = (root or Path(SERVER_LIBRARY)).is_dir()
    checks["shipping_config"] = (state / "rclone.conf").is_file()
    # CLIProxy requires live subscriptions and is provisioned separately by the operator.
    checks["cliproxy"] = (
        bool(run(["docker", "ps", "--filter", "name=qmx-cliproxy", "--format", "{{.Names}}"]))
        if checks["docker"]
        else False
    )
    return checks


def firewall_closed() -> bool:
    """ufw is on and denies incoming by default, as `qmx-recover firewall close` leaves it."""
    try:
        shown = run(["ufw", "status", "verbose"])
    except OSError, RuntimeError:
        return False
    return "Status: active" in shown and "deny (incoming)" in shown


def _refused(command: list[str]) -> bool:
    """True when the command ran and answered no; a machine without it proves nothing."""
    try:
        run(command)
    except RuntimeError:
        return True
    except OSError:
        return False
    return False


def flip_primary(home: Path, url: str, *, primary: str = "server") -> None:
    """Write `[library] primary` and `hub_url` into `home`'s settings, leaving every other line.

    The flip writes `server`; the reverse flip of MIGRATION step 8 writes `pc` with the same Hub,
    which is then a replica. Either value only caches the record on `refs/primary` (AD-14, AD-19).
    Only the flip's press calls this; setup writes `hub_url` alone (`set_hub_url`).
    """
    if primary not in ("pc", "server"):
        raise ValueError("The primary store is `pc` or `server`.")
    _write_library(home, {"primary": primary, "hub_url": url})


def set_hub_url(home: Path, url: str) -> None:
    """Write `[library] hub_url` and nothing else: `primary` stays his click's (G-FLIP)."""
    _write_library(home, {"hub_url": url})


def _write_library(home: Path, values: Mapping[str, str]) -> None:
    path = home / "settings.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    written = [f'{name} = "{value}"' for name, value in values.items()]
    replaced = re.compile(rf"^({'|'.join(map(re.escape, values))})\s*=")
    kept: list[str] = []
    inside = False
    for line in existing:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            inside = stripped == "[library]"
            if inside:
                kept.extend([line, *written])
                continue
        if inside and replaced.match(stripped):
            continue
        kept.append(line)
    if "[library]" not in "\n".join(kept):
        if kept and kept[-1] != "":
            kept.append("")
        kept.extend(["[library]", *written])
    path.write_text("\n".join(kept).rstrip("\n") + "\n", encoding="utf-8")


PAIRING_KEY: Final = "pairing-key"
"""The key both ends hold after a pairing: this machine's name on the Hub, not a right (AD-11)."""
PREVIOUS_PAIRING_KEY: Final = "pairing-key.previous"
RUN_PASS_KEY: Final = "run-pass-key"  # noqa: S105 - a file name, not a key
"""Both names are the router's too (`qmx_router.passes`), written once on each side."""
BUCKET_PREFIX: Final = "library"
"""The folder on the bucket, beside the push that writes it (`qmx_hub.bucket` writes the name once
on each side, because the two packages do not depend on each other)."""
BUCKET_FRAMES: Final = ("objects", "edges", "annotations", "blobs")
BUCKET_FILES: Final = ("refs/log.jsonl", "refs/epoch.json")


def pairing_code() -> str:
    """A fresh pairing code. It is written to a file and never printed (MIGRATION step 8.5)."""
    return secrets.token_urlsafe(32)


def pair(home: Path, code: str | None = None) -> Path:
    """Write a fresh pairing code into `home`'s vault, owner-only, and return its path.

    Re-pairing replaces the code both ends hold: the old one stops opening this machine's store,
    which is why the server-loss step 5 pairs again rather than reusing it. The run-pass secret
    rotates with it, so the outgoing key is kept as `pairing-key.previous`, which the pass
    authority accepts for one pass lifetime (engine AD-28). A first pairing leaves the unpaired
    home's `run-pass-key` in place for the same reason.
    """
    found = code or pairing_code()
    target = home / "vault" / PAIRING_KEY
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.replace(target.with_name(PREVIOUS_PAIRING_KEY))
        (target.parent / RUN_PASS_KEY).unlink(missing_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(found + "\n", encoding="utf-8")
    if os.name == "posix":
        temporary.chmod(0o600)
    temporary.replace(target)
    return target


def rebuild(
    *,
    remote: str | None = None,
    root: Path | None = None,
    prefix: str = BUCKET_PREFIX,
    runner: Callable[[Sequence[str]], str] | None = None,
    units: Sequence[str] = SERVER_UNITS,
) -> dict[str, object]:
    """Stop `units`, put the bucket's Library evidence back under `root` and rebuild the catalog.

    MIGRATION "When the server is lost" step 3: the old server pushed objects, refs, edges and
    durable blobs after each commit batch, so a new server restores those and rebuilds its index;
    the catalog is never copied, because it is derived (AD-16). The host and the Hub are stopped
    first, because whichever runs holds the store's writer lock. Without a bucket remote nothing
    is stopped or restored and the answer says so in the same words the push uses.
    """
    from qmx_hub.bucket import NO_BUCKET  # noqa: PLC0415 (the sentence has one owner)

    target = root or Path(SERVER_LIBRARY)
    if not remote:
        return {"restored": False, "said": NO_BUCKET}
    if units:
        (runner or _rclone)(("systemctl", "stop", *units))
    calls: list[tuple[str, ...]] = [
        (
            "rclone",
            "copy",
            f"{remote}:{prefix}/{name}",
            str(target / name),
            "--checksum",
            "--stats=0",
        )
        for name in BUCKET_FRAMES
    ] + [
        (
            "rclone",
            "copyto",
            f"{remote}:{prefix}/{name}",
            str(target / name),
            "--checksum",
            "--stats=0",
        )
        for name in BUCKET_FILES
    ]
    for call in calls:
        (runner or _rclone)(call)
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415

    with Store.open(target, redactor=redact, name="server") as store:
        counts: dict[str, object] = {
            "restored": True,
            "objects": len(store.object_ids()),
            "refs": len(store.refs()),
            "blobs": len(store.blob_ids()),
            "said": f"restored {len(store.object_ids())} objects and rebuilt the catalog",
        }
    return counts


def _rclone(call: Sequence[str]) -> str:
    done = subprocess.run(list(call), capture_output=True, check=False, text=True)
    if done.returncode:
        raise RuntimeError((done.stderr or done.stdout).strip() or "rclone failed")
    return done.stdout


DRAIN_ROUTE: Final = "/api/node/drain"
CONTROL_PORT: Final = 8766
"""The control service `qmx node serve` binds on the tailnet address."""
HOST_UNIT: Final = "qmx-host.service"


UNIT_PYTHON: Final = "/srv/qmx/home/.venv/bin/python"
"""The interpreter DR2A's unit names; the setup points it at the environment it syncs."""


def host_unit(role: str = "server", place: str = "") -> str:
    """The unit DR2A ships, with the role the server runs (AD-19, AD-26; DATA-PLAN DR2B) and,
    when given, the place name its host runs under (`--place`, engine AD-72).

    On the server the one host process opens the store as its writer and answers the Library
    routes, so its role is `server` and its store is the one root `/srv/qmx/library`. The file
    DR2A wrote names `--role node` and a virtual environment nothing installs, so this rewrites
    those two and leaves everything else as it stands, `OOMScoreAdjust` included (P-OOM reads it).
    A server host with no place name refuses to start, so the unit setup installs always names
    one; the unit read only for its port need not.
    """
    if place and not PLACE.fullmatch(place):
        raise ValueError("a place name is lowercase letters, digits and dashes")
    path = Path(__file__).parents[3] / "qmx-host" / "deploy" / HOST_UNIT
    if not path.is_file():
        raise RuntimeError(f"the host's unit is missing at {path}; install the source tree first")
    text = path.read_text(encoding="utf-8")
    if "--role node" not in text or UNIT_PYTHON not in text:
        raise RuntimeError(f"the host's unit at {path} no longer names --role node or its python")
    named = f" --place {place}" if place else ""
    return text.replace(
        "--role node", f"--role {role}{named} --library-root {SERVER_LIBRARY}"
    ).replace(UNIT_PYTHON, f"{SERVER_VENV}/bin/python")


def host_port(unit: str) -> int:
    """The port the host's unit serves on, which the PC's `hub_url` names."""
    found = re.search(r"--port (\d+)", unit)
    if found is None:
        raise RuntimeError("the host's unit names no --port")
    return int(found.group(1))


def host_unit_script(place: str, role: str = "server") -> str:
    """Install the host: the store root owned by `qmx`, its package in the environment, and its
    unit under the server's place name, not yet started (the import comes first). Its QMX folder
    is the layout step's. The recovery script's unit copy is this unit, so a repair keeps the
    name, and an update never rewrites the unit."""
    if not place:
        raise ValueError("the host's unit needs the server's place name")
    return (
        "set -eu\n"
        f"install -d -o qmx -g qmx -m 750 {SERVER_LIBRARY}\n"
        "uv sync --project /opt/qmx/qmx-agents --package qmx-host --frozen --no-default-groups\n"
        f"cat > /etc/systemd/system/{HOST_UNIT} <<'QMXUNIT'\n"
        f"{host_unit(role, place)}"
        "QMXUNIT\n"
        f"install -D -o root -g root -m 644 /etc/systemd/system/{HOST_UNIT} {UNIT_COPY}\n"
        "systemctl daemon-reload\n"
    )


def layout_script(folder: str = SERVER_FOLDER, venv: str = SERVER_VENV) -> str:
    """Lay out the server's QMX folder as the tree (design 62 A3, guard 4), with the host
    stopped, and start the host again when it was running, or was failing or restarting: a new
    host refuses a flat folder, so after an update it is down until the folder is laid out. One
    stopped on purpose stays stopped. qmx-home's layout step labels a fresh folder and makes its
    five parts, moves a flat home from an earlier setup into the tree, and leaves a tree as it
    is; the key folders are then made owner-only, whichever it was."""
    unit = HOST_UNIT.removesuffix(".service")
    return (
        "set -eu\n"
        f"was=$(systemctl is-active {unit} || true)\n"
        f"systemctl stop {unit} || true\n"
        f"install -d -o qmx -g qmx -m 750 {PurePosixPath(folder).parent} {folder}\n"
        f"runuser -u qmx -- {venv}/bin/python -m qmx_home layout {folder}\n"
        f"install -d -o qmx -g qmx -m 700 {folder}/keys {folder}/data/vault\n"
        f'case "$was" in active | activating | failed) systemctl start {unit} ;; esac\n'
    )


def move_key_script(
    server_home: str = SERVER_HOME, keys: str = SERVER_KEYS, old_vault: str = OLD_VAULT
) -> str:
    """Move the pairing key and the control token from `old_vault` into the host's QMX folder,
    once: the key to `<home>/vault`, the token to `keys/`.

    The bootstrap writes a fresh key whenever none is at the old path, and the old `qmx node
    bootstrap` a token, so on a rerun the folder already holds both: the copy at the old path is
    then removed unread and the one the running host uses is kept.
    """
    lines = ["set -eu"]
    for name, folder in ((PAIRING_KEY, f"{server_home}/vault"), ("control-token", keys)):
        lines += [
            f"if [ -s {folder}/{name} ]; then rm -f {old_vault}/{name}",
            f"elif [ -s {old_vault}/{name} ]; then mv {old_vault}/{name} {folder}/{name}",
            "fi",
            f"if [ -e {folder}/{name} ]; then chown qmx:qmx {folder}/{name}; "
            f"chmod 600 {folder}/{name}; fi",
        ]
    return "\n".join(lines) + "\n"


def recover_script(pc_name: str = "") -> str:
    """Install `qmx-recover` from the source tree the bootstrap just unpacked, with its settings."""
    source = "/opt/qmx/qmx-agents/packages/qmx-control/src/qmx_control/qmx-recover.sh"
    conf = {
        "HOST_UNIT": HOST_UNIT.removesuffix(".service"),
        "QMX_FOLDER": SERVER_FOLDER,
        "QMX_HOME": SERVER_HOME,
        "QMX_KEYS": SERVER_KEYS,
        "LIBRARY": SERVER_LIBRARY,
        "PORT": str(host_port(host_unit())),
        "PROJECT": "/opt/qmx/qmx-agents",
        "VENV": SERVER_VENV,
        "VERSIONS": "/opt/qmx-versions",
        "CURRENT": "/opt/qmx",
        "QMX_USER": "qmx",
        "OLD_VAULT": OLD_VAULT,
        "UNIT_COPY": UNIT_COPY,
        "PC_NAME": pc_name,
    }
    rows = "".join(f"{key}={value}\n" for key, value in conf.items())
    return (
        "set -eu\n"
        f"install -o root -g root -m 755 {source} {RECOVER}\n"
        f"cat > {RECOVER_CONF} <<'QMXCONF'\n{rows}QMXCONF\n"
        f"chown root:root {RECOVER_CONF}\n"
        f"chmod 644 {RECOVER_CONF}\n"
    )


FIREWALL_STEP: Final = "close the firewall"


type Call = Callable[[list[str], str | None], str]
"""One command on this PC or over ssh, with its stdin; returns stdout and raises on failure."""

SETUP_MARKS: Final = f"{NODE_STATE}/setup"
"""One empty file per server step that finished, in a folder named for the revision it ran at,
so setup run again at that revision skips it, and an update to another revision runs it again."""
TAILSCALE_KEY: Final = "/run/qmx-tailscale-key"
"""Where the one-off Tailscale key waits for `tailscale up`, root's alone, removed after."""


class SetupStopped(Exception):
    """A step that stops setup on purpose: `line` says why and what to do next."""

    def __init__(self, line: str) -> None:
        super().__init__(line)
        self.line = line


@dataclass(slots=True)
class Server:
    """One server as setup reaches it: the ssh command that logs in, this PC's home, the place
    name and revision, the one way commands are sent, and what setup has read from it so far."""

    ssh: tuple[str, ...]
    home: Path
    machine: str
    revision: str
    call: Call
    say: Callable[[str], None] = print
    sleep: Callable[[float], None] = time.sleep
    auth_key: Callable[[], str | None] = lambda: None
    """The one-off Tailscale key, for a server that is not on the tailnet yet."""
    hub: Callable[[Path, str], None] = set_hub_url
    """How `[library] hub_url` is written: the file itself, or a running host's settings."""
    read: dict[str, str] = field(default_factory=dict[str, str])
    marks: set[str] | None = None

    def send(self, command: str, stdin: str | None = None) -> str:
        return self.call([*self.ssh, command], stdin)

    def login(self, command: str) -> str:
        """`command` through a fresh SSH login, as the firewall check needs one."""
        return self.call([self.ssh[0], "-o", "ConnectTimeout=10", *self.ssh[1:], command], None)


class NodeStep(NamedTuple):
    name: str
    script: str
    """The script the step sends for `sudo bash`, or "" for a step on this PC."""
    check: Callable[[Server], bool]
    """True when the step's work is already in place, so the step is skipped."""
    do: Callable[[Server], None]
    """Raises SetupStopped with one line for a refusal."""


def _slug(name: str) -> str:
    return name.replace(" ", "-")


def _marked(server: Server) -> set[str]:
    if server.marks is None:
        listed = server.send(f"sudo ls {SETUP_MARKS}/{server.revision} 2>/dev/null || true")
        server.marks = {line.strip() for line in listed.splitlines() if line.strip()}
    return server.marks


def done(server: Server, name: str) -> bool:
    """True when the server step `name` finished at this revision."""
    return _slug(name) in _marked(server)


def mark(server: Server, name: str) -> None:
    folder = f"{SETUP_MARKS}/{server.revision}"
    server.send(f"sudo sh -c 'install -d -m 700 {folder} && touch {folder}/{_slug(name)}'")
    _marked(server).add(_slug(name))


def _scripted(name: str, script: str, live: Callable[[Server], bool] | None = None) -> NodeStep:
    """A step that sends `script`. A mark says it ran at this revision; `live`, when given, says
    its work is still in place, so a rerun does it again when it was undone since."""

    def finished(server: Server) -> bool:
        return done(server, name) and (live is None or live(server))

    def do(server: Server) -> None:
        try:
            server.send("sudo bash -s", script)
        except SessionLost:
            # Switching ufw on can reset the session that asked; the fresh login below decides.
            if name != FIREWALL_STEP:
                raise
        if name == FIREWALL_STEP:
            refused = kept_closed(server)
            if refused is not None:
                raise SetupStopped(refused)
        mark(server, name)

    return NodeStep(name, script, finished, do)


def _on_tailnet(server: Server) -> bool:
    try:
        found = server.send("tailscale ip -4").split()
    except RuntimeError:
        return False
    if found:
        server.read["address"] = found[0]
    return bool(found)


def join_script(key: str) -> str:
    """One root shell that sets the trap first, then reads the key from the line after its
    `read` (bash reads a piped script a byte at a time, so `read` takes that line and bash never
    runs it), writes it to a root-only file and joins. The key is in no command line, and the
    trap removes the file however the shell ends."""
    return (
        "set -eu\n"
        "umask 077\n"
        f"trap 'rm -f {TAILSCALE_KEY}' EXIT\n"
        "IFS= read -r key\n"
        f"{key}\n"
        '[ -n "$key" ]\n'
        f"printf '%s\\n' \"$key\" > {TAILSCALE_KEY}\n"
        "unset key\n"
        f"tailscale up --auth-key=file:{TAILSCALE_KEY}\n"
    )


def _join_tailnet(server: Server) -> None:
    key = (server.auth_key() or "").strip()
    if not key:
        raise SetupStopped(
            "the server is not on your tailnet yet; make a one-off auth key in the Tailscale admin "
            "console, then run setup again with it"
        )
    if len(key.split()) != 1:
        raise SetupStopped("that Tailscale key has spaces in it; copy the key again and rerun")
    server.send("sudo bash -s", join_script(key))
    if not _on_tailnet(server):
        raise SetupStopped(
            "the server ran tailscale up but has no tailnet address; check the key is unused and "
            "not expired, then run setup again"
        )


def setup_steps(
    revision: str,
    *,
    machine: str,
    hindsight: bool = False,
    hub_port: int = 0,
    pc_name: str = "",
) -> list[NodeStep]:
    """The server's half of `qmx node setup`, in order, each with its check. `machine` is the
    server's place name, which its host's unit runs under.

    The server joins the tailnet right after the bootstrap installs Tailscale, reading its key
    from a file, never an argument. The recovery script comes next, because it owns the
    firewall's rules and is his way in if a later step fails. The standalone Hub stops before the
    import because it would hold the old store's lock and serve a second root; the QMX folder is
    laid out once the host has stopped, so a flat home from an earlier setup moves while nothing
    holds it open; the host starts last, so it opens the store the import wrote.
    """
    return [
        _scripted("bootstrap", bootstrap_script(revision, hindsight=hindsight, hub_port=hub_port)),
        NodeStep("join the tailnet", "", _on_tailnet, _join_tailnet),
        _scripted("install the recovery script", recover_script(pc_name)),
        _scripted(FIREWALL_STEP, f"set -eu\n{RECOVER} firewall close\n", _firewall_on),
        _scripted("install the host", host_unit_script(machine)),
        _scripted(
            "stop and disable the standalone Hub",
            "set -eu\nsystemctl stop qmx-host || true\n"
            f"systemctl disable --now {' '.join(STANDALONE)}\n",
        ),
        _scripted("lay out the QMX folder", layout_script()),
        _scripted("move the pairing key and the control token", move_key_script()),
        _scripted(
            "import as qmx",
            f"set -eu\nrunuser -u qmx -- {SERVER_VENV}/bin/qmx node import "
            f"--home {NODE_STATE} --root {SERVER_LIBRARY}\n",
        ),
        _scripted("start the host", "set -eu\nsystemctl enable --now qmx-host\n", _host_running),
    ]


def _says_on(shown: str) -> bool:
    """The server's `firewall status` row reads on."""
    return any(row.startswith("firewall ") and row.endswith("PASS") for row in shown.splitlines())


def _firewall_on(server: Server) -> bool:
    try:
        return _says_on(server.send(f"sudo {RECOVER} firewall status"))
    except RuntimeError:
        return False


def _host_running(server: Server) -> bool:
    try:
        shown = server.send(f"systemctl is-active {HOST_UNIT.removesuffix('.service')}")
    except RuntimeError:
        return False
    return shown.split() == ["active"]


def address(server: Server) -> str:
    """The server's tailnet address, which every later call and this PC's settings name."""
    if "address" not in server.read and not _on_tailnet(server):
        raise SetupStopped("the server has no tailnet address; run: sudo tailscale up there")
    return server.read["address"]


def _hub(server: Server) -> str:
    return f"http://{address(server)}:{host_port(host_unit())}"


def _server_key(server: Server) -> str:
    if "key" not in server.read:
        server.read["key"] = server.send(f"sudo cat {SERVER_HOME}/vault/{PAIRING_KEY}").strip()
    return server.read["key"]


def _key_held(server: Server) -> bool:
    held = server.home / "vault" / PAIRING_KEY
    return held.exists() and held.read_text(encoding="utf-8").strip() == _server_key(server)


def _hub_written(server: Server) -> bool:
    return hub_url(server.home) == _hub(server)


def _write_hub(server: Server) -> None:
    server.hub(server.home, _hub(server))
    server.say(f"hub: {_hub(server)}")
    server.say(f"primary: {library_primary(server.home)} (the flip is his click)")


def _twin_rows(server: Server) -> list[str]:
    return [f"TARGET={server.ssh[-1]}", f"SERVER_TAILNET={address(server)}"]


def _twin_written(server: Server) -> bool:
    conf = server.home / TWIN_FOLDER / "qmx-recover.conf"
    if not conf.is_file():
        return False
    return conf.read_text(encoding="utf-8").splitlines()[:2] == _twin_rows(server)


def _write_twin(server: Server) -> None:
    twin = write_twin(server.home, server.ssh[-1], address(server))
    server.say(f"recovery on this PC: {twin}")


def _never(_server: Server) -> bool:
    return False


def _doctor(server: Server) -> None:
    checks = server.send(f"sudo {SERVER_VENV}/bin/qmx node verify --home {SERVER_HOME} || true")
    server.say(checks)
    if "FAIL" in checks:
        raise SetupStopped("the server's own doctor named a problem above; fix it, then run again")


def _pair(server: Server) -> None:
    pair(server.home, _server_key(server))


def pc_steps() -> list[NodeStep]:
    """The PC's half of setup: the pairing key (written, never printed, so it cannot land in a
    log; MIGRATION step 7, AD-11), `[library] hub_url` and never `primary`, the recovery twin,
    then the server's own doctor."""
    return [
        NodeStep("copy the pairing key", "", _key_held, _pair),
        NodeStep("write the hub address", "", _hub_written, _write_hub),
        NodeStep("write the recovery twin", "", _twin_written, _write_twin),
        NodeStep("read the server's doctor", "", _never, _doctor),
    ]


def run_steps(server: Server, steps: Sequence[NodeStep]) -> str | None:
    """Run `steps` in order on `server`, skipping each whose check passes. None when all are
    done, or the line that stopped them."""
    for number, step in enumerate(steps, start=1):
        if step.check(server):
            server.say(f"step {number}: {step.name}: already done")
            continue
        server.say(f"step {number}: {step.name}")
        try:
            step.do(server)
        except SetupStopped as stopped:
            return stopped.line
    return None


def setup(
    host: str,
    home: Path,
    *,
    machine: str,
    revision: str,
    call: Call,
    hindsight: bool = False,
    hub_port: int = 0,
    say: Callable[[str], None] = print,
    dry_run: bool = False,
    sleep: Callable[[float], None] = time.sleep,
    auth_key: Callable[[], str | None] = lambda: None,
) -> int:
    """`qmx node setup` after the source archive is on `host`: the server steps, then the PC's
    pairing key and `hub_url`, then the server's own doctor. `primary` is not written. `machine`
    is the server's place name (`PLACE`), the one its host runs under and its vault is sealed for.
    The connect dialog's server kind runs the same two lists.

    `dry_run` prints every step's script and the PC's three writes, and runs and writes nothing.
    A fresh SSH login that fails once the firewall closes stops setup there, before the host.
    """
    steps = setup_steps(
        revision,
        machine=machine,
        hindsight=hindsight,
        hub_port=hub_port,
        pc_name=socket.gethostname().lower(),
    )
    if dry_run:
        for number, step in enumerate(steps, start=1):
            say(f"step {number}: {step.name}")
            say(
                f"node-bootstrap.sh at {revision}"
                if step.name == "bootstrap"
                else step.script.rstrip() or f"tailscale up --auth-key=file:{TAILSCALE_KEY}"
            )
        port = host_port(host_unit())
        say(f"then on this PC: copy {SERVER_HOME}/vault/{PAIRING_KEY} to {home}/vault")
        say(f'then on this PC: [library] hub_url = "http://<tailnet address>:{port}"')
        say(f"then on this PC: write the recovery twin to {home / TWIN_FOLDER}")
        return 0
    server = Server(
        ("ssh", host), home, machine, revision, call, say=say, sleep=sleep, auth_key=auth_key
    )
    stopped = run_steps(server, [*steps, *pc_steps()])
    if stopped is not None:
        say(stopped)
        return 1
    return 0


CLOSE_WAIT_S: Final = 5.0
CLOSE_TRIES: Final = 18
"""`firewall close` switches ufw on about three seconds after it returns; this many fresh logins,
each after the wait, give it a minute and a half to say on."""


def kept_closed(server: Server) -> str | None:
    """After the firewall closes, keep it closed only when a fresh SSH login works and the
    server's own `firewall status` says on (AD-71). None when kept, or the line that stops setup.

    The close armed a timer that turns ufw off in five minutes, so a failed login undoes itself.
    """
    shown = ""
    for _ in range(CLOSE_TRIES):
        server.sleep(CLOSE_WAIT_S)
        try:
            shown = server.login(f"sudo {RECOVER} firewall status")
        except RuntimeError:
            return (
                "A fresh SSH login to the server failed after the firewall closed. The undo "
                "switches the firewall off within five minutes; then run setup again. If SSH "
                "stays shut, Contabo's VNC console is the way back: log in there and run: "
                "sudo qmx-recover firewall open"
            )
        if _says_on(shown):
            server.send(f"sudo {RECOVER} firewall keep")
            return None
    return (
        "The firewall did not say on within a minute and a half, so setup stops here. If it "
        "came on later, the undo switches it off within five minutes. The server said:\n"
        f"{shown}\n"
        "Run setup again once that is fixed."
    )


TWIN_FOLDER: Final = "bin"
TWIN: Final = "qmx-recover.ps1"


def write_twin(home: Path, host: str, address: str) -> Path:
    """The PC twin of `qmx-recover` in `<home>/bin`, with the server's SSH target and tailnet
    address, this PC's QMX folder and home `data/`, and its Python beside it. No secret is
    written."""
    folder = home / TWIN_FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / TWIN
    shutil.copyfile(Path(__file__).with_name(TWIN), target)
    rows = {
        "TARGET": host,
        "SERVER_TAILNET": address,
        "SERVER_HOME": SERVER_HOME,
        "QMX_FOLDER": str(home.resolve().parent),
        "QMX_HOME": str(home.resolve()),
        "PYTHON": sys.executable,
    }
    (folder / "qmx-recover.conf").write_text(
        "".join(f"{key}={value}\n" for key, value in rows.items()), encoding="utf-8"
    )
    return target


def post(url: str, body: Mapping[str, object], headers: Mapping[str, str]) -> Mapping[str, object]:
    request = urllib.request.Request(  # noqa: S310 (the node's own tailnet address)
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as answer:  # noqa: S310
        return cast("Mapping[str, object]", json.loads(answer.read()))


def drain(
    url: str,
    token: str,
    *,
    timeout_s: float,
    wait_s: float = 2.0,
    poster: Callable[[str, Mapping[str, object], Mapping[str, str]], Mapping[str, object]] = post,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, object]:
    """Ask the host to stop claiming fires and wait until no attempt is in flight.

    Returns the host's last answer with `drained` true only when it said so. A timeout returns
    `drained: False`, and the caller then restarts nothing.
    """
    deadline = clock() + timeout_s
    while True:
        answer = dict(poster(f"{url}{DRAIN_ROUTE}", {}, {"Authorization": f"Bearer {token}"}))
        if answer.get("drained"):
            return answer
        if clock() >= deadline:
            return answer | {"drained": False, "timed_out": True}
        sleep(wait_s)


def update(
    home: Path,
    vault: Path,
    *,
    revision: str,
    timeout_s: float = 3600.0,
    wait_s: float = 2.0,
    poster: Callable[[str, Mapping[str, object], Mapping[str, str]], Mapping[str, object]] = post,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    installer: Callable[[str], None] | None = None,
    address_of: Callable[[], str] | None = None,
) -> dict[str, object]:
    """`qmx node update`: drain, then install the pinned revision, let the bootstrap restart, and
    lay out the QMX folder with the new program (guard 4).

    `installer` and `address_of` are the install step and the node's own address, so a test never
    runs sudo or asks Tailscale; the real ones are the bootstrap and layout scripts and
    `tailscale ip -4`.
    """

    def bootstrap_install(pinned: str) -> None:
        run(["sudo", "bash", "-s"], input_text=bootstrap_script(pinned))
        run(["sudo", "bash", "-s"], input_text=layout_script())

    token = read_secret(vault, "qmx/control-token", "control-token")
    if not token:
        return {"drained": False, "restarted": False, "error": "no control token"}
    address = (address_of or (lambda: run(["tailscale", "ip", "-4"]).splitlines()[0]))()
    answered = drain(
        f"http://{address}:{CONTROL_PORT}",
        token,
        timeout_s=timeout_s,
        wait_s=wait_s,
        poster=poster,
        sleep=sleep,
        clock=clock,
    )
    if not answered.get("drained"):
        return answered | {"restarted": False}
    (installer or bootstrap_install)(revision)
    return answered | {"restarted": True, "revision": revision}


def source_archive(git: str, repository: str, revision: str) -> bytes:
    """The tar of `revision` as the index holds it. `git archive` applies `core.autocrlf`, which
    on a Windows checkout turns every shell script's LF into CRLF that bash on the server rejects;
    the repository's `.gitattributes` pins them to LF, and this switch covers an older revision."""
    return subprocess.run(
        [git, "-c", "core.autocrlf=false", "-C", repository, "archive", "--format=tar", revision],
        capture_output=True,
        check=True,
    ).stdout


def transfer(host: str, revision: str) -> str:
    """Ship the pinned source archive to the host and run the bootstrap script there."""
    ssh = shutil.which("ssh")
    git = shutil.which("git")
    if ssh is None or git is None:
        raise RuntimeError("Install Git and SSH before setting up a node.")
    archive = source_archive(git, run(["git", "rev-parse", "--show-toplevel"]), revision)
    sent = subprocess.run(
        [
            ssh,
            host,
            "sudo sh -c 'umask 077; install -d -m 700 /opt/qmx-deploy; "
            "cat > /opt/qmx-deploy/source.tar'",
        ],
        input=archive,
        capture_output=True,
        check=False,
    )
    if sent.returncode:
        raise RuntimeError("SSH could not transfer the pinned QMX source archive.")
    return ssh


def pc_home(parser: argparse.ArgumentParser, flag: Path | None) -> Path:
    """This PC's QMX folder for `setup`, `pair` and `vault install`, or one plain line and exit."""
    try:
        return resolve(flag).home
    except NoQmxFolder as missing:
        parser.exit(2, f"{missing}\n")


def main() -> int:
    parser = argparse.ArgumentParser(prog="qmx")
    node = parser.add_subparsers(dest="group", required=True).add_parser("node")
    commands = node.add_subparsers(dest="command", required=True)
    bootstrap = commands.add_parser("bootstrap")
    bootstrap.add_argument("ssh_host")
    setting_up = commands.add_parser("setup")
    setting_up.add_argument("ssh_host")
    setting_up.add_argument("--home", type=Path, default=None)
    setting_up.add_argument("--hub-port", type=int, default=0)
    setting_up.add_argument("--hindsight", action="store_true")
    setting_up.add_argument("--dry-run", action="store_true", help="print the steps, run nothing")
    setting_up.add_argument("--machine", default="", help="the server's place name")
    setting_up.add_argument(
        "--auth-key-file",
        type=Path,
        default=None,
        help="a file holding a one-off Tailscale auth key, for a server not on the tailnet yet",
    )
    importer = commands.add_parser("import")
    importer.add_argument("--home", type=Path, default=Path(NODE_STATE))
    importer.add_argument("--bucket", type=Path, default=None)
    importer.add_argument("--root", type=Path, default=Path(SERVER_LIBRARY))
    rebuilding = commands.add_parser("rebuild")
    rebuilding.add_argument("--root", type=Path, default=None)
    rebuilding.add_argument("--remote", default=None, help="the rclone remote holding the bucket")
    rebuilding.add_argument(
        "--units",
        default=",".join(SERVER_UNITS),
        help="the services stopped first, comma-separated; empty stops none",
    )
    pairing = commands.add_parser("pair")
    pairing.add_argument("--home", type=Path, default=None)
    pairing.add_argument("--ssh-host", default="", help="also install the same code on that host")
    check = commands.add_parser("verify")
    check.add_argument("--home", type=Path, default=Path(SERVER_HOME))
    check.add_argument("--vault", type=Path, default=Path(SERVER_KEYS))
    check.add_argument("--root", type=Path, default=Path(SERVER_LIBRARY))
    login = commands.add_parser("login")
    login.add_argument("--home", type=Path, default=Path(SERVER_HOME))
    login.add_argument("--vault", type=Path, default=Path(SERVER_KEYS))
    login.add_argument("--machine", default="")
    refresh = commands.add_parser("update")
    refresh.add_argument("--home", type=Path, default=Path(SERVER_HOME))
    refresh.add_argument("--vault", type=Path, default=Path(SERVER_KEYS))
    refresh.add_argument("--revision", default="")
    refresh.add_argument("--timeout", type=float, default=3600.0)
    vault_command = commands.add_parser("vault")
    vault_commands = vault_command.add_subparsers(dest="vault_command", required=True)
    vault_install_command = vault_commands.add_parser("install")
    vault_install_command.add_argument("--home", type=Path, default=Path(SERVER_HOME))
    vault_install_command.add_argument("--document", type=Path, default=None)
    vault_install_command.add_argument(
        "--ssh-host", default="", help="build the PC's document here and install it on that host"
    )
    vault_install_command.add_argument("--machine", default="", help="the server's place name")
    vault_install_command.add_argument("--pc-home", type=Path, default=None)
    vault_install_command.add_argument(
        "--name", action="append", default=[], help="one more qmx/read/* or qmx/data/* name"
    )
    vault_key_command = vault_commands.add_parser("key")
    vault_key_command.add_argument("--home", type=Path, default=Path(SERVER_HOME))
    vault_key_command.add_argument("--machine", default="", help="the server's place name")
    serve = commands.add_parser("serve")
    serve.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    serve.add_argument("--vault", type=Path, default=Path(SERVER_KEYS))
    args = parser.parse_args()
    if args.command == "import":
        from qmx_engine.ledger import redact  # noqa: PLC0415
        from qmx_library.migrate.from_bucket import import_bucket  # noqa: PLC0415
        from qmx_library.store import Store  # noqa: PLC0415

        home = cast(Path, args.home)
        bucket = cast(Path | None, args.bucket) or home / "bucket"
        with Store.open(cast(Path, args.root), redactor=redact, name="server") as store:
            done = import_bucket(store, bucket)
        print(
            f"imported {done.runs} runs, {done.artifacts} artifacts, {done.blobs} blobs, "
            f"{done.skipped} skipped"
        )
        return 0
    if args.command == "rebuild":
        found = rebuild(
            remote=cast(str | None, args.remote),
            root=cast(Path | None, args.root),
            units=tuple(unit for unit in cast(str, args.units).split(",") if unit),
        )
        print(f"{'PASS' if found.get('restored') else 'no bucket, '}{found['said']}")
        return 0 if found.get("restored") else 1
    if args.command == "pair":
        code = pairing_code()
        target = pair(pc_home(parser, args.home), code)
        host = cast(str, args.ssh_host)
        if host:
            if not re.fullmatch(r"[a-zA-Z0-9_@.:-]+", host) or host.startswith("-"):
                parser.error("Use an SSH hostname or user@hostname.")
            ssh = shutil.which("ssh")
            if ssh is None:
                raise RuntimeError("Install SSH before pairing a node.")
            run([ssh, host, f"sudo {RECOVER} pair --from-stdin"], input_text=code)
            print(f"PASS paired {host}; its host restarted with the new key")
            print("restart this PC's host so its Hub link and forwarders read the new key")
        print(f"PASS pairing code written to {target}")
        return 0
    if args.command == "setup":
        host = cast(str, args.ssh_host)
        if not re.fullmatch(r"[a-zA-Z0-9_@.:-]+", host) or host.startswith("-"):
            parser.error("Use an SSH hostname or user@hostname.")
        machine = cast(str, args.machine)
        if not PLACE.fullmatch(machine):
            parser.error("Name the server's place with --machine, the name its host runs under.")
        home = pc_home(parser, args.home)
        revision = run(["git", "rev-parse", "HEAD"])
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise RuntimeError("Setup needs an exact Git commit.")
        dry_run = bool(args.dry_run)
        key_file = cast(Path | None, args.auth_key_file)
        if not dry_run:
            transfer(host, revision)
        return setup(
            host,
            home,
            machine=machine,
            revision=revision,
            call=lambda command, text: run(command, input_text=text),
            hindsight=bool(args.hindsight) or hindsight_enabled(home),
            hub_port=int(args.hub_port),
            dry_run=dry_run,
            auth_key=lambda: key_file.read_text(encoding="utf-8").strip() if key_file else None,
        )
    if args.command == "bootstrap":
        host = cast(str, args.ssh_host)
        if not re.fullmatch(r"[a-zA-Z0-9_@.:-]+", host) or host.startswith("-"):
            parser.error("Use an SSH hostname or user@hostname.")
        git = shutil.which("git")
        if git is None or shutil.which("ssh") is None:
            raise RuntimeError("Install Git and SSH before bootstrapping a node.")
        revision = run(["git", "rev-parse", "HEAD"])
        ssh = transfer(host, revision)
        run(["ssh", host, "sudo bash -s"], input_text=bootstrap_script(revision))
        # No prompt or key is needed when rerunning an already-provisioned node.
        exists = run(
            ["ssh", host, "sudo test -s /etc/qmx/vault/control-token && echo present || true"]
        )
        if not exists:
            token = getpass.getpass(
                "Per-node control token (blank generates one): "
            ) or secrets.token_urlsafe(32)
            run(
                ["ssh", host, "sudo sh -c 'umask 077; cat > /etc/qmx/vault/control-token'"],
                input_text=token,
            )
        print("Installed. Enroll with: ssh " + shlex.quote(host) + " sudo tailscale up")
        print("Then: ssh " + shlex.quote(host) + " sudo systemctl start qmx-node")
        checklist = subprocess.run(
            [ssh, host, "sudo /opt/qmx/qmx-agents/.venv/bin/qmx node verify"],
            check=False,
        )
        return checklist.returncode
    if args.command == "verify":
        checks = verify(args.home, args.vault, root=args.root)
        for name, passed in checks.items():
            print(f"{'PASS' if passed else 'FAIL'} {name}")
        print(f"primary: {library_primary(args.home)}")
        return int(not all(checks.values()))
    if args.command == "login":
        machine = cast(str, args.machine) or socket.gethostname()
        signed_in, line = plan_login(cast(Path, args.home), cast(Path, args.vault), machine)
        print(f"{'PASS' if signed_in else 'not run, '}{line}")
        return 0
    if args.command == "update":
        revision = cast(str, args.revision) or run(["git", "rev-parse", "HEAD"])
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise RuntimeError("Update needs an exact Git commit.")
        done = update(
            cast(Path, args.home),
            cast(Path, args.vault),
            revision=revision,
            timeout_s=float(args.timeout),
        )
        print(f"{'PASS' if done.get('restarted') else 'FAIL'} drained={done.get('drained')}")
        print(json.dumps(done, sort_keys=True))
        return 0 if done.get("restarted") else 1
    if args.command == "vault" and (args.vault_command == "key" or args.ssh_host):
        machine = cast(str, args.machine)
        if not PLACE.fullmatch(machine):
            parser.error("Name the server's place with --machine, the name its host runs under.")
    if args.command == "vault" and args.vault_command == "key":
        print(vault_key(cast(Path, args.home), cast(str, args.machine)))
        return 0
    if args.command == "vault" and args.ssh_host:
        host = cast(str, args.ssh_host)
        if not re.fullmatch(r"[a-zA-Z0-9_@.:-]+", host) or host.startswith("-"):
            parser.error("Use an SSH hostname or user@hostname.")
        machine = cast(str, args.machine)
        as_qmx = f"sudo runuser -u qmx -- {SERVER_VENV}/bin/qmx node vault"
        public = run(["ssh", host, f"{as_qmx} key --home {SERVER_HOME} --machine {machine}"])
        from qmx_router.vault import PROVIDERS, KeyringSource  # noqa: PLC0415 (the PC's keyring)

        names = (*(f"qmx/{row}" for row in PROVIDERS), READ_APP, *cast(list[str], args.name))
        document = pc_vault_document(
            pc_home(parser, args.pc_home), public, machine=machine, source=KeyringSource(names)
        )
        print(run(["ssh", host, f"{as_qmx} install --home {SERVER_HOME}"], input_text=document))
        return 0
    if args.command == "vault":
        home = cast(Path, args.home)
        source = cast(Path | None, args.document)
        document = source.read_text(encoding="utf-8") if source else sys.stdin.read()
        names, gone = vault_install(home, document)
        print(f"PASS vault installed: {len(names)} entries, {len(gone)} tombstones")
        for name in names:
            print(f"  entry {name}")
        for name in gone:
            print(f"  deleted {name}")
        return 0
    address = run(["tailscale", "ip", "-4"]).splitlines()[0]
    if not address.startswith("100."):
        raise RuntimeError("Node control binds only to a Tailscale IPv4 address.")
    token = read_secret(args.vault, "qmx/control-token", "control-token")
    if not token:
        raise RuntimeError("Provision the per-node token before starting the service.")
    service = ControlService(
        args.home,
        tier="T2",
        node=socket.gethostname(),
        secret_getter=lambda service, username: read_secret(args.vault, service, username),
    )
    uvicorn.run(create_app(service, token, "http://127.0.0.1:5173"), host=address, port=8766)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
