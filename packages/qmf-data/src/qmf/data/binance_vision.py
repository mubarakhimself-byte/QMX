"""Binance's public bulk files: every file is checked against its own checksum first (W14).

`data.binance.vision` publishes one zip per dataset per day and a `.CHECKSUM` beside it. The
whole point of the bulk path is that a download can be proved complete without a second
opinion, so a file whose bytes do not hash to the checksum the bucket published beside it is
refused here, before a single row is decoded. A refused file is never a month with fewer
rows.

Three datasets land as two series kinds (DATA-PLAN DR6). `trades` and `aggTrades` are both
trade prints and land as `trades`; `bookDepth` and `bookTicker` describe the book and land as
`book`. A dataset whose rows a reader cannot name is refused rather than guessed:

============  ==========================  ==========================
dataset       kind                        columns
============  ==========================  ==========================
trades        trades                      ``t``, ``price``, ``volume``
aggTrades     trades                      ``t``, ``price``, ``volume``
bookDepth     book                        ``t``, ``value``, ``volume``
bookTicker    book                        ``t``, ``value``, ``volume``
============  ==========================  ==========================

Time is int64 epoch milliseconds and a crypto price is an int64 scaled by
:data:`CRYPTO_PRICE_SCALE` (eight decimals, read through :class:`decimal.Decimal` so no binary
float touches it). A tie separates two datasets of one kind: ``aggTrades`` lands as variant
``aggTrades`` and ``bookDepth`` as variant ``depth``, so one dataset never overwrites another's
partition.

Stdlib only.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Final, TypeAlias

from qmf.core import Ok, Result, is_refusal
from qmf.data.series import BOOK_COLUMNS, BOOK_KIND, TRADES_COLUMNS, TRADES_KIND
from qmf.data.store.refusals import invalid_input, policy_rejection, storage_failure

__all__ = [
    "BINANCE_VISION_SOURCE",
    "BUCKET",
    "COLUMNS",
    "CRYPTO_PRICE_SCALE",
    "DATASETS",
    "KIND_BOOK",
    "KIND_TRADES",
    "BulkFile",
    "Reader",
    "bucket_path",
    "decode_rows",
    "kind_for",
    "month_files",
    "parse_checksum",
    "variant_for",
    "verify_checksum",
]

BUCKET: Final[str] = "https://data.binance.vision/data"
"""The public bucket root; a file's path follows `/data/<market>/daily/<dataset>/...`."""

BINANCE_VISION_SOURCE: Final[str] = "binance"
"""The provenance noun of every series a Binance bulk download writes."""

KIND_TRADES: Final[str] = TRADES_KIND
KIND_BOOK: Final[str] = BOOK_KIND
"""The two series kinds a bulk file lands as, named once by the store's kind registry (DR6)."""

CRYPTO_PRICE_SCALE: Final[int] = 100_000_000
"""Eight decimals: the finest a Binance symbol trades, as a scaled integer."""

DATASETS: Final[dict[str, str]] = {
    "trades": KIND_TRADES,
    "aggTrades": KIND_TRADES,
    "bookDepth": KIND_BOOK,
    "bookTicker": KIND_BOOK,
}
"""Each dataset the bucket serves, and the series kind its rows land as."""

VARIANTS: Final[dict[str, str]] = {
    "trades": "",
    "aggTrades": "aggTrades",
    "bookDepth": "depth",
    "bookTicker": "ticker",
}
"""The variant that keeps two datasets of one kind apart in the partition key."""

COLUMNS: Final[dict[str, tuple[str, ...]]] = {
    KIND_TRADES: TRADES_COLUMNS,
    KIND_BOOK: BOOK_COLUMNS,
}
"""The typed columns of a kind's partition, read from the store's own kind rule (DR6).

One definition, in `qmf.data.series`: the decoder and the door's re-streaming writer therefore
agree by construction, which is what a commit requires.
"""

Reader: TypeAlias = Callable[[str], Result[bytes]]
"""Fetches one URL's bytes. The download script wires HTTPS; a test wires a mapping."""

NS_PER_MS: Final[int] = 1_000_000
_DAY: Final = timedelta(days=1)


def _clean(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def kind_for(dataset: object) -> Result[str]:
    """The series kind a dataset lands as, or a refusal naming the datasets there are."""
    token = _clean(dataset)
    if token is None or token not in DATASETS:
        return invalid_input(
            "dataset",
            "a Binance bulk download names one of: " + ", ".join(sorted(DATASETS)),
            given=repr(dataset),
        )
    return Ok(DATASETS[token])


def variant_for(dataset: object) -> Result[str]:
    """The variant that keeps this dataset's partition apart from its kind's other dataset."""
    token = _clean(dataset)
    if token is None or token not in VARIANTS:
        return invalid_input(
            "dataset",
            "a Binance bulk download names one of: " + ", ".join(sorted(VARIANTS)),
            given=repr(dataset),
        )
    return Ok(VARIANTS[token])


@dataclass(frozen=True, slots=True)
class BulkFile:
    """One day's zip in the bucket, with the checksum file published beside it."""

    dataset: str
    symbol: str
    day: date
    path: str
    checksum_path: str

    @property
    def name(self) -> str:
        return self.path.rsplit("/", 1)[-1]


def bucket_path(
    dataset: str,
    symbol: str,
    day: date,
    *,
    market: str = "spot",  # mock-data-scan: allow
) -> BulkFile:
    """Where the bucket keeps one day of one dataset, and its checksum.

    The bucket names a daily file `<symbol>-<dataset>-<date>.zip` under
    `/data/<market>/daily/<dataset>/<symbol>/`, and publishes `<file>.CHECKSUM` beside it.
    """
    name = f"{symbol}-{dataset}-{day.isoformat()}.zip"
    folder = f"{BUCKET}/{market}/daily/{dataset}/{symbol}"
    return BulkFile(
        dataset=dataset,
        symbol=symbol,
        day=day,
        path=f"{folder}/{name}",
        checksum_path=f"{folder}/{name}.CHECKSUM",
    )


def parse_checksum(text: object) -> Result[str]:
    """The sha256 hex inside a bucket `.CHECKSUM` file.

    The bucket's own file is `sha256:<hex>  <name>`; an openssl-style line
    (`SHA256 (name) = <hex>`) and a bare `<hex>` are read too, because the older files carry
    them. Bytes are decoded as UTF-8 first, because a reader hands back what the bucket sent.
    Anything else is invalid input, never a checksum that happens to match.
    """
    raw = bytes(text).decode("utf-8", "replace") if isinstance(text, (bytes, bytearray)) else text
    body = _clean(raw)
    if body is None:
        return invalid_input(
            "checksum", "a checksum file carries a sha256 digest", given=repr(text)
        )
    first = body.splitlines()[0].strip()
    for candidate in (
        first.split("=", 1)[-1].strip(),
        first.split()[0] if first.split() else "",
    ):
        token = candidate.removeprefix("sha256:").removeprefix("SHA256:").strip().lower()
        if len(token) == 64 and all(char in "0123456789abcdef" for char in token):
            return Ok(token)
    return invalid_input(
        "checksum",
        "a checksum file's first line carries a 64-character sha256 digest",
        given=first[:120],
    )


def verify_checksum(data: object, checksum_text: object, *, name: str = "") -> Result[bytes]:
    """The file's bytes when they hash to the published checksum, else a refusal.

    A mismatch is a policy refusal, not a retry: the bucket served a file that is not the file
    it published a digest for, so the month is not landed from it. The refusal names the file
    and both digests so a log says which day was refused.
    """
    if not isinstance(data, (bytes, bytearray)):
        return invalid_input(
            "data", "a bulk file's bytes are what the checksum is compared with", given=repr(data)
        )
    expected = parse_checksum(checksum_text)
    if is_refusal(expected):
        return expected
    actual = hashlib.sha256(bytes(data)).hexdigest()
    if actual != expected.value:
        return policy_rejection(
            "checksum",
            "a Binance bulk file did not hash to the checksum published beside it, so the "
            "file is refused rather than read as a month with fewer rows",
            file=name,
            published=expected.value,
            actual=actual,
        )
    return Ok(bytes(data))


def _csv_lines(payload: bytes, *, name: str) -> Result[list[list[str]]]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return invalid_input("csv", "a bulk CSV is UTF-8 text", file=name)
    return Ok([line.split(",") for line in text.splitlines() if line.strip()])


def _unzip(payload: bytes, *, name: str) -> Result[bytes]:
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            csv_names = [item for item in archive.namelist() if item.endswith(".csv")]
            if len(csv_names) != 1:
                return invalid_input(
                    "zip",
                    "a Binance daily zip holds exactly one CSV",
                    file=name,
                    found=csv_names,
                )
            return Ok(archive.read(csv_names[0]))
    except zipfile.BadZipFile:
        return invalid_input("zip", "a Binance daily file is a zip", file=name)


def _scaled_price(text: str, *, name: str) -> Result[int]:
    try:
        return Ok(int(Decimal(text) * CRYPTO_PRICE_SCALE))
    except (InvalidOperation, ValueError):
        return invalid_input(
            "price", "a trade print's price is a decimal", file=name, given=text[:40]
        )


def _timestamp_ms(text: str, *, name: str) -> Result[int]:
    token = text.strip()
    if token.isdigit():
        value = int(token)
        return Ok(value if value > 100_000_000_000 else value * 1000)
    try:
        return Ok(int(datetime.fromisoformat(token.replace("Z", "+00:00")).timestamp() * 1000))
    except ValueError:
        return invalid_input(
            "t",
            "a trade print's time is epoch milliseconds or an ISO instant",
            file=name,
            given=token[:40],
        )


def _header_index(lines: list[list[str]], wanted: Mapping[str, tuple[str, ...]]) -> dict[str, int]:
    """The column index of each wanted name in a header line, by any of its spellings."""
    found: dict[str, int] = {}
    for index, cell in enumerate(lines[0]):
        name = cell.strip().lower()
        for key, spellings in wanted.items():
            if key not in found and name in spellings:
                found[key] = index
    return found


def _row_by_position(dataset: str, cells: list[str], *, name: str) -> Result[tuple[object, ...]]:
    """One CSV line decoded by the position the bucket's dataset documents."""
    try:
        if dataset in ("trades", "aggTrades"):
            stamp = cells[4] if dataset == "trades" else cells[5]
            price = _scaled_price(cells[1], name=name)
            if is_refusal(price):
                return price
            moment = _timestamp_ms(stamp, name=name)
            if is_refusal(moment):
                return moment
            return Ok((moment.value, price.value, float(cells[2])))
        return invalid_input(
            "dataset",
            "a book dataset's rows are read by column name, because its positions differ "
            "between the bucket's files",
            file=name,
            given=dataset,
        )
    except (IndexError, ValueError):
        return invalid_input(
            "row", "a bulk CSV line carries every column its dataset names", file=name, row=cells
        )


def decode_rows(
    dataset: object, payload: object, *, name: str = ""
) -> Result[tuple[tuple[object, ...], ...]]:
    """One day's CSV as typed rows for its kind's partition.

    A trade print is `(time_ms, scaled price, size)`; a book level is
    `(time_ms, depth, notional)`. The rows come back in file order, which the bucket writes in
    time order, and a row that does not parse refuses the whole file: a day is landed whole or
    not at all.
    """
    token = _clean(dataset)
    if token is None or token not in DATASETS:
        return invalid_input(
            "dataset",
            "a bulk CSV names one of: " + ", ".join(sorted(DATASETS)),
            given=repr(dataset),
        )
    if not isinstance(payload, (bytes, bytearray)):
        return invalid_input("payload", "a bulk CSV is bytes", given=repr(type(payload)))
    lines = _csv_lines(bytes(payload), name=name)
    if is_refusal(lines):
        return lines
    rows = lines.value
    if not rows:
        return Ok(())
    header = [cell.strip().lower() for cell in rows[0]]
    named = token in ("bookDepth", "bookTicker")
    index: dict[str, int] = {}
    if named:
        index = _header_index(
            rows,
            {
                "t": ("timestamp", "time", "transact_time"),
                "value": ("percentage", "depth", "value"),
                "volume": ("notional", "volume", "qty"),
            },
        )
        if set(index) != {"t", "value", "volume"}:
            return invalid_input(
                "header",
                "a book bulk file carries a header naming its time, level and notional",
                file=name,
                header=header,
            )
        body = rows[1:]
    else:
        body = rows[1:] if header and not header[0].isdigit() else rows
    decoded: list[tuple[object, ...]] = []
    for cells in body:
        if named and index:
            try:
                moment = _timestamp_ms(cells[index["t"]], name=name)
                if is_refusal(moment):
                    return moment
                decoded.append(
                    (moment.value, float(cells[index["value"]]), float(cells[index["volume"]]))
                )
            except (IndexError, ValueError):
                return invalid_input(
                    "row",
                    "a book bulk line carries its time, level and notional",
                    file=name,
                    row=cells,
                )
            continue
        row = _row_by_position(token, cells, name=name)
        if is_refusal(row):
            return row
        decoded.append(row.value)
    return Ok(tuple(decoded))


def month_files(
    reader: Reader,
    dataset: str,
    symbol: str,
    year: int,
    month: int,
    *,
    market: str = "spot",  # mock-data-scan: allow
) -> Result[tuple[tuple[datetime, tuple[tuple[object, ...], ...]], ...]]:
    """Every day of one month, checked and decoded, in date order.

    Each day is fetched with its checksum, verified, unzipped and decoded; the first refusal
    stops the month, because a month built from the days that happened to work is a month with
    a hole nobody recorded. A day the bucket does not serve (a delisting, a holiday with no
    prints) answers storage failure and stops it too: the caller reports the day.
    """
    if year < 1970 or not 1 <= month <= 12:
        return invalid_input(
            "month", "a bulk month is a real month from 1970", given=f"{year}-{month}"
        )
    if symbol.strip() == "":
        return invalid_input("symbol", "a bulk download names its symbol", given=repr(symbol))
    start = date(year, month, 1)
    end = date(year + (month == 12), month % 12 + 1, 1)
    found: list[tuple[datetime, tuple[tuple[object, ...], ...]]] = []
    day = start
    while day < end:
        bulk = bucket_path(dataset, symbol, day, market=market)
        zipped = reader(bulk.path)
        if is_refusal(zipped):
            return zipped
        checksum = reader(bulk.checksum_path)
        if is_refusal(checksum):
            return checksum
        try:
            verified = verify_checksum(zipped.value, checksum.value, name=bulk.name)
            if is_refusal(verified):
                return verified
            csv_bytes = _unzip(verified.value, name=bulk.name)
            if is_refusal(csv_bytes):
                return csv_bytes
            rows = decode_rows(dataset, csv_bytes.value, name=bulk.name)
            if is_refusal(rows):
                return rows
            found.append(
                (
                    datetime(day.year, day.month, day.day, tzinfo=timezone.utc),
                    rows.value,
                )
            )
        except OSError as exc:
            return storage_failure(
                "could not read a bulk file", context={"file": bulk.name, "error": str(exc)}
            )
        day += _DAY
    return Ok(tuple(found))
