"""Reconcile each account with its venue, the venue winning (Level 0 AD-8, AD-38; Part C TN-01).

The runtime calls :meth:`Reconciler.run` for an account whenever :meth:`Reconciler.due` says so:
once per venue session, so at start and after every reconnect, and again when an order's
outcome turned UNKNOWN. Until the run for the current session has happened, :meth:`holds`
keeps every new entry on the account back.

One run reads everything the venue holds on the account, the open and recently done orders by
client order id and the positions by their label, and attributes each record
(:mod:`qmn.app.attribution`) against the sends the node's own journal holds. Then:

- each UNKNOWN outcome resolves from what the venue shows: the order filled, so its unit books
  the fill at the venue's price and quantity, or the venue holds nothing from it, so the entry
  is dropped. Nothing is ever sent again on an UNKNOWN; an order the venue still shows open
  stays UNKNOWN. A venue that lists no filled order, as cTrader's reconcile lists pending ones
  only, still shows the position: one open position with the order's label, market and side
  that no other order opened is the order's, under the venue's name. The order reads absent
  only when no such position is open, and two of them keep it UNKNOWN with an alarm.
- a twin or a foreign node's record stands the account down: no new entry, with an alarm.
- a position that is not the node's is never touched and never adopted. It is shown as
  "not ours, protected", and an untagged one raises the ``not_ours`` alarm once.
- one ``reconcile`` row records the run, with the node's price and stop distance beside the
  venue's fill price and stop for each of the node's positions (C-12a low L6).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Protocol, cast

from qmf.core import Ok, Result, is_refusal
from qmf.data.journal_envelope import JournalStream, RowFacts
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qmf.data.journal_writer import JournalWriter

from qmn.app.attribution import (
    NOT_OURS,
    Attributed,
    Attribution,
    Claim,
    OrderState,
    ReadBack,
    VenueOrder,
    VenuePosition,
    attribute,
)

__all__ = ["Found", "Ours", "ReadsBack", "Reconciler", "Resolves", "journal_sends"]

_STAND_DOWN = {
    Claim.TWIN: "the node cannot prove the account is its own: a twin with its tag trades it",
    Claim.FOREIGN: "the node cannot prove the account is its own: another node's tag is on it",
}


class ReadsBack(Protocol):
    def read_back(self) -> Result[ReadBack]:
        """Every order and position the venue holds on the account."""
        ...


@dataclass(frozen=True, slots=True)
class Found:
    """Where an UNKNOWN entry went at the venue: the position it opened, by the venue's name,
    and the venue's fill price."""

    position: str
    price: Decimal
    quantity: Decimal | None
    """What the venue holds in the position; None when it closed before the read."""


class Resolves(Protocol):
    """A hosted unit, which may hold an order whose outcome is UNKNOWN."""

    def resolve(self, client_order_id: str, found: Found | None, *, protected: bool) -> bool:
        """Settle the order: filled into ``found``, or never taken when ``found`` is None.
        Answers False when the order is not this unit's."""
        ...


def journal_sends(root: Path) -> Result[dict[str, Mapping[str, object]]]:
    """Every entry send the node journal holds, by client order id. The journal is written
    before an order is dispatched, so an order this node sent is here even after a restart."""
    prefix = f"{JournalStream.NODE.source}."
    sends: dict[str, Mapping[str, object]] = {}
    for folder in stream_folders(root):
        if not folder.name.startswith(prefix):
            continue
        lines = read_committed(folder)
        if is_refusal(lines):
            return lines
        for line in lines.value:
            if not isinstance(line, JournalLine) or line.record.get("kind") != "order":
                continue
            body = cast("Mapping[str, object]", line.record.get("body", {}))
            if body.get("step") == "send":
                sends[str(body["client_order_id"])] = body
    return Ok(sends)


@dataclass(frozen=True, slots=True)
class Ours:
    """A position the venue holds that this node sent, with the node journal's send row."""

    position: VenuePosition
    send: Mapping[str, object]


@dataclass
class _Account:
    session: int | None = None
    """The venue session the last run happened in."""
    tried: frozenset[str] = frozenset()
    """The UNKNOWN orders the last run saw."""
    stand_down: Claim | None = None
    not_ours: tuple[dict[str, object], ...] = ()
    mine: tuple[Ours, ...] = ()
    """The node's own positions the last run read at the venue."""


@dataclass
class Reconciler:
    journal: JournalWriter
    journal_root: Path
    tag: str
    clock_ns: Callable[[], int]
    on_alarm: Callable[[Mapping[str, object]], None]
    _accounts: dict[str, _Account] = field(default_factory=dict[str, _Account])
    _raised: set[tuple[str, ...]] = field(default_factory=set[tuple[str, ...]])

    def _of(self, account: str) -> _Account:
        return self._accounts.setdefault(account, _Account())

    def due(self, account: str, session: int, unknown: Mapping[str, str]) -> bool:
        """A run is due once per venue session, and when an UNKNOWN appeared since the last."""
        held = self._of(account)
        return held.session != session or not set(unknown) <= held.tried

    def holds(self, account: str, session: int) -> str | None:
        """Why no new entry may go on the account now, or None."""
        held = self._of(account)
        if held.session != session:
            return "the node cannot prove what the venue holds until it reconciles"
        return None if held.stand_down is None else _STAND_DOWN[held.stand_down]

    def mine(self, account: str) -> tuple[Ours, ...]:
        """The node's own positions the last run of ``account`` read, open at that time."""
        return self._of(account).mine

    def shown(self) -> list[dict[str, object]]:
        """Every position on the node's accounts that is not the node's."""
        return [row for held in self._accounts.values() for row in held.not_ours]

    def run(
        self,
        account: str,
        session: int,
        client: ReadsBack,
        unknown: Mapping[str, str],
        units: Sequence[Resolves],
    ) -> None:
        """One reconcile of ``account``. A read the venue or the journal refuses changes
        nothing, so the account stays held back and the next tick runs it again."""
        read = client.read_back()
        sends = journal_sends(self.journal_root)
        if is_refusal(read) or is_refusal(sends):
            return
        held = self._of(account)
        why = (
            "start"
            if held.session is None
            else "reconnect"
            if held.session != session
            else "unknown"
        )
        labelled, twice = _by_label(read.value, unknown, sends.value)
        venue = ReadBack(
            tuple(o for o in read.value.orders if o.client_order_id not in labelled)
            + tuple(labelled.values()),
            read.value.positions,
        )
        found = attribute(venue, tag=self.tag, sent=sends.value)
        resolved = [
            self._resolve(name, venue, sends.value, units, twice.get(name, ()))
            for name in sorted(unknown)
        ]
        held.session, held.tried = session, frozenset(unknown)
        held.stand_down = found.stand_down
        held.not_ours = tuple(
            _shown(account, position, claimed)
            for position, claimed in found.positions
            if claimed.claim is not Claim.MINE
        )
        held.mine = tuple(
            Ours(position, sends.value[claimed.client_order_id])
            for position, claimed in found.positions
            if claimed.claim is Claim.MINE and claimed.client_order_id in sends.value
        )
        self._alarms(account, found)
        body: dict[str, object] = {
            "account": account,
            "why": why,
            "session": session,
            "positions": [
                _position_row(position, claimed, sends.value)
                for position, claimed in found.positions
            ],
            "orders": [
                {
                    "client_order_id": order.client_order_id,
                    "claim": claimed.claim.value,
                    "state": order.state.value,
                    "tags": list(claimed.tags),
                }
                for order, claimed in found.orders
                if claimed.claim is not Claim.MINE
            ],
            "resolved": [row for row in resolved if row is not None],
            "stand_down": None if found.stand_down is None else found.stand_down.value,
        }
        self.journal.append(
            "reconcile",
            cast("dict[str, object]", _without_none(body)),
            RowFacts(ts_recv=self.clock_ns(), clock_ok=False),
        )

    def _resolve(
        self,
        name: str,
        read: ReadBack,
        sends: Mapping[str, Mapping[str, object]],
        units: Sequence[Resolves],
        twice: tuple[str, ...],
    ) -> dict[str, object] | None:
        if twice:
            self._raise(
                ("label_twice", name),
                {
                    "alarm": "label_twice",
                    "client_order_id": name,
                    "positions": list(twice),
                    "action": "no_new_entries",
                    "why": "more than one open position carries the label of an order whose"
                    " answer was lost, so the node cannot tell which one it opened",
                },
            )
            return None
        order = next((o for o in read.orders if o.client_order_id == name), None)
        if order is not None and order.state is OrderState.OPEN:
            return None
        position = next(
            (p for p in read.positions if order is not None and p.position == order.position), None
        )
        found = _found(order, position)
        protected = position is None or position.stop is not None
        if not any(unit.resolve(name, found, protected=protected) for unit in units):
            return None
        if not protected and position is not None:
            self._raise(
                ("unprotected", name),
                {
                    "alarm": "protection_escalation",
                    "position": position.position,
                    "market_id": position.market_id,
                    "action": "closing_reduce_only",
                    "why": "the venue holds no stop on an order whose answer was lost",
                    "origin": "placeholder",
                },
            )
        if found is None:
            return {"client_order_id": name, "outcome": "absent"}
        row: dict[str, object] = {
            "client_order_id": name,
            "outcome": "filled",
            "price": str(found.price),
        }
        if found.position != name:
            row["position"] = found.position
        sent = sends.get(name, {}).get("quantity")
        if found.quantity is not None and sent is not None and found.quantity != Decimal(str(sent)):
            row["quantity"] = str(found.quantity)
        return row

    def _alarms(self, account: str, found: Attribution) -> None:
        for claim, alarm in ((Claim.TWIN, "twin"), (Claim.FOREIGN, "foreign_claimant")):
            named = found.claimed(claim)
            if named:
                records = sorted({name for name, _ in named})
                self._raise(
                    (alarm, account, *records),
                    {
                        "alarm": alarm,
                        "account": account,
                        "records": records,
                        "tags": sorted({t for _, a in named for t in a.tags}),
                        "action": "no_new_entries",
                    },
                )
        for position, claimed in found.positions:
            if claimed.claim is Claim.UNTAGGED:
                self._raise(
                    ("not_ours", account, position.position),
                    {
                        "alarm": "not_ours",
                        "account": account,
                        "position": position.position,
                        "market_id": position.market_id,
                        "shown": NOT_OURS,
                    },
                )

    def _raise(self, key: tuple[str, ...], alarm: Mapping[str, object]) -> None:
        if key not in self._raised:
            self._raised.add(key)
            self.on_alarm(alarm)


def _found(order: VenueOrder | None, position: VenuePosition | None) -> Found | None:
    """Where a filled order went: its position at the venue's fill price, the order's own price
    when it carries one. None when the venue holds nothing from it."""
    if order is None or order.state is not OrderState.FILLED:
        return None
    if position is not None:
        price = position.entry_price if order.price is None else order.price
        return Found(position.position, price, position.quantity)
    if order.price is None:
        return None
    return Found(order.position or cast("str", order.client_order_id), order.price, None)


def _by_label(
    read: ReadBack, unknown: Iterable[str], sends: Mapping[str, Mapping[str, object]]
) -> tuple[dict[str, VenueOrder], dict[str, tuple[str, ...]]]:
    """Each UNKNOWN order the read-back shows no position of, read through the open positions
    that carry its label on its market and side and that no other order of the node opened.
    One such position, wanted by no other order, is the order's: the order is read as filled
    into it. Two or more are answered by name, and the order stays UNKNOWN."""
    opened = {o.position: o.client_order_id for o in read.orders if o.position is not None}
    held = {p.position for p in read.positions}
    wanted: dict[str, tuple[str, ...]] = {}
    for name in sorted(unknown):
        send = sends.get(name)
        order = next((o for o in read.orders if o.client_order_id == name), None)
        if send is None or (
            order is not None and (order.state is not OrderState.FILLED or order.position in held)
        ):
            continue
        if order is not None and order.price is not None:
            continue
        wanted[name] = tuple(
            p.position
            for p in read.positions
            if p.label == send.get("label")
            and p.market_id == send.get("market_id")
            and p.side == send.get("side")
            and opened.get(p.position, name) == name
            and (p.position == name or p.position not in sends)
        )
    counted = Counter(position for positions in wanted.values() for position in positions)
    labelled: dict[str, VenueOrder] = {}
    twice: dict[str, tuple[str, ...]] = {}
    for name, positions in wanted.items():
        if len(positions) == 1 and counted[positions[0]] == 1:
            send = sends[name]
            labelled[name] = VenueOrder(
                name,
                cast("str", send["label"]),
                cast("str", send["market_id"]),
                OrderState.FILLED,
                positions[0],
            )
        elif positions:
            twice[name] = positions
    return labelled, twice


def _without_none(value: object) -> object:
    """A journal row keeps no null; a key with nothing to say is left out."""
    if isinstance(value, dict):
        items = cast("dict[str, object]", value).items()
        return {key: _without_none(item) for key, item in items if item is not None}
    if isinstance(value, list):
        return [_without_none(item) for item in cast("list[object]", value)]
    return value


def _text(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _shown(account: str, position: VenuePosition, claimed: Attributed) -> dict[str, object]:
    return {
        "account": account,
        "position": position.position,
        "market_id": position.market_id,
        "side": position.side,
        "quantity": str(position.quantity),
        "entry_price": str(position.entry_price),
        "stop_at_venue": _text(position.stop),
        "claim": claimed.claim.value,
        "shown": NOT_OURS,
    }


def _position_row(
    position: VenuePosition, claimed: Attributed, sends: Mapping[str, Mapping[str, object]]
) -> dict[str, object]:
    row: dict[str, object] = {
        "position": position.position,
        "claim": claimed.claim.value,
        "tags": list(claimed.tags),
        "market_id": position.market_id,
        "side": position.side,
        "quantity": str(position.quantity),
        "fill_price": str(position.entry_price),
        "venue_stop": _text(position.stop),
    }
    send = sends.get(claimed.client_order_id or "") if claimed.claim is Claim.MINE else None
    if send is not None:
        stop, distance = Decimal(str(send["stop"])), Decimal(str(send["stop_distance"]))
        node_price = stop + distance if position.side == "long" else stop - distance
        row.update(
            unit_stop=str(stop),
            stop_distance=str(distance),
            node_price=str(node_price),
            slippage=str(position.entry_price - node_price),
        )
    return row
