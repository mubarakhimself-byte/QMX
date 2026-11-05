"""A file that stops early says so (R09, `p2-9` with `triage-2`).

The hole check counts only between two bars a file holds, so a file that stops two weeks into its
window passes it. These runs go through `run_unit` with the window the core lays out.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
from pathlib import Path

import pytest
from qmb.data.gap_check import open_time
from qmb.host.unit_runner import run_unit
from qmf.core.refusal import TypedRefusal, is_refusal
from test_unit_runner import make_run_folder, request

EURUSD = "fx.eurusd"
MARCH = {"start": "2025-03-01", "end": "2025-04-01"}
MARCH_17_MS = 1_742_169_600_000
"""00:00 UTC on Monday 17 March 2025, where the cut file stops."""
BAR_MS = 900_000
REAL = Path(os.environ.get("QML_REAL_SLICE_DIR", "D:/QMX-worktrees/unit-ship/data/dukascopy-node"))


def cut_short(root: Path, calendar: str = "fx-24x5@1") -> Path:
    """A one-market run folder whose EURUSD files stop at 17 March, on the named calendar."""
    folder = make_run_folder(root)
    (folder / "request.json").write_text(json.dumps({"markets": [EURUSD]}), "utf-8")
    for side in ("bid", "ask"):
        path = folder / "bars" / EURUSD / f"{side}.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        kept = [rows[0], *(row for row in rows[1:] if int(row[0]) < MARCH_17_MS)]
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerows(kept)
    record = folder / "records" / f"{EURUSD}.json"
    document = json.loads(record.read_text("utf-8"))
    record.write_text(json.dumps({**document, "calendar_ref": calendar}), "utf-8")
    return folder


def test_a_file_cut_two_weeks_short_says_so(tmp_path: Path) -> None:
    folder = cut_short(tmp_path)

    refused = run_unit(folder, request(folder, window=MARCH, gap_bars_refuse=4, allow_gaps=False))
    allowed = run_unit(folder, request(folder, window=MARCH, gap_bars_refuse=4))

    assert isinstance(refused, TypedRefusal)
    assert refused.context["reason"] == (
        "fx.eurusd stops short of its window: 0 bars in open time are missing before its first bar "
        "and 1056 after its last, more than the 4 a run allows unless its study allows gaps"
    )
    assert refused.context["short"] == ((EURUSD, 0, 1056),)
    assert not is_refusal(allowed)
    assert "data_short" in allowed.value.labels
    assert [(s.market_id, s.before_first, s.after_last) for s in allowed.value.short] == [
        (EURUSD, 0, 1056)
    ]


def test_a_calendar_with_no_past_closures_only_labels(tmp_path: Path) -> None:
    folder = cut_short(tmp_path, calendar="cme-fx@1")

    ran = run_unit(folder, request(folder, window=MARCH, gap_bars_refuse=4, allow_gaps=False))

    assert not is_refusal(ran)
    assert "data_short" in ran.value.labels
    assert [(s.market_id, s.before_first, s.after_last) for s in ran.value.short] == [
        (EURUSD, 0, 1012)
    ]


def test_real_january_to_march_has_no_short_head(tmp_path: Path) -> None:
    start, end = "2025-01-01", "2025-04-01"
    markets = {EURUSD: ("eurusd", "fx-24x5@1"), "metal.xauusd": ("xauusd", "metals-24x5@1")}
    wanted = [
        REAL / f"{symbol}-m15-{side}-{start}-{end}.csv"
        for symbol, _ in markets.values()
        for side in ("bid", "ask")
    ]
    if not all(path.is_file() for path in wanted):
        pytest.skip("the real January to March months are not on this machine")
    folder = make_run_folder(tmp_path)
    ends: dict[str, tuple[int, int]] = {}
    for market, (symbol, calendar) in markets.items():
        for side in ("bid", "ask"):
            shutil.copyfile(
                REAL / f"{symbol}-m15-{side}-{start}-{end}.csv",
                folder / "bars" / market / f"{side}.csv",
            )
        hours = open_time(calendar)
        assert hours is not None
        with (folder / "bars" / market / "bid.csv").open(encoding="utf-8", newline="") as handle:
            opens = [int(row["timestamp"]) for row in csv.DictReader(handle)]
        window_start, window_end = 1_735_689_600_000, 1_743_465_600_000
        ends[market] = (
            sum(hours.open_at(t * 10**6) for t in range(window_start, opens[0], BAR_MS)),
            sum(hours.open_at(t * 10**6) for t in range(opens[-1] + BAR_MS, window_end, BAR_MS)),
        )

    ran = run_unit(folder, request(folder, window={"start": start, "end": end}, allow_gaps=False))

    assert ends == {EURUSD: (0, 0), "metal.xauusd": (0, 0)}
    assert not is_refusal(ran)
    assert "data_short" not in ran.value.labels
