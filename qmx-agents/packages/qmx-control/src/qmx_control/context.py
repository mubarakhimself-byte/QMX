"""Context references (engine AD-63): one `@` grammar, one resolver per Library kind.

A reference is `@<kind>:<target>` from one closed list, usable in the composer, by the copilot
through `context_add`, in a workflow's `inputs` and in a `delegate` task, so a helper gets a
handle instead of pasted text. Resolving one pins a Library object and returns the list entry the
chat record holds (H49):

    {ref, item_id, pin: version | follow, version_id?, artifact_id?, status, note}

`version` pins the object the reference resolved to; `follow` re-reads `main` (or an app's latest
landed output) every time. `status` is `ready | pending | archived | not_cached`, and `pending`
is resolved at read time from the Library, so no writer has to flip it (review 48 L6). A pinned
item whose `main` has moved carries the note "newer version exists" (Library AD-22).

The reads are this module's narrow port, not `qmx_library`: the host that owns the store supplies
an adapter, so control stays free of the store's package and the tests use a fixture. `file`,
`folder`, `url` and `youtube` arrive with REF2 and `memory` with MEM; each is refused here by name
with that reason rather than silently unresolved.

The excerpt a model sees is capped by `H/surface.py`'s budget (25 % soft and 50 % hard of the
window, and at most 200 folder entries: Claude's defaults, Settings); this module only cuts to the
number it is given.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Final, Literal, Protocol, cast

type Pin = Literal["version", "follow"]
type Status = Literal["ready", "pending", "archived", "not_cached"]

KINDS: Final[tuple[str, ...]] = (
    "pod",
    "unit",
    "bot",
    "run",
    "app",
    "library",
    "session",
    "memory",
    "file",
    "folder",
    "url",
    "youtube",
)
"""AD-63's closed list."""

LATER: Final[Mapping[str, str]] = MappingProxyType(
    {
        "file": "the @file kind arrives with REF2",
        "folder": "the @folder kind arrives with REF2",
        "url": "the @url kind arrives with REF2",
        "youtube": "the @youtube kind arrives with REF2",
        "memory": "the @memory kind arrives with MEM",
    }
)
"""The kinds another PR brings, with the reason a reference to one is refused today."""

NEWER: Final = "newer version exists"
"""What a pinned item whose `main` has moved reads (Library AD-22, AD-63)."""

PINNED_KINDS: Final[frozenset[str]] = frozenset({"pod", "unit", "bot", "session"})
"""Kinds that name one Library item by id. `library` names one by search; `run` and `app` read a
landed output, which their own resolvers do."""

TEXT_SLOTS: Final[tuple[str, ...]] = ("content", "body.md")
"""The blob slots an excerpt may be read from, asked for every kind: a store answers the slots the
object has. A session's transcript is never asked for, since it is the CLI's, not the model's."""


class ContextRefused(ValueError):
    """A reference cannot be resolved. `str` is the tool error document, so the harness's tool
    wrapper returns its code and message rather than a bare exception type."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(json.dumps({"error": {"code": code, "message": message}}))


@dataclass(frozen=True)
class AttachedRef:
    """One entry of the chat record's `attached` list (H49, AD-63)."""

    ref: str
    item_id: str
    pin: Pin = "version"
    version_id: str | None = None
    artifact_id: str | None = None
    status: Status = "ready"
    note: str = ""

    @property
    def object_id(self) -> str:
        """The object this entry points at: its landed output, else its pinned version."""
        return self.artifact_id or self.version_id or self.item_id

    def document(self) -> dict[str, object]:
        return {
            "ref": self.ref,
            "item_id": self.item_id,
            "pin": self.pin,
            "version_id": self.version_id,
            "artifact_id": self.artifact_id,
            "status": self.status,
            "note": self.note,
        }

    @classmethod
    def from_document(cls, page: object) -> AttachedRef:
        """A record written before a field existed reads its default."""
        if not isinstance(page, Mapping):
            raise ContextRefused("invalid_arguments", f"{page!r} is not a reference entry")
        table = cast("Mapping[str, object]", page)
        values = {key: value for key, value in table.items() if value is not None}
        return cls(
            ref=str(values["ref"]),
            item_id=str(values["item_id"]),
            pin="follow" if values.get("pin") == "follow" else "version",
            version_id=_text(values.get("version_id")),
            artifact_id=_text(values.get("artifact_id")),
            status=_status(values.get("status")),
            note=str(values.get("note", "")),
        )

    def described(self) -> str:
        """One line for `context_list` and for a screen's chips."""
        parts = [self.ref, self.status]
        if self.version_id:
            parts.append(f"pinned {self.version_id.rsplit(':', 1)[-1][:6]}")
        if self.pin == "follow":
            parts.append("follow")
        if self.note:
            parts.append(self.note)
        return " ".join(parts)


def _text(value: object) -> str | None:
    return None if value is None else str(value)


def _status(value: object) -> Status:
    return "ready" if value not in ("pending", "archived", "not_cached") else value  # type: ignore[return-value]


def parse(ref: str) -> tuple[str, str]:
    """`@<kind>:<target>` as `(kind, target)`. Refuses an unknown kind, a kind that another PR
    brings, and a target that is empty."""
    text = ref.strip()
    if not text.startswith("@") or ":" not in text:
        raise ContextRefused(
            "invalid_arguments",
            f"{ref!r} is not a reference; a reference reads @<kind>:<target> and the kinds are "
            f"{', '.join(KINDS)}",
        )
    kind, target = text[1:].split(":", 1)
    if kind not in KINDS:
        raise ContextRefused(
            "invalid_arguments",
            f"@{kind} is not a reference kind; the kinds are {', '.join(KINDS)}",
        )
    if (later := LATER.get(kind)) is not None:
        raise ContextRefused("not_yet", later)
    target = target.strip()
    if not target:
        raise ContextRefused("invalid_arguments", f"{ref!r} names no {kind} after the colon")
    return kind, target


@dataclass(frozen=True)
class LibraryObject:
    """What a resolver reads of one Library object."""

    object_id: str
    item: str
    kind: str
    title: str = ""
    summary: str = ""
    fields: Mapping[str, object] = MappingProxyType({})
    annotations: Mapping[str, object] = MappingProxyType({})
    relations: tuple[tuple[str, str], ...] = ()
    data: Mapping[str, bytes] = MappingProxyType({})


@dataclass(frozen=True)
class LibraryHit:
    object_id: str
    item: str
    kind: str
    title: str = ""


class LibraryReads(Protocol):
    """The Library reads a resolver needs. The host's adapter answers them from the store; no
    policy lives here."""

    def head(self, item: str, ref: str = "main") -> str | None: ...
    def state(self, item: str) -> str | None: ...

    """`active`, `archived`, or None for an item the store never held."""

    def get(self, object_id: str, slots: Sequence[str] = ()) -> LibraryObject: ...
    def search(
        self, text: str, *, kind: str | None = None, limit: int = 20
    ) -> list[LibraryHit]: ...
    def produced(self, producer: str) -> list[str]: ...

    """The artifacts a run object produced, oldest first."""

    def outputs(self, producer: str, name: str) -> list[str]: ...

    """The artifacts an app item landed under its `provides` name, oldest first."""


@dataclass(frozen=True)
class Budget:
    """The excerpt budget `H/surface.py` measures: a soft share and a hard share of the model's
    window, in characters. Context hygiene, never a usage cap."""

    soft_chars: int
    hard_chars: int
    folder_entries: int = 200

    def __post_init__(self) -> None:
        if self.hard_chars < self.soft_chars:
            raise ContextRefused("invalid_arguments", "an excerpt's hard limit is under its soft")


def cut(text: str, limit: int) -> str:
    """`text` when it fits, else its head and a pointer saying what was left out."""
    if len(text) <= limit:
        return text
    pointer = f"[cut at {limit:,} of {len(text):,} characters; context_read has the rest.]"
    if len(pointer) >= limit:
        return pointer
    return text[: limit - len(pointer) - 2].rstrip() + "\n\n" + pointer


class Resolvers:
    """One resolver per kind over `reads`. `add` is `context_add`'s work, `refresh` re-reads a
    `follow` entry, and `read` returns the capped excerpt plus the handle."""

    def __init__(self, reads: LibraryReads, budget: Budget) -> None:
        self.reads = reads
        self.budget = budget

    def add(self, ref: str, pin: Pin = "version") -> AttachedRef:
        """Resolve `ref` into a pinned entry. `follow` leaves the version open."""
        kind, target = parse(ref)
        found = self._resolve(kind, target)
        if pin == "follow":
            found = replace(found, pin="follow", version_id=None)
        return found

    def refresh(self, attached: AttachedRef) -> AttachedRef:
        """Re-resolve an entry against the Library now. A pinned entry keeps its version and
        gains the "newer version exists" note when `main` moved, and picks up the output a
        `pending` one was waiting for; a following one moves."""
        kind, target = parse(attached.ref)
        if attached.pin == "follow":
            return replace(self._resolve(kind, target), pin="follow", version_id=None)
        current = self._resolve(kind, target)
        moved = current.version_id is not None and current.version_id != attached.version_id
        return replace(
            attached,
            artifact_id=current.artifact_id or attached.artifact_id,
            status=current.status,
            note=NEWER if moved else "",
        )

    def read(self, attached: AttachedRef, span: str | None = None) -> str:
        """The handle and an excerpt, capped at the hard budget. `span` is `a-b` in characters."""
        found = self.reads.get(self._object_id(attached), TEXT_SLOTS)
        text = self._text(found)
        if span is not None:
            text = _span(text, span)
        body = cut(text, self.budget.hard_chars)
        return f"{attached.described()}\n{found.title}\n\n{body}".strip()

    def excerpt(self, attached: AttachedRef) -> str:
        """What `context_add` returns: the handle and a soft-capped excerpt."""
        found = self.reads.get(self._object_id(attached), TEXT_SLOTS)
        head = cut(self._text(found), self.budget.soft_chars)
        return f"{attached.described()}\n{found.title}\n\n{head}"

    def _object_id(self, attached: AttachedRef) -> str:
        """A following entry reads `main` now, not the object the chat was born on."""
        if attached.pin == "follow":
            kind, target = parse(attached.ref)
            return self._resolve(kind, target).object_id
        return attached.object_id

    # -- one resolver per kind ----------------------------------------------------------

    def _resolve(self, kind: str, target: str) -> AttachedRef:
        if kind in PINNED_KINDS or kind == "library":
            return self._pinned(kind, target)
        if kind == "run":
            return self._run(target)
        if kind == "app":
            return self._app(target)
        raise ContextRefused("invalid_arguments", f"@{kind} has no resolver")

    def _pinned(self, kind: str, target: str) -> AttachedRef:
        """`@pod`, `@unit`, `@bot` and `@session` name one Library item by id; `@library` names
        one by search."""
        if kind == "library":
            hits = self.reads.search(target, limit=1)
            if not hits:
                raise ContextRefused("not_found", f"no Library item matches {target!r}")
            return self._entry(f"@library:{target}", hits[0].item, hits[0].object_id, kind=None)
        return self._entry(f"@{kind}:{target}", target, None, kind=kind)

    def _entry(
        self, ref: str, item: str, object_id: str | None, *, kind: str | None
    ) -> AttachedRef:
        head = self.reads.head(item) if object_id is None else object_id
        if head is None:
            raise ContextRefused("not_found", f"no Library item {item!r} on main")
        found = self.reads.get(head)
        if kind is not None and found.kind != kind:
            raise ContextRefused(
                "invalid_arguments", f"{item!r} is a {found.kind}, so it reads @{found.kind}:{item}"
            )
        newest = self.reads.head(item)
        moved = newest is not None and newest != head
        return AttachedRef(
            ref=ref,
            item_id=item,
            version_id=head,
            status=self._status(item),
            note=NEWER if moved else "",
        )

    def _status(self, item: str) -> Status:
        """An archived item stays readable and says so (AD-63, AD-6)."""
        return "archived" if self.reads.state(item) == "archived" else "ready"

    def _run(self, target: str) -> AttachedRef:
        """`@run:<id>` pins the run; `@run:<id>/<output>` pins the artifact it landed, and reads
        `pending` until that output lands."""
        run_id, _, output = target.partition("/")
        head = self.reads.head(run_id)
        if head is None:
            raise ContextRefused("not_found", f"no run {run_id!r} on main")
        if not output:
            return self._entry(f"@run:{run_id}", run_id, None, kind=None)
        for artifact in self.reads.produced(head):
            found = self.reads.get(artifact)
            if _names_output(found, output):
                return AttachedRef(
                    ref=f"@run:{run_id}/{output}",
                    item_id=run_id,
                    version_id=head,
                    artifact_id=artifact,
                    status=self._status(run_id),
                )
        return AttachedRef(
            ref=f"@run:{run_id}/{output}",
            item_id=run_id,
            version_id=head,
            status="pending",
            note=f"the run has not landed {output} yet",
        )

    def _app(self, target: str) -> AttachedRef:
        """`@app:<id>/<provides-name>` pins the app's latest landed output under that name, and
        `@app:<id>` the app item itself."""
        app_id, _, name = target.partition("/")
        head = self.reads.head(app_id)
        if head is None:
            raise ContextRefused("not_found", f"no mini app {app_id!r} on main")
        if not name:
            return self._entry(f"@app:{app_id}", app_id, None, kind=None)
        landed = self.reads.outputs(app_id, name)
        if not landed:
            return AttachedRef(
                ref=f"@app:{app_id}/{name}",
                item_id=app_id,
                version_id=head,
                status="pending",
                note=f"{app_id} has not landed {name} yet",
            )
        return AttachedRef(
            ref=f"@app:{app_id}/{name}",
            item_id=app_id,
            version_id=head,
            artifact_id=landed[-1],
            status=self._status(app_id),
        )

    # -- reading ------------------------------------------------------------------------

    def _text(self, found: LibraryObject) -> str:
        """The object's own text: its blob when it has one, else its fields."""
        for slot in TEXT_SLOTS:
            data = found.data.get(slot)
            if data is not None:
                return data.decode("utf-8", "replace")
        body = json.dumps(dict(found.fields), indent=2, sort_keys=True, default=str)
        head = f"{found.summary}\n\n" if found.summary else ""
        return head + body


def _names_output(found: LibraryObject, name: str) -> bool:
    """Whether an artifact was landed under `name`: its `type`, or the `output` of the app
    reference shape `qmx_apps.artifacts.ArtifactRef` (metadata carries it)."""
    if found.fields.get("type") == name:
        return True
    metadata = found.fields.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    return cast("Mapping[str, object]", metadata).get("output") == name


def _span(text: str, span: str) -> str:
    """`a-b` of a text, 0-based characters. A malformed span is refused by name."""
    start_text, _, end_text = span.partition("-")
    try:
        start, end = int(start_text), int(end_text)
    except ValueError:
        raise ContextRefused(
            "invalid_arguments", f"{span!r} is not a range; a range reads a-b"
        ) from None
    if start < 0 or end <= start:
        raise ContextRefused("invalid_arguments", f"{span!r} is not a range; a range reads a-b")
    return text[start:end]


@dataclass(frozen=True)
class Listing:
    """`context_list`'s answer: the entries, each refreshed at read time, and how many resolved."""

    entries: tuple[AttachedRef, ...] = ()
    ready: int = 0
    pending: int = 0

    def lines(self) -> list[str]:
        return [entry.described() for entry in self.entries]


def listing(entries: Sequence[AttachedRef], resolvers: Resolvers) -> Listing:
    """Each entry as the Library reads it now: `pending` clears itself when the output lands, and
    a pinned item whose main moved says so (Library AD-22)."""
    refreshed: list[AttachedRef] = []
    for entry in entries:
        try:
            refreshed.append(resolvers.refresh(entry))
        except ContextRefused as refused:
            refreshed.append(replace(entry, status="not_cached", note=refused.message))
    ready = sum(1 for entry in refreshed if entry.status == "ready")
    waiting = sum(1 for entry in refreshed if entry.status == "pending")
    return Listing(tuple(refreshed), ready, waiting)
