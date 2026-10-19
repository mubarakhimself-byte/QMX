"""LIBM's live lanes: MIGRATION steps 0 to 5 on copies of the operator's home.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/library/libm_lanes.py [lane ...]`
Lanes are `regression import dual diff alias collision real secrets processes`; none named runs
`import dual diff`. Each writes `<LIBM_EVIDENCE>/<LIBM_LOG_PREFIX>libm-<lane>.log` (default
`D:/QMX-worktrees/qma-ship/build/evidence/libm`, prefix `owner-` for the builder, `check-` for
the coordinator) and the script exits 1 if any lane failed. No model, no key, no ship home, no
lane lock. The operator's home (`LIBM_REAL_HOME`, default `~/.qmx`) is only ever copied: every
lane runs on a copy under `D:/QMX-worktrees/qma-ship/build/homes/libm-<lane>`, and `real` hashes
his `library.db` and blobs against the hashes `import` recorded before it copied them.

His home holds no registry room and no app artifacts, so `import` adds both to the copy as named
fixtures: three registry records read through QMB's real as-of port, and one app artifact with
its definition folder.

- `regression` (lane 1): the `qmx-library` and `qmx-control` suites at the parent
  (`LIBM_PARENT`, a detached worktree under `D:/Temp/libm-parent`) and at this checkout; head
  fails nothing the parent passes.
- `import` (lanes 2 and 8): steps 0 to 4 into the dry store; `verify` prints step 0's counts
  beside the store's, equal, with every blob hash checked; the import time per 1,000 items.
- `dual` (lane 3): `library_save` on the copy with the dual write attached; both stores hold it.
- `diff` (lane 4): `lib-dual-run-diff` test-run by the engine on the copy's store; it passes and
  the store holds its `test-report`; then one save made without the mirror turns the diff unclean.
- `alias` (lane 5): an old `artifacts/<sha>` ref resolves to the imported object.
- `collision` (lane 6): an fp1 planted with other content stops the registry import with an alarm.
- `real` (lane 7): his `library.db` and blobs hash as they did before the lanes.
- `secrets` (lane 9), `processes` (lane 10).
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Final, TypeVar

import psutil
from qmb.registryread import AsOfSet, DatedPointer, PassiveHub, RegistryReadPort, SupersedesRef
from qmf.core.chrono import Instant, WriterId
from qmf.core.refusal import Result, is_ok
from qmf.registry import RegistrationRecord
from qmx_control.service import ControlService, LibraryInput
from qmx_engine.ledger import redact
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR as CALLER
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.migrate import OPERATOR, MigrationAlarm, open_target, pre
from qmx_library.migrate.from_apps import import_apps
from qmx_library.migrate.from_library_b import DualWrite, import_library_b, resolve_alias
from qmx_library.migrate.from_registry import import_registry
from qmx_library.migrate.snapshot import snapshot
from qmx_library.migrate.verify import verify
from qmx_library.store import Store

BUILD: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = Path(os.environ.get("LIBM_EVIDENCE", str(BUILD / "evidence" / "libm")))
PREFIX: Final = os.environ.get("LIBM_LOG_PREFIX", "owner-")
REAL: Final = Path(os.environ.get("LIBM_REAL_HOME", str(Path.home() / ".qmx")))
PARENT: Final = os.environ.get("LIBM_PARENT", "74b783f8fe152c9b71f5356c7dcee3c625a4e476")
ROOT: Final = Path(__file__).resolve().parents[3]
LIB: Final = ROOT / "qmx-agents" / "packages" / "qmx-library"
TEMPLATE: Final = LIB / "src" / "qmx_library" / "migrate" / "lib-dual-run-diff"
LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
HASHES: Final = EVIDENCE / f"{PREFIX}libm-real-before.json"
SUITES: Final = ("qmx-library", "qmx-control")
UV: Final = shutil.which("uv") or "uv"
GIT: Final = shutil.which("git") or "git"
T = TypeVar("T")


class Log:
    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{PREFIX}libm-{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= ok

    def verdict(self) -> bool:
        self("PASS" if self.passed else "FAIL")
        return self.passed


def unwrap(result: Result[T]) -> T:
    if is_ok(result):
        return result.value
    raise AssertionError(result)


def real_hashes() -> dict[str, str]:
    files = [REAL / "library.db", *sorted((REAL / "artifacts").glob("*"))]
    return {p.relative_to(REAL).as_posix(): sha256(p.read_bytes()).hexdigest() for p in files}


def writable(remove: Callable[[str], object], path: str, _: BaseException) -> None:
    """A run's hash-checked `code/` copy is read-only."""
    os.chmod(path, 0o700)
    remove(path)


def copy_home(slug: str) -> Path:
    """A fresh copy of his Library B files; his own are only read."""
    root = BUILD / "homes" / f"libm-{slug}"
    if root.exists():
        shutil.rmtree(root, onexc=writable)
    root.mkdir(parents=True)
    if not HASHES.exists():
        HASHES.write_text(json.dumps(real_hashes(), indent=1), "utf-8")
    shutil.copy2(REAL / "library.db", root / "library.db")
    shutil.copytree(REAL / "artifacts", root / "artifacts")
    return root


def record(kind: str, body: dict[str, object], sequence: int) -> RegistrationRecord:
    writer = unwrap(WriterId.try_create("libm-fixture", "authoring", kind, "boot-1"))
    created = unwrap(Instant.try_create(1_700_000_000_000_000_000 + sequence))
    return unwrap(RegistrationRecord.try_create(kind, 1, [], body, writer, sequence, created))


def registry_port(note: str = "v2") -> RegistryReadPort:
    """Three fixture records through QMB's own as-of port: a book in two versions and a bot."""
    first = record("book-definition", {"alias": "scalping", "note": "v1"}, 0)
    second = record("book-definition", {"alias": "scalping", "note": note}, 1)
    bot = record("bot-definition", {"rule": "trend"}, 2)
    at = unwrap(Instant.try_create(1_700_000_000_000_000_010))
    pointer = unwrap(DatedPointer.try_create("scalping", second.stable_id, at))
    pair = unwrap(SupersedesRef.try_create(second.stable_id, first.stable_id))
    bound = unwrap(
        AsOfSet.try_create(
            at, records=(first, second, bot), pointers=(pointer,), supersedes=(pair,)
        )
    )
    hub = unwrap(PassiveHub.try_create((bound,)))
    return unwrap(RegistryReadPort.try_create(hub, stale_evidence_severity="workspace-declared"))


def plant_app(home: Path) -> None:
    """One app artifact and its definition folder, the apps' own layout."""
    import sqlite3  # noqa: PLC0415
    from contextlib import closing  # noqa: PLC0415

    body = json.dumps({"rows": 2}, sort_keys=True, separators=(",", ":")).encode()
    sha = sha256(body).hexdigest()
    (home / "apps/screener/blobs").mkdir(parents=True)
    (home / f"apps/screener/blobs/{sha}.json").write_bytes(body)
    ref = {"producer_app": "screener", "definition_hash": "d1", "output": "rows", "sha256": sha}
    with closing(sqlite3.connect(home / "artifacts.db")) as db, db:
        db.execute("CREATE TABLE artifacts (ref TEXT PRIMARY KEY, schema TEXT NOT NULL)")
        db.execute("INSERT INTO artifacts VALUES (?, ?)", (json.dumps(ref), '{"type":"object"}'))
    (home / "definitions/d1").mkdir(parents=True)
    (home / "definitions/d1/app.toml").write_text('id = "screener"\nname = "Screener"\n', "utf-8")


def imported(slug: str, log: Log, *, dry_run: bool) -> tuple[Path, float, int]:
    """A copy of his home with the fixtures, run through steps 0 to 4; its seconds and items."""
    home = copy_home(slug)
    plant_app(home)
    port = registry_port()
    counts = snapshot(home, port)
    log(f"step 0 counts: {json.dumps(counts.kinds)} registry {json.dumps(counts.registry)}")
    started = time.perf_counter()
    with open_target(home, dry_run=dry_run, redactor=redact) as store:
        b = import_library_b(store, home)
        r = import_registry(store, home, port)
        a = import_apps(store, home)
    seconds = time.perf_counter() - started
    log(f"library-b {b}; registry {r}; apps {a}")
    items = b.objects + r.objects + a.artifacts + a.definitions
    return home, seconds, items


def lane_import() -> bool:
    log = Log("import")
    home, seconds, items = imported("import", log, dry_run=True)
    result = verify(home, home / "migration" / "dry" / "library")
    for line in result.render().splitlines():
        log(f"  {line}")
    log.check("verify shows step 0's counts equal per kind", result.ok, len(result.rows))
    log.check("every imported blob hash checks", result.blobs_checked > 0, result.blobs_checked)
    log.check("no version chain is broken", result.bad_chains == [], result.bad_chains)
    per = 1000 * seconds / max(items, 1)
    log(f"perf: {items} items in {seconds:.2f} s, {per:.1f} s per 1,000 items")
    log.check("the import time is recorded", items > 0, f"{per:.1f} s per 1,000 items")
    return log.verdict()


def dual_home(log: Log) -> Path:
    home, _, _ = imported("dual", log, dry_run=False)
    return home


def lane_dual() -> bool:
    log = Log("dual")
    home = dual_home(log)
    service = ControlService(home)
    with Store.open(home / "library", redactor=redact) as store:
        service.attach_library_mirror(DualWrite(store))
        saved = service.library_save(
            LibraryInput(title="LIBM dual lane", kind="article", content={"lane": 3})
        )
        found = resolve_alias(store, str(saved["id"]))
        view = store.get(OPERATOR, found) if found else None
    old = service.library_get(str(saved["id"]))
    log.check("library.db holds the save", old["content"] == {"lane": 3}, old["id"])
    log.check("the store holds the save", view is not None, found)
    if view is not None:
        log.check("as the mapped kind", view.kind == "source", view.kind)
    return log.verdict()


def diff_output(engine_home: Path, run_id: str) -> object:
    with Reader.open(engine_home) as reader:
        for event in reader.events(run_id):
            if event.kind == "node_finished" and event.data.get("node_id") == "diff":
                return event.data.get("outputs")
    return None


def lane_diff() -> bool:
    log = Log("diff")
    home = dual_home(log)
    engine_home = home / "engine"
    inputs = {"home": str(home)}
    with Store.open(home / "library", redactor=redact) as store:
        adapter = EngineLibraryAdapter(store)
        with EngineService.open(engine_home, library=adapter) as svc:
            item = svc.drafts.put(TEMPLATE.name, Bundle.read(TEMPLATE), 0, caller=CALLER).item
            clean = asyncio.run(svc.tests.run(item, caller=CALLER, inputs=inputs))
            ControlService(home).library_save(
                LibraryInput(title="unmirrored", kind="note", content={})
            )
            gap = asyncio.run(svc.tests.run(item, caller=CALLER, inputs=inputs))
        reports = [r.fields.get("status") for r in adapter.objects(item, "test-report")]
    log(f"clean run {clean.run_id}: {clean.status}, diff {diff_output(engine_home, clean.run_id)}")
    log(f"gap run {gap.run_id}: {gap.status}, {gap.reason}")
    log.check("the diff test run passed", clean.status == "passed", clean.status)
    log.check("after a save without the mirror it fails", gap.status == "failed", gap.status)
    log.check("the store holds a test-report per run", reports == ["passed", "failed"], reports)
    return log.verdict()


def lane_alias() -> bool:
    log = Log("alias")
    home, _, _ = imported("alias", log, dry_run=True)
    import sqlite3  # noqa: PLC0415

    with sqlite3.connect(pre(home) / "library.db") as db:
        raw = db.execute("SELECT data FROM items ORDER BY rowid LIMIT 1").fetchone()
    row: dict[str, Any] = json.loads(raw[0])
    ref = f"artifacts/{row['sha256']}"
    with Store.open(home / "migration" / "dry" / "library", redactor=redact) as store:
        found = resolve_alias(store, ref)
        view = store.get(OPERATOR, found) if found else None
    log(f"old ref {ref} of {row['id']}")
    log.check("the old ref resolves", view is not None, found)
    if view is not None:
        same = view.blobs["content"].blob_id == f"sha256:{row['sha256']}"
        log.check("to the object holding the same bytes", same, view.blobs["content"].blob_id)
        log.check(
            "which keeps the old kind", view.fields["legacy_kind"] == row["kind"], row["kind"]
        )
    return log.verdict()


def lane_collision() -> bool:
    """The bot record's fp1 planted with another body, as a forged or corrupted registry row would
    carry it; QMB's own as-of set cannot hold one, so the plant is a port-shaped fixture."""
    log = Log("collision")
    home, _, _ = imported("collision", log, dry_run=True)
    bot = next(r for r in registry_port().bound.records if r.kind == "bot-definition")
    forged = SimpleNamespace(
        kind=bot.kind,
        contract_format_version=bot.contract_format_version,
        at_birth_parent_refs=bot.at_birth_parent_refs,
        stable_id=bot.stable_id,
        body={"rule": "forged"},
    )
    plant = SimpleNamespace(bound=SimpleNamespace(records=[forged], pointers=(), supersedes=()))
    with Store.open(home / "migration" / "dry" / "library", redactor=redact) as store:
        before = len(store.placements())
        try:
            import_registry(store, home, plant)
            stopped = "imported"
        except MigrationAlarm as alarm:
            stopped = alarm.code
        after = len(store.placements())
    alarms = (home / "migration" / "alarms.jsonl").read_text("utf-8").splitlines()
    log(f"alarm: {alarms[-1] if alarms else None}")
    log.check("the import stops with a collision alarm", stopped == "collision", stopped)
    log.check("nothing more was written", after == before, (before, after))
    return log.verdict()


def lane_real() -> bool:
    log = Log("real")
    before = json.loads(HASHES.read_text("utf-8")) if HASHES.exists() else None
    now = real_hashes()
    for name, digest in now.items():
        log(f"  {name} {digest}")
    log.check("hashes were recorded before the lanes", before is not None, HASHES)
    log.check("his library.db and blobs are unchanged", before == now, len(now))
    return log.verdict()


def run_suites(checkout: Path, log: Log, label: str) -> dict[str, set[str]]:
    failing: dict[str, set[str]] = {}
    env = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC", "CLAUDE"))}
    env.pop("NODE_USE_SYSTEM_CA", None)
    for suite in SUITES:
        folder = checkout / "qmx-agents" / "packages" / suite
        done = subprocess.run(
            [UV, "run", "--no-sync", "python", "-m", "pytest", "-n", "2", "-q", "-rf", "-p",
             "no:cacheprovider"],
            cwd=folder,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )  # fmt: skip
        lines = done.stdout.splitlines()
        failing[suite] = {line.split()[1] for line in lines if line.startswith("FAILED ")}
        log(f"{label} {suite}: {lines[-1] if lines else done.stderr[-200:]}")
    return failing


def lane_regression() -> bool:
    log = Log("regression")
    parent = Path("D:/Temp/libm-parent")
    if not parent.exists():
        subprocess.run(
            [GIT, "-C", str(ROOT), "worktree", "add", "--detach", str(parent), PARENT], check=True
        )
        subprocess.run(
            [UV, "sync", "--frozen", "--all-packages", "--all-groups"],
            cwd=parent / "qmx-agents",
            check=True,
            capture_output=True,
        )
    before = run_suites(parent, log, f"parent {PARENT[:8]}")
    after = run_suites(ROOT, log, "head")
    for suite in SUITES:
        new = sorted(after[suite] - before[suite])
        log.check(f"head fails nothing the parent passes in {suite}", new == [], new)
    return log.verdict()


def lane_secrets() -> bool:
    log = Log("secrets")
    done = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "secret_scan.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    for line in (done.stdout + done.stderr).splitlines():
        log(line)
    log.check("the secret scan is clean", done.returncode == 0, done.returncode)
    return log.verdict()


def lane_processes() -> bool:
    log = Log("processes")
    found: list[str] = []
    for process in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            line = " ".join(process.info["cmdline"] or [])
            name = str(process.info["name"] or "").lower()
        except psutil.Error:
            continue
        mine = "libm" in line and process.pid != os.getpid()
        if mine and (name.startswith(("python", "claude", "qma-cli-launcher"))):
            found.append(f"{process.info['pid']} {name} {line[:160]}")
    for row in found:
        log(f"  {row}")
    log.check("no importer, qmx_host or claude process is left", found == [], len(found))
    log.check("no lane lock is left", not LANE_LOCK.exists(), LANE_LOCK)
    return log.verdict()


LANES: Final[dict[str, Callable[[], bool]]] = {
    "regression": lane_regression,
    "import": lane_import,
    "dual": lane_dual,
    "diff": lane_diff,
    "alias": lane_alias,
    "collision": lane_collision,
    "real": lane_real,
    "secrets": lane_secrets,
    "processes": lane_processes,
}


def main() -> int:
    named = sys.argv[1:] or ["import", "dual", "diff"]
    results = {name: LANES[name]() for name in named}
    print(json.dumps(results))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
