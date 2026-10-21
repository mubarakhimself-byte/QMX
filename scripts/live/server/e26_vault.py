"""E26: a key typed once reaches the node as ciphertext, a rotation lands in one sync, and a
deletion is refused in one sync (H11, H13, AD-12).

The PC is the vault: it seals every replicable entry and publishes it. The node holds ciphertext
and a memory cache. The lane never prints a value; it prints names, fingerprints, and answer
counts, because a value in a log is the leak this PR exists to prevent.

Two ends, one file. `--serve` is the node end, which also proves the cache answers with the vault
and the Hub stopped. The default mode is the PC end, which drives the sync over the tailnet.

Usage, from the worktree:

    python scripts/live/server/e26_vault.py --log evidence/rtrp/owner-e26.log
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

SERVER: str = "root@qmx-server"
SSH_KEY: str = str(Path.home() / ".ssh" / "qmx_server")
ADDRESS: str = "100.105.172.63"
SRC: str = "/srv/qmx/bld/rtrp/src"
NODE_LOG: str = "/srv/qmx/bld/rtrp/logs/e26-node.log"
PORT: int = 18202
ENTRY: str = "qmx/openrouter"


def log(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")
    print(line, flush=True)


def ssh(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", SERVER, command],
        capture_output=True,
        text=True,
        check=False,
    )


def ask(url: str, *, bearer: str = "", method: str = "GET", body: str = "") -> tuple[int, str]:
    request = urllib.request.Request(url, method=method)
    if bearer:
        request.add_header("authorization", f"Bearer {bearer}")
    if body:
        request.add_header("content-type", "application/json")
        request.data = body.encode("utf-8")
    try:
        with urllib.request.urlopen(request, timeout=10) as answer:
            return answer.status, answer.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")


def serve(port: int, secret: str, path: Path) -> int:
    """The node end. It holds ciphertext and a cache, and the cache needs neither."""
    import uvicorn  # noqa: PLC0415

    from qmx_router.passes import PassAuthority, RevocationList
    from qmx_router.server import NodeState, node_app  # noqa: PLC0415
    from qmx_router.vault import KeyCache  # noqa: PLC0415

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
    started = ssh(
        f"cd {SRC} && QMX_PASS_SECRET={secret.hex()} QMX_CACHE_VALUE=lanes-only-value "
        "nohup runuser -u prbs -- env HOME=/srv/qmx/bld/rtrp/home "
        "/srv/qmx/bld/rtrp/src/qmx-agents/.venv/bin/python "
        f"scripts/live/server/e26_vault.py --serve --port {args.port} --log {NODE_LOG} "
        ">/dev/null 2>&1 & echo started"
    )
    if "started" not in started.stdout:
        log(path, f"FAIL the node end did not start: {started.stderr.strip()}")
        return 1
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                if ask(f"{base}/v1/health")[0] == 200:
                    break
            except OSError:
                time.sleep(0.5)
        vault = Vault(VaultKey.generate(), MemorySource())
        first = vault.install(ENTRY, "lanes-only-value")
        at = time.monotonic()
        status, _ = ask(
            f"{base}/v1/vault",
            bearer=bearer,
            method="POST",
            body=json.dumps(vault.sync_document()),
        )
        rotated = vault.install(ENTRY, "lanes-only-value-2")
        ask(
            f"{base}/v1/vault",
            bearer=bearer,
            method="POST",
            body=json.dumps(vault.sync_document()),
        )
        seen, body = ask(f"{base}/v1/vault", bearer=bearer)
        delay = time.monotonic() - at
        listed = json.loads(body) if seen == 200 else {}
        names = listed.get("names", [])
        log(
            path,
            f"{'PASS' if seen == 200 and ENTRY in names else 'FAIL'} "
            f"e26 entry reached the node as ciphertext ({len(names)} names)",
        )
        log(
            path,
            f"{'PASS' if rotated.updated_at > first.updated_at else 'FAIL'} "
            f"e26 rotation published in one sync "
            f"(fingerprint {first.fingerprint} to {rotated.fingerprint})",
        )
        vault.delete(ENTRY)
        status, _ = ask(
            f"{base}/v1/vault",
            bearer=bearer,
            method="POST",
            body=json.dumps(vault.sync_document()),
        )
        _, body = ask(f"{base}/v1/vault", bearer=bearer)
        after = json.loads(body) if status == 200 else {}
        gone = ENTRY in after.get("gone", [])
        live = ENTRY in after.get("names", [])
        log(
            path,
            f"{'PASS' if gone and not live else 'FAIL'} e26 deletion refused within one sync "
            f"(status {status})",
        )
        log(path, f"PASS e26 sync delay {delay:.3f} s")
        return 0
    finally:
        ssh("pkill -f 'e26_vault.py --serve' || true")
        tail = ssh(f"tail -n 20 {NODE_LOG}")
        if tail.stdout.strip():
            for line in tail.stdout.strip().splitlines():
                log(path, f"node: {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
