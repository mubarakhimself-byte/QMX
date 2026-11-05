"""C-14 lanes on a real host, a throwaway folder, a throwaway keyring and a fake cTrader.

Run from <worktree>/qmx-agents with its env, one at a time:
    timeout 2400 uv run --no-sync python D:/QMX-worktrees/unit-ship/evidence/c14/owner_lane_c14.py <mode> <worktree> <port>

Modes: guard (the refusal fires before any boot), refusal (real mode refuses a throwaway checkout),
bearer (the real-mode reader decodes a keyring entry, on a throwaway name outside qmx/),
rehearsal (lanes 2, 4 and 6), venuedown (lane 3), leak (lane 7).

The node is installed, proved, signed and started by the connect kind through the host's REST; the
records land through C-34's path in the kind's passport step. Two things are fixture rows, labelled
in the log: the dummy's passing G test-report and its judge's move to tested, because this lane runs
no backtest. Each check prints PASS or FAIL and the run exits non-zero on any FAIL.
"""

from __future__ import annotations

import json
import os
import select
import shutil
import socket
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, cast

MODE, WORKTREE, PORT = sys.argv[1], Path(sys.argv[2]).resolve(), int(sys.argv[3])
EVIDENCE = Path("D:/QMX-worktrees/repair-ship/tools")
KEYRING_MODULE = Path("D:/QMX-worktrees/repair-ship/tools")
SCRATCH = Path(f"D:/QMX-worktrees/repair-ship/homes/c14-{MODE}")
assert SCRATCH.as_posix().startswith("D:/QMX-worktrees/repair-ship/homes/"), SCRATCH
SCRIPT = WORKTREE / "tools" / "first_real_start.py"
KEEP = frozenset({"PYTHON_KEYRING_BACKEND", "PYTHONPATH", "C38_KEYRING_FILE", "UV_CACHE_DIR"})
STORE = SCRATCH / "keyring.json"
FAKE_VALUES = ("fake-a1", "fake-r1", "app-secret-77", "c14-sign-in-code")
LANE_S = 1500
FAILS: list[str] = []
sys.path[:0] = [str(KEYRING_MODULE), str(WORKTREE / "qmn" / "tests"), str(WORKTREE / "qmx-agents" / "packages" / "qmx-host" / "tests")]


class Log:
    def __init__(self, name: str) -> None:
        self.path = EVIDENCE / f"owner-c14-{name}.log"
        self.path.write_text("", encoding="utf-8")

    def __call__(self, line: str) -> None:
        print(line, flush=True)
        with self.path.open("a", encoding="utf-8") as out:
            out.write(line + "\n")

    def check(self, name: str, ok: bool, seen: object = "") -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name} ({seen})")
        if not ok:
            FAILS.append(name)


def refuse_unless_throwaway(settings: Path | None) -> None:
    """Stop before any host boots unless this process and the host's keep list both point at the
    throwaway keyring file. Asking which backend is chosen reads no entry."""
    import keyring  # noqa: PLC0415

    from qma.boot import read_keep_names  # noqa: PLC0415

    backend = type(keyring.get_keyring()).__name__
    if backend != "FileKeyring":
        raise SystemExit(f"FAIL this process's keyring is {backend}; no host was started")
    held = os.environ.get("C38_KEYRING_FILE", "")
    if not held.startswith(SCRATCH.as_posix()) and not Path(held).is_relative_to(SCRATCH):
        raise SystemExit(f"FAIL the keyring file {held!r} is not throwaway; no host was started")
    if settings is not None:
        kept = read_keep_names(settings)
        if not KEEP <= kept:
            raise SystemExit(f"FAIL the keep list holds only {sorted(kept)}; no host was started")


def remove(folder: Path) -> None:
    def writable(function: Any, path: str, _error: object) -> None:
        os.chmod(path, 0o700)
        function(path)

    if folder.exists():
        shutil.rmtree(folder, onexc=writable)


def throwaway_environment() -> None:
    os.environ["PYTHON_KEYRING_BACKEND"] = "owner_lane_keyring.FileKeyring"
    os.environ["C38_KEYRING_FILE"] = str(STORE)
    os.environ["PYTHONPATH"] = os.pathsep.join((str(KEYRING_MODULE), str(KEYRING_MODULE / "guard")))


class FakeOpenApi:
    """The fake cTrader on a loopback TCP port. Each connection is one session with its own
    fake, as the node's bound session and its fresh records session are at cTrader."""

    def __init__(self, make: Any) -> None:
        self.make = make
        self.fakes: list[Any] = []
        self.server = socket.create_server(("127.0.0.1", 0))
        self.port = self.server.getsockname()[1]
        self.stopping = False
        threading.Thread(target=self._serve, daemon=True).start()
        threading.Thread(target=self._quotes, daemon=True).start()

    def _serve(self) -> None:
        self.server.settimeout(0.05)
        while not self.stopping:
            try:
                peer, _ = self.server.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            threading.Thread(target=self._talk, args=(peer, self.make()), daemon=True).start()

    def _talk(self, peer: socket.socket, fake: Any) -> None:
        self.fakes.append(fake)
        buffer = b""
        peer.setblocking(False)
        try:
            while not self.stopping:
                readable, _, _ = select.select([peer], [], [], 0.01)
                if readable:
                    chunk = peer.recv(65536)
                    if not chunk:
                        return
                    buffer += chunk
                    while len(buffer) >= 4 and len(buffer) >= 4 + int.from_bytes(buffer[:4], "big"):
                        size = int.from_bytes(buffer[:4], "big")
                        fake.send(buffer[4 : 4 + size])
                        buffer = buffer[4 + size :]
                while fake._out:  # noqa: SLF001 - the lane's own fake
                    envelope = fake._out.pop(0)  # noqa: SLF001
                    peer.setblocking(True)
                    peer.sendall(len(envelope).to_bytes(4, "big") + envelope)
                    peer.setblocking(False)
        except OSError:
            return
        finally:
            self.fakes.remove(fake)
            peer.close()

    def _quotes(self) -> None:
        while not self.stopping:
            at = time.time_ns() // 1_000_000
            for fake in list(self.fakes):
                fake.quote("EURUSD", Decimal("1.08000"), Decimal("1.08012"), at)
                fake.quote("XAUUSD", Decimal("2400.00"), Decimal("2400.40"), at)
            time.sleep(0.5)

    def stop(self) -> None:
        self.stopping = True
        self.server.close()


class FakeTokens:
    def __init__(self, tokens: Any) -> None:
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:  # noqa: A002
                del format, args

            def _answer(self) -> None:
                status, body = owner.tokens(self.command, self.path)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            do_GET = _answer  # noqa: N815
            do_POST = _answer  # noqa: N815

        self.tokens = tokens
        self.http = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.http.server_address[1]
        threading.Thread(target=self.http.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self.http.shutdown()
        self.http.server_close()


class Host:
    """The real host through the lane's launcher, on the throwaway folder and keyring."""

    def __init__(self, folder: Path, log: Log) -> None:
        self.folder = folder
        self.log = log
        self.process: subprocess.Popen[bytes] | None = None
        self.launcher = str(EVIDENCE / "owner_lane_host.py")

    def bearer(self) -> str:
        return cast(str, json.loads(STORE.read_text("utf-8"))["qmx/control-token|control-token"])

    def answers(self) -> bool:
        import urllib.request  # noqa: PLC0415

        try:
            asked = urllib.request.Request(f"http://127.0.0.1:{PORT}/api/health", headers={"Authorization": f"Bearer {self.bearer()}"})
            with urllib.request.urlopen(asked, timeout=2) as said:  # noqa: S310
                return said.status == 200
        except (OSError, ValueError, KeyError):
            return False

    def start(self) -> float:
        began = time.monotonic()
        out = (SCRATCH / "serve.log").open("ab")
        self.process = subprocess.Popen(
            [sys.executable, self.launcher, "serve", "--home", str(self.folder), "--port", str(PORT)],
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=out,
        )
        self.log(f"LANE host pid {self.process.pid}")
        while time.monotonic() - began < 300:
            if self.answers():
                return time.monotonic() - began
            if self.process.poll() is not None:
                raise SystemExit("FAIL the host exited before it answered")
            time.sleep(0.5)
        raise SystemExit("FAIL the host did not answer in 300 s")

    def stop(self) -> None:
        subprocess.run(
            [sys.executable, self.launcher, "stop", "--home", str(self.folder), "--port", str(PORT)],
            capture_output=True,
            timeout=300,
            check=False,
        )
        if self.process is not None:
            try:
                self.process.wait(60)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(30)


def fixtures(home: Path, log: Log) -> None:
    """The dummy's two labelled fixture rows: no backtest runs in this lane. Written before the
    host opens the store, so the store has one writer at a time."""
    from qml.compile import CompiledUnit, compile_unit  # noqa: PLC0415
    from qmx_host.first_start import land_dummy  # noqa: PLC0415
    from qmx_host.host import LIBRARY, open_store, register_checkers  # noqa: PLC0415
    from qmx_host.lifecycle import LifecycleWriter  # noqa: PLC0415
    from qmx_judge.landing import G_CHECK, TEST_REPORT  # noqa: PLC0415
    from qmx_library.port import Draft  # noqa: PLC0415
    from qmx_library.principal import MAIN, Principal  # noqa: PLC0415
    from qmx_tools.gather import gather  # noqa: PLC0415
    from test_promote import judged  # noqa: PLC0415

    reader = Principal("operator")
    with open_store(home, home / LIBRARY, serving=False, floor=0) as store:
        register_checkers(store)
        store.lifecycle = writer = LifecycleWriter(home / "journals", "pc", "lane-fixture")
        unit = cast(str, land_dummy(store))
        document = store.get(reader, unit).fields
        compiled = compile_unit(document, gather(store, document).context)
        assert isinstance(compiled, CompiledUnit), compiled
        printed = compiled.compiled_fingerprint.value
        for market in ("fx.eurusd", "metal.xauusd"):
            judged(writer, unit, printed, market)
        fields = {
            "check": G_CHECK,
            "run_id": "qmbr-g-c14-fixture",
            "status": "finished",
            "compiled_fingerprint": printed,
            "behaviour": {},
            "safety": {"verdict": "pass"},
        }
        store.put(reader, Draft(TEST_REPORT, "qmbr-g-c14-fixture", fields=fields), on=MAIN, expected_head=None)
    log(f"FIXTURE the dummy's G report and its judge's move to tested, compiled {printed[:16]}")


def run_script(log: Log, name: str) -> tuple[int, list[str]]:
    began = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--rehearsal", "--home", str(SCRATCH / "QMX"), "--store", str(STORE), "--port", str(PORT), "--setup-s", str(LANE_S)],
        capture_output=True,
        text=True,
        timeout=LANE_S + 600,
        check=False,
        env={k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHON_KEYRING_BACKEND"}},
    )
    lines = [*done.stdout.splitlines(), *done.stderr.splitlines()]
    for line in lines:
        log(line)
    log(f"LANE {name}: script exit {done.returncode} after {time.monotonic() - began:.1f} s")
    return done.returncode, lines


def verdicts(lines: list[str]) -> dict[str, bool]:
    return {
        line[5:].split(":", 1)[0]: line.startswith("PASS ")
        for line in lines
        if line.startswith(("PASS ", "FAIL "))
    }


def scan(log: Log, roots: list[Path], extra: tuple[str, ...]) -> None:
    """Every text in `roots` for the grant, the app secret, the code and the host's bearer. The
    node's grant file and the throwaway store are where they belong and are not outputs."""
    needles = (*FAKE_VALUES, *extra)
    found: list[str] = []
    scanned = 0
    for root in roots:
        files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]
        for path in files:
            if path == STORE or path.name == "ctrader.json" or "cache" in path.parts or path.suffix in {".pyc", ".pyd", ".dll", ".exe", ".parquet", ".pb", ".zip"}:
                continue
            try:
                if path.stat().st_size > 20_000_000:
                    continue
                text = path.read_bytes().decode("utf-8", errors="replace")
            except OSError:
                continue
            scanned += 1
            found.extend(f"{path}: value {needles.index(needle)}" for needle in needles if needle in text)
    log(f"LANE scanned {scanned} files")
    log.check("no grant, secret, code or bearer in any output", found == [], found[:6])


def road_failures(name: str) -> None:
    """Every failed road step of every app on the folder, kept for the log."""
    apps = SCRATCH / "QMX" / "data" / "apps"
    with (EVIDENCE / f"owner-c14-{name}-road.log").open("w", encoding="utf-8") as out:
        for steps in sorted(apps.glob("*/road/steps.jsonl")):
            for line in steps.read_text("utf-8").splitlines():
                reference = json.loads(line)["payload"]["result_ref"]
                held = json.loads((steps.parent / reference).read_text("utf-8"))
                print(steps.parts[-3], held["stage"], f"passed={held['passed']}", held.get("duration_seconds"), file=out)
                if not held["passed"]:
                    print(json.dumps(held.get("results"))[-1500:], file=out)


def keep_outputs(name: str) -> None:
    road_failures(name)
    for held in ("host-stacks.log", "serve.log"):
        if (SCRATCH / held).is_file():
            shutil.copy(SCRATCH / held, EVIDENCE / f"owner-c14-{name}-{held}")


def prepare(log: Log) -> Path:
    remove(SCRATCH)
    SCRATCH.mkdir(parents=True)
    throwaway_environment()
    refuse_unless_throwaway(None)
    from qmx_home import resolve  # noqa: PLC0415

    folder = SCRATCH / "QMX"
    made = resolve(folder, create=True)
    settings = made.home / "settings.toml"
    settings.write_text(f"[environment]\nkeep = {json.dumps(sorted(KEEP))}\n", "utf-8")
    refuse_unless_throwaway(settings)
    log.check("the throwaway keyring guard passed before the first boot", True, STORE.name)
    STORE.write_text(
        json.dumps(
            {
                "rehearsal/app|client_id": "app-77",
                "rehearsal/app|client_secret": "app-secret-77",
                "rehearsal/code|code": "c14-sign-in-code",
            }
        ),
        "utf-8",
    )
    fixtures(made.home, log)
    return folder


def endpoints(folder: Path, port: int, token_port: int) -> None:
    venues = folder / "data" / "apps" / "trading-node" / "data" / "venues"
    venues.mkdir(parents=True)
    (venues / "endpoints.json").write_text(
        json.dumps({"host": "127.0.0.1", "port": port, "token_url": f"http://127.0.0.1:{token_port}/apps/token"}),
        "utf-8",
    )


def rehearsal() -> None:
    log = Log("rehearsal")
    folder = prepare(log)
    import test_app_binding as binding  # noqa: PLC0415
    import test_app_records as stating  # noqa: PLC0415

    codec = binding.codec()
    tokens: set[str] = {"fake-a1"}
    api = FakeOpenApi(lambda: stating.StatingCTrader(codec, tokens=tokens))
    token_endpoint = FakeTokens(binding.Tokens())
    endpoints(folder, api.port, token_endpoint.port)
    host = Host(folder, log)
    try:
        log.check("the real host answers health", True, f"{host.start():.1f} s")
        log.check("the host used the throwaway keyring", "qmx/control-token|control-token" in json.loads(STORE.read_text("utf-8")))
        code, lines = run_script(log, "lane 2")
        seen = verdicts(lines)
        log.check("lane 2: the script exits 0", code == 0, code)
        log.check("lane 2: every line reads PASS", bool(seen) and all(seen.values()), [k for k, v in seen.items() if not v])
        log.check("lane 2: eight lines", len(seen) == 8, len(seen))
        metric = [line for line in lines if line.startswith("METRIC")]
        log(f"PERF rehearsal end to end: {metric}")

        home_log = Log("home")
        code, lines = run_script(home_log, "lane 4, the same folder again, one more test trade")
        seen = verdicts(lines)
        home_log.check("lane 4: every line reads PASS on the second run", bool(seen) and all(seen.values()), [k for k, v in seen.items() if not v])
        timing = [line for line in lines if line.startswith("PASS test trade rows")]
        home_log.check("lane 4: the rows arrived inside the limit", bool(timing), timing)

        noleak = Log("noleak")
        scan(noleak, [folder, SCRATCH / "serve.log", *EVIDENCE.glob("owner-*.log")], (host.bearer(),))
        said = (SCRATCH / "serve.log").read_text("utf-8", errors="replace")
        refused = [line for line in said.splitlines() if line.startswith("LANE refused")]
        log(f"LANE outbound connections the launcher refused: {sorted(set(refused))}")
    finally:
        keep_outputs("rehearsal")
        host.stop()
        api.stop()
        token_endpoint.stop()
    said = (SCRATCH / "serve.log").read_text("utf-8", errors="replace")
    log("--- serve.log tail ---")
    for line in said.splitlines()[-12:]:
        log(line[:200])
    log.check("the host stopped", host.process is not None and host.process.poll() is not None)


def venuedown() -> None:
    log = Log("venuedown")
    folder = prepare(log)
    dead = socket.create_server(("127.0.0.1", 0))
    port = dead.getsockname()[1]
    dead.close()
    endpoints(folder, port, port)
    host = Host(folder, log)
    try:
        log.check("the real host answers health", True, f"{host.start():.1f} s")
        code, lines = run_script(log, "lane 3")
        seen = verdicts(lines)
        wanted = {
            "folder found": True,
            "practice node Ready": True,
            "demo session ready": False,
            "test trade with its stop placed, seen and closed": False,
            "passport landed": False,
            "dummy unit deployed on the chosen market": False,
            "node journal rows in This PC's store": True,
            "test trade rows in This PC's store": False,
        }
        log.check("lane 3: only the venue lines FAIL", seen == wanted, {k: v for k, v in seen.items() if wanted.get(k) != v})
        log.check("lane 3: the script exits non-zero", code != 0, code)
        one = [line for line in lines if line.startswith("FAIL ")]
        log.check("lane 3: each FAIL is one plain sentence", all(line.count(". ") == 0 for line in one), len(one))
    finally:
        keep_outputs("venuedown")
        host.stop()
    log.check("the host stopped", host.process is not None and host.process.poll() is not None)


def guard() -> None:
    """The refusal fires before any host boots, on each of the two holes."""
    log = Log("guard")
    if len(sys.argv) > 4:
        settings = None if sys.argv[4] == "backend" else Path(sys.argv[5])
        refuse_unless_throwaway(settings)
        print("NOT REFUSED")
        return
    SCRATCH.mkdir(parents=True, exist_ok=True)
    empty = SCRATCH / "settings.toml"
    empty.write_text("", "utf-8")
    own = {k: v for k, v in os.environ.items() if k not in {"PYTHON_KEYRING_BACKEND", "C38_KEYRING_FILE"}}
    no_backend = subprocess.run([sys.executable, __file__, "guard", str(WORKTREE), str(PORT), "backend"], capture_output=True, text=True, env=own, check=False)
    log.check("a process on the machine's keyring is refused", no_backend.returncode != 0 and "no host was started" in no_backend.stderr, no_backend.stderr.strip()[-120:])
    kept = {**own, "PYTHON_KEYRING_BACKEND": "owner_lane_keyring.FileKeyring", "C38_KEYRING_FILE": str(SCRATCH / "keyring.json"), "PYTHONPATH": str(KEYRING_MODULE)}
    no_keep = subprocess.run([sys.executable, __file__, "guard", str(WORKTREE), str(PORT), "keep", str(empty)], capture_output=True, text=True, env=kept, check=False)
    log.check("a keep list that drops the keyring names is refused", no_keep.returncode != 0 and "no host was started" in no_keep.stderr, no_keep.stderr.strip()[-120:])


def refusal() -> None:
    """Real mode on a throwaway clone that lacks main's commit: it refuses before any credential
    is read. `--home` is a throwaway folder, and no host runs on it."""
    log = Log("refusal")
    remove(SCRATCH)
    SCRATCH.mkdir(parents=True)
    source = SCRATCH / "source"
    source.mkdir()

    def git(*args: str, where: Path = source) -> str:
        return subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True, check=True).stdout.strip()

    def commit(message: str) -> None:
        git("add", "-A")
        git("-c", "user.name=lane", "-c", "user.email=lane@example.invalid", "commit", "-qm", message)

    git("init", "-q", "-b", "main")
    (source / "README").write_text("one\n", "utf-8")
    commit("before the script")
    (source / "tools").mkdir()
    shutil.copy(SCRIPT, source / "tools" / "first_real_start.py")
    commit("the landed script")
    origin = SCRATCH / "origin.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(source), str(origin)], check=True)
    git("remote", "add", "origin", str(origin))
    git("fetch", "-q", "origin")
    git("reset", "-q", "--hard", "HEAD~1")
    (SCRATCH / "QMX").mkdir()
    env = {k: v for k, v in os.environ.items() if k not in {"PYTHON_KEYRING_BACKEND", "C38_KEYRING_FILE"}}
    behind = subprocess.run([sys.executable, "-I", str(SCRIPT), "--home", str(SCRATCH / "QMX"), "--source", str(source), "--port", str(PORT)], capture_output=True, text=True, env=env, check=False)
    log(behind.stdout.strip())
    log.check("real mode refuses a checkout lacking main's commit", behind.returncode == 1 and behind.stdout.startswith("FAIL code landed:"), behind.returncode)
    log.check("it stopped there, with no other line", len(behind.stdout.strip().splitlines()) == 1)


def bearer() -> None:
    """The real-mode reader on a throwaway entry outside qmx/, written UTF-16 by qmn's shipped
    store, whose docstring says that is how the host's keyring writes, and as qmn's own test does
    with a throwaway name. It never names a qmx/ entry."""
    log = Log("bearer")
    from qmn.app.grants import CredentialManager  # noqa: PLC0415

    sys.path.insert(0, str(SCRIPT.parent))
    import first_real_start  # noqa: PLC0415

    target = "c14-lane-throwaway"
    entry = CredentialManager(target, encoding="utf-16-le")
    entry.write("c14-lane-value")
    try:
        log.check("credential_manager decodes a UTF-16 entry", first_real_start.credential_manager(target) == "c14-lane-value")
    finally:
        entry.delete()
    log.check("a missing entry reads None", first_real_start.credential_manager(target) is None)


def leak() -> None:
    """Lane 7: every lane log of this PR for key, token and password values."""
    log = Log("leak")
    scan(log, [p for p in EVIDENCE.glob("owner-*.log") if p.name != "owner-c14-leak.log"], ())


def main() -> int:
    began = datetime.now(UTC).isoformat()
    print(f"LANE {MODE} at {began}, worktree {WORKTREE}", flush=True)
    {"rehearsal": rehearsal, "venuedown": venuedown, "guard": guard, "refusal": refusal, "bearer": bearer, "leak": leak}[MODE]()
    if MODE not in {"guard"} or len(sys.argv) == 4:
        remove(SCRATCH)
        print(f"{'FAIL' if SCRATCH.exists() else 'PASS'} throwaway folder removed", flush=True)
    print(f"{'FAIL' if FAILS else 'PASS'} c14 {MODE} {FAILS if FAILS else ''}".rstrip(), flush=True)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
