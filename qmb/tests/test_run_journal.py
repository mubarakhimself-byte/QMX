"""Every QMB run keeps the unit's journal (B9, Level 0 AD-22 and AD-27, MIS-10, JR-04).

The bars are three synthetic months of EURUSD and XAUUSD M15, bid and ask, written by
``_write_window`` from a fixed seed: trend legs with regular pullbacks, so the dummy closes more
than its ``min_count`` trades on each market and its trend floor moves. Not evidence. Integer
arithmetic only, so the literal values below hold on every machine.
"""

# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import importlib.util
import json
import random
import shutil
import sys
from collections import Counter
from collections.abc import Callable, Iterator, Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from types import ModuleType
from typing import cast

import pyarrow.parquet as pq
import pytest
from qmb.host.unit_handler import Skip
from qmb.host.unit_runner import (
    LoadedUnit,
    UnitRunResult,
    load_unit_folder,
    parse_unit_run_request,
    run_loaded,
)
from qmb.results.journal import JournalReport, RunJournal
from qmf.core.chrono import Instant
from qmf.core.refusal import TypedRefusal
from qml.protocol.unit import DecisionRow
from qml.unit.model import Side
from test_unit_runner import make_run_folder

_APP = Path(__file__).resolve().parents[2] / "qmx-agents" / "apps" / "qmb"
_START = datetime(2025, 1, 1, tzinfo=UTC)
_END = datetime(2025, 4, 1, tzinfo=UTC)
# symbol: start price in points, decimals, one typical bar move in points, spread in points
_SHAPES = {"eurusd": (108_000, 5, 10, 2), "xauusd": (2_900_000, 3, 500, 250)}
_MARKETS = {"fx.eurusd": "eurusd", "metal.xauusd": "xauusd"}
_PERIOD, _LEG, _SWING = 64, 1200, 16
_MIN_COUNT = 20
"""The dummy's ``min_count`` on ``min_trend_strength``: closed trades before its first move."""

Rows = list[dict[str, object]]


def _open(at: datetime) -> bool:
    day, hour = at.weekday(), at.hour
    return not (day == 5 or (day == 4 and hour >= 22) or (day == 6 and hour < 22))


def _text(points: int, decimals: int) -> str:
    whole, part = divmod(points, 10**decimals)
    return f"{whole}.{part:0{decimals}d}"


def _write_window(folder: Path) -> None:
    rng = random.Random(1)  # noqa: S311 - a fixture's seeded walk, not a secret
    for market, symbol in _MARKETS.items():
        start, decimals, move, spread = _SHAPES[symbol]
        rows: dict[str, list[str]] = {"bid": [], "ask": []}
        at, n, level, last = _START, 0, start, start
        while at < _END:
            if _open(at):
                level += (1 if (n // _LEG) % 2 == 0 else -1) * move * 3 // 5
                wave = abs(n % _PERIOD - _PERIOD // 2) - _PERIOD // 4
                target = level + _SWING * move * wave * 4 // _PERIOD
                path = [last]
                for step in range(1, 5):
                    path.append(last + (target - last) * step // 4 + rng.randint(-move, move))
                last, n = path[-1], n + 1
                stamp = int(at.timestamp()) * 1000
                for side, offset in (("bid", 0), ("ask", spread)):
                    cells = [
                        _text(v + offset, decimals)
                        for v in (path[0], max(path), min(path), path[-1])
                    ]
                    rows[side].append(",".join([str(stamp), *cells, "0"]))
            at += timedelta(minutes=15)
        for side, lines in rows.items():
            (folder / "bars" / market / f"{side}.csv").write_text(
                "timestamp,open,high,low,close,volume\n" + "\n".join(lines) + "\n", "utf-8"
            )


@pytest.fixture(scope="module")
def run_folder(tmp_path_factory: pytest.TempPathFactory) -> Path:
    folder = make_run_folder(tmp_path_factory.mktemp("b9"))
    _write_window(folder)
    return folder


@pytest.fixture(scope="module")
def loaded(run_folder: Path) -> LoadedUnit:
    found = load_unit_folder(run_folder)
    assert not isinstance(found, TypedRefusal), found
    return found.value


def _body(loaded: LoadedUnit, **overrides: object) -> dict[str, object]:
    return {
        "run_id": "run-b9",
        "compiled_fingerprint": loaded.compiled.compiled_fingerprint.value,
        "equity": "10000.00",
        "execution_target": {"role": "demo", "venue_id": "icmarkets-ctrader", "account_id": "a"},
    } | overrides


def _journal(loaded: LoadedUnit, out: Path, run_id: str = "run-b9") -> RunJournal:
    opened = RunJournal.open(out, loaded.compiled, run_id=run_id, machine="pc", build="test")
    assert not isinstance(opened, TypedRefusal), opened
    return opened.value


def _run(loaded: LoadedUnit, journal: RunJournal, **overrides: object) -> UnitRunResult:
    parsed = parse_unit_run_request(_body(loaded, **overrides))
    assert not isinstance(parsed, TypedRefusal), parsed
    ran = run_loaded(loaded, parsed.value, journal=journal)
    assert not isinstance(ran, TypedRefusal), ran
    return ran.value


def _close(journal: RunJournal) -> JournalReport:
    closed = journal.close()
    assert not isinstance(closed, TypedRefusal), closed
    return closed.value


def _records(report: JournalReport, kind: str) -> Rows:
    rows: Rows = []
    for part in sorted((p for p in report.parts if p.kind == kind), key=lambda p: p.month):
        table = pq.read_table(part.path).to_pylist()
        rows += [json.loads(cast("str", row["record"])) for row in table]
    return rows


@pytest.fixture(scope="module")
def journaled(
    loaded: LoadedUnit, tmp_path_factory: pytest.TempPathFactory
) -> tuple[UnitRunResult, JournalReport]:
    journal = _journal(loaded, tmp_path_factory.mktemp("journal"))
    result = _run(loaded, journal)
    return result, _close(journal)


def test_the_window_closes_min_count_trades_on_each_market(
    journaled: tuple[UnitRunResult, JournalReport],
) -> None:
    result, _ = journaled

    closed = Counter(t.market_id for t in result.trades)

    assert min(closed.values()) >= _MIN_COUNT, f"the window is too short: {closed}"
    assert closed == {"fx.eurusd": 64, "metal.xauusd": 59}


def test_every_kind_lands_in_monthly_partitions_with_its_own_ids(
    journaled: tuple[UnitRunResult, JournalReport],
) -> None:
    _, report = journaled

    assert report.rows == {
        "calibration": 6,
        "data_event": 26,
        "fill": 246,
        "signal": 407,
        "state": 4,
        "trade": 123,
    }
    assert sorted({(p.kind, p.month) for p in report.parts if p.kind == "signal"}) == [
        ("signal", "2025-01"),
        ("signal", "2025-02"),
        ("signal", "2025-03"),
    ]
    signals = _records(report, "signal")
    ids = [str(s["record_id"]) for s in signals]
    assert ids == [cast("dict[str, str]", s["body"])["row_id"] for s in signals]
    assert len(set(ids)) == len(ids) == 407
    assert {s["world"] for s in signals} == {"backtest"}
    assert report.repeats == 0
    assert report.warnings == ()


def test_every_decision_carries_its_readings_value_source_and_version(
    journaled: tuple[UnitRunResult, JournalReport],
) -> None:
    _, report = journaled
    signals = _records(report, "signal")

    bodies = [cast("dict[str, object]", s["body"]) for s in signals]
    taken = next(b for b in bodies if b["outcome"] == "taken")
    readings = cast("Rows", taken["readings_used"])

    assert [(r["reading"], r["block"], r["version"], r["source"]) for r in readings] == [
        ("context.trend", "ema", "1", "unit"),
        ("context.strength", "roc-of-series", "1", "unit"),
        ("trigger.rsi_cross", "rsi-cross-back", "1", "unit"),
        ("entry_order.next_open", "market-next-open", "1", "unit"),
    ]
    assert all(isinstance(r["value"], str) and r["value"] for r in readings)
    reasons = Counter((b["outcome"], b.get("reason")) for b in bodies)
    assert reasons == {
        ("no_signal", "no_signal"): 202,
        ("taken", None): 145,
        ("skipped", "stop_wrong_side"): 23,
        ("suppressed_limit", "max_positions"): 20,
        ("suppressed_warming", "warming_up"): 17,
    }


def test_min_trend_strength_moves_on_the_runs_own_trades_with_its_receipt(
    journaled: tuple[UnitRunResult, JournalReport],
) -> None:
    _, report = journaled

    moves = [
        cast("dict[str, object]", r["body"])
        for r in _records(report, "calibration")
        if cast("dict[str, object]", r["body"])["number"] == "min_trend_strength"
    ]
    first = next(m for m in moves if m["old"] != m["new"])

    assert len(moves) == 6
    assert (first["old"], first["new"], first["rule"]) == (
        "0",
        "0.0001",
        "trend-floor-from-record@1",
    )
    assert cast("dict[str, object]", first["read_trades"])["count"] == 62


def test_a_gap_in_the_bars_is_a_data_event_the_unit_saw(
    journaled: tuple[UnitRunResult, JournalReport],
) -> None:
    _, report = journaled

    gaps = [cast("dict[str, object]", r["body"]) for r in _records(report, "data_event")]

    assert Counter(cast("str", g["market_id"]) for g in gaps) == {
        "fx.eurusd": 13,
        "metal.xauusd": 13,
    }
    assert {g["bars_missing"] for g in gaps} == {192}, "a weekend is 48 hours of M15 bars"


def test_a_slice_written_again_writes_nothing_twice(loaded: LoadedUnit, tmp_path: Path) -> None:
    journal = _journal(loaded, tmp_path)
    _run(loaded, journal)
    _run(loaded, journal)

    report = _close(journal)

    assert report.rows == {
        "calibration": 6,
        "data_event": 26,
        "fill": 246,
        "signal": 407,
        "state": 4,
        "trade": 123,
    }
    assert report.repeats == 812
    assert report.warnings == ()


def test_rsi_low_is_in_force_on_every_bar_and_follows_the_rsi(
    loaded: LoadedUnit, tmp_path: Path
) -> None:
    journal = _journal(loaded, tmp_path)
    _run(loaded, journal, trace="every_bar")
    report = _close(journal)

    long_rows = [
        cast("dict[str, object]", r["body"])
        for r in _records(report, "signal")
        if r["market_id"] == "fx.eurusd"
        and cast("dict[str, str]", r["body"])["side"] == "long"
        and not cast("dict[str, str]", r["body"])["detail"].startswith("time exit")
    ]
    levels = [cast("dict[str, str]", b["numbers_in_force"])["rsi_low"] for b in long_rows]
    held = loaded.bars()
    assert not isinstance(held, TypedRefusal), held
    bars = len(held.value["fx.eurusd"])

    changed = sum(1 for before, after in pairwise(levels) if before != after)

    assert len(long_rows) == bars == 6144
    assert levels[:514] == ["30"] * 514, "the default holds until 500 bars of RSI history"
    assert changed == 2168


def test_a_fill_the_host_refuses_is_a_blocked_signal_and_its_guard(
    loaded: LoadedUnit, tmp_path: Path
) -> None:
    journal = _journal(loaded, tmp_path)
    at = Instant(1_736_000_000_000_000_000)
    journal.at(at)
    row = DecisionRow("fp1:sha256:" + "a" * 64, at, "fx.eurusd", Side.LONG, "taken", (), {}, "")
    journal.append(row)
    journal.append(Skip(at, "fx.eurusd", row.row_id, "a position is open", Decimal(0)))

    report = _close(journal)
    signal = cast("dict[str, object]", _records(report, "signal")[0]["body"])
    guard = cast("dict[str, object]", _records(report, "guard")[0]["body"])

    assert (signal["outcome"], signal["reason"]) == ("blocked", "max_positions")
    assert (guard["decision_row_id"], guard["verdict"], guard["reason"]) == (
        row.row_id,
        "blocked",
        "max_positions",
    )


def _backtest_job() -> Callable[[Mapping[str, object]], dict[str, object]]:
    sys.path.insert(0, str(_APP))
    spec = importlib.util.spec_from_file_location("qmb_app_backtest", _APP / "jobs/backtest.py")
    assert spec is not None
    assert spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast("Callable[[Mapping[str, object]], dict[str, object]]", module.run)


@pytest.fixture
def job_folder(run_folder: Path, loaded: LoadedUnit, tmp_path: Path) -> Iterator[Path]:
    folder = tmp_path / "qmbr-pc-01JC0000000000000000000000"
    shutil.copytree(run_folder, folder / "in")
    request = _body(loaded) | {"compiled_fp": loaded.compiled.compiled_fingerprint.value}
    (folder / "in" / "request.json").write_text(json.dumps(request | {"motion": "both"}), "utf-8")
    yield folder


def test_motion_both_reports_both_runs_and_they_part_at_the_first_move(
    job_folder: Path,
) -> None:
    run = _backtest_job()

    left = run({"run_id": job_folder.name, "run_folder": str(job_folder)})
    bundle = cast("dict[str, object]", left["data"])
    report = json.loads((job_folder / "out" / "report.json").read_text("utf-8"))
    slots = [cast("dict[str, str]", f)["slot"] for f in cast("Rows", bundle["files"])]

    assert bundle["status"] == "finished"
    assert "journal/calibration/2025-01" in slots
    assert "journal/motion_off/signal/2025-03" in slots
    assert not [s for s in slots if s.startswith("journal/motion_off/calibration")]
    measures = cast("dict[str, dict[str, object]]", bundle["measures"])
    assert (measures["trades"], measures["motion_off"]["trades"]) == (123, 125)
    on, off = cast("Rows", report["trades"]), cast("Rows", report["motion_off"]["trades"])
    first_move = 1_740_049_200_000_000_000
    """The watermark of the first calibration row that moved ``min_trend_strength``."""
    before = [t for t in on if cast("int", t["closed_at"]) <= first_move]
    assert len(before) == 62
    assert off[: len(before)] == before
    shared = next(i for i, (a, b) in enumerate(zip(on, off, strict=False)) if a != b)
    assert shared == 63
