"""The deep-logs kinds of the connect dialog (design 06 section 9): OpenObserve, self-hosted, one
per person, on this PC or on his server.

On this PC QMX gets OpenObserve (on PATH, or the pinned release fetched into `cache/openobserve/`
and checked against its published sha256), makes its root password and an ingest credential in
the key store, sets `[telemetry] send_to = "this-pc"`, and runs it under the host on
`127.0.0.1:5080`, the address every sender already posts to, with its own telemetry off, the disk
cache and the days kept from `[telemetry.openobserve]`, and its data under `cache/openobserve/`,
which is rebuildable and never synced. No collector runs on this PC. The ingest credential is the
header every sender adds; the agent login is the one agents use at its MCP door.

On his server the step installs the shipped unit files and the collector with its on-disk queue,
with a password the server makes for itself, and points `send_to` at that server.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import io
import os
import platform
import secrets
import shutil
import subprocess
import tarfile
import threading
import time
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, cast

import httpx
import psutil
from qma.telemetry import INGEST_KEY, THIS_PC
from qmx_broker.credentials import KeyStore
from qmx_home import Layout
from qmx_home.files import plain

from qmx_host.connect import Card, Kind, Run, Step
from qmx_host.connect_compute import server_of, server_row
from qmx_host.jobs import Stopped

ROOT_KEY: Final = "qmx/openobserve-root"
AGENT_KEY: Final = "qmx/openobserve-agent"
ROOT_EMAIL: Final = "qmx@this-pc.invalid"
"""OpenObserve's root sign-in is an email; this one names this PC and reaches nobody."""
PORT: Final = 5080
LOOPBACK: Final = "127.0.0.1"
MCP: Final = f"http://{LOOPBACK}:{PORT}/api/default/mcp"
START_WAIT_S: Final = 60.0
"""How long one start may take to answer its health before the job says it did not; a bound on
one start, not a limit on him."""
DENIED: Final = ("access is denied", "permission denied", "os error 5", "requires elevation")
DEPLOY: Final = Path(__file__).resolve().parents[2] / "deploy"
"""The unit files `qmx-host` ships for a server (`openobserve.service`, `otelcol.service`,
`otelcol.yaml`), in the source tree the server setup sends."""


@dataclass(frozen=True, slots=True)
class Pinned:
    """One pinned OpenObserve release for one system: where it is, how big, its published
    sha256 (None until one is recorded, and nothing unchecked is run), and the program in it."""

    version: str
    edition: str
    url: str
    size: int
    sha256: str | None
    program: str


RELEASES: Final[Mapping[str, Pinned]] = {
    "windows-amd64": Pinned(
        "v1.1.2",
        "open source (AGPL-3.0)",
        "https://downloads.openobserve.ai/releases/openobserve/v1.1.2/"
        "openobserve-v1.1.2-windows-amd64.zip",
        150_297_501,
        None,
        "openobserve.exe",
    ),
}
"""The open-source edition, the one with no licence to accept and no ingest limit of its own. Its
size is the download server's answer (`research/sync/sources/openobserve-windows-binaries-head
.md`); the page lists the sha256 behind a button no saved copy holds, so it is recorded at the
program's arm step and a fetch refuses until then."""


def system() -> str:
    machine = platform.machine().lower()
    return f"{platform.system().lower()}-{'amd64' if machine in ('amd64', 'x86_64') else machine}"


def download(url: str, target: Path) -> None:
    with httpx.stream("GET", url, follow_redirects=True, timeout=60) as answer:
        answer.raise_for_status()
        with target.open("wb") as out:
            for chunk in answer.iter_bytes(1 << 20):
                out.write(chunk)


class NeedsAdmin(Exception):
    """OpenObserve did not start as this user; `why` is what Windows or the program said."""

    def __init__(self, why: str) -> None:
        super().__init__(why)
        self.why = why


class OpenObserveProcess:
    """OpenObserve on this PC, started and stopped by the host. Its sign-in reaches it by
    environment only, and it binds the loopback alone."""

    def __init__(
        self,
        layout: Layout,
        keys: KeyStore,
        settings: Callable[[], Mapping[str, object]],
        *,
        port: int = PORT,
        program: str | None = None,
    ) -> None:
        self.layout = layout
        self.keys = keys
        self.settings = settings
        self.port = port
        self.program = program
        self._child: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()
        self._closed = False

    @property
    def folder(self) -> Path:
        return self.layout.cache / "openobserve"

    @property
    def record(self) -> Path:
        """The pid and start time of the OpenObserve QMX started, so a host that comes back after
        a crash stops that one and no other."""
        return self.folder / "openobserve.pid"

    def _recorded(self) -> psutil.Process | None:
        try:
            pid, started = self.record.read_text(encoding="utf-8").split()
            found = psutil.Process(int(pid))
            return found if f"{found.create_time():.3f}" == started else None
        except OSError, ValueError, psutil.Error:
            return None

    def ours(self) -> bool:
        """It answers, and it is the one QMX started."""
        return self.healthy() and self._recorded() is not None

    def binary(self) -> Path | None:
        """OpenObserve on PATH, or the one fetched into `cache/openobserve/`."""
        found = shutil.which(self.program or "openobserve")
        if found is not None:
            return Path(found)
        pinned = RELEASES.get(system())
        fetched = self.folder / (pinned.program if pinned else "openobserve")
        return fetched if fetched.is_file() else None

    def healthy(self) -> bool:
        try:
            answer = httpx.get(f"http://{LOOPBACK}:{self.port}/healthz", timeout=2)
        except httpx.HTTPError:
            return False
        return answer.status_code == 200

    def environment(self) -> dict[str, str]:
        sizes = self.settings().get("openobserve")
        given = cast("dict[str, object]", sizes) if isinstance(sizes, dict) else {}
        cache_gb = float(cast("float", given.get("cache_gb", 1)))
        password = self.keys.read(ROOT_KEY)
        if not password:
            raise Stopped("OpenObserve on this PC has no sign-in yet; connect deep logs again")
        return {
            "ZO_ROOT_USER_EMAIL": ROOT_EMAIL,
            "ZO_ROOT_USER_PASSWORD": password,
            "ZO_DATA_DIR": str(self.folder / "data"),
            "ZO_LOCAL_MODE": "true",
            "ZO_HTTP_ADDR": LOOPBACK,
            "ZO_HTTP_PORT": str(self.port),
            "ZO_GRPC_ADDR": LOOPBACK,
            "ZO_TELEMETRY": "false",
            "ZO_DISK_CACHE_MAX_SIZE": str(round(cache_gb * 1024)),
            "ZO_COMPACT_DATA_RETENTION_DAYS": str(given.get("keep_days", 30)),
        }

    def start(self) -> str:
        """Start it, or find it running, and wait for its health. Raises NeedsAdmin when it
        would not start as this user, and Stopped with one line for anything else."""
        with self._lock:
            if self._closed:
                raise Stopped("the host is stopping, so OpenObserve was not started")
            if self.healthy():
                if self._recorded() is None:
                    raise Stopped(
                        f"another program answers on http://{LOOPBACK}:{self.port}, where QMX "
                        "runs OpenObserve; stop it, then connect deep logs again"
                    )
                return f"OpenObserve answers on http://{LOOPBACK}:{self.port}"
            program = self.binary()
            if program is None:
                raise Stopped("OpenObserve is not on this PC yet; connect deep logs again")
            self.folder.mkdir(parents=True, exist_ok=True)
            log = self.layout.logs / "openobserve.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            began = time.perf_counter()
            try:
                with log.open("ab") as out:
                    self._child = subprocess.Popen(
                        [str(program)],
                        cwd=self.folder,
                        env={**os.environ, **self.environment()},
                        stdout=out,
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL,
                    )
            except OSError as error:
                if getattr(error, "winerror", None) in (5, 740) or error.errno == 13:
                    raise NeedsAdmin(f"Windows said: {error.strerror}") from None
                raise Stopped(f"OpenObserve did not start: {error.strerror}") from None
            child = self._child
            with contextlib.suppress(psutil.Error):
                started = psutil.Process(child.pid).create_time()
                self.record.write_text(f"{child.pid} {started:.3f}\n", encoding="utf-8")
        while time.perf_counter() - began < START_WAIT_S:
            if self.healthy():
                return (
                    f"OpenObserve answers on http://{LOOPBACK}:{self.port} after "
                    f"{time.perf_counter() - began:.1f} s"
                )
            code = child.poll()
            if code is not None:
                said = log.read_text(encoding="utf-8", errors="replace")[-2000:]
                if code == 5 or any(word in said.casefold() for word in DENIED):
                    raise NeedsAdmin(f"it ended with code {code} and said access is denied")
                raise Stopped(
                    f"OpenObserve stopped as it started (code {code}); its log is {plain(log)}"
                )
            time.sleep(0.2)
        self.stop()
        raise Stopped(
            f"OpenObserve did not answer within {START_WAIT_S:.0f} s; its log is {plain(log)}"
        )

    def close(self) -> None:
        """The host's stop: no start after it, then the stop."""
        with self._lock:
            self._closed = True
        self.stop()

    def stop(self) -> None:
        """Stop the OpenObserve QMX started, this host's child or one a crashed host left, with
        every process it started. Safe to call when nothing runs."""
        with self._lock:
            child, self._child = self._child, None
            parent = self._recorded()
            self.record.unlink(missing_ok=True)
        tree: list[psutil.Process] = []
        with contextlib.suppress(psutil.Error):
            if parent is None and child is not None and child.poll() is None:
                parent = psutil.Process(child.pid)
            if parent is not None:
                tree = [*parent.children(recursive=True), parent]
        for one in tree:
            with contextlib.suppress(psutil.Error):
                one.terminate()
        _gone, alive = psutil.wait_procs(tree, timeout=10)
        for one in alive:
            with contextlib.suppress(psutil.Error):
                one.kill()
        if child is not None:
            with contextlib.suppress(subprocess.TimeoutExpired):
                child.wait(10)


@dataclass(frozen=True, slots=True)
class Logs:
    """What the deep-logs kinds reach: the host's OpenObserve, the release pinned for this system,
    and how a release is fetched. Tests and lanes pass a stand-in release and a loopback server."""

    process: OpenObserveProcess | None = None
    release: Pinned | None = field(default_factory=lambda: RELEASES.get(system()))
    get: Callable[[str, Path], None] = download


def logs_of(run: Run) -> Logs:
    found = run.world.logs
    if found is None or found.process is None:
        raise Stopped("deep logs are connected from a running QMX, not the card")
    return found


def _process(run: Run) -> OpenObserveProcess:
    process = logs_of(run).process
    assert process is not None  # noqa: S101 - logs_of refused a world with none
    return process


def _found(run: Run) -> bool:
    found = _process(run).binary()
    if found is not None:
        run.say(f"deep logs: OpenObserve is at {plain(found)}")
    return found is not None


def _fetch(run: Run) -> Card | None:
    """The pinned release into `cache/openobserve/`, checked against its sha256 before anything
    in it is unpacked; a wrong one is deleted, never run."""
    logs = logs_of(run)
    pinned = logs.release
    if pinned is None:
        raise Stopped(
            f"QMX has no pinned OpenObserve for {system()}; put openobserve on PATH, then "
            "connect deep logs again"
        )
    if pinned.sha256 is None:
        raise Stopped(
            f"the pinned OpenObserve {pinned.version} has no published checksum recorded yet, so "
            "QMX will not run a download it cannot check; put openobserve on PATH, then connect "
            "deep logs again"
        )
    folder = _process(run).folder
    folder.mkdir(parents=True, exist_ok=True)
    part = folder / f"{pinned.version}.part"
    try:
        logs.get(pinned.url, part)
    except OSError, httpx.HTTPError:
        part.unlink(missing_ok=True)
        raise Stopped(
            f"OpenObserve {pinned.version} could not be fetched; check this PC is online, then "
            "connect deep logs again"
        ) from None
    body = part.read_bytes()
    part.unlink()
    if hashlib.sha256(body).hexdigest() != pinned.sha256:
        raise Stopped(
            f"the OpenObserve {pinned.version} QMX fetched is not the one pinned (its checksum "
            "differs), so it was deleted and not run; try again later"
        )
    program = _member(body, pinned.program)
    if program is None:
        raise Stopped(
            f"the OpenObserve {pinned.version} release holds no {pinned.program}; put openobserve "
            "on PATH, then connect deep logs again"
        )
    (folder / pinned.program).write_bytes(program)
    run.say(f"deep logs: OpenObserve {pinned.version} fetched and checked into {plain(folder)}")
    return None


def _member(archive: bytes, name: str) -> bytes | None:
    if archive[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
            found = next((i for i in zipped.namelist() if Path(i).name == name), None)
            return None if found is None else zipped.read(found)
    with tarfile.open(fileobj=io.BytesIO(archive)) as packed:
        member = next((m for m in packed.getmembers() if Path(m.name).name == name), None)
        handle = None if member is None else packed.extractfile(member)
        return None if handle is None else handle.read()


def _signed(run: Run) -> bool:
    keys = run.world.keys
    return all(keys.read(name) for name in (ROOT_KEY, INGEST_KEY, AGENT_KEY))


def _sign_in(run: Run) -> Card | None:
    """Its root password, made here and never shown, and the header that signs in with it. On
    the open-source edition every login has full rights (no roles), so the agent login is the
    same sign-in under its own name."""
    keys = run.world.keys
    password = keys.read(ROOT_KEY) or secrets.token_urlsafe(24)
    header = "Basic " + base64.b64encode(f"{ROOT_EMAIL}:{password}".encode()).decode("ascii")
    keys.replace(ROOT_KEY, password)
    keys.replace(INGEST_KEY, header)
    keys.replace(AGENT_KEY, header)
    run.say(f"deep logs: its sign-in is in Credential Manager as {ROOT_KEY} and {INGEST_KEY}")
    return None


def _sending_to(target: str) -> Callable[[Run], bool]:
    def check(run: Run) -> bool:
        control = run.world.control
        return (
            control is not None
            and control.settings_get(cast("Any", "telemetry")).get("send_to") == target
        )

    return check


def _send_to(target: Callable[[Run], str]) -> Callable[[Run], Card | None]:
    def do(run: Run) -> Card | None:
        control = run.world.control
        if control is None:
            raise Stopped("deep logs are connected from a running QMX, not the card")
        chosen = target(run)
        control.settings_update(
            cast("Any", "telemetry"), lambda section: {**section, "send_to": chosen}
        )
        run.say(f"deep logs: QMX sends its traces, metrics and logs to {chosen}")
        return None

    return do


def _answering(run: Run) -> bool:
    return _process(run).ours()


def _start(run: Run) -> Card | None:
    try:
        run.say(f"deep logs: {_process(run).start()}")
    except NeedsAdmin as needs:
        _process(run).stop()
        return Card(
            "approval",
            f"deep logs: OpenObserve would not start as you on this PC ({needs.why}), and QMX "
            "does not give it administrator rights; answering here will not either. To keep deep "
            "logs on this PC, close QMX, start it again as administrator and connect deep logs "
            "again. Or connect deep logs on your server instead. Nothing is left running",
            ({"Name": "again", "Help": "yes, to try once more", "Examples": [], "Type": "string"},),
        )
    return None


def _door(run: Run) -> Card | None:
    run.say(f"deep logs: agents read them at {MCP} with the key {AGENT_KEY}")
    return None


def _never(_run: Run) -> bool:
    return False


ON_THIS_PC: Final = Kind(
    "deep-logs-pc",
    "Deep logs on this PC",
    (),
    False,
    (
        Step("openobserve", "qmx", _found, _fetch),
        Step("sign-in", "qmx", _signed, _sign_in),
        Step("start", "his", _answering, _start),
        Step("send-to", "qmx", _sending_to(THIS_PC), _send_to(lambda _run: THIS_PC)),
        Step("agent-door", "qmx", _never, _door),
    ),
)


# On his server.


def _the_server(run: Run) -> bool:
    if server_row(run) is None:
        raise Stopped(f"{run.place}: connect {run.place} as your server first, then its deep logs")
    return True


def _monitoring_on(run: Run) -> bool:
    try:
        shown = server_of(run).send("systemctl is-active openobserve otelcol || true")
    except RuntimeError:
        return False
    return shown.split() == ["active", "active"]


def monitoring_script() -> str:
    """Install OpenObserve and the collector as the server's services, from the unit files QMX
    ships, with a sign-in the server makes for itself and keeps in root-only files."""
    files = {
        "/etc/systemd/system/openobserve.service": "openobserve.service",
        "/etc/systemd/system/otelcol.service": "otelcol.service",
        "/etc/qmx/otelcol.yaml": "otelcol.yaml",
    }
    written = "".join(
        f"cat > {target} <<'QMXFILE'\n{(DEPLOY / name).read_text(encoding='utf-8')}QMXFILE\n"
        for target, name in files.items()
    )
    email = "qmx-observer@this-server.invalid"
    return (
        "set -eu\n"
        "for program in /usr/local/bin/openobserve /usr/local/bin/otelcol-contrib; do\n"
        '  [ -x "$program" ] || { echo "$program is not installed" >&2; exit 3; }\n'
        "done\n"
        "install -d -o qmx -g qmx -m 0700 /srv/qmx/monitoring/openobserve "
        "/srv/qmx/monitoring/otelcol /srv/qmx/monitoring/otelcol/queue\n"
        "install -d -m 0755 /etc/qmx\n"
        f"{written}"
        "umask 077\n"
        "if [ ! -s /etc/qmx/openobserve.env ]; then\n"
        '  password="$(openssl rand -base64 24)"\n'
        f"  printf 'ZO_ROOT_USER_EMAIL={email}\\nZO_ROOT_USER_PASSWORD=%s\\n' \"$password\" "
        "> /etc/qmx/openobserve.env\n"
        f"  printf 'OO_AUTH=Basic %s\\n' \"$(printf '{email}:%s' \"$password\" | base64 -w0)\" "
        "> /etc/qmx/otelcol.env\n"
        "fi\n"
        "chmod 0600 /etc/qmx/openobserve.env /etc/qmx/otelcol.env\n"
        "systemctl daemon-reload\n"
        "systemctl enable --now openobserve otelcol\n"
    )


def _monitor(run: Run) -> Card | None:
    try:
        server_of(run).send("sudo bash -s", monitoring_script())
    except RuntimeError:
        raise Stopped(
            f"{run.place}: the server has no OpenObserve or collector program in /usr/local/bin "
            "yet, or one did not start; install them there, then connect its deep logs again"
        ) from None
    run.say(f"{run.place}: OpenObserve and its collector run there, with an on-disk queue")
    return None


def _nothing(_run: Run) -> Card | None:
    return None


def _sent_to_it(run: Run) -> bool:
    return _sending_to(run.place)(run)


def _its_name(run: Run) -> str:
    return run.place


ON_A_SERVER: Final = Kind(
    "deep-logs-server",
    "Deep logs on your server",
    (),
    False,
    (
        Step("server", "qmx", _the_server, _nothing),
        Step("monitoring", "qmx", _monitoring_on, _monitor),
        Step("send-to", "qmx", _sent_to_it, _send_to(_its_name)),
    ),
)

DEEP_LOGS: Final = (ON_THIS_PC, ON_A_SERVER)
"""The deep-logs kinds, in the order the dialog offers them."""
