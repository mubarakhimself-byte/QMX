"""`catalog.db`, the Library's rebuildable index (Library AD-5, LLD section 4).

Nothing here is evidence. Every row is derived from the store's files (objects, the ref log, the
edge log and the annotation log) by the same `index_*` calls the writer makes after each commit,
so `rebuild` is a replay of the evidence through them. The file may be deleted at any time.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from collections.abc import Collection, Generator, Iterable, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Final, cast

from pydantic import JsonValue

from qmx_library.port import Hit, JsonObject, LibraryRefused, Producer, Role

TRUST: Final[Mapping[Producer, int]] = {
    "live-run": 3,
    "operator": 2,
    "agent": 1,
    "run": 1,
    "test-run": 0,
}
"""Library AD-8 (7): a passed live run, then his own items, then drafts and unfinished runs, then
test runs, so fan-out test output ranks below trusted results."""

SCHEMA: Final = """
CREATE TABLE IF NOT EXISTS objects (
    object_id TEXT PRIMARY KEY, item TEXT NOT NULL, kind TEXT NOT NULL, class TEXT NOT NULL,
    title TEXT NOT NULL, summary TEXT NOT NULL, fields TEXT NOT NULL, blobs TEXT NOT NULL,
    parents TEXT NOT NULL, relations TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS objects_item ON objects (item, kind);
CREATE TABLE IF NOT EXISTS moves (
    seq INTEGER PRIMARY KEY, item TEXT NOT NULL, ref TEXT NOT NULL, principal TEXT NOT NULL,
    prev_head TEXT, new_head TEXT NOT NULL, at TEXT NOT NULL, reason TEXT, replaced_by TEXT
);
CREATE INDEX IF NOT EXISTS moves_head ON moves (new_head);
CREATE INDEX IF NOT EXISTS moves_item ON moves (item, ref);
CREATE TABLE IF NOT EXISTS heads (
    item TEXT NOT NULL, ref TEXT NOT NULL, head TEXT NOT NULL, revision INTEGER NOT NULL,
    PRIMARY KEY (item, ref)
);
CREATE TABLE IF NOT EXISTS items (
    item TEXT PRIMARY KEY, kind TEXT NOT NULL, state TEXT NOT NULL, reason TEXT, replaced_by TEXT
);
CREATE TABLE IF NOT EXISTS relations (
    from_id TEXT NOT NULL, type TEXT NOT NULL, to_id TEXT NOT NULL, origin TEXT NOT NULL,
    edge_id TEXT, writer TEXT, at TEXT, seq INTEGER,
    PRIMARY KEY (from_id, type, to_id, origin)
);
CREATE INDEX IF NOT EXISTS relations_to ON relations (to_id, type);
CREATE TABLE IF NOT EXISTS annotations (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, object_id TEXT NOT NULL, key TEXT NOT NULL,
    value TEXT NOT NULL, principal TEXT NOT NULL, at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS annotations_object ON annotations (object_id, key);
CREATE TABLE IF NOT EXISTS aliases (
    alias TEXT NOT NULL, item TEXT NOT NULL, PRIMARY KEY (alias, item)
);
CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5 (
    object_id UNINDEXED, item UNINDEXED, kind UNINDEXED, title, tags, text,
    tokenize = 'unicode61'
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

WORD: Final = re.compile(r"\w+", re.UNICODE)


def norm(text: str) -> str:
    """Lower case, accents folded, every run of non-word characters one space."""
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(WORD.findall(folded.lower()))


def strings(value: JsonValue) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for inner in value.values():
            yield from strings(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from strings(inner)


class Catalog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.db.execute("PRAGMA journal_mode = WAL")
        self.db.execute("PRAGMA synchronous = NORMAL")
        self.db.executescript(SCHEMA)

    def close(self) -> None:
        self.db.close()

    @contextmanager
    def batch(self) -> Generator[None]:
        self.db.execute("BEGIN")
        try:
            yield
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        self.db.execute("COMMIT")

    def stamp(self) -> str | None:
        row = self.db.execute("SELECT value FROM meta WHERE key = 'evidence'").fetchone()
        return None if row is None else str(row[0])

    def set_stamp(self, stamp: str) -> None:
        self.db.execute(
            "INSERT INTO meta (key, value) VALUES ('evidence', ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (stamp,),
        )

    def index_object(
        self, object_id: str, manifest: Mapping[str, Any], klass: str, text: str
    ) -> None:
        item, kind = str(manifest["item_id"]), str(manifest["kind"])
        title, summary = str(manifest["title"]), str(manifest["summary"])
        inserted = self.db.execute(
            "INSERT OR IGNORE INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                object_id,
                item,
                kind,
                klass,
                title,
                summary,
                json.dumps(manifest["fields"]),
                json.dumps(manifest["blobs"]),
                json.dumps(manifest["parents"]),
                json.dumps(manifest["relations"]),
            ),
        ).rowcount
        if not inserted:
            return
        self.db.execute(
            "INSERT OR IGNORE INTO items (item, kind, state) VALUES (?, ?, 'active')", (item, kind)
        )
        body = " ".join([summary, *strings(cast(JsonValue, manifest["fields"])), text])
        self.db.execute(
            "INSERT INTO search (object_id, item, kind, title, tags, text) "
            "VALUES (?, ?, ?, ?, '', ?)",
            (object_id, item, kind, title, body),
        )
        self._alias(title, item)
        for relation in cast(list[dict[str, str]], manifest["relations"]):
            self.db.execute(
                "INSERT OR IGNORE INTO relations (from_id, type, to_id, origin) "
                "VALUES (?, ?, ?, 'birth')",
                (object_id, relation["type"], relation["to"]),
            )

    def _alias(self, text: str, item: str) -> None:
        alias = norm(text)
        if alias:
            self.db.execute("INSERT OR IGNORE INTO aliases VALUES (?, ?)", (alias, item))

    def index_move(self, move: Mapping[str, Any]) -> None:
        seq, item, ref, new = (
            int(move["seq"]),
            str(move["item"]),
            str(move["ref"]),
            move["new_head"],
        )
        self.db.execute(
            "INSERT OR IGNORE INTO moves VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                seq,
                item,
                ref,
                move["principal"],
                move.get("prev_head"),
                new,
                move["at"],
                move.get("reason"),
                move.get("replaced_by"),
            ),
        )
        self.db.execute(
            "INSERT INTO heads (item, ref, head, revision) VALUES (?, ?, ?, 1) "
            "ON CONFLICT (item, ref) DO UPDATE SET head = excluded.head, revision = revision + 1",
            (item, ref, new),
        )
        if ref == f"refs/items/{item}/state":
            self.db.execute(
                "UPDATE items SET state = ?, reason = ?, replaced_by = ? WHERE item = ?",
                (new, move.get("reason"), move.get("replaced_by"), item),
            )

    def index_edge(self, edge: Mapping[str, Any]) -> None:
        self.db.execute(
            "INSERT OR IGNORE INTO relations VALUES (?, ?, ?, 'edge', ?, ?, ?, ?)",
            (
                edge["from"],
                edge["type"],
                edge["to"],
                edge["edge_id"],
                edge["writer"],
                edge["at"],
                edge["seq"],
            ),
        )

    def index_annotation(self, entry: Mapping[str, Any]) -> None:
        object_id = str(entry["object_id"])
        for key, value in cast(dict[str, JsonValue], entry["values"]).items():
            self.db.execute(
                "INSERT INTO annotations (object_id, key, value, principal, at) "
                "VALUES (?, ?, ?, ?, ?)",
                (object_id, key, json.dumps(value), entry["principal"], entry["at"]),
            )
            row = self.db.execute("SELECT item FROM objects WHERE object_id = ?", (object_id,))
            found = row.fetchone()
            if found is None:
                continue
            if key == "tags" and isinstance(value, list):
                self.db.execute(
                    "UPDATE search SET tags = ? WHERE object_id = ?",
                    (" ".join(map(str, value)), object_id),
                )
            if key in ("tags", "aliases") and isinstance(value, list):
                for alias in value:
                    self._alias(str(alias), str(found[0]))

    def head(self, item: str, ref: str) -> tuple[str, int] | None:
        row = self.db.execute(
            "SELECT head, revision FROM heads WHERE item = ? AND ref = ?", (item, ref)
        ).fetchone()
        return None if row is None else (str(row[0]), int(row[1]))

    def heads_on(self, ref: str) -> list[tuple[str, str]]:
        rows = self.db.execute("SELECT item, head FROM heads WHERE ref = ? ORDER BY item", (ref,))
        return [(str(item), str(head)) for item, head in rows]

    def refs_like(self, prefix: str) -> int:
        (count,) = self.db.execute(
            "SELECT count(DISTINCT ref) FROM heads WHERE ref LIKE ? ESCAPE '\\'",
            (prefix.replace("_", "\\_").replace("%", "\\%") + "%",),
        ).fetchone()
        return int(count)

    def last_seq(self) -> int:
        (seq,) = self.db.execute("SELECT coalesce(max(seq), 0) FROM moves").fetchone()
        return int(seq)

    def row(self, object_id: str) -> tuple[Any, ...] | None:
        return self.db.execute(
            "SELECT object_id, item, kind, class, title, summary, fields, blobs, parents, "
            "relations FROM objects WHERE object_id = ?",
            (object_id,),
        ).fetchone()

    def parents(self, object_id: str) -> list[str]:
        row = self.db.execute("SELECT parents FROM objects WHERE object_id = ?", (object_id,))
        found = row.fetchone()
        return [] if found is None else cast(list[str], json.loads(found[0]))

    def annotations(self, object_id: str) -> JsonObject:
        rows = self.db.execute(
            "SELECT key, value FROM annotations WHERE object_id = ? ORDER BY seq", (object_id,)
        )
        return {str(key): json.loads(value) for key, value in rows}

    def state(self, item: str) -> str | None:
        row = self.db.execute("SELECT state FROM items WHERE item = ?", (item,)).fetchone()
        return None if row is None else str(row[0])

    def search(self, text: str, kind: str | None, include_archived: bool, limit: int) -> list[Hit]:
        words = norm(text).split()
        if not words:
            raise LibraryRefused("invalid_search", "the search names no word")
        query = " ".join(f'"{word}"' for word in words)
        rows = self.db.execute(
            "SELECT s.object_id, s.item, s.kind, s.title, bm25(search) AS rank "
            "FROM search s JOIN items i ON i.item = s.item "
            "WHERE search MATCH ? AND (? IS NULL OR s.kind = ?) AND (? OR i.state = 'active') "
            "ORDER BY rank, s.item, s.object_id",
            (query, kind, kind, include_archived),
        )
        best: dict[str, Hit] = {}
        for object_id, item, found_kind, title, rank in rows:
            if item not in best:
                best[str(item)] = Hit(str(object_id), str(item), str(found_kind), str(title), -rank)
        return self.trusted_first(list(best.values()))[:limit]

    def trusted_first(self, hits: list[Hit]) -> list[Hit]:
        """Stable: hits of equal trust keep their text rank."""
        trust = {h.object_id: TRUST[self.producer(h.object_id)] for h in hits}
        return sorted(hits, key=lambda h: -trust[h.object_id])

    def relations_of(self, object_id: str, *, reverse: bool) -> list[tuple[str, str, str]]:
        mine, other = ("to_id", "from_id") if reverse else ("from_id", "to_id")
        rows = self.db.execute(
            f"SELECT {other}, type, origin FROM relations WHERE {mine} = ? "  # noqa: S608
            "ORDER BY coalesce(seq, 0)",
            (object_id,),
        )
        return [(str(a), str(b), str(c)) for a, b, c in rows]

    def aliases(self) -> list[tuple[str, str]]:
        rows = self.db.execute("SELECT alias, item FROM aliases ORDER BY length(alias) DESC")
        return [(str(alias), str(item)) for alias, item in rows]

    def matching(self, spans: Collection[str]) -> list[tuple[str, str, Role]]:
        """`(span, item, role)` for each span that is an item's title, tag or alias (`bridge`), or
        the kind, or the old Library's kind, of an item (`filter`)."""
        if not spans:
            return []
        marks = ", ".join("?" * len(spans))
        kind = "replace(replace({}, '-', ' '), '_', ' ')"
        rows = self.db.execute(
            f"SELECT alias, item, 'bridge' FROM aliases WHERE alias IN ({marks}) "  # noqa: S608
            f"UNION SELECT {kind.format('kind')}, item, 'filter' FROM items "
            f"WHERE {kind.format('kind')} IN ({marks}) "
            f"UNION SELECT {kind.format("json_extract(fields, '$.legacy_kind')")}, item, 'filter' "
            f"FROM objects WHERE {kind.format("json_extract(fields, '$.legacy_kind')")} "
            f"IN ({marks})",
            [*spans, *spans, *spans],
        )
        return [(str(span), str(item), cast(Role, role)) for span, item, role in rows]

    def producer(self, object_id: str) -> Producer:
        """From the ref that first placed the object and, for a run's ref, that run's summary."""
        row = self.db.execute(
            "SELECT ref FROM moves WHERE new_head = ? ORDER BY seq LIMIT 1", (object_id,)
        ).fetchone()
        ref = "" if row is None else str(row[0])
        if ref.startswith("refs/agents/"):
            return "agent"
        if not ref.startswith("refs/runs/"):
            return "operator"
        run = self.db.execute(
            "SELECT json_extract(o.fields, '$.mode'), json_extract(o.fields, '$.status') "
            "FROM moves m JOIN objects o ON o.object_id = m.new_head "
            "WHERE m.item = ? AND m.ref = ? AND o.kind = 'workflow-run' "
            "ORDER BY m.seq DESC LIMIT 1",
            (ref.removeprefix("refs/runs/"), ref),
        ).fetchone()
        if run is not None and run[0] == "test":
            return "test-run"
        if run is not None and run[1] == "passed":
            return "live-run"
        return "run"

    def citations(self, item: str) -> int:
        """Relations into any object of `item` from objects of other active items."""
        (count,) = self.db.execute(
            "SELECT count(*) FROM relations r JOIN objects t ON t.object_id = r.to_id "
            "JOIN objects f ON f.object_id = r.from_id JOIN items i ON i.item = f.item "
            "WHERE t.item = ? AND f.item <> t.item AND i.state = 'active'",
            (item,),
        ).fetchone()
        return int(count)

    def texts(self, object_ids: Sequence[str]) -> dict[str, str]:
        """Indexed text by object, in one pass: `object_id` is an unindexed FTS5 column, so each
        lookup scans the table."""
        found: dict[str, str] = {}
        for start in range(0, len(object_ids), 900):
            chunk = object_ids[start : start + 900]
            marks = ", ".join("?" * len(chunk))
            rows = self.db.execute(
                f"SELECT object_id, text FROM search WHERE object_id IN ({marks})",  # noqa: S608
                chunk,
            )
            found.update((str(o), str(t)) for o, t in rows)
        return found

    def placed_seq(self, object_id: str) -> int:
        """The ref-log position of the latest move onto the object, 0 if none."""
        (seq,) = self.db.execute(
            "SELECT coalesce(max(seq), 0) FROM moves WHERE new_head = ?", (object_id,)
        ).fetchone()
        return int(seq)

    def placed_refs(self, item: str) -> list[str]:
        """The refs that ever held an object of `item`, most recently moved first."""
        rows = self.db.execute(
            "SELECT ref FROM moves WHERE item = ? AND ref NOT LIKE 'refs/items/%' "
            "GROUP BY ref ORDER BY max(seq) DESC",
            (item,),
        )
        return [str(ref) for (ref,) in rows]
