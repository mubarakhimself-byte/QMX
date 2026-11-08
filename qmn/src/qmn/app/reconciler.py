"""Reconcile each account with its venue, the venue winning (Level 0 AD-8, AD-38; Part C TN-01).

The runtime calls :meth:`Reconciler.run` for an account whenever :meth:`Reconciler.due` says so:
once per venue session, so at start and after every reconnect, and again when an order's
outcome turned UNKNOWN. Until the run for the current session has happened, :meth:`holds`
keeps every new entry on the account back.

One run reads everything the venue holds on the account, the open and recently done orders by
client order id and the positions by their label, and attributes each record
(:mod:`qmn.app.attribution`) against the sends the node's own journal holds. Then:

- each UNKNOWN outcome resolves from what the venue shows: the order filled, so its unit books
  the fill at the venue's price, or the venue holds nothing from it, so the entry is dropped.
  Nothing is ever sent again on an UNKNOWN; an order the venue still shows open stays UNKNOWN.
- a twin or a foreign node's record stands the account down: no new entry, with an alarm.
- a position that is not the node's is never touched and never adopted. It is shown as
  "not ours, protected", and an untagged one raises the ``not_ours`` alarm once.
- one ``reconcile`` row records the run, with the node's price and stop distance beside the
  venue's fill price and stop for each of the node's positions (C-12a low L6).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
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

__all__ = ["ReadsBack", "Reconciler", "Resolves", "journal_sends"]

_STAND_DOWN = {
    Claim.TWIN: "the node cannot prove the account is its own: a twin with its tag trades it",
    Claim.FOREIGN: "the node cannot prove the account is its own: another node's tag is on it",
}


class ReadsBack(Protocol):
    def read_back(self) -> Result[ReadBack]:
        """Every order and position the venue holds on the account."""
        ...


class Resolves(Protocol):
    """A hosted unit, which may hold an order whose outcome is UNKNOWN."""

    def resolve(self, client_order_id: str, price: Decimal | None, *, protected: bool) -> bool:
        """Settle the order: filled at the venue's ``price``, or never taken when ``price`` is
        None. Answers False when the order is not this unit's."""
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


@dataclass
class _Account:
    session: int | None = None
    """The venue session the last run happened in."""
    tried: frozenset[str] = frozenset()
    """The UNKNOWN orders the last run saw."""
    stand_down: Claim | None = None
    not_ours: tuple[dict[str, object], ...] = ()


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
        found = attribute(read.value, tag=self.tag, sent=sends.value)
        resolved = [self._resolve(name, read.value, units) for name in sorted(unknown)]
        held.session, held.tried = session, frozenset(unknown)
        held.stand_down = found.stand_down
        held.not_ours = tuple(
            _shown(account, position, claimed)
            for position, claimed in found.positions
            if claimed.claim is not Claim.MINE
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
        self, name: str, read: ReadBack, units: Sequence[Resolves]
    ) -> dict[str, object] | None:
        order = next((o for o in read.orders if o.client_order_id == name), None)
        if order is not None and order.state is OrderState.OPEN:
            return None
        filled = order is not None and order.state is OrderState.FILLED and order.price is not None
        price = cast("VenueOrder", order).price if filled else None
        position = next(
            (p for p in read.positions if order is not None and p.position == order.position), None
        )
        protected = position is None or position.stop is not None
        if not any(unit.resolve(name, price, protected=protected) for unit in units):
            return None
        if not protected and position is not None:
            self._raise(
                ("unprotected", name),
                {
                    "alarm": "protection_escalation",
                    "position": name,
                    "market_id": position.market_id,
                    "action": "closing_reduce_only",
                    "why": "the venue holds no stop on an order whose answer was lost",
                    "origin": "placeholder",
                },
            )
        return {
            "client_order_id": name,
            "outcome": "filled" if filled else "absent",
            "price": None if price is None else str(price),
        }

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
