"""P-MDREAD (read-back): one month of EURUSD ticks written by the new writer reads back row
for row, a second write gives the same fingerprint and no new file, and peak RAM is recorded
for a week and for a month (W9; DATA-PLAN DR3A lane 2).

Run it on the server against the raw-backup copy, or on the PC against a handful of the old
raw hour files:

    cd qmx-agents
    uv run --no-sync python ../scripts/probes/data/p_mdread.py \
        --raw-root /srv/qmx/data/raw-backup --subject EURUSD --month 2021-01

PASS when every written row reads back equal to the source and the two writes agree; FAIL
when a row differs, a fingerprint changes, more than one file lands, or the month's peak RAM
is near four times the week's.

Scratch goes under `D:/Temp/prb-dp/mdread` (or `QMX_PROBE_SCRATCH`) and is removed.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pyarrow.parquet as pq
from qmf.core import is_refusal
from qmf.data.importers.dukascopy_raw import RawTicks, raw_tick_rows
from qmf.data.series import SeriesKey, SeriesStore
from qmf.data.store.engines.typed import TICK_COLUMNS, write_in_child

from scripts.probes.data import common
from scripts.probes.data.common import Report

PROBE = "P-MDREAD"
NS_PER_DAY = 86_400 * 1_000_000_000
BATCH = 65_536


def peak_mb() -> float:
    """This process's peak working set so far, in MB."""
    if sys.platform == "win32":
        import ctypes  # noqa: PLC0415 (only the PC needs the Windows call)
        from ctypes import wintypes  # noqa: PLC0415

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        info = ctypes.windll.kernel32.K32GetProcessMemoryInfo  # type: ignore[attr-defined]
        info.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        info.restype = wintypes.BOOL
        process = ctypes.windll.kernel32.GetCurrentProcess()  # type: ignore[attr-defined]
        if not info(process, ctypes.byref(counters), counters.cb):
            raise OSError("K32GetProcessMemoryInfo failed")
        return round(counters.PeakWorkingSetSize / (1024 * 1024), 1)
    import resource  # noqa: PLC0415 (only the server needs the POSIX call)

    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)


def compare(path: Path, files: object, report: Report) -> None:
    """Read the file back in batches and compare it row for row with the source."""
    source = raw_tick_rows(files)  # type: ignore[arg-type]
    reader = pq.ParquetFile(path)
    seen = 0
    for batch in reader.iter_batches(batch_size=BATCH):
        for row in batch.to_pylist():
            want = next(source, None)
            if want is None:
                report.fail(f"the file holds more rows than the source at row {seen}")
                return
            got = tuple(row[name] for name in TICK_COLUMNS)
            if got != want:
                report.fail(f"row {seen}: read {got!r}, wrote {want!r}")
                return
            seen += 1
    if next(source, None) is not None:
        report.fail(f"the source holds more rows than the file after row {seen}")
        return
    report.numbers["rows_read_back"] = seen


def main() -> int:
    parser = argparse.ArgumentParser(description=PROBE)
    parser.add_argument(
        "--raw-root",
        default="D:/QMX-worktrees/qma-ship/data/raw-backup",
        help="the directory holding <subject>/<year>/<month>/<day>/<hour>h_ticks.bi5",
    )
    parser.add_argument("--subject", default="EURUSD")
    parser.add_argument("--month", default="2021-01", help="YYYY-MM")
    parser.add_argument("--max-hours", type=int, default=0, help="0 means every hour of the month")
    arguments = parser.parse_args()
    year, month = (int(part) for part in arguments.month.split("-"))
    report = Report(PROBE)
    raw = RawTicks(Path(arguments.raw_root), arguments.subject, year, month)
    hours = raw.hours()
    if not hours:
        report.fail(
            f"no hour files of {arguments.month} under {arguments.raw_root} for "
            f"{arguments.subject}: point --raw-root at the raw-backup copy"
        )
        return report.render()
    if arguments.max_hours:
        hours = hours[: arguments.max_hours]
    week = tuple(entry for entry in hours if entry[0] < hours[0][0] + 7 * NS_PER_DAY)
    built = SeriesKey.try_create("dukascopy", arguments.subject, "ticks", year, month)
    if is_refusal(built):
        report.fail(f"the series key was refused: {built.context}")
        return report.render()
    key = built.value
    scratch = common.scratch_folder("mdread")
    try:
        week_file = scratch / "week.parquet"
        month_file = scratch / "month.parquet"
        again_file = scratch / "month-again.parquet"
        write = partial(write_in_child, hole_bounds=key.rule.hole_bounds)
        report.numbers["hours"] = len(hours)
        week_written = write(week_file, key.text, TICK_COLUMNS, partial(raw_tick_rows, week))
        report.numbers["week_rows"] = week_written.rows
        report.numbers["week_file_mb"] = round(week_written.bytes / (1024 * 1024), 1)
        week_peak = peak_mb()
        report.numbers["week_peak_mb"] = week_peak
        month_written = write(month_file, key.text, TICK_COLUMNS, partial(raw_tick_rows, hours))
        report.numbers["month_rows"] = month_written.rows
        report.numbers["month_file_mb"] = round(month_written.bytes / (1024 * 1024), 1)
        month_peak = peak_mb()
        report.numbers["month_peak_mb"] = month_peak
        report.numbers["fingerprint"] = month_written.fingerprint
        compare(month_file, hours, report)
        again = write(again_file, key.text, TICK_COLUMNS, partial(raw_tick_rows, hours))
        report.numbers["second_fingerprint"] = again.fingerprint
        if again.fingerprint != month_written.fingerprint:
            report.fail("the second write of the same rows has a different fingerprint")
        store = SeriesStore(scratch / "store", wall=lambda: datetime(2026, 10, 23, tzinfo=UTC))
        first = store.commit_file(key, month_written)
        second = store.commit_file(key, again)
        if not first.value or not second.value:
            report.fail(f"the store refused a commit: {first} {second}")
        else:
            report.numbers["frozen"] = second.value.frozen
            report.numbers["gaps"] = len(second.value.gaps)
            files = sorted(path.name for path in store.folder(key).glob("*.parquet"))
            report.numbers["files"] = len(files)
            if len(files) != 1:
                report.fail(f"the store holds {len(files)} files for one key: {files}")
        week_peak = report.numbers["week_peak_mb"]
        month_peak = report.numbers["month_peak_mb"]
        report.numbers["peak_ratio"] = round(float(month_peak) / max(1.0, float(week_peak)), 2)
        if float(week_peak) > 0 and float(month_peak) >= 4 * float(week_peak):
            report.fail(
                f"the month's peak RAM {month_peak} MB is near four times the week's {week_peak} MB"
            )
        return report.render()
    finally:
        common.drop_scratch()


if __name__ == "__main__":
    sys.exit(main())
