"""A landed tick month folds into `bar-m1` pairs that a run reads as it reads the ticks (R09).

The ticks are cut from QML's synthetic March 2025 EURUSD pair, four per 15-minute bar at four
different minutes, as `bridge.py` cuts them, and they go through the real door.
"""

from __future__ import annotations

import csv
import json
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from qmb.host.unit_runner import load_unit_folder, parse_unit_run_request, run_loaded
from qmf.core import is_ok, is_refusal
from qmf.data.series import SeriesKey
from qmf.data.store.engines.typed import TICK_COLUMNS, TypedWriter
from qmx_host.market_data import MarketDoor, Placement  # pyright: ignore[reportMissingTypeStubs]

from qmx_tools.derive_bars import derive_month
from qmx_tools.gather import FIXTURE_RECORDS, _own, template  # pyright: ignore[reportPrivateUsage]

SLICES = Path(__file__).resolve().parents[4] / "qml" / "tests" / "fixtures" / "slices"
EURUSD = "fx.eurusd"
TICKS = "dukascopy/EURUSD/ticks/-"
MARCH = {"start": "2025-03-01", "end": "2025-04-01"}
TICK_OFFSETS_MS = (0, 200_000, 400_000, 880_000)


def slice_csv(side: str) -> Path:
    return SLICES / f"synthetic-eurusd-m15-{side}-2025-03-01-2025-04-01.csv"


def door_with_ticks(root: Path) -> MarketDoor:
    """A real door holding the cut month at a stated scale of 5, as the download leaves it."""
    opened = MarketDoor.open(root / "market", {}, placement=Placement.PC)
    assert is_ok(opened)
    door = opened.value
    rows: list[tuple[int, int, int, float, float]] = []
    with (
        slice_csv("bid").open(encoding="utf-8", newline="") as bids,
        slice_csv("ask").open(encoding="utf-8", newline="") as asks,
    ):
        for bid, ask in zip(csv.DictReader(bids), csv.DictReader(asks), strict=True):
            for offset, name in zip(TICK_OFFSETS_MS, ("open", "high", "low", "close"), strict=True):
                rows.append(
                    (
                        int(bid["timestamp"]) + offset,
                        int(Decimal(bid[name]).scaleb(5)),
                        int(Decimal(ask[name]).scaleb(5)),
                        1.0,
                        2.0,
                    )
                )
    rows.sort(key=lambda row: row[0])
    key = SeriesKey.try_create("dukascopy", "EURUSD", "ticks", 2025, 3)
    assert is_ok(key)
    staged = root / "staging" / "dukascopy" / "EURUSD" / "ticks" / "-" / "2025-03.parquet"
    staged.parent.mkdir(parents=True)
    TypedWriter(staged, key.value.text, TICK_COLUMNS).add(rows).finish()
    assert is_ok(door.commit([staged], staging=root / "staging"))
    assert is_ok(door.state_scale(TICKS, 5))
    return door


def run_folder(root: Path) -> Path:
    """A run folder for the fixture unit on EURUSD alone, with no market data yet."""
    folder = root / "in"
    (folder / "records").mkdir(parents=True)
    document = template()
    (folder / "unit.json").write_text(json.dumps(document), "utf-8")
    for pin in cast("list[dict[str, object]]", document["pins"]):
        name = f"{pin['entry_id']}@{pin['version']}"
        own = _own(name)
        assert own is not None
        (folder / "blocks" / name).mkdir(parents=True)
        (folder / "blocks" / name / "entry.json").write_bytes(own[0])
        (folder / "blocks" / name / "block.py").write_bytes(own[1])
    for market, symbol in ((EURUSD, "eurusd"), ("metal.xauusd", "xauusd")):
        shutil.copyfile(FIXTURE_RECORDS / f"{symbol}.json", folder / "records" / f"{market}.json")
    (folder / "request.json").write_text(json.dumps({"markets": [EURUSD]}), "utf-8")
    return folder


def by_csv(root: Path) -> Path:
    folder = run_folder(root)
    (folder / "bars" / EURUSD).mkdir(parents=True)
    for side in ("bid", "ask"):
        shutil.copyfile(slice_csv(side), folder / "bars" / EURUSD / f"{side}.csv")
    return folder


def by_store(root: Path, door: MarketDoor, kind: str, sides: dict[str, str]) -> Path:
    """A run folder laid out as the host lays one: verified copies beside their card."""
    folder = run_folder(root)
    data = folder / "data" / EURUSD
    files: dict[str, list[str]] = {}
    for side, series in sides.items():
        card = door.card(series)
        assert is_ok(card)
        partitions: Any = card.value["partitions"]
        copied = door.materialise([partitions[0]["fingerprint"]], into=data / side)
        assert is_ok(copied)
        files[side] = [path.relative_to(data).as_posix() for path in copied.value]
    (data / "card.json").write_text(
        json.dumps(
            {
                "kind": kind,
                "scale": 5,
                "series": list(sides.values()),
                "window": MARCH,
                "files": files,
            }
        ),
        "utf-8",
    )
    return folder


def trades_and_bars(folder: Path) -> tuple[Any, ...]:
    loaded = load_unit_folder(folder)
    assert is_ok(loaded)
    bars = list(loaded.value.feeds[EURUSD]())
    body = {
        "run_id": "r09",
        "compiled_fingerprint": loaded.value.compiled.compiled_fingerprint.value,
        "equity": "10000.00",
        "execution_target": {"role": "paper-validation", "venue_id": "qmb", "account_id": "b"},
        "allow_gaps": True,
    }
    request = parse_unit_run_request(body)
    assert is_ok(request)
    ran = run_loaded(loaded.value, request.value)
    assert is_ok(ran)
    return bars, ran.value.trades, ran.value.total_r


def test_derived_pairs_give_the_same_bars_and_trades_as_the_ticks(tmp_path: Path) -> None:
    door = door_with_ticks(tmp_path)

    landed = derive_month(door, TICKS, 2025, 3, staging=tmp_path / "staging")

    assert is_ok(landed)
    csv_bars, csv_trades, csv_r = trades_and_bars(by_csv(tmp_path / "csv"))
    tick_bars, tick_trades, _ = trades_and_bars(
        by_store(tmp_path / "ticks", door, "ticks", {"ticks": TICKS})
    )
    pair_bars, pair_trades, pair_r = trades_and_bars(
        by_store(
            tmp_path / "pairs",
            door,
            "bar-m1",
            {"bid": "dukascopy/EURUSD/bar-m1/bid", "ask": "dukascopy/EURUSD/bar-m1/ask"},
        )
    )
    assert len(pair_bars) == 1920
    assert pair_bars == tick_bars == csv_bars
    # RC-11 runs every exit each bar on the side's bars; all three feeds land this R.
    assert (len(pair_trades), pair_r) == (6, Decimal("-3.2846"))
    assert pair_trades == tick_trades == csv_trades
    assert csv_r == pair_r


def test_deriving_twice_lands_the_same_fingerprints(tmp_path: Path) -> None:
    door = door_with_ticks(tmp_path)
    staging = tmp_path / "staging"

    held = derive_month(door, TICKS, 2025, 3, staging=staging, hold="an empty hour waits")
    still_held = derive_month(door, TICKS, 2025, 3, staging=staging, hold="an empty hour waits")
    rerun = derive_month(door, TICKS, 2025, 3, staging=staging)

    assert is_ok(held)
    assert is_ok(still_held)
    assert is_ok(rerun)
    assert [receipt.key.series for receipt in rerun.value] == [
        "dukascopy/EURUSD/bar-m1/bid",
        "dukascopy/EURUSD/bar-m1/ask",
    ]
    assert [receipt.rows for receipt in rerun.value] == [7680, 7680]
    assert [r.fingerprint for r in held.value] == [r.fingerprint for r in rerun.value]
    assert [r.frozen for r in (*held.value, *still_held.value, *rerun.value)] == [
        False,
        False,
        False,
        False,
        True,
        True,
    ]
    assert door.price_scale("dukascopy/EURUSD/bar-m1/bid") == 5
    assert door.price_scale("dukascopy/EURUSD/bar-m1/ask") == 5
    assert [path.name for path in staging.iterdir()] == ["dukascopy"]


def test_a_month_or_a_scale_the_door_does_not_hold_is_refused_by_name(tmp_path: Path) -> None:
    door = door_with_ticks(tmp_path)
    staging = tmp_path / "staging"

    no_month = derive_month(door, TICKS, 2025, 4, staging=staging)
    no_scale = derive_month(door, "dukascopy/GBPUSD/ticks/-", 2025, 3, staging=staging)

    assert is_refusal(no_month)
    assert no_month.context["reason"] == "dukascopy/EURUSD/ticks/- holds no 2025-04 to derive"
    assert is_refusal(no_scale)
    assert no_scale.context["reason"] == "dukascopy/GBPUSD/ticks/- states no price scale"
