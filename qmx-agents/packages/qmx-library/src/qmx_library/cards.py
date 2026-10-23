"""The dataset card writer: one card per series, and the claim on its key (DATA-PLAN DR3A).

A price series is one item in the Library and one ``dataset`` card, named for its series key
(``source/subject/kind/variant``) so two writers cannot both land a card for the same series:
the item id is derived from the key, and each write is a compare-and-swap on that item's
``main`` head. The next write of the same fields produces the same object and moves nothing;
a month that froze or a correction that landed produces a new version whose fields carry the
partition list and the correction ranges.

The fields a card carries are the ones the plan's card shows and the marks rule reads: the
series key, the licence, the world, whether the series can be downloaded again, what it
replaced, the quality note, the coverage strip, every frozen partition with its fingerprint
and row count, and each correction with the range it covers. A consumer records a read with
:func:`read_range` in its own fields; a correction marks it only when the two ranges overlap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from qmx_library.port import Draft, JsonObject, ObjectId
from qmx_library.principal import Principal
from qmx_library.store import Store

__all__ = [
    "SERIES_PREFIX",
    "CardReceipt",
    "Correction",
    "Partition",
    "SeriesCard",
    "card_fields",
    "read_range",
    "series_of",
    "write_card",
]

SERIES_PREFIX: Final = "dataset:"
"""The item prefix a series card is named with; the rest of the item is its series key."""


def series_of(item: str) -> str:
    """The series key a card item names, empty when the item is not a series card."""
    return item[len(SERIES_PREFIX) :] if item.startswith(SERIES_PREFIX) else ""


def read_range(series: str, start_ns: int, end_ns: int) -> JsonObject:
    """A range a consumer read, for the ``reads`` list in its own fields.

    A correction marks the consumer only when the two ranges share a moment, so what a
    result records here is what decides whether a later fill touches it.
    """
    return {"series": series, "start_ns": start_ns, "end_ns": end_ns}


@dataclass(frozen=True, slots=True)
class Partition:
    """One month of a series, as the card lists it."""

    year: int
    month: int
    fingerprint: str
    rows: int
    frozen: bool
    gaps: tuple[str, ...] = ()

    @property
    def month_text(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    def as_json(self) -> JsonObject:
        return {
            "month": self.month_text,
            "fingerprint": self.fingerprint,
            "rows": self.rows,
            "frozen": self.frozen,
            "gaps": list(self.gaps),
        }


@dataclass(frozen=True, slots=True)
class Correction:
    """One correction the card records, with the range it covers."""

    start_ns: int
    end_ns: int
    old: str
    new: str
    reason: str
    at: str

    def as_json(self) -> JsonObject:
        return {
            "start_ns": self.start_ns,
            "end_ns": self.end_ns,
            "old": self.old,
            "new": self.new,
            "reason": self.reason,
            "at": self.at,
        }


@dataclass(frozen=True, slots=True)
class SeriesCard:
    """What a card says about a series beyond its partitions."""

    source: str
    subject: str
    kind: str
    variant: str = ""
    licence: str = ""
    world: str = "live"
    redownloadable: bool = False
    replaced: str = ""
    quality: dict[str, object] = field(default_factory=dict[str, object])

    @property
    def series(self) -> str:
        """The series key, the same text the partitions are stored under."""
        return f"{self.source}/{self.subject}/{self.kind}/{self.variant or '-'}"

    @property
    def item(self) -> str:
        """The Library item that claims the series key."""
        return f"{SERIES_PREFIX}{self.series}"

    @property
    def title(self) -> str:
        variant = f" {self.variant}" if self.variant else ""
        return f"{self.subject} {self.kind}{variant}"


@dataclass(frozen=True, slots=True)
class CardReceipt:
    """What one card write landed, and the head it replaced."""

    item: str
    object_id: ObjectId
    previous: ObjectId | None
    series: str

    @property
    def created(self) -> bool:
        """True when the item had no card before this write."""
        return self.previous is None

    @property
    def claimed(self) -> bool:
        """True when this write is now the head that holds the series key."""
        return self.previous != self.object_id


def card_fields(
    card: SeriesCard,
    partitions: tuple[Partition, ...] = (),
    corrections: tuple[Correction, ...] = (),
) -> JsonObject:
    """The fields a ``dataset`` card carries for a series (the dataset schema accepts them)."""
    months = sorted(partitions, key=lambda part: (part.year, part.month))
    rows = sum(part.rows for part in months)
    coverage: JsonObject = {
        "months": len(months),
        "rows": rows,
        "frozen": sum(1 for part in months if part.frozen),
        "first": months[0].month_text if months else "",
        "last": months[-1].month_text if months else "",
    }
    fields: JsonObject = {
        "source": card.source,
        "subject": card.subject,
        "kind": card.kind,
        "variant": card.variant,
        "series_key": card.series,
        "instruments": [card.subject],
        "world": card.world,
        "licence": card.licence,
        "redownloadable": card.redownloadable,
        "replaced": card.replaced,
        "quality": dict(card.quality),
        "coverage": coverage,
        "partitions": [part.as_json() for part in months],
        "corrections": [correction.as_json() for correction in corrections],
        "partition_digests": [part.fingerprint for part in months],
    }
    if months:
        fields["window"] = {"first": months[0].month_text, "last": months[-1].month_text}
    return fields


def write_card(
    store: Store,
    who: Principal,
    card: SeriesCard,
    partitions: tuple[Partition, ...] = (),
    corrections: tuple[Correction, ...] = (),
    *,
    summary: str = "",
) -> CardReceipt:
    """Write the series card, claiming its key; a moved head is a ``stale_head`` refusal."""
    fields = card_fields(card, partitions, corrections)
    head = store.head(card.item, "main")
    expected = None if head is None else head[0]
    if expected is not None and dict(store.get(who, expected).fields) == fields:
        return CardReceipt(
            item=card.item, object_id=expected, previous=expected, series=card.series
        )
    draft = Draft("dataset", card.item, card.title, summary, fields)
    commit = store.put(who, draft, on="main", expected_head=expected)
    return CardReceipt(
        item=card.item, object_id=commit.object_id, previous=expected, series=card.series
    )
