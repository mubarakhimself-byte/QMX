"""Ubuntu node installation and a Tailscale-only, token-protected control service.

`qmx node setup` is the server step of the plan (LIB4, MIGRATION steps 7 and 8): it installs the
Library Hub, the node service and, only when the setting asks for it, Hindsight; imports the
bucket's run folders into the server store; installs the host's unit with the `server` role and
the store root `/srv/qmx/library` owned by `qmx`, so the one host process is the server store's
one writer (DATA-PLAN DR2B); and flips `[library] primary = server` on the PC's home. The Hub and
the node run unprivileged as `qmx`, because a long-lived server process is not root's job.

`qmx node verify` is the doctor: one `PASS`/`FAIL` line per fact, including the primary store the
setting names and whether the Hub answers.

`qmx node rebuild` puts a new server's Library back from the bucket and rebuilds its catalog from
what came back (MIGRATION "When the server is lost", step 3), and `qmx node pair` writes a fresh
pairing code on both ends (step 5). Neither prints a key: a code is written to a file, never shown.

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
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Final, cast

import uvicorn

from qmx_control.server import create_app
from qmx_control.service import ControlService


def run(command: list[str], *, input_text: str | None = None) -> str:
    # Windows text-mode pipes turn shell-script LF into CRLF, which bash rejects.
    result = subprocess.run(
        command,
        input=input_text.encode("utf-8") if input_text is not None else None,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"{command[0]} failed ({result.returncode}); inspect the node logs.")
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


def hub_answers(home: Path) -> bool:
    """One authenticated `/healthz` against the Hub this home names."""
    url = hub_url(home)
    key_file = home / "vault" / "pairing-key"
    if url is None or not key_file.exists():
        return False
    request = urllib.request.Request(  # noqa: S310 (the home's own setting)
        f"{url}/healthz",
        headers={"Authorization": f"Bearer {key_file.read_text(encoding='utf-8').strip()}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as answer:  # noqa: S310
            return bool(json.loads(answer.read()).get("ok"))
    except OSError, urllib.error.URLError, ValueError:
        return False


def verify(home: Path, vault: Path) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    commands = {
        "docker": ["docker", "info"],
        "tailscale": ["tailscale", "ip", "-4"],
        "supervisor": ["systemctl", "is-active", "qmx-node"],
        "hub": ["systemctl", "is-active", "qmx-hub"],
        "shipping": ["systemctl", "is-active", "qmx-ship.timer"],
        "rclone": ["rclone", "version"],
    }
    for name, command in commands.items():
        try:
            checks[name] = bool(run(command))
        except OSError, RuntimeError:
            checks[name] = False
    checks["node_token"] = bool(read_secret(vault, "qmx/control-token", "control-token"))
    checks["pairing_key"] = (vault / "pairing-key").exists()
    checks["bucket"] = (home / "bucket").is_dir()
    checks["library_db"] = (home / "library").is_dir()
    checks["shipping_config"] = (home / "rclone.conf").is_file()
    checks["library_primary"] = library_primary(home) == "server"
    checks["hub_answers"] = hub_answers(home)
    # CLIProxy requires live subscriptions and is provisioned separately by the operator.
    checks["cliproxy"] = (
        bool(run(["docker", "ps", "--filter", "name=qmx-cliproxy", "--format", "{{.Names}}"]))
        if checks["docker"]
        else False
    )
    return checks


def flip_primary(home: Path, url: str, *, primary: str = "server") -> None:
    """Write `[library] primary` and `hub_url` into `home`'s settings, leaving every other line.

    The flip writes `server`; the reverse flip of MIGRATION step 8 writes `pc` with the same Hub,
    which is then a replica. Either value only caches the record on `refs/primary` (AD-14, AD-19).
    """
    if primary not in ("pc", "server"):
        raise ValueError("The primary store is `pc` or `server`.")
    path = home / "settings.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    kept: list[str] = []
    inside = False
    for line in existing:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            inside = stripped == "[library]"
            if inside:
                kept.extend([line, f'primary = "{primary}"', f'hub_url = "{url}"'])
                continue
        if inside and re.match(r"^(primary|hub_url)\s*=", stripped):
            continue
        kept.append(line)
    if "[library]" not in "\n".join(kept):
        if kept and kept[-1] != "":
            kept.append("")
        kept.extend(["[library]", f'primary = "{primary}"', f'hub_url = "{url}"'])
    path.write_text("\n".join(kept).rstrip("\n") + "\n", encoding="utf-8")


PAIRING_KEY: Final = "pairing-key"
"""The key both ends hold after a pairing: this machine's name on the Hub, not a right (AD-11)."""
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
    which is why the server-loss step 5 pairs again rather than reusing it.
    """
    found = code or pairing_code()
    target = home / "vault" / PAIRING_KEY
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(found + "\n", encoding="utf-8")
    if os.name == "posix":
        temporary.chmod(0o600)
    temporary.replace(target)
    return target


def rebuild(
    home: Path,
    *,
    remote: str | None = None,
    root: Path | None = None,
    prefix: str = BUCKET_PREFIX,
    runner: Callable[[Sequence[str]], str] | None = None,
) -> dict[str, object]:
    """Put the bucket's Library evidence back under `root` and rebuild the catalog from it.

    MIGRATION "When the server is lost" step 3: the old server pushed objects, refs, edges and
    durable blobs after each commit batch, so a new server restores those and rebuilds its index;
    the catalog is never copied, because it is derived (AD-16). Without a bucket remote nothing is
    restored and the answer says so in the same words the push uses.
    """
    from qmx_hub.bucket import NO_BUCKET  # noqa: PLC0415 (the sentence has one owner)

    target = root or home / "library"
    if not remote:
        return {"restored": False, "said": NO_BUCKET}
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
SERVER_LIBRARY: Final = "/srv/qmx/library"
"""The server store's root (Appendix D), owned by `qmx` because the host is its one writer."""


def host_unit(role: str = "server") -> str:
    """The unit DR2A ships, with the role the server runs (AD-19, AD-26; DATA-PLAN DR2B).

    On the server the one host process opens the store as its writer and answers the Library
    routes, so its role is `server`. The file DR2A wrote names `--role node`, so this rewrites that
    one flag and leaves everything else as it stands, `OOMScoreAdjust` included (P-OOM reads it).
    """
    path = Path(__file__).parents[3] / "qmx-host" / "deploy" / HOST_UNIT
    if not path.is_file():
        raise RuntimeError(f"the host's unit is missing at {path}; install the source tree first")
    return path.read_text(encoding="utf-8").replace("--role node", f"--role {role}")


def host_unit_script(role: str = "server") -> str:
    """The shell the setup step runs on the server: the store root, then DR2A's unit enabled."""
    return (
        "set -eu\n"
        f"install -d -o qmx -g qmx -m 750 {SERVER_LIBRARY}\n"
        f"cat > /etc/systemd/system/{HOST_UNIT} <<'QMXUNIT'\n"
        f"{host_unit(role)}"
        "QMXUNIT\n"
        "systemctl daemon-reload\n"
        "systemctl enable qmx-host\n"
    )


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
    """`qmx node update`: drain, then install the pinned revision and let the bootstrap restart.

    `installer` and `address_of` are the install step and the node's own address, so a test never
    runs sudo or asks Tailscale; the real ones are the bootstrap script and `tailscale ip -4`.
    """

    def bootstrap_install(pinned: str) -> None:
        run(["sudo", "bash", "-s"], input_text=bootstrap_script(pinned))

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


def transfer(host: str, revision: str) -> str:
    """Ship the pinned source archive to the host and run the bootstrap script there."""
    ssh = shutil.which("ssh")
    git = shutil.which("git")
    if ssh is None or git is None:
        raise RuntimeError("Install Git and SSH before setting up a node.")
    repository = run(["git", "rev-parse", "--show-toplevel"])
    archive = subprocess.run(
        [git, "-C", repository, "archive", "--format=tar", revision],
        capture_output=True,
        check=True,
    ).stdout
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


def main() -> int:
    parser = argparse.ArgumentParser(prog="qmx")
    node = parser.add_subparsers(dest="group", required=True).add_parser("node")
    commands = node.add_subparsers(dest="command", required=True)
    bootstrap = commands.add_parser("bootstrap")
    bootstrap.add_argument("ssh_host")
    setup = commands.add_parser("setup")
    setup.add_argument("ssh_host")
    setup.add_argument("--home", type=Path, default=Path("./qmx-home"))
    setup.add_argument("--remote-home", type=Path, default=Path("/var/lib/qmx"))
    setup.add_argument("--hub-port", type=int, default=0)
    setup.add_argument("--hindsight", action="store_true")
    importer = commands.add_parser("import")
    importer.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    importer.add_argument("--bucket", type=Path, default=None)
    rebuilding = commands.add_parser("rebuild")
    rebuilding.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    rebuilding.add_argument("--root", type=Path, default=None)
    rebuilding.add_argument("--remote", default=None, help="the rclone remote holding the bucket")
    pairing = commands.add_parser("pair")
    pairing.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    pairing.add_argument("--ssh-host", default="", help="also install the same code on that host")
    check = commands.add_parser("verify")
    check.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    check.add_argument("--vault", type=Path, default=Path("/etc/qmx/vault"))
    login = commands.add_parser("login")
    login.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    login.add_argument("--vault", type=Path, default=Path("/etc/qmx/vault"))
    login.add_argument("--machine", default="")
    refresh = commands.add_parser("update")
    refresh.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    refresh.add_argument("--vault", type=Path, default=Path("/etc/qmx/vault"))
    refresh.add_argument("--revision", default="")
    refresh.add_argument("--timeout", type=float, default=3600.0)
    vault_command = commands.add_parser("vault")
    vault_commands = vault_command.add_subparsers(dest="vault_command", required=True)
    vault_install_command = vault_commands.add_parser("install")
    vault_install_command.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    vault_install_command.add_argument("--document", type=Path, default=None)
    serve = commands.add_parser("serve")
    serve.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    serve.add_argument("--vault", type=Path, default=Path("/etc/qmx/vault"))
    args = parser.parse_args()
    if args.command == "import":
        from qmx_engine.ledger import redact  # noqa: PLC0415
        from qmx_library.migrate.from_bucket import import_bucket  # noqa: PLC0415
        from qmx_library.store import Store  # noqa: PLC0415

        home = cast(Path, args.home)
        bucket = cast(Path | None, args.bucket) or home / "bucket"
        with Store.open(home / "library", redactor=redact, name="server") as store:
            done = import_bucket(store, bucket)
        print(
            f"imported {done.runs} runs, {done.artifacts} artifacts, {done.blobs} blobs, "
            f"{done.skipped} skipped"
        )
        return 0
    if args.command == "rebuild":
        found = rebuild(
            cast(Path, args.home),
            remote=cast(str | None, args.remote),
            root=cast(Path | None, args.root),
        )
        print(f"{'PASS' if found.get('restored') else 'no bucket, '}{found['said']}")
        return 0 if found.get("restored") else 1
    if args.command == "pair":
        code = pairing_code()
        target = pair(cast(Path, args.home), code)
        host = cast(str, args.ssh_host)
        if host:
            if not re.fullmatch(r"[a-zA-Z0-9_@.:-]+", host) or host.startswith("-"):
                parser.error("Use an SSH hostname or user@hostname.")
            ssh = shutil.which("ssh")
            if ssh is None:
                raise RuntimeError("Install SSH before pairing a node.")
            run(
                [ssh, host, "sudo sh -c 'umask 077; cat > /etc/qmx/vault/pairing-key'"],
                input_text=code,
            )
            print(f"PASS paired {host}")
        print(f"PASS pairing code written to {target}")
        return 0
    if args.command == "setup":
        host = cast(str, args.ssh_host)
        if not re.fullmatch(r"[a-zA-Z0-9_@.:-]+", host) or host.startswith("-"):
            parser.error("Use an SSH hostname or user@hostname.")
        revision = run(["git", "rev-parse", "HEAD"])
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise RuntimeError("Setup needs an exact Git commit.")
        home = cast(Path, args.home)
        remote = cast(Path, args.remote_home)
        hindsight = bool(args.hindsight) or hindsight_enabled(home)
        ssh = transfer(host, revision)
        run(
            [ssh, host, "sudo bash -s"],
            input_text=bootstrap_script(revision, hindsight=hindsight, hub_port=int(args.hub_port)),
        )
        # The Hub holds the store's writer lock, so the import stops it first and starts it after,
        # and it runs as `qmx` because the store's files belong to that user.
        run([ssh, host, "sudo systemctl stop qmx-hub || true"])
        run(
            [
                ssh,
                host,
                "sudo runuser -u qmx -- /opt/qmx/qmx-agents/.venv/bin/qmx node import "
                f"--home {remote}",
            ]
        )
        run([ssh, host, "sudo systemctl restart qmx-hub qmx-node"])
        # DR2B: the server's Library service is the host's, so the setup installs DR2A's unit with
        # the `server` role and makes the store root `/srv/qmx/library` belong to `qmx`.
        run([ssh, host, "sudo bash -s"], input_text=host_unit_script())
        address = run([ssh, host, "tailscale ip -4"]).splitlines()[0]
        port = run([ssh, host, f"sudo cat {remote}/hub.port"]).strip()
        url = f"http://{address}:{port}"
        (home / "vault").mkdir(parents=True, exist_ok=True)
        # The pairing key is generated on the server by the bootstrap and copied down; its bytes
        # are never printed, so they cannot land in a log (MIGRATION step 7, AD-11).
        key = run([ssh, host, "sudo cat /etc/qmx/vault/pairing-key"])
        (home / "vault" / "pairing-key").write_text(key + "\n", encoding="utf-8")
        flip_primary(home, url)
        print(f"primary: {library_primary(home)}")
        print(f"hub: {url}")
        checks = verify(home, home / "vault")
        for name, passed in checks.items():
            print(f"{'PASS' if passed else 'FAIL'} {name}")
        return int(not all(checks.values()))
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
        checks = verify(args.home, args.vault)
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
