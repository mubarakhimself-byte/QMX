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

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal

from qmb.host.unit_handler import FillKind
from qmf.core import Account, Ok, Result
from qml.unit.model import Side

from qmn.app import runtime
from qmn.app.attribution import ReadBack
from qmn.app.feed_keeper import Bar
from qmn.venue import SubmissionOutcome

__all__ = ["PaperAccount"]


@dataclass
class _Held:
    market_id: str
    side: Side
    quantity: Decimal
    entry: Decimal
    stop: Decimal | None


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
