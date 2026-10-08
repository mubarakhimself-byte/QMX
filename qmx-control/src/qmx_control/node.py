"""Ubuntu node installation and a Tailscale-only, token-protected control service."""

from __future__ import annotations

import argparse
import getpass
import os
import re
import secrets
import shlex
import shutil
import socket
import subprocess
from pathlib import Path
from typing import cast

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


def bootstrap_script(revision: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Bootstrap needs an exact Git commit.")
    return (
        Path(__file__)
        .with_name("node-bootstrap.sh")
        .read_text(encoding="utf-8")
        .replace("@REVISION@", revision)
    )


def verify(home: Path, vault: Path) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    commands = {
        "docker": ["docker", "info"],
        "tailscale": ["tailscale", "ip", "-4"],
        "supervisor": ["systemctl", "is-active", "qmx-node"],
        "shipping": ["systemctl", "is-active", "qmx-ship.timer"],
        "rclone": ["rclone", "version"],
    }
    for name, command in commands.items():
        try:
            checks[name] = bool(run(command))
        except OSError, RuntimeError:
            checks[name] = False
    checks["node_token"] = bool(read_secret(vault, "qmx/control-token", "control-token"))
    checks["bucket"] = (home / "bucket").is_dir()
    checks["shipping_config"] = (home / "rclone.conf").is_file()
    # CLIProxy requires live subscriptions and is provisioned separately by the operator.
    checks["cliproxy"] = (
        bool(run(["docker", "ps", "--filter", "name=qmx-cliproxy", "--format", "{{.Names}}"]))
        if checks["docker"]
        else False
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(prog="qmx")
    node = parser.add_subparsers(dest="group", required=True).add_parser("node")
    commands = node.add_subparsers(dest="command", required=True)
    bootstrap = commands.add_parser("bootstrap")
    bootstrap.add_argument("ssh_host")
    check = commands.add_parser("verify")
    check.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    check.add_argument("--vault", type=Path, default=Path("/etc/qmx/vault"))
    serve = commands.add_parser("serve")
    serve.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    serve.add_argument("--vault", type=Path, default=Path("/etc/qmx/vault"))
    args = parser.parse_args()
    if args.command == "bootstrap":
        host = cast(str, args.ssh_host)
        if not re.fullmatch(r"[a-zA-Z0-9_@.:-]+", host) or host.startswith("-"):
            parser.error("Use an SSH hostname or user@hostname.")
        ssh = shutil.which("ssh")
        git = shutil.which("git")
        if ssh is None or git is None:
            raise RuntimeError("Install Git and SSH before bootstrapping a node.")
        revision = run(["git", "rev-parse", "HEAD"])
        repository = run(["git", "rev-parse", "--show-toplevel"])
        archive = subprocess.run(
            [git, "-C", repository, "archive", "--format=tar", revision],
            capture_output=True,
            check=True,
        ).stdout
        transfer = subprocess.run(
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
        if transfer.returncode:
            raise RuntimeError("SSH could not transfer the pinned QMX source archive.")
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
            [ssh, host, "sudo /opt/qmx/qmx-control/.venv/bin/qmx node verify"],
            check=False,
        )
        return checklist.returncode
    if args.command == "verify":
        checks = verify(args.home, args.vault)
        for name, passed in checks.items():
            print(f"{'PASS' if passed else 'FAIL'} {name}")
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
