"""`RecallEngine`: AD-18's memory port, over rows that are Library objects and an index that is
only ever derived data (SOLUTION-DESIGN 8.1a, 11.1 and 28.6).

Every verb reads and writes QMX's own `memory-row` objects in the home's Library, so the one store
holds the memory, its scopes' refs, its `derived-from` edges and its marks. Hindsight indexes those
rows by default; FTS5 over the same rows stands behind it, and `rebuild` re-indexes either from the
Library alone.

A recall filters by the validity window (`valid_from`, `valid_to`) and by scope and tag, then
weights what is left: `confidence`, a boost for a row learnt in the current regime, and a halving
for a row whose source carries a quarantine mark (Library AD-22). `forget` archives the item and
takes it out of both indexes, so `rebuild` cannot bring it back.

The writer split follows §11.1: a run writes its own `refs/runs/<run_id>`, and the host's engine
principal writes `refs/memory/{wf,home,operator}`. A row's key is its object id, and its item is a
fresh id, so a correction is a new row with a `replaces` edge and never an overwrite.
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, cast

from pydantic import JsonValue
from qmx_engine.ports.memory import Consolidated, Hit, Snapshot
from qmx_library.port import Draft, JsonObject, LibraryRefused
from qmx_library.principal import Principal, state_ref
from qmx_library.store import Store

from qmx_memory.fts import TOP as FTS_TOP
from qmx_memory.fts import FtsIndex
from qmx_memory.rows import (
    SCOPES,
    SNAPSHOT_LINES,
    MemoryRow,
    iso,
    keep,
    memory_ref,
    rendered,
)

ANNOTATIONS = frozenset(
    {
        "aliases",
        "confidence",
        "f",
        "u",
        "keywords",
        "learned_at",
        "occurred_at",
        "regime",
        "source_run_ids",
        "tags",
        "intent_key",
    }
)
"""What a row carries outside its identity: annotated, so it never mints a version (AD-2)."""

IDENTITY = frozenset({"scope", "tag", "intent_key", "when_to_use", "content", "refs"})
COMMIT = "derived-from"
REPLACES = "replaces"
FTS = "fts.db"
TOP = 50
"""Rows an index scores before the engine filters them."""


class Index(Protocol):
    """What an index must answer. `FtsIndex` and `HindsightIndex` both do."""

    def index(self, rows: Iterable[MemoryRow]) -> int: ...
    def forget(self, row_ids: Sequence[str], rows: Iterable[MemoryRow] = ()) -> int: ...
    def rebuild(self, rows: Iterable[MemoryRow]) -> int: ...
    def recall(
        self, query: str, tags: Sequence[str] = (), limit: int = TOP
    ) -> list[tuple[str, float]]: ...
    def close(self) -> None: ...


class RecallEngine:
    """AD-18's verbs over one home's Library, its index and the FTS5 fallback beside them."""

    def __init__(
        self,
        store: Store,
        *,
        index: Index | None = None,
        home: Path | None = None,
        clock: Callable[[], datetime] | None = None,
        extractor: Callable[[str, Sequence[str]], tuple[str, list[str]]] | None = None,
    ) -> None:
        self.store = store
        self.index = index
        self.clock = clock or (lambda: datetime.now(UTC))
        self.extractor = extractor or (
            getattr(index, "reflect", None) if index is not None else None
        )
        self.home = home or store.root / "memory"
        self.fallback = FtsIndex.open(self.home / FTS)
        self.fallback_reason = "" if index is not None else "an index is not installed"

    # -- the port's reads ----------------------------------------------------------------

    def snapshot(
        self,
        scopes: tuple[str, ...],
        budget_tokens: int,
        questions: Sequence[str] = (),
        *,
        now: datetime | None = None,
    ) -> Snapshot:
        """The hot set: the newest live rows of each scope, capped by its line bound and by
        `budget_tokens`, with any standing questions above them. Frozen at run start."""
        at = now or self.clock()
        lines: list[str] = []
        row_ids: list[str] = []
        spent = 0
        for question in questions:
            lines.append(f"? {question}")
        for scope in scopes:
            for taken, row in enumerate(self._rows(scope)):
                if not row.live_at(at) or taken >= SNAPSHOT_LINES.get(scope, 100):
                    break
                spent += row.tokens()
                if spent > budget_tokens:
                    break
                lines.append(rendered(row))
                row_ids.append(row.object_id)
        version = hashlib.sha256("".join(row_ids).encode()).hexdigest()[:16] or "empty"
        return Snapshot("\n".join(lines), version, tuple(row_ids))

    def recall(
        self,
        query: str,
        scopes: tuple[str, ...],
        budget: int,
        tags: tuple[str, ...] = (),
        *,
        now: datetime | None = None,
        regime: Sequence[str] = (),
    ) -> list[Hit]:
        """Live rows matching `query`, best first, cut at `budget` tokens."""
        at = now or self.clock()
        weighted = sorted(
            (
                (row, score * row.weight(at=at, regime=regime))
                for row, score in self._scored(query, tags)
            ),
            key=lambda pair: pair[1],
            reverse=True,
        )
        hits: list[Hit] = []
        spent = 0
        for row, score in weighted:
            if not keep([row], scopes=scopes, tags=tags, at=at, regime=regime):
                continue
            spent += row.tokens()
            if hits and spent > budget:
                break
            hits.append(self._hit(row, score))
        return hits

    def check_built(self, intent_key: str) -> list[str]:
        """Objects already built for this intent key: exact, no model (AD-27). Two sources: an
        object the Library produced on a run that passed, and a `built` row whose own key names
        the build. An archived object is not a hit, so a forgotten row never makes a build look
        done."""
        found = list(self.store.find_by_intent(self.store.engine, intent_key))
        for row in self._rows("home") + self._rows("workflow") + self._rows("operator"):
            if row.tag != "built" or row.intent_key != intent_key:
                continue
            found.extend(_named_objects(row) or [row.object_id])
        return [object_id for object_id in dict.fromkeys(found) if self._active(object_id)]

    def check_dead_end(self, query: str) -> list[Hit]:
        """Dead ends for a key or a question: the exact rows first, then a recall."""
        exact = [
            row
            for object_id in self.check_built(query)
            if self._tagged_dead_end(object_id)
            if (row := self._row(object_id)) is not None
        ]
        found = [self._hit(row, row.confidence) for row in exact]
        if found:
            return found
        return self.recall(query, SCOPES, 2_000, ("dead_end", "do_not_retry"))

    def search_runs(self, query: str, workflow: str | None = None) -> list[Hit]:
        """FTS5 over the run summaries and transcripts the Library holds, no model."""
        return [
            Hit(found.object_id, found.title, found.kind, found.rank, (found.item,))
            for found in self.store.search_runs(self.store.engine, query, workflow)
        ]

    # -- the port's writes ---------------------------------------------------------------

    def note(self, run_id: str, row: JsonObject) -> str:
        """A run-scope row, written by the run itself: the only write a node or agent has."""
        found = self.write("run", run_id, row)
        return found.object_id

    def write(
        self,
        scope: str,
        name: str,
        row: Mapping[str, object],
        *,
        refs: Sequence[str] = (),
        derived_from: Sequence[str] = (),
        replaces: str | None = None,
    ) -> MemoryRow:
        """Land one row on its scope's ref and retain it. `row` may carry annotations; they are
        split off its identity, so a later `feedback` never mints a version."""
        who = self._writer(scope, name)
        ref = memory_ref(scope, name)
        at = self.clock()
        fields = self._identity(scope, row, at=at, refs=refs)
        item = str(uuid.uuid7())
        title = fields["when_to_use"] or fields["content"]
        draft = Draft(
            "memory-row", item=item, title=str(title)[:120], fields=_json(fields), tags=()
        )
        commit = self.store.put(who, draft, on=ref, expected_head=None)
        notes = {key: value for key, value in row.items() if key in ANNOTATIONS}
        notes.setdefault("learned_at", iso(at))
        self.store.annotate(who, commit.object_id, _json(notes))
        for target in derived_from:
            self._relate(commit.object_id, COMMIT, target)
        if replaces is not None:
            self._relate(commit.object_id, REPLACES, replaces)
        written = self._row(commit.object_id)
        if written is None:
            raise LibraryRefused("not_found", f"the row {commit.object_id} was not written")
        self.retain([written])
        return written

    def consolidate(self, run_id: str, into_scope: str, name: str = "") -> Consolidated:
        """A run's rows as one `procedure` row in `into_scope`, derived from each of them."""
        rows = [row for row in self._rows("run", name=run_id) if not row.tainted]
        if not rows:
            return Consolidated()
        content = "\n".join(row.content for row in rows)
        written = self.write(
            into_scope,
            name or run_id,
            {
                "tag": "procedure",
                "when_to_use": f"what run {run_id} learnt",
                "content": content[:8_000],
                "keywords": sorted({word for row in rows for word in row.keywords}),
                "source_run_ids": [run_id],
            },
            derived_from=[row.object_id for row in rows],
        )
        return Consolidated(added=1 if written else 0)

    def feedback(self, row_ids: tuple[str, ...], outcome: str) -> None:
        """One use of each row: `f` counts uses, `u` counts the ones that did not pay off."""
        passed = outcome == "pass"
        for row_id in row_ids:
            row = self._row(row_id)
            if row is None:
                continue
            self.store.annotate(
                self.store.engine,
                row_id,
                {"f": row.f + (1 if passed else 0), "u": row.u + (0 if passed else 1)},
            )

    # -- AD-18's own verbs ---------------------------------------------------------------

    def retain(self, rows: Iterable[MemoryRow], tags: Sequence[str] = ()) -> str:
        """Index rows that are already Library objects. The fallback takes them whether or not
        Hindsight answered, so a stopped engine never leaves a gap in the backup."""
        found = list(rows)
        self.fallback.index(found)
        if self.index is not None:
            try:
                self.index.index(found)
            except Exception as error:  # the fallback is the point of it
                self.fallback_reason = f"{type(error).__name__}: {error}"
        return str(uuid.uuid7())

    def forget(self, row_ids: Sequence[str]) -> int:
        """Archive each row's item and drop it from both indexes. Returns how many were archived.
        The index gets the live rows too, so an adapter that cannot delete one document can
        re-index without the forgotten row instead of leaving it in recall."""
        forgotten = 0
        for row_id in row_ids:
            row = self._row(row_id)
            if row is None:
                continue
            if self._active(row_id):
                self.store.archive(self.store.engine, row.item, "forgotten by its owner")
                forgotten += 1
            self.fallback.forget([row_id])
            if self.index is not None:
                try:
                    self.index.forget([row_id], self._live())
                except Exception as error:  # an index that will not delete is left to the rebuild
                    self.fallback_reason = f"{type(error).__name__}: {error}"
        return forgotten

    def _live(self) -> list[MemoryRow]:
        """Every live row, for an index that has to re-index instead of deleting one."""
        return [row for scope in SCOPES for row in self._rows(scope)]

    def rebuild(self, scope: str = "all") -> str:
        """Wipe the indexes and re-index the live rows of `scope` from the Library alone. An
        archived row is not live, so a forgotten row does not come back."""
        scopes = SCOPES if scope == "all" else (scope,)
        rows = [row for one in scopes for row in self._rows(one)]
        self.fallback.rebuild(rows)
        if self.index is not None:
            self.index.rebuild(rows)
        return str(uuid.uuid7())

    def reflect(self, question: str, tags: Sequence[str] = ()) -> tuple[str, list[str]]:
        """A provider's own answer, with the rows it cited. Hindsight only: the built-in search
        has no model and refuses by name."""
        if self.extractor is None:
            raise LibraryRefused("not_supported", "reflect needs a provider that can answer")
        return self.extractor(question, tags)

    def close(self) -> None:
        self.fallback.close()
        if self.index is not None:
            self.index.close()

    # -- reading the Library ------------------------------------------------------------

    def _rows(self, scope: str, name: str = "") -> list[MemoryRow]:
        """The live rows of one scope, newest first. An archived item is left out."""
        items = self.store.with_field("memory-row", "scope", scope)
        found = [self._row(object_id) for object_id in items]
        live = [row for row in found if row is not None and self._active(row.object_id)]
        if name:
            ref = memory_ref(scope, name)
            named = {object_id for object_id, _ in self.store.placed(name, "memory-row", ref)}
            live = [row for row in live if row.object_id in named] if named else live
        return sorted(live, key=lambda row: row.learned_at, reverse=True)

    def _row(self, object_id: str) -> MemoryRow | None:
        try:
            view = self.store.get(self.store.engine, object_id)
        except LibraryRefused:
            return None
        if view.kind != "memory-row":
            return None
        return MemoryRow.of(view.object_id, view.item, view.fields, view.annotations)

    def _scored(self, query: str, tags: Sequence[str]) -> list[tuple[MemoryRow, float]]:
        """The index's candidates as rows, with its own score. The weight is the read's, applied
        once by `recall`, because a regime is what the read asks for, not what the index knows."""
        wanted = list(tags)
        found: list[tuple[str, float]] = []
        if self.index is not None:
            try:
                found = self.index.recall(query, wanted, TOP)
                self.fallback_reason = ""
            except Exception as error:  # the fallback is the point of it
                self.fallback_reason = f"{type(error).__name__}: {error}"
                found = []
        if not found:
            found = self.fallback.recall(query, wanted, FTS_TOP)
        scored: list[tuple[MemoryRow, float]] = []
        for row_id, score in found:
            row = self._row(row_id)
            if row is None or not self._active(row_id):
                continue
            scored.append((self.tainted(row), score))
        return scored

    def tainted(self, row: MemoryRow) -> MemoryRow:
        """The row with its quarantine flag read from the Library's marks: its own, or a source
        its `refs` name."""
        sources: list[str] = [row.object_id, *_named_objects(row)]
        for source in sources:
            if self._quarantined(source):
                return replace(row, tainted=True)
        return row

    def _quarantined(self, object_id: str) -> bool:
        try:
            found = self.store.marks(self.store.engine, object_id)
        except LibraryRefused:
            return False
        return found.worst == "quarantined"

    def _hit(self, row: MemoryRow, score: float) -> Hit:
        return Hit(
            row.object_id,
            row.content,
            row.tag,
            score,
            row.refs,
            {
                "scope": row.scope,
                "tag": row.tag,
                "when_to_use": row.when_to_use,
                "valid_from": row.valid_from,
                "valid_to": row.valid_to,
                "regime": list(row.regime),
                "learned_at": row.learned_at,
                "tainted": row.tainted,
                "item": row.item,
            },
        )

    def _active(self, object_id: str) -> bool:
        """Whether the object's item is still active: `forget` archives it, never deletes it."""
        try:
            view = self.store.get(self.store.engine, object_id)
        except LibraryRefused:
            return False
        state = self.store.head(view.item, state_ref(view.item))
        return state is None or state[0] != "archived"

    def _tagged_dead_end(self, object_id: str) -> bool:
        row = self._row(object_id)
        return row is not None and row.tag in ("dead_end", "do_not_retry")

    # -- writing helpers -----------------------------------------------------------------

    def _writer(self, scope: str, name: str) -> Principal:
        """§11.1's one writer per ref: the run for its own rows, the host's engine otherwise."""
        if scope == "run":
            return Principal("run", name)
        if scope not in SCOPES:
            raise LibraryRefused("invalid_scope", f"{scope!r} is not a memory scope")
        return self.store.engine

    def _identity(
        self, scope: str, row: Mapping[str, object], *, at: datetime, refs: Sequence[str]
    ) -> dict[str, object]:
        valid_from = str(row.get("valid_from") or iso(at))
        return {
            "scope": scope,
            "tag": str(row.get("tag", "lesson")),
            "intent_key": row.get("intent_key"),
            "when_to_use": str(row.get("when_to_use", "")),
            "content": str(row.get("content", "")),
            "refs": _refs(row.get("refs")) or list(refs),
            "valid_from": valid_from,
            "valid_to": row.get("valid_to"),
        }

    def _relate(self, from_id: str, edge: str, to_id: str) -> None:
        try:
            self.store.relate(self.store.engine, from_id, edge, to_id)
        except LibraryRefused:
            return


def _refs(value: object) -> list[str]:
    """A row's `refs` as written: a list of strings, or nothing."""
    return [str(one) for one in cast("list[object]", value)] if isinstance(value, list) else []


def _named_objects(row: MemoryRow) -> list[str]:
    """The Library objects a row's refs name: `item:<object_id>` and `object:<object_id>`."""
    found: list[str] = []
    for ref in row.refs:
        prefix, _, target = ref.partition(":")
        if prefix in ("item", "object") and target:
            found.append(target)
    return found


def _json(values: Mapping[str, object]) -> JsonObject:
    """Library values as JSON the store accepts: tuples and datetimes become plain values."""
    found: JsonObject = {}
    for key, value in values.items():
        found[key] = _plain(value)
    return found


def _plain(value: object) -> JsonValue:
    if isinstance(value, datetime):
        return iso(value)
    if isinstance(value, tuple | list):
        return [_plain(one) for one in cast("list[object]", value)]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)
