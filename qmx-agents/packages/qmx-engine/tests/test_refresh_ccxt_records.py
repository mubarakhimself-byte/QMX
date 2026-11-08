"""The CCXT records refresh's script step (C-02), run as the engine runs it, on its recorded market
lists: perp records land with contract unit, funding interval and data levels, and every record
it writes is one the Library's kinds take."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from qmf.core import is_refusal
from qml.numbers import parse_record
from qmx_library.kinds import kind

from qmx_engine.templates.catalog import PACK

SCRIPT = PACK / "refresh-ccxt-records" / "scripts" / "refresh.py"
INVERSE = "inverse: money per price unit is not constant in the quote currency"


def step(work: Path, given: dict[str, Any]) -> str:
    """The script under `python -I`, its inputs on stdin under `in`, as the script node runs it."""
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "TEMP", "TMP")}
    done = subprocess.run(
        [sys.executable, "-I", str(SCRIPT)],
        input=json.dumps({"in": given}),
        capture_output=True,
        text=True,
        env=env | {"QMX_WORK": str(work)},
        cwd=work,
        timeout=120,
        check=True,
    )
    return done.stdout


def written(work: Path, folder: str) -> dict[str, dict[str, Any]]:
    return {
        path.name: json.loads(path.read_text("utf-8"))
        for path in sorted((work / "library" / folder).glob("*.json"))
    }


def test_the_fixture_refresh_lands_perp_futures_and_spot_records_and_says_what_it_skipped(
    tmp_path: Path,
) -> None:
    summary = json.loads(step(tmp_path, {"fixture": True}))
    records = written(tmp_path, "instruments")

    assert summary["status"] == "refreshed" and summary["source"] == "fixture"
    assert summary["venues"] == {
        "binance": {"records": 5, "skipped": {INVERSE: 1}},
        "hyperliquid": {"records": 4, "skipped": {}},
    }
    assert isinstance(summary["seconds"], float)
    assert records["hyperliquid__BTC_USDC_USDC.json"] == {
        "venue": "hyperliquid",
        "symbol": "BTC/USDC:USDC",
        "market_id": "btc",
        "class": "perp",
        "currency": "USDC",
        "digits": 0,
        "tick_size": "1",
        "contract_size": "1",
        "value_per_point": "1",
        "value_conversion": {"symbol": "USDC", "method": "linear_in_quote"},
        "conversion_check": {"ways": {"contract_size": "1"}, "tolerance": "0.001", "agrees": None},
        "lot_step": "0.00001",
        "min_lot": "0.00001",
        "calendar_ref": "crypto-24x7@1",
        "zone": "UTC",
        "day_boundary": "00:00",
        "data_levels": {
            "schema": "qmx.data-level/1",
            "levels": [0, 1, 3, 4, 5],
            "volume": "exchange",
            "depth": "by_price",
            "derivatives_clock": "live",
            "history": "provider_limited",
            "licence": "exchange-public-api",
        },
        "leverage": {"version": 1, "tiers": [{"leverage": "40"}]},
        "margin": {"intraday": "0.025", "overnight": "0.025"},
        "funding_interval": "PT1H",
        "funding_source": "hyperliquid: perps pay funding every hour",
        "status": "live",
    }
    binance = {r["symbol"]: r for r in records.values() if r["venue"] == "binance"}
    assert {s: (r["funding_interval"], r["funding_source"]) for s, r in binance.items()
            if r["class"] == "perp"} == {
        "BTC/USDT:USDT": ("PT8H", "binance: every 8 hours unless fundingInfo lists the symbol"),
        "ETH/USDT:USDT": ("PT4H", "binance: fundingInfo"),
    }  # fmt: skip
    near, far = binance["BTC/USDT:USDT-261225"], binance["BTC/USDT:USDT-270326"]
    assert (near["root"], near["expiry"], near["rolls_to"]) == (
        "BTC/USDT:USDT",
        "2026-12-25T08:00:00.000Z",
        "BTC/USDT:USDT-270326",
    )
    assert "rolls_to" not in far
    assert records["hyperliquid__OLD_USDC_USDC.json"]["status"] == "delisted"
    assert (binance["BTC/USDT"]["class"], binance["BTC/USDT"]["contract_size"]) == (
        "spot_crypto",
        "1",
    )


def test_every_written_record_is_one_the_library_takes_and_qml_reads_where_it_is_full(
    tmp_path: Path,
) -> None:
    step(tmp_path, {"fixture": True})
    records = written(tmp_path, "instruments")
    venues = written(tmp_path, "venues")

    for fields in records.values():
        kind("instrument").check(fields, set())
    for fields in venues.values():
        kind("venue").check(fields, set())
    hyperliquid = parse_record(records["hyperliquid__ETH_USDC_USDC.json"] | {"record_version": 1})
    binance = parse_record(records["binance__BTC_USDT_USDT.json"] | {"record_version": 1})

    assert not is_refusal(hyperliquid) and hyperliquid.value.tick_size.as_tuple().exponent == -1
    assert is_refusal(binance)
    assert binance.context["problems"] == (
        "/leverage: the required key is missing",
        "/margin: the required key is missing",
    )
    assert venues["hyperliquid.json"]["trigger_basis"] == "mark"
    assert venues["hyperliquid.json"]["data_levels"] == {
        "schema": "qmx.data-level/1",
        "levels": [0, 1, 3, 4, 5],
    }
    assert venues["binance.json"]["rate_limits"] == {"ccxt_rate_limit_ms": 50}


def test_an_exchange_with_no_record_profile_fails_the_step_and_writes_nothing(
    tmp_path: Path,
) -> None:
    out = step(tmp_path, {"fixture": True, "exchanges": ["kraken"]})

    assert out == "[QMX_FAILURE] no record profile for kraken\n"
    assert written(tmp_path, "instruments") == {}
