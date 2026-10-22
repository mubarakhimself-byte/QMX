"""P-DUKA (W14; engine AD-68, rulings 122 and 128), premise: dukascopy-node 1.50.0,
QMX's own bi5 fetch and the old raw bi5 files agree for one month of EURUSD ticks.

Three tick sources for the month this probe pins (`2021-01`):

* the old raw files the PC already holds, `venue=FOREX/platform=CTRADER/instrument=EURUSD/
  resolution=tick/date=*/raw/NNh_ticks.bi5` (ruling 130), decoded with the repo's stdlib
  decoder;
* QMX's own fetch, `qmf.data.dukascopy.DukascopyAdapter`, over the same provider hours with
  an HTTPS transport injected here;
* dukascopy-node 1.50.0 from `D:/Tools/dukascopy-node`, one price side per run with
  `--retries` and `--retry-on-empty` on.

For each pair it compares row count, first and last tick, the bid and ask prices row for
row, and the gaps (which UTC hours carry ticks and how many). It writes only under
`D:/Temp/prb-dp/duka/` and removes that root before it exits.

    uv run --no-sync python -m scripts.probes.data.p_duka

The compare function carries its own test, because the section's Files block names no test
file: `uv run --no-sync python -m pytest scripts/probes/data/p_duka.py -n 0`.
"""

from __future__ import annotations

import csv
import http.client
import json
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from qmf.core import Instrument, Ok, Result, VenueId, is_refusal
from qmf.data.dukascopy import (
    NS_PER_HOUR,
    DukascopyAdapter,
    DukascopyHourKey,
    decode_bi5_ticks,
)
from qmf.data.ingest import SourceRequest

from scripts.probes.data import common
from scripts.probes.data.common import FAILED, PASSED, Report

PROBE = "P-DUKA"
SYMBOL = "EURUSD"
MONTH = "2021-01"
PRICE_SCALE = 5
NODE_ROOT = Path("D:/Tools/dukascopy-node")
NODE_VERSION = "1.50.0"
OLD_TICKS = Path(
    "C:/Users/Mubarak/Documents/QMX/data/raw/external-deep-history/venue=FOREX/"
    "platform=CTRADER/instrument=EURUSD/resolution=tick"
)
NS_PER_MS = 1_000_000
MS_PER_HOUR = 3_600_000


@dataclass(frozen=True, slots=True)
class TickSet:
    """One source's month of ticks: epoch-ms times and scaled bid and ask prices."""

    label: str
    t: list[int] = field(default_factory=list)
    bid: list[int] = field(default_factory=list)
    ask: list[int] = field(default_factory=list)
    seconds: float = 0.0
    error: str = ""


@dataclass(frozen=True, slots=True)
class Agreement:
    """Four comparisons between two tick sources, each with the words a row quotes."""

    label: str
    rows: str
    first: str
    last: str
    prices: str
    gaps: str

    @property
    def ok(self) -> bool:
        return all(
            part.startswith("equal")
            for part in (self.rows, self.first, self.last, self.prices, self.gaps)
        )


def month_bounds(month: str) -> tuple[date, date]:
    """First day of `YYYY-MM` and the first day of the month after it."""
    year, number = (int(part) for part in month.split("-"))
    start = date(year, number, 1)
    return start, date(year + (number == 12), number % 12 + 1, 1)


def stamp(milliseconds: int) -> str:
    moment = datetime.fromtimestamp(milliseconds / 1000, tz=UTC)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def hourly_counts(ticks: TickSet) -> dict[int, int]:
    return dict(Counter(value // MS_PER_HOUR for value in ticks.t))


def verdict(agreements: list[Agreement]) -> str:
    return PASSED if agreements and all(item.ok for item in agreements) else FAILED


def compare_ticks(label: str, left: TickSet, right: TickSet) -> Agreement:
    """Compare rows, first and last tick, prices row for row, and gaps."""
    rows = (
        f"equal ({len(left.t)})"
        if len(left.t) == len(right.t)
        else f"differ: {len(left.t)} vs {len(right.t)}"
    )
    first = _edge("first", left.t[:1], right.t[:1])
    last = _edge("last", left.t[-1:], right.t[-1:])
    counts_left, counts_right = hourly_counts(left), hourly_counts(right)
    gaps = (
        f"equal ({len(counts_left)} hours carry ticks)"
        if counts_left == counts_right
        else f"differ: {len(counts_left)} hours vs {len(counts_right)} hours carry ticks"
    )
    return Agreement(
        label=label,
        rows=rows,
        first=first,
        last=last,
        prices=_compare_prices(left, right),
        gaps=gaps,
    )


def _edge(name: str, wanted: list[int], got: list[int]) -> str:
    if not wanted or not got:
        return f"differ: {name} tick {'absent' if not wanted else stamp(wanted[0])} vs " + (
            "absent" if not got else stamp(got[0])
        )
    if wanted[0] != got[0]:
        return f"differ: {stamp(got[0])} vs {stamp(wanted[0])}"
    return f"equal {stamp(wanted[0])}"


def _compare_prices(left: TickSet, right: TickSet) -> str:
    if len(left.t) != len(right.t):
        return f"differ: {len(left.t)} prices vs {len(right.t)}"
    for side in ("bid", "ask"):
        wanted = getattr(left, side)
        got = getattr(right, side)
        for index, (want, other) in enumerate(zip(wanted, got, strict=True)):
            if want != other:
                return f"differ {side} at row {index}: {other} vs {want}"
    return f"equal (bid and ask, {len(left.t)} rows)"


class HttpsBi5Transport:
    """Dukascopy's hourly bi5 files over HTTPS, fetched ahead on a bounded thread pool.

    The adapter above asks hour by hour and owns retry policy; this owns only the bytes.
    One month of hours is prefetched, because a serial month of round trips against this
    host runs past the probe's time budget (its connection attempts also time out now and
    then, which a retry on a fresh connection clears).
    """

    HOST = "datafeed.dukascopy.com"
    USER_AGENT = "qmx-data-probe/1.0"

    def __init__(self, *, workers: int = 8, retries: int = 4, timeout: float = 40.0) -> None:
        self._workers = workers
        self._retries = retries
        self._timeout = timeout
        self._local = threading.local()
        self._pool: ThreadPoolExecutor | None = None
        self._pending: dict[int, Future[bytes]] = {}

    def prefetch(self, keys: list[DukascopyHourKey]) -> None:
        """Start every hour's download; `fetch_hour` collects one."""
        self._pool = ThreadPoolExecutor(max_workers=self._workers)
        for key in keys:
            marker = key.year * 100_000_000 + key.month_0 * 1_000_000 + key.day * 10_000 + key.hour
            if marker not in self._pending:
                self._pending[marker] = self._pool.submit(self._download, key)

    def close(self) -> None:
        if self._pool is not None:
            self._pool.shutdown(wait=True)
            self._pool = None

    def _connection(self) -> http.client.HTTPSConnection:
        connection = getattr(self._local, "connection", None)
        if connection is None:
            connection = http.client.HTTPSConnection(self.HOST, timeout=self._timeout)
            self._local.connection = connection
        return connection

    def _forget(self) -> None:
        connection = getattr(self._local, "connection", None)
        if connection is not None:
            connection.close()
            self._local.connection = None

    def _download(self, key: DukascopyHourKey) -> bytes:
        path = (
            f"/datafeed/{key.symbol}/{key.year}/{key.month_0:02d}/{key.day:02d}/"
            f"{key.hour:02d}h_ticks.bi5"
        )
        problem = "no attempt"
        for attempt in range(self._retries):
            try:
                connection = self._connection()
                connection.request(
                    "GET", path, headers={"User-Agent": self.USER_AGENT, "Accept": "*/*"}
                )
                response = connection.getresponse()
                body = response.read()
                if response.status == 200:
                    return body
                if response.status == 404:
                    return b""  # no ticks for that hour, the provider's convention
                problem = f"HTTP {response.status}"
                self._forget()
            except (OSError, http.client.HTTPException) as error:
                problem = f"{type(error).__name__}: {error}"
                self._forget()
            time.sleep(1.0 + attempt)
        raise RuntimeError(f"dukascopy {path} failed after {self._retries} tries ({problem})")

    def fetch_hour(self, key: DukascopyHourKey) -> Result[bytes]:
        marker = key.year * 100_000_000 + key.month_0 * 1_000_000 + key.day * 10_000 + key.hour
        pending = self._pending.get(marker)
        if pending is None:
            return Ok(self._download(key))
        return Ok(pending.result())


def read_old_raw(month: str) -> TickSet:
    """Decode the month's old raw bi5 files with the repo's stdlib decoder."""
    start, end = month_bounds(month)
    times: list[int] = []
    bid: list[int] = []
    ask: list[int] = []
    started = time.monotonic()
    day = start
    while day < end:
        folder = OLD_TICKS / f"date={day.isoformat()}" / "raw"
        for hour in range(24):
            path = folder / f"{hour:02d}h_ticks.bi5"
            if not path.exists():
                continue
            hour_start = datetime(day.year, day.month, day.day, hour, tzinfo=UTC)
            decoded = decode_bi5_ticks(
                path.read_bytes(),
                hour_start_ns=int(hour_start.timestamp() * 1_000_000_000),
                price_scale=PRICE_SCALE,
            )
            if is_refusal(decoded):
                raise RuntimeError(f"{path} did not decode: {decoded.context}")
            for tick in decoded.value:
                times.append(tick.event_time_ns // NS_PER_MS)
                bid.append(tick.bid_verbatim)
                ask.append(tick.ask_verbatim)
        day += timedelta(days=1)
    return TickSet(label="old-raw", t=times, bid=bid, ask=ask, seconds=time.monotonic() - started)


def manifest_rows(month: str) -> int:
    """The old collector's own record count for the month, for a cross-check."""
    start, end = month_bounds(month)
    total = 0
    day = start
    while day < end:
        manifest = OLD_TICKS / f"date={day.isoformat()}" / "_manifest.json"
        if manifest.exists():
            document = json.loads(manifest.read_text(encoding="utf-8"))
            total += int(document.get("dataset", {}).get("record_count", 0))
        day += timedelta(days=1)
    return total


def month_hour_keys(month: str) -> list[DukascopyHourKey]:
    """Every provider hour in the month, in order."""
    start, end = month_bounds(month)
    keys: list[DukascopyHourKey] = []
    day = start
    while day < end:
        for hour in range(24):
            key = DukascopyHourKey.try_create(SYMBOL, day.year, day.month - 1, day.day, hour)
            if is_refusal(key):
                raise RuntimeError(f"hour key refused: {key.context}")
            keys.append(key.value)
        day += timedelta(days=1)
    return keys


def read_qmx_fetch(month: str) -> TickSet:
    """Fetch the month through QMX's own bi5 adapter, one day per bounded window."""
    start, end = month_bounds(month)
    venue = VenueId.try_create("dukascopy")
    if is_refusal(venue):
        raise RuntimeError(f"the venue token was refused: {venue.context}")
    instrument = Instrument.try_create(venue.value, SYMBOL)
    if is_refusal(instrument):
        raise RuntimeError(f"EURUSD did not build an Instrument: {instrument.context}")
    transport = HttpsBi5Transport()
    transport.prefetch(month_hour_keys(month))
    adapter = DukascopyAdapter(
        transport,
        instruments={SYMBOL: instrument.value},
        price_scales={SYMBOL: PRICE_SCALE},
    )
    times: list[int] = []
    bid: list[int] = []
    ask: list[int] = []
    day = start
    started = time.monotonic()
    try:
        while day < end:
            day_start = datetime(day.year, day.month, day.day, tzinfo=UTC)
            window_start = int(day_start.timestamp() * 1_000_000_000)
            request = SourceRequest(
                source="dukascopy",
                bounds={
                    "symbol": SYMBOL,
                    "start_ns": window_start,
                    "end_ns": window_start + 24 * NS_PER_HOUR,
                },
            )
            fetched = adapter.fetch(request)
            if is_refusal(fetched):
                raise RuntimeError(f"QMX fetch refused {day}: {fetched.context}")
            for record in fetched.value:
                times.append(record.event_time // NS_PER_MS)
                bid.append(_scaled(record.bid, "bid"))
                ask.append(_scaled(record.ask, "ask"))
            day += timedelta(days=1)
    finally:
        transport.close()
    return TickSet(label="qmx-fetch", t=times, bid=bid, ask=ask, seconds=time.monotonic() - started)


def _scaled(block: object, side: str) -> int:
    """The scaled integer inside one CT-15 price block; never a binary float (DEC-0105)."""
    if not isinstance(block, dict):
        raise RuntimeError(f"{side} is {type(block).__name__}, expected a scaled price block")
    return int(block["verbatim"])


def read_node(month: str) -> TickSet:
    """Run dukascopy-node once per price side and read its CSVs back."""
    start, end = month_bounds(month)
    node = shutil.which("node")
    entry = NODE_ROOT / "node_modules" / "dukascopy-node" / "dist" / "cli" / "index.js"
    if node is None or not entry.exists():
        return TickSet(label="duka-node", error=f"node or {entry} is missing")
    installed = str(json.loads((entry.parents[2] / "package.json").read_text("utf-8"))["version"])
    folder = common.scratch_folder("duka") / "node"
    started = time.monotonic()
    problems: list[str] = []
    sides: dict[str, dict[int, int]] = {}
    for side in ("bid", "ask"):
        run_folder = folder / side
        command = [
            node,
            str(entry),
            "-i",
            SYMBOL.lower(),
            "-from",
            start.isoformat(),
            "-to",
            end.isoformat(),
            "-t",
            "tick",
            "-p",
            side,
            "-v",
            "-f",
            "csv",
            "-dir",
            str(run_folder),
            "-r",
            "3",
            "-re",
            "--batch-size",
            "24",
            "--batch-pause",
            "250",
        ]
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=900, check=False
        )
        if completed.returncode != 0:
            said = (completed.stdout + completed.stderr).strip().splitlines()
            problems.append(f"{side} run exit {completed.returncode}: {said[-1] if said else ''}")
        sides[side] = _read_node_files(run_folder, side)
    seconds = time.monotonic() - started
    if problems:
        return TickSet(
            label="duka-node",
            seconds=seconds,
            error=f"dukascopy-node {installed}: " + "; ".join(problems),
        )
    moments = sorted(set(sides["bid"]) | set(sides["ask"]))
    if not moments:
        return TickSet(label="duka-node", seconds=seconds, error="dukascopy-node wrote no rows")
    missing = [value for value in moments if value not in sides["bid"]]
    if missing:
        return TickSet(
            label="duka-node",
            seconds=seconds,
            error=f"dukascopy-node bid pass lacks {len(missing)} timestamps the ask pass has",
        )
    return TickSet(
        label="duka-node",
        t=moments,
        bid=[sides["bid"][value] for value in moments],
        ask=[sides["ask"][value] for value in moments],
        seconds=seconds,
    )


def _read_node_files(folder: Path, side: str) -> dict[int, int]:
    """Merge a side's CSVs into `epoch-ms -> scaled price`."""
    prices: dict[int, int] = {}
    if not folder.exists():
        return prices
    for path in sorted(folder.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            names = reader.fieldnames or []
            for row in reader:
                moment = _node_stamp(names, row)
                price = _node_price(row, side)
                if moment is not None and price is not None:
                    prices[moment] = price
    return prices


def _node_stamp(names: list[str], row: dict[str, str]) -> int | None:
    key = next((name for name in names if name and "time" in name.lower()), None)
    if key is None:
        return None
    raw = (row.get(key) or "").strip()
    if raw.isdigit():
        value = int(raw)
        return value if value > 100_000_000_000 else value * 1000
    try:
        return int(datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return None


def _node_price(row: dict[str, str], side: str) -> int | None:
    for name, value in row.items():
        if name and name.lower() == side:
            return round(float(value) * 10**PRICE_SCALE)
    for name, value in row.items():
        if name and "price" in name.lower():
            return round(float(value) * 10**PRICE_SCALE)
    return None


def main() -> int:
    report = Report(probe=PROBE)
    report.numbers["month"] = MONTH
    report.numbers["symbol"] = SYMBOL
    report.numbers["node_pin"] = _node_version()
    try:
        old = read_old_raw(MONTH)
        qmx = read_qmx_fetch(MONTH)
        node = read_node(MONTH)
        for ticks in (old, qmx, node):
            report.numbers[f"{ticks.label}_rows"] = len(ticks.t)
            report.numbers[f"{ticks.label}_seconds"] = f"{ticks.seconds:.1f}"
            if ticks.error:
                report.note(f"{ticks.label}: {ticks.error}")
        report.numbers["old_raw_manifest_rows"] = manifest_rows(MONTH)
        pairs = [
            compare_ticks("old-raw vs qmx-fetch", old, qmx),
            compare_ticks("old-raw vs duka-node", old, node),
            compare_ticks("qmx-fetch vs duka-node", qmx, node),
        ]
        for pair in pairs:
            report.note(
                f"{pair.label}: rows {pair.rows}; first {pair.first}; last {pair.last}; "
                f"prices {pair.prices}; gaps {pair.gaps}"
            )
            if not pair.ok:
                report.fail(f"{pair.label} does not agree")
        return report.render()
    finally:
        common.drop_scratch()


def _node_version() -> str:
    manifest = NODE_ROOT / "node_modules" / "dukascopy-node" / "package.json"
    if not manifest.exists():
        return "absent"
    return str(json.loads(manifest.read_text(encoding="utf-8"))["version"])


def test_compare_ticks_passes_equal_lists_and_fails_a_shifted_price() -> None:
    """The plan's unit box: compare two equal tick lists, then one with a shifted price."""
    base = TickSet(
        label="old-raw",
        t=[1_600_000_000_000, 1_600_000_001_000, 1_600_000_002_000],
        bid=[108_000, 108_010, 108_020],
        ask=[108_012, 108_022, 108_032],
    )
    same = TickSet(label="qmx-fetch", t=list(base.t), bid=list(base.bid), ask=list(base.ask))
    equal = compare_ticks("old-raw vs qmx-fetch", base, same)
    if verdict([equal]) != PASSED or equal.prices != "equal (bid and ask, 3 rows)":
        raise AssertionError(f"equal lists gave {verdict([equal])}: {equal}")
    shifted = TickSet(
        label="duka-node",
        t=list(base.t),
        bid=[108_000, 108_011, 108_020],
        ask=list(base.ask),
    )
    changed = compare_ticks("old-raw vs duka-node", base, shifted)
    if verdict([changed]) != FAILED:
        raise AssertionError(f"a shifted price gave {verdict([changed])}")
    if changed.prices != "differ bid at row 1: 108011 vs 108010":
        raise AssertionError(f"the shifted price was reported as {changed.prices}")
    if changed.rows != "equal (3)":
        raise AssertionError(f"row counts should still agree, got {changed.rows}")


if __name__ == "__main__":
    sys.exit(main())
