"""Trigger and fire rows (SOLUTION-DESIGN 4.1), in `engine.sqlite` under the one writer (AD-23).

A trigger lives outside the definition and pins one published object (AD-10). It names one
`home_engine`: the place whose engine fires it, any name in his place list (AD-72), This PC
unless he names another. An engine instance claims only its own home's rows (AD-3); this one is
`pc`. A trigger is written only onto a listed place (`create`), and one whose place has since left
the list reads `blocked_config` with a line naming it (`standing`).
The kinds are `cron` in an IANA zone, `interval`, `manual`, `after`, `webhook`, `event` and
`session`. A `webhook` fires once per delivery id the host's door hands in (`deliver`). An `event`
row stores its filter; its matcher comes with TRG2b. A `session` row waits for copilot loops. A
fire is one occurrence of a trigger: at most one row per occurrence, which is what makes a claim
exclusive. A wake is a paused run's `resume_at`, which the ticker honours (AD-9).

`priority` orders waiting fires, higher first, then by age (AD-58); the spine's `normal | high` are
0 and `HIGH`. `ready_by` is a local `HH:MM` in the trigger's zone: as that deadline nears, the
fire's priority rises towards `HIGH` (`priority_at`).

`role_pins` and `effort_pin` override role resolution for the runs a trigger fires (B-60).
`source` is stored as 4.1 names it; nothing reads it yet. `incident_id` names the open incident.
"""

from __future__ import annotations

import json
import secrets
import sqlite3
from collections.abc import Collection
from dataclasses import dataclass, field, replace
from datetime import datetime, time, timedelta
from typing import Final, Literal, cast
from zoneinfo import ZoneInfo

from pydantic import JsonValue

from qmx_engine.ledger.store import Ledger, Operation, Transaction
from qmx_engine.service.context import Caller, Refused
from qmx_engine.settings import PC
from qmx_engine.triggers.catchup import CatchUp
from qmx_engine.triggers.cron import Clocked, Cron, Interval, after, instant, stamp

type JsonObject = dict[str, JsonValue]
type HomeEngine = str
"""A place name from the place list (`settings.places`), whatever he typed."""
type Delivery = Literal["inbox", "digest", "silent"]
type Delivered = Literal["delivered", "unverified", "failed", "none"]
"""What became of a fire's delivery, beside its status. An empty payload fails closed."""
type LastStatus = Literal["ok", "silent", "blocked_config", "failed", "delivery_failed", "unknown"]
type FireStatus = Literal[
    "pending",
    "claimed",
    "running",
    "held",
    "merged",
    "skipped",
    "ok",
    "silent",
    "blocked_config",
    "failed",
    "waiting",
    "unknown",
    "cancelled",
]

HERE: Final[HomeEngine] = PC
"""The home this engine instance claims for."""
LIVE: Final = ("claimed", "running")
"""Fire statuses that hold a lease."""
ENDINGS: Final = ("ok", "silent", "blocked_config", "failed", "unknown", "cancelled", "skipped")
"""Fire statuses a fire never leaves."""
HIGH: Final = 10
"""The spine's `high` priority, and the most `ready_by` adds."""


@dataclass(frozen=True, slots=True)
class Manual:
    pass


@dataclass(frozen=True, slots=True)
class After:
    workflow_item: str
    """The workflow whose finished runs fire this trigger."""


@dataclass(frozen=True, slots=True)
class Webhook:
    pass


@dataclass(frozen=True, slots=True)
class Event:
    filter: JsonObject
    """`kind`, `output`, `producer` and `coalesce` of AD-64, read by TRG2b's matcher."""


@dataclass(frozen=True, slots=True)
class Session:
    pass


type Spec = Cron | Interval | Manual | After | Webhook | Event | Session


@dataclass(frozen=True, slots=True)
class Trigger:
    id: str
    workflow_item: str
    pinned_object: str
    spec: Spec
    created_by: str
    created_at: str
    home_engine: HomeEngine = HERE
    follow_champion: bool = False
    enabled: bool = True
    precheck_ref: str | None = None
    """A source script in the pinned workflow's folder, run as a `monitor` before each fire."""
    role_pins: JsonObject = field(default_factory=dict[str, JsonValue])
    effort_pin: str | None = None
    delivery: Delivery = "digest"
    continuity: bool = False
    catch_up: CatchUp = "merged"
    max_concurrent: int = 1
    source: str = "ticker"
    next_fire_at: str | None = None
    last_status: LastStatus | None = None
    failure_streak: int = 0
    quota_hold_until: str | None = None
    incident_id: str | None = None
    last_outputs: JsonObject | None = None
    priority: int = 0
    ready_by: str | None = None
    """A local `HH:MM` in `zone`."""
    blocked: str | None = None
    """Why it cannot fire, read against the place list by `standing`; never stored."""

    @property
    def kind(self) -> str:
        match self.spec:
            case Cron():
                return "cron"
            case Interval():
                return "interval"
            case Manual():
                return "manual"
            case After():
                return "after"
            case Webhook():
                return "webhook"
            case Event():
                return "event"
            case Session():
                return "session"

    @property
    def zone(self) -> str:
        return self.spec.zone if isinstance(self.spec, Cron) else "UTC"

    @property
    def clocked(self) -> Clocked | None:
        return self.spec if isinstance(self.spec, Cron | Interval) else None


@dataclass(frozen=True, slots=True)
class Fire:
    id: str
    trigger_id: str
    occurrence_at: str
    status: FireStatus
    claimed_by: str | None = None
    lease_until: str | None = None
    detail: str | None = None
    run_id: str | None = None
    merged_into: str | None = None
    merged: int = 0
    payload: JsonObject | None = None
    digest: str | None = None
    delivery_id: str | None = None
    delivery: Delivered | None = None
    rerun: int = 0
    """How many spend-neutral re-runs came before this fire."""
    rerun_of: str | None = None
    """The first failed fire of a re-run chain."""


COLUMNS: Final = (
    "id, workflow_item, pinned_object, follow_champion, home_engine, kind, spec, enabled,"
    " precheck_ref, role_pins, effort_pin, delivery, continuity, catch_up, max_concurrent, source,"
    " created_by, created_at, next_fire_at, last_status, failure_streak, quota_hold_until,"
    " incident_id, last_outputs, priority, ready_by"
)
FIRE_COLUMNS: Final = (
    "id, trigger_id, occurrence_at, status, claimed_by, lease_until, detail, run_id, merged_into,"
    " merged, payload, digest, delivery_id, delivery, rerun, rerun_of"
)


def spec_json(spec: Spec) -> str:
    match spec:
        case Cron(expr, zone):
            found: JsonObject = {"expr": expr, "zone": zone}
        case Interval(seconds, _):
            found = {"seconds": seconds}
        case After(item):
            found = {"workflow_item": item}
        case Event(matched):
            found = {"filter": matched}
        case Manual() | Webhook() | Session():
            found = {}
    return json.dumps(found, sort_keys=True)


def spec_of(kind: str, text: str, created_at: str) -> Spec:
    data = json.loads(text)
    match kind:
        case "cron":
            return Cron(str(data["expr"]), str(data["zone"]))
        case "interval":
            return Interval(int(data["seconds"]), instant(created_at))
        case "after":
            return After(str(data["workflow_item"]))
        case "webhook":
            return Webhook()
        case "event":
            return Event(data["filter"])
        case "session":
            return Session()
        case _:
            return Manual()


def trigger_of(row: tuple[object, ...]) -> Trigger:
    (
        id_,
        item,
        pinned,
        follow,
        home,
        kind,
        spec,
        enabled,
        precheck,
        pins,
        effort,
        delivery,
        continuity,
        catch_up,
        max_concurrent,
        source,
        by,
        created,
        next_fire,
        last,
        streak,
        hold,
        incident,
        outputs,
        priority,
        ready_by,
    ) = row
    return Trigger(
        id=str(id_),
        workflow_item=str(item),
        pinned_object=str(pinned),
        spec=spec_of(str(kind), str(spec), str(created)),
        created_by=str(by),
        created_at=str(created),
        home_engine=str(home),
        follow_champion=bool(follow),
        enabled=bool(enabled),
        precheck_ref=cast(str | None, precheck),
        role_pins=json.loads(str(pins)),
        effort_pin=cast(str | None, effort),
        delivery=cast(Delivery, delivery),
        continuity=bool(continuity),
        catch_up=cast(CatchUp, catch_up),
        max_concurrent=cast(int, max_concurrent),
        source=str(source),
        next_fire_at=cast(str | None, next_fire),
        last_status=cast(LastStatus | None, last),
        failure_streak=cast(int, streak),
        quota_hold_until=cast(str | None, hold),
        incident_id=cast(str | None, incident),
        last_outputs=None if outputs is None else json.loads(str(outputs)),
        priority=cast(int, priority),
        ready_by=cast(str | None, ready_by),
    )


def fire_of(row: tuple[object, ...]) -> Fire:
    (
        id_,
        trigger,
        occurrence,
        status,
        by,
        lease,
        detail,
        run,
        into,
        merged,
        payload,
        digest,
        delivery_id,
        delivery,
        rerun,
        rerun_of,
    ) = row
    return Fire(
        str(id_),
        str(trigger),
        str(occurrence),
        cast(FireStatus, status),
        cast(str | None, by),
        cast(str | None, lease),
        cast(str | None, detail),
        cast(str | None, run),
        cast(str | None, into),
        cast(int, merged),
        None if payload is None else json.loads(str(payload)),
        cast(str | None, digest),
        cast(str | None, delivery_id),
        cast(Delivered | None, delivery),
        cast(int, rerun),
        cast(str | None, rerun_of),
    )


def first_fire(spec: Spec, created: datetime) -> str | None:
    match spec:
        case Cron() | Interval():
            return stamp(next(after(spec, created)))
        case _:
            return None


def create(
    ledger: Ledger,
    *,
    workflow_item: str,
    pinned_object: str,
    spec: Spec,
    caller: Caller,
    now: datetime,
    home_engine: HomeEngine = HERE,
    follow_champion: bool = False,
    precheck_ref: str | None = None,
    delivery: Delivery = "digest",
    continuity: bool = False,
    catch_up: CatchUp = "merged",
    max_concurrent: int = 1,
    priority: int = 0,
    ready_by: str | None = None,
    places: Collection[str] = (HERE,),
) -> Trigger:
    """A new trigger, created by a user or an agent. A run never creates one (SOLUTION-DESIGN
    4.2 step 7). `places` is the place list its home must be in."""
    if caller.kind == "workflow":
        raise Refused("trigger_refused", "a workflow run cannot create, edit or enable triggers")
    if home_engine not in places:
        raise Refused("place_unknown", f"the place '{home_engine}' is not in the place list")
    if isinstance(spec, Interval):
        spec = Interval(spec.seconds, now)
    trigger = Trigger(
        id=f"trigger-{secrets.token_hex(6)}",
        workflow_item=workflow_item,
        pinned_object=pinned_object,
        spec=spec,
        created_by=caller.principal,
        created_at=stamp(now),
        home_engine=home_engine,
        follow_champion=follow_champion,
        precheck_ref=precheck_ref,
        delivery=delivery,
        continuity=continuity,
        catch_up=catch_up,
        max_concurrent=max_concurrent,
        next_fire_at=first_fire(spec, now),
        priority=priority,
        ready_by=ready_by,
    )
    ledger.write(insert(trigger))
    return trigger


def insert(trigger: Trigger) -> Operation[None]:
    def operation(txn: Transaction) -> None:
        txn.connection.execute(
            f"INSERT INTO triggers ({COLUMNS}) VALUES ({', '.join('?' * 26)})",  # noqa: S608
            (
                trigger.id,
                trigger.workflow_item,
                trigger.pinned_object,
                int(trigger.follow_champion),
                trigger.home_engine,
                trigger.kind,
                spec_json(trigger.spec),
                int(trigger.enabled),
                trigger.precheck_ref,
                json.dumps(trigger.role_pins),
                trigger.effort_pin,
                trigger.delivery,
                int(trigger.continuity),
                trigger.catch_up,
                trigger.max_concurrent,
                trigger.source,
                trigger.created_by,
                trigger.created_at,
                trigger.next_fire_at,
                trigger.last_status,
                trigger.failure_streak,
                trigger.quota_hold_until,
                trigger.incident_id,
                None if trigger.last_outputs is None else json.dumps(trigger.last_outputs),
                trigger.priority,
                trigger.ready_by,
            ),
        )

    return operation


def new_fire_id() -> str:
    return f"fire-{secrets.token_hex(6)}"


def fire_now(ledger: Ledger, trigger_id: str, now: datetime, payload: JsonObject) -> str:
    """A pending fire of a `manual` or `after` trigger, claimed on the next tick."""
    fire_id = new_fire_id()

    def operation(txn: Transaction) -> None:
        txn.connection.execute(
            "INSERT INTO fires (id, trigger_id, occurrence_at, status, merged, payload)"
            " VALUES (?, ?, ?, 'pending', 0, ?)",
            (fire_id, trigger_id, stamp(now), json.dumps(payload)),
        )

    ledger.write(operation)
    return fire_id


def triggers(connection: sqlite3.Connection, where: str = "", *args: object) -> list[Trigger]:
    rows = connection.execute(
        f"SELECT {COLUMNS} FROM triggers {where} ORDER BY created_at, id",  # noqa: S608
        args,
    ).fetchall()
    return [trigger_of(row) for row in rows]


def standing(trigger: Trigger, places: Collection[str]) -> Trigger:
    """The trigger as he should see it: one homed on a place no longer in the list reads
    `blocked_config` with a line naming the place, until the place is listed again."""
    if trigger.home_engine in places:
        return trigger
    line = f"the place '{trigger.home_engine}' was removed"
    return replace(trigger, last_status="blocked_config", blocked=line)


def fires(connection: sqlite3.Connection, trigger_id: str) -> list[Fire]:
    rows = connection.execute(
        f"SELECT {FIRE_COLUMNS} FROM fires WHERE trigger_id = ?"  # noqa: S608
        " ORDER BY occurrence_at, id",
        (trigger_id,),
    ).fetchall()
    return [fire_of(row) for row in rows]


def priority_at(trigger: Trigger, occurrence: datetime, now: datetime, window: float) -> int:
    """The fire's priority at `now`: its own, raised by up to `HIGH` over the `window` seconds
    before the first `ready_by` at or after its occurrence, and by all of `HIGH` once past it."""
    if trigger.ready_by is None:
        return trigger.priority
    zone = ZoneInfo(trigger.zone)
    local = occurrence.astimezone(zone)
    due = datetime.combine(local.date(), time.fromisoformat(trigger.ready_by), zone)
    if due < local:
        due += timedelta(days=1)
    left = (due - now).total_seconds()
    if left >= window:
        return trigger.priority
    return trigger.priority + (HIGH if left <= 0 else round(HIGH * (1 - left / window)))


def deliver(
    ledger: Ledger, trigger_id: str, delivery_id: str, payload: JsonObject, now: datetime
) -> tuple[str, bool]:
    """A pending fire for one webhook delivery, and whether it is new: a delivery id seen before
    returns the fire it made."""

    def operation(txn: Transaction) -> tuple[str, bool]:
        db = txn.connection
        seen = db.execute(
            "SELECT id FROM fires WHERE trigger_id = ? AND delivery_id = ?",
            (trigger_id, delivery_id),
        ).fetchone()
        if seen is not None:
            return str(seen[0]), False
        fire_id, at = new_fire_id(), now
        while db.execute(
            "SELECT 1 FROM fires WHERE trigger_id = ? AND occurrence_at = ?",
            (trigger_id, stamp(at)),
        ).fetchone():
            at += timedelta(microseconds=1)
        db.execute(
            "INSERT INTO fires (id, trigger_id, occurrence_at, status, merged, payload,"
            " delivery_id) VALUES (?, ?, ?, 'pending', 0, ?, ?)",
            (fire_id, trigger_id, stamp(at), json.dumps(payload), delivery_id),
        )
        return fire_id, True

    return ledger.write(operation)


def put_wake(run_id: str, resume_at: str) -> Operation[None]:
    """Ask the ticker to resume a paused run at `resume_at`. A later pause replaces the wake and
    frees its lease."""

    def operation(txn: Transaction) -> None:
        txn.connection.execute(
            "INSERT OR REPLACE INTO wakes (run_id, resume_at, claimed_by, lease_until)"
            " VALUES (?, ?, NULL, NULL)",
            (run_id, stamp(instant(resume_at))),
        )

    return operation
