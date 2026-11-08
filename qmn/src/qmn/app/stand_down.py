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
from typing import Final, cast

from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_kinds.unit import LIFECYCLE_SCHEMA
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
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
    "held_from_start",
    "held_from_stop",
    "restored",
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

    def document(self) -> dict[str, Json]:
        return {
            "deployment_id": self.deployment_id,
            "unit_id": self.unit_id,
            "version_ref": self.version_ref,
            "compiled_fingerprint": self.compiled_fingerprint,
            "market_id": self.market_id,
            "lane": self.lane,
            "world": self.world.value,
        }


@dataclass(frozen=True, slots=True)
class Held:
    """One stand-down in force at one scope.

    ``covers`` are the scopes his resume clears it from; ``healthy_since_ns`` is when a row
    that clears itself last saw its cause gone. A risk stop carries its subject and the
    ``event_id`` of its ``lifecycle`` row once that row landed; until then ``pending`` holds
    the row still to land."""

    kind: Kind
    scope: str
    since_ns: int
    cause: str
    covers: frozenset[str] = frozenset({"all"})
    healthy_since_ns: int | None = None
    subject: Subject | None = None
    event_id: str | None = None
    pending: Mapping[str, object] | None = None

    @property
    def row(self) -> Row:
        return TABLE[self.kind]

    @property
    def waits(self) -> bool:
        """Whether only he clears it: a restart must never let it go."""
        return self.row.clears is not Clears.ITSELF

    def document(self) -> dict[str, Json]:
        shown: dict[str, Json] = {
            "stand_down": self.kind.value,
            "scope": self.scope,
            "word": self.row.word.value,
            "cause": self.cause,
            "clears": self.row.clears.value,
            "since_ns": self.since_ns,
        }
        if self.event_id is not None:
            shown["lifecycle_event"] = self.event_id
        return shown

    def record(self) -> dict[str, object]:
        """What its ``stand_down`` start row carries, so a restart rebuilds it from the node
        journal alone: its scopes, its subject, and a risk stop's ``lifecycle`` row still to
        land."""
        kept: dict[str, object] = {**self.document(), "covers": sorted(self.covers)}
        if self.subject is not None:
            kept["subject"] = self.subject.document()
        if self.pending is not None:
            kept["pending"] = dict(self.pending)
        return kept


def _subject(found: Mapping[str, object], lane: str, world: str) -> Subject:
    return Subject(
        str(found["deployment_id"]),
        str(found["unit_id"]),
        str(found["version_ref"]),
        str(found["compiled_fingerprint"]),
        str(found["market_id"]),
        lane,
        JournalWorld(world),
    )


def held_from_start(body: Mapping[str, object], written_ns: int) -> Held:
    """The stand-down a ``stand_down`` start row records (:meth:`Held.record`). A row written
    before C-13 names no scopes, and is cleared from ``all`` and its own scope, as
    :meth:`StandDowns.hold` holds it."""
    found = body.get("subject")
    subject = None
    if isinstance(found, Mapping):
        named = cast("Mapping[str, object]", found)
        subject = _subject(named, str(named["lane"]), str(named["world"]))
    pending = body.get("pending")
    scope = str(body["scope"])
    since = body.get("since_ns")
    covers = body.get("covers")
    return Held(
        Kind(str(body["stand_down"])),
        scope,
        since if isinstance(since, int) else written_ns,
        str(body["cause"]),
        frozenset(str(s) for s in cast("list[object]", covers))
        if isinstance(covers, list)
        else frozenset({"all", scope}),
        subject=subject,
        event_id=None if body.get("lifecycle_event") is None else str(body["lifecycle_event"]),
        pending=cast("Mapping[str, object]", pending) if isinstance(pending, Mapping) else None,
    )


def held_from_stop(body: Mapping[str, object], world: str, written_ns: int) -> Held:
    """The risk stop a ``lifecycle`` row by ``risk_rule`` records, as :meth:`StandDowns.risk_stop`
    wrote it. A row that does not name its deployment holds every entry on the node until his
    resume at ``all``, the safe side of not knowing its scope."""
    rule = str(cast("Mapping[str, object]", body["by"])["principal"])
    cause = f"{rule}: {body.get('reason')}"
    if "deployment_id" not in body:
        return Held(Kind.RISK_STOP, "all", written_ns, cause, event_id=str(body["event_id"]))
    subject = _subject(body, str(body["from"]), world)
    return Held(
        Kind.RISK_STOP,
        f"unit:{subject.deployment_id}:{subject.market_id}",
        cast("int", body["since_ns"]),
        cause,
        frozenset(str(scope) for scope in cast("list[object]", body["covers"])),
        subject=subject,
        event_id=str(body["event_id"]),
    )


def _rows(root: Path, stream: JournalStream, kind: str) -> Result[list[JournalLine]]:
    """Every committed row of one kind in the writer root, folder by folder."""
    found: list[JournalLine] = []
    for folder in stream_folders(root):
        if not folder.name.startswith(f"{stream.source}.{kind}."):
            continue
        lines = read_committed(folder)
        if is_refusal(lines):
            return lines
        found.extend(line for line in lines.value if isinstance(line, JournalLine))
    return Ok(found)


def restored(root: Path) -> Result[list[Held]]:
    """The stand-downs waiting for him when the node last stopped, rebuilt from its journals.

    A risk stop whose ``lifecycle`` row landed is held until a later row ``clears`` it, which
    his resume lands; that row is what the PC reads too. A stop whose row names no deployment
    (written before C-13) gets no such row, so the node journal's ``clear`` row of the same
    stop clears it. Every other stand-down that waits for him, and a risk stop whose
    ``lifecycle`` row never landed, is held from its node-journal ``stand_down`` start row until
    a ``clear`` row for its scope follows. A read the volume refuses, or a row it cannot
    parse, is answered as a refusal, never as "nothing held"."""
    stops = _rows(root, JournalStream.UNIT, "lifecycle")
    if is_refusal(stops):
        return stops
    rows = _rows(root, JournalStream.NODE, "stand_down")
    if is_refusal(rows):
        return rows
    try:
        return Ok(_waiting(stops.value, rows.value))
    except (KeyError, TypeError, ValueError) as error:
        return TypedRefusal(
            category=RefusalCategory.INVALID_INPUT,
            retryability=Retryability.NO,
            context={"field": "stand_down", "reason": f"a stop row does not parse: {error!r}"},
        )


def _waiting(stops: Sequence[JournalLine], rows: Sequence[JournalLine]) -> list[Held]:
    landed: dict[str, Held] = {}
    cleared: set[str] = set()
    for line in stops:
        body = cast("Mapping[str, object]", line.record.get("body", {}))
        by = body.get("by")
        if isinstance(body.get("clears"), str):
            cleared.add(str(body["clears"]))
        elif (
            isinstance(by, Mapping) and cast("Mapping[str, object]", by).get("kind") == "risk_rule"
        ):
            world = str(line.record["world"])
            landed[str(body["event_id"])] = held_from_stop(body, world, line.t)
    waiting: dict[tuple[Kind, str], Held] = {}
    ended: set[tuple[Kind, str, object]] = set()
    for line in rows:
        body = cast("Mapping[str, object]", line.record.get("body", {}))
        key = (Kind(str(body["stand_down"])), str(body["scope"]))
        if body.get("event") == "clear":
            waiting.pop(key, None)
            ended.add((*key, body.get("since_ns")))
        elif body.get("event") == "start" and TABLE[key[0]].clears is not Clears.ITSELF:
            waiting[key] = held_from_start(body, line.t)
    held = {key: found for key, found in waiting.items() if _unlanded(found, landed)}
    for event_id, stop in landed.items():
        if event_id not in cleared and (stop.kind, stop.scope, stop.since_ns) not in ended:
            held[(stop.kind, stop.scope)] = stop
    return list(held.values())


def _unlanded(held: Held, landed: Mapping[str, Held]) -> bool:
    """A start row decides only for a stop whose ``lifecycle`` row never landed."""
    pending = held.pending
    return pending is None or str(pending.get("event_id")) not in landed


def _iso(at_ns: int) -> str:
    return datetime.fromtimestamp(at_ns / 1e9, UTC).isoformat()


def _reading(cause: bool, healthy: bool) -> bool | None:
    """True past a row's entry band, False inside its healthy band, None between the two."""
    return True if cause else (False if healthy else None)


def _event_id(*parts: str) -> str:
    digest = hashlib.sha256("/".join(parts).encode("utf-8")).hexdigest()
    return f"lifecycle-{digest[:24]}"


class StandDowns:
    """The stand-downs this node holds, journalled as they start and clear.

    ``free_bytes`` and ``clock_offset_ns`` are the node's probes: the volume's free space and
    the clock's offset from its time source, None while no probe has read one. ``on_alarm``
    takes the alarm a risk stop raises when its ``lifecycle`` row cannot be written.
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
        on_alarm: Callable[[Mapping[str, object]], None],
        clock_offset_ns: Callable[[], int | None] = lambda: None,
    ) -> None:
        self.journal = journal
        self.journal_root = journal_root
        self.machine = machine
        self.build = build
        self.boot_epoch_id = boot_epoch_id
        self.clock_ns = clock_ns
        self.free_bytes = free_bytes
        self.on_alarm = on_alarm
        self.clock_offset_ns = clock_offset_ns
        self.held: dict[tuple[Kind, str], Held] = {}
        self._lifecycle: dict[tuple[str, JournalWorld], JournalWriter] = {}
        self._unrecorded: set[tuple[Kind, str]] = set()
        """Stand-downs whose start row did not land in the node journal."""

    # --- what stops entries ---

    def blocking(self, scopes: Iterable[str]) -> Held | None:
        """The first stand-down in force at any of ``scopes``, or None."""
        wanted = set(scopes)
        return next((held for held in self.held.values() if held.scope in wanted), None)

    def document(self) -> list[dict[str, Json]]:
        return [held.document() for held in self.held.values()]

    def in_memory_only(self) -> list[Held]:
        """The stand-downs waiting for him that no journal holds yet, so a process restart
        would lose them: neither their start row nor a risk stop's ``lifecycle`` row landed."""
        return [
            held
            for key, held in self.held.items()
            if held.waits and key in self._unrecorded and held.event_id is None
        ]

    def adopt(self, restored: Iterable[Held]) -> None:
        """Hold what a restart rebuilt from the journals, writing no row: each started before."""
        for held in restored:
            self.held.setdefault((held.kind, held.scope), held)

    # --- the rows that clear by themselves ---

    def watch_node(self) -> None:
        """The clock band and the disk guard, node-wide."""
        now = self.clock_ns()
        offset = self.clock_offset_ns()
        if offset is not None:
            band = _reading(abs(offset) > CLOCK_NO_NEW_ENTRIES_NS, abs(offset) <= CLOCK_WARN_NS)
            self._observe(Kind.CLOCK_BAND, "all", band, now, f"clock offset {offset} ns")
        free = self.free_bytes()
        low = _reading(free < DISK_GUARD_BYTES, free > DISK_GUARD_BYTES + DISK_MARGIN_BYTES)
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
        stop holds lands nothing. The hold starts even when the row cannot be written, with
        the ``risk_stop_unrecorded`` alarm, and :meth:`settle` lands the row on a later tick.
        Answers the stop's event id, or None when its row did not land."""
        scope = f"unit:{subject.deployment_id}:{subject.market_id}"
        held = self.held.get((Kind.RISK_STOP, scope))
        if held is not None:
            return held.event_id
        now = self.clock_ns()
        event_id = _event_id("risk_stop", subject.deployment_id, subject.market_id, rule, str(now))
        scopes = frozenset({"all", *covers})
        body = self._move(subject, event_id, subject.lane, "stopped", now, reason=reason)
        body.update(
            by={"kind": "risk_rule", "principal": rule}, covers=sorted(scopes), since_ns=now
        )
        # The hold and its node-journal row come before the lifecycle row, so a crash while
        # that row is written leaves the stop on the volume for the restart to rebuild.
        self._start(
            Held(
                Kind.RISK_STOP,
                scope,
                now,
                f"{rule}: {reason}",
                scopes,
                subject=subject,
                pending=body,
            )
        )
        if not self._settle((Kind.RISK_STOP, scope)):
            self.on_alarm(
                {
                    "alarm": "risk_stop_unrecorded",
                    "deployment_id": subject.deployment_id,
                    "market_id": subject.market_id,
                    "rule": rule,
                    "action": "no_new_entries",
                    "why": "the stop's lifecycle row could not be written, so only the node shows"
                    " it",
                }
            )
            return None
        return event_id

    def settle(self) -> None:
        """Land each held risk stop's ``lifecycle`` row that has not landed yet."""
        for key, held in list(self.held.items()):
            if held.pending is not None:
                self._settle(key)

    def _settle(self, key: tuple[Kind, str]) -> bool:
        held = self.held[key]
        if held.pending is None or held.subject is None:
            return True
        if not self._land(held.subject, held.pending):
            return False
        self.held[key] = replace(held, event_id=str(held.pending["event_id"]), pending=None)
        return True

    def resumes(self, changes: Sequence[Change]) -> None:
        """His ``resume`` clears each stand-down waiting for him that it covers and that
        started before he issued it and before it reached the node, since ``issued_at`` may
        run ahead of the node's clock. A cleared risk stop lands his move back to its lane. The
        spec-change card's click reaches the node as his resume at the instrument."""
        for change in changes:
            if change.kind != "resume" or change.outcome is not Outcome.ACCEPTED:
                continue
            scope = str(change.args.get("scope"))
            for held in list(self.held.values()):
                waits = held.row.clears is not Clears.ITSELF
                after = min(change.issued_at_ns, change.arrived_at_ns) > held.since_ns
                if waits and scope in held.covers and after:
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
            "deployment_id": subject.deployment_id,
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
        """The node's lifecycle stream of one unit in one world. The unit's run journal opens
        the same scope for its other kinds, so both writers are ``node@<machine>`` with their
        own sequence counters; each kind is its own series, so neither holds the other's
        partition. The host's lifecycle stream is role ``host``."""
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
        key = (held.kind, held.scope)
        self.held[key] = held
        if not self._row({"event": "start", **held.record()}):
            self._unrecorded.add(key)

    def _clear(self, held: Held, by: str) -> None:
        key = (held.kind, held.scope)
        del self.held[key]
        self._unrecorded.discard(key)
        self._row({"event": "clear", **held.document(), "cleared_by": by})

    def _row(self, body: Mapping[str, object]) -> bool:
        facts = RowFacts(ts_recv=self.clock_ns(), clock_ok=False)
        return not is_refusal(self.journal.append("stand_down", body, facts))

    def close(self) -> None:
        for writer in self._lifecycle.values():
            writer.close()
        self._lifecycle.clear()
