"""E67: two engines, one intent key, one build (LIB4 lane 2).

Run from `qmx-agents/` with the agents venv:

    uv run --no-sync python ../scripts/live/server/e67_claims.py

The Hub runs on the server under `/srv/qmx/bld/lib4`, from the PR head's own checkout, on an
ephemeral port. One engine runs on the PC and one on the server, started within a second of each
other, and both ask the Hub for the same claim:

- phase `live`: whichever engine reaches the claim first builds and writes its output, the other
  waits on the holder and links that output without building;
- phase `dead`: the first engine is killed while it holds the claim; the second waits one `ttl`,
  takes the claim and builds.

Writes `<LIB4_EVIDENCE>/<LIB4_LOG_PREFIX>lib4-e67.log` (default
`D:/QMX-worktrees/qma-ship/build/evidence/lib4`, prefix `owner-`) and exits 1 when a check failed.
No model, no key, no ship home, no lane lock.

The other two server lanes import this file's `prepare_server`, `start_hub` and `Log`, because a
script run from this folder puts the folder on `sys.path`.
"""

from __future__ import annotations

import json
import os
import secrets
import shlex
import shutil
import subprocess
import sys
import time
import urllib.request
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

HERE: Final = Path(__file__).resolve().parent
ROOT: Final = HERE.parents[2]
LANE: Final = "e67"
SERVER_DIR: Final = "/srv/qmx/bld/lib4"
SERVER_HOME: Final = f"{SERVER_DIR}/home"
VENV: Final = f"{SERVER_DIR}/src/qmx-agents/.venv"
KEY: Final = "fingerprint:e67:build:paper-17"
TTL: Final = 5
EVIDENCE: Final = Path(
    os.environ.get("LIB4_EVIDENCE", "D:/QMX-worktrees/qma-ship/build/evidence/lib4")
)
HOMES: Final = Path(os.environ.get("LIB4_HOME_ROOT", "D:/QMX-worktrees/qma-ship/build/homes"))
PREFIX: Final = os.environ.get("LIB4_LOG_PREFIX", "owner-")


def server_ssh() -> list[str]:
    """The server, over the tailnet, key only. Override with `LIB4_SSH` (space-separated)."""
    override = os.environ.get("LIB4_SSH")
    if override:
        return override.split()
    key = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".ssh" / "qmx_server"
    return ["ssh", "-i", str(key), "-o", "BatchMode=yes", "root@qmx-server"]


def ssh(command: str, *, timeout: int = 1800) -> str:
    result = subprocess.run(
        [*server_ssh(), command], capture_output=True, text=True, timeout=timeout, check=False
    )
    if result.returncode:
        raise RuntimeError(
            f"ssh failed ({result.returncode}): {command}\n{result.stderr.strip()[-2000:]}"
        )
    return result.stdout.strip()


def as_prbs(command: str) -> str:
    """Run one shell command as the unprivileged `prbs` user with its own home and uv cache."""
    return (
        f"runuser -u prbs -- env HOME={SERVER_HOME} UV_CACHE_DIR={SERVER_DIR}/uv-cache "
        f"sh -c {json.dumps(command)}"
    )


def rsync_up(source: Path, target: str) -> None:
    """Copy the PR head's tree to the server without its virtualenvs or git objects."""
    rsync = shutil.which("rsync")
    if rsync is None:
        raise RuntimeError("rsync is required to place the PR head on the server")
    transport = shlex.join(server_ssh()[:-1])
    result = subprocess.run(
        [
            rsync,
            "-az",
            "--delete",
            "--exclude",
            ".git",
            "--exclude",
            ".venv",
            "--exclude",
            "**/.venv",
            "--exclude",
            "**/__pycache__",
            "--exclude",
            "node_modules",
            "--exclude",
            "apps/qmx-ui",
            "-e",
            transport,
            f"{source}/",
            f"{server_ssh()[-1]}:{target}/",
        ],
        capture_output=True,
        text=True,
        timeout=3600,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"rsync failed: {result.stderr.strip()[-2000:]}")


INSTALLS: Final = (
    f"install -d -m 0755 {SERVER_DIR} {SERVER_DIR}/uv {SERVER_DIR}/home {SERVER_DIR}/uv-cache",
    "id -u prbs >/dev/null 2>&1 || useradd --system --home-dir "
    f"{SERVER_DIR}/home --shell /usr/sbin/nologin prbs",
    f"chown -R prbs:prbs {SERVER_DIR}/uv {SERVER_DIR}/home {SERVER_DIR}/uv-cache",
    f"runuser -u prbs -- env HOME={SERVER_HOME} sh -c "
    f"'test -x {SERVER_DIR}/uv/uv || (curl -LsSf https://astral.sh/uv/0.12.23/install.sh -o "
    f"{SERVER_DIR}/uv/uv-install.sh && UV_INSTALL_DIR={SERVER_DIR}/uv "
    f"sh {SERVER_DIR}/uv/uv-install.sh)'",
)
"""Every command here is recorded verbatim in `evidence/lib4/owner-installs.md`."""


def prepare_server(lane: str = LANE) -> None:
    """Install uv and Python 3.14 once, then put the PR head under `SERVER_DIR/src`."""
    if LOCAL:
        return
    for install in INSTALLS:
        ssh(install)
    rsync_up(ROOT, f"{SERVER_DIR}/src")
    ssh(
        as_prbs(
            f"cd {SERVER_DIR}/src/qmx-agents && {SERVER_DIR}/uv/uv sync --frozen --python 3.14 "
            f"--no-dev --package qmx-hub --package qmx-library"
        )
    )
    ssh(f"install -d -m 0755 {SERVER_DIR}/{lane} && chown -R prbs:prbs {SERVER_DIR}/{lane}")


LOCAL: Final = os.environ.get("LIB4_LOCAL") == "1"
"""`LIB4_LOCAL=1` rehearses the same lanes on this PC: the Hub runs here on 127.0.0.1 and both
engines are local processes. The server runs the same script without it."""
LOCAL_PROCESSES: list[subprocess.Popen[bytes]] = []


def start_hub(lane: str, *, primary: str = "server", extra: str = "") -> tuple[str, str]:
    """Start one Hub for `lane` on an ephemeral port; return its URL and its pairing key."""
    home = Path(HOMES) / f"lib4-{lane}" / "hub"
    if LOCAL:
        return _local_hub(home, primary=primary, extra=extra)
    remote = f"{SERVER_DIR}/{lane}/hub"
    address = ssh("tailscale ip -4 | head -1")
    ssh(
        as_prbs(
            f"mkdir -p {remote}/vault && chmod 700 {remote}/vault && "
            f"[ -s {remote}/vault/pairing-key ] || openssl rand -hex 32 "
            f"> {remote}/vault/pairing-key"
        )
    )
    ssh(
        f"cd {SERVER_DIR} && setsid nohup runuser -u prbs -- env HOME={SERVER_HOME} "
        f"UV_CACHE_DIR={SERVER_DIR}/uv-cache {VENV}/bin/python -m qmx_hub.server "
        f"--home {remote} --host {address} --port 0 --primary {primary} {extra} "
        f">{SERVER_DIR}/{lane}/hub.log 2>&1 < /dev/null & echo started"
    )
    port = ""
    for _ in range(60):
        port = ssh(f"cat {remote}/hub.port 2>/dev/null || true")
        if port:
            break
        time.sleep(0.5)
    if not port:
        raise RuntimeError(f"the Hub for {lane} never wrote hub.port; see {lane}/hub.log")
    key = ssh(f"cat {remote}/vault/pairing-key")
    return f"http://{address}:{port}", key


def _local_hub(home: Path, *, primary: str, extra: str = "") -> tuple[str, str]:
    """The same Hub as the server runs, on this PC, for a rehearsal or a lane without a box."""
    shutil.rmtree(home, ignore_errors=True)
    (home / "vault").mkdir(parents=True)
    key = secrets.token_hex(32)
    (home / "vault" / "pairing-key").write_text(key, encoding="utf-8")
    arguments = ["--home", str(home), "--host", "127.0.0.1", "--port", "0", "--primary", primary]
    arguments.extend(extra.split()) if extra else None
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            f"from qmx_hub.server import main; raise SystemExit(main({arguments!r}))",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    LOCAL_PROCESSES.append(process)
    port_file = home / "hub.port"
    for _ in range(60):
        if port_file.exists():
            return f"http://127.0.0.1:{port_file.read_text(encoding='utf-8').strip()}", key
        time.sleep(0.25)
    raise RuntimeError(f"the local Hub never wrote {port_file}")


def stop_hub(lane: str) -> None:
    if LOCAL:
        for process in LOCAL_PROCESSES:
            process.terminate()
            process.wait(timeout=10)
        LOCAL_PROCESSES.clear()
        return
    ssh(f"pkill -f 'qmx_hub.server --home {SERVER_DIR}/{lane}/hub' || true")


def write_home(home: Path, url: str, key: str, *, primary: str = "server") -> None:
    (home / "vault").mkdir(parents=True, exist_ok=True)
    (home / "vault" / "pairing-key").write_text(key + "\n", encoding="utf-8")
    (home / "settings.toml").write_text(
        f'[library]\nprimary = "{primary}"\nhub_url = "{url}"\n', encoding="utf-8"
    )


def health(url: str, key: str) -> dict[str, Any]:
    request = urllib.request.Request(  # noqa: S310 (the lane's own URL)
        f"{url}/healthz", headers={"Authorization": f"Bearer {key}"}
    )
    with urllib.request.urlopen(request, timeout=10) as answer:  # noqa: S310
        return dict(json.loads(answer.read()))


class Log:
    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{PREFIX}{slug}.log"
        self.lines: list[str] = []
        self.failed = False

    def say(self, line: str) -> None:
        print(line, flush=True)
        self.lines.append(line)

    def check(self, ok: bool, line: str) -> None:
        self.say(("PASS " if ok else "FAIL ") + line)
        self.failed = self.failed or not ok

    def close(self) -> int:
        self.path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        return 1 if self.failed else 0


def engine(hub_url: str, key: str, run_id: str, *, hold: float) -> int:
    """One engine: claim, then build, or wait and link, or take the claim after it lapses."""
    from qmx_library.client import HubClient  # noqa: PLC0415
    from qmx_library.port import Draft  # noqa: PLC0415

    client = HubClient(hub_url, key, f"run:{run_id}")
    claim = client.claim(KEY, run_id, TTL)
    answer: dict[str, Any] = {
        "run": run_id,
        "first_claim_granted": claim.granted,
        "held_by": claim.run_id,
        "held_until": None if claim.expires is None else claim.expires.isoformat(),
    }
    if claim.granted and hold:
        answer["action"] = "holding"
        print(json.dumps(answer), flush=True)
        time.sleep(hold)
        return 0
    if claim.granted:
        built = _build(client, run_id, answer, Draft)
        print(json.dumps(built), flush=True)
        return 0
    holder = claim.run_id
    linked = None
    until = time.time() + 4
    while time.time() < until and linked is None:
        linked = _linked(client, holder)
        time.sleep(0.25)
    if linked is not None:
        client.release(KEY, run_id)
        answer["action"] = "waited and linked"
        answer["linked"] = linked
        print(json.dumps(answer), flush=True)
        return 0
    taken = None
    until = time.time() + TTL + 15
    while time.time() < until:
        taken = client.claim(KEY, run_id, TTL)
        if taken.granted:
            break
        time.sleep(0.25)
    if taken is None or not taken.granted:
        answer["action"] = "the claim never lapsed"
        print(json.dumps(answer), flush=True)
        return 1
    built = _build(client, run_id, answer, Draft)
    built["action"] = "built after the holder died"
    print(json.dumps(built), flush=True)
    return 0


def _build(client: Any, run_id: str, answer: dict[str, Any], draft_type: Any) -> dict[str, Any]:
    time.sleep(2.0)
    output = client.put(
        draft_type("note", run_id, title=f"built by {run_id}"),
        on=f"refs/runs/{run_id}",
        expected_head=None,
    )
    client.release(KEY, run_id)
    answer["action"] = "built"
    answer["output"] = output.object_id
    answer["built_at"] = round(time.time(), 3)
    return answer


def _linked(client: Any, holder: str | None) -> str | None:
    if holder is None:
        return None
    try:
        head = client.call("head", item=holder, ref=f"refs/runs/{holder}")
    except Exception:
        return None
    return None if head is None else str(head)


def engine_on_server(lane: str, hub_url: str, key: str, run_id: str, *, hold: float) -> Any:
    """The same engine on the server, in the lane's venv; its one JSON line returns on stdout."""
    if LOCAL:
        return engine_locally(hub_url, key, run_id, hold=hold)
    payload = shlex.quote(json.dumps([hub_url, key, run_id, hold]))
    command = (
        f"cd {SERVER_DIR}/src && LIB4_ENGINE={payload} "
        f"{VENV}/bin/python {SERVER_DIR}/src/scripts/live/server/e67_claims.py --engine"
    )
    return subprocess.Popen(
        [*server_ssh(), command], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )


def engine_locally(hub_url: str, key: str, run_id: str, *, hold: float) -> Any:
    return subprocess.Popen(
        [sys.executable, __file__, "--engine"],
        env={**os.environ, "LIB4_ENGINE": json.dumps([hub_url, key, run_id, hold])},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def answer_of(process: Any) -> dict[str, Any]:
    out, err = process.communicate(timeout=180)
    text = out.decode("utf-8", "replace").strip().splitlines()
    if not text:
        raise RuntimeError(f"the engine said nothing: {err.decode('utf-8', 'replace')[-1000:]}")
    return dict(json.loads(text[-1]))


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--engine" in args:
        payload = json.loads(os.environ["LIB4_ENGINE"])
        return engine(payload[0], payload[1], payload[2], hold=float(payload[3]))
    log = Log("lib4-e67")
    hub_url = ""
    try:
        log.say(f"lane e67 at {time.strftime('%Y-%m-%dT%H:%M:%S')}")
        prepare_server(LANE)
        hub_url, key = start_hub(LANE)
        write_home(HOMES / f"lib4-{LANE}", hub_url, key)
        log.check(health(hub_url, key).get("ok") is True, f"hub answers at {hub_url}")

        first, second = "e67-a-live", "e67-b-live"
        started = time.time()
        a = engine_locally(hub_url, key, first, hold=0)
        started_b = time.time()
        b = engine_on_server(LANE, hub_url, key, second, hold=0)
        live_a, live_b = answer_of(a), answer_of(b)
        log.check(
            abs(started_b - started) < 1.0,
            f"both engines started within one second ({started_b - started:.3f}s)",
        )
        claimed = [answer for answer in (live_a, live_b) if answer["first_claim_granted"]]
        log.check(
            len(claimed) == 1,
            f"exactly one engine took the claim ({claimed[0]['run'] if claimed else 'none'})",
        )
        if len(claimed) == 1:
            winner = claimed[0]
            loser = live_b if winner["run"] == live_a["run"] else live_a
            log.check(
                loser["held_by"] == winner["run"],
                f"{loser['run']} was refused and told the holder is {loser['held_by']}",
            )
            log.check(winner.get("action") == "built", f"{winner['run']} built the paper")
            log.check(
                loser.get("action") == "waited and linked"
                and loser.get("linked") == winner.get("output"),
                f"{loser['run']} linked {winner['run']}'s output and built nothing",
            )

        killed, taker = "e67-a-dead", "e67-b-dead"
        held = engine_locally(hub_url, key, killed, hold=60)
        if held.stdout is None:
            raise RuntimeError("the killed engine has no stdout to read")
        # The holder says it holds before it sleeps; wait for that line, so the kill below lands on
        # a claim that already exists rather than on a process still importing.
        held_line = held.stdout.readline()
        if not held_line:
            raise RuntimeError("the killed engine never said it held the claim")
        dead_a = dict(json.loads(held_line))
        started_taker = time.time()
        waiting = engine_on_server(LANE, hub_url, key, taker, hold=0)
        # Long enough for the taker to reach the Hub and be refused while the holder still lives.
        time.sleep(3.0)
        held.kill()
        held.communicate(timeout=10)
        dead_b = answer_of(waiting)
        waited = time.time() - started_taker
        log.check(dead_a.get("action") == "holding", "the killed engine held the claim")
        log.check(
            dead_b["first_claim_granted"] is False and dead_b.get("held_by") == killed,
            f"{taker} was refused and told the holder is {dead_b.get('held_by')}",
        )
        log.check(
            str(dead_b.get("action", "")).startswith("built"),
            "after one ttl the second engine took the claim and built the paper",
        )
        log.check(waited >= TTL, f"the second waited at least one ttl ({waited:.1f}s >= {TTL}s)")
    except Exception as error:
        log.check(False, f"lane aborted: {error}")
    finally:
        if hub_url:
            stop_hub(LANE)
    return log.close()


if __name__ == "__main__":
    raise SystemExit(main())
