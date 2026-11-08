"""Download one month of one Binance bulk dataset and land it through the door.

Binance publishes one zip per dataset per day and a `.CHECKSUM` beside it, so a month can be
proved complete without a second opinion: every file is checked before a row is read, and a
file that does not hash to its checksum stops the month. `trades` and `aggTrades` land as the
`trades` kind, `bookDepth` and `bookTicker` as `book`; the dataset that is not the kind's
default travels in the variant, so two datasets never share one partition.

The run claims its partition key, checks free disk before the write, keeps a heartbeat on its
own thread, and hands the staged month to the door's `commit`. A month is landed whole or not
at all: the days that happened to work are never written as if they were the month.

Each day's file is stamp-checked before it lands (LD-03): its unit is read from the magnitude of
its first and last stamps and converted to UTC milliseconds, so the spot files Binance writes in
microseconds from 1 January 2025 land on the same clock as the months before. A change of unit
from the previous file, or from the month the series last landed (kept beside the claims), is a
seam on the card, and so is a change of a book dataset's cadence (LD-04). The month is counted
against open time, on the source definition's `calendar` or else `crypto-24x7@1`, and an empty
open hour holds it open until the source definition lists it in `confirmed_empty` (LD-01).
"""

import json
import os
import shutil
import sys
import threading
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from qmf.core import Ok, is_refusal
from qmf.data.binance_vision import (
    BINANCE_VISION_SOURCE,
    COLUMNS,
    kind_for,
    month_files,
    variant_for,
)
from qmf.data.importers.quality import check_month, confirmed_hours, open_at_of
from qmf.data.importers.stamps import ClockLedger, StampCheck, card_facts
from qmf.data.series import SeriesKey
from qmf.data.store.engines.typed import TypedWriter
from qmf.data.store.refusals import storage_failure
from qmx_host.market_data import MarketDoor, Placement
from qmx_library.cards import Partition, SeriesCard, card_fields

from qmx_engine.triggers.preflight import shipped_calendars
from qmx_engine.workers.zones import home_of

FAILURE = "[QMX_FAILURE]"
USER_AGENT = "qmx-feed/1.0"
TIMEOUT_SECONDS = 60
DEFAULT_FLOOR_GB = 3.0
DEFAULT_CALENDAR = "crypto-24x7@1"


def fail(why: str) -> None:
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


def http_reader(url: str):
    """The bucket's bytes over HTTPS, with the folder taken from the file's own path."""
    request = Request(  # noqa: S310 (the bucket's own url, http or https)
        url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}
    )
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as reply:  # noqa: S310
            return Ok(reply.read())
    except HTTPError as error:
        return storage_failure(
            "the bucket answered an error", context={"url": url, "status": error.code}
        )
    except (URLError, OSError) as error:
        return storage_failure(
            "the bucket could not be read", context={"url": url, "error": str(error)}
        )


def file_reader(base: Path):
    """The same bytes from a folder, which is how a test and a seeded bucket run."""

    def read(url: str):
        marker = "data.binance.vision/"
        path = base / url.split(marker, 1)[-1] if marker in url else Path(url)
        if not path.is_file():
            return storage_failure("the bulk file is not there", context={"path": str(path)})
        return Ok(path.read_bytes())

    return read


def month_of(text: str) -> tuple[int, int]:
    try:
        year, month = (int(part) for part in text.split("-"))
    except ValueError:
        fail(f"the month {text!r} is not YYYY-MM")
    if not 1 <= month <= 12:
        fail(f"the month {text!r} is not a real month")
    return year, month


def heartbeat(shared: Path, state: dict[str, object]) -> threading.Event:
    stop = threading.Event()

    def tick() -> None:
        target = shared / "logs" / "download-binance.json"
        while not stop.wait(10.0):
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                state["at"] = datetime.now(UTC).isoformat()
                target.write_text(json.dumps(state), encoding="utf-8")
            except OSError:
                pass

    threading.Thread(target=tick, name="heartbeat-binance", daemon=True).start()
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
dataset = str(source.get("dataset") or "trades")
symbol = str(source.get("symbol") or "").strip().upper()
if symbol == "":
    fail("the source definition names no symbol")
year, month = month_of(str(source.get("month") or ""))
named_calendar = str(source.get("calendar") or "").strip()
calendar_ref = named_calendar or DEFAULT_CALENDAR
calendar = shipped_calendars().get(calendar_ref)
if named_calendar and calendar is None:
    fail(f"no shipped calendar is named {named_calendar!r}")
if calendar is None:
    calendar_ref = None
confirmed = confirmed_hours(source.get("confirmed_empty") or [])
if isinstance(confirmed, str):
    fail(f"confirmed_empty: {confirmed}")
kind = kind_for(dataset)
if is_refusal(kind):
    fail(f"the dataset was refused: {kind.context}")
variant = variant_for(dataset)
if is_refusal(variant):
    fail(f"the dataset's variant was refused: {variant.context}")
shared = Path(os.environ["QMX_WORK_SHARED"])
home = home_of(shared)
settings_file = home / "settings.toml"
settings = tomllib.loads(settings_file.read_text("utf-8")) if settings_file.is_file() else {}
data = settings.get("data") if isinstance(settings.get("data"), dict) else {}
root, placement = door_place(home, data)
key = SeriesKey.try_create(BINANCE_VISION_SOURCE, symbol, kind.value, year, month, variant.value)
if is_refusal(key):
    fail(f"the partition key was refused: {key.context}")
columns = COLUMNS[kind.value]
if tuple(key.value.rule.columns) != columns:
    fail(
        f"the store's rule for kind {kind.value!r} holds {list(key.value.rule.columns)} where "
        f"this decoder writes {list(columns)}; the door re-streams a commit through the rule's "
        "columns, so the two have to be one definition (qmf.data.series)"
    )
claim_path = claim(root, key.value.text)
if claim_path is None:
    print(json.dumps({"status": "claimed", "key": key.value.text}))
    raise SystemExit(0)
state: dict[str, object] = {"key": key.value.text, "days": 0}
stop = heartbeat(shared, state)
try:
    opened = MarketDoor.open(root, data, placement=placement)
    if is_refusal(opened):
        fail(f"the market-data door did not open: {opened.context}")
    door = opened.value
    base = str(source.get("base") or "")
    if base.startswith("file://"):
        reader = file_reader(Path(base.removeprefix("file://")))
    elif base.startswith(("http://", "https://")) or base == "":
        reader = http_reader
    else:
        reader = file_reader(Path(base))
    fetched = month_files(
        reader, dataset, symbol, year, month, market=str(source.get("market") or "spot")
    )
    if is_refusal(fetched):
        fail(f"the month was refused: {fetched.context}")
    ledger = ClockLedger(root)
    unit, cadence = ledger.before(key.value.series, year, month)
    stamps = StampCheck(cadenced=kind.value == "book", after=unit, after_cadence_ms=cadence)
    rows: list[tuple[object, ...]] = []
    for day, day_rows in fetched.value:
        checked = stamps.file(f"{symbol}-{dataset}-{day:%Y-%m-%d}", day_rows)
        if is_refusal(checked):
            fail(f"the stamps did not check: {checked.context}")
        rows.extend(checked.value)
        state["days"] = int(state["days"]) + 1
    if not rows:
        print(json.dumps({"status": "empty", "key": key.value.text}))
        raise SystemExit(0)
    report = (
        None
        if calendar is None
        else check_month(
            (int(str(row[0])) for row in rows),
            start_ms=key.value.start_ns // 1_000_000,
            end_ms=key.value.end_ns // 1_000_000,
            open_at=open_at_of(calendar),
            confirmed=confirmed,
        )
    )
    hold = None if report is None else report.hold
    staging = root / "staging"
    staged = staging / BINANCE_VISION_SOURCE / symbol / kind.value / (variant.value or "-")
    staged = staged / f"{year:04d}-{month:02d}.parquet"
    staged.parent.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(staged.parent).free / (1024**3)
    floor = float(data.get("disk_floor_gb") or DEFAULT_FLOOR_GB)
    if free < floor:
        fail(
            f"the partition keeps the disk below its floor: {free:.1f} GB free, {floor:g} GB floor"
        )
    TypedWriter(staged, key.value.text, columns).add(rows).finish()
    landed = door.commit([staged], staging=staging, born_on=placement, hold=hold)
    if is_refusal(landed):
        fail(f"the door refused the commit: {landed.context}")
    receipt = landed.value[0]
    ledger.record(key.value.series, year, month, stamps)
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
        source=BINANCE_VISION_SOURCE,
        subject=symbol,
        kind=kind.value,
        variant=variant.value,
        licence=str(source.get("licence") or "binance-public-data"),
        world="live",
        redownloadable=True,
        quality={
            "checksum": "every day's file checked against the bucket's own .CHECKSUM",
            "dataset": dataset,
            "price_scale": 100_000_000,
            "days": len(fetched.value),
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
                "checked": None if report is None else report.as_json(),
                "fingerprint": receipt.fingerprint,
                "days": len(fetched.value),
                "dataset": dataset,
            },
            sort_keys=True,
        )
    )
finally:
    stop.set()
    claim_path.unlink(missing_ok=True)
