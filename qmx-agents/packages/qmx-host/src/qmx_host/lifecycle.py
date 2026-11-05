"""This PC's one `lifecycle` writer (Part B CONTRACTS §3, AD-208, R1-B-06, LC-B-30).

`record_move(event)` appends Part A's `qmx.lifecycle/1` move as a unit-journal `lifecycle` row,
its record id the move's `event_id`, after checking it against Part A's `fold` over every move
already in this machine's journals: a move `fold` rejects is refused with its typed reason and
nothing is written. Its callers are the verdict landing, for the judge's draft to tested or
draft to parked move, and Part C's promote action, for his clicks. The judge never moves a unit
toward paper or live: `fold` refuses that for any principal but `operator`.

One `JournalWriter` per unit holds that unit's stream (role `host`, so the node's own stream of
risk stops never shares a partition). The journal envelope has no world for a research move, so
the host's stream sits in `paper`, the lowest hot-path world; the world is a stamp, and `fold`
reads moves across every world.
"""

from __future__ import annotations

import dataclasses
import threading
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Final, cast

from qmf.core import fingerprint, is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_kinds.unit import LIFECYCLE_SCHEMA
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qmf.data.journal_writer import AppendOutcome, JournalWriter, WriterScope
from qml.lifecycle import Actor, ActorKind, Event, MarketKey, Refusal, State, fold

__all__ = ["KIND", "ROLE", "LifecycleWriter", "MoveRefused", "judge_moves"]

KIND: Final = "lifecycle"
ROLE: Final = "host"
WORLD: Final = JournalWorld.PAPER
OUTCOME_MOVES: Final[Mapping[str, State]] = {"pass": State.TESTED, "fail": State.PARKED}
"""The judge's move per market: a pass is tested, a fail is parked. Too thin, no trades and a
verdict with a step not run move nothing."""


class MoveRefused(ValueError):
    """A move `fold` rejects, with its typed reason."""

    def __init__(self, refusal: Refusal | str, message: str) -> None:
        super().__init__(message)
        self.refusal = refusal


def _body(event: Event) -> dict[str, object]:
    body: dict[str, object] = {
        "schema": LIFECYCLE_SCHEMA,
        "event_id": event.event_id,
        "unit_id": event.unit_id,
        "version_ref": event.version_ref,
        "compiled_fingerprint": event.compiled_fingerprint,
        "market_id": event.market_id,
        "from": event.from_state.value,
        "to": event.to_state.value,
        "by": {"kind": event.by.kind.value, "principal": event.by.principal},
        "reason": event.reason,
        "at": event.at.isoformat(),
    }
    if event.evidence_ref is not None:
        body["evidence_ref"] = event.evidence_ref
    if event.clears is not None:
        body["clears"] = event.clears
    return body


def _event(line: JournalLine) -> Event | None:
    """A committed `lifecycle` row as `fold` reads it; any other row is None."""
    record = line.record
    if record.get("kind") != KIND:
        return None
    body = cast(Mapping[str, object], record.get("body", {}))
    by = cast(Mapping[str, object], body["by"])
    evidence, clears = body.get("evidence_ref"), body.get("clears")
    return Event(
        event_id=str(body["event_id"]),
        unit_id=str(body["unit_id"]),
        version_ref=str(body["version_ref"]),
        compiled_fingerprint=str(body["compiled_fingerprint"]),
        market_id=str(body["market_id"]),
        from_state=State(str(body["from"])),
        to_state=State(str(body["to"])),
        by=Actor(ActorKind(str(by["kind"])), str(by["principal"])),
        reason=str(body["reason"]),
        evidence_ref=None if evidence is None else str(evidence),
        at=datetime.fromisoformat(str(body["at"])),
        writer=str(record.get("writer_id", "")),
        sequence=line.seq,
        clears=None if clears is None else str(clears),
    )


@dataclasses.dataclass
class LifecycleWriter:
    """The host's lifecycle writer over `root`, this machine's journal root."""

    root: Path
    machine: str
    build: str
    clock: Callable[[], int] = time.time_ns
    boot_epoch_id: str = dataclasses.field(default_factory=lambda: uuid.uuid4().hex[:12])
    _writers: dict[str, JournalWriter] = dataclasses.field(default_factory=dict[str, JournalWriter])
    _lock: threading.Lock = dataclasses.field(default_factory=threading.Lock)

    @property
    def writer_id(self) -> str:
        return f"{ROLE}@{self.machine}"

    def events(self, unit_id: str) -> tuple[Event, ...]:
        """Every move of `unit_id` committed under this machine's journal root, any writer."""
        found: list[Event] = []
        for folder in stream_folders(self.root):
            lines = read_committed(folder)
            if is_refusal(lines):
                raise MoveRefused("storage", f"the lifecycle journal {folder} does not read")
            for line in lines.value:
                event = _event(line) if isinstance(line, JournalLine) else None
                if event is not None and event.unit_id == unit_id:
                    found.append(event)
        return tuple(found)

    def state(self, key: MarketKey) -> State:
        return fold(self.events(key.unit_id)).state(key)

    def record_move(self, event: Event) -> str:
        """Append `event` once and answer its id. A move already written answers its id again
        and writes nothing; a move `fold` rejects is refused with its reason."""
        with self._lock:
            known = self.events(event.unit_id)
            if any(seen.event_id == event.event_id for seen in known):
                return event.event_id
            mine = [seen.sequence for seen in known if seen.writer == self.writer_id]
            stamped = dataclasses.replace(
                event, writer=self.writer_id, sequence=max(mine, default=-1) + 1
            )
            folded = fold([*known, stamped])
            for rejected in folded.rejected:
                if rejected.event.event_id == event.event_id:
                    raise MoveRefused(rejected.refusal, rejected.message)
            facts = RowFacts(
                ts_recv=self.clock(),
                clock_ok=False,
                unit_id=event.unit_id,
                unit_version=event.version_ref,
                market_id=event.market_id,
            )
            appended = self._writer(event.unit_id).append(KIND, _body(stamped), facts)
            if is_refusal(appended):
                raise MoveRefused("storage", f"the lifecycle row was not written: {appended}")
            if appended.value.outcome is AppendOutcome.DETERMINISM_BREAK:
                raise MoveRefused("determinism_break", f"{event.event_id} differs from its row")
            return event.event_id

    def record_verdict(self, moves: Sequence[Event]) -> list[str]:
        """The judge's moves of one verdict: each market still a draft moves, a move already
        written is answered again, and a market past draft is left as it is."""
        done: list[str] = []
        for move in moves:
            known = {seen.event_id for seen in self.events(move.unit_id)}
            if move.event_id in known or self.state(move.key) is State.DRAFT:
                done.append(self.record_move(move))
        return done

    def close(self) -> None:
        with self._lock:
            for writer in self._writers.values():
                writer.close()
            self._writers.clear()

    def _writer(self, unit_id: str) -> JournalWriter:
        found = self._writers.get(unit_id)
        if found is not None:
            return found
        scope = WriterScope(JournalStream.UNIT, unit_id, WORLD, self.machine, ROLE, self.build)
        opened = JournalWriter.open(
            self.root, scope, clock=self.clock, boot_epoch_id=self.boot_epoch_id
        )
        if is_refusal(opened):
            raise MoveRefused("storage", f"the lifecycle journal of {unit_id} did not open")
        self._writers[unit_id] = opened.value
        return opened.value


def judge_moves(
    verdict_id: str,
    fields: Mapping[str, object],
    *,
    unit_id: str,
    at: datetime,
) -> list[Event]:
    """The draft to tested or draft to parked move of each market the verdict passed or failed,
    by the judge with the judge run's principal. Each move is named by the verdict and market,
    so landing the verdict again names the same move."""
    moves: list[Event] = []
    for market in cast(list[Mapping[str, object]], fields.get("per_market", [])):
        to = OUTCOME_MOVES.get(str(market.get("outcome")))
        if to is None:
            continue
        name = fingerprint({"verdict": verdict_id, "market": str(market["market"]), "to": to.value})
        if is_refusal(name):
            continue
        moves.append(
            Event(
                event_id=f"lifecycle-{name.value.digest[:24]}",
                unit_id=unit_id,
                version_ref=str(fields["unit"]),
                compiled_fingerprint=str(fields.get("compiled_fp", "")),
                market_id=str(market["market"]),
                from_state=State.DRAFT,
                to_state=to,
                by=Actor(ActorKind.JUDGE, str(fields.get("principal", "judge"))),
                reason=f"the judge's verdict: {market.get('outcome')} by the "
                f"{fields.get('preset')} preset",
                evidence_ref=verdict_id,
                at=at,
                writer="",
                sequence=0,
            )
        )
    return moves
