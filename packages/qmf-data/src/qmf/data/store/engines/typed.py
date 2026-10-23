"""Typed price-partition writer — int64 time, int64 scaled prices, streamed fingerprint (W9).

A price partition is a typed Parquet file, written in row groups as the rows arrive, with
no copy of the rows in its metadata. Time is int64 UTC epoch milliseconds and a price is
int64 scaled by :data:`PRICE_SCALE`, so no binary float sits on the money path; a volume is
float64 and may be null. The schema is the one P-MDREAD-DUCK proved: pyarrow 25.0.1 writes
it and DuckDB 1.5.5 reads it back row for row (DATA-PLAN, PRB-DP).

The fingerprint is sha256 over a pinned logical encoding — the header, the partition key,
the column names, then each time-ordered row — so it depends on the key and the values
alone, never on the writer's buffering, the compression, or the file's byte layout. Two
writes of the same rows give the same fingerprint wherever they run.

Rows stream: :class:`TypedWriter` holds one row group at a time, so peak memory is the row
group and not the partition. :func:`write_in_child` runs the same writer in a spawned child
process, so an importer's own process holds no rows at all.

pyarrow ships no type stubs; the unknown-type rules are disabled at file scope here, as in
``parquet.py``, so the rest of the package stays strictly typed.
"""

# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import hashlib
import multiprocessing
import os
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final, cast

import pyarrow as pa
import pyarrow.parquet as pq
from qmf.data.store.engines import SeriesFile, StoreEngineError

__all__ = [
    "BAR_COLUMNS",
    "FLOAT_COLUMNS",
    "PRICE_SCALE",
    "ROW_GROUP_ROWS",
    "TICK_COLUMNS",
    "VALUE_COLUMNS",
    "TypedWriter",
    "schema_for",
    "write_in_child",
]

# Dukascopy's own scale: a raw price integer divided by 100_000 is the price (5 digits).
PRICE_SCALE: Final[int] = 100_000
ROW_GROUP_ROWS: Final[int] = 250_000

TICK_COLUMNS: Final[tuple[str, ...]] = ("t", "bid", "ask", "bid_volume", "ask_volume")
BAR_COLUMNS: Final[tuple[str, ...]] = ("t", "open", "high", "low", "close", "volume")
VALUE_COLUMNS: Final[tuple[str, ...]] = ("t", "value")
FLOAT_COLUMNS: Final[frozenset[str]] = frozenset({"bid_volume", "ask_volume", "volume", "value"})
_HEADER: Final[bytes] = b"qmf-series-v1\n"
_INT64_MIN: Final[int] = -(2**63)
_INT64_MAX: Final[int] = 2**63 - 1


def schema_for(columns: Sequence[str]) -> pa.Schema:
    """The typed schema of a partition: int64 ``t``, int64 prices, float64 the rest."""
    return pa.schema(
        [pa.field(name, pa.float64() if name in FLOAT_COLUMNS else pa.int64()) for name in columns]
    )


def _cell(value: object) -> bytes:
    """One value in the pinned logical encoding the fingerprint hashes.

    An int is its decimal digits, a float is ``float.hex()`` (so ``-0.0`` and ``0.0`` differ
    and NaN has one spelling), a null is ``-``, and a string is its UTF-8 bytes behind a
    length, so no two shapes share an encoding.
    """
    if value is None:
        return b"-"
    if isinstance(value, bool):
        return b"T" if value else b"F"
    if isinstance(value, int):
        return str(value).encode("ascii")
    if isinstance(value, float):
        return value.hex().encode("ascii")
    if isinstance(value, str):
        data = value.encode("utf-8")
        return str(len(data)).encode("ascii") + b":" + data
    raise TypeError(f"{value!r} has no pinned encoding")


class TypedWriter:
    """Stream rows into one typed Parquet file and fingerprint them as they pass.

    ``target`` is where the file lands; the store may write to a temporary name and rename
    once it knows the fingerprint. :meth:`add` may be called any number of times; rows are
    buffered up to ``row_group_rows`` and then written as one row group. Rows must be
    time-ordered: a row whose ``t`` is below its predecessor is refused.
    """

    def __init__(
        self,
        target: Path,
        key: str,
        columns: Sequence[str],
        *,
        row_group_rows: int = ROW_GROUP_ROWS,
    ) -> None:
        if row_group_rows < 1:
            raise ValueError("a row group holds at least one row")
        self._target = target
        self._key = key
        self._columns = tuple(columns)
        self._schema = schema_for(self._columns)
        self._row_group_rows = row_group_rows
        self._rows = 0
        self._last_t: int | None = None
        self._pending: list[tuple[object, ...]] = []
        self._hasher = hashlib.sha256()
        self._hasher.update(_HEADER)
        self._hasher.update(key.encode("utf-8"))
        self._hasher.update(b"\n")
        self._hasher.update(",".join(self._columns).encode("ascii"))
        self._writer = pq.ParquetWriter(target, self._schema, compression="zstd")
        self._closed = False

    @property
    def rows(self) -> int:
        """Rows accepted so far."""
        return self._rows

    def add(self, rows: Iterable[Sequence[object]]) -> TypedWriter:
        """Accept a stream of rows; one row group is written per ``row_group_rows``."""
        if self._closed:
            raise ValueError("the writer is finished")
        for row in rows:
            values = self._checked(row)
            self._hasher.update(b"\n")
            self._hasher.update(b",".join(_cell(value) for value in values))
            self._pending.append(values)
            self._rows += 1
            if len(self._pending) >= self._row_group_rows:
                self._flush()
        return self

    def finish(self) -> SeriesFile:
        """Flush, close, fsync the file, and return what was written."""
        if self._closed:
            raise ValueError("the writer is finished")
        self._flush()
        self._closed = True
        try:
            self._writer.close()
            descriptor = os.open(self._target, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except (OSError, pa.ArrowException) as exc:
            raise StoreEngineError(
                "could not finish the typed partition file",
                engine="typed",
                detail={"target": str(self._target), "error": str(exc)},
            ) from exc
        return SeriesFile(
            key=self._key,
            fingerprint=self._hasher.hexdigest(),
            rows=self._rows,
            bytes=self._target.stat().st_size,
            path=self._target,
            columns=self._columns,
        )

    def _checked(self, row: Sequence[object]) -> tuple[object, ...]:
        if len(row) != len(self._columns):
            raise StoreEngineError(
                f"a row of {len(self._columns)} columns got {len(row)} values",
                engine="typed",
                retryable=False,
                detail={"key": self._key, "columns": list(self._columns)},
            )
        values: list[object] = []
        for name, value in zip(self._columns, row, strict=True):
            if name in FLOAT_COLUMNS:
                if value is not None and not isinstance(value, int | float):
                    raise StoreEngineError(
                        f"{name} takes a number or null, not {type(value).__name__}",
                        engine="typed",
                        retryable=False,
                    )
                values.append(None if value is None else float(cast("int | float", value)))
                continue
            if isinstance(value, bool) or not isinstance(value, int):
                raise StoreEngineError(
                    f"{name} takes an integer, not {type(value).__name__}",
                    engine="typed",
                    retryable=False,
                )
            number = int(value)
            if not _INT64_MIN <= number <= _INT64_MAX:
                raise StoreEngineError(
                    f"{name} is outside int64: {number}", engine="typed", retryable=False
                )
            if name == "t":
                if self._last_t is not None and number < self._last_t:
                    raise StoreEngineError(
                        "rows must be time-ordered; t went backwards",
                        engine="typed",
                        retryable=False,
                        detail={"t": number, "previous": self._last_t},
                    )
                self._last_t = number
            values.append(number)
        return tuple(values)

    def _flush(self) -> None:
        if not self._pending:
            return
        columns = [
            pa.array([row[index] for row in self._pending], type=self._schema.field(index).type)
            for index in range(len(self._columns))
        ]
        table = pa.Table.from_arrays(columns, schema=self._schema)
        try:
            self._writer.write_table(table, row_group_size=self._row_group_rows)
        except (OSError, pa.ArrowException) as exc:
            raise StoreEngineError(
                "could not write a row group of the typed partition",
                engine="typed",
                detail={"error": str(exc)},
            ) from exc
        self._pending = []


def write_in_child(
    target: Path,
    key: str,
    columns: Sequence[str],
    rows: Callable[[], Iterable[Sequence[object]]],
    *,
    timeout_s: float = 3600.0,
) -> SeriesFile:
    """Run :class:`TypedWriter` in a spawned child, so this process holds no rows.

    ``rows`` must be picklable by reference (a module-level function or a
    ``functools.partial`` of one); it is called in the child, which streams the rows into
    the file. The parent's peak memory is the child's result, not the partition.
    """
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=1, mp_context=context) as pool:
        return pool.submit(_write_job, target, key, tuple(columns), rows).result(timeout=timeout_s)


def _write_job(
    target: Path,
    key: str,
    columns: tuple[str, ...],
    rows: Callable[[], Iterable[Sequence[object]]],
) -> SeriesFile:
    """The child's entry point: the same writer, on rows this process streams itself."""
    return TypedWriter(target, key, columns).add(rows()).finish()
