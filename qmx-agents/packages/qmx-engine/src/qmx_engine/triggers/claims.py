"""Claiming fires and wakes under a lease, and settling fires (AD-10, SOLUTION-DESIGN 4.2).

A claim is one ledger transaction. It inserts at most one `fire` row per occurrence, so a second
claimant that comes to the same occurrence finds the row and skips it. A claimed fire carries a
lease that its claimant's heartbeat renews every tick. A fire whose lease ran out belongs to a
claimant that died; the next claimant takes it over and resumes its run if one started.

A trigger on a quota hold merges every occurrence into its one held fire, and the held fire is
claimed once the hold ends. A trigger already running `max_concurrent` fires stays due, so its
next occurrence fires once one ends.

A fire ends once: `settle` never writes over an ending, and `settle_run` ends the fire of a run a
wake finished whether that fire still reads `waiting` or its own task has not yet written it, so a
late `waiting` cannot reopen a fire whose run already ended (L-65).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final

from qmx_engine.ledger.store import Operation, Transaction
from qmx_engine.triggers.catchup import collapse
from qmx_engine.triggers.cron import after, instant, missed, stamp
from qmx_engine.triggers.rows import (
    COLUMNS,
    ENDINGS,
    FIRE_COLUMNS,
    Fire,
    FireStatus,
    HomeEngine,
    JsonObject,
    LastStatus,
    Trigger,
    fire_of,
    new_fire_id,
    trigger_of,
)

LAST: Final[dict[FireStatus, LastStatus]] = {
    "ok": "ok",
    "silent": "silent",
    "blocked_config": "blocked_config",
    "failed": "failed",
    "unknown": "unknown",
}
"""A fire's ending as its trigger's `last_status`; other endings leave it unchanged."""
ENDED: Final = ", ".join(f"'{status}'" for status in ENDINGS)
JOINED: Final = ", ".join(f"t.{column.strip()}" for column in COLUMNS.split(","))


@dataclass(frozen=True, slots=True)
class Claimed:
    fire: Fire
    trigger: Trigger


@dataclass(frozen=True, slots=True)
class Lease:
    claimant: str
    now: datetime
    seconds: float

    @property
    def at(self) -> str:
        return stamp(self.now)

    @property
    def until(self) -> str:
        return stamp(self.now + timedelta(seconds=self.seconds))


def claim_due(
    lease: Lease, *, grace: timedelta, home: HomeEngine, busy: Collection[str] = ()
) -> Operation[list[Claimed]]:
    """Every fire this claimant takes on this tick. `busy` names fires it runs already."""

    def operation(txn: Transaction) -> list[Claimed]:
        db = txn.connection
        due = db.execute(
            f"SELECT {COLUMNS} FROM triggers WHERE home_engine = ? AND enabled = 1"  # noqa: S608
            " AND (next_fire_at <= ? OR quota_hold_until <= ?)",
            (home, lease.at, lease.at),
        ).fetchall()
        claimed: list[Claimed] = []
        for row in due:
            claimed += _clocked(db, trigger_of(row), lease, grace)
        claimed += _pending(db, lease, home)
        claimed += _stale(db, lease, home, busy)
        return claimed

    return operation


def _clocked(
    db: sqlite3.Connection, trigger: Trigger, lease: Lease, grace: timedelta
) -> list[Claimed]:
    schedule = trigger.clocked
    occurrences: list[datetime] = []
    next_fire = trigger.next_fire_at
    if schedule is not None and next_fire is not None and next_fire <= lease.at:
        occurrences = missed(schedule, instant(next_fire), lease.now)
        next_fire = stamp(next(after(schedule, lease.now)))
    held = _held(db, trigger.id)
    if trigger.quota_hold_until is not None and held is not None:
        _merge(db, held, occurrences)
        _advance(db, trigger.id, next_fire)
        if trigger.quota_hold_until > lease.at:
            return []
        db.execute("UPDATE triggers SET quota_hold_until = NULL WHERE id = ?", (trigger.id,))
        return [Claimed(_take(db, held.id, lease), trigger)]
    if _live(db, trigger.id, lease.at) >= trigger.max_concurrent:
        return []
    plan = collapse(occurrences, lease.now, grace, trigger.catch_up)
    for occurrence, why in plan.skipped:
        _insert(db, trigger.id, occurrence, "skipped", detail=why)
    _advance(db, trigger.id, next_fire)
    if plan.fire is None:
        return []
    fire_id = _insert(db, trigger.id, plan.fire, "claimed", lease=lease)
    return [] if fire_id is None else [Claimed(_get(db, fire_id), trigger)]


def _pending(db: sqlite3.Connection, lease: Lease, home: HomeEngine) -> list[Claimed]:
    rows = db.execute(
        f"SELECT {JOINED}, f.id"  # noqa: S608
        " FROM fires f JOIN triggers t ON t.id = f.trigger_id WHERE f.status = 'pending'"
        " AND t.home_engine = ? AND t.enabled = 1 ORDER BY f.occurrence_at, f.id",
        (home,),
    ).fetchall()
    claimed: list[Claimed] = []
    for row in rows:
        trigger = trigger_of(row[:-1])
        if _live(db, trigger.id, lease.at) < trigger.max_concurrent:
            claimed.append(Claimed(_take(db, str(row[-1]), lease), trigger))
    return claimed


def _stale(
    db: sqlite3.Connection, lease: Lease, home: HomeEngine, busy: Collection[str]
) -> list[Claimed]:
    """Take over fires whose claimant died. A fire whose run left a wake paused before the
    death: the wake owns that run, so the fire only waits on it and is never resumed here."""
    db.execute(
        "UPDATE fires SET status = 'waiting', lease_until = NULL"
        " WHERE status IN ('claimed', 'running') AND lease_until <= ?"
        " AND run_id IN (SELECT run_id FROM wakes)",
        (lease.at,),
    )
    rows = db.execute(
        f"SELECT {JOINED}, f.id"  # noqa: S608
        " FROM fires f JOIN triggers t ON t.id = f.trigger_id"
        " WHERE f.status IN ('claimed', 'running') AND f.lease_until <= ? AND t.home_engine = ?",
        (lease.at, home),
    ).fetchall()
    return [
        Claimed(_take(db, str(row[-1]), lease), trigger_of(row[:-1]))
        for row in rows
        if row[-1] not in busy
    ]


def _live(db: sqlite3.Connection, trigger_id: str, now: str) -> int:
    (count,) = db.execute(
        "SELECT count(*) FROM fires WHERE trigger_id = ? AND status IN ('claimed', 'running')"
        " AND lease_until > ?",
        (trigger_id, now),
    ).fetchone()
    return int(count)


def _held(db: sqlite3.Connection, trigger_id: str) -> Fire | None:
    row = db.execute(
        f"SELECT {FIRE_COLUMNS} FROM fires WHERE trigger_id = ? AND status = 'held'",  # noqa: S608
        (trigger_id,),
    ).fetchone()
    return None if row is None else fire_of(row)


def _get(db: sqlite3.Connection, fire_id: str) -> Fire:
    row = db.execute(
        f"SELECT {FIRE_COLUMNS} FROM fires WHERE id = ?",  # noqa: S608
        (fire_id,),
    ).fetchone()
    return fire_of(row)


def _insert(
    db: sqlite3.Connection,
    trigger_id: str,
    occurrence: datetime,
    status: FireStatus,
    *,
    detail: str | None = None,
    lease: Lease | None = None,
    merged_into: str | None = None,
) -> str | None:
    """The new fire's id, or None when the occurrence already has a fire."""
    fire_id = new_fire_id()
    cursor = db.execute(
        "INSERT OR IGNORE INTO fires (id, trigger_id, occurrence_at, status, detail, claimed_by,"
        " claimed_at, lease_until, merged_into, merged) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
        (
            fire_id,
            trigger_id,
            stamp(occurrence),
            status,
            detail,
            None if lease is None else lease.claimant,
            None if lease is None else lease.at,
            None if lease is None else lease.until,
            merged_into,
        ),
    )
    return fire_id if cursor.rowcount == 1 else None


def _merge(db: sqlite3.Connection, held: Fire, occurrences: list[datetime]) -> None:
    added = sum(
        _insert(db, held.trigger_id, o, "merged", merged_into=held.id) is not None
        for o in occurrences
    )
    db.execute("UPDATE fires SET merged = merged + ? WHERE id = ?", (added, held.id))


def _take(db: sqlite3.Connection, fire_id: str, lease: Lease) -> Fire:
    """Claim a pending, held or stale fire; a stale one keeps its status and run."""
    db.execute(
        "UPDATE fires SET claimed_by = ?, claimed_at = ?, lease_until = ?,"
        " status = CASE WHEN status = 'running' THEN 'running' ELSE 'claimed' END WHERE id = ?",
        (lease.claimant, lease.at, lease.until, fire_id),
    )
    return _get(db, fire_id)


def _advance(db: sqlite3.Connection, trigger_id: str, next_fire: str | None) -> None:
    db.execute("UPDATE triggers SET next_fire_at = ? WHERE id = ?", (next_fire, trigger_id))


def heartbeat(lease: Lease, fire_ids: Collection[str], run_ids: Collection[str]) -> Operation[None]:
    """Renew the lease on every fire and wake this claimant holds."""

    def operation(txn: Transaction) -> None:
        db = txn.connection
        db.executemany(
            "UPDATE fires SET lease_until = ? WHERE id = ? AND claimed_by = ?",
            [(lease.until, f, lease.claimant) for f in fire_ids],
        )
        db.executemany(
            "UPDATE wakes SET lease_until = ? WHERE run_id = ? AND claimed_by = ?",
            [(lease.until, r, lease.claimant) for r in run_ids],
        )

    return operation


def claim_wakes(lease: Lease, busy: Collection[str] = ()) -> Operation[list[tuple[str, str]]]:
    """Each paused run whose `resume_at` has come, with that instant, unless another claimant
    holds its wake."""

    def operation(txn: Transaction) -> list[tuple[str, str]]:
        db = txn.connection
        rows = db.execute(
            "SELECT run_id, resume_at FROM wakes WHERE resume_at <= ?"
            " AND (lease_until IS NULL OR lease_until <= ?) ORDER BY resume_at, run_id",
            (lease.at, lease.at),
        ).fetchall()
        found = [(str(run), str(at)) for run, at in rows if run not in busy]
        db.executemany(
            "UPDATE wakes SET claimed_by = ?, lease_until = ? WHERE run_id = ?",
            [(lease.claimant, lease.until, run) for run, _ in found],
        )
        return found

    return operation


def end_wake(run_id: str, claimant: str) -> Operation[None]:
    """Drop a wake once its run was resumed; a newer pause has replaced it and is kept."""

    def operation(txn: Transaction) -> None:
        txn.connection.execute(
            "DELETE FROM wakes WHERE run_id = ? AND claimed_by = ?", (run_id, claimant)
        )

    return operation


def start(fire_id: str, run_id: str) -> Operation[None]:
    def operation(txn: Transaction) -> None:
        txn.connection.execute(
            "UPDATE fires SET status = 'running', run_id = ? WHERE id = ?", (run_id, fire_id)
        )

    return operation


def hold(fire: Fire, until: str) -> Operation[None]:
    """Park a fire into a closed usage window; later occurrences merge into it."""

    def operation(txn: Transaction) -> None:
        db = txn.connection
        db.execute(
            "UPDATE fires SET status = 'held', claimed_by = NULL, lease_until = NULL,"
            " detail = ? WHERE id = ?",
            (f"quota hold until {until}", fire.id),
        )
        db.execute(
            "UPDATE triggers SET quota_hold_until = ? WHERE id = ?", (until, fire.trigger_id)
        )

    return operation


def settle(
    fire: Fire,
    status: FireStatus,
    at: str,
    *,
    detail: str | None = None,
    digest: str | None = None,
    outputs: JsonObject | None = None,
) -> Operation[None]:
    """End a fire, and carry its ending to the trigger: `last_status`, the failure streak, and
    the outputs `continuity` injects next time."""

    def operation(txn: Transaction) -> None:
        db = txn.connection
        cursor = db.execute(
            "UPDATE fires SET status = ?, detail = coalesce(?, detail), digest = ?,"  # noqa: S608
            f" ended_at = ?, lease_until = NULL WHERE id = ? AND status NOT IN ({ENDED})",
            (status, detail, digest, at, fire.id),
        )
        if cursor.rowcount:
            _carry(db, fire.trigger_id, status, outputs)

    return operation


def settle_run(
    run_id: str, status: FireStatus, at: str, outputs: JsonObject | None
) -> Operation[None]:
    """End the fire whose run a wake resumed and finished: a fire reading `waiting`, or one whose
    task still runs and has not settled it yet."""

    def operation(txn: Transaction) -> None:
        db = txn.connection
        row = db.execute(
            "SELECT trigger_id FROM fires WHERE run_id = ?"
            " AND status IN ('waiting', 'claimed', 'running')",
            (run_id,),
        ).fetchone()
        if row is None:
            return
        db.execute(
            "UPDATE fires SET status = ?, ended_at = ?, lease_until = NULL WHERE run_id = ?"
            " AND status IN ('waiting', 'claimed', 'running')",
            (status, at, run_id),
        )
        _carry(db, str(row[0]), status, outputs)

    return operation


def _carry(
    db: sqlite3.Connection, trigger_id: str, status: FireStatus, outputs: JsonObject | None
) -> None:
    last = LAST.get(status)
    if last is None:
        return
    failing = last in ("failed", "blocked_config", "unknown")
    db.execute(
        "UPDATE triggers SET last_status = ?,"
        " failure_streak = CASE WHEN ? THEN failure_streak + 1 ELSE 0 END,"
        " last_outputs = coalesce(?, last_outputs) WHERE id = ?",
        (last, failing, None if outputs is None else json.dumps(outputs), trigger_id),
    )
