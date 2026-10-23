"""P-MDREAD-TIMES: read times for one month of ticks and every year of m1 the store holds.

The measure probe of the data round (55 row 20). It reads the same spans from four places and
records the seconds each took: the PC's cache, the server's disk, the server's door over the
tailnet, and a fetch from the bucket. The spans are one month of ticks and, for every year of m1
the store holds, that year's twelve month partitions.

    uv run --no-sync python scripts/probes/data/p_mdread_times.py `
        --pc-store D:/Qmx/library/market `
        --door-url http://qmx-server:8420 `
        --bucket-target qmxr2:/price `
        --ticks-month 2021-01 `
        --report D:/Temp/dr3c-times.json

PASS when every read the probe ran finished and its numbers are recorded. FAIL when a read is
killed or does not finish, which is the plan's FAIL line. A source the run was not given is
recorded as `not run` with its reason and is not a failure: the PC rows run on the PC and the
server's disk row runs on the server, so one machine rarely holds all four.

The door row is a `POST /api/data/read` with `purpose = exploration` and a `data_scope` of `*`,
which is how a remote caller reaches the primary's door. A read past the door's handle threshold
comes back as a handle, so its rows are written to a JSONL file under `--scratch`; the probe
removes that file and reports its size. The bearer is taken from the environment variable
`--door-token-env` names, and is never printed, written or recorded. The bucket row is an
`rclone copy` of the span's month folders followed by a local read of what landed, because the
bucket's layout is the store's layout; the rclone config path is passed to rclone, never read.

The PC's cache, the server's disk and a fetched copy are read at the partition level: the state
file names the partition, and the row count decodes every batch of it, so the number is a real
read and not a metadata call.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pyarrow.parquet as pq
from pyarrow import compute
from qmf.core import is_refusal
from qmf.data.series import OPEN_NAME, SeriesKey, SeriesStore

from scripts.probes.data.common import Report

PROBE = "P-MDREAD-TIMES"
BATCH = 65_536
DEFAULT_M1: Final[str] = "dukascopy/EURUSD/bar-m1/-"
DEFAULT_TICKS: Final[str] = "dukascopy/EURUSD/ticks/-"


@dataclass(frozen=True, slots=True)
class Span:
    """One read: a series, the months it covers, and the half-open window it asks for."""

    series: str
    label: str
    months: tuple[tuple[int, int], ...]

    @property
    def first_ns(self) -> int:
        year, month = self.months[0]
        return _month_start(year, month)

    @property
    def end_ns(self) -> int:
        year, month = self.months[-1]
        return _month_start(year + 1, 1) if month == 12 else _month_start(year, month + 1)


@dataclass(frozen=True, slots=True)
class Reading:
    """One source's read of one span: what it covered and how long it took."""

    source: str
    span: str
    months: int
    rows: int
    seconds: float | None
    note: str = ""
    detail: dict[str, object] = field(default_factory=dict[str, object])

    @property
    def measured(self) -> bool:
        return self.seconds is not None

    def as_json(self) -> dict[str, object]:
        return {
            "source": self.source,
            "span": self.span,
            "months": self.months,
            "rows": self.rows,
            "seconds": self.seconds,
            "note": self.note,
            **self.detail,
        }


def _month_start(year: int, month: int) -> int:
    return int(datetime(year, month, 1, tzinfo=UTC).timestamp()) * 1_000_000_000


def _key(series: str, year: int, month: int) -> SeriesKey:
    source, subject, kind, variant = series.split("/")
    built = SeriesKey.try_create(
        source, subject, kind, year, month, "" if variant == "-" else variant
    )
    if is_refusal(built):
        raise ValueError(f"{series}/{year:04d}-{month:02d} is not a key")
    return built.value


def _partition(store: SeriesStore, key: SeriesKey) -> Path | None:
    """The file a store holds for one month, or None when it holds none."""
    state = store.state(key)
    if state is None:
        return None
    folder = store.folder(key)
    return folder / (f"{state.fingerprint}.parquet" if state.frozen else OPEN_NAME)


def _rows_in(path: Path) -> int:
    """Decode every row group of one partition and count its rows.

    Every value of every column is touched, so the number is the time to read and decode the
    partition and not the time to read its footer. Measured on one month of ticks (574,368 rows,
    4 MB): a footer-only read is 20 ms and this is 27 ms, against 10 ms for `read_table` on a warm
    cache, so the figure is a streaming decode and the four sources are compared like for like.
    """
    handle = pq.ParquetFile(path)
    rows = 0
    for batch in handle.iter_batches(batch_size=BATCH):
        for index in range(batch.num_columns):
            _ = compute.sum(batch.column(index))
        rows += batch.num_rows
    return rows


def years_in(store_root: Path, series: str) -> dict[int, tuple[tuple[int, int], ...]]:
    """Which years of a series a store holds, each with the months it holds of that year."""
    folder = store_root / "series" / series
    held: dict[int, list[tuple[int, int]]] = {}
    if not folder.is_dir():
        return {}
    for month in sorted(folder.iterdir()):
        if not month.is_dir() or not (month / "state.json").is_file():
            continue
        parts = month.name.split("-")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            continue
        held.setdefault(int(parts[0]), []).append((int(parts[0]), int(parts[1])))
    return {year: tuple(months) for year, months in sorted(held.items())}


def local_reading(root: Path, source: str, span: Span) -> Reading:
    """Read a span from a store on this machine, in the door's own partition layout."""
    store = SeriesStore(root / "series")
    started = time.perf_counter()
    rows = 0
    months = 0
    for year, month in span.months:
        path = _partition(store, _key(span.series, year, month))
        if path is None or not path.is_file():
            return Reading(
                source,
                span.label,
                months,
                rows,
                None,
                f"not run: {span.series} {year}-{month:02d} is not in this store",
            )
        rows += _rows_in(path)
        months += 1
    return Reading(source, span.label, months, rows, round(time.perf_counter() - started, 3))


def door_reading(url: str, token: str, span: Span, into: Path) -> Reading:
    """Read a span through the server's door over the tailnet, as a remote caller does."""
    body = json.dumps(
        {
            "series": span.series,
            "start_ns": span.first_ns,
            "end_ns": span.end_ns,
            "purpose": "exploration",
            "data_scope": ["*"],
            "into": str(into),
        }
    ).encode("utf-8")
    request = urllib.request.Request(  # noqa: S310 (the URL is given on the command line)
        f"{url.rstrip('/')}/api/data/read",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=3600) as answer:  # noqa: S310 (the URL is given)
            served = json.loads(answer.read())
    except (urllib.error.URLError, TimeoutError, OSError) as refused:
        return Reading("door", span.label, 0, 0, None, f"failed: {refused}")
    seconds = round(time.perf_counter() - started, 3)
    handle = served.get("handle")
    if isinstance(handle, dict):
        rows = int(handle.get("rows", 0))
        detail: dict[str, object] = {
            "handle_bytes": Path(str(handle.get("path", ""))).stat().st_size
            if Path(str(handle.get("path", ""))).is_file()
            else 0
        }
        months = len(served.get("months", []))
        return Reading("door", span.label, months, rows, seconds, "served as a handle", detail)
    rows = len(served.get("data", []))
    return Reading(
        "door", span.label, len(served.get("months", [])), rows, seconds, "served as rows"
    )


def find_rclone() -> str | None:
    """An explicit override, then PATH, then the path the plan installs it at."""
    for candidate in (
        os.environ.get("QMX_RCLONE"),
        shutil.which("rclone"),
        "D:/Tools/rclone/rclone.exe",
    ):
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def bucket_reading(
    binary: str, config: Path | None, target: str, span: Span, scratch: Path
) -> Reading:
    """Fetch a span's month folders from the bucket, then read what landed."""
    started = time.perf_counter()
    fetched = 0
    for year, month in span.months:
        remote = f"{target.rstrip('/')}/{span.series}/{year:04d}-{month:02d}"
        local = scratch / span.series / f"{year:04d}-{month:02d}"
        local.mkdir(parents=True, exist_ok=True)
        command = [
            binary,
            *(["--config", str(config)] if config else []),
            "copy",
            remote,
            str(local),
        ]
        done = subprocess.run(command, capture_output=True, check=False)
        if done.returncode != 0:
            return Reading(
                "bucket",
                span.label,
                0,
                fetched,
                None,
                f"failed: rclone copy exited {done.returncode}: "
                f"{done.stderr.decode('utf-8', 'replace').strip()[-300:]}",
            )
        fetched += 1
    rows = 0
    for path in sorted(scratch.glob(f"{span.series}/*/*.parquet")):
        rows += _rows_in(path)
    seconds = round(time.perf_counter() - started, 3)
    return Reading("bucket", span.label, fetched, rows, seconds, "fetched then read")


def spans_for(
    store_root: Path | None, ticks_series: str, ticks_month: str, m1_series: str
) -> tuple[Span, ...]:
    """The one month of ticks and every year of m1 the store holds, in time order."""
    found: list[Span] = []
    year, month = (int(part) for part in ticks_month.split("-"))
    found.append(Span(ticks_series, f"{year:04d}-{month:02d}", ((year, month),)))
    if store_root is not None:
        for year, months in years_in(store_root, m1_series).items():
            found.append(Span(m1_series, f"{year:04d}", months))
    return tuple(found)


def main() -> int:
    parser = argparse.ArgumentParser(description=PROBE)
    parser.add_argument("--pc-store", type=Path, default=None, help="the PC cache's store root")
    parser.add_argument("--server-store", type=Path, default=None, help="the server's store root")
    parser.add_argument(
        "--discover", type=Path, default=None, help="the store to read the m1 years from"
    )
    parser.add_argument("--door-url", default="", help="the server door's base URL")
    parser.add_argument(
        "--door-token-env",
        default="QMX_DOOR_TOKEN",
        help="the environment variable holding the door's bearer; its value is never printed",
    )
    parser.add_argument("--bucket-target", default="", help="the bucket remote and path")
    parser.add_argument("--rclone-config", type=Path, default=None, help="the rclone config path")
    parser.add_argument("--ticks-series", default=DEFAULT_TICKS)
    parser.add_argument("--ticks-month", default="2021-01")
    parser.add_argument("--m1-series", default=DEFAULT_M1)
    parser.add_argument("--scratch", type=Path, default=Path("D:/Temp/prb-dp"), help="scratch root")
    parser.add_argument("--report", type=Path, default=None, help="the JSON report to write")
    parser.add_argument("--keep", action="store_true", help="leave the scratch root behind")
    arguments = parser.parse_args()

    discover = arguments.discover or arguments.pc_store or arguments.server_store
    report = Report(PROBE)
    scratch = arguments.scratch / "mdread-times"
    scratch.mkdir(parents=True, exist_ok=True)
    readings: list[Reading] = []
    try:
        if discover is None:
            report.fail("no --pc-store, --server-store or --discover, so no span can be read")
            return report.render()
        spans = spans_for(
            discover, arguments.ticks_series, arguments.ticks_month, arguments.m1_series
        )
        for span in spans:
            for source, root in (
                ("pc-cache", arguments.pc_store),
                ("server-disk", arguments.server_store),
            ):
                if root is None:
                    readings.append(
                        Reading(source, span.label, 0, 0, None, "not run: no store given")
                    )
                    continue
                readings.append(local_reading(root, source, span))
            if not arguments.door_url:
                readings.append(Reading("door", span.label, 0, 0, None, "not run: no --door-url"))
            else:
                token = os.environ.get(arguments.door_token_env, "")
                if not token:
                    readings.append(
                        Reading(
                            "door",
                            span.label,
                            0,
                            0,
                            None,
                            f"not run: the environment has no {arguments.door_token_env}",
                        )
                    )
                else:
                    into = scratch / "handle" / span.label
                    into.mkdir(parents=True, exist_ok=True)
                    readings.append(door_reading(arguments.door_url, token, span, into))
                    shutil.rmtree(into, ignore_errors=True)
            binary = find_rclone() if arguments.bucket_target else None
            if not arguments.bucket_target:
                readings.append(
                    Reading("bucket", span.label, 0, 0, None, "not run: no bucket target")
                )
            elif binary is None:
                readings.append(
                    Reading("bucket", span.label, 0, 0, None, "not run: rclone is absent")
                )
            else:
                readings.append(
                    bucket_reading(
                        binary, arguments.rclone_config, arguments.bucket_target, span, scratch
                    )
                )
    finally:
        if not arguments.keep:
            shutil.rmtree(scratch, ignore_errors=True)

    for reading in readings:
        if reading.note.startswith("failed"):
            report.fail(f"{reading.source} {reading.span}: {reading.note}")
        if reading.measured:
            report.numbers[f"{reading.source} {reading.span}"] = (
                f"{reading.months} months, {reading.rows} rows, {reading.seconds}s"
                + (f" ({reading.note})" if reading.note else "")
            )
        else:
            report.note(f"{reading.source} {reading.span}: {reading.note}")
    measure = [reading for reading in readings if reading.measured]
    report.numbers["readings"] = f"{len(measure)} measured of {len(readings)}"
    if not measure:
        report.fail("no source read a span, so nothing was measured")
    if arguments.report is not None:
        arguments.report.parent.mkdir(parents=True, exist_ok=True)
        arguments.report.write_text(
            json.dumps([reading.as_json() for reading in readings], indent=2, sort_keys=True)
            + "\n",
            "utf-8",
        )
        report.note(f"report: {arguments.report.as_posix()}")
    return report.render()


if __name__ == "__main__":
    sys.exit(main())
