"""A unit's paper lane: its decisions on the venue's live prices, its fills simulated, no order
sent (Level 0 AD-38, AD-39; Part C slice C-12c).

A paper deployment trades through the same order path as a live one: the local guards, the
cross-unit hook, the protection gate proving the venue's stop form, the journal before
dispatch. Only the last step differs. Where a live lane's ticket reaches the venue, a paper
lane's ticket reaches :class:`PaperAccount`, which fills it at the feed's price and holds its
stop the way a broker would. The account binding it sits beside is read for its account, its
proven stop forms and its balance, and is never sent anything.

A paper lane starts from the unit's defaults, as QMB tested it (AD-38). Its rows carry world
``paper`` in the unit journal and in the node journal, so no paper fill reads as a venue's.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import cast

from qmb.host.unit_handler import FillKind
from qmf.core import Account, Ok, Result, is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qml.unit.model import Side

from qmn.app import runtime
from qmn.app.attribution import ReadBack, VenuePosition
from qmn.app.feed_keeper import Bar
from qmn.app.reconciler import Ours
from qmn.venue import SubmissionOutcome

__all__ = ["PaperAccount", "restored"]


@dataclass
class _Held:
    market_id: str
    side: Side
    quantity: Decimal
    entry: Decimal
    stop: Decimal | None


def restored(root: Path, deployment_id: str) -> Result[tuple[Ours, ...]]:
    """Each position the paper lane still holds for ``deployment_id``, rebuilt from the journals.

    A position is a ``send`` row in the node journal's ``paper`` partition with a ``filled`` row,
    no ``closed`` row, and no ``trade`` row naming its client order id in the unit journal. A paper
    stop that fires writes no node journal row, so the trade row is the only proof a past stop
    closed; without it every past stopped trade would come back as an open position and could
    close a second time. Stops crossed while the process was down fire on the next bar.
    """
    orders = _paper_orders(root, deployment_id)
    if is_refusal(orders):
        return orders
    traded = _paper_trades(root)
    if is_refusal(traded):
        return traded
    sends, fills, closed = orders.value
    found: list[Ours] = []
    for name, send in sends.items():
        held = _position(name, send, fills.get(name), closed, traded.value)
        if held is not None:
            found.append(Ours(held, send))
    return Ok(tuple(found))


def _position(
    name: str,
    send: Mapping[str, object],
    fill: tuple[str, str] | None,
    closed: frozenset[str],
    traded: frozenset[str],
) -> VenuePosition | None:
    """One rebuilt position, or None when its rows say it is closed or cannot hold a stop."""
    if fill is None or name in closed or name in traded:
        return None
    try:
        return VenuePosition(
            name,
            None if send.get("label") is None else str(send["label"]),
            str(send["market_id"]),
            str(send["side"]),
            Decimal(fill[1]),
            Decimal(fill[0]),
            Decimal(str(send["stop"])),
        )
    except (KeyError, ArithmeticError):
        return None


def _paper_orders(
    root: Path, deployment_id: str
) -> Result[tuple[dict[str, Mapping[str, object]], dict[str, tuple[str, str]], frozenset[str]]]:
    """The paper partition's entry sends for this deployment, their fills, and their closes.

    A send row carries its deployment id; a fill or close row carries only the client order id
    the entry minted, which is unique on the node, so those are collected by name."""
    sends: dict[str, Mapping[str, object]] = {}
    fills: dict[str, tuple[str, str]] = {}
    closed: set[str] = set()
    for folder in stream_folders(root):
        if not folder.name.startswith(f"{JournalStream.NODE.source}.order."):
            continue
        lines = read_committed(folder)
        if is_refusal(lines):
            return lines
        for line in lines.value:
            if not isinstance(line, JournalLine):
                continue
            if line.record.get("world") != JournalWorld.PAPER.value:
                continue
            body = cast("Mapping[str, object]", line.record.get("body", {}))
            name = body.get("client_order_id")
            if not isinstance(name, str):
                continue
            step = body.get("step")
            if step == "send" and body.get("deployment_id") == deployment_id:
                sends[name] = body
            elif step == "filled" and "price" in body and "quantity" in body:
                fills[name] = (str(body["price"]), str(body["quantity"]))
            elif step == "closed":
                closed.add(name)
    return Ok((sends, fills, frozenset(closed)))


def _paper_trades(root: Path) -> Result[frozenset[str]]:
    """Every client order id the unit journals name as traded in the paper world."""
    traded: set[str] = set()
    for folder in stream_folders(root):
        if not folder.name.startswith(f"{JournalStream.UNIT.source}.trade."):
            continue
        lines = read_committed(folder)
        if is_refusal(lines):
            return lines
        for line in lines.value:
            if not isinstance(line, JournalLine):
                continue
            if line.record.get("world") != JournalWorld.PAPER.value:
                continue
            body = cast("Mapping[str, object]", line.record.get("body", {}))
            if body.get("trade_id") is not None:
                traded.add(str(body["trade_id"]))
    return Ok(frozenset(traded))


@dataclass
class PaperAccount:
    """The paper lane of one deployment at one account binding.

    ``simulated`` is every ticket the lane filled or refused itself. An entry fills at the ask
    for a long and the bid for a short, from the bars the feed closed; its stop is held at the
    order's distance from that fill and fires on the feed's bars, at the stop or at the open
    when a bar opens past it. A close fills at the other side. Nothing here holds a session to
    a venue.
    """

    binding: runtime.VenueAccount
    simulated: list[runtime.Ticket] = field(default_factory=list["runtime.Ticket"])
    _positions: dict[str, _Held] = field(default_factory=dict[str, _Held])
    _closed: dict[str, runtime.VenueClose] = field(default_factory=dict[str, "runtime.VenueClose"])
    _quotes: dict[str, tuple[Decimal, Decimal]] = field(
        default_factory=dict[str, tuple[Decimal, Decimal]]
    )

    @property
    def account(self) -> Account:
        return self.binding.account

    @property
    def stop_forms(self) -> Mapping[str, str]:
        """The stop forms the binding's venue proved, so a paper order passes the same gate a
        live one would."""
        return self.binding.stop_forms

    def equity(self) -> Decimal:
        return self.binding.equity()

    def nets_positions(self) -> bool:
        """A paper order stands in for one that would net at the binding's venue."""
        return self.binding.nets_positions()

    def bar_size_ns(self) -> int | None:
        return self.binding.bar_size_ns()

    def add_markets(self, markets: Mapping[str, str], /) -> bool:
        return self.binding.add_markets(markets)

    def unauthorised(self, market: str, /) -> str | None:
        return self.binding.unauthorised(market)

    def on_bar(self, event: Bar) -> None:
        bar = event.bar
        for position, held in list(self._positions.items()):
            if held.market_id != event.market_id or held.stop is None:
                continue
            long = held.side is Side.LONG
            quote = bar.bid if long else bar.ask
            worse = 1 if long else -1
            if (held.stop - quote.open) * worse > 0:
                self._close(position, runtime.VenueClose(FillKind.STOP, quote.open, gap=True))
            elif (held.stop - (quote.low if long else quote.high)) * worse >= 0:
                self._close(position, runtime.VenueClose(FillKind.STOP, held.stop))
        self._quotes[event.market_id] = (bar.bid.close, bar.ask.close)

    def _close(self, position: str, closed: runtime.VenueClose) -> None:
        del self._positions[position]
        self._closed[position] = closed

    def adopt(self, found: Sequence[Ours]) -> None:
        """Hold each rebuilt position, so its stop fires on the next bar and its close answers.
        A position already held keeps its state."""
        for ours in found:
            position = ours.position
            self._positions.setdefault(
                position.position,
                _Held(
                    position.market_id,
                    Side(position.side),
                    position.quantity,
                    position.entry_price,
                    position.stop,
                ),
            )

    def send(self, ticket: runtime.Ticket, /) -> Result[runtime.Sent]:
        self.simulated.append(ticket)
        quote = self._quotes.get(ticket.market_id)
        if quote is None:
            return Ok(runtime.Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "paper-no-price"))
        bid, ask = quote
        params = ticket.command.order_parameters
        filled = SubmissionOutcome.ACCEPTED_BY_VENUE
        if params is not None and ticket.tags is not None and ticket.quantity is not None:
            long = ticket.side is Side.LONG
            price = ask if long else bid
            distance = params.protective_stop_distance
            stop = None
            if distance is not None:
                gap = Decimal(distance.value).scaleb(-distance.scale)
                stop = price - gap if long else price + gap
            self._positions[ticket.tags.client_order_id] = _Held(
                ticket.market_id, ticket.side, ticket.quantity, price, stop
            )
            return Ok(runtime.Sent(filled, price))
        position = ticket.position
        if position is None or position not in self._positions:
            return Ok(runtime.Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "no-such-position"))
        held = self._positions[position]
        amendment = ticket.command.protection_amendment
        if amendment is not None:
            gap = Decimal(amendment.new_distance.value).scaleb(-amendment.new_distance.scale)
            held.stop = held.entry - gap if held.side is Side.LONG else held.entry + gap
            return Ok(runtime.Sent(filled, held.stop))
        price = bid if held.side is Side.LONG else ask
        self._close(position, runtime.VenueClose(FillKind.CLOSE, price))
        return Ok(runtime.Sent(filled, price))

    def stop_of(self, position: str, /) -> Decimal | None:
        held = self._positions.get(position)
        return None if held is None else held.stop

    def closed(self, position: str, /) -> runtime.VenueClose | None:
        return self._closed.get(position)

    def read_back(self) -> Result[ReadBack]:
        """A paper lane holds nothing at the venue. The node reconciles the binding."""
        return Ok(ReadBack((), ()))
