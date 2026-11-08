"""The account, venue and instrument records a deploy reads, landed from the node's own cTrader
read (C-34, Level 0 AD-26, Part C AD-312).

Promote reads one `account`, one `venue` and one `instrument` record per market from the
Library's `main` (`promote.py`). After a passing self-test the node answers its `records` read:
the bound account's facts and each named symbol's, as cTrader states them on a fresh session.
This module maps that answer onto the three kinds and lands each record on `main` as the store's
engine, by its standing-rule `land` (`qmx_library.principal.may_advance`): the record is put on
this job's run ref, then the engine merges it into `main`. No other kind takes this path, and
no agent or run moves `main` by it.

A record changes only when its facts do: the head on `main` is read, the venue's facts are laid
over it, and a new version lands only when the result differs. Keys he wrote on the record and
cTrader does not state, a calendar or a note, stay as he wrote them. `world` is cTrader's live
flag for the account as the node read it, never an argument.

cTrader only. The CCXT refresh template's record files stay run artifacts until something binds
a CCXT venue (BACKLOG).
"""

from __future__ import annotations

import asyncio
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_UP, Decimal
from typing import TYPE_CHECKING, Final, Literal, cast

from pydantic import JsonValue
from qmx_apps.errors import AppError, Document
from qmx_library.port import Draft, JsonObject, LibraryRefused
from qmx_library.principal import MAIN, Principal, runs_ref, state_ref
from qmx_library.store import Store

if TYPE_CHECKING:
    from qmx_apps.supervisor import Supervisor

__all__ = [
    "DATA_LEVELS",
    "KINDS",
    "MARKETS",
    "REFRESH_S",
    "RUN",
    "Landed",
    "Market",
    "Record",
    "Refresh",
    "VenueRecords",
    "bound_accounts",
    "land",
    "node_call",
    "read_and_land",
    "records_of",
    "refresh",
    "said",
    "self_test_passed",
]

NODE_APP: Final = "trading-node"
KINDS: Final = frozenset({"account", "venue", "instrument"})
"""The only kinds this path lands on main."""
RUN: Final = "venue-records"
"""The run whose ref each record is put on before the engine lands it on `main`."""
LANDER: Final = Principal("run", RUN)
REFRESH_S: Final = 86_400
"""`[node] records_refresh_s`, starting at one day: how often the refresh job reads the node's
records again."""
MARGIN_PLACES: Final = 4
"""A margin fraction is written at 4 places, rounded up, so it never says less than cTrader
takes (1:30 is 0.0334)."""
DATA_LEVELS: Final[JsonObject] = {
    "schema": "qmx.data-level/1",
    "levels": [0, 1, 2],
    "volume": "tick_count",
}
"""What the node's cTrader binding offers: its calendar, the bars it builds from spots and the
quote ticks, with tick-count volume."""


@dataclass(frozen=True, slots=True)
class Market:
    """A market he names for his cTrader account, with QMX's own facts about it that cTrader
    does not state: the underlying it shares across venues, its class and the calendar QMX
    reads it by."""

    symbol: str
    market_id: str
    klass: str
    calendar_ref: str
    zone: str
    day_boundary: str


MARKETS: Final = (
    Market("EURUSD", "eurusd", "fx", "fx-24x5@1", "America/New_York", "17:00"),
    Market("XAUUSD", "gold", "metal", "metals-24x5@1", "America/New_York", "17:00"),
)
"""`[node] record_markets`: the markets whose records land, starting at the dummy's two."""

type Call = Callable[[str, Mapping[str, object]], Mapping[str, object]]
"""One node operation through the supervisor: the node's answer, `{ok, value}` or a refusal."""
type Outcome = Literal["landed", "unchanged", "refused"]


@dataclass(frozen=True, slots=True)
class Record:
    """One record to land: its kind, the fields that name it on `main`, the item a new one
    takes, the venue's facts (which always win) and his named facts (which fill only keys the
    record lacks)."""

    kind: str
    match: Mapping[str, str]
    item: str
    title: str
    facts: JsonObject
    named: JsonObject


@dataclass(frozen=True, slots=True)
class Landed:
    kind: str
    item: str
    outcome: Outcome
    version: int | None
    why: str = ""


@dataclass(frozen=True, slots=True)
class Refresh:
    account: str
    landed: tuple[Landed, ...]
    refused: str | None = None


def _slug(*parts: str) -> str:
    return "-".join(re.sub(r"[^a-z0-9]+", "-", part.lower()).strip("-") for part in parts)


def _decimal(value: Decimal) -> str:
    return f"{value.normalize():f}"


def _present(values: Mapping[str, object]) -> JsonObject:
    return {key: cast(JsonValue, value) for key, value in values.items() if value is not None}


def records_of(answer: Mapping[str, object], markets: Sequence[Market] = MARKETS) -> list[Record]:
    """The node's `qmx.node.records/1` answer as the three kinds' records: one account, one
    venue, and one instrument per named market cTrader answered."""
    venue_part = cast("Mapping[str, object]", answer["venue"])
    account = cast("Mapping[str, object]", answer["account"])
    venue = str(venue_part["name"])
    account_id = str(account["id"])
    leverage = account.get("leverage")
    found: list[Record] = [
        Record(
            "account",
            {"venue": venue, "account_id": account_id},
            f"account-{_slug(venue, account_id)}",
            f"{account_id} at {venue}",
            _present(
                {
                    "venue": venue,
                    "account_id": account_id,
                    "world": account["world"],
                    "broker": account.get("broker") or None,
                    "position_mode": account.get("position_mode"),
                    "base_currency": account.get("base_currency"),
                    "leverage": leverage,
                    "owner": account.get("owner"),
                    "grant_scope": account.get("grant_scope"),
                }
            ),
            {},
        ),
        Record(
            "venue",
            {"venue": venue},
            f"venue-{_slug(venue)}",
            venue,
            {"venue": venue, "sandbox": str(venue_part["sandbox"]), "data_levels": DATA_LEVELS},
            {},
        ),
    ]
    named = {market.symbol: market for market in markets}
    for row in cast("list[Mapping[str, object]]", answer.get("instruments") or []):
        market = named.get(str(row["symbol"]))
        if market is None:
            continue
        found.append(_instrument(venue, row, market, leverage))
    return found


def _instrument(venue: str, row: Mapping[str, object], market: Market, leverage: object) -> Record:
    """cTrader's symbol facts in the instrument kind's units. Volumes are cents of the base
    unit, so a lot is `lot_size / 100` units and a lot step is `step_volume / lot_size`."""
    lot = Decimal(cast("int", row["lot_size"]))
    digits, pip = cast("int", row["digits"]), cast("int", row["pip_position"])
    contract = lot.scaleb(-2)
    biggest = row.get("max_volume")
    facts: dict[str, object] = {
        "venue": venue,
        "symbol": market.symbol,
        "currency": row.get("quote_currency"),
        "digits": digits,
        "tick_size": _decimal(Decimal(1).scaleb(-digits)),
        "pip": {"size": _decimal(Decimal(1).scaleb(-pip)), "source": f"ctrader: pipPosition {pip}"},
        "contract_size": _decimal(contract),
        "value_per_point": _decimal(contract),
        "lot_step": _decimal(Decimal(cast("int", row["step_volume"])) / lot),
        "min_lot": _decimal(Decimal(cast("int", row["min_volume"])) / lot),
        "max_lot": None if biggest is None else _decimal(Decimal(cast("int", biggest)) / lot),
        "server_zone": row.get("schedule_zone"),
        "data_levels": DATA_LEVELS,
        "status": "live" if row.get("trading_mode") == "ENABLED" else "suspect",
    }
    if isinstance(leverage, str):
        margin = (Decimal(1) / Decimal(leverage)).quantize(
            Decimal(1).scaleb(-MARGIN_PLACES), rounding=ROUND_UP
        )
        facts["leverage"] = {
            "version": 1,
            "tiers": [
                {
                    "leverage": leverage,
                    "source": "ctrader: the account's leverageInCents; the symbol's own"
                    " dynamic leverage is not read",
                }
            ],
        }
        facts["margin"] = {"intraday": _decimal(margin), "overnight": _decimal(margin)}
    return Record(
        "instrument",
        {"venue": venue, "symbol": market.symbol},
        f"instrument-{_slug(venue, market.symbol)}",
        f"{market.symbol} at {venue}",
        _present(facts),
        {
            "market_id": market.market_id,
            "class": market.klass,
            "calendar_ref": market.calendar_ref,
            "zone": market.zone,
            "day_boundary": market.day_boundary,
        },
    )


def _on_main(store: Store, record: Record) -> list[tuple[str, str, JsonObject]]:
    """Each live item of the record's kind whose head on `main` holds its naming fields."""
    key, value = next(iter(record.match.items()))
    reader = Principal("operator")
    items = {store.get(reader, found).item for found in store.with_field(record.kind, key, value)}
    held: list[tuple[str, str, JsonObject]] = []
    for item in sorted(items):
        head, state = store.head(item, MAIN), store.head(item, state_ref(item))
        if head is None or (state is not None and state[0] == "archived"):
            continue
        fields = store.get(reader, head[0]).fields
        if all(fields.get(name) == wanted for name, wanted in record.match.items()):
            held.append((item, head[0], fields))
    return held


def land(store: Store, records: Sequence[Record]) -> list[Landed]:
    """Land each record on `main`: put on this job's run ref, then merged by the engine. A
    record whose facts match its head lands nothing; two records naming the same market, or an
    archived item, land nothing and say why."""
    done: list[Landed] = []
    ref = runs_ref(RUN)
    for record in records:
        if record.kind not in KINDS:
            why = "only account, venue and instrument records land by this path"
            done.append(Landed(record.kind, record.item, "refused", None, why))
            continue
        held = _on_main(store, record)
        if len(held) > 1:
            why = f"{len(held)} {record.kind} records on main name {dict(record.match)}"
            done.append(Landed(record.kind, held[0][0], "refused", None, why))
            continue
        item, head, fields = held[0] if held else (record.item, None, {})
        merged: JsonObject = {
            **{key: value for key, value in record.named.items() if key not in fields},
            **fields,
            **record.facts,
        }
        if head is not None and merged == fields:
            done.append(Landed(record.kind, item, "unchanged", _version(store, item)))
            continue
        try:
            run_head = store.head(item, ref)
            store.put(
                LANDER,
                Draft(
                    record.kind,
                    item=item,
                    title=record.title,
                    fields=merged,
                    parents=[] if head is None else [head],
                ),
                on=ref,
                expected_head=None if run_head is None else run_head[0],
            )
            merged_into = store.merge(
                store.engine, item, from_ref=ref, into=MAIN, strategy="ff-only"
            )
        except LibraryRefused as refused:
            done.append(Landed(record.kind, item, "refused", None, str(refused)))
            continue
        if merged_into.outcome == "conflict":
            done.append(
                Landed(record.kind, item, "refused", None, f"{item} moved on main meanwhile")
            )
            continue
        done.append(Landed(record.kind, item, "landed", _version(store, item)))
    return done


def _version(store: Store, item: str) -> int | None:
    head = store.head(item, MAIN)
    return None if head is None else head[1]


def _value(answer: Mapping[str, object]) -> Mapping[str, object] | None:
    found = answer.get("value")
    return cast("Mapping[str, object]", found) if answer.get("ok") is True else None


def node_call(apps: Supervisor) -> Call:
    """The trading node's operations through the supervisor; a call the supervisor refuses
    reads as the node's refusal."""

    def call(operation: str, arguments: Mapping[str, object]) -> Mapping[str, object]:
        try:
            called = apps.call(NODE_APP, operation, cast("Document", dict(arguments)))
        except AppError as error:
            return {"ok": False, "code": error.code, "message": str(error)}
        return cast("Mapping[str, object]", called.get("result") or {})

    return call


def self_test_passed(call: Call) -> bool:
    """The node's passport holds its self-test's checks, every one ok."""
    passport = _value(call("passport", {})) or {}
    checks = cast("list[Mapping[str, object]]", passport.get("checks") or [])
    return bool(checks) and all(check.get("ok") is True for check in checks)


def bound_accounts(call: Call) -> list[str]:
    """The cTrader accounts the node holds bound, from its `status` venue row."""
    status = _value(call("status", {})) or {}
    for row in cast("list[Mapping[str, object]]", status.get("venues") or []):
        if row.get("venue") == "ctrader":
            return [str(account) for account in cast("list[object]", row.get("accounts") or [])]
    return []


def read_and_land(
    call: Call, store: Store, account: str, markets: Sequence[Market] = MARKETS
) -> Refresh:
    """Ask the node for `account`'s records and land them."""
    answer = call("records", {"account": account, "symbols": [m.symbol for m in markets]})
    value = _value(answer)
    if value is None:
        return Refresh(account, (), f"{answer.get('code')}: {answer.get('message')}")
    return Refresh(account, tuple(land(store, records_of(value, markets))))


def refresh(call: Call, store: Store, markets: Sequence[Market] = MARKETS) -> list[Refresh]:
    """Once the node's self-test passed, land each bound account's records."""
    if not self_test_passed(call):
        return []
    return [read_and_land(call, store, account, markets) for account in bound_accounts(call)]


def said(found: Refresh) -> str:
    """One plain line for a refresh of one account."""
    if found.refused is not None:
        return f"records: the node did not read account {found.account}'s records ({found.refused})"
    counts = {
        outcome: sum(item.outcome == outcome for item in found.landed)
        for outcome in ("landed", "unchanged", "refused")
    }
    line = (
        f"records: account {found.account}, {counts['landed']} landed on main,"
        f" {counts['unchanged']} unchanged"
    )
    refused = [item.why for item in found.landed if item.outcome == "refused"]
    return line + (f", {len(refused)} refused ({'; '.join(refused)})" if refused else "")


class VenueRecords:
    """The daily refresh beside the records job: every `every_s` it reads each bound account's
    records again and lands what changed. A node that is not running, or not self-tested, lands
    nothing; one bad round never ends the loop."""

    def __init__(
        self,
        call: Call,
        store: Store,
        *,
        every_s: float = REFRESH_S,
        markets: Sequence[Market] = MARKETS,
    ) -> None:
        self.call = call
        self.store = store
        self.every_s = every_s
        self.markets = markets

    def round(self) -> list[Refresh]:
        return refresh(self.call, self.store, self.markets)

    async def run(self) -> None:
        while True:
            await asyncio.sleep(self.every_s)
            try:
                for found in await asyncio.to_thread(self.round):
                    print(said(found), file=sys.stderr)
            except Exception as error:  # one bad round never ends the loop
                print(
                    f"records: a refresh failed: {type(error).__name__}: {error}", file=sys.stderr
                )
