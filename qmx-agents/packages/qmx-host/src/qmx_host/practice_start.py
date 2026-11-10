"""Start a practice world from nothing: the shipped month's bars in an empty market store, and the
instrument records the canary reads, landed on `main` (RC-17, slice 5).

A first run has no broker. `practice_start` copies `qmn/src/qmn/app/practice_bars` into the
market store as source `practice`, one `bar-m1` piece per 15-minute bar inside its own bucket, and
lands QML's shipped instrument records on `main` through `qmx_host.venue_records.land`, the one
path a record takes onto `main`. Promote then reads them as it reads a node's own records.

Nothing here overwrites. The bars commit idempotently, because the same rows again land nothing,
and a record is landed only where `main` holds none for its venue and symbol, so a folder that
already holds a broker's records keeps them.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

from pydantic import JsonValue
from qmf.core import is_refusal
from qmf.data.series import SeriesKey
from qmf.data.store.engines.typed import BAR_COLUMNS, TypedWriter
from qmx_apps.supervisor import MARKET_STORE
from qmx_library.principal import MAIN, state_ref
from qmx_tools.unit_check import shipped_records

from qmx_host.market_data import MarketDoor
from qmx_host.venue_records import Landed, Record, land

if TYPE_CHECKING:
    from qmx_library.store import Store

PRACTICE: Final = "practice"
"""The market store's source for the bars QMX ships, and what a run asks for by `source`."""
DEFAULT_BARS: Final = (
    Path(__file__).resolve().parents[5] / "qmn" / "src" / "qmn" / "app" / "practice_bars"
)
"""The shipped month, in the checkout QMX runs from."""
STAGING: Final = "staging"
"""Where a month is written before the door commits it, as the host writes its own runs."""
BAR: Final = "bar-m1"
"""The series kind a 15-minute month is saved under: one piece per bar, inside the bar's bucket."""
PIECE_MS: Final = 14 * 60_000
"""Where a 15-minute bar's one `bar-m1` piece sits: the last minute of its 900-second bucket, so
the piece ends where the bar closes and the roll-up rebuilds the bar's own OHLC."""
NOT_ON_MAIN: Final = frozenset({"source", "conversions"})
"""The shipped record's two keys the Library's `instrument` kind does not hold: the label that says
it ships with QMX, and the conversion map, empty here because a USD quote in a USD account is rate
1 with no lookup (AD-10)."""
_NAME: Final = re.compile(
    r"^(?P<symbol>[a-z0-9]+)-m15-(?P<side>bid|ask)-(?P<start>\d{4}-\d{2}-\d{2})"
    r"-(?P<end>\d{4}-\d{2}-\d{2})\.csv$"
)
PRICES: Final = ("open", "high", "low", "close")


class Refused(Exception):
    """Why a practice world cannot start, by name: a bar file the month does not read, a store that
    will not open, a commit the door refuses."""


@dataclass(frozen=True, slots=True)
class Started:
    """What `practice_start` put in place: the source, the months now in the store, the series they
    landed under, and each shipped record's landing, in the file's order."""

    source: str
    months: tuple[str, ...]
    series: tuple[str, ...]
    instruments: tuple[Landed, ...]


def practice_start(home: Path, store: Store, *, bars: Path | None = None) -> Started:
    """Fill `home`'s market store with the shipped month under `practice`, and land the shipped
    instrument records on `main` where it holds none for their venue and symbol."""
    folder = DEFAULT_BARS if bars is None else bars
    door = MarketDoor.open(home / MARKET_STORE, {})
    if is_refusal(door):
        raise Refused(f"the market store does not open: {door.context.get('reason')}")
    series, months = _bars_in(door.value, folder, home / STAGING)
    found = land(
        store,
        [record for venue, symbol, record in _records() if not _held(store, venue, symbol)],
    )
    return Started(PRACTICE, tuple(sorted(set(months))), tuple(series), tuple(found))


def _bars_in(door: MarketDoor, folder: Path, staging: Path) -> tuple[list[str], list[str]]:
    """Commit every pair of month files under `practice`, and answer the series and the months."""
    series: list[str] = []
    months: list[str] = []
    staged: list[Path] = []
    for bid in sorted(folder.glob("*-m15-bid-*.csv")):
        name = _NAME.match(bid.name)
        if name is None:
            raise Refused(
                f"{bid.name} is not a month QMX ships; a bar file is "
                "symbol-m15-side-YYYY-MM-DD-YYYY-MM-DD.csv"
            )
        ask = bid.with_name(bid.name.replace("-bid-", "-ask-"))
        if not ask.is_file():
            raise Refused(f"{bid.name} has no ask file beside it: {ask.name} is missing")
        sides = [_month(bid), _month(ask)]
        if [stamp for stamp, _ in sides[0]] != [stamp for stamp, _ in sides[1]]:
            raise Refused(f"{bid.name} and {ask.name} do not cover the same bars")
        scales = {_digits(prices) for side in sides for _, prices in side}
        if len(scales) != 1:
            raise Refused(f"{bid.name} and {ask.name} are not written at one price scale")
        scale = scales.pop()
        symbol = str(name["symbol"])
        for side, rows in zip(("bid", "ask"), sides, strict=True):
            for month, path, text in _by_month(door, symbol, side, rows, scale, staging):
                staged.append(path)
                series.append(text)
                months.append(month)
    if not staged:
        raise Refused(f"{folder} holds no month of bars")
    landed = door.commit(staged, staging=staging)
    if is_refusal(landed):
        raise Refused(f"the market store refuses the month: {landed.context.get('reason')}")
    return series, months


def _month(path: Path) -> list[tuple[int, list[str]]]:
    """One side's rows: the timestamp and the four prices as the file writes them."""
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = [
                (int(row["timestamp"]), [row[name] for name in PRICES])
                for row in csv.DictReader(handle)
            ]
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise Refused(f"{path.name} does not read as a month of bars: {error}") from error
    if not rows:
        raise Refused(f"{path.name} holds no bars")
    return rows


def _digits(prices: list[str]) -> int:
    return max(len(price.partition(".")[2]) for price in prices)


def _by_month(
    door: MarketDoor,
    symbol: str,
    side: str,
    rows: list[tuple[int, list[str]]],
    scale: int,
    staging: Path,
) -> list[tuple[str, Path, str]]:
    """Stage `rows` as one `bar-m1` file per month, state each series' price scale, and answer
    `(month, path, series)` for each."""
    grouped: dict[str, list[tuple[int, list[str]]]] = {}
    for stamp, prices in rows:
        at = datetime.fromtimestamp(stamp // 1000, UTC)
        grouped.setdefault(f"{at.year:04d}-{at.month:02d}", []).append((stamp, prices))
    found: list[tuple[str, Path, str]] = []
    for month, group in sorted(grouped.items()):
        year, number = (int(part) for part in month.split("-"))
        key = SeriesKey.try_create(PRACTICE, symbol.upper(), BAR, year, number, side)
        if is_refusal(key):
            raise Refused(f"{symbol} {month} does not make a series: {key.context.get('reason')}")
        path = staging / PRACTICE / symbol.upper() / BAR / side / f"{month}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        writer = TypedWriter(path, key.value.text, BAR_COLUMNS)
        writer.add(
            sorted(
                (stamp + PIECE_MS, *(int(Decimal(price).scaleb(scale)) for price in prices), 0.0)
                for stamp, prices in group
            )
        )
        writer.finish()
        stated = door.state_scale(key.value.series, scale)
        if is_refusal(stated):
            raise Refused(
                f"{key.value.series} cannot state its price scale: {stated.context.get('reason')}"
            )
        found.append((month, path, key.value.series))
    return found


def _records() -> list[tuple[str, str, Record]]:
    """QML's shipped instrument records as the Library's `instrument` kind holds them."""
    found: list[tuple[str, str, Record]] = []
    for document in shipped_records():
        venue, symbol = str(document["venue"]), str(document["symbol"])
        facts = {
            key: cast("JsonValue", value)
            for key, value in document.items()
            if key not in NOT_ON_MAIN
        }
        item = "instrument-" + re.sub(r"[^a-z0-9]+", "-", f"{venue}-{symbol}".lower()).strip("-")
        found.append(
            (
                venue,
                symbol,
                Record(
                    "instrument",
                    {"venue": venue, "symbol": symbol},
                    item,
                    f"{symbol} at {venue}",
                    facts,
                    {},
                ),
            )
        )
    return found


def _held(store: Store, venue: str, symbol: str) -> bool:
    """Whether `main` holds a live instrument record for this venue and symbol. An item only on a
    draft or a run ref holds nothing there, and an archived item is withdrawn, so its replacement
    binds alone (Library AD-6)."""
    for object_id in store.with_field("instrument", "symbol", symbol):
        view = store.get(store.engine, object_id)
        if view.fields.get("venue") != venue or view.fields.get("symbol") != symbol:
            continue
        head = store.head(view.item, MAIN)
        if head is None:
            continue
        state = store.head(view.item, state_ref(view.item))
        if state is None or state[0] != "archived":
            return True
    return False
