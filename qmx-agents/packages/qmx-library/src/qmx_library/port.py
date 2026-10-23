"""`LibraryPort`, the one way into the Library (Library AD-9, LLD section 7).

Every caller (the host's doors, the engine through `EngineLibraryAdapter`, later the hub and the
migrator) goes through these verbs. Every verb takes the caller's `Principal` first; the door
derives it, callers never choose it. A refusal is a `LibraryRefused` with one code from the closed
set `CODES`, never a raw exception.

There is no delete verb (AD-6, ruling 9): an item is archived, a version is superseded by a new
object, and nothing stored is ever removed. `get`, `search`, `walk` and `resolve` take an
optional `as_of`, a time or a ref-log position, answered from the ref log (46 K-26).

Three verbs landed with the Hub (LIB4). `claim` and `release` are AD-24's compare-and-swap on
`refs/claims/<intent_key>`, called only by engine instances. `purge` is AD-6's one exception to
archive-never-delete: the operator alone, for a blob that holds a secret, a tombstone on every
copy. `adopt` is still absent; it needs the operator's recovery flow beside the Hub.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, Protocol

from pydantic import JsonValue

if TYPE_CHECKING:
    from qmx_library.marks import Marks
    from qmx_library.principal import Principal
    from qmx_library.view import CardView, Family, PageView

type JsonObject = dict[str, JsonValue]
type ObjectId = str
"""`fp1:sha256:<hex>` of the object's canonical identity bytes."""
type BlobId = str
"""`sha256:<hex>` of the blob's bytes."""
type Class = Literal["record", "definition", "governed"]
type Strategy = Literal["auto", "ff-only"]
type StoreRole = Literal["writer", "replica", "cache"]
"""What one store is for (AD-19): the `writer` is the primary store and the only one that moves
refs; a `replica` mirrors the primary's refs and objects and sends its writes to it; a `cache`
does the same and is allowed to drop a durable blob once two verified remote copies exist
(AD-10)."""
type AsOf = datetime | int
"""A time, or a ref-log position (the `seq` of a move): the store as it stood then."""
type Relation = tuple[str, ObjectId] | tuple[str, ObjectId, JsonObject]
"""`(type, to)`, or `(type, to, locator)` naming where in `to` the object came from (AD-4)."""

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
        "read_only_replica",
        "invalid_claim",
        "purge_refused",
        "blob_purged",
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
    relations: Sequence[Relation] = ()
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
    locators: Mapping[ObjectId, JsonObject] = field(default_factory=dict[ObjectId, JsonObject])
    """The locator of each at-birth relation that carries one, by its target."""
    purged: frozenset[str] = frozenset()
    """The blob slots an operator purge tombstoned; each reads `blob_purged` (AD-6)."""
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


type Role = Literal["bridge", "filter"]
"""`bridge` names one thing (a title, a tag, an alias); `filter` names a sort of thing (a kind)."""
type Producer = Literal["live-run", "operator", "agent", "run", "test-run"]
"""Who placed an object first: a passed live run, his own item (or the migrator's import of
it), an agent's draft, a run that has not passed, or a test-mode run."""
type Refusal = Literal["no_entry_point", "only_archived_or_superseded", "no_evidence_as_of"]
type Signal = Literal["too_few_concepts", "no_path", "no_quotable_terminal"]


@dataclass(frozen=True, slots=True)
class Match:
    item: str
    surface: str
    """The alias as the question spelled it, normalised."""
    role: Role


@dataclass(frozen=True, slots=True)
class Result:
    object_id: ObjectId
    item: str
    kind: str
    title: str
    preview: str
    producer: Producer
    citations: int
    via: str | None
    """None when an alias grounded the item, else the relation that admitted it."""
    source: str | None
    """The item `via` was walked from."""


@dataclass(frozen=True, slots=True)
class Answer:
    """What `qmx_library.search.answer` hands the answering step (AD-8). A refusal is a plain
    fact and carries no results; otherwise the step abstains when `abstain` is set."""

    refused: Refusal | None
    confidence: float
    abstain: bool
    signals: tuple[Signal, ...]
    matches: tuple[Match, ...]
    results: tuple[Result, ...]


@dataclass(frozen=True, slots=True)
class MergeResult:
    outcome: Literal["up-to-date", "fast-forward", "merged", "conflict"]
    object_id: ObjectId
    """The new head of `into`, or the `merge-conflict` object when the outcome is a conflict."""


@dataclass(frozen=True, slots=True)
class Claim:
    """AD-24's answer: `granted`, or `held_by(run_id, expires)` when another live run holds it and
    a claim past its `expires` may be taken by the next caller."""

    granted: bool
    run_id: str | None
    expires: datetime | None
    """When the caller's own claim runs out, or when the holder's does."""


@dataclass(frozen=True, slots=True)
class PurgeResult:
    """AD-6's one exception: the blob's bytes are gone on this store and a tombstone names why."""

    blob_id: BlobId
    ref: str
    """The transient ref the purge is recorded on, `refs/purges/<hex>`."""
    tombstone: Path


class LibraryPort(Protocol):
    def resolve(
        self, who: Principal, item: str, ref: str = "main", *, as_of: AsOf | None = None
    ) -> ObjectId: ...

    def get(
        self,
        who: Principal,
        object_id: ObjectId,
        *,
        blobs: Literal["meta", "fetch"] = "meta",
        as_of: AsOf | None = None,
    ) -> ObjectView: ...

    def search(
        self,
        who: Principal,
        text: str,
        *,
        kind: str | None = None,
        include_archived: bool = False,
        limit: int = 20,
        as_of: AsOf | None = None,
    ) -> list[Hit]: ...

    def walk(
        self,
        who: Principal,
        start: Sequence[ObjectId],
        types: Sequence[str] = (),
        direction: Literal["out", "in", "both"] = "out",
        depth: int = 2,
        *,
        as_of: AsOf | None = None,
    ) -> list[Step]: ...

    def view(
        self, who: Principal, object_id: ObjectId, level: Literal["card", "page"] = "card"
    ) -> CardView | PageView: ...

    def family(self, who: Principal, object_id: ObjectId) -> Family: ...

    def marks(self, who: Principal, object_id: ObjectId) -> Marks: ...

    def mark(self, who: Principal, item: str, quarantined: bool, reason: str) -> None: ...

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

    def claim(self, who: Principal, intent_key: str, run_id: str, ttl: int) -> Claim: ...

    def release(self, who: Principal, intent_key: str, run_id: str) -> None: ...

    def purge(self, who: Principal, blob_id: BlobId, reason: str) -> PurgeResult: ...
