"""Journal months as typed partitions: staged, committed, read back, frozen (AD-209)."""

# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import itertools
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

import pyarrow.parquet as pq
from qmf.core import Result, is_ok, is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_writer import AppendOutcome, JournalWriter, WriterScope, stage
from qmf.data.series import SeriesKey, SeriesStore, rule_for
from qmf.data.store.engines.typed import TICK_COLUMNS

T = TypeVar("T")

_START_NS = 1_772_409_600_000_000_000  # 2026-03-02T00:00:00Z
_FACTS = RowFacts(ts_recv=_START_NS, clock_ok=True, unit_id="u-dummy")
_SIGNAL = {"row_id": "fp1:sha256:aa", "instant": 1_000, "outcome": "taken"}


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _clock() -> Callable[[], int]:
    ticks = itertools.count(_START_NS, 1_000_000)
    return lambda: next(ticks)


def _hot(root: Path, scope: WriterScope) -> JournalWriter:
    return _ok(JournalWriter.open(root, scope, clock=_clock(), boot_epoch_id="boot-1"))


def _rows(path: Path) -> list[tuple[object, ...]]:
    return [tuple(row.values()) for row in pq.read_table(path).to_pylist()]


def test_a_journal_month_commits_reads_back_and_freezes_after_its_settlement_day(
    tmp_path: Path,
) -> None:
    scope = WriterScope(JournalStream.UNIT, "u-dummy", JournalWorld.PAPER, "pc-1", "node", "b8")
    writer = _hot(tmp_path / "streams", scope)
    writer.append("signal", _SIGNAL, _FACTS)
    writer.append("signal", {**_SIGNAL, "row_id": "fp1:sha256:bb"}, _FACTS)
    (staged,) = _ok(stage(tmp_path / "streams", tmp_path / "staging"))
    key = _ok(SeriesKey.try_create("journal-unit", "u-dummy", "signal", 2026, 3, "paper.pc-1"))
    rows = _rows(staged.path)
    early = SeriesStore(tmp_path / "store", wall=lambda: datetime(2026, 4, 1, 12, tzinfo=UTC))
    late = SeriesStore(tmp_path / "store", wall=lambda: datetime(2026, 4, 2, 1, tzinfo=UTC))

    first = _ok(early.commit(key, rows))
    again = _ok(early.commit(key, rows))
    frozen = _ok(late.commit(key, rows))
    read = _ok(late.read(key))

    assert staged.path == tmp_path / "staging/journal-unit/u-dummy/signal/paper.pc-1/2026-03.parquet"
    assert (first.frozen, again.frozen, frozen.frozen) == (False, False, True)
    assert again.fingerprint == first.fingerprint
    records = [json.loads(str(row["record"])) for row in read.rows]
    assert [(record["seq"], record["record_id"]) for record in records] == [
        (0, "fp1:sha256:aa"),
        (1, "fp1:sha256:bb"),
    ]
    assert [row["seq"] for row in read.rows] == [0, 1]


def test_price_kinds_keep_their_columns() -> None:
    assert rule_for("dukascopy", "ticks").columns == TICK_COLUMNS
    assert rule_for("journal-market", "minute").columns == ("t", "seq", "record")


def test_series_rows_stage_as_their_store_kind(tmp_path: Path) -> None:
    scope = WriterScope(JournalStream.MARKET, "EURUSD", JournalWorld.LIVE, "pc-1", "recorder", "b8")
    writer = _hot(tmp_path / "streams", scope)
    t0 = _START_NS // 1_000_000
    bar = (t0, 108_000, 108_050, 107_990, 108_020, 12.5)

    writer.append_series("recorded", "EURUSD", "bar-m1", bar)
    backwards = writer.append_series("recorded", "EURUSD", "bar-m1", (t0 - 60_000, 1, 1, 1, 1, None))
    (staged,) = _ok(stage(tmp_path / "streams", tmp_path / "staging"))

    assert is_refusal(backwards)
    assert _rows(staged.path) == [bar]


def test_bundle_mode_writes_the_run_journal_as_partition_files(tmp_path: Path) -> None:
    scope = WriterScope(JournalStream.UNIT, "u-dummy", JournalWorld.BACKTEST, "pc-1", "qmb", "b8")
    writer = _ok(JournalWriter.open_bundle(tmp_path / "out", scope, clock=_clock()))

    writer.append("signal", _SIGNAL, _FACTS)
    repeat = _ok(writer.append("signal", _SIGNAL, _FACTS))
    (written,) = _ok(writer.close())

    assert repeat.outcome is AppendOutcome.REPEAT
    assert written.rows == 1
    assert written.path == tmp_path / "out/journal-unit/u-dummy/signal/backtest.pc-1/2026-03.parquet"
