"""MIGRATION step 2: Library B (`library.db` and `artifacts/<sha256>`) into the store.

One `items` row is one object. The old root keeps its id as an item alias, every version keeps
its own id and its `artifacts/<sha>` ref as aliases, so `resolve_alias` finds the object an old
ref named. `previous_id` becomes the object's one parent. The blob moves byte for byte, so its
hash is the old `sha256`. Old kinds map by `KINDS`; any other string becomes an `artifact`, and
every object keeps its old kind in `fields.legacy_kind`. Links become `related-to` edges written
by `migrator`; memo rows become `fields.memo_key` on the version they named.

`JUNK` is the test junk his real home collected from the remote-flow lanes: sixteen
`workflow-result` rows titled `remote-flow`, each written by a test run rather than by him. The
import skips exactly those ids and reports them, so P-REHEARSE can compare step 0's counts minus
this list (fix-check 58, N18) instead of asking the importer to guess.

`switch_over` is the whole cut-over (MIGRATION steps 0, 2 and 4, then step 6's retirement) as one
call, so `scripts/data/switch_library.py` and probe P-REHEARSE run the same steps this module's
tests run.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import stat
import uuid
from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

from pydantic import JsonValue

from qmx_library.migrate import MIGRATOR, OPERATOR, open_target, place, pre, target, with_legacy
from qmx_library.migrate.from_apps import Imported as AppsImported
from qmx_library.migrate.from_apps import import_apps
from qmx_library.migrate.snapshot import Counts, snapshot
from qmx_library.migrate.verify import Verification, verify
from qmx_library.port import Draft, JsonObject, LibraryRefused, ObjectId
from qmx_library.store import Redactor, Store

KINDS: Final = {
    "article": "source",
    "backtest": "backtest-result",
    "tool-result": "artifact",
    "remote-result": "artifact",
    "app-output": "artifact",
}
SLOTS: Final = {"source": "content", "artifact": "content", "backtest-result": "report"}
"""The blob slot each new kind's schema names for the old content."""
JUNK: Final[tuple[str, ...]] = (
    "0a1b1754-1d4e-4577-9568-3675688d1f1b",
    "15a376cf-c81a-43d1-9bc9-20271eba54dd",
    "2126ac41-c240-43c9-b36c-90d8754c2dff",
    "27332773-86ba-4599-a62d-86e7e794e7f0",
    "2ec1bae1-c1c4-48bc-a956-fff1634056b0",
    "33b60b36-0207-4cca-b221-40dea5e4768e",
    "38ff65b2-6433-4f03-936c-c523e991c5dd",
    "3cc93b07-2be1-4b26-86e4-1742cfd4530c",
    "48087ec6-9915-43a3-ad5e-938ee1e1e8cb",
    "5c9a3ad7-bc80-45fd-8891-fcadd99d6e1a",
    "6945707e-4bfe-49b3-bb84-326a72fcc2b0",
    "85e7ca0b-adea-4e73-9334-884236e935c0",
    "9df34f75-8efd-4000-8aa3-afe7e97650eb",
    "c454a345-02f7-45a8-b24d-f9af16df18c5",
    "d2ccbe7e-6e59-435a-9afa-c787cafd731b",
    "f97c2036-a726-4564-a745-a0cdecdcd7b6",
)
"""The ids of the known test junk, filtered by id and never by title (fix-check 58, N18)."""
RETIRED: Final = "migration/retired"

type Document = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class Imported:
    objects: int
    skipped: int
    edges: int
    junk: tuple[str, ...] = ()


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
    """Every row of the frozen `library.db` but the known test junk."""
    db_path = pre(home) / "library.db"
    if not db_path.exists():
        return Imported(0, 0, 0)
    with closing(sqlite3.connect(db_path)) as db:
        rows = [
            cast(dict[str, Any], json.loads(r)) for (r,) in db.execute("SELECT data FROM items")
        ]
        memo = {str(i): str(k) for k, i in db.execute("SELECT key, item_id FROM memo")}
        links = db.execute("SELECT source, target FROM links").fetchall()
    junk = tuple(sorted(str(row["id"]) for row in rows if str(row["id"]) in JUNK))
    rows = [row for row in rows if str(row["id"]) not in JUNK]
    rows.sort(key=lambda r: (str(r["root_id"]), int(r["version"])))
    put = skipped = 0
    for row in rows:
        body = (pre(home) / "artifacts" / str(row["sha256"])).read_bytes()
        if put_version(store, row, body, memo.get(str(row["id"]))):
            put += 1
        else:
            skipped += 1
    edges = sum(relate(store, str(s), str(t)) for s, t in links)
    return Imported(put, skipped, edges, junk)


@dataclass(frozen=True, slots=True)
class Switched:
    """What one cut-over did, as the report `switch_library.py` writes says it."""

    counts: Counts
    imported: Imported
    apps: AppsImported
    verification: Verification
    retired: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.verification.ok

    def report(self) -> dict[str, JsonValue]:
        return cast(
            dict[str, JsonValue],
            {
                "ok": self.ok,
                "step0": {
                    "kinds": dict(self.counts.kinds),
                    "roots": len(self.counts.versions),
                    "links": self.counts.links,
                    "memo": self.counts.memo,
                    "blobs": self.counts.blobs,
                    "blob_bytes": self.counts.blob_bytes,
                    "app_artifacts": self.counts.app_artifacts,
                    "app_definitions": self.counts.app_definitions,
                },
                "imported": {
                    "objects": self.imported.objects,
                    "skipped": self.imported.skipped,
                    "edges": self.imported.edges,
                },
                "junk": list(self.imported.junk),
                "apps": {
                    "artifacts": self.apps.artifacts,
                    "definitions": self.apps.definitions,
                    "skipped": self.apps.skipped,
                },
                "verification": [
                    {"what": row.name, "step0": row.before, "store": row.after}
                    for row in self.verification.rows
                ],
                "bad_blobs": self.verification.bad_blobs,
                "bad_chains": self.verification.bad_chains,
                "retired": list(self.retired),
            },
        )


def retire(home: Path) -> tuple[str, ...]:
    """Step 6: `library.db`, `artifacts.db` and `artifacts/` to `migration/retired/`, read-only."""
    folder = home / RETIRED
    folder.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for name in ("library.db", "artifacts.db"):
        source = home / name
        if not source.is_file():
            continue
        target = folder / name
        if target.exists():
            raise LibraryRefused("collision", f"{target} already holds the retired {name}")
        for suffix in ("-wal", "-shm"):
            (home / f"{name}{suffix}").unlink(missing_ok=True)
        shutil.move(str(source), str(target))
        moved.append(name)
    blobs = home / "artifacts"
    if blobs.is_dir():
        target = folder / "artifacts"
        if target.exists():
            raise LibraryRefused("collision", f"{target} already holds the retired artifacts/")
        shutil.move(str(blobs), str(target))
        moved.append("artifacts")
    for kept in folder.iterdir() if folder.is_dir() else ():
        for path in [kept, *kept.rglob("*")]:
            path.chmod(stat.S_IREAD | (stat.S_IEXEC if path.is_dir() else 0))
    return tuple(moved)


def switch_over(home: Path, *, redactor: Redactor) -> Switched:
    """MIGRATION step 0, steps 2 and 4, then step 6's retirement, verified before anything moves.

    The store is written under `<home>/library/`; the import reads only `migration/pre/`; the old
    files move only after `verify` holds every count, hash and version chain against step 0's
    numbers minus `JUNK`.
    """
    home = home.resolve()
    counts = snapshot(home)
    store = open_target(home, dry_run=False, redactor=redactor)
    try:
        imported = import_library_b(store, home)
        apps = import_apps(store, home)
    finally:
        store.close()
    checked = verify(home, target(home, dry_run=False), junk=imported.junk)
    if not checked.ok:
        return Switched(counts, imported, apps, checked, ())
    return Switched(counts, imported, apps, checked, retire(home))
