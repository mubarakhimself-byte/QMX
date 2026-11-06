"""The MIS's configuration on This PC: name the source that holds each admitted market's bars.

The MIS publishes nothing until something calls its `configure` operation, and a call that leaves
`source` out reads under the instrument record's venue. The bars do not live there: a download
writes them under the source that downloaded them, so the call is accepted and every round
publishes zero readings with no error (p34-2). This file is that caller.

Every `instrument` item on the Library's `main` is a market the MIS reads. The market-data door
says which source holds its `bar-m1` bars, and a market no source holds is configured without a
source, so the MIS's `status` names it instead of it going quiet. The op id is the fingerprint of
the market list, so a pass over an unchanged universe answers its first answer and writes nothing.

It runs on This PC only, beside the records refresh and on the same cadence: a record that lands
later is configured at the next pass, and one bad pass never ends the loop.
"""

from __future__ import annotations

import asyncio
import sys
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, cast

from pydantic import JsonValue
from qmf.core import fingerprint, is_refusal
from qmf.data.series import BAR_KIND
from qmx_apps.errors import AppError, Document
from qmx_library.port import JsonObject, LibraryRefused
from qmx_library.principal import MAIN, Principal
from qmx_library.store import Store

from qmx_host.market_data import MarketDoor, SeriesInfo

if TYPE_CHECKING:
    from qmx_apps.supervisor import Supervisor

__all__ = [
    "BAR_VARIANTS",
    "MIS_APP",
    "Attempt",
    "Call",
    "Market",
    "MisConfigure",
    "arguments",
    "instruments",
    "markets",
    "mis_call",
]

MIS_APP: Final = "mis"
"""The app id this job configures."""
BAR_VARIANTS: Final = ("mid", "bid", "")
"""The `bar-m1` side the MIS reads, in the order it tries them (`mis_core.BAR_VARIANTS`)."""
OPERATOR: Final = Principal("operator")
"""The principal this job reads the Library as: a read, never a write."""

type Call = Callable[[str, Mapping[str, object]], Mapping[str, object]]
"""One MIS operation through the supervisor: its answer, `{ok, value}` or a refusal."""


@dataclass(frozen=True, slots=True)
class Market:
    """One market the MIS reads: the instrument record's snapshot and where its bars live."""

    market_id: str
    instrument: JsonObject
    source: str | None
    """The store's source for this symbol's `bar-m1` bars, or None when no source holds any."""


@dataclass(frozen=True, slots=True)
class Attempt:
    """One pass of this job: the markets it named and the MIS's answer to the configure."""

    named: tuple[Market, ...]
    answer: Mapping[str, object]

    def said(self) -> str:
        """One plain line for the host's log."""
        if not self.named:
            return "mis: no instrument records on main yet; nothing to configure"
        if self.answer.get("ok") is not True:
            return (
                f"mis: the configure was refused: {self.answer.get('code')}:"
                f" {self.answer.get('message')}"
            )
        value = cast("Mapping[str, object]", self.answer.get("value") or {})
        bare = sum(1 for market in self.named if market.source is None)
        return f"mis: {value.get('configured')} markets configured, {bare} without bars"


def mis_call(apps: Supervisor) -> Call:
    """The MIS's operations through the supervisor; a call the supervisor refuses reads as the
    MIS's refusal."""

    def call(operation: str, arguments: Mapping[str, object]) -> Mapping[str, object]:
        try:
            called = apps.call(MIS_APP, operation, cast("Document", dict(arguments)))
        except AppError as error:
            return {"ok": False, "code": error.code, "message": str(error)}
        return cast("Mapping[str, object]", called.get("result") or {})

    return call


def instruments(store: Store) -> list[tuple[str, JsonObject]]:
    """Every `instrument` record on `main`, by item, in item order."""
    found: list[tuple[str, JsonObject]] = []
    for item, object_id in store.heads_on(MAIN):
        try:
            view = store.get(OPERATOR, object_id)
        except LibraryRefused:
            continue
        if view.kind == "instrument":
            found.append((item, view.fields))
    return found


def markets(store: Store, door: MarketDoor | None) -> tuple[Market, ...]:
    """Every admitted market with the source of the store's bars for its symbol, by market id.

    A record whose fields do not carry what the MIS parses is named on stderr and left out, so one
    broken record never stops the markets the rest name. With no door the store cannot be read,
    no source is known, and every market is bare."""
    series = () if door is None else _series(door)
    found: list[Market] = []
    for item, fields in instruments(store):
        read = _read(fields)
        if read is None:
            print(f"mis: the record {item} does not hold the fields the MIS reads", file=sys.stderr)
            continue
        market_id, symbol, snapshot = read
        found.append(Market(market_id, snapshot, _source(symbol, series)))
    return tuple(sorted(found, key=lambda market: market.market_id))


def arguments(named: Sequence[Market]) -> JsonObject:
    """`configure`'s arguments: the markets, and an op id that is the fingerprint of the list."""
    entries: list[JsonValue] = []
    for market in named:
        entry: JsonObject = {"market_id": market.market_id, "instrument": market.instrument}
        if market.source is not None:
            entry["source"] = market.source
        entries.append(entry)
    made = fingerprint({"markets": entries})
    if is_refusal(made):
        raise ValueError(f"the market list has no fingerprint: {made.category.value}")
    return {"op_id": made.value.value, "markets": entries}


class MisConfigure:
    """The MIS's configuration on This PC, on the records refresh cadence (p34-2)."""

    def __init__(
        self,
        call: Call,
        store: Store,
        door: MarketDoor | None,
        *,
        every_s: float,
        started: threading.Event | None = None,
    ) -> None:
        self.call = call
        self.store = store
        self.door = door
        self.every_s = every_s
        self.started = started
        """Set when the first-party apps finished starting; the first pass waits for it."""

    def round(self) -> Attempt:
        """Name every admitted market's source and configure the MIS with them."""
        named = markets(self.store, self.door)
        if not named:
            return Attempt((), {"ok": True, "value": {"configured": 0, "refused": []}})
        return Attempt(named, self.call("configure", arguments(named)))

    async def run(self) -> None:
        """Configure after the apps start, then again each `every_s`. One bad pass is named and
        the loop carries on; a pass with nothing to configure says so in plain words."""
        started = self.started
        if started is not None:
            await asyncio.to_thread(started.wait)
        while True:
            try:
                print(self.round().said(), file=sys.stderr)
            except Exception as error:  # one bad pass never ends the loop
                print(f"mis: a configure failed: {type(error).__name__}: {error}", file=sys.stderr)
            await asyncio.sleep(self.every_s)


def _series(door: MarketDoor) -> tuple[SeriesInfo, ...]:
    """The store's series, or none when the door cannot list them (a refusal is named)."""
    listed = door.instruments()
    if is_refusal(listed):
        print(
            f"mis: the market store did not list its series: {listed.category.value}",
            file=sys.stderr,
        )
        return ()
    return listed.value


def _source(symbol: str, series: Sequence[SeriesInfo]) -> str | None:
    """The source whose `bar-m1` bars the MIS reads for `symbol`, or None when none holds any.

    The MIS reads `mid`, else `bid`, else the bare variant; among sources the same order and then
    the source's name pick one, so the same store always names the same source."""
    found = [
        row
        for row in series
        if row.subject == symbol and row.kind == BAR_KIND and row.variant in BAR_VARIANTS
    ]
    if not found:
        return None
    return min(found, key=lambda row: (BAR_VARIANTS.index(row.variant), row.source)).source


def _read(fields: Mapping[str, object]) -> tuple[str, str, JsonObject] | None:
    """The market id, symbol and snapshot the MIS parses, or None when the record lacks them."""
    market_id = fields.get("market_id")
    venue = fields.get("venue")
    symbol = fields.get("symbol")
    klass = fields.get("class")
    digits = fields.get("digits")
    data_levels = fields.get("data_levels")
    held = cast("Mapping[str, object]", data_levels) if isinstance(data_levels, dict) else {}
    levels = held.get("levels")
    if (
        not isinstance(market_id, str)
        or not market_id
        or not isinstance(venue, str)
        or not venue
        or not isinstance(symbol, str)
        or not symbol
        or not isinstance(klass, str)
        or not klass
        or isinstance(digits, bool)
        or not isinstance(digits, int)
        or digits < 0
        or not isinstance(levels, list)
        or not all(isinstance(level, int) for level in cast("list[object]", levels))
    ):
        return None
    snapshot: JsonObject = {
        "venue": venue,
        "symbol": symbol,
        "class": klass,
        "digits": digits,
        "data_levels": {"levels": cast("list[object]", levels)},
    }
    pip = fields.get("pip")
    size = cast("Mapping[str, object]", pip).get("size") if isinstance(pip, dict) else None
    if isinstance(size, str) and size:
        snapshot["pip"] = {"size": size}
    return market_id, symbol, snapshot
