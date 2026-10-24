"""The CCXT top-up pages by the exchange's own declared limit and returns every bar (DR11)."""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
from typing import Any

import pytest

from qmx_engine.templates.catalog import PACK

SCRIPT = PACK / "download-ccxt" / "scripts" / "download.py"
START = 1700000000000
MINUTE = 60000


class Exchange:
    def __init__(self, features: dict[str, Any], bars: int) -> None:
        self.features = features
        self.series = [[START + i * MINUTE, 1, 2, 0.5, 1.5, 10] for i in range(bars)]
        self.calls: list[tuple[int, int | None]] = []

    def fetch_ohlcv(
        self, symbol: str, timeframe: str, since: int, limit: int | None = None
    ) -> list[list[Any]]:
        self.calls.append((since, limit))
        rows = [row for row in self.series if row[0] >= since]
        return rows[: limit or 500]


def script(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """The script's functions, loaded through its own dry-run path so nothing is fetched."""
    monkeypatch.setenv("QMX_WORK", str(tmp_path))
    monkeypatch.setattr("sys.stdin", io.StringIO('{"in": {"dry_run": true}}'))
    spec = importlib.util.spec_from_file_location("download_ccxt", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with pytest.raises(SystemExit):
        spec.loader.exec_module(module)
    return vars(module)


def test_a_declared_page_of_300_returns_every_bar_of_a_longer_range(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exchange = Exchange({"spot": {"fetchOHLCV": {"limit": 300}}}, bars=701)
    bars = script(tmp_path, monkeypatch)["fetch_bars"](
        exchange, "BTC/USDT", "1m", START, START + 1000 * MINUTE
    )
    assert len(bars) == 701
    assert bars[-1][0] == 1700042000000
    assert exchange.calls == [
        (1700000000000, 300),
        (1700018000000, 300),
        (1700036000000, 300),
        (1700042060000, 300),
    ]


def test_an_exchange_that_declares_no_limit_chooses_its_own_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exchange = Exchange({}, bars=701)
    bars = script(tmp_path, monkeypatch)["fetch_bars"](
        exchange, "BTC/USDT", "1m", START, START + 1000 * MINUTE
    )
    assert len(bars) == 701
    assert exchange.calls == [
        (1700000000000, None),
        (1700030000000, None),
        (1700042060000, None),
    ]
