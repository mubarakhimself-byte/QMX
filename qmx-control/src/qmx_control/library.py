"""Immutable content blobs, version chains and full-text catalog search."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import uuid
from collections.abc import Callable, Generator
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from qmx_control.models import ControlError, Document, LibraryInput, MemoKey


def encoded(value: JsonValue) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


class Library:
    def __init__(self, home: Path) -> None:
        self.home = home
        home.mkdir(parents=True, exist_ok=True)
        self.blobs = home / "artifacts"
        self.blobs.mkdir(exist_ok=True)
        self.lock = threading.RLock()
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY, data TEXT NOT NULL,
                    root TEXT NOT NULL, version INTEGER NOT NULL, source TEXT NOT NULL,
                    fetched_date TEXT, UNIQUE(root,version));
                CREATE UNIQUE INDEX IF NOT EXISTS fetched_source ON items(source,fetched_date)
                    WHERE fetched_date IS NOT NULL;
                CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(id UNINDEXED,title,tags,text);
                CREATE TABLE IF NOT EXISTS links(source TEXT,target TEXT,relation TEXT,
                    PRIMARY KEY(source,target,relation));
                CREATE TABLE IF NOT EXISTS memo(key TEXT PRIMARY KEY,item_id TEXT NOT NULL);
            """)
        # The domain tools previously stored JSON envelopes by their envelope hash.
        for path in sorted(self.blobs.glob("*.json")):
            if not re.fullmatch(r"[0-9a-f]{64}\.json", path.name):
                continue
            body = path.read_bytes()
            if sha256(body).hexdigest() != path.stem:
                raise ControlError("corrupt_blob", "Artifact hash mismatch.", 409)
            legacy = cast(Document, json.loads(body))
            with self.connect() as db:
                if db.execute("SELECT 1 FROM items WHERE id=?", (path.stem,)).fetchone():
                    continue
            self.save(
                LibraryInput(title=str(legacy["name"]), kind=str(legacy["kind"]), content=legacy),
                item_id=path.stem,
            )

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.home / "library.db", timeout=5)) as db, db:
            yield db

    def save(self, item: LibraryInput, *, item_id: str | None = None) -> Document:
        try:
            body = encoded(item.content)
        except ValueError as error:
            raise ControlError(
                "invalid_content", "Artifact content must contain finite JSON values."
            ) from error
        digest = sha256(body).hexdigest()
        with self.lock, self.connect() as db:
            # Reserve the SQLite writer before checking version/source uniqueness.
            db.execute("BEGIN IMMEDIATE")
            if item.fetched_date:
                if not item.source:
                    raise ControlError("source_required", "A fetched result needs its source URL.")
                # Reject impossible dates as well as malformed strings.
                try:
                    datetime.strptime(item.fetched_date, "%Y-%m-%d")
                except ValueError as error:
                    raise ControlError("invalid_date", "Use a valid YYYY-MM-DD date.") from error
                row = db.execute(
                    "SELECT id FROM items WHERE source=? AND fetched_date=?",
                    (item.source, item.fetched_date),
                ).fetchone()
                if row:
                    return self.get(row[0])
            artifact_id = item_id or str(uuid.uuid4())
            root = artifact_id
            version = 1
            if item.previous_id:
                previous = self.get(item.previous_id)
                if previous["kind"] != item.kind:
                    raise ControlError("invalid_version", "Versions must keep their artifact type.")
                root = str(previous["root_id"])
                version = int(str(previous["version"])) + 1
                if db.execute(
                    "SELECT 1 FROM items WHERE root=? AND version=?", (root, version)
                ).fetchone():
                    raise ControlError("version_conflict", "Version the latest artifact.", 409)
            path = self.blobs / digest
            try:
                with path.open("xb") as stream:
                    stream.write(body)
            except FileExistsError:
                if path.read_bytes() != body:
                    raise ControlError("corrupt_blob", "Artifact hash mismatch.", 409) from None
            data: Document = {
                "id": artifact_id,
                "kind": item.kind,
                "title": item.title,
                "tags": list(item.tags),
                "source": item.source,
                "created": datetime.now(UTC).isoformat(),
                "root_id": root,
                "version": version,
                "previous_id": item.previous_id,
                "sha256": digest,
                "size": len(body),
                "ref": f"artifacts/{digest}",
                "fetched_date": item.fetched_date,
            }
            db.execute(
                "INSERT INTO items VALUES(?,?,?,?,?,?)",
                (
                    artifact_id,
                    json.dumps(data),
                    root,
                    version,
                    item.source,
                    item.fetched_date,
                ),
            )
            text = item.extracted_text or json.dumps(item.content, ensure_ascii=False)
            db.execute(
                "INSERT INTO search VALUES(?,?,?,?)",
                (
                    artifact_id,
                    item.title,
                    " ".join(item.tags),
                    f"{item.source}\n{text}",
                ),
            )
        return {**data, "content": item.content}

    def get(self, artifact_id: str) -> Document:
        with self.connect() as db:
            row = db.execute("SELECT data FROM items WHERE id=?", (artifact_id,)).fetchone()
            memo = db.execute("SELECT key FROM memo WHERE item_id=?", (artifact_id,)).fetchone()
        if row is None:
            raise ControlError("not_found", "Unknown Library artifact.", 404)
        data = cast(Document, json.loads(row[0]))
        if memo:
            data["memo_key"] = memo[0]
        path = self.blobs / str(data["sha256"])
        try:
            body = path.read_bytes()
        except FileNotFoundError as error:
            raise ControlError("corrupt_blob", "Artifact blob is missing.", 409) from error
        if sha256(body).hexdigest() != data["sha256"]:
            raise ControlError("corrupt_blob", "Artifact hash mismatch.", 409)
        return {**data, "content": cast(JsonValue, json.loads(body))}

    def search(self, query: str = "", offset: int = 0, limit: int = 100) -> list[Document]:
        if offset < 0 or not 1 <= limit <= 1000:
            raise ControlError("invalid_page", "Use offset >= 0 and limit between 1 and 1000.")
        with self.connect() as db:
            if query.strip():
                # Existing article outboxes search by a literal source URL.
                if query.startswith(("https://", "http://")):
                    query = '"' + query.replace('"', '""') + '"'
                try:
                    rows = db.execute(
                        "SELECT id FROM search WHERE search MATCH ? ORDER BY rank LIMIT ? OFFSET ?",
                        (query, limit, offset),
                    ).fetchall()
                except sqlite3.OperationalError as error:
                    raise ControlError(
                        "invalid_search", "Use a valid FTS5 search expression."
                    ) from error
            else:
                rows = db.execute(
                    "SELECT id FROM items ORDER BY rowid LIMIT ? OFFSET ?", (limit, offset)
                ).fetchall()
        return [self.get(row[0]) for row in rows]

    def versions(self, artifact_id: str) -> list[Document]:
        root = self.get(artifact_id)["root_id"]
        with self.connect() as db:
            rows = db.execute(
                "SELECT id FROM items WHERE root=? ORDER BY version", (root,)
            ).fetchall()
        return [self.get(row[0]) for row in rows]

    def by_ref(self, ref: str) -> Document:
        if re.fullmatch(r"artifacts/[0-9a-f]{64}\.json", ref):
            return self.get(Path(ref).stem)
        with self.connect() as db:
            row = db.execute(
                "SELECT id FROM items WHERE json_extract(data,'$.ref')=? ORDER BY rowid LIMIT 1",
                (ref,),
            ).fetchone()
        if row is None:
            raise ControlError(
                "not_found", "Use an artifacts/<sha256> reference from the Library.", 404
            )
        return self.get(row[0])

    def count(self, query: str = "") -> int:
        with self.connect() as db:
            if not query.strip():
                return db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
            try:
                return db.execute(
                    "SELECT COUNT(*) FROM search WHERE search MATCH ?", (query,)
                ).fetchone()[0]
            except sqlite3.OperationalError as error:
                raise ControlError(
                    "invalid_search", "Use a valid FTS5 search expression."
                ) from error

    def link(self, source_id: str, target_id: str, relation: str = "related") -> Document:
        self.get(source_id)
        self.get(target_id)
        if not relation.strip():
            raise ControlError("invalid_relation", "Supply a link relation.")
        with self.lock, self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO links VALUES(?,?,?)", (source_id, target_id, relation)
            )
        return {"source_id": source_id, "target_id": target_id, "relation": relation}

    def links(self, artifact_id: str) -> list[Document]:
        self.get(artifact_id)
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM links WHERE source=? OR target=?",
                (
                    artifact_id,
                    artifact_id,
                ),
            ).fetchall()
        return [{"source_id": row[0], "target_id": row[1], "relation": row[2]} for row in rows]

    def memoized(self, identity: MemoKey, produce: Callable[[], LibraryInput]) -> Document:
        key = sha256(encoded(identity.model_dump(mode="json"))).hexdigest()
        # The owner serializes identical work so two callers cannot compute the same result.
        with self.lock:
            with self.connect() as db:
                row = db.execute("SELECT item_id FROM memo WHERE key=?", (key,)).fetchone()
            if row:
                return {**self.get(row[0]), "memo_key": key}
            result = self.save(produce())
            with self.connect() as db:
                db.execute("INSERT INTO memo VALUES(?,?)", (key, result["id"]))
            return {**result, "memo_key": key}
