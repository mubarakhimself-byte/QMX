"""Downloads check stamps and hold a month with an empty open hour; the data-quality block names
it (B11, LD-01, LD-03, LD-04).

The Binance downloader runs on the real engine against a bucket folder written here, so the
stamp check, the clock ledger, the door's hold and the card facts are the shipped script's own.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from flows import run_folder
from pydantic import JsonValue
from qmf.core import is_ok
from qmf.data.series import SeriesKey, SeriesStore
from qmx_home import resolve

from qmx_engine.templates.catalog import PACK, SHARED

BINANCE = PACK / "download-binance"
BLOCK = SHARED / "data-quality" / "scripts" / "data_quality.py"
MINUTE = timedelta(minutes=1)


def bucket(
    base: Path, year: int, month: int, *, micro: bool, skip_hour: datetime | None = None
) -> None:
    """One trade print a minute for every day of a month, in the bucket's own layout."""
    day = date(year, month, 1)
    while day.month == month:
        lines: list[str] = []
        moment = datetime(day.year, day.month, day.day, tzinfo=UTC)
        for index in range(1440):
            at = moment + index * MINUTE
            if skip_hour is not None and skip_hour <= at < skip_hour + timedelta(hours=1):
                continue
            stamp = int(at.timestamp()) * (1_000_000 if micro else 1000)
            lines.append(f"{index},97000.5,0.01,970.005,{stamp},true,true")
        name = f"BTCUSDT-trades-{day.isoformat()}.zip"
        folder = base / "data" / "spot" / "daily" / "trades" / "BTCUSDT"
        folder.mkdir(parents=True, exist_ok=True)
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w") as archive:
            archive.writestr(name.replace(".zip", ".csv"), "\n".join(lines) + "\n")
        (folder / name).write_bytes(payload.getvalue())
        digest = hashlib.sha256(payload.getvalue()).hexdigest()
        (folder / f"{name}.CHECKSUM").write_text(f"{digest}  {name}\n", encoding="utf-8")
        day += timedelta(days=1)


def download(home: Path, base: Path, month: str, **source: JsonValue) -> dict[str, Any]:
    named: dict[str, JsonValue] = {
        "dataset": "trades",
        "symbol": "BTCUSDT",
        "month": month,
        "base": str(base),
    }
    outcome, events = run_folder(BINANCE, home, {"source": named | source})
    assert outcome.status == "passed", outcome
    found = next(
        e.data["outputs"]
        for e in events
        if e.kind == "node_finished" and e.data["node_id"] == "download"
    )
    return cast("dict[str, Any]", found)["main"]


def test_a_microsecond_month_after_a_millisecond_month_lands_with_its_seam(tmp_path: Path) -> None:
    home, base = resolve(tmp_path / "QMX", create=True, drives=[]).home, tmp_path / "bucket"
    bucket(base, 2024, 12, micro=False)
    bucket(base, 2025, 1, micro=True)

    december = download(home, base, "2024-12")
    january = download(home, base, "2025-01")

    assert (december["source_clock"], december["seams"]) == ({"zone": "UTC", "unit": "ms"}, [])
    assert january["source_clock"] == {"zone": "UTC", "unit": "us"}
    assert january["seams"] == [
        {
            "kind": "stamp_unit",
            "at": "2025-01-01T00:00:00.000Z",
            "at_ms": 1_735_689_600_000,
            "before": "ms",
            "after": "us",
        }
    ]
    key = SeriesKey.try_create("binance", "BTCUSDT", "trades", 2025, 1)
    assert is_ok(key)
    read = SeriesStore(home / "market" / "series").read(key.value, end_ns=1_735_689_720_000_000_000)
    assert is_ok(read)
    assert [row["t"] for row in read.value.rows] == [1_735_689_600_000, 1_735_689_660_000]


def test_an_empty_open_hour_holds_the_month_unfrozen_and_the_block_names_it(tmp_path: Path) -> None:
    home, base = resolve(tmp_path / "QMX", create=True, drives=[]).home, tmp_path / "bucket"
    hole = datetime(2025, 1, 7, 10, tzinfo=UTC)
    bucket(base, 2025, 1, micro=True, skip_hour=hole)

    first = download(home, base, "2025-01")
    retry = download(home, base, "2025-01")
    agreed = download(home, base, "2025-01", confirmed_empty=["2025-01-07T10"])

    assert (first["frozen"], retry["frozen"], agreed["frozen"]) == (False, False, True)
    assert retry["held_open"] == (
        "1 empty hour(s) in open time wait for a retry and a second source to agree: "
        "2025-01-07T10:00:00.000Z"
    )
    assert retry["checked"]["empty_open_hours"] == ["2025-01-07T10:00:00.000Z"]
    assert agreed["held_open"] is None


def test_the_block_lists_the_month_s_gap_with_its_minutes(tmp_path: Path) -> None:
    home, base = resolve(tmp_path / "QMX", create=True, drives=[]).home, tmp_path / "bucket"
    bucket(base, 2025, 1, micro=False, skip_hour=datetime(2025, 1, 7, 10, tzinfo=UTC))
    landed = download(home, base, "2025-01")
    work = tmp_path / "work"
    work.mkdir()

    done = subprocess.run(
        [sys.executable, "-I", str(BLOCK)],
        input=json.dumps(
            {
                "in": {
                    "series": "binance/BTCUSDT/trades/-",
                    "month": "2025-01",
                    "calendar": "crypto-24x7@1",
                    "root": str(home / "market"),
                    "card": {"source_clock": landed["source_clock"], "seams": landed["seams"]},
                }
            }
        ),
        capture_output=True,
        text=True,
        env={k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "TEMP", "TMP")}
        | {"QMX_WORK": str(work)},
        cwd=work,
        timeout=120,
        check=True,
    )
    report = json.loads(done.stdout)

    assert report["gaps"] == [
        {"from": "2025-01-07T10:00:00.000Z", "to": "2025-01-07T11:00:00.000Z", "minutes": 60}
    ]
    assert (report["missing_minutes"], report["frozen"], report["held_open"]) == (60, False, True)
    assert report["unconfirmed_hours"] == ["2025-01-07T10:00:00.000Z"]
    assert report["source_clock"] == {"zone": "UTC", "unit": "ms"}
