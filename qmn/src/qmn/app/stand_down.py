"""The node's stand-down table, as data, and the stand-downs it holds (Level 0 AD-38).

Every automatic stand-down stops new entries at its scope and nothing else: exits, the stops
the broker holds and the kill switch keep working, because the order path consults a
stand-down only before an entry. Each row clears the way AD-38's table says. Four clear by
themselves once their cause has been gone for the row's named time; three wait for him.

A risk stop is the one automatic move in trading (standing order 7). It lands one
``lifecycle`` row in the unit's journal, ``by: {kind: risk_rule}``, and holds the unit's
entries on that market until his ``resume`` reaches a scope that covers it. His resume lands
the move back out of ``stopped``, naming the stop it clears. Nothing resumes or promotes on
its own.

Every value below is a named setting with a starting default. The clock bands are labelled
placeholders, because the registry rows that will hold them are still blank.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Final

from qmf.core import is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_kinds.unit import LIFECYCLE_SCHEMA
from qmf.data.journal_writer import JournalWriter, WriterScope

from qmn.app.feed_keeper import FeedKeeper
from qmn.app.store import Change, Json, Outcome

__all__ = [
    "CLOCK_INSIDE_FOR_NS",
    "CLOCK_NO_NEW_ENTRIES_NS",
    "CLOCK_WARN_NS",
    "DISK_GUARD_BYTES",
    "DISK_MARGIN_BYTES",
    "FEED_FRESH_FOR_NS",
    "FEED_STALE_AFTER_NS",
    "REPEATED_FAULT_RESTARTS",
    "REPEATED_FAULT_WINDOW_NS",
    "TABLE",
    "Clears",
    "Held",
    "Kind",
    "Row",
    "StandDowns",
    "Subject",
    "Word",
]

FEED_STALE_AFTER_NS: Final = 120_000_000_000
"""`[node] feed_stale_after_s`, starting at 120 s: a market whose last quote is older stops
new entries on it."""
FEED_FRESH_FOR_NS: Final = 60_000_000_000
"""`[node] feed_fresh_for_s`, starting at 60 s: how long a stale market's feed must be fresh
again before entries resume on it."""
CLOCK_WARN_NS: Final = 100_000_000
"""`[node] clock_warn_ms`, starting at 100 ms, a labelled placeholder (`clock_drift_warn`)."""
CLOCK_NO_NEW_ENTRIES_NS: Final = 500_000_000
"""`[node] clock_no_new_entries_ms`, starting at 500 ms, a labelled placeholder
(`clock_drift_no_new_entry`): an offset past it stops new entries."""
CLOCK_INSIDE_FOR_NS: Final = 300_000_000_000
"""`[node] clock_inside_for_s`, starting at 5 minutes: how long the offset must stay inside the
warn band before entries resume."""
DISK_GUARD_BYTES: Final = 2 * 1024**3
"""`[node] journal_guard_bytes`, starting at 2 GB: free space below it stops new entries."""
DISK_MARGIN_BYTES: Final = 1024**3
"""`[node] journal_guard_margin_bytes`, starting at 1 GB: entries resume once free space is back
above the guard plus this margin."""
REPEATED_FAULT_RESTARTS: Final = 5
"""`[node] crash_loop_restarts`, starting at 5: restarts inside the window that stand the node
down (`funnel/solutions/node.md` section 10). The healing fold (C-13) counts them."""
REPEATED_FAULT_WINDOW_NS: Final = 600_000_000_000
"""`[node] crash_loop_window_s`, starting at 10 minutes."""


class Kind(StrEnum):
    STALE_FEED = "stale_feed"
    CLOCK_BAND = "clock_band"
    DISK = "disk"
    VENUE_NOT_READY = "venue_not_ready"
    REPEATED_FAULT = "repeated_fault"
    SPEC_CHANGE = "spec_change"
    RISK_STOP = "risk_stop"


class Clears(StrEnum):
    ITSELF = "itself"
    HIS_RESUME = "his_resume"
    HIS_CLICK = "his_click"


class Word(StrEnum):
    """A health stop and a risk stop are different words on every screen (AD-38)."""

    HEALTH = "Stopped by a health check"
    RISK = "Stopped by a risk rule"


@dataclass(frozen=True, slots=True)
class Row:
    """One row of AD-38's stand-down table.

    ``held_for_ns`` is how long the cause must stay gone before a row that clears itself
    clears; zero clears at once. ``blocks`` is the reason text an entry it stops carries,
    worded so QMB's journal files it under its reason code.
    """

    kind: Kind
    entries_stop_when: str
    clears: Clears
    clears_when: str
    starting_default: str
    word: Word
    blocks: str
    held_for_ns: int = 0


TABLE: Final[Mapping[Kind, Row]] = {
    Kind.STALE_FEED: Row(
        Kind.STALE_FEED,
        "a market's feed is older than its stale_after",
        Clears.ITSELF,
        "the feed is fresh again for a named time",
        "60 s fresh",
        Word.HEALTH,
        "stood down, stale feed: the node cannot prove a fresh price",
        FEED_FRESH_FOR_NS,
    ),
    Kind.CLOCK_BAND: Row(
        Kind.CLOCK_BAND,
        "the offset passes the no-new-entries band",
        Clears.ITSELF,
        "the offset is back inside the warn band for a named time",
        "5 minutes inside",
        Word.HEALTH,
        "stood down, clock band: the node cannot prove its clock",
        CLOCK_INSIDE_FOR_NS,
    ),
    Kind.DISK: Row(
        Kind.DISK,
        "free space falls below the journal guard",
        Clears.ITSELF,
        "free space is back above the guard",
        "the guard plus a named margin",
        Word.HEALTH,
        "stood down, disk: free space is below the node journal guard",
    ),
    Kind.VENUE_NOT_READY: Row(
        Kind.VENUE_NOT_READY,
        "the session drops or its capabilities fail re-verification",
        Clears.ITSELF,
        "authenticated, subscribed and re-verified",
        "as built",
        Word.HEALTH,
        "venue not ready",
    ),
    Kind.REPEATED_FAULT: Row(
        Kind.REPEATED_FAULT,
        "the same technical fault repeats past the crash-loop fold",
        Clears.HIS_RESUME,
        "his resume",
        "5 restarts in 10 minutes",
        Word.HEALTH,
        "stood down, repeated fault: the node cannot prove its runtime is sound until his resume",
    ),
    Kind.SPEC_CHANGE: Row(
        Kind.SPEC_CHANGE,
        "the broker changes a symbol's lot step, margin, digits, leverage or trading mode",
        Clears.HIS_CLICK,
        "his click on the change card",
        "his click",
        Word.HEALTH,
        "stood down, spec change: the node cannot prove its orders against the broker's"
        " changed record until his click",
    ),
    Kind.RISK_STOP: Row(
        Kind.RISK_STOP,
        "a risk rule fires",
        Clears.HIS_RESUME,
        "his resume",
        "his resume",
        Word.RISK,
        "risk stop: a risk rule holds this unit's entries, as the kill switch would, until his"
        " resume",
    ),
}
"""AD-38's table, row by row. The venue row's text is the order path's own guard, which
already stops entries while the session is not ready."""


@dataclass(frozen=True, slots=True)
class Subject:
    """The deployment a risk stop holds, and the unit and market its ``lifecycle`` row moves."""

    deployment_id: str
    unit_id: str
    version_ref: str
    compiled_fingerprint: str
    market_id: str
    lane: str
    world: JournalWorld


@dataclass(frozen=True, slots=True)
class Held:
    """One stand-down in force at one scope.

    ``covers`` are the scopes his resume clears it from; ``healthy_since_ns`` is when a row
    that clears itself last saw its cause gone. A risk stop carries its subject and the
    ``event_id`` of its ``lifecycle`` row."""

    kind: Kind
    scope: str
    since_ns: int
    cause: str
    covers: frozenset[str] = frozenset({"all"})
    healthy_since_ns: int | None = None
    subject: Subject | None = None
    event_id: str | None = None

    @property
    def row(self) -> Row:
        return TABLE[self.kind]

    def document(self) -> dict[str, Json]:
        return {
            "stand_down": self.kind.value,
            "scope": self.scope,
            "word": self.row.word.value,
            "cause": self.cause,
            "clears": self.row.clears.value,
            "since_ns": self.since_ns,
            "lifecycle_event": self.event_id,
        }


def _iso(at_ns: int) -> str:
    return datetime.fromtimestamp(at_ns / 1e9, UTC).isoformat()


def _event_id(*parts: str) -> str:
    digest = hashlib.sha256("/".join(parts).encode("utf-8")).hexdigest()
    return f"lifecycle-{digest[:24]}"


class StandDowns:
    """The stand-downs this node holds, journalled as they start and clear.

    ``free_bytes`` and ``clock_offset_ns`` are the node's probes: the volume's free space and
    the clock's offset from its time source, None while no probe has read one.
    """

    def __init__(
        self,
        journal: JournalWriter,
        *,
        journal_root: Path,
        machine: str,
        build: str,
        boot_epoch_id: str,
        clock_ns: Callable[[], int],
        free_bytes: Callable[[], int],
        clock_offset_ns: Callable[[], int | None] = lambda: None,
    ) -> None:
        self.journal = journal
        self.journal_root = journal_root
        self.machine = machine
        self.build = build
        self.boot_epoch_id = boot_epoch_id
        self.clock_ns = clock_ns
        self.free_bytes = free_bytes
        self.clock_offset_ns = clock_offset_ns
        self.held: dict[tuple[Kind, str], Held] = {}
        self._lifecycle: dict[tuple[str, JournalWorld], JournalWriter] = {}

    # --- what stops entries ---

    def blocking(self, scopes: Iterable[str]) -> Held | None:
        """The first stand-down in force at any of ``scopes``, or None."""
        wanted = set(scopes)
        return next((held for held in self.held.values() if held.scope in wanted), None)

    def document(self) -> list[dict[str, Json]]:
        return [held.document() for held in self.held.values()]

    # --- the rows that clear by themselves ---

    def watch_node(self) -> None:
        """The clock band and the disk guard, node-wide."""
        now = self.clock_ns()
        offset = self.clock_offset_ns()
        if offset is not None:
            band = (
                True
                if abs(offset) > CLOCK_NO_NEW_ENTRIES_NS
                else (False if abs(offset) <= CLOCK_WARN_NS else None)
            )
            self._observe(Kind.CLOCK_BAND, "all", band, now, f"clock offset {offset} ns")
        free = self.free_bytes()
        low = (
            True
            if free < DISK_GUARD_BYTES
            else (False if free > DISK_GUARD_BYTES + DISK_MARGIN_BYTES else None)
        )
        self._observe(Kind.DISK, "all", low, now, f"{free} bytes free")

    def watch_feed(self, account_id: str, feed: FeedKeeper) -> None:
        """The binding's session and each of its markets' feed age."""
        now = self.clock_ns()
        self._observe(
            Kind.VENUE_NOT_READY, f"account:{account_id}", not feed.ready, now, feed.reason
        )
        for market in feed.markets:
            quote = feed.quote(market)
            if quote is None:
                continue
            age = now - quote.receive_time
            self._observe(
                Kind.STALE_FEED,
                f"instrument:{market}",
                age > FEED_STALE_AFTER_NS,
                now,
                f"last quote {age // 1_000_000_000} s ago",
            )

    def _observe(self, kind: Kind, scope: str, bad: bool | None, now: int, cause: str) -> None:
        """One reading of a row that clears itself: True is its cause, False is healthy and
        None is between its bands, which keeps a held row held and starts nothing."""
        key = (kind, scope)
        held = self.held.get(key)
        if bad is True:
            if held is None:
                self._start(Held(kind, scope, now, cause))
            elif held.healthy_since_ns is not None:
                self.held[key] = replace(held, healthy_since_ns=None)
            return
        if held is None:
            return
        if bad is None:
            if held.healthy_since_ns is not None:
                self.held[key] = replace(held, healthy_since_ns=None)
            return
        since = now if held.healthy_since_ns is None else held.healthy_since_ns
        if now - since >= held.row.held_for_ns:
            self._clear(held, "itself")
        else:
            self.held[key] = replace(held, healthy_since_ns=since)

    # --- the rows that wait for him ---

    def hold(self, kind: Kind, scope: str, cause: str, *, covers: Iterable[str] = ()) -> bool:
        """Start a stand-down that waits for his resume or click; True when it was not held."""
        if (kind, scope) in self.held:
            return False
        self._start(Held(kind, scope, self.clock_ns(), cause, frozenset({"all", *covers})))
        return True

    def risk_stop(
        self, subject: Subject, rule: str, reason: str, *, covers: Iterable[str]
    ) -> str | None:
        """A risk rule stops ``subject``: one ``lifecycle`` row, ``by: risk_rule``, and the
        unit's entries on that market held until his resume. A rule firing again while the
        stop holds lands nothing. Answers the stop's event id, or None when its row could not
        be written."""
        scope = f"unit:{subject.deployment_id}:{subject.market_id}"
        held = self.held.get((Kind.RISK_STOP, scope))
        if held is not None:
            return held.event_id
        now = self.clock_ns()
        event_id = _event_id("risk_stop", subject.deployment_id, subject.market_id, rule, str(now))
        body = self._move(subject, event_id, subject.lane, "stopped", now, reason=reason)
        body["by"] = {"kind": "risk_rule", "principal": rule}
        if not self._land(subject, body):
            return None
        self._start(
            Held(
                Kind.RISK_STOP,
                scope,
                now,
                f"{rule}: {reason}",
                frozenset({"all", *covers}),
                subject=subject,
                event_id=event_id,
            )
        )
        return event_id

    def resumes(self, changes: Sequence[Change]) -> None:
        """His ``resume`` clears each stand-down waiting for him that it covers and that
        started before he issued it. A cleared risk stop lands his move back to its lane. The
        spec-change card's click reaches the node as his resume at the instrument."""
        for change in changes:
            if change.kind != "resume" or change.outcome is not Outcome.ACCEPTED:
                continue
            scope = str(change.args.get("scope"))
            for held in list(self.held.values()):
                waits = held.row.clears is not Clears.ITSELF
                if waits and scope in held.covers and change.issued_at_ns > held.since_ns:
                    self._resumed(held, change)

    def _resumed(self, held: Held, change: Change) -> None:
        subject = held.subject
        if subject is not None and held.event_id is not None:
            now = self.clock_ns()
            event_id = _event_id("resume", held.event_id, change.op_id)
            body = self._move(subject, event_id, "stopped", subject.lane, now, reason="his resume")
            body["by"] = {"kind": "his_click", "principal": "operator"}
            body["clears"] = held.event_id
            body["evidence_ref"] = change.op_id
            if not self._land(subject, body):
                return
        self._clear(held, "operator")

    # --- journal rows ---

    @staticmethod
    def _move(
        subject: Subject, event_id: str, start: str, end: str, now: int, *, reason: str
    ) -> dict[str, object]:
        return {
            "schema": LIFECYCLE_SCHEMA,
            "event_id": event_id,
            "unit_id": subject.unit_id,
            "version_ref": subject.version_ref,
            "compiled_fingerprint": subject.compiled_fingerprint,
            "market_id": subject.market_id,
            "from": start,
            "to": end,
            "reason": reason,
            "at": _iso(now),
        }

    def _land(self, subject: Subject, body: Mapping[str, object]) -> bool:
        writer = self._writer(subject)
        if writer is None:
            return False
        facts = RowFacts(
            ts_recv=self.clock_ns(),
            clock_ok=False,
            unit_id=subject.unit_id,
            unit_version=subject.version_ref,
            market_id=subject.market_id,
        )
        return not is_refusal(writer.append("lifecycle", body, facts))

    def _writer(self, subject: Subject) -> JournalWriter | None:
        """The node's lifecycle stream of one unit in one world: its own partition, which no
        other writer on this machine holds (the host's is role ``host``)."""
        key = (subject.unit_id, subject.world)
        found = self._lifecycle.get(key)
        if found is None:
            scope = WriterScope(
                JournalStream.UNIT, subject.unit_id, subject.world, self.machine, "node", self.build
            )
            opened = JournalWriter.open(
                self.journal_root, scope, clock=self.clock_ns, boot_epoch_id=self.boot_epoch_id
            )
            if is_refusal(opened):
                return None
            found = self._lifecycle[key] = opened.value
        return found

    def _start(self, held: Held) -> None:
        self.held[(held.kind, held.scope)] = held
        self._row("start", held, None)

    def _clear(self, held: Held, by: str) -> None:
        del self.held[(held.kind, held.scope)]
        self._row("clear", held, by)

    def _row(self, event: str, held: Held, by: str | None) -> None:
        body: dict[str, object] = {"event": event, **held.document()}
        if by is not None:
            body["cleared_by"] = by
        self.journal.append("stand_down", body, RowFacts(ts_recv=self.clock_ns(), clock_ok=False))

    def close(self) -> None:
        for writer in self._lifecycle.values():
            writer.close()
        self._lifecycle.clear()
