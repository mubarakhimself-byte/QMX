"""The Library store: content-addressed objects and blobs, refs moved only by compare-and-swap, and
append-only edge and annotation logs (Library AD-1, AD-2, AD-5, AD-6, AD-7).

Evidence is the files under the store's root:

    objects/ab/cd/<hex>.json    one canonical identity manifest per object, written once
    blobs/ab/cd/<hex>           the bytes of a durable blob, written once
    blobs/transient/<hex>       a transient blob (checkpoints), kept on this store only
    refs/log.jsonl              every ref move, append-only
    edges/<store>.jsonl         after-birth relations, append-only, one stream per writer
    annotations/log.jsonl       tags, authorship and other annotations, append-only
    kinds/<kind>.schema.json    the kinds this store was written with

`catalog.db` is rebuilt from those files whenever it is missing or behind them. One process
writes a store: `open` takes an OS lock on `writer.lock` and refuses a second writer. Every put
passes the redactor first, so the stored bytes are the only bytes (engine AD-37).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import unicodedata
import uuid
from collections import deque
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import IO, Any, Final, Literal, Protocol, Self, cast

from pydantic import JsonValue

from qmx_library.fts import Catalog, norm
from qmx_library.kinds import Kind, kind, schema_files
from qmx_library.marks import CLEAR, QUARANTINED, Marks, marks, marks_ref
from qmx_library.port import (
    RELATIONS,
    AsOf,
    BlobRef,
    BlobView,
    Class,
    Commit,
    Draft,
    Grounding,
    Hit,
    JsonObject,
    LibraryRefused,
    MergeResult,
    ObjectId,
    ObjectView,
    Relation,
    Step,
    Strategy,
    normalised,
)
from qmx_library.principal import MAIN, Act, Principal, may_advance, own_ref, state_ref

MANIFEST: Final = "qmx.library.object/1"
CHECKOUT_FILE: Final = ".checkout.json"
TEXT_LIMIT: Final = 1_000_000
"""Bytes of one text blob read into the search index."""


class Redactor(Protocol):
    """`qmx_engine.ledger.redact`, passed in by the host so the Library imports no engine code."""

    def redact(self, text: str) -> str: ...

    def redact_json(self, value: object) -> tuple[JsonValue, int]: ...

    def holds_value(self, data: bytes) -> bool: ...


def canonical(value: object) -> bytes:
    """Sorted keys, no whitespace, NFC strings, no NaN: the fp1 recipe, floats and nulls allowed."""

    def nfc(node: object) -> object:
        if isinstance(node, str):
            return unicodedata.normalize("NFC", node)
        if isinstance(node, dict):
            return {nfc(k): nfc(v) for k, v in cast(dict[object, object], node).items()}
        if isinstance(node, list | tuple):
            return [nfc(v) for v in cast(Sequence[object], node)]
        return node

    text = json.dumps(nfc(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8")


def fp1(value: object) -> ObjectId:
    return f"fp1:sha256:{sha256(canonical(value)).hexdigest()}"


def locator(value: JsonObject) -> JsonObject:
    """Where in its source an object came from: `{seconds}`, `{page, paragraph?}` or `{line}`
    (AD-4)."""

    def count(key: str) -> bool:
        found = value.get(key)
        return isinstance(found, int) and not isinstance(found, bool) and found >= 1

    seconds = value.get("seconds")
    match sorted(value):
        case ["seconds"] if isinstance(seconds, int | float) and not isinstance(seconds, bool):
            ok = seconds >= 0
        case ["line"]:
            ok = count("line")
        case ["page"]:
            ok = count("page")
        case ["page", "paragraph"]:
            ok = count("page") and count("paragraph")
        case _:
            ok = False
    if not ok:
        raise LibraryRefused("schema_invalid", f"{value!r} is not a locator")
    return value


def _sharded(root: Path, hexdigest: str, suffix: str = "") -> Path:
    return root / hexdigest[:2] / hexdigest[2:4] / f"{hexdigest}{suffix}"


def _lock(handle: IO[bytes]) -> None:
    if sys.platform == "win32":
        import msvcrt  # noqa: PLC0415

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl  # noqa: PLC0415

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _write_once(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() != data:
            raise LibraryRefused("collision", f"{path.name} exists with other bytes")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}")
    with temp.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def _append(path: Path, record: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(json.dumps(record, sort_keys=True).encode("utf-8") + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _lines(path: Path) -> Generator[dict[str, Any]]:
    if path.exists():
        with path.open("rb") as handle:
            for line in handle:
                if line.strip():
                    yield cast(dict[str, Any], json.loads(line))


class Store:
    """The writer of one store. Every verb of `LibraryPort` is here; the reads the engine adapter
    needs beside them (`head`, `placed`, `moves`, `read_blob`) are catalog queries."""

    def __init__(
        self,
        root: Path,
        handle: IO[bytes],
        *,
        name: str,
        redactor: Redactor,
        wall: Callable[[], datetime],
    ) -> None:
        self.root = root
        self.name = name
        self.engine = Principal("engine", name)
        self.redactor = redactor
        self.wall = wall
        self._handle = handle
        self._mutex = threading.RLock()
        self.catalog = Catalog(root / "catalog.db")
        if self.catalog.stamp() != self._stamp():
            self.rebuild_indexes()
        self._seq = self.catalog.last_seq()
        (edges,) = self.catalog.db.execute(
            "SELECT count(*) FROM relations WHERE origin = 'edge'"
        ).fetchone()
        self._edge_seq = int(edges)

    @classmethod
    def open(
        cls,
        root: Path,
        *,
        redactor: Redactor,
        name: str = "pc",
        wall: Callable[[], datetime] | None = None,
    ) -> Store:
        root.mkdir(parents=True, exist_ok=True)
        handle = (root / "writer.lock").open("a+b")
        try:
            _lock(handle)
        except OSError:
            handle.close()
            raise LibraryRefused(
                "storage_failure", f"another process writes the Library at {root}"
            ) from None
        kinds = root / "kinds"
        kinds.mkdir(exist_ok=True)
        for schema in schema_files():
            target = kinds / schema.name
            if not target.exists() or target.read_bytes() != schema.read_bytes():
                shutil.copyfile(schema, target)
        try:
            return cls(
                root, handle, name=name, redactor=redactor, wall=wall or (lambda: datetime.now(UTC))
            )
        except BaseException:
            handle.close()
            raise

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self.catalog.close()
        self._handle.close()

    @property
    def ref_log(self) -> Path:
        return self.root / "refs" / "log.jsonl"

    @property
    def edge_log(self) -> Path:
        return self.root / "edges" / f"{self.name}.jsonl"

    @property
    def annotation_log(self) -> Path:
        return self.root / "annotations" / "log.jsonl"

    def _object_path(self, object_id: ObjectId) -> Path:
        return _sharded(self.root / "objects", object_id.rsplit(":", 1)[-1], ".json")

    def _blob_path(self, blob_id: str, *, transient: bool) -> Path:
        hexdigest = blob_id.removeprefix("sha256:")
        if transient:
            return self.root / "blobs" / "transient" / hexdigest
        return _sharded(self.root / "blobs", hexdigest)

    def _stamp(self) -> str:
        logs = [*sorted((self.root / "edges").glob("*.jsonl")), self.ref_log, self.annotation_log]
        sizes = {str(p.relative_to(self.root)): p.stat().st_size for p in logs if p.exists()}
        return json.dumps(sizes, sort_keys=True)

    def rebuild_indexes(self) -> None:
        """Drop `catalog.db` and replay the evidence into a new one (AD-5, FM-9)."""
        with self._mutex:
            self.catalog.close()
            for suffix in ("", "-wal", "-shm"):
                (self.root / f"catalog.db{suffix}").unlink(missing_ok=True)
            self.catalog = Catalog(self.root / "catalog.db")
            with self.catalog.batch():
                for path in sorted((self.root / "objects").rglob("*.json")):
                    manifest = cast(dict[str, Any], json.loads(path.read_bytes()))
                    self._index_object(f"fp1:sha256:{path.stem}", manifest)
                for move in _lines(self.ref_log):
                    self.catalog.index_move(move)
                for log in sorted((self.root / "edges").glob("*.jsonl")):
                    for edge in _lines(log):
                        self.catalog.index_edge(edge)
                for entry in _lines(self.annotation_log):
                    self.catalog.index_annotation(entry)
                self.catalog.set_stamp(self._stamp())

    def _index_object(self, object_id: ObjectId, manifest: Mapping[str, Any]) -> None:
        texts: list[str] = []
        for spec in cast(dict[str, dict[str, Any]], manifest["blobs"]).values():
            path = self._blob_path(str(spec["sha256"]), transient=False)
            if path.exists() and int(spec["size"]) <= TEXT_LIMIT:
                with suppress(UnicodeDecodeError):
                    texts.append(path.read_bytes().decode("utf-8"))
        klass = kind(str(manifest["kind"])).klass
        self.catalog.index_object(object_id, manifest, klass, " ".join(texts))

    def _now(self) -> str:
        return self.wall().astimezone(UTC).isoformat().replace("+00:00", "Z")

    def _move(
        self,
        who: Principal,
        item: str,
        ref: str,
        new_head: str,
        *,
        reason: str | None = None,
        replaced_by: str | None = None,
    ) -> Commit:
        found = self.catalog.head(item, ref)
        prev = None if found is None else found[0]
        self._seq += 1
        move: dict[str, object] = {
            "seq": self._seq,
            "item": item,
            "ref": ref,
            "principal": str(who),
            "prev_head": prev,
            "new_head": new_head,
            "at": self._now(),
        }
        if reason is not None:
            move["reason"] = reason
        if replaced_by is not None:
            move["replaced_by"] = replaced_by
        _append(self.ref_log, move)
        self.catalog.index_move(move)
        return Commit(new_head, item, ref, prev, self._seq)

    def _annotate(self, who: Principal, object_id: ObjectId, values: JsonObject) -> None:
        entry = {"object_id": object_id, "values": values, "principal": str(who), "at": self._now()}
        _append(self.annotation_log, entry)
        self.catalog.index_annotation(entry)

    @contextmanager
    def _writing(self) -> Generator[None]:
        with self._mutex, self.catalog.batch():
            yield
            self.catalog.set_stamp(self._stamp())

    def _blob(self, slot: str, data: bytes | BlobRef, spec: Kind) -> dict[str, JsonValue]:
        media = spec.slot(slot)
        if isinstance(data, BlobRef):
            path = self._blob_path(data.blob_id, transient=media.transient)
            if not path.exists():
                raise LibraryRefused("blob_unavailable", f"no blob {data.blob_id}")
            data = path.read_bytes()
        data = self._redacted(data)
        blob_id = f"sha256:{sha256(data).hexdigest()}"
        _write_once(self._blob_path(blob_id, transient=media.transient), data)
        return {"sha256": blob_id, "size": len(data), "media_type": media.media_type}

    def _redacted(self, data: bytes) -> bytes:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            if self.redactor.holds_value(data):
                raise LibraryRefused("secret_in_blob", "a binary blob holds a secret") from None
            return data
        return self.redactor.redact(text).encode("utf-8")

    def _require(self, object_id: ObjectId) -> tuple[Any, ...]:
        row = self.catalog.row(object_id)
        if row is None:
            raise LibraryRefused("not_found", f"no object {object_id}")
        return row

    def _check_owner(self, who: Principal, ref: str, act: Act) -> None:
        if not may_advance(who, ref, act, store=self.name):
            raise LibraryRefused("ref_not_owned", f"{who} may not {act} onto {ref}")

    def _active(self, item: str) -> None:
        if self.catalog.state(item) == "archived":
            raise LibraryRefused("archived", f"item {item} is archived")

    def _mint(
        self, who: Principal, draft: Draft, item: str, parents: Sequence[ObjectId]
    ) -> tuple[ObjectId, Kind]:
        spec = kind(draft.kind)
        fields = cast(JsonObject, self.redactor.redact_json(draft.fields)[0])
        spec.check(fields, set(draft.blobs))
        relations: list[JsonObject] = []
        for relation in draft.relations:
            name, to = normalised(relation[0]), relation[1]
            if name not in RELATIONS:
                raise LibraryRefused("unknown_relation", f"{relation[0]!r} is not a relation")
            self._require(to)
            entry: JsonObject = {"type": name, "to": to}
            if len(relation) == 3:
                entry["locator"] = locator(relation[2])
            relations.append(entry)
        for parent in parents:
            self._require(parent)
        manifest: dict[str, JsonValue] = {
            "schema": MANIFEST,
            "kind": draft.kind,
            "schema_version": spec.schema_version,
            "item_id": item,
            "title": self.redactor.redact(draft.title),
            "summary": self.redactor.redact(draft.summary),
            "fields": fields,
            "blobs": {slot: self._blob(slot, data, spec) for slot, data in draft.blobs.items()},
            "parents": list(parents),
            "relations": cast(list[JsonValue], relations),
            "world": None,
        }
        object_id = fp1(manifest)
        fresh = not self._object_path(object_id).exists()
        _write_once(self._object_path(object_id), canonical(manifest))
        self._index_object(object_id, manifest)
        if fresh:
            author: JsonObject = {"kind": who.who, "id": who.id or who.who}
            values: JsonObject = {"author": author, "created": self._now()}
            if draft.tags:
                values["tags"] = self.redactor.redact_json(list(draft.tags))[0]
            self._annotate(who, object_id, values)
        return object_id, spec

    def put(
        self, who: Principal, draft: Draft, *, on: str, expected_head: ObjectId | None
    ) -> Commit:
        """A new object on `on`, which `who` owns. `expected_head` is the head the caller read,
        None for a ref the item does not have yet; any other head refuses `stale_head`."""
        self._check_owner(who, on, "put")
        spec = kind(draft.kind)
        if spec.retired:
            raise LibraryRefused("unknown_kind", f"{draft.kind} is retired")
        if on == MAIN and spec.klass != "record":
            raise LibraryRefused(
                "ref_not_owned", f"a {draft.kind} reaches main only by publish, never by put"
            )
        item = draft.item or str(uuid.uuid7())
        with self._writing():
            self._active(item)
            found = self.catalog.head(item, on)
            head = None if found is None else found[0]
            if head != expected_head:
                raise LibraryRefused("stale_head", f"{on} of {item} is at {head}")
            parents = list(draft.parents) if draft.parents is not None else [h for h in [head] if h]
            object_id, _ = self._mint(who, draft, item, parents)
            if object_id == head:
                return Commit(object_id, item, on, head, self._seq)
            return self._move(who, item, on, object_id)

    def relate(self, who: Principal, from_id: ObjectId, relation: str, to_id: ObjectId) -> str:
        name = normalised(relation)
        if name not in RELATIONS:
            raise LibraryRefused("unknown_relation", f"{relation!r} is not a relation")
        with self._writing():
            self._require(from_id)
            self._require(to_id)
            edge_id = fp1({"from": from_id, "type": name, "to": to_id})
            seen = self.catalog.db.execute(
                "SELECT 1 FROM relations WHERE from_id = ? AND type = ? AND to_id = ? "
                "AND origin = 'edge'",
                (from_id, name, to_id),
            ).fetchone()
            if seen is None:
                self._edge_seq += 1
                edge = {
                    "seq": self._edge_seq,
                    "edge_id": edge_id,
                    "from": from_id,
                    "type": name,
                    "to": to_id,
                    "writer": str(who),
                    "at": self._now(),
                }
                _append(self.edge_log, edge)
                self.catalog.index_edge(edge)
        return edge_id

    def branch(self, who: Principal, item: str, *, from_ref: str, name: str) -> Commit:
        self._check_owner(who, name, "put")
        with self._writing():
            if self.catalog.head(item, name) is not None:
                raise LibraryRefused("stale_head", f"{name} of {item} exists")
            return self._move(who, item, name, self.resolve(who, item, from_ref))

    def annotate(self, who: Principal, object_id: ObjectId, values: JsonObject) -> None:
        """Annotation fields the object's kind accepts; no new version (AD-2). The operator and
        the engine annotate anything, another principal only objects on refs it owns."""
        with self._writing():
            row = self._require(object_id)
            spec = kind(str(row[2]))
            refused = sorted(set(values) - spec.annotations)
            if refused:
                raise LibraryRefused(
                    "annotation_not_accepted", f"a {spec.name} takes no {refused[0]}"
                )
            if who.who != "operator" and who != self.engine:
                refs = self.catalog.db.execute(
                    "SELECT DISTINCT ref FROM moves WHERE new_head = ?", (object_id,)
                )
                if not any(may_advance(who, str(r), "put", store=self.name) for (r,) in refs):
                    raise LibraryRefused("ref_not_owned", f"{who} owns no ref of {object_id}")
            self._annotate(who, object_id, cast(JsonObject, self.redactor.redact_json(values)[0]))

    def archive(
        self, who: Principal, item: str, reason: str, *, replaced_by: str | None = None
    ) -> None:
        """Archive, never delete (AD-6): a move of `refs/items/<item>/state`; no object changes."""
        self._check_owner(who, state_ref(item), "state")
        with self._writing():
            if self.catalog.state(item) is None:
                raise LibraryRefused("not_found", f"no item {item}")
            self._move(
                who, item, state_ref(item), "archived", reason=reason, replaced_by=replaced_by
            )

    def merge(
        self,
        who: Principal,
        item: str,
        *,
        from_ref: str,
        into: str,
        strategy: Strategy = "auto",
    ) -> MergeResult:
        """Merge `from_ref` into `into`. A fast-forward moves the ref; otherwise `auto` merges
        three ways, field by field and blob slot by slot, and `ff-only` stops. Anything that
        cannot merge cleanly becomes a `merge-conflict` object; a conflict never picks a side.
        The engine merges only to land a run's objects: records onto `main`, every other class
        onto `refs/drafts/<item>` (AD-18)."""
        act: Act = "land" if who == self.engine else "merge"
        self._check_owner(who, into, act)
        with self._writing():
            self._active(item)
            theirs = self.resolve(who, item, from_ref)
            if act == "land":
                klass = cast(Class, self._require(theirs)[3])
                if (into == MAIN) != (klass == "record"):
                    raise LibraryRefused("ref_not_owned", f"a run's {klass} never lands on {into}")
            found = self.catalog.head(item, into)
            ours = None if found is None else found[0]
            if ours == theirs or (ours is not None and self._descends(ours, theirs)):
                return MergeResult("up-to-date", ours or theirs)
            if ours is None or self._descends(theirs, ours):
                self._move(who, item, into, theirs, reason=f"merge {from_ref}")
                return MergeResult("fast-forward", theirs)
            if strategy == "ff-only":
                return self._conflict(who, item, into, None, ours, theirs, [{"path": "history"}])
            return self._three_way(who, item, into, from_ref, ours, theirs)

    def _descends(self, child: ObjectId, ancestor: ObjectId) -> bool:
        return ancestor in self._ancestry(child)

    def _ancestry(self, start: ObjectId) -> dict[ObjectId, int]:
        """Every ancestor of `start` (itself included) and its distance."""
        seen = {start: 0}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for parent in self.catalog.parents(node):
                if parent not in seen:
                    seen[parent] = seen[node] + 1
                    queue.append(parent)
        return seen

    def _three_way(
        self, who: Principal, item: str, into: str, from_ref: str, ours: ObjectId, theirs: ObjectId
    ) -> MergeResult:
        mine, other = self._ancestry(ours), self._ancestry(theirs)
        common = [(mine[o] + other[o], o) for o in mine.keys() & other.keys()]
        base = min(common)[1] if common else None
        views = [self._view(o) if o else None for o in (base, ours, theirs)]
        b, o, t = views[0], cast(ObjectView, views[1]), cast(ObjectView, views[2])
        entries: list[JsonObject] = []

        def pick(path: str, base_v: object, ours_v: object, theirs_v: object) -> object:
            if theirs_v in (ours_v, base_v):
                return ours_v
            if ours_v == base_v:
                return theirs_v
            entries.append({"path": path})
            return ours_v

        fields: JsonObject = {}
        for key in sorted(o.fields.keys() | t.fields.keys()):
            value = pick(
                f"fields.{key}",
                b.fields.get(key) if b else None,
                o.fields.get(key),
                t.fields.get(key),
            )
            if value is not None:
                fields[key] = cast(JsonValue, value)
        title = pick("title", b.title if b else None, o.title, t.title)
        summary = pick("summary", b.summary if b else None, o.summary, t.summary)
        blobs: dict[str, BlobRef] = {}
        for slot in sorted(o.blobs.keys() | t.blobs.keys()):
            ours_b, theirs_b = o.blobs.get(slot), t.blobs.get(slot)
            base_b = b.blobs.get(slot) if b else None
            chosen = pick(
                f"blobs.{slot}",
                base_b and base_b.blob_id,
                ours_b and ours_b.blob_id,
                theirs_b and theirs_b.blob_id,
            )
            if isinstance(chosen, str):
                blobs[slot] = BlobRef(chosen)
        if entries:
            return self._conflict(who, item, into, base, ours, theirs, entries)
        relations: dict[Relation, None] = dict.fromkeys([*o.relations, *t.relations])
        relations |= dict.fromkeys([("merged-from", ours), ("merged-from", theirs)])
        draft = Draft(
            o.kind,
            item,
            str(title),
            str(summary),
            fields,
            blobs,
            list(relations),
            [ours, theirs],
        )
        object_id, _ = self._mint(who, draft, item, [ours, theirs])
        self._move(who, item, into, object_id, reason=f"merge {from_ref}")
        return MergeResult("merged", object_id)

    def _conflict(
        self,
        who: Principal,
        item: str,
        into: str,
        base: ObjectId | None,
        ours: ObjectId,
        theirs: ObjectId,
        entries: list[JsonObject],
    ) -> MergeResult:
        ref = f"refs/conflicts/{item}/{self.catalog.refs_like(f'refs/conflicts/{item}/') + 1}"
        fields: JsonObject = {
            "base": base,
            "ours": ours,
            "theirs": theirs,
            "into": into,
            "entries": cast(list[JsonValue], entries),
        }
        draft = Draft("merge-conflict", title=f"Conflict merging into {into}", fields=fields)
        conflict = str(uuid.uuid7())
        object_id, _ = self._mint(who, draft, conflict, [])
        self._move(who, conflict, ref, object_id, reason=f"conflict on {item}")
        return MergeResult("conflict", object_id)

    def checkout(self, who: Principal, item: str, ref: str = MAIN) -> Path:
        """A working copy of `item` at `ref`, in the folder of the ref `who` writes to (AD-20).
        The checkout is never evidence; `commit` reads it back."""
        head = self.resolve(who, item, ref)
        view = self.get(who, head, blobs="fetch")
        target = own_ref(who, item, ref)
        folder = self.root / "checkout" / target / item
        shutil.rmtree(folder, ignore_errors=True)
        (folder / "blobs").mkdir(parents=True)
        manifest = {
            "kind": view.kind,
            "title": view.title,
            "summary": view.summary,
            "fields": view.fields,
        }
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        for slot, data in view.data.items():
            path = folder / "blobs" / slot
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        found = self.catalog.head(item, target)
        state = {"item": item, "ref": target, "base": head, "head": found and found[0]}
        (folder / CHECKOUT_FILE).write_text(json.dumps(state), encoding="utf-8")
        return folder

    def commit(
        self,
        who: Principal,
        checkout: Path,
        message: str = "",
        *,
        expected_head: ObjectId | None = None,
    ) -> Commit:
        """Put the edited working copy onto its ref, parented on the object it was checked out
        from. `expected_head` defaults to the ref's head when it was checked out."""
        state = cast(dict[str, Any], json.loads((checkout / CHECKOUT_FILE).read_text("utf-8")))
        manifest = cast(dict[str, Any], json.loads((checkout / "manifest.json").read_text("utf-8")))
        blobs = {
            path.relative_to(checkout / "blobs").as_posix(): path.read_bytes()
            for path in sorted((checkout / "blobs").rglob("*"))
            if path.is_file()
        }
        draft = Draft(
            str(manifest["kind"]),
            str(state["item"]),
            str(manifest["title"]),
            str(manifest["summary"]),
            cast(JsonObject, manifest["fields"]),
            blobs,
            parents=[str(state["base"])],
        )
        expected = expected_head if expected_head is not None else state["head"]
        done = self.put(who, draft, on=str(state["ref"]), expected_head=expected)
        if message:
            self.annotate(who, done.object_id, {"tags": [f"commit: {message}"]})
        return done

    def resolve(
        self, who: Principal, item: str, ref: str = MAIN, *, as_of: AsOf | None = None
    ) -> ObjectId:
        with self._mutex:
            if as_of is None:
                found = self.catalog.head(item, ref)
                head = None if found is None else found[0]
            else:
                row = self.catalog.db.execute(
                    "SELECT new_head FROM moves WHERE item = ? AND ref = ? AND seq <= ? "
                    "ORDER BY seq DESC LIMIT 1",
                    (item, ref, self._cut(as_of)[0]),
                ).fetchone()
                head = None if row is None else str(row[0])
        if head is None:
            raise LibraryRefused("not_found", f"{item} has no {ref}")
        return head

    def _cut(self, as_of: AsOf) -> tuple[int, str]:
        """The last ref-log position and the time `as_of` names; `(0, "")` before the first."""
        db = self.catalog.db
        if isinstance(as_of, int):
            row = db.execute(
                "SELECT seq, at FROM moves WHERE seq <= ? ORDER BY seq DESC LIMIT 1", (as_of,)
            ).fetchone()
            return (0, "") if row is None else (int(row[0]), str(row[1]))
        at = as_of.astimezone(UTC).isoformat().replace("+00:00", "Z")
        (seq,) = db.execute(
            "SELECT coalesce(max(seq), 0) FROM moves WHERE julianday(at) <= julianday(?)", (at,)
        ).fetchone()
        return int(seq), at

    def _placed_by(self, object_id: ObjectId, seq: int) -> bool:
        row = self.catalog.db.execute(
            "SELECT 1 FROM moves WHERE new_head = ? AND seq <= ? LIMIT 1", (object_id, seq)
        ).fetchone()
        return row is not None

    def _view(self, object_id: ObjectId) -> ObjectView:
        row = self._require(object_id)
        _, item, kind_name, klass, title, summary, fields, blobs, parents, relations = row
        return ObjectView(
            object_id,
            str(item),
            str(kind_name),
            cast(Class, klass),
            str(title),
            str(summary),
            json.loads(fields),
            {
                slot: BlobView(spec["sha256"], spec["size"], spec["media_type"])
                for slot, spec in cast(dict[str, dict[str, Any]], json.loads(blobs)).items()
            },
            tuple(json.loads(parents)),
            tuple((r["type"], r["to"]) for r in json.loads(relations)),
            self.catalog.annotations(object_id),
            {r["to"]: r["locator"] for r in json.loads(relations) if "locator" in r},
        )

    def get(
        self,
        who: Principal,
        object_id: ObjectId,
        *,
        blobs: Literal["meta", "fetch"] = "meta",
        as_of: AsOf | None = None,
    ) -> ObjectView:
        """The object; with `as_of`, refused `not_found` unless a ref held it by then, and its
        annotations as they stood then."""
        with self._mutex:
            view = self._view(object_id)
            if as_of is not None:
                seq, at = self._cut(as_of)
                if not self._placed_by(object_id, seq):
                    raise LibraryRefused("not_found", f"no object {object_id} as of {as_of}")
                rows = self.catalog.db.execute(
                    "SELECT key, value FROM annotations WHERE object_id = ? "
                    "AND julianday(at) <= julianday(?) ORDER BY seq",
                    (object_id, at),
                )
                view = replace(view, annotations={str(k): json.loads(v) for k, v in rows})
        if blobs == "meta":
            return view
        spec = kind(view.kind)
        data = {
            slot: self.read_blob(blob.blob_id, transient=spec.slot(slot).transient)
            for slot, blob in view.blobs.items()
        }
        return replace(view, data=data)

    def read_blob(self, blob_id: str, *, transient: bool = False) -> bytes:
        path = self._blob_path(blob_id, transient=transient)
        if not path.exists():
            raise LibraryRefused("blob_unavailable", f"no blob {blob_id}")
        data = path.read_bytes()
        if f"sha256:{sha256(data).hexdigest()}" != blob_id:
            raise LibraryRefused("corrupt_blob", f"{blob_id} does not hash to its name")
        return data

    def search(
        self,
        who: Principal,
        text: str,
        *,
        kind: str | None = None,
        include_archived: bool = False,
        limit: int = 20,
        as_of: AsOf | None = None,
    ) -> list[Hit]:
        """FTS5 over the objects; with `as_of`, over the objects that were the head of a ref
        then, and the items active then."""
        with self._mutex:
            if as_of is None:
                return self.catalog.search(text, kind, include_archived, limit)
            words = norm(text).split()
            if not words:
                raise LibraryRefused("invalid_search", "the search names no word")
            seq, _ = self._cut(as_of)
            rows = self.catalog.db.execute(
                "SELECT s.object_id, s.item, s.kind, s.title, bm25(search) AS rank FROM search s "
                "WHERE search MATCH :query AND (:kind IS NULL OR s.kind = :kind) "
                "AND EXISTS (SELECT 1 FROM moves m WHERE m.new_head = s.object_id "
                "  AND m.seq <= :seq AND NOT EXISTS (SELECT 1 FROM moves n WHERE n.item = m.item"
                "  AND n.ref = m.ref AND n.seq > m.seq AND n.seq <= :seq)) "
                "AND (:archived OR coalesce((SELECT new_head FROM moves WHERE item = s.item "
                "  AND ref = 'refs/items/' || s.item || '/state' AND seq <= :seq "
                "  ORDER BY seq DESC LIMIT 1), 'active') <> 'archived') "
                "ORDER BY rank, s.item, s.object_id",
                {
                    "query": " ".join(f'"{word}"' for word in words),
                    "kind": kind,
                    "seq": seq,
                    "archived": include_archived,
                },
            )
            best: dict[str, Hit] = {}
            for object_id, item, found_kind, title, rank in rows:
                best.setdefault(
                    str(item), Hit(str(object_id), str(item), str(found_kind), str(title), -rank)
                )
                if len(best) == limit:
                    break
            return list(best.values())

    def search_runs(self, who: Principal, text: str, workflow: str | None = None) -> list[Hit]:
        hits = self.search(who, text, kind="workflow-run", limit=1000)
        if workflow is None:
            return hits
        return [h for h in hits if self._view(h.object_id).fields.get("workflow_item") == workflow]

    def walk(
        self,
        who: Principal,
        start: Sequence[ObjectId],
        types: Sequence[str] = (),
        direction: Literal["out", "in", "both"] = "out",
        depth: int = 2,
        *,
        as_of: AsOf | None = None,
    ) -> list[Step]:
        """With `as_of`, only edges written by then, to objects a ref held by then."""
        wanted = {normalised(t) for t in types}
        seen = set(start)
        steps: list[Step] = []
        frontier = list(start)
        with self._mutex:
            cut = None if as_of is None else self._cut(as_of)
            for level in range(1, depth + 1):
                reached: list[str] = []
                for node in frontier:
                    found = [
                        *(self._relations(node, False, cut) if direction != "in" else []),
                        *(self._relations(node, True, cut) if direction != "out" else []),
                    ]
                    for other, relation, origin in found:
                        if (wanted and relation not in wanted) or other in seen:
                            continue
                        seen.add(other)
                        reached.append(other)
                        steps.append(Step(other, relation, cast(Any, origin), level))
                frontier = reached
        return steps

    def _relations(
        self, node: ObjectId, reverse: bool, cut: tuple[int, str] | None
    ) -> list[tuple[str, str, str]]:
        if cut is None:
            return self.catalog.relations_of(node, reverse=reverse)
        mine, other = ("to_id", "from_id") if reverse else ("from_id", "to_id")
        rows = self.catalog.db.execute(
            f"SELECT {other}, type, origin FROM relations WHERE {mine} = ? "  # noqa: S608
            "AND (origin = 'birth' OR julianday(at) <= julianday(?)) "
            f"AND EXISTS (SELECT 1 FROM moves m WHERE m.new_head = {other} AND m.seq <= ?) "
            "ORDER BY coalesce(seq, 0)",
            (node, cut[1], cut[0]),
        )
        return [(str(a), str(b), str(c)) for a, b, c in rows]

    def marks(self, who: Principal, object_id: ObjectId) -> Marks:
        """The worst mark on `object_id` or upstream of it, with its path (AD-22)."""
        with self._mutex:
            self._require(object_id)
            return marks(self.catalog.db, object_id)

    def mark(self, who: Principal, item: str, quarantined: bool, reason: str) -> None:
        """Set or clear `quarantined` on `item`: a move of `refs/items/<item>/marks`, by the
        operator alone (AD-22)."""
        if who.who != "operator":
            raise LibraryRefused("ref_not_owned", f"{who} may not mark {item}; the operator marks")
        with self._writing():
            if self.catalog.state(item) is None:
                raise LibraryRefused("not_found", f"no item {item}")
            value = QUARANTINED if quarantined else CLEAR
            self._move(who, item, marks_ref(item), value, reason=reason)

    def ground(self, who: Principal, text: str) -> Grounding:
        """Items whose title, tag or alias occurs in `text`, longest alias first; no model."""
        rest = f" {norm(text)} "
        items: list[str] = []
        with self._mutex:
            for alias, item in self.catalog.aliases():
                if f" {alias} " in rest and self.catalog.state(item) == "active":
                    rest = rest.replace(f" {alias} ", "  ")
                    if item not in items:
                        items.append(item)
        return Grounding(tuple(items), "grounded" if items else "no_entry_point")

    def find_by_intent(self, who: Principal, intent_key: str) -> list[ObjectId]:
        """Active objects annotated with `intent_key` whose producing run passed (engine L6)."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT a.object_id FROM annotations a "
                "JOIN objects o ON o.object_id = a.object_id "
                "JOIN items i ON i.item = o.item AND i.state = 'active' "
                "WHERE a.key = 'intent_key' AND a.value = ? AND a.seq = ("
                "  SELECT max(seq) FROM annotations WHERE object_id = a.object_id "
                "  AND key = 'intent_key') "
                "AND EXISTS (SELECT 1 FROM relations r JOIN objects run ON run.object_id = r.to_id "
                "  WHERE r.from_id = a.object_id AND r.type = 'produced-by' "
                "  AND json_extract(run.fields, '$.status') = 'passed') "
                "ORDER BY a.seq",
                (json.dumps(intent_key),),
            )
            return [str(object_id) for (object_id,) in rows]

    def head(self, item: str, ref: str) -> tuple[ObjectId, int] | None:
        """The head of `ref` for `item` and how many times it has moved."""
        with self._mutex:
            return self.catalog.head(item, ref)

    def placed(self, item: str, kind_name: str, ref: str | None) -> list[tuple[ObjectId, str]]:
        """Objects of `kind_name` that were ever a head of `item` (on `ref` when given), in the
        order they first became one, each with the first ref it reached."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT m.new_head, m.ref FROM moves m JOIN objects o ON o.object_id = m.new_head "
                "WHERE m.item = ? AND o.kind = ? AND (? IS NULL OR m.ref = ?) ORDER BY m.seq",
                (item, kind_name, ref, ref),
            )
            seen: dict[str, str] = {}
            for object_id, first in rows:
                seen.setdefault(str(object_id), str(first))
            return list(seen.items())

    def placement(self, object_id: ObjectId) -> tuple[str, str, str] | None:
        """`(ref, principal, at)` of the first move to `object_id`, `main` if it ever reached
        `main`."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT ref, principal, at FROM moves WHERE new_head = ? ORDER BY seq",
                (object_id,),
            ).fetchall()
        if not rows:
            return None
        ref, principal, at = rows[0]
        if any(r[0] == MAIN for r in rows):
            ref = MAIN
        return str(ref), str(principal), str(at)

    def history(self, item: str) -> list[tuple[str, str, str]]:
        """`(kind, ref, principal)` of every move of `item` to an object, oldest first."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT o.kind, m.ref, m.principal FROM moves m "
                "JOIN objects o ON o.object_id = m.new_head WHERE m.item = ? ORDER BY m.seq",
                (item,),
            )
            return [(str(kind), str(ref), str(who)) for kind, ref, who in rows]

    def placements(self, after: int = 0) -> list[dict[str, Any]]:
        """The ref moves after `after` that placed an object for the first time."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT m.seq, m.item, m.ref, m.new_head, o.kind FROM moves m "
                "JOIN objects o ON o.object_id = m.new_head WHERE m.seq > ? "
                "AND m.seq = (SELECT min(seq) FROM moves WHERE new_head = m.new_head) "
                "ORDER BY m.seq",
                (after,),
            )
            keys = ("seq", "item", "ref", "new_head", "kind")
            return [dict(zip(keys, row, strict=True)) for row in rows]

    def heads_on(self, ref: str) -> list[tuple[str, ObjectId]]:
        with self._mutex:
            return self.catalog.heads_on(ref)

    def has_item(self, item: str) -> bool:
        with self._mutex:
            return self.catalog.state(item) is not None

    def edges_of(
        self, object_id: ObjectId, *, reverse: bool
    ) -> list[tuple[str, str, str, str, str]]:
        """After-birth edges `(from, type, to, writer, at)` out of `object_id`, or into it."""
        mine = "to_id" if reverse else "from_id"
        with self._mutex:
            rows = self.catalog.db.execute(
                f"SELECT from_id, type, to_id, writer, at FROM relations WHERE {mine} = ? "  # noqa: S608
                "AND origin = 'edge' ORDER BY seq",
                (object_id,),
            )
            return [(str(a), str(b), str(c), str(d), str(e)) for a, b, c, d, e in rows]

    def with_field(self, kind_name: str, key: str, value: str) -> list[ObjectId]:
        """Objects of `kind_name` whose `fields.<key>` is `value`, in the order they were placed."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT o.object_id FROM objects o JOIN moves m ON m.new_head = o.object_id "
                "WHERE o.kind = ? AND json_extract(o.fields, '$.' || ?) = ? "
                "GROUP BY o.object_id ORDER BY min(m.seq)",
                (kind_name, key, value),
            )
            return [str(object_id) for (object_id,) in rows]

    def advance(
        self,
        who: Principal,
        item: str,
        ref: str,
        new_head: ObjectId,
        *,
        expected_head: ObjectId | None,
    ) -> Commit:
        """Move `ref` to an object already stored, by compare-and-swap (AD-2)."""
        self._check_owner(who, ref, "put")
        with self._writing():
            self._require(new_head)
            found = self.catalog.head(item, ref)
            head = None if found is None else found[0]
            if head != expected_head:
                raise LibraryRefused("stale_head", f"{ref} of {item} is at {head}")
            if head == new_head:
                return Commit(new_head, item, ref, head, self._seq)
            return self._move(who, item, ref, new_head)

    def put_transient(self, who: Principal, ref: str, data: bytes) -> str:
        """A transient blob (a checkpoint) for a run that owns `ref`: kept on this store only,
        never bucketed (AD-6)."""
        self._check_owner(who, ref, "put")
        with self._mutex:
            data = self._redacted(data)
            blob_id = f"sha256:{sha256(data).hexdigest()}"
            _write_once(self._blob_path(blob_id, transient=True), data)
            return blob_id
