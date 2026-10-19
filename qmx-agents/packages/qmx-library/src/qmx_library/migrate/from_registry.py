"""MIGRATION step 3: the registry room into the store, read only through QMB's as-of port (B-15).

The importer takes the port (`qmb.registryread.RegistryReadPort` or anything shaped like it) and
reads its bound as-of set: one object per record, of the kind `KINDS` maps it to, with
`fields.governed_fp1` the record's `fp1` and its identity content (`body`, the contract version,
the at-birth parents) beside it. A supersedes chain is one item whose versions are parented in
order, and each pair is also a `supersedes` edge. Dated pointers become item aliases. Nothing
here opens QMB's SQLite or imports QMB.

Every record is checked before anything is written: one `fp1` seen with two identity contents,
in the set or against an object already imported, stops the import with an alarm (FM-14).

The kind schemas hash the manifest (`identity: manifest`), not CT-06's identity content, so an
object id is not the record's `fp1`; `fields.governed_fp1` carries it.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol, cast

from pydantic import JsonValue

from qmx_library.migrate import MIGRATOR, OPERATOR, alarm, place, with_legacy
from qmx_library.port import Draft, JsonObject
from qmx_library.store import Store

KINDS: Final = {
    "bot-definition": "bot",
    "strategy-family": "strategy",
    "confluence": "component",
    "book-definition": "book",
    "bms-definition": "bms",
    "book-binding": "binding",
    "split-manifest": "dataset",
    "source-observation": "source",
    "performance-result": "backtest-result",
    "experiment-spec": "setup",
}
"""Library AD-3's table for the ten DEC-0271 kinds, and no other."""
IDENTITY: Final = ("record_kind", "contract_format_version", "at_birth_parent_refs", "body")


class Fp(Protocol):
    @property
    def value(self) -> str: ...


class Record(Protocol):
    @property
    def kind(self) -> str: ...
    @property
    def contract_format_version(self) -> int: ...
    @property
    def at_birth_parent_refs(self) -> Sequence[Fp]: ...
    @property
    def body(self) -> Mapping[str, object]: ...
    @property
    def stable_id(self) -> Fp: ...


class Pointer(Protocol):
    @property
    def alias(self) -> str: ...
    @property
    def target(self) -> Fp: ...


class Pair(Protocol):
    @property
    def newer(self) -> Fp: ...
    @property
    def older(self) -> Fp: ...


class AsOf(Protocol):
    @property
    def records(self) -> Sequence[Record]: ...
    @property
    def pointers(self) -> Sequence[Pointer]: ...
    @property
    def supersedes(self) -> Sequence[Pair]: ...


class RegistryRead(Protocol):
    @property
    def bound(self) -> AsOf: ...


@dataclass(frozen=True, slots=True)
class Imported:
    objects: int
    skipped: int
    edges: int


def thawed(value: object) -> JsonValue:
    """A record body, frozen into mappings and tuples by qmf, as plain JSON."""
    if isinstance(value, Mapping):
        return {str(k): thawed(v) for k, v in cast(Mapping[object, object], value).items()}
    if isinstance(value, list | tuple):
        return [thawed(v) for v in cast(Iterable[object], value)]
    if value is None or isinstance(value, str | int | float | bool):
        return value
    found = getattr(value, "value", None)
    return found if isinstance(found, str) else str(value)


def identity(record: Record) -> JsonObject:
    return {
        "record_kind": record.kind,
        "contract_format_version": record.contract_format_version,
        "at_birth_parent_refs": [p.value for p in record.at_birth_parent_refs],
        "body": thawed(record.body),
    }


def stored_identity(store: Store, object_id: str) -> JsonObject:
    fields = store.get(OPERATOR, object_id).fields
    return {key: fields.get(key) for key in IDENTITY}


def check(store: Store, home: Path, records: Sequence[Record]) -> None:
    seen: dict[str, JsonObject] = {}
    for record in records:
        fp, mine = record.stable_id.value, identity(record)
        if record.kind not in KINDS:
            raise alarm(home, "unknown_kind", {"fp1": fp, "record_kind": record.kind})
        if seen.setdefault(fp, mine) != mine:
            raise alarm(home, "collision", {"fp1": fp, "where": "as-of set"})
        found = with_legacy(store, "governed_fp1", fp)
        if found is not None and stored_identity(store, found) != mine:
            raise alarm(home, "collision", {"fp1": fp, "where": "store", "object_id": found})


def import_registry(store: Store, home: Path, port: RegistryRead) -> Imported:
    bound = port.bound
    records = list(bound.records)
    check(store, home, records)
    older_of = {p.newer.value: p.older.value for p in bound.supersedes}
    aliases: dict[str, list[JsonValue]] = {}
    for pointer in bound.pointers:
        aliases.setdefault(pointer.target.value, []).append(pointer.alias)
    by_fp = {r.stable_id.value: r for r in records}

    def depth(fp: str) -> int:
        return 1 + depth(older_of[fp]) if fp in older_of else 0

    put = skipped = 0
    for record in sorted(records, key=lambda r: (depth(r.stable_id.value), r.stable_id.value)):
        fp = record.stable_id.value
        if with_legacy(store, "governed_fp1", fp) is not None:
            skipped += 1
            continue
        older = older_of.get(fp)
        parent = with_legacy(store, "governed_fp1", older) if older in by_fp else None
        item = store.get(OPERATOR, parent).item if parent else str(uuid.uuid7())
        names = aliases.get(fp, [])
        draft = Draft(
            KINDS[record.kind],
            item,
            title=str(names[0]) if names else f"{record.kind} {fp.rsplit(':', 1)[-1][:12]}",
            fields={"governed_fp1": fp, **identity(record)},
            parents=[parent] if parent else [],
        )
        done = place(store, draft)
        store.annotate(OPERATOR, done.object_id, {"aliases": [fp, *names]})
        put += 1
    edges = 0
    for pair in bound.supersedes:
        newer = with_legacy(store, "governed_fp1", pair.newer.value)
        older = with_legacy(store, "governed_fp1", pair.older.value)
        if newer and older:
            store.relate(MIGRATOR, newer, "supersedes", older)
            edges += 1
    return Imported(put, skipped, edges)
