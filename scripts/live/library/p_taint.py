"""P-TAINT (Library AD-22, SOLUTION-DESIGN 28.8): `marks()` on a synthetic 100,000-item edge
table in SQLite, memory rows included, for items with a 20-deep, 500-node ancestry.

The store is rebuilt from a fixed seed on every run, so a rerun measures the same graph. The
items fall into clusters of 20 upstream layers of 25 objects; a cluster's tip is the probed item.
Inside a cluster the walked relations (`consumed`, `derived-from`, `uses`, `compiles-to`) link
each object to three objects one layer up; `cites` and `mentions` edges reach other clusters
and must not be walked. `marks()` is one recursive query plus a parent-pointer path, the shape
LIB2 would ship (Lib AD-8 rule 10: the SQLite edge table with recursive queries first).

    uv run --no-sync python scripts/live/library/p_taint.py
"""

from __future__ import annotations

import random
import sqlite3
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from common import HOMES, Log, Verdict, p95

ITEMS: Final = 100_000
LAYERS: Final = 20
WIDTH: Final = 25
CLUSTER: Final = 1 + LAYERS * WIDTH
TARGETS: Final = 20
REPEATS: Final = 10
PASS_P95_MS: Final = 50.0
SEED: Final = 2026_10_18
WALKED: Final = ("consumed", "derived-from", "uses", "compiles-to")
WALK_PARAMS: Final = {f"w{n}": relation for n, relation in enumerate(WALKED)}
NOT_WALKED: Final = ("cites", "mentions")
KINDS: Final = ("artifact", "backtest-result", "dataset", "memory-row", "workflow-run", "source")
RANK: Final = {"none": 0, "superseded": 1, "corrected": 2, "quarantined": 3}
FALLBACK: Final = (
    "LIB2 adds a derived closure index rebuilt from the edges (an index, never evidence)."
)

SCHEMA: Final = """
CREATE TABLE items(item_id TEXT PRIMARY KEY, kind TEXT NOT NULL, head TEXT NOT NULL);
CREATE TABLE objects(object_id TEXT PRIMARY KEY, item_id TEXT NOT NULL);
CREATE TABLE edges(src TEXT NOT NULL, dst TEXT NOT NULL, type TEXT NOT NULL);
CREATE TABLE marks(item_id TEXT PRIMARY KEY, mark TEXT NOT NULL, reason TEXT NOT NULL);
"""
INDEXES: Final = """
CREATE INDEX edges_up ON edges(src, type, dst);
CREATE INDEX edges_down ON edges(dst, type);
CREATE INDEX objects_item ON objects(item_id);
"""

MARKS_SQL: Final = """
WITH RECURSIVE up(node, child) AS (
  SELECT dst, src FROM edges WHERE src = :start AND type IN (:w0, :w1, :w2, :w3)
  UNION
  SELECT e.dst, e.src FROM edges e JOIN up ON e.src = up.node WHERE e.type IN (:w0, :w1, :w2, :w3)
)
SELECT up.node, up.child,
  (SELECT m.mark FROM objects o JOIN marks m ON m.item_id = o.item_id
   WHERE o.object_id = up.node) AS stored,
  (SELECT i.head <> up.node FROM objects o JOIN items i ON i.item_id = o.item_id
   WHERE o.object_id = up.node) AS superseded,
  EXISTS(SELECT 1 FROM edges r WHERE r.dst = up.node AND r.type = 'replaces') AS corrected
FROM up
"""


@dataclass(frozen=True)
class Marks:
    worst: str
    path: tuple[str, ...]
    child_of: dict[str, str]
    """Each upstream object to the first object found below it on the walk."""


def marks(db: sqlite3.Connection, object_id: str) -> Marks:
    """The worst mark upstream of `object_id` and the path that carries it (Library AD-22)."""
    child_of: dict[str, str] = {}
    worst, at = "none", ""
    for node, child, stored, superseded, corrected in db.execute(
        MARKS_SQL, {"start": object_id, **WALK_PARAMS}
    ):
        child_of.setdefault(node, child)
        mark = (
            "quarantined"
            if stored == "quarantined"
            else "corrected"
            if corrected
            else "superseded"
            if superseded
            else "none"
        )
        if RANK[mark] > RANK[worst]:
            worst, at = mark, node
    path: list[str] = []
    while at and at != object_id:
        path.append(at)
        at = child_of[at]
    return Marks(worst, (object_id, *reversed(path)) if path else (), child_of)


def depth(found: Marks, object_id: str) -> int:
    """Hops from `object_id` to the furthest upstream object along the walk's parent pointers."""
    longest = 0
    for node in found.child_of:
        hops, here = 0, node
        while here != object_id:
            here, hops = found.child_of[here], hops + 1
        longest = max(longest, hops)
    return longest


def oid(n: int) -> str:
    return f"o{n:06d}"


def build(path: Path) -> list[str]:
    """Write the store and return the probed tips, half with a quarantined root 20 hops up."""
    path.unlink(missing_ok=True)
    rng = random.Random(SEED)  # noqa: S311
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    items: list[tuple[str, str, str]] = []
    objects: list[tuple[str, str]] = []
    edges: list[tuple[str, str, str]] = []
    marks_rows: list[tuple[str, str, str]] = []
    clusters = ITEMS // CLUSTER
    next_object = clusters * CLUSTER
    tips: list[str] = []
    for c in range(clusters):
        base = c * CLUSTER
        layer_of = [base + 1 + layer * WIDTH for layer in range(LAYERS)]
        for n in range(base, base + CLUSTER):
            kind = "memory-row" if rng.random() < 0.15 else rng.choice(KINDS)
            items.append((f"i{n:06d}", kind, oid(n)))
            objects.append((oid(n), f"i{n:06d}"))
        for j in range(WIDTH):
            edges.append((oid(base), oid(layer_of[0] + j), rng.choice(WALKED)))
        for layer in range(LAYERS - 1):
            for j in range(WIDTH):
                child = oid(layer_of[layer] + j)
                for step in (0, 1, rng.randrange(2, WIDTH)):
                    parent = oid(layer_of[layer + 1] + (j + step) % WIDTH)
                    edges.append((child, parent, rng.choice(WALKED)))
        for _ in range(CLUSTER // 2):
            here = oid(base + rng.randrange(CLUSTER))
            there = oid(rng.randrange(clusters * CLUSTER))
            edges.append((here, there, rng.choice(NOT_WALKED)))
        if c % 3 == 0:
            stale = base + 1 + rng.randrange(LAYERS * WIDTH)
            items[stale] = (items[stale][0], items[stale][1], oid(next_object))
            objects.append((oid(next_object), items[stale][0]))
            next_object += 1
        if c % 4 == 0:
            fixed = oid(base + 1 + rng.randrange(LAYERS * WIDTH))
            edges.append((oid(next_object), fixed, "replaces"))
            objects.append((oid(next_object), f"i{next_object:06d}"))
            items.append((f"i{next_object:06d}", "dataset", oid(next_object)))
            next_object += 1
        if c < TARGETS:
            tips.append(oid(base))
            if c % 2 == 0:
                root = layer_of[LAYERS - 1] + rng.randrange(WIDTH)
                marks_rows.append((f"i{root:06d}", "quarantined", "probe: corrected feed"))
    filler = ITEMS - len(items)
    for k in range(filler):
        n = next_object + k
        items.append((f"i{n:06d}", rng.choice(KINDS), oid(n)))
        objects.append((oid(n), f"i{n:06d}"))
        edges.append((oid(n), oid(rng.randrange(clusters * CLUSTER)), rng.choice(WALKED)))
    with db:
        db.executemany("INSERT INTO items VALUES (?, ?, ?)", items)
        db.executemany("INSERT INTO objects VALUES (?, ?)", objects)
        db.executemany("INSERT INTO edges VALUES (?, ?, ?)", edges)
        db.executemany("INSERT INTO marks VALUES (?, ?, ?)", marks_rows)
    db.executescript(INDEXES)
    db.execute("ANALYZE")
    db.close()
    return tips


def verdict(samples_ms: Sequence[float], ancestry: int, levels: int) -> Verdict:
    """PASS when the p95 is at most 50 ms on an ancestry of at least 500 nodes, 20 deep."""
    worst = p95(samples_ms)
    numbers = {
        "p95_ms": round(worst, 2),
        "p50_ms": round(sorted(samples_ms)[len(samples_ms) // 2], 2),
        "max_ms": round(max(samples_ms), 2),
        "samples": len(samples_ms),
        "ancestry": ancestry,
        "depth": levels,
    }
    if ancestry < 500 or levels < 20:
        return Verdict(
            "P-TAINT",
            "FAIL",
            numbers,
            "the probe graph is smaller than the pass line names",
            FALLBACK,
        )
    if worst <= PASS_P95_MS:
        return Verdict("P-TAINT", "PASS", numbers, f"p95 is within {PASS_P95_MS:.0f} ms")
    return Verdict("P-TAINT", "FAIL", numbers, f"p95 is over {PASS_P95_MS:.0f} ms", FALLBACK)


def main() -> None:
    log = Log("prb-l-taint-nest")
    HOMES.mkdir(parents=True, exist_ok=True)
    store = HOMES / "p_taint.db"
    started = time.perf_counter()
    tips = build(store)
    db = sqlite3.connect(f"file:{store.as_posix()}?mode=ro", uri=True)
    counts = {
        table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # noqa: S608
        for table in ("items", "objects", "edges", "marks")
    }
    memory_rows = db.execute("SELECT count(*) FROM items WHERE kind = 'memory-row'").fetchone()[0]
    log.say(
        f"built {store.name} in {time.perf_counter() - started:.1f} s: {counts}, "
        f"memory rows {memory_rows}, size {store.stat().st_size / 1e6:.1f} MB"
    )
    samples: list[float] = []
    ancestry, deepest = CLUSTER, 0
    for tip in tips:
        began = time.perf_counter()
        found = marks(db, tip)
        samples.append((time.perf_counter() - began) * 1000)
        for _ in range(REPEATS - 1):
            began = time.perf_counter()
            marks(db, tip)
            samples.append((time.perf_counter() - began) * 1000)
        hops = depth(found, tip)
        ancestry, deepest = min(ancestry, len(found.child_of)), max(deepest, hops)
        log.say(
            f"  {tip}: worst={found.worst} path_len={len(found.path)} "
            f"ancestry={len(found.child_of)} depth={hops}"
        )
    db.close()
    fresh: list[float] = []
    for tip in tips:
        began = time.perf_counter()
        with sqlite3.connect(f"file:{store.as_posix()}?mode=ro", uri=True) as cold:
            marks(cold, tip)
        cold.close()
        fresh.append((time.perf_counter() - began) * 1000)
    result = verdict(samples, ancestry, deepest)
    result.notes.append(f"fresh connection per call p95 {p95(fresh):.2f} ms over {len(fresh)}")
    log.verdict(result)


if __name__ == "__main__":
    main()
