"""The journal envelope ``qmx.journal.envelope/1`` around every record (AD-208, Level 0 AD-27).

Every journal record is one envelope around one kind body. The writer stamps the parts it
owns (the record id, the stream and kind, the writer and its gapless sequence, the write
time, the world, the machine and the build); the caller hands it the facts of the row
(:class:`RowFacts`): when the venue and this machine saw it, whether the clock was proven,
whether it is backfilled, and which unit, market, account and run it belongs to. The unit
never stamps its own world: the writer takes it from the run or the deployment.

A record is stored as canonical JSON, which has no null: a fact that is absent is an
omitted key. Stdlib only.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

__all__ = [
    "BUNDLE_WORLDS",
    "ENVELOPE_SCHEMA",
    "HOT_PATH_WORLDS",
    "JournalStream",
    "JournalWorld",
    "Link",
    "RowFacts",
    "envelope_json",
]

ENVELOPE_SCHEMA: Final[str] = "qmx.journal.envelope/1"


class JournalWorld(StrEnum):
    """Where a record happened. Finer than the CT-13 store's own ``live`` room."""

    BACKTEST = "backtest"
    STRESS = "stress"
    PAPER = "paper"
    DEMO = "demo"
    LIVE = "live"
    SHADOW = "shadow"
    SYNTHETIC = "synthetic"


HOT_PATH_WORLDS: Final[frozenset[JournalWorld]] = frozenset(
    {JournalWorld.PAPER, JournalWorld.DEMO, JournalWorld.LIVE, JournalWorld.SHADOW}
)
"""Worlds appended in process to a CT-13 stream (its ``live`` room)."""

BUNDLE_WORLDS: Final[frozenset[JournalWorld]] = frozenset(
    {JournalWorld.BACKTEST, JournalWorld.STRESS, JournalWorld.SYNTHETIC}
)
"""Worlds that never use the hot path: QMB's bundle mode writes them."""


class JournalStream(StrEnum):
    """The four journals. Each is the store source ``journal-<stream>``."""

    UNIT = "unit"
    MARKET = "market"
    NODE = "node"
    READINGS = "readings"

    @property
    def source(self) -> str:
        return f"journal-{self.value}"


@dataclass(frozen=True, slots=True)
class Link:
    """A pointer from a record: a record id, a partition key plus seq, or a Library id."""

    rel: str
    ref: str


@dataclass(frozen=True, slots=True)
class RowFacts:
    """What the caller knows about one row; the writer stamps everything else.

    Times are epoch nanoseconds. ``clock_ok`` is false while the machine's offset is
    unproven. ``account`` names the broker, the account id and its type.
    """

    ts_recv: int
    clock_ok: bool
    ts_venue: int | None = None
    clock_offset_ns: int | None = None
    backfilled: bool = False
    unit_id: str | None = None
    unit_version: str | None = None
    market_id: str | None = None
    venue: str | None = None
    account: str | None = None
    platform: str | None = None
    run_id: str | None = None
    trace_id: str | None = None
    links: tuple[Link, ...] = ()


def envelope_json(
    facts: RowFacts,
    *,
    record_id: str,
    stream: JournalStream,
    kind: str,
    schema_version: int,
    writer_id: str,
    seq: int,
    ts_write: int,
    world: JournalWorld,
    machine: str,
    build: str,
    body: Mapping[str, object],
) -> dict[str, object]:
    """The record as one JSON object: the envelope's fields with the body under ``body``."""
    record: dict[str, object] = {
        "schema": ENVELOPE_SCHEMA,
        "record_id": record_id,
        "stream": stream.value,
        "kind": kind,
        "schema_version": schema_version,
        "writer_id": writer_id,
        "seq": seq,
        "ts_recv": facts.ts_recv,
        "ts_write": ts_write,
        "clock_ok": facts.clock_ok,
        "backfilled": facts.backfilled,
        "world": world.value,
        "machine": machine,
        "build": build,
        "links": [{"rel": link.rel, "ref": link.ref} for link in facts.links],
        "body": dict(body),
    }
    optional = {
        "ts_venue": facts.ts_venue,
        "clock_offset_ns": facts.clock_offset_ns,
        "unit_id": facts.unit_id,
        "unit_version": facts.unit_version,
        "market_id": facts.market_id,
        "venue": facts.venue,
        "account": facts.account,
        "platform": facts.platform,
        "run_id": facts.run_id,
        "trace_id": facts.trace_id,
    }
    record.update({name: value for name, value in optional.items() if value is not None})
    return record
