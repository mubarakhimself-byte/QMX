"""Import the old ticks and the risk-lab CSVs as partitions, read where they already are.

One run reads the old ticks (`--ticks-root`) and the CSVs (`--csv-root`) in place, or a copy
under `--raw-backup-root` when one was made; nothing is copied first. It imports each instrument
and month through the door's `commit` into the QMX folder's `market` (`--market`, by default
`$QMX_HOME/market`, else `~/.qmx/market`), resumes from the last committed month after a stop,
writes one `dataset` card per series, and writes a report of rows per month, files per series
and a comparison against a `MANIFEST.sha256` when one sits beside the copy. A commit needs no
holdout: the door opens without one (ruling 137), and `--seal-boundary-ns` is optional.

How a month is imported. DR3A's importers own the reading: `RawTicks` selects a month's hour
files and `raw_tick_rows` decodes them, `CsvBars` reads a risk-lab file. The importer's rows are
staged as one typed Parquet file whose path names its key
(`<source>/<subject>/<kind>/<variant>/<YYYY-MM>.parquet`), and the door's `commit` re-streams
that file through the typed writer, so the fingerprint the store records is computed there and
never taken from the staged file's own claim. The staged file is transport only and is removed
after its commit. The staged and the stored fingerprint must agree; a month where they differ
fails the run, because that is the one way a row could change on the way in.

Resume. A month whose key already has a state in the store is not read again; the run records
what the store holds and moves on. Stopping anywhere leaves the store as the record of what
landed, so a rerun adds only the missing months. The report is rewritten after every month, so a
stopped run still leaves the counts it reached.

The source is read only. Nothing here writes under the raw root, and the report names the
manifest paths a month's files did not match.

    cd qmx-agents
    uv run --no-sync python ../scripts/data/import_old_ticks.py `
        --ticks-root <the old ticks folder> `
        --csv-root <the risk-lab CSV folder> `
        --report <where the JSON report goes>

`--from-month` and `--to-month` bound a scratch run. They are the run's own bound, not a cap on
the import: the real run passes neither and imports every month the copy holds.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Final

from qmf.core import TypedRefusal, is_refusal
from qmf.data.dukascopy import PERSONAL_USE_LICENSE
from qmf.data.importers.csv_bars import RISK_LAB_SOURCE, CsvBars
from qmf.data.importers.dukascopy_raw import DUKASCOPY_SOURCE, RawTicks, raw_tick_rows
from qmf.data.series import (
    BAR_KIND,
    TICKS_KIND,
    CommitReceipt,
    SeriesKey,
    SeriesState,
    SeriesStore,
)
from qmf.data.store.engines.typed import write_in_child
from qmx_engine.ledger import redact
from qmx_host.market_data import MarketDoor, Placement
from qmx_library.cards import Correction, Partition, SeriesCard, write_card
from qmx_library.port import LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

__all__ = [
    "Plan",
    "Report",
    "csv_files",
    "import_csv",
    "import_ticks",
    "instrument_dirs",
    "main",
    "manifest_rows",
    "manifest_ticks",
    "month_rows",
    "months_in",
    "run",
]

MANIFEST_NAME: Final[str] = "MANIFEST.sha256"
RISK_LAB_MANIFEST: Final[str] = "MANIFEST.risk-lab.sha256"
TICKS_FOLDER: Final[str] = "external-deep-history"
CSV_FOLDER: Final[str] = "risk-lab-2026-10-05-data"
LISTED: Final[int] = 50
"""A report names this many differing paths; its counts carry the rest."""
MANIFEST_LINE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<sha>[0-9a-f]{64})\s+(?:(?P<size>\d+)\s+)?\*?(?P<path>.+)$"
)
MONTH_TEXT: Final[re.Pattern[str]] = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})$")
DATE_DIR: Final[re.Pattern[str]] = re.compile(
    r"^date=(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$"
)
CSV_NAME: Final[re.Pattern[str]] = re.compile(
    r"^(?P<subject>[a-z0-9]+)_m1_(?P<variant>bid|ask)_(?P<year>\d{4})(?P<partial>_partial)?\.csv$"
)
TOKEN: Final[re.Pattern[str]] = re.compile(r"instrument=([^/]+)")
DATE: Final[re.Pattern[str]] = re.compile(r"date=(\d{4})-(\d{2})-(\d{2})")
HOUR_SUFFIX: Final[str] = "h_ticks.bi5"


@dataclass(frozen=True, slots=True)
class Plan:
    """What one run imports, where it writes, and where its report goes."""

    store: Path
    staging: Path
    report: Path
    raw_backup_root: Path | None = None
    seal_boundary_ns: int | None = None
    placement: Placement = Placement.PC
    library: Path | None = None
    holdout_months: int = 12
    world: str = "replay"
    ticks_root: Path | None = None
    ticks_manifest: Path | None = None
    csv_root: Path | None = None
    csv_manifest: Path | None = None
    subjects: tuple[str, ...] = ()
    first_month: str = ""
    last_month: str = ""
    only: str = "all"

    @property
    def ticks(self) -> Path | None:
        return self.ticks_root or _under(self.raw_backup_root, TICKS_FOLDER)

    @property
    def ticks_record(self) -> Path | None:
        return self.ticks_manifest or _under(self.raw_backup_root, MANIFEST_NAME)

    @property
    def csvs(self) -> Path | None:
        return self.csv_root or _under(self.raw_backup_root, CSV_FOLDER)

    @property
    def csv_record(self) -> Path | None:
        return self.csv_manifest or _under(self.raw_backup_root, RISK_LAB_MANIFEST)

    def in_scope(self, year: int, month: int) -> bool:
        """Whether a month falls inside the run's own bound, inclusive at both ends."""
        text = f"{year:04d}-{month:02d}"
        if self.first_month and text < self.first_month:
            return False
        return not (self.last_month and text > self.last_month)


@dataclass(frozen=True, slots=True)
class ManifestRow:
    """One line of a DR0 manifest: a path relative to the copied root, and its hash."""

    path: str
    sha256: str
    size: int | None = None


@dataclass
class Report:
    """What one run did, in the shape the JSON report and the printed summary read."""

    plan: Plan
    months: list[dict[str, object]] = field(default_factory=list[dict[str, object]])
    cards: list[dict[str, object]] = field(default_factory=list[dict[str, object]])
    manifest: dict[str, dict[str, object]] = field(default_factory=dict[str, dict[str, object]])
    problems: list[str] = field(default_factory=list[str])
    began: float = field(default_factory=time.perf_counter)

    def add(self, record: dict[str, object]) -> None:
        self.months.append(record)
        self.write()

    def fail(self, problem: str) -> None:
        self.problems.append(problem)

    @property
    def seconds(self) -> float:
        return round(time.perf_counter() - self.began, 1)

    def series(self) -> list[dict[str, object]]:
        """One row per series: its months, source files, rows and what the run did."""
        grouped: dict[str, dict[str, object]] = {}
        for month in self.months:
            name = str(month["series"])
            row = grouped.setdefault(
                name,
                {
                    "series": name,
                    "months": 0,
                    "files": 0,
                    "rows": 0,
                    "frozen": 0,
                    "imported": 0,
                    "skipped": 0,
                    "empty": 0,
                    "refused": 0,
                    "manifest": "match",
                },
            )
            row["months"] = int(row["months"]) + 1
            row["files"] = int(row["files"]) + int(str(month["files"]))
            row["rows"] = int(row["rows"]) + int(str(month["rows"]))
            row["frozen"] = int(row["frozen"]) + (1 if month["frozen"] else 0)
            action = str(month["action"])
            row[action] = int(row[action]) + 1
            if month["manifest"] not in ("match", "not checked"):
                row["manifest"] = str(month["manifest"])
        return [grouped[name] for name in sorted(grouped)]

    def as_json(self) -> dict[str, object]:
        imported = [row for row in self.months if row["action"] == "imported"]
        spent = sum(float(str(row["seconds"])) for row in imported)
        return {
            "raw_backup_root": _posix(self.plan.raw_backup_root),
            "store": self.plan.store.as_posix(),
            "first_month": self.plan.first_month,
            "last_month": self.plan.last_month,
            "subjects": list(self.plan.subjects),
            "seconds": self.seconds,
            "months_imported": len(imported),
            "months_per_minute": round(len(imported) / (spent / 60), 2) if spent else 0.0,
            "peak_self_mb": _peak_mb("self"),
            "peak_child_mb": _peak_mb("children"),
            "manifest": self.manifest,
            "series": self.series(),
            "months": self.months,
            "cards": self.cards,
            "problems": self.problems,
        }

    def write(self) -> None:
        """Put the report where the run was told to, replacing the last one atomically."""
        self.plan.report.parent.mkdir(parents=True, exist_ok=True)
        scratch = self.plan.report.with_name(f"{self.plan.report.name}.tmp")
        scratch.write_text(json.dumps(self.as_json(), indent=2, sort_keys=True) + "\n", "utf-8")
        os.replace(scratch, self.plan.report)

    def summary(self) -> int:
        """Print the counts, the manifest comparison and any problem, then the exit code."""
        print(f"import old ticks: {self.seconds}s")
        for row in self.series():
            print(
                f"  series {row['series']}: {row['months']} months, {row['files']} files, "
                f"{row['rows']} rows, {row['frozen']} frozen, {row['imported']} imported, "
                f"{row['skipped']} skipped, {row['empty']} empty, {row['refused']} refused, "
                f"manifest {row['manifest']}"
            )
        for name, section in self.manifest.items():
            print(f"  manifest {name}: {json.dumps(section, sort_keys=True)}")
        for card in self.cards:
            print(f"  card {card['series']}: {card.get('object_id', card.get('why', ''))}")
        for problem in self.problems:
            print(f"  problem: {problem}")
        print(f"  report: {self.plan.report.as_posix()}")
        return 0 if not self.problems else 1


def _peak_mb(scope: str) -> float | None:
    """Peak resident memory in MB for this process, or for its largest reaped child.

    The server is Linux, where `/proc/self/status` carries this process's high-water mark and
    `RUSAGE_CHILDREN` carries the largest writer child. A platform that exposes neither records
    nothing rather than an invented figure.
    """
    if scope == "children":
        try:
            import resource  # noqa: PLC0415 (the POSIX figure only)
        except ImportError:
            return None
        return round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024, 1)
    try:
        for line in Path("/proc/self/status").read_text("utf-8").splitlines():
            if line.startswith("VmHWM:"):
                return round(int(line.split()[1]) / 1024, 1)
    except OSError, ValueError:
        return None
    return None


def _under(root: Path | None, name: str) -> Path | None:
    return None if root is None else root / name


def _posix(path: Path | None) -> str | None:
    return None if path is None else path.as_posix()


def _reason(refusal: TypedRefusal) -> str:
    return f"{refusal.category}: {json.dumps(dict(refusal.context), sort_keys=True)}"


def month_of(text: str) -> tuple[int, int]:
    """A `YYYY-MM` month as `(year, month)`, refusing any other shape."""
    match = MONTH_TEXT.match(text)
    if match is None:
        raise ValueError(f"{text!r} is not a YYYY-MM month")
    return int(match["year"]), int(match["month"])


def manifest_rows(path: Path) -> tuple[ManifestRow, ...]:
    """Read a DR0 manifest: one `<sha256>  <bytes>  <path>` line per copied file.

    The hash marker `*` and a leading `./` are dropped, because the PC's own sha256sum wrote
    them and the comparison is by path.
    """
    rows: list[ManifestRow] = []
    for line in path.read_text("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        match = MANIFEST_LINE.match(line)
        if match is None:
            continue
        found = match["path"].strip()
        while found.startswith("./"):
            found = found[2:]
        size = match["size"]
        rows.append(
            ManifestRow(found.replace("\\", "/"), match["sha"], int(size) if size else None)
        )
    return tuple(rows)


def manifest_ticks(
    rows: Sequence[ManifestRow],
) -> dict[tuple[str, int, int], tuple[str, ...]]:
    """The manifest's tick files by `(subject, year, month)`; other files are left out."""
    wanted: dict[tuple[str, int, int], list[str]] = {}
    for row in rows:
        if not row.path.endswith(HOUR_SUFFIX):
            continue
        subject = TOKEN.search(row.path)
        date = DATE.search(row.path)
        if subject is None or date is None:
            continue
        key = (subject.group(1), int(date.group(1)), int(date.group(2)))
        wanted.setdefault(key, []).append(row.path)
    return {key: tuple(sorted(paths)) for key, paths in wanted.items()}


def instrument_dirs(ticks_root: Path) -> dict[str, Path]:
    """Every `instrument=<SYMBOL>` folder under the old ticking tree, by symbol."""
    found: dict[str, Path] = {}
    for candidate in sorted(ticks_root.rglob("instrument=*")):
        if candidate.is_dir():
            found.setdefault(candidate.name.split("=", 1)[1], candidate)
    return found


def months_in(directory: Path) -> set[tuple[int, int]]:
    """Every month the `date=YYYY-MM-DD` folders of one instrument name."""
    tick = directory / "resolution=tick"
    folder = tick if tick.is_dir() else directory
    months: set[tuple[int, int]] = set()
    for entry in folder.iterdir():
        match = DATE_DIR.match(entry.name)
        if match is not None and entry.is_dir():
            months.add((int(match["year"]), int(match["month"])))
    return months


def csv_files(csv_root: Path) -> tuple[tuple[Path, str, str, int, bool], ...]:
    """The risk-lab files as `(path, subject, variant, year, partial)` in name order."""
    found: list[tuple[Path, str, str, int, bool]] = []
    for path in sorted(csv_root.glob("*.csv")):
        match = CSV_NAME.match(path.name)
        if match is not None:
            found.append(
                (
                    path,
                    match["subject"].upper(),
                    match["variant"],
                    int(match["year"]),
                    match["partial"] is not None,
                )
            )
    return tuple(found)


def _key(
    source: str, subject: str, kind: str, year: int, month: int, variant: str = ""
) -> SeriesKey:
    """One validated series key, or a `ValueError` naming what the key refused."""
    built = SeriesKey.try_create(source, subject, kind, year, month, variant)
    if is_refusal(built):
        raise ValueError(f"{built.category}: {dict(built.context)}")
    return built.value


def _staged(staging: Path, key: SeriesKey) -> Path:
    """Where a month's file waits for the door: `<staging>/<series>/<YYYY-MM>.parquet`."""
    target = staging / key.series / f"{key.year:04d}-{key.month:02d}.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _held(state: SeriesState | None) -> dict[str, object] | None:
    """What the store already holds for a month, or None when nothing is there."""
    if state is None:
        return None
    return {
        "action": "skipped",
        "rows": state.rows,
        "fingerprint": state.fingerprint,
        "frozen": state.frozen,
        "gaps": len(state.gaps),
    }


def _empty() -> dict[str, object]:
    """A month the source holds no row for: a gap the report records."""
    return {"action": "empty", "rows": 0, "fingerprint": "", "frozen": False, "gaps": 0}


def _commit(
    door: MarketDoor, plan: Plan, key: SeriesKey, staged: Path, report: Report
) -> dict[str, object]:
    """Hand one staged file to the door and describe what it landed."""
    landed = door.commit([staged], staging=plan.staging)
    staged.unlink(missing_ok=True)
    if is_refusal(landed):
        report.fail(f"{key.text}: the door refused the commit: {_reason(landed)}")
        return {"action": "refused", "rows": 0, "fingerprint": "", "frozen": False, "gaps": 0}
    receipt: CommitReceipt = landed.value[0]
    return {
        "action": "imported",
        "rows": receipt.rows,
        "fingerprint": receipt.fingerprint,
        "frozen": receipt.frozen,
        "gaps": len(receipt.gaps),
    }


def _verdict(
    found: Sequence[str], wanted: Sequence[str], *, checked: bool
) -> tuple[str, list[str], list[str]]:
    """A month's files against the manifest's: the verdict, what is missing, what is extra."""
    if not checked:
        return "not checked", [], []
    extra = sorted(set(found) - set(wanted))
    missing = sorted(set(wanted) - set(found))
    if not extra and not missing:
        return "match", [], []
    return "differ", missing[:LISTED], extra[:LISTED]


def import_ticks(plan: Plan, door: MarketDoor, report: Report) -> None:
    """Import every instrument and month of the raw copy, in time order."""
    store = door.series_store()
    ticks = plan.ticks
    if ticks is None:
        report.fail("name the old ticks with --ticks-root, where they are, or --raw-backup-root")
        return
    record = plan.ticks_record
    checked = record is not None and record.is_file()
    rows = manifest_rows(record) if record is not None and checked else ()
    wanted = manifest_ticks(rows)
    tick_files = sum(len(paths) for paths in wanted.values())
    report.manifest["ticks"] = {
        "record": _posix(record),
        "lines": len(rows),
        "tick_files": tick_files,
        "other_files": len(rows) - tick_files,
        "months": len(wanted),
    }
    directories = instrument_dirs(ticks)
    if not directories:
        report.fail(f"no instrument folder is under {ticks.as_posix()}")
        return
    named: set[str] = set()
    read: set[str] = set()
    for subject, directory in sorted(directories.items()):
        if plan.subjects and subject not in plan.subjects:
            continue
        for year, month in sorted(months_in(directory)):
            if not plan.in_scope(year, month):
                continue
            named.update(wanted.get((subject, year, month), ()))
            read.update(
                _import_tick_month(
                    plan, door, store, report, ticks, subject, directory, year, month, wanted, checked
                )
            )
    report.manifest["ticks"] |= {
        "files_in_scope": len(named),
        "missing_from_copy": sorted(named - read)[:LISTED],
        "not_in_manifest": sorted(read - named)[:LISTED],
    }
    if named - read:
        report.fail(f"{len(named - read)} tick files the manifest names were not read")
    if read - named:
        report.fail(f"{len(read - named)} tick files read are not in the manifest")


def _import_tick_month(
    plan: Plan,
    door: MarketDoor,
    store: SeriesStore,
    report: Report,
    ticks: Path,
    subject: str,
    directory: Path,
    year: int,
    month: int,
    wanted: dict[tuple[str, int, int], tuple[str, ...]],
    checked: bool,
) -> set[str]:
    """One instrument month: compare its files with the manifest, then import or skip it."""
    key = _key(DUKASCOPY_SOURCE, subject, TICKS_KIND, year, month)
    started = time.perf_counter()
    files = RawTicks(directory, subject, year, month).hours()
    found = tuple(sorted(path.relative_to(ticks).as_posix() for _, path in files))
    verdict, missing, extra = _verdict(
        found, wanted.get((subject, year, month), ()), checked=checked
    )
    record: dict[str, object] = {
        "series": key.series,
        "month": f"{year:04d}-{month:02d}",
        "files": len(files),
        "manifest": verdict,
        "missing_from_copy": missing,
        "not_in_manifest": extra,
    }
    if verdict == "differ":
        report.fail(
            f"{key.text}: {len(missing)} of the manifest's files are missing, "
            f"{len(extra)} files are not in the manifest"
        )
    if not files:
        record |= _empty()
    elif (held := _held(store.state(key))) is not None:
        record |= held
    else:
        staged = _staged(plan.staging, key)
        written = write_in_child(
            staged,
            key.text,
            key.rule.columns,
            partial(raw_tick_rows, files),
            hole_bounds=key.rule.hole_bounds,
        )
        if written.rows == 0:
            staged.unlink(missing_ok=True)
            record |= _empty()
        else:
            landed = _commit(door, plan, key, staged, report)
            if landed["fingerprint"] != written.fingerprint:
                report.fail(
                    f"{key.text}: the door stored {landed['fingerprint']}, the staged file was "
                    f"{written.fingerprint}"
                )
            record |= landed
    record["seconds"] = round(time.perf_counter() - started, 3)
    report.add(record)
    return set(found)


def import_csv(plan: Plan, door: MarketDoor, report: Report) -> None:
    """Import every risk-lab file, one month partition per side, in name order."""
    store = door.series_store()
    csvs = plan.csvs
    if csvs is None:
        report.fail("name the risk-lab CSVs with --csv-root, where they are, or --raw-backup-root")
        return
    record = plan.csv_record
    rows = manifest_rows(record) if record is not None and record.is_file() else ()
    recorded = {row.path: row for row in rows}
    files = csv_files(csvs)
    if not files:
        report.fail(f"no risk-lab CSV is under {csvs.as_posix()}")
        return
    report.manifest["csv"] = {
        "record": _posix(record),
        "lines": len(rows),
        "files": len(files),
        "unrecorded": sorted(path.name for path, *_ in files if path.name not in recorded),
        "unread": sorted(name for name in recorded if name not in {f[0].name for f in files}),
        "coverage": {},
    }
    for path, subject, variant, year, partial_file in files:
        if plan.subjects and subject not in plan.subjects:
            continue
        compared = _compare_csv(path, recorded.get(path.name))
        if compared not in ("match", "not checked"):
            report.fail(f"{path.name}: the risk-lab manifest comparison is {compared}")
        _import_csv_file(
            plan, door, store, report, path, subject, variant, year, partial_file, compared
        )


def _compare_csv(path: Path, row: ManifestRow | None) -> str:
    """A risk-lab file against its manifest line: match, or which side differs."""
    if row is None:
        return "no line"
    if row.size is not None and path.stat().st_size != row.size:
        return "size differs"
    return "match"


def _import_csv_file(
    plan: Plan,
    door: MarketDoor,
    store: SeriesStore,
    report: Report,
    path: Path,
    subject: str,
    variant: str,
    year: int,
    partial_file: bool,
    compared: str,
) -> None:
    """One risk-lab file: every month it holds becomes one partition, or a recorded gap."""
    last: SeriesKey | None = None
    empty: list[str] = []
    for month in range(1, 13):
        if not plan.in_scope(year, month):
            continue
        key = _key(RISK_LAB_SOURCE, subject, BAR_KIND, year, month, variant)
        started = time.perf_counter()
        record: dict[str, object] = {
            "series": key.series,
            "month": f"{year:04d}-{month:02d}",
            "files": 1,
            "manifest": compared,
            "missing_from_copy": [],
            "not_in_manifest": [] if compared == "match" else [path.name],
            "source": path.name,
            "partial": partial_file,
        }
        if (held := _held(store.state(key))) is not None:
            record |= held
        else:
            staged = _staged(plan.staging, key)
            bars = CsvBars(path, subject, year, month, variant)
            written = write_in_child(
                staged,
                key.text,
                key.rule.columns,
                partial(month_rows, bars, key.start_ns // 1_000_000, key.end_ns // 1_000_000),
            )
            if written.rows == 0:
                staged.unlink(missing_ok=True)
                record |= _empty()
            else:
                landed = _commit(door, plan, key, staged, report)
                if landed["fingerprint"] != written.fingerprint:
                    report.fail(
                        f"{key.text}: the door stored {landed['fingerprint']}, the staged file "
                        f"was {written.fingerprint}"
                    )
                record |= landed
                last = key
        if record["action"] == "empty":
            empty.append(str(record["month"]))
        record["seconds"] = round(time.perf_counter() - started, 3)
        report.add(record)
    _note_coverage(store, report, path, last, empty, partial_file)


def month_rows(bars: CsvBars, start_ms: int, end_ms: int) -> Iterator[Sequence[object]]:
    """The rows of one month of a risk-lab file, streamed in time order.

    A risk-lab file holds a whole year, so the month's window is what makes one partition of
    that year. This runs in the writer's child, which is why it is a module-level function.
    """
    for row in bars.rows():
        if start_ms <= int(row[0]) < end_ms:  # type: ignore[arg-type]
            yield row


def _note_coverage(
    store: SeriesStore,
    report: Report,
    path: Path,
    last: SeriesKey | None,
    empty: Sequence[str],
    partial_file: bool,
) -> None:
    """What a file covers: its last row, the months it holds no row for, and any partial mark.

    The note states what the file gave, not a verdict: a file whose last bar is a couple of hours
    before the UTC month end is complete in its own zone, so only a whole empty month is called
    out as a gap.
    """
    note: dict[str, object] = {"partial": partial_file}
    if empty:
        note["empty_months"] = list(empty)
    if last is not None:
        read = store.read(last)
        if not is_refusal(read) and read.value.rows:
            last_t = int(read.value.rows[-1]["t"])  # type: ignore[arg-type]
            note["last"] = datetime.fromtimestamp(last_t // 1000, tz=UTC).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
    if partial_file or empty or "last" in note:
        report.manifest["csv"]["coverage"][path.name] = note  # type: ignore[index]


def write_cards(plan: Plan, store: SeriesStore, report: Report) -> None:
    """One `dataset` card per series the run touched, through DR3A's card writer."""
    if plan.library is None:
        report.cards.append({"series": "", "why": "no --library given, so no card was written"})
        return
    try:
        library = Store.open(plan.library, redactor=redact)
    except LibraryRefused as refused:
        report.fail(
            f"the Library at {plan.library.as_posix()} is held by another writer ({refused}); "
            "the card pass needs it, and the partitions stay committed"
        )
        return
    with library:
        for series in report.series():
            _write_card(plan, store, library, report, series)


def _write_card(
    plan: Plan, store: SeriesStore, library: Store, report: Report, series: dict[str, object]
) -> None:
    """One series' card: its partitions from the store, plus any correction they recorded."""
    name = str(series["series"])
    source, subject, kind, variant = name.split("/")
    variant = "" if variant == "-" else variant
    partitions: list[Partition] = []
    corrections: list[Correction] = []
    for record in report.months:
        if record["series"] != name:
            continue
        year, month = month_of(str(record["month"]))
        state = store.state(_key(source, subject, kind, year, month, variant))
        if state is None:
            continue
        partitions.append(
            Partition(year, month, state.fingerprint, state.rows, state.frozen, state.gaps)
        )
        corrections.extend(
            Correction(item.start_ns, item.end_ns, item.old, item.new, item.reason, item.at)
            for item in state.corrections
        )
    card = SeriesCard(
        source,
        subject,
        kind,
        variant,
        licence=PERSONAL_USE_LICENSE if source == DUKASCOPY_SOURCE else "",
        world=plan.world,
        redownloadable=source == DUKASCOPY_SOURCE,
        quality={"months": len(partitions)},
    )
    landed = write_card(library, Principal("operator"), card, tuple(partitions), tuple(corrections))
    report.cards.append({"series": name, "item": landed.item, "object_id": landed.object_id})
    report.write()


def run(plan: Plan) -> Report:
    """Import both sources through the door, then write the cards and the report."""
    report = Report(plan)
    data: dict[str, object] = {"holdout_months": plan.holdout_months, "world": plan.world}
    if plan.seal_boundary_ns is not None:
        data["seal_boundary_ns"] = plan.seal_boundary_ns
    opened = MarketDoor.open(plan.store, data, placement=plan.placement)
    if is_refusal(opened):
        report.fail(f"the door did not open: {_reason(opened)}")
        report.write()
        return report
    door = opened.value
    if plan.only in ("ticks", "all"):
        import_ticks(plan, door, report)
    if plan.only in ("csv", "all"):
        import_csv(plan, door, report)
    write_cards(plan, door.series_store(), report)
    report.write()
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import the old ticks and risk-lab CSVs.")
    parser.add_argument(
        "--raw-backup-root",
        type=Path,
        default=None,
        help="a folder holding a copy of both sources and their manifests, when one was made",
    )
    parser.add_argument("--ticks-root", type=Path, default=None, help="the old ticks copy")
    parser.add_argument("--ticks-manifest", type=Path, default=None, help="its manifest")
    parser.add_argument("--csv-root", type=Path, default=None, help="the risk-lab CSV copy")
    parser.add_argument("--csv-manifest", type=Path, default=None, help="its manifest")
    parser.add_argument(
        "--market",
        "--store",
        dest="store",
        type=Path,
        default=Path(os.environ.get("QMX_HOME") or Path.home() / ".qmx") / "market",
        help="the door's store root, by default the QMX folder's market",
    )
    parser.add_argument(
        "--placement",
        type=Placement,
        choices=tuple(Placement),
        default=Placement.PC,
        help="the place this store is on, which each commit records as born_on",
    )
    parser.add_argument("--library", type=Path, default=None, help="the Library store to card")
    parser.add_argument("--staging", type=Path, default=None, help="where staged files wait")
    parser.add_argument("--report", type=Path, required=True, help="the JSON report to write")
    parser.add_argument(
        "--seal-boundary-ns",
        type=int,
        default=None,
        help="optional: a holdout boundary for the door; a commit needs none",
    )
    parser.add_argument("--holdout-months", type=int, default=12)
    parser.add_argument("--world", default="replay")
    parser.add_argument("--subjects", default="", help="a comma-separated subset of instruments")
    parser.add_argument("--from-month", default="", help="YYYY-MM, the run's own first month")
    parser.add_argument("--to-month", default="", help="YYYY-MM, the run's own last month")
    parser.add_argument("--only", choices=("ticks", "csv", "all"), default="all")
    arguments = parser.parse_args(argv)
    for text in (arguments.from_month, arguments.to_month):
        if text:
            month_of(text)
    plan = Plan(
        raw_backup_root=arguments.raw_backup_root,
        store=arguments.store,
        staging=arguments.staging or arguments.store / "staging",
        report=arguments.report,
        seal_boundary_ns=arguments.seal_boundary_ns,
        placement=arguments.placement,
        library=arguments.library,
        holdout_months=arguments.holdout_months,
        world=arguments.world,
        ticks_root=arguments.ticks_root,
        ticks_manifest=arguments.ticks_manifest,
        csv_root=arguments.csv_root,
        csv_manifest=arguments.csv_manifest,
        subjects=tuple(item.strip() for item in arguments.subjects.split(",") if item.strip()),
        first_month=arguments.from_month,
        last_month=arguments.to_month,
        only=arguments.only,
    )
    return run(plan).summary()


if __name__ == "__main__":
    sys.exit(main())
