"""Top up a crypto series' recent days through CCXT and land the month through the door.

CCXT is the fallback for the days a bulk file is not published yet: it reaches the exchange's
own public API for the last day or two of one-minute bars. The bars land as the `bar-m1` kind
with variant `trade` (the exchange's trade-built bars, not a one-sided quote series), which is a
kind the store already has: a bar month freezes on the provider's checksum and takes a re-fetch
when it does not arrive.

The run claims its partition key, checks free disk, keeps a heartbeat on its own thread, and
hands the staged month to the door's `commit`. One price side per run is the source's slot; a
trade-built bar series has one side and says so in its variant.
"""

import json
import os
import shutil
import sys
import threading
import tomllib
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from qmf.core import is_refusal
from qmf.data.series import SeriesKey
from qmf.data.store.engines.typed import BAR_COLUMNS, TypedWriter
from qmx_host.market_data import MarketDoor, Placement
from qmx_library.cards import Partition, SeriesCard, card_fields

from qmx_engine.workers.zones import home_of

FAILURE = "[QMX_FAILURE]"
DEFAULT_FLOOR_GB = 3.0
DEFAULT_PRICE_SCALE = 8
KIND = "bar-m1"
VARIANT = "trade"


def fail(why: str) -> None:
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


def month_of(text: str) -> tuple[int, int]:
    try:
        year, month = (int(part) for part in text.split("-"))
    except ValueError:
        fail(f"the month {text!r} is not YYYY-MM")
    if not 1 <= month <= 12:
        fail(f"the month {text!r} is not a real month")
    return year, month


def scaled(value: object, scale: int) -> int:
    try:
        return int(Decimal(str(value)) * (10**scale))
    except InvalidOperation, ValueError:
        fail(f"a bar's number {value!r} is not a decimal")


def heartbeat(shared: Path, state: dict[str, object]) -> threading.Event:
    stop = threading.Event()

    def tick() -> None:
        target = shared / "logs" / "download-ccxt.json"
        while not stop.wait(10.0):
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                state["at"] = datetime.now(UTC).isoformat()
                target.write_text(json.dumps(state), encoding="utf-8")
            except OSError:
                pass

    threading.Thread(target=tick, name="heartbeat-ccxt", daemon=True).start()
    return stop


def door_place(home: Path, data: dict[str, object]) -> tuple[Path, Placement]:
    """`[data] root` and `placement`, by default the host door's own `<home>/market` on This PC."""
    root = Path(str(data.get("root") or home / "market"))
    return root, Placement(str(data.get("placement") or Placement.PC))


def claim(root: Path, key_text: str) -> Path | None:
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


def page_limit(exchange: Any) -> int | None:
    """The exchange's own declared most bars per request, or None to let the exchange choose."""
    try:
        limit: object = exchange.features["spot"]["fetchOHLCV"]["limit"]
    except AttributeError, KeyError, TypeError:
        return None
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        return None
    return limit


def fetch_bars(
    exchange: Any, symbol: str, timeframe: str, start_ms: int, end_ms: int
) -> list[list[Any]]:
    """Every bar in `[start_ms, end_ms)`, paged by the exchange's own declared limit."""
    page = {} if (limit := page_limit(exchange)) is None else {"limit": limit}
    bars: list[list[Any]] = []
    cursor = start_ms
    while cursor < end_ms:
        try:
            batch = exchange.fetch_ohlcv(symbol, timeframe, since=cursor, **page)
        except Exception as error:  # the exchange's own refusals reach us as exceptions
            fail(f"{exchange_name} refused the read at {cursor}: {type(error).__name__}: {error}")
        fresh = [row for row in batch if cursor <= int(row[0]) < end_ms]
        if not fresh:
            break
        bars.extend(fresh)
        cursor = max(int(row[0]) for row in fresh) + 60_000
    return bars


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
exchange_name = str(source.get("exchange") or "").strip()
symbol = str(source.get("symbol") or "").strip()
if exchange_name == "" or symbol == "":
    fail("the source definition names no exchange and symbol")
year, month = month_of(str(source.get("month") or ""))
timeframe = str(source.get("timeframe") or "1m")
scale = int(source.get("price_scale") or DEFAULT_PRICE_SCALE)
try:
    import ccxt
except ImportError:
    fail("ccxt is not installed on this machine, so the recent-days top-up cannot run")
library = getattr(ccxt, exchange_name, None)
if library is None:
    fail(f"ccxt knows no exchange named {exchange_name!r}")
shared = Path(os.environ["QMX_WORK_SHARED"])
home = home_of(shared)
settings_file = home / "settings.toml"
settings = tomllib.loads(settings_file.read_text("utf-8")) if settings_file.is_file() else {}
data = settings.get("data") if isinstance(settings.get("data"), dict) else {}
root, placement = door_place(home, data)
key = SeriesKey.try_create(exchange_name, symbol.replace("/", ""), KIND, year, month, VARIANT)
if is_refusal(key):
    fail(f"the partition key was refused: {key.context}")
claim_path = claim(root, key.value.text)
if claim_path is None:
    print(json.dumps({"status": "claimed", "key": key.value.text}))
    raise SystemExit(0)
stop = heartbeat(shared, {"key": key.value.text, "bars": 0})
try:
    opened = MarketDoor.open(root, data, placement=placement)
    if is_refusal(opened):
        fail(f"the market-data door did not open: {opened.context}")
    door = opened.value
    start_ms = key.value.start_ns // 1_000_000
    end_ms = key.value.end_ns // 1_000_000
    exchange = library({"enableRateLimit": True})
    rows: list[tuple[object, ...]] = [
        (
            int(moment),
            scaled(opened_price, scale),
            scaled(high, scale),
            scaled(low, scale),
            scaled(close, scale),
            float(volume),
        )
        for moment, opened_price, high, low, close, volume in fetch_bars(
            exchange, symbol, timeframe, start_ms, end_ms
        )
    ]
    if not rows:
        print(json.dumps({"status": "empty", "key": key.value.text}))
        raise SystemExit(0)
    staging = root / "staging"
    staged = staging / exchange_name / symbol.replace("/", "") / KIND / VARIANT
    staged = staged / f"{year:04d}-{month:02d}.parquet"
    staged.parent.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(staged.parent).free / (1024**3)
    floor = float(data.get("disk_floor_gb") or DEFAULT_FLOOR_GB)
    if free < floor:
        fail(
            f"the partition keeps the disk below its floor: {free:.1f} GB free, {floor:g} GB floor"
        )
    TypedWriter(staged, key.value.text, BAR_COLUMNS).add(rows).finish()
    landed = door.commit([staged], staging=staging, born_on=placement)
    if is_refusal(landed):
        fail(f"the door refused the commit: {landed.context}")
    receipt = landed.value[0]
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
        source=exchange_name,
        subject=symbol.replace("/", ""),
        kind=KIND,
        variant=VARIANT,
        licence=str(source.get("licence") or "exchange-public-api"),
        world="live",
        redownloadable=True,
        quality={
            "bars": "trade-built bars from the exchange's public API, not a one-sided quote series",
            "timeframe": timeframe,
            "price_scale": scale,
            "topup": "recent days only; a bulk file replaces this month when it is published",
        },
    )
    cards = Path(os.environ.get("QMX_WORK") or ".") / "library" / "cards"
    card_path = cards / f"{card.series.replace('/', '_')}.json"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(json.dumps(card_fields(card, partitions), indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "landed",
                "key": key.value.text,
                "rows": receipt.rows,
                "frozen": receipt.frozen,
                "fingerprint": receipt.fingerprint,
                "exchange": exchange_name,
            },
            sort_keys=True,
        )
    )
finally:
    stop.set()
    claim_path.unlink(missing_ok=True)
