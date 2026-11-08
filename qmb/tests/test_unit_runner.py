"""QMB trades the dummy unit from a run folder through the shared handler (B5b).

The bars are QML's synthetic EURUSD and XAUUSD month (``qml/tests/fixtures/slices``), so the
literal values below hold on every machine. ``test_the_real_dukascopy_month_trades`` reads the
real March 2025 month from ``QMB_REAL_SLICE_DIR`` when it is present (personal use, never
committed) and is skipped otherwise.
"""

from __future__ import annotations

import json
import os
import shutil
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qmb.host.unit_handler import FillKind
from qmb.host.unit_runner import (
    ZERO_TRADES,
    UnitRunRequest,
    UnitRunResult,
    load_unit_folder,
    parse_unit_run_request,
    run_unit,
)
from qmf.core.refusal import RefusalCategory, TypedRefusal, is_refusal
from qml.blocks.api import EntryFace, parse_entry
from qml.numbers import lots, parse_record

_REPO = Path(__file__).resolve().parents[2]
_QML = _REPO / "qml"
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_DUMMY = _QML / "src" / "qml" / "unit" / "templates" / "dummy-trend-pullback.json"
_SYNTHETIC = _QML / "tests" / "fixtures" / "slices"
_REAL = Path(os.environ.get("QMB_REAL_SLICE_DIR", "D:/QMX-worktrees/unit-ship/data/dukascopy-node"))
_MARKETS = {"fx.eurusd": "eurusd", "metal.xauusd": "xauusd"}
CORPUS = _QML / "tests" / "corpus"


def dummy_document() -> dict[str, object]:
    document = cast("dict[str, object]", json.loads(_DUMMY.read_text("utf-8")))
    pins: list[dict[str, object]] = []
    for folder in sorted(p for p in _STDLIB.iterdir() if (p / "1" / "entry.json").is_file()):
        face = parse_entry((folder / "1" / "entry.json").read_bytes())
        assert isinstance(face, EntryFace), face
        pins.append({"entry_id": face.entry_id, "version": 1, "fingerprint": face.fingerprint})
    document["pins"] = pins
    return document


def make_run_folder(
    root: Path,
    document: dict[str, object] | None = None,
    *,
    bars: Path = _SYNTHETIC,
    prefix: str = "synthetic-",
) -> Path:
    """A run folder as the core lays it out: the unit, its pinned blocks, records and bars."""
    folder = root / "run"
    folder.mkdir()
    (folder / "unit.json").write_text(json.dumps(document or dummy_document()), "utf-8")
    for block in (p for p in _STDLIB.iterdir() if (p / "1" / "block.py").is_file()):
        pin = folder / "blocks" / f"{block.name}@1"
        pin.mkdir(parents=True)
        shutil.copyfile(block / "1" / "block.py", pin / "block.py")
        shutil.copyfile(block / "1" / "entry.json", pin / "entry.json")
    (folder / "records").mkdir()
    for market, symbol in _MARKETS.items():
        shutil.copyfile(
            _QML / "tests" / "fixtures" / "records" / f"{symbol}.json",
            folder / "records" / f"{market}.json",
        )
        (folder / "bars" / market).mkdir(parents=True)
        for side in ("bid", "ask"):
            shutil.copyfile(
                bars / f"{prefix}{symbol}-m15-{side}-2025-03-01-2025-04-01.csv",
                folder / "bars" / market / f"{side}.csv",
            )
    return folder


def request(folder: Path, **overrides: object) -> UnitRunRequest:
    loaded = load_unit_folder(folder)
    assert not isinstance(loaded, TypedRefusal), loaded
    body: dict[str, object] = {
        "run_id": "run-b5b",
        "compiled_fingerprint": loaded.value.compiled.compiled_fingerprint.value,
        "equity": "10000.00",
        "execution_target": {"role": "demo", "venue_id": "icmarkets-ctrader", "account_id": "a"},
    } | overrides
    parsed = parse_unit_run_request(body)
    assert not isinstance(parsed, TypedRefusal), parsed
    return parsed.value


def _run(folder: Path) -> UnitRunResult:
    result = run_unit(folder, request(folder))
    assert not isinstance(result, TypedRefusal), result
    return result.value


def _eurusd_lots(amount: Decimal) -> Decimal:
    record = parse_record(json.loads((_QML / "tests/fixtures/records/eurusd.json").read_text()))
    assert not isinstance(record, TypedRefusal)
    sized = lots(amount, record.value)
    assert not isinstance(sized, TypedRefusal)
    return Decimal(sized.value.value).scaleb(-sized.value.scale)


def test_the_dummy_trades_the_month_and_every_fill_is_its_receipt_after_lot_rounding(
    tmp_path: Path,
) -> None:
    result = _run(make_run_folder(tmp_path))

    entries = [f for f in result.fills if f.kind is FillKind.ENTRY]
    assert len(result.trades) == 8
    assert [(f.market_id, f.side.value, f.quantity, f.receipt_quantity) for f in entries[:2]] == [
        ("fx.eurusd", "short", Decimal("1.72"), Decimal("1.72")),
        ("fx.eurusd", "short", Decimal("1.08"), Decimal("1.08")),
    ]
    assert all(
        f.quantity == _eurusd_lots(cast("Decimal", f.receipt_quantity))
        for f in entries
        if f.market_id == "fx.eurusd"
    )
    assert all(f.quantity == f.receipt_quantity for f in entries)
    first, last = result.trades[0], result.trades[-1]
    assert (first.exit_kind, first.money, first.r) == (
        FillKind.STOP,
        Decimal("-49.88"),
        Decimal("-1.0000"),
    )
    assert (last.exit_kind, last.money, last.r) == (
        FillKind.TARGET,
        Decimal("95.38"),
        Decimal("2.0013"),
    )
    assert result.net_money == Decimal("-114.97")
    assert result.total_r == Decimal("-2.2597")
    assert result.labels == ()


def test_no_entry_fills_before_the_derived_warm_up(tmp_path: Path) -> None:
    folder = make_run_folder(tmp_path)
    loaded = load_unit_folder(folder)
    assert not isinstance(loaded, TypedRefusal)
    warm = loaded.value.compiled.warm_up["m15"]
    result = _run(folder)

    for fill in (f for f in result.fills if f.kind is FillKind.ENTRY):
        stamps = [b.knowable_at for b in loaded.value.bars[fill.market_id]]
        assert stamps.index(fill.instant) >= warm


def test_a_compiled_fingerprint_other_than_the_pinned_one_refuses_at_start(
    tmp_path: Path,
) -> None:
    folder = make_run_folder(tmp_path)
    pinned = request(folder, compiled_fingerprint="fp1:sha256:" + "0" * 64)

    result = run_unit(folder, pinned)

    assert is_refusal(result)
    assert result.category is RefusalCategory.POLICY_REJECTION
    assert result.context["field"] == "compiled_fingerprint"


def test_a_unit_that_never_trades_is_labelled_zero_trades(tmp_path: Path) -> None:
    document = dummy_document()
    numbers = cast("dict[str, dict[str, object]]", document["numbers"])
    numbers["min_trend_strength"]["default"] = numbers["min_trend_strength"]["range"]["max"]  # type: ignore[index]

    result = _run(make_run_folder(tmp_path, document))

    assert result.trades == ()
    assert result.labels == (ZERO_TRADES,)


def test_a_request_with_a_float_equity_is_refused() -> None:
    body = {
        "run_id": "r",
        "compiled_fingerprint": "fp1:sha256:" + "0" * 64,
        "equity": 10000.0,
        "execution_target": {"role": "demo", "venue_id": "v", "account_id": "a"},
    }

    refused = parse_unit_run_request(body)

    assert is_refusal(refused)
    assert refused.context["field"] == "equity"


@pytest.mark.skipif(not _REAL.is_dir(), reason="the real Dukascopy month is not on this machine")
def test_the_real_dukascopy_month_trades(tmp_path: Path) -> None:
    result = _run(make_run_folder(tmp_path, bars=_REAL, prefix=""))

    entries = [f for f in result.fills if f.kind is FillKind.ENTRY]
    assert entries
    assert all(f.quantity == f.receipt_quantity for f in entries)
