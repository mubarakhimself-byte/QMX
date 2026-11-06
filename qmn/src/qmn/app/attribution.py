"""Whose is each position and order on an account (Level 0 AD-8, Part C NODE.md section 8).

Every order the node sends carries its tag twice: in the client order id, ``q<tag>-<ULID>``,
and in cTrader's ``label``, ``qmx:<tag>:<unit tag>``. The venue keeps the label on the position
and the client order id on the order, so a position is read through the order that opened it.

Each record on the account gets one :class:`Claim`:

- ``mine``: it carries only this node's tag, and the node's own journal holds the order's send.
- ``twin``: it carries this node's tag, and the journal does not hold that send. Another process
  with this node's identity is trading the account (a copied volume, TN-04), so the account
  stands down.
- ``foreign``: it carries another node's tag. One node trades an account (AD-8), so the account
  stands down; the record itself is never touched.
- ``untagged``: it carries no node's tag, such as his own trade. It is never touched and never
  adopted, and the node shows it as "not ours, never touched", adding "no stop at the broker"
  when the venue holds none.

Nothing here reads a venue or a journal; :mod:`qmn.app.reconciler` does both.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Final

__all__ = [
    "NOT_OURS",
    "Attributed",
    "Attribution",
    "Claim",
    "OrderState",
    "ReadBack",
    "VenueOrder",
    "VenuePosition",
    "attribute",
    "tags_of",
]

NOT_OURS: Final = "not ours, never touched"
"""What the node shows beside a position that is not its own."""
_LABEL: Final = re.compile(r"qmx:([a-z2-7]{8}):.+")
_CLIENT_ORDER_ID: Final = re.compile(r"q([a-z2-7]{8})-[0-9A-HJKMNP-TV-Z]{26}")


class Claim(StrEnum):
    MINE = "mine"
    TWIN = "twin"
    FOREIGN = "foreign"
    UNTAGGED = "untagged"


class OrderState(StrEnum):
    OPEN = "open"
    FILLED = "filled"
    GONE = "gone"
    """Rejected, cancelled or expired: the venue holds nothing from it."""


@dataclass(frozen=True, slots=True)
class VenueOrder:
    """One order as the venue reads it back: open, or recently done within its lookback."""

    client_order_id: str | None
    label: str | None
    market_id: str
    state: OrderState
    position: str | None = None
    """The position the order opened, once it filled."""
    price: Decimal | None = None
    """The venue's fill price, once it filled."""


@dataclass(frozen=True, slots=True)
class VenuePosition:
    """One open position as the venue reads it back. A position carries its label, never a
    client order id (``ProtoOAPosition`` has none)."""

    position: str
    label: str | None
    market_id: str
    side: str
    quantity: Decimal
    entry_price: Decimal
    stop: Decimal | None


@dataclass(frozen=True, slots=True)
class ReadBack:
    """Everything the venue holds on one account at one read."""

    orders: tuple[VenueOrder, ...]
    positions: tuple[VenuePosition, ...]


@dataclass(frozen=True, slots=True)
class Attributed:
    claim: Claim
    tags: tuple[str, ...]
    """Every node tag the record carries, sorted."""
    client_order_id: str | None


@dataclass(frozen=True, slots=True)
class Attribution:
    """Each position and order on one account, with its claim."""

    positions: tuple[tuple[VenuePosition, Attributed], ...]
    orders: tuple[tuple[VenueOrder, Attributed], ...]

    def claimed(self, claim: Claim) -> tuple[tuple[str, Attributed], ...]:
        """Each position and order named by ``claim``: a position by its venue name, an order
        by its client order id."""
        named = [(p.position, a) for p, a in self.positions if a.claim is claim]
        named += [(o.client_order_id or "", a) for o, a in self.orders if a.claim is claim]
        return tuple(named)

    @property
    def stand_down(self) -> Claim | None:
        """Why the account takes no new entry: a twin first, then a foreign node."""
        for claim in (Claim.TWIN, Claim.FOREIGN):
            if self.claimed(claim):
                return claim
        return None


def tags_of(label: str | None, client_order_id: str | None) -> tuple[str, ...]:
    """Every node tag in a label and a client order id, sorted and without repeats."""
    found = {
        match.group(1)
        for pattern, text in ((_LABEL, label), (_CLIENT_ORDER_ID, client_order_id))
        if text is not None and (match := pattern.fullmatch(text)) is not None
    }
    return tuple(sorted(found))


def _claim(
    tags: tuple[str, ...], client_order_id: str | None, tag: str, sent: Iterable[str]
) -> Claim:
    if not tags:
        return Claim.UNTAGGED
    if tag not in tags:
        return Claim.FOREIGN
    if tags == (tag,) and client_order_id is not None and client_order_id in sent:
        return Claim.MINE
    return Claim.TWIN


def attribute(read: ReadBack, *, tag: str, sent: Iterable[str]) -> Attribution:
    """Each record's claim. ``sent`` is every client order id the node's journal holds a send
    for. A position whose opening order the venue no longer lists is read by its label alone,
    so one with this node's tag and no send to prove it is a twin."""
    held = frozenset(sent)
    opened_by: Mapping[str, VenueOrder] = {
        order.position: order for order in read.orders if order.position is not None
    }
    positions: list[tuple[VenuePosition, Attributed]] = []
    for position in read.positions:
        order = opened_by.get(position.position)
        coid = None if order is None else order.client_order_id
        tags = tuple(
            sorted(
                {
                    *tags_of(position.label, None),
                    *(() if order is None else tags_of(order.label, coid)),
                }
            )
        )
        positions.append((position, Attributed(_claim(tags, coid, tag, held), tags, coid)))
    orders: list[tuple[VenueOrder, Attributed]] = []
    for order in read.orders:
        tags = tags_of(order.label, order.client_order_id)
        claim = _claim(tags, order.client_order_id, tag, held)
        orders.append((order, Attributed(claim, tags, order.client_order_id)))
    return Attribution(tuple(positions), tuple(orders))
