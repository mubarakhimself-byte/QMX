"""cTrader, MT5 and CCXT fills into ``fill`` partitions and one ``trade`` item per round trip.

AD-31's three layers, built here:

* **Fills are partitions.** Every fill of one account of one month is a row in the
  ``<broker>/<account>/fill/<month>`` series, written through
  :class:`~qmf.data.series.SeriesStore`, so a fill month freezes at month end and a late fill for a
  frozen month is an automatic correction with a reason. The series rules already declare the fill
  kind (:data:`~qmf.data.series.FILL_KIND`), so nothing here re-decides the freeze or the columns.
* **A round trip is one ``trade`` item.** Fills are grouped by position id, in observation order,
  and the group becomes a draft the caller puts through the Library's port. The item name is
  ``trade/<account>/<position id>`` so a re-import addresses the same item, and ``broker_ids``
  carries every id the broker gave, which is the key the dedupe is made on.
* **Money is an exact integer.** Every money field is scaled by :attr:`Money.digits` and kept as an
  ``int``; nothing on the money path is a float. Prices are integers scaled by ``price_digits``.

The three adapters (:func:`from_ctrader`, :func:`from_mt5`, :func:`from_ccxt`) read the row shapes
those providers give and never reach the network, so an import runs on a statement the caller
already read and a test runs on a literal.

Two facts a statement cannot give are absent rather than invented: ``initial_risk`` and ``r`` need
the stop the trade was taken with, so a round trip imported from fills leaves them out and the card
shows ``unavailable`` with that reason.

The fill partition's typed columns are the shared bar set (``t, open, high, low, close, volume``),
which is what ``series.RULES`` declares for the fill kind today; a fill's price is written to all
four price columns and its volume to ``volume``, and the broker ids and the raw record ride the
``trade`` item's ``fills``. A fill series with its own typed columns is a separate change to
``qmf.data.series``.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Final, cast

from pydantic import JsonValue
from qmf.core import Ok, Result, is_refusal
from qmf.data.series import FILL_KIND, CommitReceipt, SeriesKey, SeriesStore
from qmf.data.store.refusals import invalid_input

__all__ = [
    "Fill",
    "JournalImport",
    "JournalStatement",
    "Money",
    "RoundTrip",
    "TradeDraft",
    "from_ccxt",
    "from_ctrader",
    "from_mt5",
    "import_journal",
    "round_trips",
]

PROVIDERS: Final = ("ctrader", "mt5", "ccxt")
WORLDS: Final = {"ctrader": "demo", "mt5": "demo", "ccxt": "live"}
"""What world an import assumes unless the caller says otherwise: a broker statement is a demo or
a live account and the caller knows which; the default is the safe one for the connector."""


@dataclass(frozen=True, slots=True)
class Money:
    """A money amount as an exact integer and the digits it is scaled by."""

    minor: int
    digits: int

    @classmethod
    def of(cls, value: object, digits: int) -> Money:
        """Parse `value` (a string, an int or a Decimal) into minor units, exactly."""
        if isinstance(value, Money):
            return value
        if isinstance(value, bool):
            raise ValueError(f"{value!r} is not money")
        if isinstance(value, int):
            return cls(value * 10**digits, digits)
        if isinstance(value, Decimal):
            return cls(int((value * 10**digits).to_integral_value(ROUND_HALF_UP)), digits)
        try:
            amount = Decimal(str(value).strip().replace(",", ""))
        except InvalidOperation as why:
            raise ValueError(f"{value!r} is not money") from why
        return cls(int((amount * 10**digits).to_integral_value(ROUND_HALF_UP)), digits)

    def plus(self, other: Money) -> Money:
        if other.digits != self.digits:
            raise ValueError(f"{other.digits} digits do not add to {self.digits}")
        return Money(self.minor + other.minor, self.digits)


ZERO: Final = Money(0, 0)


def _scaled(value: object, digits: int, *, name: str) -> int:
    return Money.of(value, digits).minor


def _instant(value: object) -> int:
    """A fill's time as int64 UTC nanoseconds, from epoch seconds, milliseconds or ISO-8601."""
    if isinstance(value, bool):
        raise ValueError(f"{value!r} is not a time")
    if isinstance(value, int | float):
        number = float(value)
        return int(number * 1_000_000) * 1000 if number < 1e11 else int(number) * 1_000_000
    text = str(value).strip().replace("Z", "+00:00")
    if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
        return _instant(int(text))
    found = datetime.fromisoformat(text)
    moment = found if found.tzinfo is not None else found.replace(tzinfo=UTC)
    return int(moment.timestamp() * 1_000_000_000)


@dataclass(frozen=True, slots=True)
class Fill:
    """One broker fill, as the statement gives it."""

    provider: str
    account: str
    broker_id: str
    position_id: str
    instrument: str
    side: str
    volume: str
    price_minor: int
    price_digits: int
    money_digits: int
    at_ns: int
    fee: int = 0
    swap: int = 0
    net: int | None = None
    currency: str = "USD"
    raw: JsonValue = None

    @property
    def money(self) -> Money:
        return Money(self.fee + self.swap, self.money_digits)


@dataclass(frozen=True, slots=True)
class JournalStatement:
    """One statement of one account: where it came from and the fills it holds."""

    provider: str
    account: str
    fills: tuple[Fill, ...]
    broker: str = ""
    world: str = ""
    currency: str = "USD"
    money_digits: int = 2
    price_digits: int = 5
    correction: str | None = None
    """The reason a late fill for a frozen month is a correction, or None for a plain import."""

    def __post_init__(self) -> None:
        if self.provider not in PROVIDERS:
            raise ValueError(f"{self.provider!r} is not one of {PROVIDERS}")


@dataclass(frozen=True, slots=True)
class TradeDraft:
    """A round trip as the ``trade`` item the caller puts through the Library."""

    item: str
    intent_key: str
    title: str
    fields: dict[str, JsonValue]
    fills_key: str


@dataclass(frozen=True, slots=True)
class RoundTrip:
    """One position: its fills in observation order and the trade they make."""

    account: str
    position_id: str
    instrument: str
    side: str
    fills: tuple[Fill, ...]

    @property
    def broker_ids(self) -> tuple[str, ...]:
        return tuple(fill.broker_id for fill in self.fills)

    @property
    def broker(self) -> str:
        return self.fills[0].provider

    @property
    def money_digits(self) -> int:
        return self.fills[0].money_digits

    @property
    def price_digits(self) -> int:
        return self.fills[0].price_digits

    @property
    def currency(self) -> str:
        return self.fills[0].currency

    @property
    def opened_ns(self) -> int:
        return self.fills[0].at_ns

    @property
    def closed_ns(self) -> int:
        return self.fills[-1].at_ns

    @property
    def holding_ns(self) -> int:
        return self.closed_ns - self.opened_ns

    @property
    def entry_price(self) -> int:
        return self.fills[0].price_minor

    @property
    def exit_price(self) -> int:
        return self.fills[-1].price_minor

    @property
    def volume(self) -> str:
        total = Decimal(0)
        for fill in self.fills:
            total += Decimal(fill.volume)
        return str(total.normalize())

    @property
    def fees(self) -> int:
        return sum(fill.fee for fill in self.fills)

    @property
    def swap(self) -> int:
        return sum(fill.swap for fill in self.fills)

    @property
    def net_result(self) -> int | None:
        """The statement's own net when every fill carried one; else nothing is invented."""
        given = [fill.net for fill in self.fills]
        if any(value is None for value in given):
            return None
        return sum(cast(int, value) for value in given)

    def as_fields(self, *, world: str, broker: str) -> dict[str, JsonValue]:
        """The ``trade`` schema's fields for this round trip, with money as exact integers."""
        fields: dict[str, JsonValue] = {
            "account": self.account,
            "broker": broker,
            "position_id": self.position_id,
            "broker_ids": list(self.broker_ids),
            "world": world,
            "instrument": self.instrument,
            "side": self.side,
            "volume": self.volume,
            "entry_ns": self.opened_ns,
            "exit_ns": self.closed_ns,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "price_digits": self.price_digits,
            "money_digits": self.money_digits,
            "currency": self.currency,
            "fees": self.fees,
            "swap": self.swap,
            "holding_ns": self.holding_ns,
            "fills": [fill.raw for fill in self.fills],
        }
        net = self.net_result
        if net is not None:
            fields["net_result"] = net
            fields["gross_result"] = net - self.swap + self.fees
        return fields

    def draft(self, *, world: str, broker: str) -> TradeDraft:
        item = f"trade/{self.account}/{self.position_id}"
        return TradeDraft(
            item=item,
            intent_key=f"trade:{self.account}:{self.position_id}",
            title=f"{self.instrument} {self.side} {self.position_id}",
            fields=self.as_fields(world=world, broker=broker),
            fills_key=",".join(self.broker_ids),
        )


@dataclass(frozen=True, slots=True)
class JournalImport:
    """What one statement's import landed, and what it recognised as already held."""

    account: str
    partitions: tuple[CommitReceipt, ...]
    added: tuple[TradeDraft, ...]
    held: tuple[str, ...]
    """The items that were already held, so this import wrote no trade for them."""

    unresolved: tuple[str, ...] = ()
    """The position ids with one fill only: a position still open is not a round trip yet."""

    @property
    def fills_written(self) -> int:
        return sum(receipt.rows for receipt in self.partitions)

    @property
    def idempotent(self) -> bool:
        return all(receipt.idempotent for receipt in self.partitions)


def _rows(key: SeriesKey, fills: Sequence[Fill]) -> list[tuple[int, int, int, int, int, float]]:
    """One typed row per fill: its price on the four price columns, its volume, in time order."""
    ordered = sorted(fills, key=lambda fill: fill.at_ns)
    return [
        (fill.at_ns // 1_000_000, fill.price_minor, fill.price_minor, fill.price_minor,
         fill.price_minor, float(fill.volume))
        for fill in ordered
    ]  # fmt: skip


def _months(fills: Sequence[Fill]) -> Iterator[tuple[int, int]]:
    months = {(moment.year, moment.month) for moment in map(_moment_of, fills)}
    yield from sorted(months)


def _moment_of(fill: Fill) -> datetime:
    return datetime.fromtimestamp(fill.at_ns / 1_000_000_000, tz=UTC)


def round_trips(fills: Iterable[Fill]) -> tuple[tuple[RoundTrip, ...], tuple[str, ...]]:
    """Group fills by position id in observation order; return the round trips and the open ones."""
    grouped: dict[str, list[Fill]] = {}
    for fill in fills:
        grouped.setdefault(fill.position_id, []).append(fill)
    trips: list[RoundTrip] = []
    open_positions: list[str] = []
    for position_id in sorted(grouped):
        ordered = sorted(grouped[position_id], key=lambda fill: fill.at_ns)
        first = ordered[0]
        if len(ordered) < 2:
            open_positions.append(position_id)
            continue
        trips.append(
            RoundTrip(
                account=first.account,
                position_id=position_id,
                instrument=first.instrument,
                side=first.side,
                fills=tuple(ordered),
            )
        )
    return tuple(trips), tuple(open_positions)


def import_journal(
    store: SeriesStore,
    statement: JournalStatement,
    *,
    held: Iterable[str] = (),
    world: str | None = None,
) -> Result[JournalImport]:
    """Write the statement's fills as monthly partitions and draft one `trade` per round trip.

    `held` names the trade items the caller already holds, by the item name
    :meth:`RoundTrip.draft` gives; a round trip whose item is held is returned in `held` and never
    added, which is the "a re-import of the same statement dedupes by broker ids" rule.
    """
    if not statement.fills:
        return invalid_input("fills", "the statement holds no fill", account=statement.account)
    keys: list[SeriesKey] = []
    for year, month in _months(statement.fills):
        built = SeriesKey.try_create(statement.provider, statement.account, FILL_KIND, year, month)
        if is_refusal(built):
            return built
        keys.append(built.value)
    receipts: list[CommitReceipt] = []
    for key in keys:
        month = [fill for fill in statement.fills if _moment_of(fill).year == key.year]
        month = [fill for fill in month if _moment_of(fill).month == key.month]
        written = store.commit(key, _rows(key, month), correction=statement.correction)
        if is_refusal(written):
            return written
        receipts.append(written.value)
    trips, open_positions = round_trips(statement.fills)
    already = set(held)
    chosen_world = world or statement.world or WORLDS.get(statement.provider, "demo")
    drafts = [
        trip.draft(world=chosen_world, broker=statement.broker or statement.provider)
        for trip in trips
    ]
    return Ok(
        JournalImport(
            account=statement.account,
            partitions=tuple(receipts),
            added=tuple(draft for draft in drafts if draft.item not in already),
            held=tuple(draft.item for draft in drafts if draft.item in already),
            unresolved=open_positions,
        )
    )


def _row(row: dict[str, object], *names: str) -> object:
    wanted = {name.lower() for name in names}
    for key, value in row.items():
        if key.strip().lower() in wanted:
            return value
    return None


def from_ctrader(
    rows: Iterable[dict[str, object]],
    *,
    account: str,
    currency: str = "USD",
    money_digits: int = 2,
    price_digits: int = 5,  # mock-data-scan: allow
) -> tuple[Fill, ...]:
    """cTrader's deal rows: ``dealId``, ``positionId``, ``symbolName``, ``tradeSide``, ``volume``,
    ``executionPrice``, ``executionTime``, ``commission`` and ``swap``."""
    found: list[Fill] = []
    for row in rows:
        size = Decimal(str(_row(row, "volume", "volumeinlots") or "0"))
        found.append(
            Fill(
                provider="ctrader",
                account=str(_row(row, "accountid") or account),
                broker_id=str(_row(row, "dealid", "id")),
                position_id=str(_row(row, "positionid", "position")),
                instrument=str(_row(row, "symbolname", "symbol")),
                side=str(_row(row, "tradeside", "side")).lower(),
                volume=str(size),
                price_minor=_scaled(
                    _row(row, "executionprice", "price"), price_digits, name="price"
                ),
                price_digits=price_digits,
                money_digits=money_digits,
                at_ns=_instant(_row(row, "executiontime", "time")),
                fee=_scaled(_row(row, "commission", "fee") or 0, money_digits, name="commission"),
                swap=_scaled(_row(row, "swap") or 0, money_digits, name="swap"),
                net=_scaled(_row(row, "netprofit", "profit"), money_digits, name="net")
                if _row(row, "netprofit", "profit") is not None
                else None,
                currency=currency,
                raw=cast(JsonValue, row),
            )
        )
    return tuple(found)


def from_mt5(
    rows: Iterable[dict[str, object]],
    *,
    account: str,
    currency: str = "USD",
    money_digits: int = 2,
    price_digits: int = 5,  # mock-data-scan: allow
) -> tuple[Fill, ...]:
    """MT5's deal rows: ``Deal``, ``Position``, ``Symbol``, ``Type``, ``Volume``, ``Price``,
    ``Time``, ``Commission``, ``Swap`` and ``Profit``. A ``Type`` of 0 buys and 1 sells."""
    found: list[Fill] = []
    for row in rows:
        kind = str(_row(row, "type", "dealtype"))
        found.append(
            Fill(
                provider="mt5",
                account=str(_row(row, "login", "account") or account),
                broker_id=str(_row(row, "deal", "ticket", "id")),
                position_id=str(_row(row, "position", "positionid")),
                instrument=str(_row(row, "symbol")),
                side="buy" if kind in ("0", "buy") else "sell",
                volume=str(Decimal(str(_row(row, "volume") or "0"))),
                price_minor=_scaled(_row(row, "price"), price_digits, name="price"),
                price_digits=price_digits,
                money_digits=money_digits,
                at_ns=_instant(_row(row, "time")),
                fee=_scaled(_row(row, "commission") or 0, money_digits, name="commission"),
                swap=_scaled(_row(row, "swap") or 0, money_digits, name="swap"),
                net=_scaled(_row(row, "profit"), money_digits, name="profit")
                if _row(row, "profit") is not None
                else None,
                currency=currency,
                raw=cast(JsonValue, row),
            )
        )
    return tuple(found)


def from_ccxt(
    rows: Iterable[dict[str, object]],
    *,
    account: str,
    currency: str = "USD",
    money_digits: int = 8,
    price_digits: int = 8,  # mock-data-scan: allow
) -> tuple[Fill, ...]:
    """CCXT's ``fetchMyTrades`` rows: ``id``, ``order``, ``symbol``, ``side``, ``amount``,
    ``price``, ``timestamp``, ``fee`` and ``info`` (where an exchange puts its position id)."""
    found: list[Fill] = []
    for row in rows:
        info = _row(row, "info")
        inside = cast(dict[str, object], info) if isinstance(info, dict) else {}
        fee = _row(row, "fee")
        charged = cast(dict[str, object], fee).get("cost") if isinstance(fee, dict) else None
        found.append(
            Fill(
                provider="ccxt",
                account=str(_row(row, "account") or account),
                broker_id=str(_row(row, "id")),
                position_id=str(
                    _row(row, "positionid")
                    or _row(inside, "positionId", "position_id", "orderId")
                    or _row(row, "order")
                ),
                instrument=str(_row(row, "symbol")),
                side=str(_row(row, "side")).lower(),
                volume=str(Decimal(str(_row(row, "amount") or "0"))),
                price_minor=_scaled(_row(row, "price"), price_digits, name="price"),
                price_digits=price_digits,
                money_digits=money_digits,
                at_ns=_instant(_row(row, "timestamp")),
                fee=_scaled(charged or 0, money_digits, name="fee"),
                net=None,
                currency=currency,
                raw=cast(JsonValue, row),
            )
        )
    return tuple(found)


def dumped(note: JournalImport) -> str:
    """One line per import for a log, with the counts and the ids it defers."""
    return json.dumps(
        {
            "account": note.account,
            "partitions": [receipt.key.text for receipt in note.partitions],
            "rows": note.fills_written,
            "added": [draft.item for draft in note.added],
            "held": list(note.held),
            "open_positions": list(note.unresolved),
        },
        sort_keys=True,
    )
