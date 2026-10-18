"""The Library port backed by one SQLite file, `<qmx_home>/engine/library-fake.sqlite`, until the
Library agent's store answers (ruling 91 holds real data work).

Objects, blobs, edges and annotations are append-only and refs only move: SQL triggers refuse
every DELETE, and every UPDATE outside `refs`, so nothing is ever deleted (AD-14) even through raw
SQL. The kind and edge columns carry `CHECK`s over the closed sets. A write onto
`refs/runs/<run_id>` must carry the principal `run:<run_id>` (Library AD-7). The fake's merge into
`main` is always a fast-forward, so a published version keeps its draft's content hash and always
gets the draft's `tested-by` edges.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from types import TracebackType
from typing import Any, Final, Self, cast

from pydantic import JsonValue
from qmx_ledger.journal import encoded, fingerprint

from qmx_engine.ports.library import (
    EDGES,
    KINDS,
    MAIN,
    Bundle,
    Draft,
    Edge,
    EdgeName,
    JsonObject,
    Kind,
    LibraryEvent,
    LibraryRefused,
    RunSummary,
    Stored,
    champions_ref,
    drafts_ref,
    is_draft_ref,
    runs_ref,
)

APPEND_ONLY: Final = ("blobs", "objects", "edges", "annotations")


def _quoted(names: frozenset[str]) -> str:
    return ", ".join(f"'{name}'" for name in sorted(names))


SCHEMA: Final = (
    f"""
CREATE TABLE IF NOT EXISTS blobs (hash TEXT PRIMARY KEY, data BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS objects (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL CHECK (kind IN ({_quoted(KINDS)})),
    item TEXT NOT NULL,
    ref TEXT NOT NULL,
    fields TEXT NOT NULL,
    blob TEXT,
    principal TEXT NOT NULL,
    at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS refs (
    ref TEXT NOT NULL,
    item TEXT NOT NULL,
    object_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    PRIMARY KEY (ref, item)
);
CREATE TABLE IF NOT EXISTS edges (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id TEXT NOT NULL,
    edge TEXT NOT NULL CHECK (edge IN ({_quoted(EDGES)})),
    to_id TEXT NOT NULL,
    principal TEXT NOT NULL,
    at TEXT NOT NULL,
    UNIQUE (from_id, edge, to_id)
);
CREATE TABLE IF NOT EXISTS annotations (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    principal TEXT NOT NULL,
    at TEXT NOT NULL
);
"""
    + "".join(
        f"""
CREATE TRIGGER IF NOT EXISTS {table}_never_deleted BEFORE DELETE ON {table}
BEGIN SELECT RAISE(ABORT, 'the Library never deletes (AD-14)'); END;"""
        for table in (*APPEND_ONLY, "refs")
    )
    + "".join(
        f"""
CREATE TRIGGER IF NOT EXISTS {table}_append_only BEFORE UPDATE ON {table}
BEGIN SELECT RAISE(ABORT, 'the Library is append-only (AD-14)'); END;"""
        for table in APPEND_ONLY
    )
)

COLUMNS: Final = "object_id, kind, item, ref, fields, principal, at, blob"


def library_path(home: Path) -> Path:
    return home / "engine" / "library-fake.sqlite"


def _stored(row: tuple[object, ...]) -> Stored:
    object_id, kind, item, ref, fields, principal, at, blob = row
    return Stored(
        str(object_id),
        cast(Kind, kind),
        str(item),
        str(ref),
        json.loads(str(fields)),
        str(principal),
        str(at),
        None if blob is None else str(blob),
    )


class LibraryFake:
    def __init__(self, path: Path, *, wall: Callable[[], datetime] | None = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.wall = wall or (lambda: datetime.now(UTC))
        self.db = sqlite3.connect(path)
        self.db.executescript(SCHEMA)

    @classmethod
    def open(cls, home: Path, *, wall: Callable[[], datetime] | None = None) -> LibraryFake:
        return cls(library_path(home), wall=wall)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self.db.close()

    def _blob(self, data: bytes) -> str:
        digest = f"sha256:{sha256(data).hexdigest()}"
        self.db.execute("INSERT OR IGNORE INTO blobs (hash, data) VALUES (?, ?)", (digest, data))
        return digest

    def _put(
        self,
        kind: Kind,
        item: str,
        ref: str,
        fields: JsonObject,
        principal: str,
        blob: str | None = None,
    ) -> Stored:
        if ref.startswith("refs/runs/") and principal != f"run:{ref.removeprefix('refs/runs/')}":
            raise LibraryRefused("wrong_principal", f"only the run itself writes on {ref}")
        (count,) = self.db.execute("SELECT count(*) FROM objects").fetchone()
        object_id = f"obj-{fingerprint([kind, item, ref, fields, blob, count])[:24]}"
        stored = Stored(
            object_id, kind, item, ref, fields, principal, self.wall().isoformat(), blob
        )
        self.db.execute(
            f"INSERT INTO objects ({COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",  # noqa: S608
            (object_id, kind, item, ref, json.dumps(fields), principal, stored.at, blob),
        )
        return stored

    def _move(self, ref: str, item: str, object_id: str) -> int:
        head = self._head(ref, item)
        revision = (head[1] if head else 0) + 1
        self.db.execute(
            "INSERT INTO refs (ref, item, object_id, revision) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (ref, item) DO UPDATE SET object_id = excluded.object_id, "
            "revision = excluded.revision",
            (ref, item, object_id, revision),
        )
        return revision

    def _head(self, ref: str, item: str) -> tuple[str, int] | None:
        row = self.db.execute(
            "SELECT object_id, revision FROM refs WHERE ref = ? AND item = ?", (ref, item)
        ).fetchone()
        return None if row is None else (str(row[0]), int(row[1]))

    def _bundle(self, stored: Stored) -> Bundle:
        if stored.kind != "workflow" or stored.blob is None:
            raise LibraryRefused("not_a_workflow", f"{stored.object_id} is a {stored.kind}")
        body = json.loads(self.get_artifact(stored.blob))
        files = {ref: self.get_artifact(digest) for ref, digest in body["files"].items()}
        return Bundle(body["definition"], files)

    def _store_bundle(self, bundle: Bundle) -> str:
        files = {ref: self._blob(data) for ref, data in sorted(bundle.files.items())}
        return self._blob(encoded({"definition": bundle.definition, "files": files}))

    def get(self, object_id: str) -> Stored:
        row = self.db.execute(
            f"SELECT {COLUMNS} FROM objects WHERE object_id = ?",  # noqa: S608
            (object_id,),
        ).fetchone()
        if row is None:
            raise LibraryRefused("unknown_object", f"no object {object_id}")
        return _stored(row)

    def get_object(self, object_id: str) -> Bundle:
        return self._bundle(self.get(object_id))

    def get_draft(self, item: str, ref: str) -> Draft:
        head = self._head(ref, item)
        if head is None or not is_draft_ref(ref):
            raise LibraryRefused("no_draft", f"no draft of {item} on {ref}")
        stored = self.get(head[0])
        bundle = self._bundle(stored)
        found = stored.fields.get("content_hash")
        return Draft(
            item, ref, stored.object_id, head[1], bundle, found if isinstance(found, str) else None
        )

    def put_draft(
        self,
        item: str | None,
        bundle: Bundle,
        expected_revision: int,
        *,
        principal: str,
        ref: str | None = None,
        fields: JsonObject | None = None,
    ) -> Draft:
        if ref is not None and not is_draft_ref(ref):
            raise LibraryRefused("not_a_draft_ref", f"a draft never lands on {ref}")
        with self.db:
            if item is None:
                item = self._new_item(str(bundle.definition.get("id") or "workflow"))
            ref = ref or drafts_ref(item)
            head = self._head(ref, item)
            if (head[1] if head else 0) != expected_revision:
                raise LibraryRefused(
                    "revision_conflict",
                    f"{ref} is at revision {head[1] if head else 0}, not {expected_revision}",
                )
            digest = bundle.content_hash()
            stored = self._put(
                "workflow",
                item,
                ref,
                {**(fields or {}), "content_hash": digest, "revision": expected_revision + 1},
                principal,
                self._store_bundle(bundle),
            )
            revision = self._move(ref, item, stored.object_id)
        return Draft(item, ref, stored.object_id, revision, bundle, digest)

    def _new_item(self, base: str) -> str:
        taken = {str(r[0]) for r in self.db.execute("SELECT DISTINCT item FROM objects")}
        item, n = base, 2
        while item in taken:
            item, n = f"{base}-{n}", n + 1
        return item

    def publish(self, item: str, from_ref: str, semver: str, *, principal: str) -> str:
        draft = self.get_draft(item, from_ref)
        if draft.content_hash is None:
            raise LibraryRefused("unresolved_variant", "resolve the variant before publishing")
        versions = self.objects(item, "workflow", MAIN)
        for version in versions:
            if version.fields.get("content_hash") == draft.content_hash:
                return version.object_id
        if any(v.fields.get("semver") == semver for v in versions):
            raise LibraryRefused("semver_taken", f"{item} already has a version {semver}")
        source = self.get(draft.object_id)
        with self.db:
            fields: JsonObject = {
                "content_hash": draft.content_hash,
                "semver": semver,
                "from_draft": draft.object_id,
            }
            stored = self._put("workflow", item, MAIN, fields, principal, source.blob)
            self._move(MAIN, item, stored.object_id)
            for edge in self.edges(draft.object_id, "tested-by"):
                self._link(stored.object_id, "tested-by", edge.to_id, principal)
        return stored.object_id

    def land_draft(self, item: str, from_run: str, *, principal: str) -> str:
        made = self.objects(item, "workflow", runs_ref(from_run))
        if not made:
            raise LibraryRefused("unknown_object", f"run {from_run} made no {item}")
        ref = drafts_ref(item)
        head = self._head(ref, item)
        with self.db:
            fields = {**made[-1].fields, "revision": (head[1] if head else 0) + 1}
            stored = self._put("workflow", item, ref, fields, principal, made[-1].blob)
            self._move(ref, item, stored.object_id)
        return stored.object_id

    def put_artifact(
        self,
        data: bytes,
        type_: str,
        metadata: JsonObject,
        *,
        run_id: str,
        principal: str,
        intent_key: str | None = None,
    ) -> Stored:
        with self.db:
            digest = self._blob(data)
            fields: JsonObject = {"type": type_, "metadata": metadata, "intent_key": intent_key}
            return self._put("artifact", digest, runs_ref(run_id), fields, principal, digest)

    def get_artifact(self, blob: str) -> bytes:
        row = self.db.execute("SELECT data FROM blobs WHERE hash = ?", (blob,)).fetchone()
        if row is None:
            raise LibraryRefused("unknown_blob", f"no blob {blob}")
        return bytes(row[0])

    def put_run_summary(self, summary: RunSummary, *, principal: str) -> Stored:
        with self.db:
            fields = cast(JsonObject, asdict(summary))
            return self._put(
                "workflow-run", summary.run_id, runs_ref(summary.run_id), fields, principal
            )

    def put_test_report(self, draft_hash: str, report: JsonObject, *, principal: str) -> Stored:
        item, run_id = str(report["workflow_item"]), str(report["run_id"])
        with self.db:
            fields: JsonObject = {**report, "content_hash": draft_hash}
            return self._put("test-report", item, runs_ref(run_id), fields, principal)

    def put_checkpoint(
        self, run_id: str, node_id: str, attempt: int, data: bytes, *, principal: str
    ) -> str:
        with self.db:
            digest = self._blob(data)
            fields: JsonObject = {"slot": f"checkpoints/{node_id}/{attempt}", "class": "transient"}
            self._put("checkpoint", run_id, runs_ref(run_id), fields, principal, digest)
        return digest

    def put_agent_tool(self, run_id: str, tool: JsonObject, *, principal: str) -> Stored:
        with self.db:
            fields: JsonObject = {**tool, "review": "unreviewed"}
            return self._put(
                "agent-tool", str(tool.get("name")), runs_ref(run_id), fields, principal
            )

    def put_memory_row(self, run_id: str, row: JsonObject, *, principal: str) -> Stored:
        with self.db:
            fields: JsonObject = {**row, "scope": "run"}
            return self._put("memory-row", run_id, runs_ref(run_id), fields, principal)

    def link(self, from_id: str, edge: EdgeName, to_id: str, *, principal: str) -> None:
        with self.db:
            self._link(from_id, edge, to_id, principal)

    def _link(self, from_id: str, edge: EdgeName, to_id: str, principal: str) -> None:
        if edge not in EDGES:
            raise LibraryRefused("edge_not_in_set", f"{edge} is not one of {sorted(EDGES)}")
        self.get(from_id)
        self.get(to_id)
        self.db.execute(
            "INSERT OR IGNORE INTO edges (from_id, edge, to_id, principal, at) "
            "VALUES (?, ?, ?, ?, ?)",
            (from_id, edge, to_id, principal, self.wall().isoformat()),
        )

    def find_by_intent(self, intent_key: str) -> list[str]:
        rows = self.db.execute(
            "SELECT o.object_id FROM objects o JOIN edges e ON e.from_id = o.object_id "
            "AND e.edge = 'produced-by' JOIN objects r ON r.object_id = e.to_id "
            "WHERE json_extract(o.fields, '$.intent_key') = ? "
            "AND json_extract(r.fields, '$.status') = 'passed' ORDER BY o.seq",
            (intent_key,),
        )
        return [str(row[0]) for row in rows]

    def list_runs(self, workflow_item: str, object_id: str | None = None) -> list[RunSummary]:
        latest: dict[str, RunSummary] = {}
        rows = self.db.execute(
            f"SELECT {COLUMNS} FROM objects WHERE kind = 'workflow-run' "  # noqa: S608
            "AND json_extract(fields, '$.workflow_item') = ? ORDER BY seq",
            (workflow_item,),
        )
        for row in rows:
            summary = RunSummary(**cast(dict[str, Any], _stored(row).fields))
            if object_id is None or summary.object_id == object_id:
                latest[summary.run_id] = summary
        return list(latest.values())

    def champion(self, workflow_item: str) -> str | None:
        head = self._head(champions_ref(workflow_item), workflow_item)
        return None if head is None else head[0]

    def set_champion(self, workflow_item: str, object_id: str, *, principal: str) -> None:
        self.get(object_id)
        with self.db:
            self._move(champions_ref(workflow_item), workflow_item, object_id)

    def events(self, after: int = 0) -> list[LibraryEvent]:
        rows = self.db.execute(
            "SELECT seq, kind, object_id, ref FROM objects WHERE seq > ? ORDER BY seq", (after,)
        )
        return [
            LibraryEvent(int(seq), f"library.{kind}.created", str(object_id), str(ref))
            for seq, kind, object_id, ref in rows
        ]

    def edges(
        self, object_id: str, edge: EdgeName | None = None, *, reverse: bool = False
    ) -> list[Edge]:
        mine = "to_id" if reverse else "from_id"
        rows = self.db.execute(
            f"SELECT from_id, edge, to_id, principal, at FROM edges WHERE {mine} = ? "  # noqa: S608
            "AND (? IS NULL OR edge = ?) ORDER BY seq",
            (object_id, edge, edge),
        )
        return [Edge(str(a), cast(EdgeName, b), str(c), str(d), str(e)) for a, b, c, d, e in rows]

    def objects(self, item: str, kind: Kind, ref: str | None = None) -> list[Stored]:
        rows = self.db.execute(
            f"SELECT {COLUMNS} FROM objects WHERE item = ? AND kind = ? "  # noqa: S608
            "AND (? IS NULL OR ref = ?) ORDER BY seq",
            (item, kind, ref, ref),
        )
        return [_stored(row) for row in rows]

    def annotate(self, object_id: str, key: str, value: JsonValue, *, principal: str) -> None:
        self.get(object_id)
        with self.db:
            self.db.execute(
                "INSERT INTO annotations (object_id, key, value, principal, at) "
                "VALUES (?, ?, ?, ?, ?)",
                (object_id, key, json.dumps(value), principal, self.wall().isoformat()),
            )

    def annotation(self, object_id: str, key: str) -> JsonValue:
        row = self.db.execute(
            "SELECT value FROM annotations WHERE object_id = ? AND key = ? "
            "ORDER BY seq DESC LIMIT 1",
            (object_id, key),
        ).fetchone()
        return None if row is None else json.loads(row[0])
