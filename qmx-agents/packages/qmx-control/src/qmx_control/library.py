"""The home's one Library: the content store at `<home>/library/`, in the documents the doors serve.

MIGRATION step 6 retired `library.db`, so nothing here keeps a second copy of an item. A save is one
`LibraryPort` put (Library AD-1, AD-9), a version chain is the object's parents, a link is an edge,
and a search is the store's index. The old document shape the REST and MCP doors, the copilot's
tools and the UI read is built from the object, so the cut-over changes where an item lives and not
what a caller sees.

The host that owns the store hands it over with `attach`; a process with no host (a test, a script)
opens the home's store itself, and one process holds one writer per home.
"""

from __future__ import annotations

import json
import threading
import uuid
import weakref
from collections.abc import Callable
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Final, cast

from pydantic import JsonValue
from qmx_apps.artifacts import Landing
from qmx_library.kinds import kind
from qmx_library.port import Commit, Draft, JsonObject, LibraryRefused, ObjectId, ObjectView
from qmx_library.principal import MAIN, Principal, drafts_ref
from qmx_library.store import Store

from qmx_control.models import ControlError, Document, LibraryInput, MemoKey

OPERATOR: Final = Principal("operator")
LIBRARY: Final = "library"
KINDS: Final = {"article": "source", "backtest": "backtest-result"}
"""The old kind strings the store has a kind of its own for; every other string is an `artifact`."""
SLOTS: Final = {"source": "content", "artifact": "content", "backtest-result": "report"}
"""The blob slot each store kind's schema names for the old `content`."""
ERRORS: Final = {"not_found": 404, "storage_failure": 409, "read_only_replica": 409}


def encoded(value: JsonValue) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


class Unredacted:
    """The redaction seam of a process that was handed no host redactor (AD-37)."""

    def redact(self, text: str) -> str:
        return text

    def redact_json(self, value: object) -> tuple[JsonValue, int]:
        return cast(JsonValue, value), 0

    def holds_value(self, data: bytes) -> bool:
        return False


WRITING: Final = Unredacted()
_STORES: weakref.WeakValueDictionary[Path, Store] = weakref.WeakValueDictionary()
_STORES_LOCK: Final = threading.Lock()


def open_store(home: Path) -> Store:
    """The one writer of `<home>/library/` this process uses, opened on first use."""
    root = (home / LIBRARY).resolve()
    with _STORES_LOCK:
        found = _STORES.get(root)
        if found is not None:
            return found
        opened = Store.open(root, redactor=WRITING, name="pc")
        _STORES[root] = opened
        return opened


def slot_of(view: ObjectView) -> str:
    return SLOTS.get(view.kind) or next(iter(view.blobs), "")


def refused(error: LibraryRefused) -> ControlError:
    """The store's refusal as the control door's error."""
    message = str(error).split(": ", 1)[-1]
    return ControlError(error.code, message, ERRORS.get(error.code, 400))


class Library:
    def __init__(self, home: Path) -> None:
        self.home = home
        self._store: Store | None = None
        self._lock = threading.RLock()

    def attach(self, store: Store) -> None:
        """The host's store is this home's Library from now on (MIGRATION step 6)."""
        self._store = store

    @property
    def store(self) -> Store:
        with self._lock:
            if self._store is None:
                self._store = open_store(self.home)
            return self._store

    def close(self) -> None:
        """Drop this process's writer on `<home>/library/`, so the next step may open it."""
        with self._lock:
            found, self._store = self._store, None
        if found is None:
            return
        with _STORES_LOCK:
            if _STORES.get(found.root) is found:
                del _STORES[found.root]
        found.close()

    def save(self, item: LibraryInput, *, memo_key: str | None = None) -> Document:
        """Save one object: a new one, a version of `previous_id`, or the day's fetch."""
        try:
            body = encoded(item.content)
        except ValueError as error:
            raise ControlError(
                "invalid_content", "Artifact content must contain finite JSON values."
            ) from error
        self._fetched_source(item)
        with self._lock:
            known = self._fetched(item)
            if known is not None:
                return self._document(known)
            parent = self._previous(item)
            store_kind = KINDS.get(item.kind, "artifact")
            fields: JsonObject = {"legacy_kind": item.kind}
            if store_kind == "source":
                fields["url"] = item.source
                if item.fetched_date:
                    fields["fetched_date"] = item.fetched_date
            if item.extracted_text:
                # The old Library indexed the extracted text beside the source URL; the store
                # indexes every string in `fields`, so the text stays findable without a slot.
                fields["extracted_text"] = item.extracted_text
            if memo_key is not None:
                fields["memo_key"] = memo_key
            item_id = parent[0] if parent is not None else str(uuid.uuid7())
            draft = Draft(
                store_kind,
                item_id,
                title=item.title,
                fields=fields,
                blobs={SLOTS[store_kind]: body},
                parents=[parent[1]] if parent is not None else [],
                tags=list(item.tags),
            )
            try:
                commit = self._land(draft)
            except LibraryRefused as error:
                raise refused(error) from error
            return self._document(commit.object_id)

    def get(self, artifact_id: str) -> Document:
        """Read one object with its verified content."""
        return self._document(artifact_id)

    def by_ref(self, ref: str) -> Document:
        """The object an `artifacts/<sha256>` reference names."""
        name = ref.removesuffix(".json")
        if not name.startswith("artifacts/"):
            raise ControlError(
                "not_found", "Use an artifacts/<sha256> reference from the Library.", 404
            )
        digest = f"sha256:{name.removeprefix('artifacts/')}"
        row = self.store.catalog.db.execute(
            "SELECT object_id FROM objects WHERE "
            "json_extract(blobs, '$.content.sha256') = ? OR "
            "json_extract(blobs, '$.report.sha256') = ? ORDER BY rowid LIMIT 1",
            (digest, digest),
        ).fetchone()
        if row is None:
            raise ControlError(
                "not_found", "Use an artifacts/<sha256> reference from the Library.", 404
            )
        return self._document(str(row[0]))

    def search(self, query: str = "", offset: int = 0, limit: int = 100) -> list[Document]:
        """The store's index over titles, tags and text, or every object when `query` is blank."""
        if offset < 0 or not 1 <= limit <= 1000:
            raise ControlError("invalid_page", "Use offset >= 0 and limit between 1 and 1000.")
        if not query.strip():
            placed = [str(p["new_head"]) for p in self.store.placements(0)]
            return [self._document(found) for found in placed[offset : offset + limit]]
        try:
            hits = self.store.search(OPERATOR, query, limit=offset + limit)
        except LibraryRefused as error:
            raise refused(error) from error
        return [self._document(hit.object_id) for hit in hits[offset:]]

    def tagged(self, tag: str) -> list[Document]:
        """The latest version of every object carrying `tag`."""
        rows = self.store.catalog.db.execute(
            "SELECT a.object_id FROM annotations a, json_each(a.value) j "
            "WHERE a.key = 'tags' AND j.value = ? ORDER BY a.seq",
            (tag,),
        ).fetchall()
        latest: dict[str, tuple[int, str]] = {}
        for (object_id,) in rows:
            view = self._view(str(object_id))
            depth = len(self.store.ancestry_of(view.object_id))
            held = latest.get(view.item)
            if held is None or held[0] < depth:
                latest[view.item] = (depth, view.object_id)
        found = [self._document(object_id) for _, object_id in latest.values()]
        return sorted(found, key=lambda item: str(item["created"]))

    def versions(self, artifact_id: str) -> list[Document]:
        """One item's immutable version chain, oldest first."""
        view = self._view(artifact_id)
        return [self._document(found) for found, _ in self.store.placed(view.item, view.kind, MAIN)]

    def count(self, query: str = "") -> int:
        """How many items the Library holds, or how many answer `query`."""
        if query.strip():
            return len(self.search(query, limit=1000))
        (found,) = self.store.catalog.db.execute("SELECT count(*) FROM items").fetchone()
        return int(found)

    def link(self, source_id: str, target_id: str, relation: str = "related") -> Document:
        """Link two existing objects without changing their contents."""
        self._view(source_id)
        self._view(target_id)
        if not relation.strip():
            raise ControlError("invalid_relation", "Supply a link relation.")
        try:
            self.store.relate(OPERATOR, source_id, relation, target_id)
        except LibraryRefused as error:
            raise refused(error) from error
        return {"source_id": source_id, "target_id": target_id, "relation": relation}

    def links(self, artifact_id: str) -> list[Document]:
        """Incoming and outgoing links of one object."""
        self._view(artifact_id)
        out = self.store.edges_of(artifact_id, reverse=False)
        into = self.store.edges_of(artifact_id, reverse=True)
        return [
            {"source_id": source, "target_id": target, "relation": relation}
            for source, relation, target, *_ in (*out, *into)
        ]

    def memoized(self, identity: MemoKey, produce: Callable[[], LibraryInput]) -> Document:
        """Reuse a deterministic result, recording newly computed ones under their memo key."""
        key = sha256(encoded(identity.model_dump(mode="json"))).hexdigest()
        # The one writer serializes identical work so two callers cannot compute the same result.
        with self._lock:
            found = self._memo(key)
            if found is not None:
                return {**self._document(found), "memo_key": key}
            return {**self.save(produce(), memo_key=key), "memo_key": key}

    def instance(self, app: str) -> ObjectId:
        """The `mini-app-instance` of `app`, put on first use (MIGRATION step 4)."""
        row = self.store.catalog.db.execute(
            "SELECT object_id FROM objects WHERE kind = 'mini-app-instance' "
            "AND json_extract(fields, '$.legacy_app') = ? ORDER BY rowid LIMIT 1",
            (app,),
        ).fetchone()
        if row is not None:
            return str(row[0])
        draft = Draft(
            "mini-app-instance",
            str(uuid.uuid7()),
            title=app,
            fields={"legacy_app": app, "app_id": app},
        )
        return self._land(draft).object_id

    def component(self, app: str, output: str, schema: JsonValue) -> ObjectId:
        """The `component` holding one output's `provides` schema (MIGRATION step 4)."""
        key = sha256(json.dumps([app, output, schema], sort_keys=True).encode()).hexdigest()
        row = self.store.catalog.db.execute(
            "SELECT object_id FROM objects WHERE kind = 'component' "
            "AND json_extract(fields, '$.legacy_provides') = ? ORDER BY rowid LIMIT 1",
            (key,),
        ).fetchone()
        if row is not None:
            return str(row[0])
        draft = Draft(
            "component",
            str(uuid.uuid7()),
            title=f"{app} {output}",
            fields={
                "legacy_provides": key,
                "app_id": app,
                "output": output,
                "schema": schema,
            },
        )
        return self._land(draft).object_id

    def landed(self, landing: Landing) -> ObjectId:
        """One app output as one `artifact` (AD-64), `produced-by` its instance."""
        ref = landing.ref
        row = self.store.catalog.db.execute(
            "SELECT object_id FROM objects WHERE json_extract(fields, '$.legacy_ref') = ? "
            "ORDER BY rowid LIMIT 1",
            (ref.model_dump_json(),),
        ).fetchone()
        if row is not None:
            return str(row[0])
        fields: JsonObject = {
            **cast(JsonObject, landing.fields),
            "legacy_ref": ref.model_dump_json(),
            "legacy_kind": "app-output",
            "output": landing.output,
            "definition_hash": ref.definition_hash,
            "producer_app": ref.producer_app,
        }
        draft = Draft(
            "artifact",
            str(uuid.uuid7()),
            title=f"{landing.app_id} {landing.output}"[:200],
            fields=fields,
            blobs={"content": encoded(landing.data)},
            relations=[
                ("produced-by", self.instance(landing.app_id)),
                ("instance-of", self.component(landing.app_id, landing.output, landing.schema)),
            ],
            tags=[landing.app_id, landing.output],
        )
        try:
            return self._land(draft).object_id
        except LibraryRefused as error:
            raise refused(error) from error

    def _land(self, draft: Draft) -> Commit:
        """A record directly onto `main`; any other class through its draft ref and a merge."""
        store = self.store
        item = str(draft.item)
        if kind(draft.kind).klass == "record":
            head = store.head(item, MAIN)
            return store.put(
                OPERATOR, draft, on=MAIN, expected_head=None if head is None else head[0]
            )
        ref = drafts_ref(item)
        head = store.head(item, ref)
        done = store.put(OPERATOR, draft, on=ref, expected_head=None if head is None else head[0])
        store.merge(OPERATOR, item, from_ref=ref, into=MAIN, strategy="ff-only")
        return done

    def _fetched_source(self, item: LibraryInput) -> None:
        if not item.fetched_date:
            return
        if not item.source:
            raise ControlError("source_required", "A fetched result needs its source URL.")
        try:
            datetime.strptime(item.fetched_date, "%Y-%m-%d")
        except ValueError as error:
            raise ControlError("invalid_date", "Use a valid YYYY-MM-DD date.") from error

    def _fetched(self, item: LibraryInput) -> ObjectId | None:
        """The object an earlier fetch of the same source on the same day saved."""
        if not item.fetched_date or not item.source:
            return None
        row = self.store.catalog.db.execute(
            "SELECT object_id FROM objects WHERE "
            "json_extract(fields, '$.url') = ? AND "
            "json_extract(fields, '$.fetched_date') = ? ORDER BY rowid LIMIT 1",
            (item.source, item.fetched_date),
        ).fetchone()
        return None if row is None else str(row[0])

    def _previous(self, item: LibraryInput) -> tuple[str, str] | None:
        """The `(item, object)` `previous_id` names, when it is this chain's latest version."""
        if not item.previous_id:
            return None
        previous = self._view(item.previous_id)
        if str(previous.fields.get("legacy_kind", previous.kind)) != item.kind:
            raise ControlError("invalid_version", "Versions must keep their artifact type.")
        head = self.store.head(previous.item, MAIN)
        if head is None or head[0] != previous.object_id:
            raise ControlError("version_conflict", "Version the latest artifact.", 409)
        return previous.item, previous.object_id

    def _memo(self, key: str) -> ObjectId | None:
        row = self.store.catalog.db.execute(
            "SELECT object_id FROM objects WHERE json_extract(fields, '$.memo_key') = ? "
            "ORDER BY rowid LIMIT 1",
            (key,),
        ).fetchone()
        return None if row is None else str(row[0])

    def _view(self, object_id: str) -> ObjectView:
        try:
            return self.store.get(OPERATOR, object_id)
        except LibraryRefused as error:
            raise refused(error) from error

    def _root(self, view: ObjectView) -> ObjectId:
        found = view
        while found.parents:
            found = self._view(found.parents[0])
        return found.object_id

    def _document(self, object_id: str) -> Document:
        try:
            view = self.store.get(OPERATOR, object_id, blobs="fetch")
        except LibraryRefused as error:
            raise refused(error) from error
        slot = slot_of(view)
        blob = view.blobs[slot]
        digest = blob.blob_id.removeprefix("sha256:")
        document: Document = {
            "id": view.object_id,
            "kind": str(view.fields.get("legacy_kind", view.kind)),
            "title": view.title,
            "tags": cast(JsonValue, view.annotations.get("tags") or []),
            "source": str(view.fields.get("url", "")),
            "created": str(view.annotations.get("created", "")),
            "root_id": self._root(view),
            "version": len(self.store.ancestry_of(view.object_id)),
            "previous_id": view.parents[0] if view.parents else None,
            "sha256": digest,
            "size": blob.size,
            "ref": f"artifacts/{digest}",
            "fetched_date": cast(JsonValue, view.fields.get("fetched_date")),
            "content": cast(JsonValue, json.loads(view.data[slot])),
        }
        if "memo_key" in view.fields:
            document["memo_key"] = view.fields["memo_key"]
        return document
