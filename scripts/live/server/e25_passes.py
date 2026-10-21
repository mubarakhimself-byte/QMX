"""E25 across the pair: a pass is the only thing a remote attempt may carry (AD-41).

The PC mints passes; the node runs the tailnet app the PC reaches and refuses. Every refusal is
read by its own code, not by its status, because a 403 that means the wrong thing is a pass that
worked for the wrong reason.

Two ends, one file. The PC end is the default and drives the lane. The node end is `--serve`: it
starts the app on the tailnet, writes its own log, and waits. The PC end stops it at the end.

Usage, from the worktree:

    python scripts/live/server/e25_passes.py --log evidence/rtrp/owner-e25.log
"""

from __future__ import annotations

import argparse
import os
import http.client
import json
import subprocess
import time
import urllib.parse
from pathlib import Path

SERVER: str = "root@qmx-server"
SSH_KEY: str = str(Path.home() / ".ssh" / "qmx_server")
ADDRESS: str = "100.105.172.63"
SRC: str = "/srv/qmx/bld/rtrp/src"
NODE_LOG: str = "/srv/qmx/bld/rtrp/logs/e25-node.log"
PORT: int = 18201
UNIT: str = "rtrp-e25"
WAIT_S: float = 90.0


def log(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")
    print(line, flush=True)


def ssh(command: str) -> subprocess.CompletedProcess[str]:
    """One remote command with a hard deadline. ssh without one can wait on a channel a
    background process still holds, which is the failure that once lost this lane a run."""
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


def serve(port: int, secret: str, path: Path) -> int:
    """The node end: the tailnet app, with the pass list this lane shares."""
    import uvicorn  # noqa: PLC0415

    from qmx_router.passes import PassAuthority, RevocationList
    from qmx_router.server import NodeState, node_app  # noqa: PLC0415

    authority = PassAuthority(
        secret=bytes.fromhex(secret),
        revocations=RevocationList(path.parent / "e25-revoked.json"),
    )
    state = NodeState(site="contabo", passes=authority)
    log(path, f"node app on 0.0.0.0:{port}")
    uvicorn.run(node_app(state), host="0.0.0.0", port=port, log_level="warning")
    return 0


def ask(url: str, *, bearer: str = "", method: str = "GET", body: str = "") -> tuple[int, str]:
    """One HTTP request with its own connection and its own deadline. `http.client` and not
    `urllib`: the opener's proxy and redirect machinery adds paths that can wait past a timeout."""
    target = urllib.parse.urlsplit(url)
    connection = http.client.HTTPConnection(target.hostname or "", target.port or 80, timeout=8)
    headers = {"authorization": f"Bearer {bearer}"} if bearer else {}
    try:
        connection.request(method, target.path, body=body or None, headers=headers)
        answer = connection.getresponse()
        return answer.status, answer.read().decode("utf-8")
    finally:
        connection.close()


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
    parser = argparse.ArgumentParser(prog="e25_passes")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--secret", default="")
    parser.add_argument("--log", type=Path, default=Path("owner-e25.log"))
    args = parser.parse_args()
    path = args.log
    path.parent.mkdir(parents=True, exist_ok=True)
    if args.serve:
        return serve(args.port, args.secret or os.environ["QMX_PASS_SECRET"], path)

    from qmx_router.passes import Ask, PassAuthority

    secret = os.urandom(32)
    authority = PassAuthority(secret=secret)
    base = f"http://{ADDRESS}:{args.port}"
    ssh(f"mkdir -p {Path(NODE_LOG).parent} && rm -f {NODE_LOG}")
    log(path, f"run {time.strftime('%Y-%m-%dT%H:%M:%S')} port {args.port}")
    # A transient systemd unit, not a shell background job: ssh keeps its channel open for any
    # process that inherited it, and `setsid`/`nohup` did not release it here. systemd-run returns
    # in a second, runs the node as `prbs`, and gives the lane one word to stop it with.
    ssh(f"systemctl stop {UNIT} 2>/dev/null || true")
    started = ssh(
        f"systemd-run --collect --uid=prbs --gid=prbs --working-directory={SRC} "
        "--setenv=HOME=/srv/qmx/bld/rtrp/home "
        f"--setenv=QMX_PASS_SECRET={secret.hex()} --unit={UNIT} "
        "/srv/qmx/bld/rtrp/src/qmx-agents/.venv/bin/python "
        f"scripts/live/server/e25_passes.py --serve --port {args.port} --log {NODE_LOG}"
    )
    if "Running as unit" not in started.stdout + started.stderr:
        log(path, f"FAIL the node end did not start: {started.stdout} {started.stderr}")
        return 1
    try:
        if not wait_for_health(f"{base}/v1/health", path):
            return 1

        def mint(**over: object) -> tuple[object, str]:
            fields: dict[str, object] = {
                "run": "run-e25",
                "placement": "contabo",
                "read_scope": ("facts", "vault"),
                "write_prefix": "facts",
                "key_scope": ("qmx/openrouter",),
                "model_scope": ("claude/haiku",),
            }
            fields.update(over)
            return authority.mint(**fields)  # type: ignore[arg-type]

        minted, bearer = mint()
        status, _ = ask(f"{base}/v1/health")
        checks = []
        # Each misuse gets its own run, because an ended run ends every pass that names it.
        _, admin = mint(
            run="run-e25-admin",
            read_scope=("facts", "vault", "passes", "runs"),
            write_prefix="",
        )
        checks.append(("allowed pass reads facts", ask(f"{base}/v1/facts", bearer=bearer)[0] == 200))
        checks.append(("absent", ask(f"{base}/v1/facts")[0] == 403))
        checks.append(("malformed", ask(f"{base}/v1/facts", bearer="qmx1.nope")[0] == 403))
        other = PassAuthority(secret=os.urandom(32))
        checks.append(
            ("bad_mac", ask(f"{base}/v1/facts", bearer=other.bearer(minted))[0] == 403)
        )
        revoked_pass, revoked_bearer = mint(run="run-e25-revoked")
        ask(
            f"{base}/v1/passes",
            bearer=admin,
            method="POST",
            body=json.dumps({"revoke": revoked_pass.id}),
        )
        checks.append(("revoked", ask(f"{base}/v1/facts", bearer=revoked_bearer)[0] == 403))
        ended_pass, ended_bearer = mint(run="run-e25-ended")
        ask(
            f"{base}/v1/passes",
            bearer=admin,
            method="POST",
            body=json.dumps({"end_run": "run-e25-ended"}),
        )
        checks.append(("owner_ended", ask(f"{base}/v1/facts", bearer=ended_bearer)[0] == 403))
        _, short = mint(ttl_s=-1.0)
        checks.append(("expired", ask(f"{base}/v1/facts", bearer=short)[0] == 403))
        _, outside = mint(read_scope=("vault",))
        checks.append(("read_scope", ask(f"{base}/v1/facts", bearer=outside)[0] == 403))
        _, writer = mint()
        checks.append(
            (
                "write_scope allowed",
                ask(f"{base}/v1/facts", bearer=writer, method="POST", body='{"facts":[]}')[0]
                == 200,
            )
        )
        _, elsewhere = mint(write_prefix="runs")
        checks.append(
            (
                "write_scope refused",
                ask(f"{base}/v1/facts", bearer=elsewhere, method="POST", body='{"facts":[]}')[0]
                == 403,
            )
        )
        for name, passed in checks:
            log(path, f"{'PASS' if passed else 'FAIL'} e25 {name}")
        codes = {name for name, passed in checks if not passed}
        log(
            path,
            f"{'PASS' if not codes else 'FAIL'} e25_every_misuse_refused "
            f"({len(checks)} checks, {len(codes)} failed)",
        )
        log(path, f"health {status}")
        return 0 if not codes else 1
    finally:
        ssh(f"systemctl stop {UNIT} 2>/dev/null || true")
        tail = ssh(f"tail -n 20 {NODE_LOG}")
        if tail.stdout.strip():
            for line in tail.stdout.strip().splitlines():
                log(path, f"node: {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
