"""`view(object_id, level)`: the one read that serves every kind's card and full page (Library
AD-33, ruling 127, DATA-PLAN DR12).

A card answers what an item is when it stands among many; a page answers what he sees when he
opens it. Both carry the same header, which this module computes at read time and never stores:
the title, the kind and its icon, the version label, the state and, when archived, the reason, who
made it and when, the worst mark with the path that carries it, how it landed, where its bytes are
and their size, and freshness for a kind that has one.

The rest is declared by the kind's own schema. `card.facts` names at most five facts, each a
computed read or a field; `card.thumbnail` names a blob slot, a computed chart or the kind icon;
`card.badge` names what the badge shows; `page.tabs` names field sets, blob slots, relation
neighbourhoods and computed reads, each with a renderer. A fact that cannot be computed answers
`unavailable` with its reason, never a stale number.

`family(object_id)` is AD-32's one family read: the parent, the children, the siblings and the
history of a variant, each edge carrying the `what_changed` annotation its child holds.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from functools import cache
from typing import TYPE_CHECKING, Final, Literal, cast

from pydantic import JsonValue

from qmx_library.kinds import schema_files
from qmx_library.port import RELATIONS, JsonObject, LibraryRefused, ObjectId, ObjectView

if TYPE_CHECKING:
    from qmx_library.principal import Principal
    from qmx_library.store import Store

__all__ = [
    "CardView",
    "Fact",
    "Family",
    "Header",
    "Lineage",
    "PageView",
    "family",
    "header",
    "view",
]

type Level = Literal["card", "page"]
MAX_FACTS: Final = 5
VARIANT: Final = "variant-of"
TRADES_SLOTS: Final = ("trades", "equity", "report")
"""The blob slots an equity read looks for a JSON trade table in, in the order it tries them."""
COMPUTED: Final = frozenset(
    {
        "entry-exit",
        "equity",
        "fills",
        "history",
        "holding_time",
        "members",
        "status",
        "summary",
        "tests",
        "title",
        "trades",
        "used_in",
        "versions",
    }
)


class Unavailable(Exception):
    """A fact or a tab this read cannot compute; its message is the reason shown."""


@cache
def _schemas() -> dict[str, dict[str, object]]:
    """Each kind's raw schema: the card and page declarations the kind registry does not carry."""
    found: dict[str, dict[str, object]] = {}
    for path in schema_files():
        doc = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
        found[str(doc["kind"])] = doc
    return found


def _declared(kind_name: str, key: str) -> dict[str, object]:
    return cast(dict[str, object], _schemas().get(kind_name, {}).get(key) or {})


@dataclass(frozen=True, slots=True)
class Fact:
    """One card fact: its value, or why it could not be computed."""

    name: str
    value: JsonValue = None
    unavailable: str = ""

    def as_json(self) -> JsonObject:
        if self.unavailable:
            return {"name": self.name, "available": False, "reason": self.unavailable}
        return {"name": self.name, "available": True, "value": self.value}


@dataclass(frozen=True, slots=True)
class Header:
    """What every card and page carries, computed here and never stored."""

    title: str
    kind: str
    icon: str
    version: str
    state: Literal["active", "archived"]
    reason: str
    author: str
    at: str
    mark: str
    mark_path: tuple[ObjectId, ...]
    landed_ref: str
    landed_rule: str
    store: str
    size: int
    freshness: JsonObject | None = field(default=None)

    def as_json(self) -> JsonObject:
        body: JsonObject = {
            "title": self.title,
            "kind": self.kind,
            "icon": self.icon,
            "version": self.version,
            "state": self.state,
            "author": self.author,
            "at": self.at,
            "mark": None if self.mark == "" else self.mark,
            "mark_path": list(self.mark_path),
            "landed": {"ref": self.landed_ref, "rule": self.landed_rule},
            "bytes": {"store": self.store, "size": self.size},
        }
        if self.state == "archived":
            body["archived_because"] = self.reason or "no reason was recorded"
        if self.freshness is not None:
            body["freshness"] = self.freshness
        return body


@dataclass(frozen=True, slots=True)
class CardView:
    header: Header
    facts: tuple[Fact, ...]
    thumbnail: JsonObject
    badge: str

    def as_json(self) -> JsonObject:
        return {
            "level": "card",
            "header": self.header.as_json(),
            "facts": [fact.as_json() for fact in self.facts],
            "thumbnail": self.thumbnail,
            "badge": self.badge,
        }


@dataclass(frozen=True, slots=True)
class PageView:
    header: Header
    tabs: tuple[JsonObject, ...]

    def as_json(self) -> JsonObject:
        return {"level": "page", "header": self.header.as_json(), "tabs": list(self.tabs)}


@dataclass(frozen=True, slots=True)
class Lineage:
    """One edge of a family, with the `what_changed` annotation its child carries (AD-32)."""

    edge: str
    from_id: ObjectId
    to_id: ObjectId
    what_changed: str

    def as_json(self) -> JsonObject:
        return {
            "edge": self.edge,
            "from": self.from_id,
            "to": self.to_id,
            "what_changed": self.what_changed,
        }


@dataclass(frozen=True, slots=True)
class Family:
    root: ObjectId
    parent: ObjectId | None
    children: tuple[ObjectId, ...]
    siblings: tuple[ObjectId, ...]
    history: tuple[tuple[str, str, str], ...]
    edges: tuple[Lineage, ...]

    def as_json(self) -> JsonObject:
        return {
            "root": self.root,
            "parent": self.parent,
            "children": list(self.children),
            "siblings": list(self.siblings),
            "history": [list(row) for row in self.history],
            "edges": [edge.as_json() for edge in self.edges],
        }


@dataclass(frozen=True, slots=True)
class Neighbour:
    item: str
    object_id: ObjectId
    edge: str
    direction: Literal["in", "out"]


def _archived(store: Store, item: str) -> tuple[bool, str]:
    if store.catalog.state(item) != "archived":
        return False, ""
    row = store.catalog.db.execute("SELECT reason FROM items WHERE item = ?", (item,)).fetchone()
    return True, "" if row is None or row[0] is None else str(row[0])


def _version(store: Store, found: ObjectView, ref: str) -> str:
    semver = found.annotations.get("semver")
    if isinstance(semver, str) and semver:
        return semver
    placed = [object_id for object_id, _ in store.placed(found.item, found.kind, ref)]
    return f"v{placed.index(found.object_id) + 1 if found.object_id in placed else 1}"


def _landed_rule(klass: str) -> str:
    return {"record": "auto", "definition": "drafts", "governed": "governed"}.get(klass, klass)


def _freshness(found: ObjectView) -> JsonObject | None:
    """A kind has freshness when its fields name the month it reaches; nothing else is a clock."""
    for key in ("coverage", "window"):
        block = found.fields.get(key)
        if isinstance(block, dict):
            last = cast(dict[str, JsonValue], block).get("last")
            if isinstance(last, str) and last:
                return {"through": last}
    return None


def header(store: Store, who: Principal, object_id: ObjectId) -> Header:
    """The header every card and page carries, computed at read."""
    found = store.get(who, object_id)
    ref, principal, at = store.placement(object_id) or ("", "", "")
    archived, reason = _archived(store, found.item)
    marks = store.marks(who, object_id)
    declared = _declared(found.kind, "card")
    thumbnail = str(declared.get("thumbnail", "icon"))
    icon = thumbnail.removeprefix("blobs.") if thumbnail.startswith("blobs.") else "icon"
    if icon != "icon" and icon not in found.blobs:
        icon = "icon"
    return Header(
        title=found.title or found.item,
        kind=found.kind,
        icon=icon,
        version=_version(store, found, ref),
        state="archived" if archived else "active",
        reason=reason,
        author=principal,
        at=at,
        mark=marks.label,
        mark_path=marks.path,
        landed_ref=ref,
        landed_rule=_landed_rule(found.klass),
        store=store.name,
        size=sum(blob.size for blob in found.blobs.values()),
        freshness=_freshness(found),
    )


def _neighbours(
    store: Store,
    who: Principal,
    found: ObjectView,
    edge: str,
    direction: Literal["in", "out"],
) -> list[Neighbour]:
    """The objects joined to `found` by `edge` (every relation when it is `*`), both or either
    way. At-birth relations are read from the object and after-birth edges from the edge log."""
    names = RELATIONS if edge == "*" else {edge}
    rows: list[tuple[str, str, str]] = [
        (name, to, "out") for name, to in found.relations if name in names
    ]
    rows += [(step.edge, step.object_id, "out") for step in _edges(store, found.object_id, False)]
    rows += [(step.edge, step.object_id, "in") for step in _edges(store, found.object_id, True)]
    wanted = [row for row in rows if row[0] in names and row[2] == direction]
    found_steps: list[Neighbour] = []
    seen: set[ObjectId] = set()
    for name, other, way in wanted:
        if other in seen:
            continue
        seen.add(other)
        try:
            view_of_other = store.get(who, other)
        except LibraryRefused:
            continue
        found_steps.append(
            Neighbour(view_of_other.item, other, name, cast("Literal['in', 'out']", way))
        )
    return found_steps


def _edges(store: Store, object_id: ObjectId, reverse: bool) -> list[Neighbour]:
    steps: list[Neighbour] = []
    for from_id, name, to_id, _writer, _at in store.edges_of(object_id, reverse=reverse):
        other = from_id if reverse else to_id
        steps.append(Neighbour("", other, name, "in" if reverse else "out"))
    return steps


def _table(store: Store, found: ObjectView, slots: Sequence[str]) -> JsonValue:
    """The first JSON body among `slots`, or the reason none could be read."""
    for slot in slots:
        if slot not in found.blobs:
            continue
        try:
            return cast(JsonValue, json.loads(store.read_blob(found.blobs[slot].blob_id)))
        except LibraryRefused as why:
            raise Unavailable(f"the {slot} blob could not be read: {why}") from why
        except (OSError, ValueError) as why:
            raise Unavailable(f"the {slot} blob is corrupt: {why}") from why
    raise Unavailable(f"the {found.kind} holds no slot among {', '.join(slots)}")


def _rows(table: JsonValue) -> list[dict[str, JsonValue]]:
    if isinstance(table, list):
        return [cast(dict[str, JsonValue], row) for row in table if isinstance(row, dict)]
    if isinstance(table, dict):
        rows = cast(dict[str, JsonValue], table).get("trades")
        if isinstance(rows, list):
            return [cast(dict[str, JsonValue], row) for row in rows if isinstance(row, dict)]
    raise Unavailable("the blob holds neither a list of trades nor a `trades` list")


def _equity(store: Store, found: ObjectView) -> JsonValue:
    """The running net result of a trades table, in the money each row carries."""
    running: float = 0.0
    curve: list[float] = []
    for row in _rows(_table(store, found, TRADES_SLOTS)):
        result, digits = row.get("net_result"), row.get("money_digits")
        if not isinstance(result, int) or isinstance(result, bool):
            raise Unavailable("a trade row carries no integer net_result")
        step = (
            result / 10**digits
            if isinstance(digits, int) and not isinstance(digits, bool)
            else result
        )
        running += step
        curve.append(round(running, 6))
    return cast(JsonValue, curve)


def _holding(held: int) -> str:
    minutes, seconds = divmod(held // 1_000_000_000, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m"
    return f"{seconds}s"


def _computed(store: Store, who: Principal, found: ObjectView, name: str) -> JsonValue:
    match name:
        case "equity":
            return _equity(store, found)
        case "trades":
            return cast(JsonValue, _rows(_table(store, found, TRADES_SLOTS)))
        case "entry-exit":
            entry, exit_ = found.fields.get("entry_price"), found.fields.get("exit_price")
            if not isinstance(entry, int) or not isinstance(exit_, int):
                raise Unavailable("the trade records no entry and exit price")
            return {
                "entry_price": entry,
                "exit_price": exit_,
                "price_digits": found.fields.get("price_digits", 0),
                "entry_ns": found.fields.get("entry_ns"),
                "exit_ns": found.fields.get("exit_ns"),
                "side": found.fields.get("side"),
            }
        case "history":
            return [list(row) for row in store.history(found.item)]
        case "fills":
            fills = found.fields.get("fills")
            if not isinstance(fills, list):
                raise Unavailable("the trade records no fills")
            return fills
        case "members":
            items = found.fields.get("items")
            if not isinstance(items, list):
                raise Unavailable("the collection lists no members")
            return len(items)
        case "versions":
            return [
                {"object_id": object_id, "ref": ref}
                for object_id, ref in store.placed(found.item, found.kind, None)
            ]
        case "status":
            return _hypothesis(store, who, found)
        case "tests":
            return len({step.item for step in _neighbours(store, who, found, "tests", "in")})
        case "used_in":
            return len({step.item for step in _neighbours(store, who, found, "*", "in")})
        case "holding_time":
            held = found.fields.get("holding_ns")
            if not isinstance(held, int) or isinstance(held, bool):
                raise Unavailable("the trade records no holding time")
            return _holding(held)
        case "title":
            return found.title
        case "summary":
            return found.summary
        case _:
            raise Unavailable(f"no computation is named {name!r}")


def _hypothesis(store: Store, who: Principal, found: ObjectView) -> JsonValue:
    from qmx_library.status import status  # noqa: PLC0415 (only a hypothesis read needs it)

    if found.kind != "hypothesis":
        raise Unavailable(f"a {found.kind} has no hypothesis status")
    computed = status(store, who, found.item)
    return {
        "status": computed.status,
        "by_regime": dict(computed.by_regime),
        "counted": list(computed.counted),
        "ignored": list(computed.ignored),
    }


def _fact(store: Store, who: Principal, found: ObjectView, name: str) -> Fact:
    try:
        return Fact(name, _computed(store, who, found, name))
    except Unavailable as why:
        reason = str(why)
    value = found.fields.get(name)
    if value is not None:
        return Fact(name, value)
    if name not in COMPUTED:
        reason = f"the {found.kind} records no {name}"
    return Fact(name, unavailable=reason)


def _thumbnail(found: ObjectView, declared: str) -> JsonObject:
    if declared.startswith("blobs."):
        slot = declared.removeprefix("blobs.")
        if slot in found.blobs:
            return {"kind": "blob", "slot": slot}
        return {"kind": "icon", "icon": found.kind}
    if declared.startswith("computed:"):
        return {"kind": "computed", "name": declared.removeprefix("computed:")}
    return {"kind": "icon", "icon": found.kind}


def _content(store: Store, who: Principal, found: ObjectView, source: str) -> JsonValue:
    if source == "fields":
        return cast(JsonValue, dict(found.fields))
    if source == "annotations":
        return cast(JsonValue, dict(found.annotations))
    if source.startswith("fields."):
        key = source.removeprefix("fields.")
        value = found.fields.get(key)
        if value is None:
            raise Unavailable(f"the {found.kind} records no {key}")
        return value
    if source.startswith("blobs."):
        return _slot(found, source.removeprefix("blobs."))
    if source.startswith("walk:"):
        _, edge, direction = source.split(":")
        return [
            {"item": step.item, "object_id": step.object_id, "edge": step.edge}
            for step in _neighbours(store, who, found, edge, "in" if direction == "in" else "out")
        ]
    if source.startswith("computed:"):
        return _computed(store, who, found, source.removeprefix("computed:"))
    raise Unavailable(f"no tab source is named {source!r}")


def _slot(found: ObjectView, slot: str) -> JsonValue:
    if "*" in slot:
        held: list[JsonValue] = [
            {
                "slot": name,
                "blob_id": blob.blob_id,
                "size": blob.size,
                "media_type": blob.media_type,
            }
            for name, blob in sorted(found.blobs.items())
            if fnmatchcase(name, slot)
        ]
        if not held:
            raise Unavailable(f"no blob slot matches {slot}")
        return held
    blob = found.blobs.get(slot)
    if blob is None:
        raise Unavailable(f"the {found.kind} has no blob {slot}")
    return {
        "slot": slot,
        "blob_id": blob.blob_id,
        "size": blob.size,
        "media_type": blob.media_type,
    }


def _tab(store: Store, who: Principal, found: ObjectView, entry: dict[str, object]) -> JsonObject:
    source = str(entry.get("source", "fields"))
    tab: JsonObject = {
        "tab": str(entry.get("tab", "")),
        "renderer": str(entry.get("renderer", "json")),
        "source": source,
    }
    try:
        tab["content"] = _content(store, who, found, source)
    except Unavailable as why:
        tab["available"] = False
        tab["reason"] = str(why)
    else:
        tab["available"] = True
    return tab


def view(
    store: Store, who: Principal, object_id: ObjectId, level: Level = "card"
) -> CardView | PageView:
    """The card or the full page of one object, with the header computed at read."""
    found = store.get(who, object_id)
    head = header(store, who, object_id)
    if level == "page":
        page = _declared(found.kind, "page")
        return PageView(
            head,
            tuple(
                _tab(store, who, found, entry)
                for entry in cast(list[dict[str, object]], page.get("tabs") or [])
            ),
        )
    card = _declared(found.kind, "card")
    names = [str(name) for name in cast(list[str], card.get("facts") or ["title", "summary"])]
    if len(names) > MAX_FACTS:
        raise LibraryRefused(
            "schema_invalid", f"{found.kind} declares {len(names)} card facts; a card shows five"
        )
    return CardView(
        head,
        tuple(_fact(store, who, found, name) for name in names),
        _thumbnail(found, str(card.get("thumbnail", "icon"))),
        str(card.get("badge", "state")),
    )


def _what_changed(store: Store, who: Principal, object_id: ObjectId) -> str:
    """The change a variant records against its parent: an annotation, a field, or its metadata."""
    found = store.get(who, object_id)
    for candidate in (
        found.annotations.get("what_changed"),
        found.fields.get("what_changed"),
    ):
        if isinstance(candidate, str):
            return candidate
    metadata = found.fields.get("metadata")
    if isinstance(metadata, dict):
        held = cast(dict[str, JsonValue], metadata).get("what_changed")
        if isinstance(held, str):
            return held
    return ""


def family(store: Store, who: Principal, object_id: ObjectId) -> Family:
    """AD-32's one family read: parent, children, siblings and history, both directions."""
    found = store.get(who, object_id)
    parents = _neighbours(store, who, found, VARIANT, "out")
    children = _neighbours(store, who, found, VARIANT, "in")
    parent = parents[0].object_id if parents else None
    siblings: tuple[ObjectId, ...] = ()
    if parent is not None:
        siblings = tuple(
            step.object_id
            for step in _neighbours(store, who, store.get(who, parent), VARIANT, "in")
            if step.object_id != object_id
        )
    edges = tuple(
        Lineage(VARIANT, step.object_id, object_id, _what_changed(store, who, step.object_id))
        for step in children
    ) + tuple(
        Lineage(VARIANT, object_id, step.object_id, _what_changed(store, who, object_id))
        for step in parents
    )
    return Family(
        object_id,
        parent,
        tuple(step.object_id for step in children),
        siblings,
        tuple(store.history(found.item)),
        edges,
    )
