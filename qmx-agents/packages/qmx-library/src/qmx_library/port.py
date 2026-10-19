"""`LibraryPort`, the one way into the Library (Library AD-9, LLD section 7).

Every caller (the host's doors, the engine through `EngineLibraryAdapter`, later the hub and the
migrator) goes through these verbs. Every verb takes the caller's `Principal` first; the door
derives it, callers never choose it. A refusal is a `LibraryRefused` with one code from the closed
set `CODES`, never a raw exception.

There is no delete verb (AD-6, ruling 9): an item is archived, a version is superseded by a new
object, and nothing stored is ever removed. `marks`, `mark`, `claim`, `release`, `purge` and
`adopt` are not here yet: marks and claims come with their own stores, and `adopt` and `purge`
need the server.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, Protocol

from pydantic import JsonValue

if TYPE_CHECKING:
    from qmx_library.principal import Principal

type JsonObject = dict[str, JsonValue]
type ObjectId = str
"""`fp1:sha256:<hex>` of the object's canonical identity bytes."""
type BlobId = str
"""`sha256:<hex>` of the blob's bytes."""
type Class = Literal["record", "definition", "governed"]
type Strategy = Literal["auto", "ff-only"]

CODES: Final = frozenset(
    {
        "unknown_kind",
        "schema_invalid",
        "unknown_relation",
        "stale_head",
        "ref_not_owned",
        "not_found",
        "corrupt_blob",
        "collision",
        "blob_unavailable",
        "merge_conflict",
        "archived",
        "storage_failure",
        "invalid_search",
        "annotation_not_accepted",
        "secret_in_blob",
    }
)

CT07: Final = frozenset(
    {
        "supersedes",
        "promoted-from",
        "occurrence-of",
        "corroborates",
        "disagrees-with",
        "confirmed-as",
        "confirmation",
        "invalidation",
        "interaction",
        "out-of-sequence",
        "continues-performance",
        "carries-ledger",
        "enacts",
        "branches-from",
    }
)
RELATIONS: Final = CT07 | frozenset(
    {
        "produced-by",
        "consumed",
        "derived-from",
        "uses",
        "part-of",
        "cites",
        "tested-by",
        "tests",
        "instance-of",
        "run-of",
        "ran-on",
        "variant-of",
        "version-of",
        "merged-from",
        "annotates",
        "replaces",
        "archived-as",
        "resolves",
        "made-by",
        "used-by",
        "compiles-to",
        "touched",
        "mentions",
        "explains",
        "related-to",
    }
)
"""AD-4's closed vocabulary: CT-07's fourteen edges verbatim plus the Library set. `ran-on` is
retired and parses, but no new code writes it."""


class LibraryRefused(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def normalised(relation: str) -> str:
    """Old callers write `_`; the engine's `supersedes` predates `replaces` (AD-4)."""
    return relation.replace("_", "-")


@dataclass(frozen=True, slots=True)
class BlobRef:
    """A blob already in the store, named by its id instead of its bytes."""

    blob_id: BlobId


@dataclass(frozen=True, slots=True)
class Draft:
    """What a caller puts. `item` None mints a new UUIDv7 item; `parents` None takes the head of
    the ref it lands on, if any."""

    kind: str
    item: str | None = None
    title: str = ""
    summary: str = ""
    fields: JsonObject = field(default_factory=dict[str, JsonValue])
    blobs: Mapping[str, bytes | BlobRef] = field(default_factory=dict[str, bytes | BlobRef])
    relations: Sequence[tuple[str, ObjectId]] = ()
    parents: Sequence[ObjectId] | None = None
    tags: Sequence[str] = ()


@dataclass(frozen=True, slots=True)
class Commit:
    object_id: ObjectId
    item: str
    ref: str
    prev_head: ObjectId | None
    seq: int


@dataclass(frozen=True, slots=True)
class BlobView:
    blob_id: BlobId
    size: int
    media_type: str


@dataclass(frozen=True, slots=True)
class ObjectView:
    object_id: ObjectId
    item: str
    kind: str
    klass: Class
    title: str
    summary: str
    fields: JsonObject
    blobs: Mapping[str, BlobView]
    parents: tuple[ObjectId, ...]
    relations: tuple[tuple[str, ObjectId], ...]
    annotations: JsonObject
    data: Mapping[str, bytes] = field(default_factory=dict[str, bytes])
    """The blob bytes by slot, filled only by `get(..., blobs="fetch")`."""


@dataclass(frozen=True, slots=True)
class Hit:
    object_id: ObjectId
    item: str
    kind: str
    title: str
    rank: float


@dataclass(frozen=True, slots=True)
class Step:
    """One object reached by `walk`, the relation that admitted it, and how far out it is."""

    object_id: ObjectId
    via: str
    origin: Literal["birth", "edge"]
    depth: int


@dataclass(frozen=True, slots=True)
class Grounding:
    items: tuple[str, ...]
    verdict: Literal["grounded", "no_entry_point"]


@dataclass(frozen=True, slots=True)
class MergeResult:
    outcome: Literal["up-to-date", "fast-forward", "merged", "conflict"]
    object_id: ObjectId
    """The new head of `into`, or the `merge-conflict` object when the outcome is a conflict."""


class LibraryPort(Protocol):
    def resolve(self, who: Principal, item: str, ref: str = "main") -> ObjectId: ...

    def get(
        self, who: Principal, object_id: ObjectId, *, blobs: Literal["meta", "fetch"] = "meta"
    ) -> ObjectView: ...

    def search(
        self,
        who: Principal,
        text: str,
        *,
        kind: str | None = None,
        include_archived: bool = False,
        limit: int = 20,
    ) -> list[Hit]: ...

    def walk(
        self,
        who: Principal,
        start: Sequence[ObjectId],
        types: Sequence[str] = (),
        direction: Literal["out", "in", "both"] = "out",
        depth: int = 2,
    ) -> list[Step]: ...

    def ground(self, who: Principal, text: str) -> Grounding: ...

    def find_by_intent(self, who: Principal, intent_key: str) -> list[ObjectId]: ...

    def search_runs(self, who: Principal, text: str, workflow: str | None = None) -> list[Hit]: ...

    def put(
        self, who: Principal, draft: Draft, *, on: str, expected_head: ObjectId | None
    ) -> Commit: ...

    def relate(self, who: Principal, from_id: ObjectId, relation: str, to_id: ObjectId) -> str: ...

    def branch(self, who: Principal, item: str, *, from_ref: str, name: str) -> Commit: ...

    def merge(
        self,
        who: Principal,
        item: str,
        *,
        from_ref: str,
        into: str,
        strategy: Strategy = "auto",
    ) -> MergeResult: ...

    def checkout(self, who: Principal, item: str, ref: str = "main") -> Path: ...

    def commit(
        self, who: Principal, checkout: Path, message: str = "", *, expected_head: ObjectId | None
    ) -> Commit: ...

    def annotate(self, who: Principal, object_id: ObjectId, values: JsonObject) -> None: ...

    def archive(
        self, who: Principal, item: str, reason: str, *, replaced_by: str | None = None
    ) -> None: ...
