"""Ubuntu node installation and a Tailscale-only, token-protected control service.

`qmx node setup` is the server step of the plan (LIB4, MIGRATION steps 7 and 8): it installs the
Library Hub, the node service and, only when the setting asks for it, Hindsight; imports the
bucket's run folders into the server store; and flips `[library] primary = server` on the PC's
home. The Hub and the node run unprivileged as `qmx`, because a long-lived server process is not
root's job.

`qmx node verify` is the doctor: one `PASS`/`FAIL` line per fact, including the primary store the
setting names and whether the Hub answers.
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
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

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


def bootstrap_script(revision: str, *, hindsight: bool = False, hub_port: int = 0) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Bootstrap needs an exact Git commit.")
    if not 18100 <= hub_port <= 18199:
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


def flip_primary(home: Path, url: str) -> None:
    """Write `[library] primary = server` into `home`'s settings, leaving every other line."""
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
                kept.extend([line, 'primary = "server"', f'hub_url = "{url}"'])
                continue
        if inside and re.match(r"^(primary|hub_url)\s*=", stripped):
            continue
        kept.append(line)
    if "[library]" not in "\n".join(kept):
        if kept and kept[-1] != "":
            kept.append("")
        kept.extend(["[library]", 'primary = "server"', f'hub_url = "{url}"'])
    path.write_text("\n".join(kept).rstrip("\n") + "\n", encoding="utf-8")


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
    check = commands.add_parser("verify")
    check.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    check.add_argument("--vault", type=Path, default=Path("/etc/qmx/vault"))
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
            ["ssh", host, "sudo bash -s"],
            input_text=bootstrap_script(revision, hindsight=hindsight, hub_port=int(args.hub_port)),
        )
        exists = run(
            ["ssh", host, "sudo test -s /etc/qmx/vault/pairing-key && echo present || true"]
        )
        if not exists:
            # The pairing key is generated on the server and copied down; its bytes are never
            # printed here, so it cannot land in a log (MIGRATION step 7, AD-11).
            generated = subprocess.run(
                [ssh, host, "sudo sh -c 'umask 077; cat > /etc/qmx/vault/pairing-key'"],
                input=secrets.token_hex(32).encode("utf-8"),
                capture_output=True,
                check=False,
            )
            if generated.returncode:
                raise RuntimeError("SSH could not exchange the Hub pairing key.")
        # The Hub holds the store's writer lock, so the import stops it first and starts it after.
        run(["ssh", host, "sudo systemctl stop qmx-hub || true"])
        run(["ssh", host, f"sudo /opt/qmx/qmx-agents/.venv/bin/qmx node import --home {remote}"])
        run(["ssh", host, "sudo systemctl restart qmx-hub qmx-node"])
        address = run(["ssh", host, "tailscale ip -4"]).splitlines()[0]
        port = run(["ssh", host, f"sudo cat {remote}/hub.port"]).strip()
        url = f"http://{address}:{port}"
        (home / "vault").mkdir(parents=True, exist_ok=True)
        key = run(["ssh", host, "sudo cat /etc/qmx/vault/pairing-key"])
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
