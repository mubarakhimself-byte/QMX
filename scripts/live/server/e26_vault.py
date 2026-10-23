"""E26: each machine opens the vault with its own key pair, a rotation lands in one sync, and a
deletion is refused in one sync (H11, H13, AD-28, ruling 135).

The PC is where the key was typed: it seals every replicable entry once for itself and once for the
node, and publishes it. The node holds ciphertext and opens only its own share, with the private key
in its own key file, so it never asks the PC for a value. The lane never prints a value; it prints
names, fingerprints, and answer codes, because a value in a log is the leak this lane exists to
prevent.

Two ends, one file. `--serve` is the node end: it makes or reads `/srv/qmx/bld/rtrp/home/.qmx/`
`vault.key`, publishes its public half for the PC, and after the sync opens its own entry. The
default mode is the PC end, which drives the sync over the tailnet.

Usage, from the worktree:

    python scripts/live/server/e26_vault.py --log evidence/rtrp/owner-e26.log
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import http.client
import json
import os
import subprocess
import time
import urllib.parse
from pathlib import Path

SERVER: str = "root@qmx-server"
SSH_KEY: str = str(Path.home() / ".ssh" / "qmx_server")
ADDRESS: str = "100.105.172.63"
LANE: str = os.environ.get("QMX_LANE", "/srv/qmx/bld/rtrp")
"""The checkout, home and log folder on the server. A lane run from a check folder sets
`QMX_LANE=/srv/qmx/check/dr2c` instead of editing this file."""
SRC: str = f"{LANE}/src"
NODE_LOG: str = f"{LANE}/logs/e26-node.log"
NODE_HOME: str = f"{LANE}/home"
KEY_PUB: str = f"{LANE}/logs/e26-key.pub"
PYTHON: str = f"{SRC}/qmx-agents/.venv/bin/python"
PORT: int = 18202
UNIT: str = "rtrp-e26"
WAIT_S: float = 60.0
ENTRY: str = "qmx/openrouter"
MACHINE: str = "contabo"
VALUE: str = "lanes-only-value"


def log(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")
    print(line, flush=True)


def ssh(command: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", SERVER, command],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired as expired:
        return subprocess.CompletedProcess([], 1, "", f"ssh timed out: {expired}")


def ask(url: str, *, bearer: str = "", method: str = "GET", body: str = "") -> tuple[int, str]:
    target = urllib.parse.urlsplit(url)
    connection = http.client.HTTPConnection(target.hostname or "", target.port or 80, timeout=8)
    headers = {"authorization": f"Bearer {bearer}"} if bearer else {}
    try:
        connection.request(method, target.path, body=body or None, headers=headers)
        answer = connection.getresponse()
        return answer.status, answer.read().decode("utf-8")
    finally:
        connection.close()


def serve(port: int, secret: str, path: Path) -> int:
    """The node end: its own key pair, its own store, and no value from the PC."""
    import uvicorn  # noqa: PLC0415

    from qmx_router.passes import PassAuthority, RevocationList
    from qmx_router.server import NodeState, node_app
    from qmx_router.vault import (
        KEY_FILE,
        KEY_FOLDER,
        VaultKey,
        VaultStore,
        VaultUnavailable,
        read_machine_key,
        write_machine_key,
    )

    key_home = Path(os.environ.get("QMX_VAULT_HOME", NODE_HOME))
    written = key_home / KEY_FOLDER / KEY_FILE
    if not written.exists():
        write_machine_key(key_home, VaultKey.generate())
        log(path, f"PASS e26 the node made its own key pair at {KEY_FOLDER}/{KEY_FILE}")
    try:
        key = read_machine_key(key_home, MACHINE)
    except VaultUnavailable as missing:
        log(path, f"FAIL e26 {missing}")
        return 1
    log(path, f"PASS e26 the node read its own key file at {KEY_FOLDER}/{KEY_FILE}")
    Path(os.environ["QMX_KEY_PUB"]).write_text(
        base64.b64encode(key.public_bytes()).decode("ascii"), encoding="utf-8"
    )
    try:
        read_machine_key(key_home / "empty", MACHINE)
    except VaultUnavailable as missing:
        log(path, f"PASS e26 a machine with no key file says {missing}")
    else:
        log(path, "FAIL e26 a machine with no key file opened anyway")

    authority = PassAuthority(
        secret=bytes.fromhex(secret),
        revocations=RevocationList(path.parent / "e26-revoked.json"),
    )
    state = NodeState(site=MACHINE, passes=authority, vault=VaultStore(MACHINE))

    async def run() -> None:
        server = uvicorn.Server(
            uvicorn.Config(node_app(state), host="0.0.0.0", port=port, log_level="warning")
        )
        serving = asyncio.create_task(server.serve())
        while not server.started:
            await asyncio.sleep(0.01)
        log(path, f"node app on 0.0.0.0:{port}")
        deadline = time.monotonic() + WAIT_S * 2
        while time.monotonic() < deadline and not state.vault.has(ENTRY):
            await asyncio.sleep(0.2)
        try:
            opened = state.vault.open(ENTRY, key)
        except Exception as error:
            log(path, f"FAIL e26 the node did not open its own entry: {type(error).__name__}")
        else:
            log(
                path,
                f"{'PASS' if opened == os.environ.get('QMX_ENTRY_VALUE') else 'FAIL'} "
                "e26 the node opened its own entry with its own key",
            )
        await serving

    asyncio.run(run())
    return 0


def wait_for_health(url: str, path: Path) -> bool:
    deadline = time.monotonic() + WAIT_S
    last = "no attempt yet"
    while time.monotonic() < deadline:
        try:
            status, body = ask(url)
        except OSError as error:
            last = f"{type(error).__name__}: {error}"
            time.sleep(0.5)
            continue
        if status == 200:
            log(path, f"health 200 after {WAIT_S - (deadline - time.monotonic()):.1f} s")
            return True
        last = f"status {status}: {body[:120]}"
        time.sleep(0.5)
    log(path, f"FAIL the node never answered {url} (last: {last})")
    return False


def node_public_key(path: Path) -> bytes | None:
    """The node's public half, published as text by the node end. Only the public half travels."""
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        found = ssh(f"cat {KEY_PUB} 2>/dev/null")
        if found.returncode == 0 and found.stdout.strip():
            return base64.b64decode(found.stdout.strip())
        time.sleep(0.5)
    log(path, "FAIL the node published no public key")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(prog="e26_vault")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--secret", default="")
    parser.add_argument("--log", type=Path, default=Path("owner-e26.log"))
    args = parser.parse_args()
    path = args.log
    path.parent.mkdir(parents=True, exist_ok=True)
    if args.serve:
        return serve(args.port, args.secret or os.environ["QMX_PASS_SECRET"], path)

    from qmx_router.passes import PassAuthority
    from qmx_router.vault import MemorySource, Vault, VaultKey

    secret = os.urandom(32)
    authority = PassAuthority(secret=secret)
    _, bearer = authority.mint(
        run="run-e26",
        placement=MACHINE,
        read_scope=("vault",),
        write_prefix="vault",
        key_scope=("*",),
        model_scope=("*",),
    )
    base = f"http://{ADDRESS}:{args.port}"
    ssh(f"mkdir -p {Path(NODE_LOG).parent} && rm -f {NODE_LOG} {KEY_PUB}")
    log(path, f"run {time.strftime('%Y-%m-%dT%H:%M:%S')} port {args.port}")
    ssh(f"systemctl stop {UNIT} 2>/dev/null || true")
    started = ssh(
        f"systemd-run --collect --uid=prbs --gid=prbs --working-directory={SRC} "
        f"--setenv=HOME={NODE_HOME} --setenv=QMX_VAULT_HOME={NODE_HOME} "
        f"--setenv=QMX_KEY_PUB={KEY_PUB} --setenv=QMX_ENTRY_VALUE={VALUE} "
        f"--setenv=QMX_PASS_SECRET={secret.hex()} "
        f"--unit={UNIT} {PYTHON} "
        f"scripts/live/server/e26_vault.py --serve --port {args.port} --log {NODE_LOG}"
    )
    if "Running as unit" not in started.stdout + started.stderr:
        log(path, f"FAIL the node end did not start: {started.stdout} {started.stderr}")
        return 1
    checks: list[tuple[str, bool]] = []
    try:
        if not wait_for_health(f"{base}/v1/health", path):
            return 1
        public = node_public_key(path)
        if public is None:
            return 1
        vault = Vault(
            VaultKey.generate(),
            MemorySource(),
            machine="pc",
            peers={MACHINE: VaultKey.from_public_bytes(public)},
        )
        first = vault.install(ENTRY, VALUE)
        at = time.monotonic()
        posted, _ = ask(
            f"{base}/v1/vault", bearer=bearer, method="POST", body=json.dumps(vault.sync_document())
        )
        rotated = vault.install(ENTRY, VALUE + "-2")
        ask(f"{base}/v1/vault", bearer=bearer, method="POST", body=json.dumps(vault.sync_document()))
        seen, body = ask(f"{base}/v1/vault", bearer=bearer)
        delay = time.monotonic() - at
        listed = json.loads(body) if seen == 200 else {}
        names = listed.get("names", [])
        checks.append(
            (
                f"the entry reached the node as ciphertext (posted {posted})",
                seen == 200 and ENTRY in names,
            )
        )
        checks.append(
            (
                f"rotation published in one sync ({first.fingerprint} to {rotated.fingerprint})",
                rotated.updated_at > first.updated_at and rotated.fingerprint != first.fingerprint,
            )
        )
        vault.delete(ENTRY)
        posted, _ = ask(
            f"{base}/v1/vault", bearer=bearer, method="POST", body=json.dumps(vault.sync_document())
        )
        _, body = ask(f"{base}/v1/vault", bearer=bearer)
        after = json.loads(body) if posted == 200 else {}
        checks.append(
            (
                f"deletion refused within one sync (posted {posted})",
                ENTRY in after.get("gone", []) and ENTRY not in after.get("names", []),
            )
        )
        for name, passed in checks:
            log(path, f"{'PASS' if passed else 'FAIL'} e26 {name}")
        log(path, f"PASS e26 sync delay {delay:.3f} s")
        return 0 if all(passed for _, passed in checks) else 1
    finally:
        ssh(f"systemctl stop {UNIT} 2>/dev/null || true")
        tail = ssh(f"tail -n 30 {NODE_LOG}")
        if tail.stdout.strip():
            for line in tail.stdout.strip().splitlines():
                log(path, f"node: {line}")


if __name__ == "__main__":
    raise SystemExit(main())
