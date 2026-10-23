"""Marks, derived at read (Library AD-22).

One mark is stored: `quarantined`, with a reason, on `refs/items/<item_id>/marks`, set or cleared
by the operator alone (`Store.mark`). Three more are computed and never stored: `superseded` (the
object is no longer the head of its item's `main`), `corrected` (a `replaces` edge points at
it), and `corrected` on a range (a correction the series card records overlaps the range a
consumer says it read). `marks(object_id)` walks upstream from the object shown, along
`consumed`, `derived-from` and `uses` out of each object and `compiles-to` into it (a book's
upstream is the pod compiled to it), and returns the worst mark with the path that carries it.
Nothing is written onto descendants, so clearing a mark clears everything derived
from it at once.

Two rules keep a data revision from marking work it did not change (DATA-PLAN DR3A, P-MARKS):
a newer card of the **same series** does not supersede the version a result read, because the
result read the series and not that snapshot of it; and a correction marks only a consumer
whose recorded read range overlaps the corrected range, so a result that read 2019 stays
unmarked when March 2024 is corrected.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Final, Literal, cast

from qmx_library.port import ObjectId

type Mark = Literal["superseded", "corrected", "quarantined"]

QUARANTINED: Final = "quarantined"
CLEAR: Final = "clear"
RANK: Final[dict[Mark | None, int]] = {None: 0, "superseded": 1, "corrected": 2, "quarantined": 3}
UPSTREAM_OUT: Final = ("consumed", "derived-from", "uses")
UPSTREAM_IN: Final = "compiles-to"
SERIES_KIND: Final = "dataset"

WALK: Final = """
WITH RECURSIVE up(node, child) AS (
  SELECT :start, NULL
  UNION
  SELECT r.to_id, up.node FROM relations r JOIN up ON r.from_id = up.node
  WHERE r.type IN (:o0, :o1, :o2)
  UNION
  SELECT r.from_id, up.node FROM relations r JOIN up ON r.to_id = up.node
  WHERE r.type = :i0
)
SELECT up.node, up.child,
  (SELECT h.head FROM objects o JOIN heads h
     ON h.item = o.item AND h.ref = 'refs/items/' || o.item || '/marks'
   WHERE o.object_id = up.node) AS stored,
  (SELECT m.reason FROM objects o JOIN moves m
     ON m.item = o.item AND m.ref = 'refs/items/' || o.item || '/marks'
   WHERE o.object_id = up.node ORDER BY m.seq DESC LIMIT 1) AS reason,
  (SELECT h.head <> up.node FROM objects o JOIN heads h ON h.item = o.item AND h.ref = 'main'
   WHERE o.object_id = up.node) AS superseded,
  EXISTS (SELECT 1 FROM relations r WHERE r.to_id = up.node AND r.type = 'replaces') AS replaced
FROM up
"""
PARAMS: Final = {
    "o0": UPSTREAM_OUT[0],
    "o1": UPSTREAM_OUT[1],
    "o2": UPSTREAM_OUT[2],
    "i0": UPSTREAM_IN,
}
DETAILS: Final = "SELECT kind, item, fields FROM objects WHERE object_id = ?"
HEAD: Final = "SELECT head FROM heads WHERE item = ? AND ref = 'main'"


def marks_ref(item: str) -> str:
    return f"refs/items/{item}/marks"


@dataclass(frozen=True, slots=True)
class Marks:
    worst: Mark | None
    path: tuple[ObjectId, ...]
    """From the object shown to the object carrying `worst`; empty when nothing is marked."""
    reason: str = ""
    """The stored reason when `worst` is `quarantined`."""

    @property
    def label(self) -> str:
        """What a card shows beside the object, empty when nothing is marked."""
        if self.worst is None:
            return ""
        if len(self.path) == 1:
            return self.worst
        return f"built on {self.worst} input: {' -> '.join(self.path)}"


@dataclass(frozen=True, slots=True)
class _Object:
    kind: str
    item: str
    fields: dict[str, object]

    @property
    def series(self) -> str:
        """The series key this object is a card of, empty when it is not a series card."""
        if self.kind != SERIES_KIND:
            return ""
        found = self.fields.get("series_key")
        return found if isinstance(found, str) else ""


def _cached(
    seen: dict[str, _Object | None], db: sqlite3.Connection, object_id: str
) -> _Object | None:
    if object_id not in seen:
        row = db.execute(DETAILS, (object_id,)).fetchone()
        if row is None:
            seen[object_id] = None
        else:
            kind_name, item, fields = row
            loaded = json.loads(fields) if fields else {}
            seen[object_id] = _Object(str(kind_name), str(item), cast(dict[str, object], loaded))
    return seen[object_id]


def _head(db: sqlite3.Connection, item: str) -> str | None:
    row = db.execute(HEAD, (item,)).fetchone()
    return None if row is None else str(row[0])


def _entries(fields: dict[str, object], key: str) -> list[dict[str, object]]:
    found = fields.get(key)
    if not isinstance(found, list):
        return []
    return [
        cast(dict[str, object], entry)
        for entry in cast(list[object], found)
        if isinstance(entry, dict) and "start_ns" in entry and "end_ns" in entry
    ]


def _overlaps(read: dict[str, object], fixed: dict[str, object]) -> bool:
    """Whether a read range and a correction range share a moment (both half-open)."""
    try:
        read_start = int(read["start_ns"])  # type: ignore[arg-type]
        read_end = int(read["end_ns"])  # type: ignore[arg-type]
        fixed_start = int(fixed["start_ns"])  # type: ignore[arg-type]
        fixed_end = int(fixed["end_ns"])  # type: ignore[arg-type]
    except KeyError, TypeError, ValueError:
        return False
    return read_start < fixed_end and fixed_start < read_end


def _path_to(child_of: dict[str, str | None], start: str, node: str) -> tuple[str, ...]:
    """The walk from ``start`` down to ``node``, in that order."""
    path: list[str] = []
    here: str | None = node
    while here is not None:
        path.append(here)
        here = child_of.get(here)
    return tuple(reversed(path))


def _range_correction(
    db: sqlite3.Connection,
    start: str,
    child_of: dict[str, str | None],
    seen: dict[str, _Object | None],
) -> str | None:
    """The nearest series card whose correction range overlaps a read along the path."""
    candidates: list[tuple[int, str]] = []
    for node in child_of:
        carried = _cached(seen, db, node)
        if carried is None or not carried.series:
            continue
        head = _head(db, carried.item) or node
        head_object = _cached(seen, db, head)
        if head_object is None:
            continue
        corrections = _entries(head_object.fields, "corrections")
        if not corrections:
            continue
        path = _path_to(child_of, start, node)
        readers = [entry for key in path if (entry := _cached(seen, db, key)) is not None]
        overlaps = any(
            _overlaps(read, correction)
            for reader in readers
            for read in _entries(reader.fields, "reads")
            if read.get("series") == carried.series
            for correction in corrections
        )
        if overlaps:
            candidates.append((len(path), node))
    if not candidates:
        return None
    return min(candidates)[1]


def marks(db: sqlite3.Connection, object_id: ObjectId) -> Marks:
    """The worst mark on `object_id` or upstream of it, and the path that carries it."""
    child_of: dict[str, str | None] = {}
    seen: dict[str, _Object | None] = {}
    worst: Mark | None = None
    at, why = "", ""
    for node, child, stored, reason, superseded, replaced in db.execute(
        WALK, {"start": object_id, **PARAMS}
    ):
        child_of.setdefault(node, child)
        held = _cached(seen, db, str(node))
        same_series = False
        if superseded and held is not None and held.series:
            head = _head(db, held.item)
            head_object = None if head is None else _cached(seen, db, head)
            same_series = head_object is not None and head_object.series == held.series
        found: Mark | None = (
            "quarantined"
            if stored == QUARANTINED
            else "corrected"
            if replaced
            else "superseded"
            if superseded and not same_series
            else None
        )
        if RANK[found] > RANK[worst]:
            worst, at, why = found, str(node), str(reason or "")
    if worst is None:
        corrected_at = _range_correction(db, object_id, child_of, seen)
        if corrected_at is not None:
            worst, at = "corrected", corrected_at
    if worst is None:
        return Marks(None, ())
    return Marks(worst, _path_to(child_of, object_id, at), why if worst == QUARANTINED else "")
