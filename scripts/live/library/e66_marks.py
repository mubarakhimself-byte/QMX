"""LIB2's live lanes: E66 and the menu around it, on the real Library store.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/library/e66_marks.py [lane ...]`
Lanes are `e66 taint asof agent regime memory superseded secrets processes`; none named runs
`e66 taint asof`. Each writes `<LIB2_EVIDENCE>/<LIB2_LOG_PREFIX>lib2-<lane>.log` (default
`D:/QMX-worktrees/qma-ship/build/evidence/lib2`, prefix `owner-`, `check-` for the coordinator),
on a throwaway home under `D:/QMX-worktrees/qma-ship/build/homes/lib2-<lane>`, and the script
exits 1 if any lane failed. No model, no key, no ship home, no lane lock.

- `e66` (lane 2): dataset r12 feeds two results that support a hypothesis and a published
  workflow that uses it. Quarantining r12 shows on both results with the path, refuses the
  workflow's trigger in the real ticker (`quarantined_input`, no run) and turns the hypothesis
  `open`; clearing the mark restores all three, and the next fire runs.
- `taint` (lane 3): P-TAINT's own 100,000-item graph (`scripts/live/library/p_taint.py`, same
  seed) loaded into the store's `catalog.db` schema, and `qmx_library.marks.marks` timed on it.
  The probe drew `compiles-to` child to parent like the other walked edges; the Library writes it
  pod to book, so the lane loads those edges reversed and the ancestry stays the probe's.
  Pass is p95 at most 50 ms on a 500-node, 20-deep ancestry.
- `asof` (lane 4): an item read as of a time before its last version answers with the older one.
- `agent` (lane 5), `regime` (lane 6), `memory` (lane 7), `superseded` (lane 8), `secrets`
  (lane 9) and `processes` (lane 10), as the plan names them.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import psutil
from qmx_engine.ledger import redact
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.settings import StaticSettings
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR as ENGINE_OPERATOR
from qmx_engine.settings import DEFAULTS
from qmx_engine.triggers import rows
from qmx_engine.triggers.ticker import Scheduler
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.fts import Catalog
from qmx_library.marks import marks
from qmx_library.port import Draft, JsonObject, LibraryRefused, Relation
from qmx_library.principal import Principal
from qmx_library.status import status
from qmx_library.store import Store

BUILD: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = Path(os.environ.get("LIB2_EVIDENCE", str(BUILD / "evidence" / "lib2")))
PREFIX: Final = os.environ.get("LIB2_LOG_PREFIX", "owner-")
ROOT: Final = Path(__file__).resolve().parents[3]
CHAIN: Final = ROOT / "qmx-agents" / "packages" / "qmx-engine" / "tests" / "fixtures" / "workflows"
PROBES: Final = ROOT / "scripts" / "live" / "library"
LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
OPERATOR: Final = Principal("operator")
AGENT: Final = Principal("agent", "lib2-lane")
TAINT_LINE_MS: Final = 50.0
PROBE_P95_MS: Final = 13.73
SETTINGS: Final = {**DEFAULTS, "triggers.rerun_delays": ()}
"""No re-run is held after a refused fire, so the lane reads each fire once."""


class Log:
    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{PREFIX}lib2-{slug}.log"
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


def home(slug: str) -> Path:
    root = BUILD / "homes" / f"lib2-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def opened(slug: str) -> Store:
    return Store.open(home(slug) / "library", redactor=redact)


def put(
    store: Store,
    kind: str,
    item: str,
    relations: list[Relation] | None = None,
    fields: JsonObject | None = None,
) -> str:
    found = store.head(item, "main")
    draft = Draft(kind, item, item, fields=fields or {}, relations=relations or [])
    head = None if found is None else found[0]
    return store.put(OPERATOR, draft, on="main", expected_head=head).object_id


def short(path: tuple[str, ...], names: dict[str, str]) -> str:
    return " -> ".join(names.get(o, o[-8:]) for o in path)


def lane_e66() -> bool:
    log = Log("e66")
    root = home("e66")
    with Store.open(root / "library", redactor=redact) as store:
        adapter = EngineLibraryAdapter(store)
        r12 = put(store, "dataset", "r12", fields={"source": "lane", "instruments": ["EURUSD"]})
        idea = put(store, "hypothesis", "idea", fields={"statement": "r12 momentum holds"})
        first = put(
            store,
            "backtest-result",
            "res-1",
            [("consumed", r12), ("tests", idea)],
            {"outcome": "supports"},
        )
        second = put(
            store,
            "backtest-result",
            "res-2",
            [("consumed", r12), ("tests", idea)],
            {"outcome": "supports"},
        )
        names = {r12: "r12", first: "res-1", second: "res-2"}
        log(f"r12 {r12}; results {first} {second}; hypothesis idea {idea}")
        with EngineService.open(
            root / "home", library=adapter, settings=StaticSettings(SETTINGS)
        ) as svc:
            bundle = Bundle.read(CHAIN / "script-chain")
            item = svc.drafts.put(None, bundle, 0, caller=ENGINE_OPERATOR).item
            report = asyncio.run(svc.tests.run(item, caller=ENGINE_OPERATOR))
            log(f"workflow {item} test run {report.status}")
            version = svc.versions.publish(item, "1.0.0", caller=ENGINE_OPERATOR)
            svc.versions.enable(version, caller=ENGINE_OPERATOR)
            store.relate(OPERATOR, version, "uses", r12)
            names[version] = "workflow"
            trigger = rows.create(
                svc.ctx.engine.ledger,
                workflow_item=item,
                pinned_object=version,
                spec=rows.Manual(),
                caller=ENGINE_OPERATOR,
                now=datetime.now(UTC),
            )
            log(f"published {version}, which uses r12; manual trigger {trigger.id}")
            before = status(store, OPERATOR, "idea").status
            log.check(
                "before the mark the hypothesis reads supported", before == "supported", before
            )

            store.mark(OPERATOR, "r12", True, "feed corrected upstream")
            log("operator quarantined r12: feed corrected upstream")
            for obj in (first, second):
                seen = store.marks(OPERATOR, obj)
                log.check(
                    f"{names[obj]} reads built on quarantined input with its path",
                    seen.worst == "quarantined" and seen.path == (obj, r12),
                    f"{seen.label.split(':')[0]}: {short(seen.path, names)} ({seen.reason})",
                )
            fire = fire_once(svc, trigger.id)
            digest = digest_of(svc, fire.id)
            log(f"fire {fire.id}: {fire.status}; digest {digest}")
            log.check(
                "the trigger is refused with quarantined_input and its path, and starts no run",
                fire.status == "blocked_config"
                and fire.run_id is None
                and f"quarantined_input: {version} is built on quarantined input: "
                f"{version} -> {r12}"
                in digest,
                (fire.status, fire.run_id),
            )
            during = status(store, OPERATOR, "idea")
            log.check(
                "the hypothesis supported only by those results reads open",
                during.status == "open" and set(during.ignored) == {first, second},
                (during.status, len(during.ignored)),
            )

            store.mark(OPERATOR, "r12", False, "checked again")
            log("operator cleared the mark on r12")
            cleared = [store.marks(OPERATOR, obj).worst for obj in (first, second)]
            log.check("both results read unmarked", cleared == [None, None], cleared)
            after = status(store, OPERATOR, "idea").status
            log.check("the hypothesis reads supported again", after == "supported", after)
            fire = fire_once(svc, trigger.id)
            log(f"fire {fire.id}: {fire.status} {fire.detail}")
            log.check(
                "the next fire runs", fire.status == "ok" and fire.run_id is not None, fire.status
            )
    return log.verdict()


def digest_of(svc: EngineService, fire_id: str) -> str:
    with Reader.open(svc.ctx.home) as reader:
        row = reader.connection.execute("SELECT digest FROM fires WHERE id = ?", (fire_id,))
        return str(row.fetchone()[0])


def fire_once(svc: EngineService, trigger_id: str) -> rows.Fire:
    rows.fire_now(svc.ctx.engine.ledger, trigger_id, datetime.now(UTC), {})
    ticker = Scheduler(svc.ctx)

    async def go() -> None:
        await ticker.tick()
        await ticker.settle()

    asyncio.run(go())
    with Reader.open(svc.ctx.home) as reader:
        return rows.fires(reader.connection, trigger_id)[-1]


def lane_taint() -> bool:
    log = Log("taint")
    sys.path.insert(0, str(PROBES))
    import p_taint  # noqa: PLC0415

    root = home("taint")
    probe_db = root / "p_taint.db"
    began = time.perf_counter()
    tips = p_taint.build(probe_db)
    catalog = Catalog(root / "catalog.db")
    db = catalog.db
    src = sqlite3.connect(probe_db)
    item_of = dict(src.execute("SELECT object_id, item_id FROM objects"))
    db.execute("BEGIN")
    db.executemany(
        "INSERT INTO objects VALUES (?, ?, 'dataset', 'record', '', '', '{}', '{}', '[]', '[]')",
        item_of.items(),
    )
    db.executemany(
        "INSERT INTO heads VALUES (?, 'main', ?, 1)",
        src.execute("SELECT item_id, head FROM items"),
    )
    db.executemany(
        "INSERT OR IGNORE INTO relations (from_id, type, to_id, origin) VALUES (?, ?, ?, 'edge')",
        src.execute(
            "SELECT iif(type = 'compiles-to', dst, src), type, "
            "iif(type = 'compiles-to', src, dst) FROM edges"
        ),
    )
    stored = src.execute("SELECT item_id, reason FROM marks").fetchall()
    db.executemany(
        "INSERT INTO heads VALUES (?, 'refs/items/' || ? || '/marks', 'quarantined', 1)",
        [(item, item) for item, _ in stored],
    )
    db.executemany(
        "INSERT INTO moves (item, ref, principal, new_head, at, reason) "
        "VALUES (?, 'refs/items/' || ? || '/marks', 'operator', 'quarantined', '2026-10-20Z', ?)",
        [(item, item, reason) for item, reason in stored],
    )
    db.execute("COMMIT")
    db.execute("ANALYZE")
    src.close()
    (objects,) = db.execute("SELECT count(*) FROM objects").fetchone()
    (edges,) = db.execute("SELECT count(*) FROM relations").fetchone()
    log(
        f"P-TAINT graph (seed {p_taint.SEED}) in the catalog schema in "
        f"{time.perf_counter() - began:.1f} s: {objects} objects, {edges} relations, "
        f"{len(stored)} quarantined roots, {len(tips)} probed tips"
    )
    samples: list[float] = []
    quarantined = 0
    for tip in tips:
        found = marks(db, tip)
        quarantined += found.worst == "quarantined"
        log(f"  {tip}: worst={found.worst} path_len={len(found.path)}")
        for _ in range(p_taint.REPEATS):
            start = time.perf_counter()
            marks(db, tip)
            samples.append((time.perf_counter() - start) * 1000)
    reach = db.execute(
        "WITH RECURSIVE up(node) AS (SELECT ? UNION SELECT r.to_id FROM relations r "
        "JOIN up ON r.from_id = up.node WHERE r.type IN ('consumed', 'derived-from', 'uses') "
        "UNION SELECT r.from_id FROM relations r JOIN up ON r.to_id = up.node "
        "WHERE r.type = 'compiles-to') SELECT count(*) - 1 FROM up",
        (tips[0],),
    ).fetchone()[0]
    catalog.close()
    worst = p_taint.p95(samples)
    log(
        f"marks() p95 {worst:.2f} ms, p50 {sorted(samples)[len(samples) // 2]:.2f} ms, "
        f"max {max(samples):.2f} ms over {len(samples)} samples; probe baseline p95 "
        f"{PROBE_P95_MS} ms; ancestry of the first tip {reach}"
    )
    log.check(
        "half the tips find their quarantined root", quarantined == len(tips) // 2, quarantined
    )
    log.check("the first tip's ancestry is at least 500 nodes", reach >= 500, reach)
    log.check(
        f"marks() p95 is at most {TAINT_LINE_MS:.0f} ms", worst <= TAINT_LINE_MS, f"{worst:.2f}"
    )
    return log.verdict()


def lane_asof() -> bool:
    log = Log("asof")
    with opened("asof") as store:
        first = put(store, "note", "plan", fields={})
        time.sleep(0.05)
        then = datetime.now(UTC)
        time.sleep(0.05)
        last = store.put(
            OPERATOR, Draft("note", "plan", "plan v2"), on="main", expected_head=first
        ).object_id
        log(f"plan v1 {first}, then {then.isoformat()}, plan v2 {last}")
        now_head = store.resolve(OPERATOR, "plan")
        old_head = store.resolve(OPERATOR, "plan", as_of=then)
        log.check("the head now is v2", now_head == last, now_head)
        log.check("as of the earlier time v1 answers", old_head == first, old_head)
        title = store.get(OPERATOR, old_head, as_of=then).title
        log.check("get as of then reads v1's title", title == "plan", title)
        hits = [h.object_id for h in store.search(OPERATOR, "plan", as_of=then)]
        log.check("search as of then finds v1 only", hits == [first], hits)
        log.check(
            "get of v2 as of then is not_found",
            refused(lambda: store.get(OPERATOR, last, as_of=then)) == "not_found",
            "not_found",
        )
    return log.verdict()


def refused(call: Callable[[], object]) -> str:
    try:
        call()
    except LibraryRefused as error:
        return error.code
    return "accepted"


def lane_agent() -> bool:
    log = Log("agent")
    with opened("agent") as store:
        put(store, "dataset", "r12")
        code = refused(lambda: store.mark(AGENT, "r12", True, "an agent thinks so"))
        log.check("an agent principal's mark is refused", code == "ref_not_owned", code)
        log.check("nothing is marked", store.head("r12", "refs/items/r12/marks") is None, "none")
    return log.verdict()


def lane_regime() -> bool:
    log = Log("regime")
    with opened("regime") as store:
        feed = put(store, "dataset", "feed")
        idea = put(store, "hypothesis", "idea", fields={"statement": "carry pays"})
        for name, outcome in (("low-vol", "supports"), ("high-vol", "refutes")):
            res = put(
                store,
                "backtest-result",
                f"res-{name}",
                [("consumed", feed), ("tests", idea)],
                {"outcome": outcome},
            )
            store.annotate(OPERATOR, res, {"tags": [f"regime:{name}"]})
        found = status(store, OPERATOR, "idea")
        log(f"status {found.status}, by regime {dict(found.by_regime)}")
        log.check(
            "it reads mixed, supported in low-vol and refuted in high-vol",
            (found.status, dict(found.by_regime))
            == ("mixed", {"high-vol": "refuted", "low-vol": "supported"}),
            found.status,
        )
    return log.verdict()


def lane_memory() -> bool:
    log = Log("memory")
    with opened("memory") as store:
        feed = put(store, "dataset", "feed")
        run = put(
            store,
            "workflow-run",
            "run-1",
            [("consumed", feed)],
            {"run_id": "run-1", "mode": "live", "status": "passed"},
        )
        row = put(
            store,
            "memory-row",
            "lesson",
            [("derived-from", run)],
            {"scope": "operator", "tag": "lesson", "when_to_use": "always", "content": "x"},
        )
        store.mark(OPERATOR, "feed", True, "tainted feed")
        seen = store.marks(OPERATOR, row)
        names = {feed: "feed", run: "run-1", row: "lesson"}
        log.check(
            "the memory row's marks show the path through its run",
            seen.worst == "quarantined" and seen.path == (row, run, feed),
            short(seen.path, names),
        )
    return log.verdict()


def lane_superseded() -> bool:
    log = Log("superseded")
    with opened("superseded") as store:
        v1 = put(store, "dataset", "feed")
        res = put(store, "backtest-result", "res", [("consumed", v1)], {"outcome": "supports"})
        put(store, "dataset", "feed", fields={"source": "v2"})
        seen = store.marks(OPERATOR, res)
        stored = store.head("feed", "refs/items/feed/marks")
        log.check(
            "it reads superseded with no stored mark",
            seen.worst == "superseded" and seen.path == (res, v1) and stored is None,
            (seen.worst, stored),
        )
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
        host = name.startswith("python") and "qmx_host" in line
        if "lib2-" in line and (host or name.startswith(("claude", "qma-cli-launcher"))):
            found.append(f"{process.info['pid']} {name} {line[:160]}")
    for row in found:
        log(f"  {row}")
    log.check("no qmx_host, claude or qma-cli-launcher process is left", found == [], len(found))
    log.check("no lane lock is left", not LANE_LOCK.exists(), LANE_LOCK)
    return log.verdict()


LANES: Final[dict[str, Callable[[], bool]]] = {
    "e66": lane_e66,
    "taint": lane_taint,
    "asof": lane_asof,
    "agent": lane_agent,
    "regime": lane_regime,
    "memory": lane_memory,
    "superseded": lane_superseded,
    "secrets": lane_secrets,
    "processes": lane_processes,
}


def main() -> int:
    named = sys.argv[1:] or ["e66", "taint", "asof"]
    results = {name: LANES[name]() for name in named}
    print(json.dumps(results))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
