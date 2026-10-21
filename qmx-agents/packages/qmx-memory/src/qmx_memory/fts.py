"""FTS5 over the same rows: the backup that answers when Hindsight is stopped (AD-18, ruling 119).

The table is derived data. It holds each row's own words and the tags a read filters on, and a
rebuild wipes it and re-indexes the live Library rows, so a lost or swapped engine costs nothing.

A query is read as words, each quoted, joined by OR: that keeps a model's punctuation out of
FTS5's own grammar and ranks a row holding more of the words first.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from collections.abc import Iterable, Sequence
from pathlib import Path

from qmx_memory.rows import MemoryRow

WORDS = re.compile(r"[^\W_]+", re.UNICODE)
TOP = 50
"""Rows a fallback read scores before the engine filters them."""

SCHEMA = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5("
    "row_id UNINDEXED, item UNINDEXED, text, tags UNINDEXED, tokenize='porter unicode61')"
)


def terms(query: str) -> list[str]:
    """The words of a query, in order, deduplicated."""
    return list(dict.fromkeys(found.lower() for found in WORDS.findall(query)))


class FtsIndex:
    """One SQLite file beside the home, holding the fallback index. The host writes and reads it
    from worker threads, so one connection serves them all behind one lock."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(SCHEMA)

    @classmethod
    def open(cls, path: Path) -> FtsIndex:
        return cls(path)

    def close(self) -> None:
        with self.lock:
            self.db.close()

    def index(self, rows: Iterable[MemoryRow]) -> int:
        """Add or replace each row by object id; returns how many were written."""
        found = list(rows)
        with self.lock:
            for row in found:
                self.db.execute("DELETE FROM memory_fts WHERE row_id = ?", (row.object_id,))
                self.db.execute(
                    "INSERT INTO memory_fts (row_id, item, text, tags) VALUES (?, ?, ?, ?)",
                    (row.object_id, row.item, row.indexed(), " ".join(row.tags())),
                )
            self.db.commit()
        return len(found)

    def forget(self, row_ids: Sequence[str], rows: Iterable[MemoryRow] = ()) -> int:
        """Delete rows from the index. A forgotten row is gone until something retains it again.
        `rows` is the adapter contract's re-index fallback; this index always deletes by id."""
        del rows
        removed = 0
        with self.lock:
            for row_id in row_ids:
                cursor = self.db.execute("DELETE FROM memory_fts WHERE row_id = ?", (row_id,))
                removed += cursor.rowcount if cursor.rowcount > 0 else 0
            self.db.commit()
        return removed

    def rebuild(self, rows: Iterable[MemoryRow]) -> int:
        found = list(rows)
        with self.lock:
            self.db.execute("DELETE FROM memory_fts")
            self.db.executemany(
                "INSERT INTO memory_fts (row_id, item, text, tags) VALUES (?, ?, ?, ?)",
                [(r.object_id, r.item, r.indexed(), " ".join(r.tags())) for r in found],
            )
            self.db.commit()
        return len(found)

    def recall(
        self, query: str, tags: Sequence[str] = (), limit: int = TOP
    ) -> list[tuple[str, float]]:
        """`(row_id, score)` best first, from 1 down: bm25 is negative and better when smaller.
        `tags` is the engine's filter to apply: FTS5 ranks the words and the engine keeps what
        the read asked for, so both indexes answer the same question the same way."""
        del tags
        words = terms(query)
        if not words:
            return []
        asked = " OR ".join(f'"{word}"' for word in words)
        with self.lock:
            found = self.db.execute(
                "SELECT row_id, bm25(memory_fts) AS rank FROM memory_fts "
                "WHERE memory_fts MATCH ? ORDER BY rank, row_id LIMIT ?",
                (asked, limit),
            ).fetchall()
        return [(str(row), 1.0 / (1.0 + abs(float(rank)))) for row, rank in found]

    def count(self) -> int:
        with self.lock:
            (found,) = self.db.execute("SELECT count(*) FROM memory_fts").fetchone()
        return int(found)
