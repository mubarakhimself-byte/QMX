"""Marks, derived at read (Library AD-22).

One mark is stored: `quarantined`, with a reason, on `refs/items/<item_id>/marks`, set or cleared
by the operator alone (`Store.mark`). Two more are computed and never stored: `superseded` (the
object is no longer the head of its item's `main`) and `corrected` (a `replaces` edge points at
it). `marks(object_id)` walks upstream from the object shown, along `consumed`, `derived-from` and
`uses` out of each object and `compiles-to` into it (a book's upstream is the pod compiled to
it), and returns the worst mark with the path that carries it. Nothing is written onto
descendants, so clearing a mark clears everything derived from it at once.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Final, Literal

from qmx_library.port import ObjectId

type Mark = Literal["superseded", "corrected", "quarantined"]

QUARANTINED: Final = "quarantined"
CLEAR: Final = "clear"
RANK: Final[dict[Mark | None, int]] = {None: 0, "superseded": 1, "corrected": 2, "quarantined": 3}
UPSTREAM_OUT: Final = ("consumed", "derived-from", "uses")
UPSTREAM_IN: Final = "compiles-to"

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
  EXISTS (SELECT 1 FROM relations r WHERE r.to_id = up.node AND r.type = 'replaces') AS corrected
FROM up
"""
PARAMS: Final = {"o0": UPSTREAM_OUT[0], "o1": UPSTREAM_OUT[1], "o2": UPSTREAM_OUT[2]} | {
    "i0": UPSTREAM_IN
}


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


def marks(db: sqlite3.Connection, object_id: ObjectId) -> Marks:
    """The worst mark on `object_id` or upstream of it, and the path that carries it."""
    child_of: dict[str, str | None] = {}
    worst: Mark | None = None
    at, why = "", ""
    for node, child, stored, reason, superseded, corrected in db.execute(
        WALK, {"start": object_id, **PARAMS}
    ):
        child_of.setdefault(node, child)
        found: Mark | None = (
            "quarantined"
            if stored == QUARANTINED
            else "corrected"
            if corrected
            else "superseded"
            if superseded
            else None
        )
        if RANK[found] > RANK[worst]:
            worst, at, why = found, str(node), str(reason or "")
    if worst is None:
        return Marks(None, ())
    path: list[str] = []
    here: str | None = at
    while here is not None:
        path.append(here)
        here = child_of[here]
    return Marks(worst, tuple(reversed(path)), why if worst == QUARANTINED else "")
