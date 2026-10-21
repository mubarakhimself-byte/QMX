"""E63 and the cross-machine lane for TRG2b: a landing on the server fires the next app there.

Run from `qmx-agents/` with the agents venv, on the PC:

    uv run --no-sync python ../scripts/live/server/e63_chain.py --lane e63
    uv run --no-sync python ../scripts/live/server/e63_chain.py --lane cross
    uv run --no-sync python ../scripts/live/server/e63_chain.py --lane pev

One process on the server owns the store, because the Library takes one writer per root: the
worker starts the Hub's own door on a tailnet port from that store and runs the engine over the
same store, which is the only shape that works while one process holds the writer lock. The PC
never lands anything for `e63`: the macro fixture app's own `Artifacts.save` runs on the server,
the `signal-fixture` workflow is enabled there with an `event` trigger homed `contabo`, and the
chain completes while no PC process takes part. For `cross` and `pev` the PC lands artifacts in its
own store and syncs the run refs to the Hub, so the trigger fires on a row that arrived by
replication.

Writes `<TRG2B_EVIDENCE>/owner-trg2b-<lane>.log` and exits 1 when a check failed. No model, no
provider key, no ship home, no lane lock.

`pev` is the P-EV probe (the plan's first Build box): a fire within two ticks of the object reaching
the Hub, and a claim round trip under 1 s at p95, both at the default 60 s tick.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final, cast

HERE: Final = Path(__file__).resolve().parent
ROOT: Final = HERE.parents[2]
SERVER_DIR: Final = "/srv/qmx/bld/trg2b"
SERVER_HOME: Final = f"{SERVER_DIR}/home"
VENV: Final = f"{SERVER_DIR}/src/qmx-agents/.venv"
PACKAGES: Final = (
    "qmx-hub",
    "qmx-library",
    "qmx-engine",
    "qmx-apps",
)
EVIDENCE: Final = Path(
    os.environ.get("TRG2B_EVIDENCE", "D:/QMX-worktrees/qma-ship/build/evidence/trg2b")
)
HOMES: Final = Path(os.environ.get("TRG2B_HOME_ROOT", "D:/QMX-worktrees/qma-ship/build/homes"))
PREFIX: Final = os.environ.get("TRG2B_LOG_PREFIX", "owner-")
TWO_TICKS: Final = 120.0
"""P-EV's pass line: a fire within two ticks at the default 60 s tick."""
DEFAULT_TICK: Final = 60.0
FILTER: Final = {"kind": "artifact", "output": "bias", "producer": "macro-daily-bias"}
SLUGS: Final = {"e63": "trg2b-e63", "cross": "trg2b-cross", "pev": "trg2b-pev"}


def server_ssh() -> list[str]:
    """The server, over the tailnet, key only. Override with `TRG2B_SSH` (space-separated)."""
    override = os.environ.get("TRG2B_SSH")
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


def archive_head(target: str) -> None:
    """Send the PR head's committed tree to `target` as one gzipped tar, once per head."""
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is required to place the PR head on the server")
    head = subprocess.run(
        [git, "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    marker = f"{target}/.trg2b-head"
    if ssh(f"cat {marker} 2>/dev/null || true") == head:
        return
    archive = subprocess.run(
        [git, "-C", str(ROOT), "archive", "--format=tar.gz", head],
        capture_output=True,
        check=True,
        timeout=600,
    ).stdout
    result = subprocess.run(
        [
            *server_ssh(),
            f"rm -rf {target} && install -d -m 0755 {target} && tar -xzf - -C {target} "
            f"&& printf %s {head} > {marker}",
        ],
        input=archive,
        capture_output=True,
        timeout=3600,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            "the source archive did not land on the server: "
            f"{result.stderr.decode('utf-8', 'replace')[-2000:]}"
        )


def prepare_server() -> None:
    """Put the PR head under `SERVER_DIR/src` and sync the one venv the worker runs from."""
    ssh(
        f"install -d -m 0755 {SERVER_DIR} {SERVER_DIR}/home {SERVER_DIR}/uv-cache "
        f"&& chown -R prbs:prbs {SERVER_DIR}/home {SERVER_DIR}/uv-cache"
    )
    archive_head(f"{SERVER_DIR}/src")
    ssh(f"chown -R prbs:prbs {SERVER_DIR}/src")
    packages = " ".join(f"--package {name}" for name in PACKAGES)
    ssh(
        as_prbs(
            f"cd {SERVER_DIR}/src/qmx-agents && /usr/local/bin/uv sync --frozen "
            f"--python 3.14 --no-dev {packages}"
        ),
        timeout=3600,
    )


def tailnet_address() -> str:
    return ssh("tailscale ip -4 | head -1")


def start_worker(payload: Mapping[str, Any]) -> None:
    """One detached server process: the store's writer, the Hub's door and the engine."""
    lane = str(payload["lane"])
    folder = f"{SERVER_DIR}/{lane}"
    stop_worker(lane)
    ssh(f"rm -rf {folder} && install -d -m 0755 {folder} && chown -R prbs:prbs {folder}")
    script = f"{SERVER_DIR}/src/scripts/live/server/e63_chain.py"
    arguments = json.dumps(dict(payload))
    command = (
        f"cd {SERVER_DIR}/src && HOME={SERVER_HOME} UV_CACHE_DIR={SERVER_DIR}/uv-cache "
        f"exec setpriv --reuid=prbs --regid=prbs --init-groups {VENV}/bin/python {script} "
        f"--worker {json.dumps(arguments)}"
    )
    ssh(
        f"setsid nohup sh -c {json.dumps(command)} > {folder}/worker.out 2>&1 < /dev/null "
        f"& echo started"
    )


def stop_worker(lane: str) -> None:
    folder = f"{SERVER_DIR}/{lane}"
    ssh("pkill -f 'e63_chain[.]py --worker' || true")
    ssh(f"rm -rf {folder} || true")


def events_of(lane: str) -> list[dict[str, Any]]:
    text = ssh(f"cat {SERVER_DIR}/{lane}/events.jsonl 2>/dev/null || true")
    return [cast(dict[str, Any], json.loads(line)) for line in text.splitlines() if line.strip()]


def worker_out(lane: str) -> str:
    return ssh(f"cat {SERVER_DIR}/{lane}/worker.out 2>/dev/null | tail -20 || true")


def write_home(home: Path, url: str, key: str) -> None:
    (home / "vault").mkdir(parents=True, exist_ok=True)
    (home / "vault" / "pairing-key").write_text(key + "\n", encoding="utf-8")
    (home / "settings.toml").write_text(
        f'[library]\nprimary = "server"\nhub_url = "{url}"\n', encoding="utf-8"
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


def percentile(values: Sequence[float], share: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(share * (len(ordered) - 1))))
    return ordered[index]


def fixture_workflow(folder: Path) -> Path:
    """The `signal-fixture` workflow: one script that refuses a run it did not get a bias on."""
    root = folder / "signal-fixture"
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / "check.py").write_text(
        "import json\n"
        "import sys\n"
        "\n"
        "found = json.load(sys.stdin)\n"
        "event = found.get('event')\n"
        "assert event is None or event.get('output') == 'bias', f\"no bias on the signal: {found}\"\n"
        "print(json.dumps({'signal': 'ran', 'object_id': (event or {}).get('object_id')}))\n",
        encoding="utf-8",
    )
    definition = {
        "schema": "qmx.workflow/1",
        "id": "signal-fixture",
        "name": "Signal fixture: run on the macro app's bias",
        "nodes": [
            {
                "id": "start",
                "name": "Start",
                "type": "trigger",
                "typeVersion": 1,
                "parameters": {"kinds": ["manual", "event"]},
            },
            {
                "id": "check",
                "name": "Check the bias",
                "type": "script",
                "typeVersion": 1,
                "parameters": {"script": "scripts/check.py"},
            },
        ],
        "connections": {
            "Start": {"main": [[{"node": "Check the bias", "port": "in", "map": "one"}]]},
        },
    }
    (root / "definition.json").write_text(json.dumps(definition, indent=2), encoding="utf-8")
    return root


def land_bias(server: Path, library: Any, run_id: str) -> tuple[str, float]:
    """The macro fixture app's own landing path, on the server, for one bias object."""
    from qmx_apps.artifacts import Artifacts, Landing  # noqa: PLC0415
    from qmx_apps.manifest import Definition  # noqa: PLC0415

    definition = Definition.load(server / "examples/apps/macro-daily-bias")
    made: list[str] = []

    def sink(found: Landing) -> str:
        metadata = cast(dict[str, Any], found.fields["metadata"])
        landed = library.put_artifact(
            json.dumps(found.data, sort_keys=True).encode(),
            found.output,
            cast(Any, metadata),
            run_id=run_id,
            principal=f"run:{run_id}",
            intent_key=f"{run_id}:bias",
        )
        made.append(str(landed.object_id))
        return str(landed.object_id)

    store = Artifacts(server / "macro-app", library=sink)
    started = time.time()
    store.save(
        definition,
        "bias",
        {
            "bias": "bullish",
            "rationale": "the daily fixtures agree",
            "as_of": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": "macro-daily-bias",
        },
    )
    return (made[0] if made else ""), time.time() - started


def worker(payload: Mapping[str, Any]) -> int:
    """The server process: one store writer, the Hub's door beside it, and the engine over it."""
    mode = str(payload["mode"])
    folder = Path(str(payload["folder"]))
    engine_home = folder / "engine"
    (folder / "vault").mkdir(parents=True, exist_ok=True)
    events = folder / "events.jsonl"

    def emit(**entry: Any) -> None:
        line = json.dumps({**entry, "at": round(time.time(), 4)}, sort_keys=True)
        with events.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    try:
        import asyncio  # noqa: PLC0415

        from qmx_engine.control_door import set_enabled  # noqa: PLC0415
        from qmx_engine.ledger import redact  # noqa: PLC0415
        from qmx_engine.ports.library import Bundle  # noqa: PLC0415
        from qmx_engine.ports.settings import StaticSettings  # noqa: PLC0415
        from qmx_engine.service.api import EngineService  # noqa: PLC0415
        from qmx_engine.service.context import OPERATOR  # noqa: PLC0415
        from qmx_engine.settings import DEFAULTS  # noqa: PLC0415
        from qmx_engine.triggers import rows  # noqa: PLC0415
        from qmx_engine.triggers.ticker import Scheduler  # noqa: PLC0415
        from qmx_hub.server import Hub, serve  # noqa: PLC0415
        from qmx_library.adapter import EngineLibraryAdapter  # noqa: PLC0415
        from qmx_library.store import Store  # noqa: PLC0415

        key_file = folder / "vault" / "pairing-key"
        if not key_file.exists():
            key_file.write_text(secrets.token_hex(32), encoding="utf-8")
        key = key_file.read_text(encoding="utf-8").strip()
        store = Store.open(folder / "library", redactor=redact, name="server")
        library = EngineLibraryAdapter(store)
        server = serve(Hub(store), host=str(payload["host"]), port=0, key=key)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        (folder / "hub.port").write_text(str(server.server_address[1]), encoding="utf-8")
        emit(event="hub", port=server.server_address[1])

        settings = StaticSettings({**DEFAULTS, "scheduler.tick": float(payload["tick"])})
        workflow = fixture_workflow(folder)
        with EngineService.open(engine_home, library=library, settings=settings) as svc:
            item = svc.drafts.put(None, Bundle.read(workflow), 0, caller=OPERATOR).item
            asyncio.run(svc.tests.run(item, caller=OPERATOR))
            version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
            svc.versions.enable(version, caller=OPERATOR)
            now = svc.ctx.clock.now()
            trigger = rows.create(
                svc.ctx.engine.ledger,
                workflow_item=item,
                pinned_object=version,
                spec=rows.Event(dict(payload["filter"])),
                caller=OPERATOR,
                now=now,
                home_engine="contabo",
            )
            svc.ctx.engine.ledger.write(set_enabled(trigger.id, True))
            ticker = Scheduler(svc.ctx, home="contabo", credentials=set(), skills=set())
            emit(event="armed", trigger=trigger.id, tick=float(payload["tick"]))
            asyncio.run(_drive(ticker, store, library, trigger, mode, folder, payload, emit))
            fires = _fires(engine_home, trigger.id)
        server.shutdown()
        delays = [entry["delay_s"] for entry in _read(events) if entry["event"] == "done"]
        landed = len([entry for entry in _read(events) if entry["event"] == "landed"])
        replicated = len([entry for entry in _read(events) if entry["event"] == "replicated"])
        passed = bool(delays) and all(delay <= TWO_TICKS for delay in delays)
        if mode == "e63":
            passed = bool(delays) and landed >= 1
        emit(
            event="verdict",
            mode=mode,
            landed=landed,
            replicated=replicated,
            fires=len(fires),
            delays=[round(delay, 3) for delay in delays],
            pass_=passed,
        )
        return 0 if passed else 1
    except Exception as error:  # the PC reads the reason out of the events file
        emit(event="error", message=f"{type(error).__name__}: {error}")
        return 1


async def _drive(
    ticker: Any,
    store: Any,
    library: Any,
    trigger: Any,
    mode: str,
    folder: Path,
    payload: Mapping[str, Any],
    emit: Any,
) -> None:
    import asyncio  # noqa: PLC0415

    stop = asyncio.Event()
    serving = asyncio.create_task(ticker.serve(stop))
    engine = Path(str(payload["folder"])) / "engine"
    await _armed(engine, trigger.id, float(payload["tick"]))
    cursor = store.catalog.last_seq()
    replicated: dict[str, float] = {}
    reported: set[str] = set()
    expect = int(payload.get("expect", 1))
    if mode == "e63":
        run_id = f"trg2b-e63-{int(time.time())}"
        object_id, spent = land_bias(Path(str(payload["source"])), library, run_id)
        emit(event="landed", object_id=object_id, save_s=round(spent, 3))
    else:
        emit(event="watching", cursor=cursor)
    deadline = time.time() + float(payload["timeout"])
    landing_seen: dict[str, float] = {
        str(entry["object_id"]): float(entry["at"])
        for entry in _read(folder / "events.jsonl")
        if entry["event"] == "landed" and entry.get("object_id")
    }
    while time.time() < deadline:
        if mode != "e63":
            for row in store.placements(cursor):
                cursor = max(cursor, int(row["seq"]))
                if row["kind"] != "artifact" or row["new_head"] in replicated:
                    continue
                found = _object(library, str(row["new_head"]))
                if found is None or found.fields.get("type") != FILTER["output"]:
                    continue
                replicated[str(row["new_head"])] = time.time()
                emit(event="replicated", object_id=row["new_head"], seq=row["seq"])
        fires = _fires(engine, trigger.id)
        for fire in fires:
            if fire.id not in reported:
                reported.add(fire.id)
                emit(event="fire", fire_id=fire.id, status=fire.status, object_id=_object_of(fire))
        ended = [fire for fire in fires if fire.status in ("ok", "silent", "failed", "skipped")]
        for fire in ended:
            entry = _object_of(fire)
            if not entry or f"done:{fire.id}" in replicated:
                continue
            replicated[f"done:{fire.id}"] = 0.0
            started = landing_seen.get(entry) or _replicated_at(folder, entry)
            if started is None:
                continue
            emit(
                event="done",
                fire_id=fire.id,
                status=fire.status,
                object_id=entry,
                delay_s=round(time.time() - started, 3),
            )
        if (mode == "e63" and ended) or len(ended) >= expect:
            break
        await asyncio.sleep(0.1)
    stop.set()
    await serving


def _object(library: Any, object_id: str) -> Any:
    """The stored object, or None when the store does not have it yet."""
    from qmx_engine.ports.library import LibraryRefused  # noqa: PLC0415

    try:
        return library.get(object_id)
    except LibraryRefused:
        return None


async def _armed(engine: Path, trigger_id: str, tick: float) -> None:
    """Wait for the trigger's first drain, which writes its cursor: a new trigger starts at the
    log's tail, so a landing before that drain would fire nothing."""
    import asyncio  # noqa: PLC0415

    from qmx_engine.ledger.store import Reader  # noqa: PLC0415
    from qmx_engine.triggers import event  # noqa: PLC0415

    deadline = time.time() + max(10.0, tick * 2 + 5.0)
    while time.time() < deadline:
        if (engine / "engine" / "engine.sqlite").exists():
            with Reader.open(engine) as reader:
                if event.cursor_of(reader.connection, trigger_id) is not None:
                    return
        await asyncio.sleep(0.1)


def _replicated_at(folder: Path, object_id: str) -> float | None:
    for entry in _read(folder / "events.jsonl"):
        if entry["event"] == "replicated" and entry.get("object_id") == object_id:
            return float(entry["at"])
    return None


def _fires(home: Path, trigger_id: str) -> list[Any]:
    from qmx_engine.ledger.store import Reader  # noqa: PLC0415
    from qmx_engine.triggers.rows import fires  # noqa: PLC0415

    if not (home / "engine" / "engine.sqlite").exists():
        return []
    with Reader.open(home) as reader:
        return fires(reader.connection, trigger_id)


def _object_of(fire: Any) -> str:
    payload = fire.payload or {}
    found = payload.get("event") if isinstance(payload, dict) else None
    return str(found.get("object_id")) if isinstance(found, dict) else ""


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        cast(dict[str, Any], json.loads(line)) for line in path.read_text().splitlines() if line
    ]


def pc_landing(home: Path, store: Any, library: Any, index: int) -> str:
    """One landing in the PC's own store, the shape the macro app lands, minted on a run ref."""
    run_id = f"trg2b-pc-{index}-{int(time.time())}"
    made = library.put_artifact(
        json.dumps({"bias": "bullish", "index": index}).encode(),
        "bias",
        {
            "ref": {
                "producer_app": "macro-daily-bias",
                "output": "bias",
                "sha256": f"{index:064d}",
            },
            "landed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        run_id=run_id,
        principal=f"run:{run_id}",
        intent_key=f"{run_id}:bias",
    )
    return str(made.object_id)


def sync_to_hub(home: Path, store: Any) -> Any:
    from qmx_hub.replicate import StorePeer, sync  # noqa: PLC0415
    from qmx_library.client import HubClient, owners  # noqa: PLC0415

    return sync(StorePeer(store), HubClient.connect(home), owners(home))


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--worker" in args:
        return worker(cast(Mapping[str, Any], json.loads(args[args.index("--worker") + 1])))
    lane = args[args.index("--lane") + 1] if "--lane" in args else "e63"
    if lane not in SLUGS:
        print(f"known lanes are {', '.join(SLUGS)}")
        return 2
    log = Log(SLUGS[lane])
    try:
        log.say(f"lane {lane} at {time.strftime('%Y-%m-%dT%H:%M:%S')}")
        prepare_server()
        host = tailnet_address()
        tick = DEFAULT_TICK if lane == "pev" else 5.0
        expect = 10 if lane == "cross" else 1
        payload = {
            "lane": lane,
            "mode": lane,
            "host": host,
            "folder": f"{SERVER_DIR}/{lane}",
            "source": f"{SERVER_DIR}/src",
            "filter": FILTER,
            "tick": tick,
            "expect": expect,
            "timeout": 900 if lane == "e63" else 1500,
        }
        start_worker(payload)
        port = ""
        for _ in range(120):
            port = ssh(f"cat {SERVER_DIR}/{lane}/hub.port 2>/dev/null || true")
            if port:
                break
            time.sleep(0.5)
        if not port:
            log.check(False, f"the worker never wrote hub.port: {worker_out(lane)}")
            return log.close()
        url = f"http://{host}:{port}"
        key = ssh(f"cat {SERVER_DIR}/{lane}/vault/pairing-key")
        home = HOMES / f"trg2b-{lane}"
        write_home(home, url, key)
        log.check(health(url, key).get("ok") is True, f"the Hub answers at {url}")

        if lane == "pev":
            claims = claim_round_trips(url, key)
            log.say(
                f"claim round trip p50={percentile(claims, 0.5):.1f}ms "
                f"p95={percentile(claims, 0.95):.1f}ms n={len(claims)}"
            )
            log.check(percentile(claims, 0.95) < 1000.0, "a claim round trip under 1 s at p95")
        if lane in ("cross", "pev"):
            store, library = pc_store(home)
            client = hub_client(home)
            cursor = 0
            count = 10 if lane == "cross" else 1
            spaced = 6.0 if lane == "cross" else 0.0
            for index in range(count):
                object_id = pc_landing(home, store, library, index)
                done = sync_to_hub(home, store)
                log.say(
                    f"landed {object_id} and synced {len(done.pushed_refs)} refs, "
                    f"{len(done.pushed)} objects"
                )
                if done.alarms:
                    log.say(f"sync alarms: {done.alarms}")
                row = wait_for_hub_row(client, object_id, cursor)
                if row is not None:
                    cursor = max(cursor, int(row["seq"]))
                log.check(
                    row is not None and row["kind"] == "artifact",
                    f"the Hub's ref log shows {object_id} as an artifact at seq "
                    f"{0 if row is None else row['seq']}",
                )
                if spaced and index + 1 < count:
                    time.sleep(spaced)
            store.close()

        verdict = wait_for_verdict(lane, log)
        report(lane, log, verdict)
    except Exception as error:
        log.check(False, f"lane aborted: {type(error).__name__}: {error}")
        log.say(worker_out(lane))
    finally:
        stop_worker(lane)
    return log.close()


def hub_client(home: Path) -> Any:
    from qmx_library.client import HubClient  # noqa: PLC0415

    return HubClient.connect(home)


def wait_for_hub_row(
    client: Any, object_id: str, after: int, timeout: float = 10.0
) -> dict[str, Any] | None:
    """The Hub's own ref-log row for `object_id`, read through the `events` verb."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for row in cast(list[dict[str, Any]], client.call("events", after=after, limit=1000)):
            if str(row["object_id"]) == object_id:
                return row
        time.sleep(0.2)
    return None


def claim_round_trips(url: str, key: str, count: int = 20) -> list[float]:
    from qmx_library.client import HubClient  # noqa: PLC0415

    client = HubClient(url, key, "operator")
    times: list[float] = []
    for index in range(count):
        started = time.perf_counter()
        claim = client.claim(f"trg2b:pev:{index}", f"run-pev-{index}", 30)
        times.append((time.perf_counter() - started) * 1000.0)
        if claim.granted:
            client.release(f"trg2b:pev:{index}", f"run-pev-{index}")
    return times


def pc_store(home: Path) -> tuple[Any, Any]:
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_library.adapter import EngineLibraryAdapter  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415

    store = Store.open(home / "library", redactor=redact, name="pc")
    return store, EngineLibraryAdapter(store)


def wait_for_verdict(lane: str, log: Log, timeout: float = 1800.0) -> dict[str, Any]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        entries = events_of(lane)
        for entry in entries:
            if entry["event"] == "error":
                return {"event": "error", "message": entry["message"]}
            if entry["event"] == "verdict":
                return entry
        time.sleep(2.0)
    return {"event": "timeout", "seen": events_of(lane)[-3:]}


def report(lane: str, log: Log, verdict: Mapping[str, Any]) -> None:
    if verdict.get("event") == "error":
        log.check(False, f"the worker failed: {verdict.get('message')}")
        return
    if verdict.get("event") == "timeout":
        log.check(False, f"no verdict in time; last lines {verdict.get('seen')}")
        return
    delays = [float(delay) for delay in cast(list[Any], verdict["delays"])]
    log.say(
        f"landed {verdict['landed']}, replicated {verdict['replicated']}, "
        f"fires {verdict['fires']}, delays {delays}"
    )
    if lane == "e63":
        log.check(bool(delays), "the macro app's bias fired the signal fixture on Contabo")
        log.check(
            all(delay <= TWO_TICKS for delay in delays),
            f"each fire within two ticks ({max(delays, default=0.0):.1f}s <= {TWO_TICKS:.0f}s)",
        )
        return
    expected = 10 if lane == "cross" else 1
    log.check(len(delays) == expected, f"{expected} landings, {len(delays)} fires")
    log.check(
        verdict["replicated"] == expected,
        f"{verdict['replicated']} objects reached the Hub by replication",
    )
    p95 = percentile(delays, 0.95) if delays else float("inf")
    log.say(
        f"replication to fire p50={percentile(delays, 0.5):.1f}s p95={p95:.1f}s n={len(delays)}"
    )
    log.check(p95 <= TWO_TICKS, f"p95 {p95:.1f}s against two ticks {TWO_TICKS:.0f}s")
    if lane == "pev":
        log.say(f"P-EV replication_to_fire_s={delays[0] if delays else 'none'}")


if __name__ == "__main__":
    raise SystemExit(main())
