"""A run folder's market store months feed the unit runner (R08).

The months hold ticks cut from QML's synthetic March 2025 CSV pair, four per bar, in the typed
partition format the market-data door copies. Its bars are 1,920 for EURUSD, the same as the CSV's.
"""

from __future__ import annotations

import csv
import json
import shutil
from decimal import Decimal
from pathlib import Path

from qmb.host.unit_runner import load_unit_folder, run_loaded
from qmf.core.refusal import TypedRefusal, is_refusal
from qmf.data.series import SeriesKey
from qmf.data.store.engines.typed import TICK_COLUMNS, TypedWriter
from test_unit_runner import _SYNTHETIC, make_run_folder, request

EURUSD = "fx.eurusd"
TICK_OFFSETS_MS = (0, 200_000, 400_000, 880_000)
"""Open, high, low and close, each at its own moment inside a 15-minute bar."""
LAST_BAR_CLOSES_NS = 1_743_199_200_000_000_000
"""22:00 UTC on Friday 28 March 2025, the end of the bar the CSV's last row opens."""


def tick_rows(symbol: str, scale: int) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    sides = [
        csv.DictReader(
            (_SYNTHETIC / f"synthetic-{symbol}-m15-{side}-2025-03-01-2025-04-01.csv").open(
                encoding="utf-8", newline=""
            )
        )
        for side in ("bid", "ask")
    ]
    for bid, ask in zip(*sides, strict=True):
        for offset, name in zip(TICK_OFFSETS_MS, ("open", "high", "low", "close"), strict=True):
            rows.append(
                (
                    int(bid["timestamp"]) + offset,
                    int(Decimal(bid[name]).scaleb(scale)),
                    int(Decimal(ask[name]).scaleb(scale)),
                    1.0,
                    1.0,
                )
            )
    return sorted(rows, key=lambda row: row[0])  # pyright: ignore[reportArgumentType, reportCallIssue, reportUnknownLambdaType]


def in_the_store(folder: Path, market: str, window: dict[str, str], **card: object) -> None:
    """Move one market of a run folder from its CSV pair to a copied month and its card."""
    symbol = market.rsplit(".", 1)[-1]
    shutil.rmtree(folder / "bars" / market)
    data = folder / "data" / market
    (data / "ticks").mkdir(parents=True)
    key = SeriesKey.try_create("dukascopy", symbol.upper(), "ticks", 2025, 3)
    assert not is_refusal(key)
    TypedWriter(data / "ticks" / "month.parquet", key.value.text, TICK_COLUMNS).add(
        tick_rows(symbol, 5)
    ).finish()
    (data / "card.json").write_text(
        json.dumps(
            {
                "kind": "ticks",
                "fidelity": "quotes",
                "series": [key.value.series],
                "window": window,
                "months": ["2025-03"],
                "files": {"ticks": ["ticks/month.parquet"]},
            }
            | card
        ),
        "utf-8",
    )


def test_one_market_of_a_two_market_unit_runs(tmp_path: Path) -> None:
    folder = make_run_folder(tmp_path)
    whole = load_unit_folder(folder)
    assert not is_refusal(whole)
    (folder / "request.json").write_text(json.dumps({"markets": [EURUSD]}), "utf-8")

    loaded = load_unit_folder(folder)
    assert not is_refusal(loaded)
    bars = {market: sum(1 for _ in feed()) for market, feed in loaded.value.feeds.items()}
    ran = run_loaded(loaded.value, request(folder))

    assert not is_refusal(ran)
    assert bars == {EURUSD: 1920}
    assert (len(ran.value.trades), ran.value.total_r) == (6, Decimal("-3.2610"))
    assert {trade.market_id for trade in ran.value.trades} == {EURUSD}
    assert loaded.value.compiled.compiled_fingerprint == whole.value.compiled.compiled_fingerprint


def test_a_series_with_no_stated_scale_is_refused_by_name(tmp_path: Path) -> None:
    folder = make_run_folder(tmp_path)
    in_the_store(folder, EURUSD, {"start": "2025-03-01", "end": "2025-04-01"})

    refused = load_unit_folder(folder)

    assert isinstance(refused, TypedRefusal)
    assert refused.context["reason"] == "dukascopy/EURUSD/ticks/- states no price scale"


def test_the_window_end_closes_the_last_bar(tmp_path: Path) -> None:
    folder = make_run_folder(tmp_path)
    in_the_store(folder, EURUSD, {"start": "2025-03-01", "end": "2025-04-01"}, scale=5)

    loaded = load_unit_folder(folder)

    assert not is_refusal(loaded)
    bars = list(loaded.value.feeds[EURUSD]())
    assert len(bars) == 1920
    assert bars[-1].knowable_at.value_ns == LAST_BAR_CLOSES_NS  # pyright: ignore[reportAttributeAccessIssue]


def test_the_window_clips_the_months_to_its_own_days(tmp_path: Path) -> None:
    folder = make_run_folder(tmp_path)
    in_the_store(folder, EURUSD, {"start": "2025-03-10", "end": "2025-03-11"}, scale=5)

    loaded = load_unit_folder(folder)

    assert not is_refusal(loaded)
    assert sum(1 for _ in loaded.value.feeds[EURUSD]()) == 96
