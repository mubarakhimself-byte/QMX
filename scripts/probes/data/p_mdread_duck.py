"""P-MDREAD-DUCK (W9; Library AD-25, F1), premise: DuckDB 1.5.5 reads a Parquet file
written in the planned typed schema back row for row.

The schema under test is the one W9 writes: int64 `t` (UTC epoch milliseconds), int64
prices scaled by 1e5, float64 volumes, and no dictionary or nested types. Three tables
are written with pyarrow 25.0.1 through `ParquetWriter` so each file holds several row
groups, then read back with DuckDB 1.5.5 and compared column by column:

* `ticks` — 1,000,000 rows, four row groups, an hour-long hole, duplicate timestamps and
  a few null volumes;
* `bars` — 100,000 rows, the OHLC columns and a nullable volume;
* `boundary` — the values a lossy reader changes: int64 min and max, 2**53+1, float64 NaN
  and infinity, -0.0, a non-ASCII string and nulls.

A column that differs is named in the output with the type DuckDB read and the first
row that differs, which is what the fallback row in `FINDINGS.md` needs.

    uv run --no-sync python scripts/probes/data/p_mdread_duck.py

Scratch goes to `D:/Temp/prb-dp/mdread-duck/` and is removed before the probe exits.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from scripts.probes.data import common
from scripts.probes.data.common import Report

PROBE = "P-MDREAD-DUCK"
PRICE_SCALE = 100_000
ROWS_TICKS = 1_000_000
ROWS_BARS = 100_000
ROW_GROUP = 250_000
START_MS = 1_704_067_200_000  # 2024-01-01T00:00:00Z
HOUR_MS = 3_600_000
NS_PER_MS = 1_000_000

TICKS_SCHEMA = pa.schema(
    [
        pa.field("t", pa.int64()),
        pa.field("bid", pa.int64()),
        pa.field("ask", pa.int64()),
        pa.field("bid_volume", pa.float64()),
        pa.field("ask_volume", pa.float64()),
    ]
)
BARS_SCHEMA = pa.schema(
    [
        pa.field("t", pa.int64()),
        pa.field("open", pa.int64()),
        pa.field("high", pa.int64()),
        pa.field("low", pa.int64()),
        pa.field("close", pa.int64()),
        pa.field("volume", pa.float64()),
    ]
)
BOUNDARY_SCHEMA = pa.schema(
    [
        pa.field("kind", pa.string()),
        pa.field("whole", pa.int64()),
        pa.field("real", pa.float64()),
        pa.field("flag", pa.bool_()),
    ]
)

DUCKDB_TYPES = {
    "int64": "BIGINT",
    "double": "DOUBLE",
    "string": "VARCHAR",
    "bool": "BOOLEAN",
}


@dataclass(frozen=True, slots=True)
class Table:
    """One scratch file: its name, schema and every written row group."""

    name: str
    schema: pa.Schema
    row_groups: tuple[pa.Table, ...]

    @property
    def rows(self) -> int:
        return sum(chunk.num_rows for chunk in self.row_groups)


def ticks_table() -> Table:
    """A month-shaped ticks file: the hole sits where an hour of no ticks would."""
    times: list[int] = []
    bid: list[int] = []
    ask: list[int] = []
    bid_volume: list[float | None] = []
    ask_volume: list[float | None] = []
    for row in range(ROWS_TICKS):
        offset = row * 1000 if row < ROWS_TICKS // 2 else row * 1000 + HOUR_MS
        if row % 100_000 == 0:
            offset -= 1000  # duplicate the previous tick's timestamp
        times.append(START_MS + offset)
        price = 108_000 + (row * 7) % 500
        bid.append(price)
        ask.append(price + 12)
        bid_volume.append(None if row % ROW_GROUP == 3 else (row % 97) * 0.25)
        ask_volume.append(None if row % ROW_GROUP == 5 else (row % 89) * 0.5)
    arrays = {
        "t": pa.array(times, pa.int64()),
        "bid": pa.array(bid, pa.int64()),
        "ask": pa.array(ask, pa.int64()),
        "bid_volume": pa.array(bid_volume, pa.float64()),
        "ask_volume": pa.array(ask_volume, pa.float64()),
    }
    return _chunked("ticks", TICKS_SCHEMA, arrays, ROWS_TICKS)


def bars_table() -> Table:
    times = [START_MS + row * HOUR_MS for row in range(ROWS_BARS)]
    opens = [108_000 + (row * 13) % 900 for row in range(ROWS_BARS)]
    highs = [value + 25 for value in opens]
    lows = [value - 25 for value in opens]
    closes = [value + 10 for value in opens]
    volume: list[float | None] = [
        None if row % 1000 == 0 else row * 1.5 for row in range(ROWS_BARS)
    ]
    arrays = {
        "t": pa.array(times, pa.int64()),
        "open": pa.array(opens, pa.int64()),
        "high": pa.array(highs, pa.int64()),
        "low": pa.array(lows, pa.int64()),
        "close": pa.array(closes, pa.int64()),
        "volume": pa.array(volume, pa.float64()),
    }
    return _chunked("bars", BARS_SCHEMA, arrays, ROWS_BARS)


def boundary_table() -> Table:
    values = {
        "kind": pa.array(
            [
                "int64-min",
                "int64-max",
                "beyond-float53",
                "negative",
                "zero",
                "nan",
                "infinity",
                "unicode",
            ],
            pa.string(),
        ),
        "whole": pa.array(
            [
                -(2**63),
                2**63 - 1,
                2**53 + 1,
                -1,
                0,
                None,
                None,
                None,
            ],
            pa.int64(),
        ),
        "real": pa.array(
            [None, None, None, 0.1, -0.0, math.nan, math.inf, 1e308],
            pa.float64(),
        ),
        "flag": pa.array([True, False, True, None, False, True, None, False], pa.bool_()),
    }
    rows = 8
    return _chunked("boundary", BOUNDARY_SCHEMA, values, rows)


def _chunked(name: str, schema: pa.Schema, arrays: dict[str, pa.Array], rows: int) -> Table:
    """Build `rows` in ROW_GROUP-sized pieces, as the streaming writer will."""
    chunks: list[pa.Table] = []
    for start in range(0, rows, ROW_GROUP):
        length = min(ROW_GROUP, rows - start)
        columns = {key: array.slice(start, length) for key, array in arrays.items()}
        chunks.append(pa.Table.from_arrays([columns[f.name] for f in schema], schema=schema))
    return Table(name=name, schema=schema, row_groups=tuple(chunks))


def write(table: Table, folder: Path) -> tuple[Path, int]:
    """Write every row group through one ParquetWriter; returns the file and its bytes."""
    path = folder / f"{table.name}.parquet"
    writer = pq.ParquetWriter(path, table.schema, compression="zstd")
    try:
        for chunk in table.row_groups:
            writer.write_table(chunk, row_group_size=ROW_GROUP)
    finally:
        writer.close()
    return path, path.stat().st_size


def same(want: object, got: object) -> bool:
    """Equality that treats NaN as equal to NaN and keeps bools apart from 0/1."""
    if want is None or got is None:
        return want is None and got is None
    if isinstance(want, bool) or isinstance(got, bool):
        return isinstance(want, bool) and isinstance(got, bool) and want is got
    if isinstance(want, float) and isinstance(got, float):
        if math.isnan(want) or math.isnan(got):
            return math.isnan(want) and math.isnan(got)
        return want == got
    return type(want) is type(got) and want == got


def first_difference(want: list[object], got: list[object]) -> str | None:
    if len(want) != len(got):
        return f"{len(got)} rows, expected {len(want)}"
    for index, (left, right) in enumerate(zip(want, got, strict=True)):
        if not same(left, right):
            return f"row {index}: {right!r}, expected {left!r}"
    return None


def compare_table(connection: duckdb.DuckDBPyConnection, table: Table, path: Path) -> Report:
    """Read one scratch file with DuckDB and compare every column with what was written."""
    report = Report(probe=PROBE)
    written = pa.concat_tables(table.row_groups)
    described = connection.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]).fetchall()
    read_types = {row[0]: row[1] for row in described}
    read_back = connection.execute("SELECT * FROM read_parquet(?)", [str(path)]).to_arrow_table()
    report.numbers[f"{table.name}_rows"] = f"{table.rows} written, {read_back.num_rows} read"
    report.numbers[f"{table.name}_row_groups"] = pq.ParquetFile(path).num_row_groups
    for field in table.schema:
        expected_type = DUCKDB_TYPES[str(field.type)]
        got_type = read_types.get(field.name, "missing")
        if got_type != expected_type:
            report.note(f"{table.name}.{field.name}: DuckDB {got_type}, planned {expected_type}")
            report.fail(f"{table.name}.{field.name} read as {got_type}")
            continue
        difference = first_difference(
            written.column(field.name).to_pylist(),
            read_back.column(field.name).to_pylist(),
        )
        if difference is not None:
            report.fail(f"{table.name}.{field.name} differs at {difference}")
            continue
        report.note(f"{table.name}.{field.name}: {got_type}, identical")
    return report


def main() -> int:
    folder = common.scratch_folder("mdread-duck")
    try:
        tables = (ticks_table(), bars_table(), boundary_table())
        files = {table.name: write(table, folder) for table in tables}
        connection = duckdb.connect()
        try:
            reports = [compare_table(connection, table, files[table.name][0]) for table in tables]
        finally:
            connection.close()
        combined = Report(probe=PROBE)
        combined.numbers["pyarrow"] = common.package_version("pyarrow")
        combined.numbers["duckdb"] = common.package_version("duckdb")
        combined.numbers["row_group_size"] = ROW_GROUP
        combined.numbers["compression"] = "zstd"
        combined.numbers["files"] = ", ".join(
            f"{name} {size} bytes" for name, (_, size) in files.items()
        )
        for report in reports:
            combined.numbers.update(report.numbers)
            combined.details.extend(report.details)
            for problem in report.problems:
                combined.fail(problem)
        return combined.render()
    finally:
        common.drop_scratch()


if __name__ == "__main__":
    sys.exit(main())
