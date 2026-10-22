"""E26: a key typed once reaches the node as ciphertext, a rotation lands in one sync, and a
deletion is refused in one sync (H11, H13, AD-12).

The PC is the vault: it seals every replicable entry and publishes it. The node holds ciphertext
and a memory cache. The lane never prints a value; it prints names, fingerprints, and answer
codes, because a value in a log is the leak this PR exists to prevent.

Two ends, one file. `--serve` is the node end, which also proves the cache answers with the vault
and the Hub stopped: no sync has ever reached it and the cached value is still there. The default
mode is the PC end, which drives the sync over the tailnet.

Usage, from the worktree:

    python scripts/live/server/e26_vault.py --log evidence/rtrp/owner-e26.log
"""

from __future__ import annotations

import argparse
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
SRC: str = "/srv/qmx/bld/rtrp/src"
NODE_LOG: str = "/srv/qmx/bld/rtrp/logs/e26-node.log"
PORT: int = 18202
UNIT: str = "rtrp-e26"
WAIT_S: float = 60.0
ENTRY: str = "qmx/openrouter"


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
    """The node end. It holds ciphertext and a cache, and the cache needs neither."""
    import uvicorn  # noqa: PLC0415

    from qmx_router.passes import PassAuthority, RevocationList
    from qmx_router.server import NodeState, node_app
    from qmx_router.vault import KeyCache

    authority = PassAuthority(
        secret=bytes.fromhex(secret),
        revocations=RevocationList(path.parent / "e26-revoked.json"),
    )
    state = NodeState(site="contabo", passes=authority)
    cache = KeyCache()
    planted = os.environ.get("QMX_CACHE_VALUE", "")
    if planted:
        cache.put(ENTRY, planted, 600.0)
    # The vault and the Hub are stopped as far as this process is concerned: no sync has ever
    # reached it. A cached value answering is the whole point of the cache.
    answered = cache.get(ENTRY) == planted and planted != ""
    log(path, f"{'PASS' if answered else 'FAIL'} e26 cached keys answer with the vault stopped")
    log(path, f"{'PASS' if not state.vault.has(ENTRY) else 'FAIL'} e26 no ciphertext before sync")
    log(path, f"node app on 0.0.0.0:{port}")
    uvicorn.run(node_app(state), host="0.0.0.0", port=port, log_level="warning")
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
        placement="contabo",
        read_scope=("vault",),
        write_prefix="vault",
        key_scope=("*",),
        model_scope=("*",),
    )
    base = f"http://{ADDRESS}:{args.port}"
    ssh(f"mkdir -p {Path(NODE_LOG).parent} && rm -f {NODE_LOG}")
    log(path, f"run {time.strftime('%Y-%m-%dT%H:%M:%S')} port {args.port}")
    ssh(f"systemctl stop {UNIT} 2>/dev/null || true")
    started = ssh(
        f"systemd-run --collect --uid=prbs --gid=prbs --working-directory={SRC} "
        "--setenv=HOME=/srv/qmx/bld/rtrp/home "
        f"--setenv=QMX_PASS_SECRET={secret.hex()} --setenv=QMX_CACHE_VALUE=lanes-only-value "
        f"--unit={UNIT} /srv/qmx/bld/rtrp/src/qmx-agents/.venv/bin/python "
        f"scripts/live/server/e26_vault.py --serve --port {args.port} --log {NODE_LOG}"
    )
    if "Running as unit" not in started.stdout + started.stderr:
        log(path, f"FAIL the node end did not start: {started.stdout} {started.stderr}")
        return 1
    checks: list[tuple[str, bool]] = []
    try:
        if not wait_for_health(f"{base}/v1/health", path):
            return 1
        vault = Vault(VaultKey.generate(), MemorySource())
        first = vault.install(ENTRY, "lanes-only-value")
        at = time.monotonic()
        posted, _ = ask(
            f"{base}/v1/vault", bearer=bearer, method="POST", body=json.dumps(vault.sync_document())
        )
        rotated = vault.install(ENTRY, "lanes-only-value-2")
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
        tail = ssh(f"tail -n 20 {NODE_LOG}")
        if tail.stdout.strip():
            for line in tail.stdout.strip().splitlines():
                log(path, f"node: {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
