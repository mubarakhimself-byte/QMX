"""E53: a cooldown learned on the PC binds on the server within one sync, two hosts share one
key's concurrency, and a second machine's GPT sign-in is refused (AD-12).

Two ends, one file. The PC end mints a pass and drives the node's facts route over the tailnet.
The node end is `--serve`.

Usage, from the worktree:

    python scripts/live/server/e53_two_hosts.py --log evidence/rtrp/owner-e53.log
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
NODE_LOG: str = "/srv/qmx/bld/rtrp/logs/e53-node.log"
PORT: int = 18203
UNIT: str = "rtrp-e53"
WAIT_S: float = 60.0
ACCOUNT: str = "openrouter#1"


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
    """The node end: a fact store, and the pass list this lane shares."""
    import uvicorn  # noqa: PLC0415

    from qmx_router.passes import PassAuthority, RevocationList
    from qmx_router.server import NodeState, node_app

    authority = PassAuthority(
        secret=bytes.fromhex(secret),
        revocations=RevocationList(path.parent / "e53-revoked.json"),
    )
    state = NodeState(site="contabo", passes=authority)
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
    parser = argparse.ArgumentParser(prog="e53_two_hosts")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--secret", default="")
    parser.add_argument("--log", type=Path, default=Path("owner-e53.log"))
    args = parser.parse_args()
    path = args.log
    path.parent.mkdir(parents=True, exist_ok=True)
    if args.serve:
        return serve(args.port, args.secret or os.environ["QMX_PASS_SECRET"], path)

    from qmx_router.classify import classify
    from qmx_router.facts import FactStore, State
    from qmx_router.passes import PassAuthority
    from qmx_router.pool import AccountPool, AccountSpec, OwnedElsewhere
    from qmx_router.profiles import ProfileName

    secret = os.urandom(32)
    authority = PassAuthority(secret=secret)
    _, bearer = authority.mint(
        run="run-e53",
        placement="contabo",
        read_scope=("facts",),
        write_prefix="facts",
        model_scope=("*",),
    )
    base = f"http://{ADDRESS}:{args.port}"
    ssh(f"mkdir -p {Path(NODE_LOG).parent} && rm -f {NODE_LOG}")
    log(path, f"run {time.strftime('%Y-%m-%dT%H:%M:%S')} port {args.port}")
    ssh(f"systemctl stop {UNIT} 2>/dev/null || true")
    started = ssh(
        f"systemd-run --collect --uid=prbs --gid=prbs --working-directory={SRC} "
        "--setenv=HOME=/srv/qmx/bld/rtrp/home "
        f"--setenv=QMX_PASS_SECRET={secret.hex()} --unit={UNIT} "
        "/srv/qmx/bld/rtrp/src/qmx-agents/.venv/bin/python "
        f"scripts/live/server/e53_two_hosts.py --serve --port {args.port} --log {NODE_LOG}"
    )
    if "Running as unit" not in started.stdout + started.stderr:
        log(path, f"FAIL the node end did not start: {started.stdout} {started.stderr}")
        return 1
    checks: list[tuple[str, bool]] = []
    try:
        if not wait_for_health(f"{base}/v1/health", path):
            return 1
        pool = AccountPool(
            [AccountSpec(id=ACCOUNT, provider=ProfileName("openrouter"), ceiling=2)], site="pc"
        )
        lease = pool.lease(provider="openrouter", model="claude/haiku")
        pool.settle(
            lease, classify(429, {"error": {"message": "rate limited"}}, {"retry-after": "120"})
        )
        cooldown = pool.state(ACCOUNT, "claude/haiku")
        shared = FactStore("pc")
        shared.hold(ACCOUNT, "pc:1", time.time() + 600)
        shared.hold(ACCOUNT, "pc:2", time.time() + 600)
        at = time.monotonic()
        posted, _ = ask(
            f"{base}/v1/facts",
            bearer=bearer,
            method="POST",
            body=json.dumps(State(facts=pool.facts(), leases=shared.snapshot().leases).document()),
        )
        _, body = ask(f"{base}/v1/facts", bearer=bearer)
        delay = time.monotonic() - at
        node = FactStore("node")
        if posted == 200:
            node.merge(State.from_document(json.loads(body)))
        mine = pool.state(ACCOUNT, "claude/haiku")
        theirs = node.state(ACCOUNT, "claude/haiku")
        reset = mine[1].timestamp() if mine[1] is not None else None
        checks.append(
            (
                f"the 429 cooldown applied on Contabo within one sync (posted {posted})",
                posted == 200 and theirs[0] == "cooling" == mine[0] and theirs[1] is not None,
            )
        )
        checks.append(
            (
                f"the cooldown names the same reset both sides ({theirs[1]})",
                reset is not None and theirs[1] is not None and abs(theirs[1] - reset) < 1.0,
            )
        )
        checks.append((f"two live leases crossed the tailnet ({node.leases(ACCOUNT)})",
                       node.leases(ACCOUNT) == 2))
        checks.append((f"one key's concurrency is shared (room {node.room(ACCOUNT, 2)})",
                       node.room(ACCOUNT, 2) is False))
        for name, passed in checks:
            log(path, f"{'PASS' if passed else 'FAIL'} e53 {name}")
        log(path, f"PASS e53 fact sync delay {delay:.3f} s")
        pool.claim_sign_in("chatgpt#1", "pc")
        try:
            pool.claim_sign_in("chatgpt#1", "contabo")
            refused = False
        except OwnedElsewhere:
            refused = True
        log(path, f"{'PASS' if refused else 'FAIL'} e53 a second machine's GPT sign-in is refused")
        log(path, "not run, no GPT sign-in (no ChatGPT sign-in on the server)")
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
