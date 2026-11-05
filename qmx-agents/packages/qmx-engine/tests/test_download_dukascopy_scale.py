"""The Dukascopy download decodes each symbol at the scale its source names (C-31).

The script runs as the script node runs it, under `python -I`, on a month whose hourly files are
already in the run's hour cache, so nothing is fetched. The hour that holds a tick carries the
first bid and ask of 2025-03 in dukascopy-node's m15 files for that symbol
(`unit-ship/data/dukascopy-node/<symbol>-m15-{bid,ask}-2025-03-01-2025-04-01.csv`): gold at
2025-03-02T23:00Z bid 2855.205 ask 2856.475, EURUSD at 22:00Z bid 1.04032 ask 1.04033.
"""

from __future__ import annotations

import calendar
import json
import lzma
import os
import struct
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pyarrow.parquet as pq  # pyright: ignore[reportMissingTypeStubs]
import qml
from qmf.core import is_ok
from qmf.data.series import SeriesKey, SeriesStore
from qmx_home import resolve
from qmx_host.market_data import MarketDoor  # pyright: ignore[reportMissingTypeStubs]

from qmx_engine.templates.catalog import PACK

SCRIPT = PACK / "download-dukascopy" / "scripts" / "download.py"
FAILURE = "[QMX_FAILURE]"
GOLD_RECORD = Path(qml.__file__).resolve().parents[2] / "tests/fixtures/records/xauusd.json"


def bi5(ask: int, bid: int) -> bytes:
    """One hour holding one tick at the hour's start, in Dukascopy's bi5 frame."""
    return lzma.compress(struct.pack("!IIIff", 0, ask, bid, 1.0, 2.0), format=lzma.FORMAT_ALONE)


def step(tmp_path: Path, given: dict[str, Any], tick: tuple[int, int, int, int]) -> str:
    """The script on a fresh QMX folder with every hour of 2025-03 cached, even for a run that
    should fetch nothing, so no run of this file reaches the provider. The hour `tick` names
    (day, hour, ask, bid) holds that one tick."""
    folder = resolve(tmp_path / "QMX", create=True, drives=[]).root
    shared = folder / "cache" / "zones" / "run-1" / "work"
    work = tmp_path / "attempt"
    work.mkdir(parents=True, exist_ok=True)
    hours = shared / "hours" / str(given["source"]["symbol"]) / "2025" / "02"
    day, hour, ask, bid = tick
    for d in range(1, calendar.monthrange(2025, 3)[1] + 1):
        for h in range(24):
            cached = hours / f"{d:02d}" / f"{h:02d}.bi5"
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(bi5(ask, bid) if (d, h) == (day, hour) else b"")
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "TEMP", "TMP")}
    done = subprocess.run(
        [sys.executable, "-I", str(SCRIPT)],
        input=json.dumps({"in": given}),
        capture_output=True,
        text=True,
        env=env | {"QMX_WORK": str(work), "QMX_WORK_SHARED": str(shared)},
        cwd=work,
        timeout=300,
        check=True,
    )
    return done.stdout.strip()


def month(tmp_path: Path, symbol: str) -> tuple[SeriesStore, SeriesKey]:
    """The door's series store on the run's QMX folder and the 2025-03 key of `symbol`'s ticks."""
    key = SeriesKey.try_create("dukascopy", symbol, "ticks", 2025, 3)
    assert is_ok(key)
    return SeriesStore(tmp_path / "QMX" / "data" / "market" / "series"), key.value


def landed(tmp_path: Path, symbol: str) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    """The landed month's fingerprint, the card the run wrote, and the month's stored rows."""
    store, key = month(tmp_path, symbol)
    state = store.state(key)
    assert state is not None, "the month landed in the door"
    (file,) = store.folder(key).glob("*.parquet")
    rows = cast("list[dict[str, Any]]", pq.read_table(file).to_pylist())  # pyright: ignore[reportUnknownMemberType]
    card_file = tmp_path / "attempt" / "library" / "cards" / f"dukascopy_{symbol}_ticks_-.json"
    return state.fingerprint, json.loads(card_file.read_text("utf-8")), rows


def priced(row: dict[str, Any], card: dict[str, Any]) -> tuple[Decimal, Decimal]:
    """A row's bid and ask as a reader prices them: the stored integer at the card's scale."""
    scale = card["quality"]["price_scale"]
    return Decimal(row["bid"]).scaleb(-scale), Decimal(row["ask"]).scaleb(-scale)


def stated_scale(tmp_path: Path, symbol: str, kind: str = "ticks/-") -> int | None:
    """The scale a QMB run would read for the series, through the door the host opens."""
    door = MarketDoor.open(tmp_path / "QMX" / "data" / "market", {})
    assert is_ok(door)
    return door.value.price_scale(f"dukascopy/{symbol}/{kind}")


def stored_bars(tmp_path: Path, side: str) -> list[dict[str, Any]]:
    """March's EURUSD `bar-m1` rows of one side, as the store holds them."""
    store, _ = month(tmp_path, "EURUSD")
    key = SeriesKey.try_create("dukascopy", "EURUSD", "bar-m1", 2025, 3, side)
    assert is_ok(key)
    (file,) = store.folder(key.value).glob("*.parquet")
    return cast("list[dict[str, Any]]", pq.read_table(file).to_pylist())  # pyright: ignore[reportUnknownMemberType]


def nothing_landed(tmp_path: Path, symbol: str) -> bool:
    store, key = month(tmp_path, symbol)
    return store.state(key) is None


def test_gold_at_scale_three_reads_its_first_price_exactly(tmp_path: Path) -> None:
    source = {"symbol": "XAUUSD", "month": "2025-03", "price_scale": 3}

    summary = json.loads(step(tmp_path, {"source": source}, (2, 23, 2856475, 2855205)))
    _, card, rows = landed(tmp_path, "XAUUSD")

    assert (summary["status"], summary["rows"]) == ("landed", 1)
    assert rows[0]["t"] == 1740956400000
    assert priced(rows[0], card) == (Decimal("2855.205"), Decimal("2856.475"))
    assert stated_scale(tmp_path, "XAUUSD") == 3


def test_eurusd_at_scale_five_lands_the_same_month_as_before(tmp_path: Path) -> None:
    source = {"symbol": "EURUSD", "month": "2025-03", "price_scale": 5}

    step(tmp_path, {"source": source}, (2, 22, 104033, 104032))
    fingerprint, card, rows = landed(tmp_path, "EURUSD")

    assert rows[0]["t"] == 1740952800000
    assert priced(rows[0], card) == (Decimal("1.04032"), Decimal("1.04033"))
    # The parent's run of this same hour, at its constant scale of 5, landed this fingerprint.
    assert fingerprint == "e9e20ec33ed69f41bf1fe525ace93ffb44effe87a12b3605a4d32fa732cfe719"


def test_a_source_with_no_price_scale_is_refused_and_lands_nothing(tmp_path: Path) -> None:
    out = step(
        tmp_path,
        {"source": {"symbol": "XAUUSD", "month": "2025-03"}},
        (2, 23, 2856475, 2855205),
    )

    assert out == (
        f"{FAILURE} the source names no price_scale for XAUUSD; Dukascopy serves each symbol at "
        "its own scale (5 for EURUSD, 3 for XAUUSD and USDJPY), so name it"
    )
    assert nothing_landed(tmp_path, "XAUUSD")


def test_a_scale_its_instrument_record_disagrees_with_is_refused(tmp_path: Path) -> None:
    record = {"venue": "dukascopy", "symbol": "XAUUSD", "digits": 5}
    source = {"symbol": "XAUUSD", "month": "2025-03", "price_scale": 3, "instrument": record}

    out = step(tmp_path, {"source": source}, (2, 23, 2856475, 2855205))

    assert out == (
        f"{FAILURE} the source names price_scale 3 for XAUUSD, but its Dukascopy instrument "
        "record states 5 digits; correct whichever is wrong before a month lands"
    )
    assert nothing_landed(tmp_path, "XAUUSD")


def test_another_venues_record_cannot_confirm_a_dukascopy_scale(tmp_path: Path) -> None:
    ctrader_gold = json.loads(GOLD_RECORD.read_text("utf-8"))
    source = {"symbol": "XAUUSD", "month": "2025-03", "price_scale": 3, "instrument": ctrader_gold}

    out = step(tmp_path, {"source": source}, (2, 23, 2856475, 2855205))

    assert out == (
        f"{FAILURE} the instrument record is for the venue 'icmarkets-ctrader', and a Dukascopy "
        "month's scale is checked only against Dukascopy's own record, because digits differ by "
        "venue"
    )
    assert nothing_landed(tmp_path, "XAUUSD")


def test_a_gold_card_landed_at_scale_five_reads_wrong_scale(tmp_path: Path) -> None:
    source = {"symbol": "XAUUSD", "month": "2025-03", "price_scale": 3}
    card: dict[str, Any] = {
        "source": "dukascopy",
        "subject": "XAUUSD",
        "kind": "ticks",
        "series_key": "dukascopy/XAUUSD/ticks/-",
        "quality": {"volume": "liquidity", "price_scale": 5, "hours_refused": 0},
        "partitions": [{"month": "2025-02"}, {"month": "2025-03"}],
    }

    tick = (2, 23, 2856475, 2855205)
    wrong = json.loads(step(tmp_path, {"source": source, "check": card}, tick))
    card["quality"]["price_scale"] = 3
    right = json.loads(step(tmp_path / "again", {"source": source, "check": card}, tick))

    assert wrong == {
        "status": "wrong_scale",
        "series": "dukascopy/XAUUSD/ticks/-",
        "months": ["2025-02", "2025-03"],
        "card_price_scale": 5,
        "price_scale": 3,
        "note": "landed at the wrong price scale, download it again",
    }
    assert right["status"] == "scale_ok"
    assert nothing_landed(tmp_path, "XAUUSD")
    assert stated_scale(tmp_path, "XAUUSD") is None
    assert stated_scale(tmp_path / "again", "XAUUSD") == 3


def test_a_landed_month_lands_its_minute_bars_and_a_rerun_lands_the_same_rows(
    tmp_path: Path,
) -> None:
    source = {"symbol": "EURUSD", "month": "2025-03", "price_scale": 5}
    tick = (2, 22, 104033, 104032)

    first = json.loads(step(tmp_path, {"source": source}, tick))
    again = json.loads(step(tmp_path, {"source": source}, tick))

    series = ["dukascopy/EURUSD/bar-m1/bid", "dukascopy/EURUSD/bar-m1/ask"]
    assert (first["derived"], again["derived"]) == (series, series)
    assert first["fingerprint"] == again["fingerprint"]
    assert [stored_bars(tmp_path, side) for side in ("bid", "ask")] == [
        [{"t": 1740952800000, "open": 104032, "high": 104032, "low": 104032, "close": 104032, "volume": 2.0}],
        [{"t": 1740952800000, "open": 104033, "high": 104033, "low": 104033, "close": 104033, "volume": 1.0}],
    ]
    assert stated_scale(tmp_path, "EURUSD", kind="bar-m1/bid") == 5


def test_a_source_naming_no_calendar_takes_its_markets_or_says_it_has_none(tmp_path: Path) -> None:
    def landed_with(symbol: str, scale: int) -> dict[str, Any]:
        source = {"symbol": symbol, "month": "2025-03", "price_scale": scale}
        return json.loads(step(tmp_path / symbol, {"source": source}, (2, 22, 104033, 104032)))

    euro, gold, silver, bitcoin = (
        landed_with("EURUSD", 5),
        landed_with("XAUUSD", 3),
        landed_with("XAGUSD", 3),
        landed_with("BTCUSD", 1),
    )

    assert (euro["calendar"], euro["frozen"]) == ({"ref": "fx-24x5@1"}, False)
    assert (gold["calendar"], gold["frozen"]) == ({"ref": "metals-24x5@1"}, False)
    assert silver["calendar"] == {"ref": "metals-24x5@1"}
    assert "calendar" not in bitcoin
    assert bitcoin["calendar_note"] == (
        "no calendar for BTCUSD, so its open hours are not counted; name one in the source's "
        "calendar to count them"
    )
    assert "calendar_note" not in euro
    assert bitcoin["held_open"] is None
