"""Download one month of one instrument's Dukascopy ticks and land it through the door.

One run is one partition (a symbol and a month). The run claims that partition's key before
it fetches anything, so a second run on the same key writes nothing; it checks free disk before
each write; it keeps a heartbeat on its own thread so the host's Machines list shows an hour
count while the month is in flight; and it writes one row per tick carrying both price sides,
which is the ticks kind's shape.

The fetcher is QMX's own (`qmf.data.dukascopy`): probe P-DUKA failed because dukascopy-node
1.50.0 fetches nothing, and QMX's fetch agrees with the operator's old raw bi5 files on every
hour the provider served. `qmf.data.dukascopy.decode_node_csv` keeps the node's output readable
for the cross-check adapter, but the node is not what this template runs.

The provider's refusals are an operating condition, never a fact about the data: each hour
that answers is cached, a refusal is retried on a fresh connection, and an hour still refused
after its retries stops the month from landing. A refused hour is never read as an hour with
no ticks.

The volume on every row is Dukascopy's own liquidity. The card says so.

A bi5 price is a whole number at the symbol's own scale on Dukascopy: 5 digits for EURUSD, 3 for
XAUUSD and USDJPY. The rows keep the provider's integers and the card states the scale they are
at, so the source must name `price_scale`. A source with none is refused rather than guessed, and
when the source hands in Dukascopy's own `instrument` record for the symbol, its `digits` must
agree. A run given `check` (a landed series' card) fetches nothing and reports `wrong_scale` when
that card states another scale; downloading the month again lands the same rows under a card at
the right scale. The door keeps the scale a landed month or a `scale_ok` check states, because a
QMB run refuses a series with none.

Before the month lands, its stamps are checked (a bi5 tick is milliseconds from its UTC hour,
so the source clock is UTC in milliseconds) and the month is counted against its market's
`calendar`, as the source definition names it or else as the symbol implies it: a currency pair
on `fx-24x5@1`, gold and silver on `metals-24x5@1`. Any other symbol has none, and the output says
so. An hour wholly inside open time with no tick is a fetch failure until a retry and a second
source agree, so the month lands held open, unfrozen, until the source definition lists that hour
in `confirmed_empty` (LD-01). The card states the clock, the seams and the calendar.

The month's one-minute bid and ask bars land right after its ticks, under the same hold, so a run
reads them instead of millions of ticks.
"""

import http.client
import json
import os
import shutil
import sys
import threading
import time
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

from qmf.core import is_refusal
from qmf.data.dukascopy import (
    VOLUME_LIQUIDITY,
    DukascopyHourKey,
    decode_bi5_ticks,
)
from qmf.data.importers.quality import check_month, confirmed_hours, open_at_of
from qmf.data.importers.stamps import ClockLedger, StampCheck, card_facts
from qmf.data.series import SeriesKey
from qmf.data.store.engines.typed import TICK_COLUMNS, TypedWriter
from qmx_host.market_data import MarketDoor, Placement
from qmx_library.cards import Partition, SeriesCard, card_fields
from qmx_tools.derive_bars import derive_month

from qmx_engine.triggers.preflight import shipped_calendars
from qmx_engine.workers.zones import home_of

FAILURE = "[QMX_FAILURE]"
HOST = "datafeed.dukascopy.com"
USER_AGENT = "qmx-feed/1.0"
SOURCE = "dukascopy"
DEFAULT_FLOOR_GB = 3.0
HEARTBEAT_SECONDS = 10.0
METAL_CODES = frozenset({"XAU", "XAG"})
CURRENCY_CODES = frozenset(
    [
        "AUD",
        "CAD",
        "CHF",
        "CNH",
        "CZK",
        "DKK",
        "EUR",
        "GBP",
        "HKD",
        "HUF",
        "ILS",
        "JPY",
        "MXN",
        "NOK",
        "NZD",
        "PLN",
        "RON",
        "RUB",
        "SEK",
        "SGD",
        "THB",
        "TRY",
        "USD",
        "ZAR",
    ]
)
"""The currencies of Dukascopy's spot pairs, so a six-letter crypto or stock code is no pair."""


def fail(why: str) -> NoReturn:
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


def default_calendar(symbol: str) -> str | None:
    """The calendar a source naming none trades on, or None when the symbol does not imply one."""
    base, quote = symbol[:3], symbol[3:]
    if base in METAL_CODES:
        return "metals-24x5@1"
    return "fx-24x5@1" if base in CURRENCY_CODES and quote in CURRENCY_CODES else None


def scale_of(source: dict[str, object], symbol: str) -> int:
    """The digits after the point in every price Dukascopy serves for `symbol`, as the source
    names them, checked against the symbol's Dukascopy instrument record when one is handed in.
    Digits are a venue's fact (cTrader quotes gold at 2, Dukascopy at 3), so only Dukascopy's
    own record can confirm the scale."""
    scale = source.get("price_scale")
    if scale is None:
        fail(
            f"the source names no price_scale for {symbol}; Dukascopy serves each symbol at its "
            "own scale (5 for EURUSD, 3 for XAUUSD and USDJPY), so name it"
        )
    if isinstance(scale, bool) or not isinstance(scale, int) or scale < 0:
        fail(f"price_scale is the whole number of digits after the point, not {scale!r}")
    record = source.get("instrument")
    if record is None:
        return scale
    if not isinstance(record, dict):
        fail("the source's instrument is the fields of the symbol's Dukascopy instrument record")
    venue = record.get("venue")
    if venue != SOURCE:
        fail(
            f"the instrument record is for the venue {venue!r}, and a Dukascopy month's scale "
            "is checked only against Dukascopy's own record, because digits differ by venue"
        )
    if str(record.get("symbol") or "").strip().upper() != symbol:
        fail(f"the instrument record is for {record.get('symbol')!r}, not {symbol}")
    digits = record.get("digits")
    if isinstance(digits, bool) or digits != scale:
        fail(
            f"the source names price_scale {scale} for {symbol}, but its Dukascopy instrument "
            f"record states {digits!r} digits; correct whichever is wrong before a month lands"
        )
    return scale


def scale_report(card: object, symbol: str, scale: int) -> dict[str, object]:
    """A landed series' card read against the source's scale. Its months are `wrong_scale` when
    the card states any other scale, or none, so no reader takes them as good prices."""
    if not isinstance(card, dict) or card.get("source") != SOURCE or card.get("subject") != symbol:
        fail(f"check takes the dataset card of the {SOURCE} {symbol} series this source names")
    quality = card.get("quality")
    stated = quality.get("price_scale") if isinstance(quality, dict) else None
    parts = card.get("partitions") if isinstance(card.get("partitions"), list) else []
    months = [part.get("month") for part in parts if isinstance(part, dict)]
    report: dict[str, object] = {
        "status": "scale_ok",
        "series": card.get("series_key"),
        "months": months,
        "card_price_scale": stated,
        "price_scale": scale,
    }
    if isinstance(stated, bool) or stated != scale:
        report["status"] = "wrong_scale"
        report["note"] = "landed at the wrong price scale, download it again"
    return report


def month_of(text: str) -> tuple[int, int]:
    try:
        year, month = (int(part) for part in text.split("-"))
    except ValueError:
        fail(f"the month {text!r} is not YYYY-MM")
    if not 1970 <= year <= 9999 or not 1 <= month <= 12:
        fail(f"the month {text!r} is not a real month")
    return year, month


def month_hours(year: int, month: int, symbol: str) -> list[DukascopyHourKey]:
    import calendar  # noqa: PLC0415 (a month's length only)

    hours: list[DukascopyHourKey] = []
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        for hour in range(24):
            built = DukascopyHourKey.try_create(symbol, year, month - 1, day, hour)
            if is_refusal(built):
                fail(f"the hour key was refused: {built.context}")
            hours.append(built.value)
    return hours


def marker(key: DukascopyHourKey) -> str:
    return f"{key.symbol}/{key.year}/{key.month_0:02d}/{key.day:02d}/{key.hour:02d}"


class Fetch:
    """The provider's hourly files over HTTPS: one connection per thread, cached on disk.

    A refused hour is retried on a *fresh* connection, because the provider's 503 bursts come
    from a connection it has already decided about. An hour that answers is cached under the
    workflow's shared work folder, so a re-run resumes instead of re-fetching, and an hour that
    still fails after its retries is recorded in `refused` and is never handed over as empty.
    """

    RETRIES = 4
    WORKERS = 8
    TIMEOUT = 30.0

    def __init__(self, cache: Path, *, workers: int = WORKERS) -> None:
        self._cache = cache
        self._local = threading.local()
        self._lock = threading.Lock()
        self._workers = workers
        self.done = 0
        self.refused: list[str] = []

    def connection(self) -> http.client.HTTPSConnection:
        found = getattr(self._local, "connection", None)
        if found is None:
            found = http.client.HTTPSConnection(HOST, timeout=self.TIMEOUT)
            self._local.connection = found
        return found

    def forget(self) -> None:
        found = getattr(self._local, "connection", None)
        if found is not None:
            found.close()
            self._local.connection = None

    def hour(self, key: DukascopyHourKey) -> bytes | None:
        cached = self._cache / f"{marker(key)}.bi5"
        if cached.is_file():
            with self._lock:
                self.done += 1
            return cached.read_bytes()
        path = (
            f"/datafeed/{key.symbol}/{key.year}/{key.month_0:02d}/{key.day:02d}/"
            f"{key.hour:02d}h_ticks.bi5"
        )
        problem = "no attempt"
        for attempt in range(self.RETRIES):
            try:
                connection = self.connection()
                connection.request("GET", path, headers={"User-Agent": USER_AGENT})
                reply = connection.getresponse()
                body = reply.read()
                if reply.status == 200:
                    cached.parent.mkdir(parents=True, exist_ok=True)
                    cached.write_bytes(body)
                    with self._lock:
                        self.done += 1
                    return body
                if reply.status == 404:
                    with self._lock:
                        self.done += 1
                    return b""  # the provider's own convention: no ticks in that hour
                problem = f"HTTP {reply.status}"
                self.forget()
            except (OSError, http.client.HTTPException) as error:
                problem = f"{type(error).__name__}: {error}"
                self.forget()
            time.sleep(2.0 + attempt)
        with self._lock:
            self.refused.append(f"{marker(key)} ({problem})")
        return None

    def month(self, keys: list[DukascopyHourKey]) -> dict[int, bytes | None]:
        from concurrent.futures import ThreadPoolExecutor  # noqa: PLC0415

        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            bodies = list(pool.map(self.hour, keys))
        return {id(key): body for key, body in zip(keys, bodies, strict=True)}


def heartbeat(shared: Path, slug: str, state: dict[str, object]) -> threading.Event:
    """Keep one JSON reading current while the download runs, on its own thread."""
    stop = threading.Event()

    def tick() -> None:
        target = shared / "logs" / f"download-{slug}.json"
        while not stop.wait(HEARTBEAT_SECONDS):
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                state["at"] = datetime.now(UTC).isoformat()
                target.write_text(json.dumps(state), encoding="utf-8")
            except OSError:
                pass

    thread = threading.Thread(target=tick, name=f"heartbeat-{slug}", daemon=True)
    thread.start()
    return stop


def claim(root: Path, key_text: str) -> Path | None:
    """The partition's one writer: a claim file the first run creates and the rest find."""
    folder = root / ".claims"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / key_text.replace("/", "_")
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json.dumps({"pid": os.getpid(), "at": datetime.now(UTC).isoformat()}))
    return path


def door_place(home: Path, data: dict[str, object]) -> tuple[Path, Placement]:
    """`[data] root` and `placement`, by default the host door's own `<home>/market` on This PC."""
    root = Path(str(data.get("root") or home / "market"))
    return root, Placement(str(data.get("placement") or Placement.PC))


def free_disk(folder: Path, floor_gb: float) -> str:
    """Why this write may not start, or an empty string when the disk has room."""
    folder.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(folder).free / (1024**3)
    if free < floor_gb:
        return f"{free:.1f} GB free under {folder}, below the {floor_gb:g} GB floor"
    return ""


given = json.load(sys.stdin).get("in") or {}
if isinstance(given, dict) and given.get("dry_run"):
    (Path(os.environ["QMX_WORK"]) / "library" / "cards").mkdir(parents=True, exist_ok=True)
    print(
        json.dumps(
            {
                "status": "dry_run",
                "note": "nothing fetched; the source slot is read when a download runs",
            }
        )
    )
    raise SystemExit(0)
source = given.get("source") if isinstance(given, dict) else None
if not isinstance(source, dict):
    fail("the run names no source definition under `source`")
symbol = str(source.get("symbol") or "").strip().upper()
if symbol == "":
    fail("the source definition names no symbol")
scale = scale_of(source, symbol)
shared = Path(os.environ["QMX_WORK_SHARED"])
home = home_of(shared)
settings_file = home / "settings.toml"
settings = tomllib.loads(settings_file.read_text("utf-8")) if settings_file.is_file() else {}
data = settings.get("data") if isinstance(settings.get("data"), dict) else {}
root, placement = door_place(home, data)
if "check" in given:
    report = scale_report(given["check"], symbol, scale)
    if report["status"] == "scale_ok":
        checked = MarketDoor.open(root, data, placement=placement)
        if is_refusal(checked):
            fail(f"the market-data door did not open: {checked.context}")
        stated = checked.value.state_scale(str(report["series"]), scale)
        if is_refusal(stated):
            fail(f"the door did not keep the scale: {stated.context}")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0)
year, month = month_of(str(source.get("month") or ""))
named_calendar = str(source.get("calendar") or "").strip()
calendar_ref = named_calendar or default_calendar(symbol)
calendar = shipped_calendars().get(calendar_ref) if calendar_ref else None
if named_calendar and calendar is None:
    fail(f"no shipped calendar is named {named_calendar!r}")
if calendar is None:
    calendar_ref = None
confirmed = confirmed_hours(source.get("confirmed_empty") or [])
if isinstance(confirmed, str):
    fail(f"confirmed_empty: {confirmed}")
key = SeriesKey.try_create("dukascopy", symbol, "ticks", year, month)
if is_refusal(key):
    fail(f"the partition key was refused: {key.context}")
store_root = root
claim_path = claim(store_root, key.value.text)
if claim_path is None:
    print(json.dumps({"status": "claimed", "key": key.value.text}))
    raise SystemExit(0)
stop = heartbeat(shared, "dukascopy", {"key": key.value.text, "hours": 0, "of": 24 * 31})
try:
    opened = MarketDoor.open(root, data, placement=placement)
    if is_refusal(opened):
        fail(f"the market-data door did not open: {opened.context}")
    door = opened.value
    keys = month_hours(year, month, symbol)
    state = {"key": key.value.text, "hours": 0, "of": len(keys)}
    fetch = Fetch(shared / "hours")
    bodies = fetch.month(keys)
    state["hours"] = fetch.done
    if fetch.refused:
        print(
            json.dumps(
                {
                    "status": "refused",
                    "key": key.value.text,
                    "refused": fetch.refused[:20],
                    "refused_hours": len(fetch.refused),
                    "note": "an hour the provider refused is not an hour with no ticks",
                }
            )
        )
        raise SystemExit(1)
    rows: list[tuple[object, ...]] = []
    start_ns = key.value.start_ns
    for position, hour_key in enumerate(keys):
        body = bodies[id(hour_key)]
        if body is None:
            fail(f"the hour {marker(hour_key)} was not fetched")
        built = hour_key.hour_start_ns()
        if is_refusal(built):
            fail(f"the hour {marker(hour_key)} has no start: {built.context}")
        decoded = decode_bi5_ticks(body, hour_start_ns=built.value, price_scale=scale)
        if is_refusal(decoded):
            fail(f"the hour {marker(hour_key)} did not decode: {decoded.context}")
        for tick in decoded.value:
            if tick.event_time_ns < start_ns or tick.event_time_ns >= key.value.end_ns:
                continue
            rows.append(
                (
                    tick.event_time_ns // 1_000_000,
                    tick.bid_verbatim,
                    tick.ask_verbatim,
                    tick.bid_volume,
                    tick.ask_volume,
                )
            )
        state["hours"] = position + 1
    if not rows:
        print(json.dumps({"status": "empty", "key": key.value.text}))
        raise SystemExit(0)
    ledger = ClockLedger(root)
    unit, _ = ledger.before(key.value.series, year, month)
    stamps = StampCheck(after=unit)
    checked_rows = stamps.file(key.value.text, rows)
    if is_refusal(checked_rows):
        fail(f"the stamps did not check: {checked_rows.context}")
    report = (
        None
        if calendar is None
        else check_month(
            (row[0] for row in rows),
            start_ms=start_ns // 1_000_000,
            end_ms=key.value.end_ns // 1_000_000,
            open_at=open_at_of(calendar),
            confirmed=confirmed,
        )
    )
    staging = root / "staging"
    staged = staging / "dukascopy" / symbol / "ticks" / "-" / f"{year:04d}-{month:02d}.parquet"
    staged.parent.mkdir(parents=True, exist_ok=True)
    short = free_disk(staged.parent, float(data.get("disk_floor_gb") or DEFAULT_FLOOR_GB))
    if short:
        fail(f"the partition keeps the disk below its floor: {short}")
    written = TypedWriter(staged, key.value.text, TICK_COLUMNS).add(checked_rows.value).finish()
    hold = None if report is None else report.hold
    landed = door.commit([staged], staging=staging, born_on=placement, hold=hold)
    if is_refusal(landed):
        fail(f"the door refused the commit: {landed.context}")
    receipt = landed.value[0]
    ledger.record(key.value.series, year, month, stamps)
    stated = door.state_scale(key.value.series, scale)
    if is_refusal(stated):
        fail(f"the door did not keep the scale: {stated.context}")
    derived = derive_month(door, key.value.series, year, month, staging=staging, hold=hold)
    if is_refusal(derived):
        fail(f"the door did not land the month's one-minute bars: {derived.context}")
    partitions = (
        Partition(
            year=year,
            month=month,
            fingerprint=receipt.fingerprint,
            rows=receipt.rows,
            frozen=receipt.frozen,
            gaps=receipt.gaps,
        ),
    )
    card = SeriesCard(
        source="dukascopy",
        subject=symbol,
        kind="ticks",
        variant="",
        licence=str(source.get("licence") or "dukascopy-personal-use"),
        world="live",
        redownloadable=True,
        quality={
            "volume": VOLUME_LIQUIDITY,
            "volume_note": (
                "volume is Dukascopy's own liquidity on its own book, not a consolidated tape"
            ),
            "price_scale": scale,
            "hours_refused": 0,
            "checked": None if report is None else report.as_json(),
        },
    )
    cards = Path(os.environ.get("QMX_WORK") or ".") / "library" / "cards"
    card_path = cards / f"{card.series.replace('/', '_')}.json"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    fields = {**card_fields(card, partitions), **card_facts(stamps, calendar_ref)}
    card_path.write_text(json.dumps(fields, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "landed",
                "key": key.value.text,
                "rows": receipt.rows,
                "frozen": receipt.frozen,
                "held_open": hold,
                **card_facts(stamps, calendar_ref),
                **(
                    {}
                    if calendar_ref
                    else {
                        "calendar_note": f"no calendar for {symbol}, so its open hours are not "
                        "counted; name one in the source's calendar to count them"
                    }
                ),
                "checked": None if report is None else report.as_json(),
                "fingerprint": receipt.fingerprint,
                "derived": [bars.key.series for bars in derived.value],
                "hours": len(keys),
                "staged_bytes": written.bytes,
                "volume": VOLUME_LIQUIDITY,
            },
            sort_keys=True,
        )
    )
finally:
    stop.set()
    claim_path.unlink(missing_ok=True)
