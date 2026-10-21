"""Check an import against step 0, and diff the two Libraries while both run (step 5).

Both read the store read-only, through its `catalog.db` and its blob files, so they run beside
the host that writes it. `verify` sets step 0's numbers beside the store's, per kind, hashes every
imported blob, and walks every version chain; `dual_diff` compares the live `library.db` with the
store: every old version present, its blob the same hash, and the latest version per root the
head of `main`.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from collections.abc import Generator
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from qmx_library.migrate.snapshot import Counts

LEGACY_B = "json_extract(fields, '$.legacy_id') IS NOT NULL"


@contextmanager
def read_only(path: Path) -> Generator[sqlite3.Connection]:
    with closing(sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)) as db:
        yield db


@dataclass(frozen=True, slots=True)
class Row:
    name: str
    before: int
    after: int


@dataclass(frozen=True, slots=True)
class Verification:
    rows: list[Row]
    bad_blobs: list[str] = field(default_factory=list[str])
    bad_chains: list[str] = field(default_factory=list[str])
    blobs_checked: int = 0

    @property
    def ok(self) -> bool:
        return (
            not self.bad_blobs
            and not self.bad_chains
            and all(r.before == r.after for r in self.rows)
        )

    def render(self) -> str:
        width = max([len(r.name) for r in self.rows] + [4])
        lines = [f"{'what':<{width}}  step0  store"]
        for row in self.rows:
            mark = "" if row.before == row.after else "  MISMATCH"
            lines.append(f"{row.name:<{width}}  {row.before:>5}  {row.after:>5}{mark}")
        lines.append(f"blobs hashed {self.blobs_checked}, bad {len(self.bad_blobs)}")
        lines.append(f"version chains bad {len(self.bad_chains)}")
        lines.extend(f"  bad blob {b}" for b in self.bad_blobs)
        lines.extend(f"  bad chain {c}" for c in self.bad_chains)
        return "\n".join(lines)


def blob_file(store_root: Path, blob_id: str) -> Path:
    hexdigest = blob_id.removeprefix("sha256:")
    return store_root / "blobs" / hexdigest[:2] / hexdigest[2:4] / hexdigest


def hashes(store_root: Path, blob_id: str) -> bool:
    path = blob_file(store_root, blob_id)
    return path.exists() and f"sha256:{sha256(path.read_bytes()).hexdigest()}" == blob_id


def objects(db: sqlite3.Connection, where: str) -> list[dict[str, Any]]:
    rows = db.execute(
        "SELECT o.object_id, o.item, o.kind, o.fields, o.blobs, o.parents FROM objects o "  # noqa: S608
        f"WHERE {where} AND EXISTS (SELECT 1 FROM moves m WHERE m.new_head = o.object_id)"
    )
    return [
        {
            "id": object_id,
            "item": item,
            "kind": kind,
            "fields": json.loads(fields),
            "blobs": json.loads(blobs),
            "parents": json.loads(parents),
        }
        for object_id, item, kind, fields, blobs, parents in rows
    ]


def chain_problem(by_id: dict[str, dict[str, Any]], found: dict[str, Any]) -> str | None:
    fields = found["fields"]
    parents = cast(list[str], found["parents"])
    previous = fields.get("legacy_previous")
    if previous is None:
        return None if not parents else f"{fields['legacy_id']} has parents but no previous"
    if (
        len(parents) != 1
        or by_id.get(parents[0], {}).get("fields", {}).get("legacy_id") != previous
    ):
        return f"{fields['legacy_id']} is not parented on {previous}"
    length, node = 0, found
    while node["parents"]:
        length, node = length + 1, by_id[node["parents"][0]]
    if length != int(fields["legacy_version"]) - 1:
        return (
            f"{fields['legacy_id']} chain is {length + 1} long, version {fields['legacy_version']}"
        )
    return None


def verify(home: Path, store_root: Path) -> Verification:
    before = Counts.read(home)
    with read_only(store_root / "catalog.db") as db:
        library_b = objects(db, LEGACY_B)
        registry = objects(db, "json_extract(fields, '$.governed_fp1') IS NOT NULL")
        apps = objects(db, "json_extract(fields, '$.legacy_ref') IS NOT NULL")
        definitions = objects(db, "json_extract(fields, '$.legacy_definition') IS NOT NULL")
        ids = [o["id"] for o in library_b]
        edges = sum(
            1
            for (from_id, to_id) in db.execute(
                "SELECT from_id, to_id FROM relations WHERE origin = 'edge' "
                "AND type = 'related-to' AND writer = 'migrator'"
            )
            if from_id in ids and to_id in ids
        )
    by_id = {o["id"]: o for o in library_b}
    kinds = Counter(str(o["fields"]["legacy_kind"]) for o in library_b)
    roots = Counter(str(o["fields"]["legacy_root"]) for o in library_b)
    rows = [Row(f"library-b {k}", before.kinds.get(k, 0), kinds.get(k, 0))
            for k in sorted(before.kinds.keys() | kinds.keys())]  # fmt: skip
    rows.append(
        Row(
            "library-b roots with all versions",
            len(before.versions),
            sum(1 for r, n in before.versions.items() if roots.get(r) == n),
        )
    )
    rows.append(Row("library-b links", before.links, edges))
    memo = sum(1 for o in library_b if o["fields"].get("memo_key"))
    rows.append(Row("library-b memo rows", before.memo, memo))
    bad_blobs: list[str] = []
    checked: dict[str, int] = {}
    for found in [*library_b, *apps, *definitions]:
        for spec in cast(dict[str, dict[str, Any]], found["blobs"]).values():
            blob_id = str(spec["sha256"])
            if not hashes(store_root, blob_id):
                bad_blobs.append(f"{found['id']} {blob_id}")
            checked[blob_id] = int(spec["size"])
        legacy = found["fields"].get("legacy_sha256")
        if legacy and f"sha256:{legacy}" not in [s["sha256"] for s in found["blobs"].values()]:
            bad_blobs.append(f"{found['fields']['legacy_id']} moved as other bytes than {legacy}")
    b_blobs = {f"sha256:{o['fields']['legacy_sha256']}" for o in library_b}
    rows.append(Row("library-b blobs", before.blobs, len(b_blobs & checked.keys())))
    rows.append(
        Row(
            "library-b blob bytes",
            before.blob_bytes,
            sum(checked[b] for b in b_blobs if b in checked),
        )
    )
    registry_kinds = Counter(str(o["fields"]["record_kind"]) for o in registry)
    rows.extend(
        Row(f"registry {k}", before.registry.get(k, 0), registry_kinds.get(k, 0))
        for k in sorted(before.registry.keys() | registry_kinds.keys())
    )
    rows.append(Row("app artifacts", before.app_artifacts, len(apps)))
    rows.append(Row("app definitions", before.app_definitions, len(definitions)))
    chains = [p for o in library_b if (p := chain_problem(by_id, o))]
    return Verification(rows, bad_blobs, chains, len(checked))


@dataclass(frozen=True, slots=True)
class Diff:
    old: int
    new: int
    missing: list[str]
    other_bytes: list[str]
    stale_heads: list[str]

    @property
    def clean(self) -> bool:
        return self.old == self.new and not (self.missing or self.other_bytes or self.stale_heads)

    def as_json(self) -> dict[str, Any]:
        return {
            "clean": self.clean,
            "old": self.old,
            "new": self.new,
            "missing": self.missing,
            "other_bytes": self.other_bytes,
            "stale_heads": self.stale_heads,
        }


def dual_diff(home: Path, store_root: Path) -> Diff:
    """Counts, hashes and latest version per root, live `library.db` against the store."""
    with read_only(home / "library.db") as db:
        old = [cast(dict[str, Any], json.loads(r)) for (r,) in db.execute("SELECT data FROM items")]
    with read_only(store_root / "catalog.db") as db:
        new = {str(o["fields"]["legacy_id"]): o for o in objects(db, LEGACY_B)}
        heads = {(str(i), str(h)) for i, h in db.execute("SELECT item, head FROM heads "
                                                          "WHERE ref = 'main'")}  # fmt: skip
    latest: dict[str, dict[str, Any]] = {}
    for row in old:
        root = str(row["root_id"])
        if root not in latest or int(row["version"]) > int(latest[root]["version"]):
            latest[root] = row
    missing = [str(r["id"]) for r in old if str(r["id"]) not in new]
    other = [
        str(r["id"])
        for r in old
        if str(r["id"]) in new
        and f"sha256:{r['sha256']}"
        not in [s["sha256"] for s in new[str(r["id"])]["blobs"].values()]
    ]
    stale = [
        root
        for root, row in latest.items()
        if (found := new.get(str(row["id"]))) is not None
        and (found["item"], found["id"]) not in heads
    ]
    return Diff(len(old), len(new), missing, other, stale)
