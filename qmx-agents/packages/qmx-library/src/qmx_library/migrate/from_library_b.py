"""MIGRATION step 2: Library B (`library.db` and `artifacts/<sha256>`) into the store, and step 5's
dual write, which maps every new `library_save` the same way.

One `items` row is one object. The old root keeps its id as an item alias, every version keeps
its own id and its `artifacts/<sha>` ref as aliases, so `resolve_alias` finds the object an old
ref named. `previous_id` becomes the object's one parent. The blob moves byte for byte, so its
hash is the old `sha256`. Old kinds map by `KINDS`; any other string becomes an `artifact`, and
every object keeps its old kind in `fields.legacy_kind`. Links become `related-to` edges written
by `migrator`; memo rows become `fields.memo_key` on the version they named.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

from pydantic import JsonValue

from qmx_library.migrate import MIGRATOR, OPERATOR, place, pre, with_legacy
from qmx_library.port import Draft, JsonObject, LibraryRefused, ObjectId
from qmx_library.store import Store

KINDS: Final = {
    "article": "source",
    "backtest": "backtest-result",
    "tool-result": "artifact",
    "remote-result": "artifact",
    "app-output": "artifact",
}
SLOTS: Final = {"source": "content", "artifact": "content", "backtest-result": "report"}
"""The blob slot each new kind's schema names for the old content."""

type Document = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class Imported:
    objects: int
    skipped: int
    edges: int


def encoded(value: JsonValue) -> bytes:
    """The bytes Library B stored for `content` (`qmx_control.library.encoded`)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def resolve_alias(store: Store, alias: str) -> ObjectId | None:
    """The first object annotated with `alias` (an old id or an `artifacts/<sha>` ref)."""
    row = store.catalog.db.execute(
        "SELECT a.object_id FROM annotations a, json_each(a.value) j "
        "WHERE a.key = 'aliases' AND j.value = ? ORDER BY a.seq LIMIT 1",
        (alias,),
    ).fetchone()
    return None if row is None else str(row[0])


def item_for_root(store: Store, root: str) -> str:
    found = resolve_alias(store, root)
    return store.get(OPERATOR, found).item if found else str(uuid.uuid7())


def draft_for(store: Store, row: Document, body: bytes, memo_key: str | None) -> Draft:
    new_kind = KINDS.get(str(row["kind"]), "artifact")
    fields: JsonObject = {
        "legacy_id": str(row["id"]),
        "legacy_kind": str(row["kind"]),
        "legacy_root": str(row["root_id"]),
        "legacy_version": int(row["version"]),
        "legacy_previous": cast(JsonValue, row.get("previous_id")),
        "legacy_sha256": str(row["sha256"]),
        "created": str(row["created"]),
    }
    if row.get("source"):
        fields["url"] = str(row["source"])
    if row.get("fetched_date"):
        fields["fetched_date"] = str(row["fetched_date"])
    if memo_key:
        fields["memo_key"] = memo_key
    previous = row.get("previous_id")
    parent = with_legacy(store, "legacy_id", str(previous)) if previous else None
    if previous and parent is None:
        raise LibraryRefused("not_found", f"version {row['id']} names no imported {previous}")
    return Draft(
        new_kind,
        item_for_root(store, str(row["root_id"])),
        title=str(row["title"]),
        fields=fields,
        blobs={SLOTS[new_kind]: body},
        parents=[parent] if parent else [],
        tags=[str(t) for t in cast(list[object], row.get("tags") or [])],
    )


def put_version(store: Store, row: Document, body: bytes, memo_key: str | None = None) -> bool:
    """One old version into the store; False when it is already there."""
    if with_legacy(store, "legacy_id", str(row["id"])) is not None:
        return False
    done = place(store, draft_for(store, row, body, memo_key))
    aliases: list[JsonValue] = [str(row["id"]), f"artifacts/{row['sha256']}"]
    store.annotate(OPERATOR, done.object_id, {"aliases": aliases})
    return True


def relate(store: Store, source_id: str, target_id: str) -> bool:
    found = [with_legacy(store, "legacy_id", i) for i in (source_id, target_id)]
    if None in found:
        return False
    store.relate(MIGRATOR, str(found[0]), "related-to", str(found[1]))
    return True


def import_library_b(store: Store, home: Path) -> Imported:
    db_path = pre(home) / "library.db"
    if not db_path.exists():
        return Imported(0, 0, 0)
    with closing(sqlite3.connect(db_path)) as db:
        rows = [
            cast(dict[str, Any], json.loads(r)) for (r,) in db.execute("SELECT data FROM items")
        ]
        memo = {str(i): str(k) for k, i in db.execute("SELECT key, item_id FROM memo")}
        links = db.execute("SELECT source, target FROM links").fetchall()
    rows.sort(key=lambda r: (str(r["root_id"]), int(r["version"])))
    put = skipped = 0
    for row in rows:
        body = (pre(home) / "artifacts" / str(row["sha256"])).read_bytes()
        if put_version(store, row, body, memo.get(str(row["id"]))):
            put += 1
        else:
            skipped += 1
    edges = sum(relate(store, str(s), str(t)) for s, t in links)
    return Imported(put, skipped, edges)


class DualWrite:
    """Step 5: the store side of `library_save` while both Libraries run. `library.db` stays the
    truth; a refusal here is returned to the caller and the nightly diff shows the gap."""

    def __init__(self, store: Store) -> None:
        self.store = store

    def saved(self, document: Document) -> str | None:
        content = cast(JsonValue, document["content"])
        try:
            put_version(self.store, document, encoded(content), document.get("memo_key"))
        except LibraryRefused as refused:
            return refused.code
        return None

    def linked(self, source_id: str, target_id: str) -> str | None:
        try:
            return None if relate(self.store, source_id, target_id) else "not_found"
        except LibraryRefused as refused:
            return refused.code
