"""Event triggers read the Library ref log by cursor (AD-64, AD-10).

A row that lands in the Library is a Library ref move, and a landing an app made under one of its
`provides` names is an `artifact` object whose `fields.type` is that name and whose
`fields.metadata.ref.producer_app` is the app that produced it. An `event` trigger's filter names
any of `kind`, `output` and `producer`, and a row matches when every named one matches; a filter
that names none of them is refused because it would fire on the whole Library. `kind` is the
object kind, `output` its provides name and `producer` the app that landed it, falling back to the
writer's principal for objects that name no app (a note, a run summary, an artifact an operator
put).

Each trigger keeps a cursor in the ledger's `meta` row `event_cursor:<trigger_id>`, holding the
last ref-log `seq` it has read. One tick reads the ref log once from the oldest cursor it needs,
resolves every row it has not seen to a `Landing`, and writes the fires and the new cursors in one
transaction, so a crash can leave neither a row read and fired and then read again, nor a row
skipped. A trigger first seen on a tick starts its cursor at the log's tail: it fires for landings
after it exists, never for the Library's history. A re-delivery of one object is the same object
id, so the fire it would make is refused by the fires table's `(trigger_id, delivery_id)` index,
where the delivery id is `event:<object_id>`: dedupe is per trigger and object, and unbounded.

`coalesce` is `each` (the default) or `latest`. With `latest`, a landing supersedes every fire of
that trigger still queued for a claim, so one fire runs on the newest object; the superseded fires
end `skipped` with the object that replaced them. The tick reads the log before it claims, so a
burst inside one tick collapses without a queue at all.

While `autonomy.paused` is set the tick drains nothing and keeps its cursors: landings wait in the
log. The first tick after the flag clears fires at most once per trigger, on the newest match,
whatever its `coalesce`, which is AD-10's pause rule for a clocked trigger read for a landing: a
pause loses no work and hands back no burst.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Final, Literal, Protocol, cast

from qmx_engine.ledger.store import Ledger, Operation, Reader, Transaction
from qmx_engine.ports.library import LibraryEvent, LibraryRefused, Stored
from qmx_engine.service.context import Refused
from qmx_engine.triggers.cron import stamp
from qmx_engine.triggers.rows import (
    Event,
    HomeEngine,
    JsonObject,
    Trigger,
    new_fire_id,
    triggers,
)

type Coalesce = Literal["each", "latest"]


class RefLog(Protocol):
    """The two reads an event drain makes of the Library: its ref-log tail and one object."""

    def events(self, after: int = 0) -> list[LibraryEvent]: ...

    def get(self, object_id: str) -> Stored: ...


CURSOR: Final = "event_cursor:"
"""The `meta` key prefix of a trigger's cursor: the last ref-log `seq` it has read."""
PAUSED: Final = "event_paused"
"""The `meta` key that says the last drain ran while `autonomy.paused` was set."""
NAMES: Final = frozenset({"kind", "output", "producer"})
"""The facts a filter matches on, at least one of which it must name."""
KEYS: Final = NAMES | {"coalesce"}
DELIVERY: Final = "event:"
"""A fire's delivery id for a landed object: the same object never fires a trigger twice."""


@dataclass(frozen=True, slots=True)
class Filter:
    """A trigger's `event` filter, parsed and checked at the boundary."""

    kind: str | None = None
    output: str | None = None
    producer: str | None = None
    coalesce: Coalesce = "each"


@dataclass(frozen=True, slots=True)
class Landing:
    """One ref-log row resolved to the facts a filter matches on."""

    seq: int
    object_id: str
    kind: str
    output: str | None
    producer: str
    """The app that produced an artifact, else the principal that wrote the object."""

    def matches(self, found: Filter) -> bool:
        return (
            (found.kind is None or found.kind == self.kind)
            and (found.output is None or found.output == self.output)
            and (found.producer is None or found.producer == self.producer)
        )


@dataclass(frozen=True, slots=True)
class Plan:
    """What one event trigger takes from this drain: its fires and its next cursor."""

    trigger: Trigger
    landings: tuple[Landing, ...]
    cursor: int
    coalesce: Coalesce


@dataclass(frozen=True, slots=True)
class Drain:
    fired: tuple[str, ...]
    """The fires this drain queued, oldest landing first."""
    superseded: int
    """Fires `coalesce: latest` dropped because a newer object replaced them."""
    cursor: int
    """The ref-log `seq` this drain read to; every trigger's cursor is now at it or past it."""


def filter_of(trigger: Trigger) -> Filter:
    """The trigger's filter, refused when it is not one this matcher can honour."""
    if not isinstance(trigger.spec, Event):
        raise Refused("not_event", f"{trigger.id} is a {trigger.kind} trigger")
    return parse(trigger.spec.filter)


def parse(found: JsonObject) -> Filter:
    unknown = sorted(set(found) - KEYS)
    if unknown:
        raise Refused("event_filter", f"an event filter has no {', '.join(unknown)}")
    named = {name: _text(found, name) for name in sorted(NAMES)}
    if not any(named.values()):
        raise Refused("event_filter", "an event filter names kind, output or producer")
    coalesce = found.get("coalesce", "each")
    if coalesce not in ("each", "latest"):
        raise Refused("event_filter", "coalesce is each or latest")
    return Filter(
        kind=named["kind"],
        output=named["output"],
        producer=named["producer"],
        coalesce=coalesce,
    )


def _text(found: JsonObject, name: str) -> str | None:
    value = found.get(name)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise Refused("event_filter", f"{name} is a non-empty string")
    return value


def producer_of(stored: Stored) -> str:
    """Who produced the object: an artifact names its app, anything else its writer.

    An app's landing carries the app as `fields.metadata.producer_app` (the `ArtifactRef` shape the
    apps package writes); a nested `fields.metadata.ref.producer_app` is read too, because a
    hand-landed artifact or a mirror may carry that shape."""
    metadata = stored.fields.get("metadata")
    if isinstance(metadata, dict):
        table = cast(dict[str, object], metadata)
        app = table.get("producer_app")
        if isinstance(app, str) and app:
            return app
        ref = table.get("ref")
        if isinstance(ref, dict):
            nested = cast(dict[str, object], ref).get("producer_app")
            if isinstance(nested, str) and nested:
                return nested
    return stored.principal


def output_of(stored: Stored) -> str | None:
    """The provides name an artifact landed under, when it names one."""
    found = stored.fields.get("type")
    return found if isinstance(found, str) and found else None


def landing(event: LibraryEvent, stored: Stored) -> Landing:
    return Landing(event.seq, event.object_id, stored.kind, output_of(stored), producer_of(stored))


def drain(
    ledger: Ledger,
    library: RefLog,
    *,
    home: Path,
    engine: HomeEngine,
    now: datetime,
    paused: bool = False,
) -> Drain:
    """Read the ref log once and queue the fires every event trigger on this engine owes.

    `home` is the engine's home directory, whose ledger holds the cursors; `engine` is the home
    literal this instance claims for, so the PC never drains a Contabo trigger's rows."""
    with Reader.open(home) as reader:
        found = [
            trigger
            for trigger in triggers(reader.connection)
            if trigger.kind == "event" and trigger.home_engine == engine
        ]
        cursors = {trigger.id: cursor_of(reader.connection, trigger.id) for trigger in found}
        was_paused = is_paused(reader.connection)
    if paused:
        if not was_paused:
            ledger.write(mark_paused())
        return Drain((), 0, max((seq for seq in cursors.values() if seq is not None), default=0))
    known = [seq for seq in cursors.values() if seq is not None]
    events = library.events(min(known) if known else 0)
    tail = max((event.seq for event in events), default=max(known, default=0))
    seen: dict[str, Landing | None] = {}
    plans: list[Plan] = []
    for trigger in found:
        try:
            wanted = filter_of(trigger)
        except Refused:
            plans.append(Plan(trigger, (), tail, "each"))
            continue
        cursor = cursors[trigger.id]
        if cursor is None or not trigger.enabled:
            plans.append(Plan(trigger, (), tail, wanted.coalesce))
            continue
        matched = tuple(
            match
            for event in events
            if event.seq > cursor
            and (match := resolve(event, library, seen)) is not None
            and match.matches(wanted)
        )
        coalesce = "latest" if was_paused else wanted.coalesce
        chosen = matched if coalesce == "each" else matched[-1:]
        plans.append(Plan(trigger, chosen, tail, wanted.coalesce))
    return ledger.write(record(plans, tail, now, resumed=was_paused))


def resolve(
    event: LibraryEvent, library: RefLog, seen: dict[str, Landing | None]
) -> Landing | None:
    """The row's landing, once per object per drain. A row whose object the store no longer has
    matches nothing: it cannot be read, so it cannot be the output a trigger waits for."""
    if event.object_id not in seen:
        try:
            seen[event.object_id] = landing(event, library.get(event.object_id))
        except LibraryRefused:
            seen[event.object_id] = None
    found = seen[event.object_id]
    if found is None:
        return None
    return Landing(event.seq, found.object_id, found.kind, found.output, found.producer)


def cursor_of(connection: sqlite3.Connection, trigger_id: str) -> int | None:
    """A trigger's cursor, or None when it has never drained."""
    row = connection.execute(
        "SELECT value FROM meta WHERE key = ?", (CURSOR + trigger_id,)
    ).fetchone()
    return None if row is None else int(str(row[0]))


def is_paused(connection: sqlite3.Connection) -> bool:
    row = connection.execute("SELECT value FROM meta WHERE key = ?", (PAUSED,)).fetchone()
    return row is not None


def mark_paused() -> Operation[None]:
    def operation(txn: Transaction) -> None:
        txn.connection.execute(
            "INSERT INTO meta (key, value) VALUES (?, '1')"
            " ON CONFLICT (key) DO UPDATE SET value = '1'",
            (PAUSED,),
        )

    return operation


def record(plans: list[Plan], tail: int, now: datetime, *, resumed: bool) -> Operation[Drain]:
    """Queue every planned fire and move every cursor in one transaction."""

    def operation(txn: Transaction) -> Drain:
        db = txn.connection
        fired: list[str] = []
        superseded = 0
        at = stamp(now)
        for plan in plans:
            if plan.coalesce == "latest" and plan.landings:
                newest = plan.landings[-1]
                superseded += db.execute(
                    "UPDATE fires SET status = 'skipped', ended_at = ?, detail = ?"
                    " WHERE trigger_id = ? AND status = 'pending'",
                    (at, f"superseded by object {newest.object_id}", plan.trigger.id),
                ).rowcount
            for found in plan.landings:
                if (fire_id := _insert(db, plan.trigger.id, found, now)) is not None:
                    fired.append(fire_id)
            db.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?)"
                " ON CONFLICT (key) DO UPDATE SET value = excluded.value",
                (CURSOR + plan.trigger.id, str(plan.cursor)),
            )
        if resumed:
            db.execute("DELETE FROM meta WHERE key = ?", (PAUSED,))
        return Drain(tuple(fired), superseded, tail)

    return operation


def _insert(db: sqlite3.Connection, trigger_id: str, found: Landing, now: datetime) -> str | None:
    """A pending fire for one landed object, or None when the object already fired this trigger."""
    fire_id = new_fire_id()
    occurrence = now
    while db.execute(
        "SELECT 1 FROM fires WHERE trigger_id = ? AND occurrence_at = ?",
        (trigger_id, stamp(occurrence)),
    ).fetchone():
        occurrence += timedelta(microseconds=1)
    cursor = db.execute(
        "INSERT OR IGNORE INTO fires"
        " (id, trigger_id, occurrence_at, status, merged, payload, delivery_id)"
        " VALUES (?, ?, ?, 'pending', 0, ?, ?)",
        (
            fire_id,
            trigger_id,
            stamp(occurrence),
            json.dumps(payload(found)),
            DELIVERY + found.object_id,
        ),
    )
    return fire_id if cursor.rowcount == 1 else None


def payload(found: Landing) -> JsonObject:
    """What the fire hands its run as `inputs.event`."""
    return {
        "event": {
            "object_id": found.object_id,
            "seq": found.seq,
            "kind": found.kind,
            "output": found.output,
            "producer": found.producer,
        }
    }
