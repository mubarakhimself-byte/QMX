"""Write the golden values QML's stdlib blocks are tested against (A4).

This script is the only QMX code that imports TA-Lib. QML and its tests read the committed
fixture and never import TA-Lib. Run it with TA-Lib 0.7.1 on a machine where it installs:

    uv run --no-project --python 3.14 --with ta-lib==0.7.1 --with numpy \
        python tools/dictionary/golden_talib.py

The close series is a seeded random walk written as five-decimal strings, so the fixture is
the same on every run; the script refuses any other TA-Lib version.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

import numpy  # pyright: ignore[reportMissingImports]
import talib  # pyright: ignore[reportMissingImports]

TALIB_VERSION = "0.7.1"
SEED = 20261101
BARS = 3000
OUT = Path(__file__).resolve().parents[2] / "qml" / "tests" / "golden" / "talib-0.7.1.json"


def _closes() -> list[str]:
    walk = random.Random(SEED)  # noqa: S311 - a seeded fixture walk, not a secret
    price = 1.10000
    closes: list[str] = []
    for _ in range(BARS):
        price = max(0.5, price * (1 + walk.gauss(0.0, 0.0012)))
        closes.append(f"{price:.5f}")
    return closes


def _series(values: Any) -> list[str | None]:
    return [None if numpy.isnan(v) else repr(float(v)) for v in values]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]


def _rolling_percentile(values: Any, percentile: float, window: int) -> list[str | None]:
    out: list[str | None] = []
    for end in range(1, len(values) + 1):
        if end < window:
            out.append(None)
            continue
        chunk = values[end - window : end]
        out.append(repr(float(numpy.percentile(chunk, percentile))))  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    return out


def _percentile_case(percentile: int) -> str:
    return f"percentile-of-own-history@1 percentile={percentile} window_bars=500 of close"


def main() -> int:
    version = str(talib.__version__)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    if version != TALIB_VERSION:
        print(f"golden_talib: TA-Lib {version} found, {TALIB_VERSION} required", file=sys.stderr)
        return 1
    closes = _closes()
    array = numpy.array([float(c) for c in closes], dtype=numpy.float64)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    rsi = talib.RSI(array, timeperiod=14)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    cases = {
        "ema@1 period=14": _series(talib.EMA(array, timeperiod=14)),  # pyright: ignore[reportUnknownMemberType]
        "ema@1 period=100": _series(talib.EMA(array, timeperiod=100)),  # pyright: ignore[reportUnknownMemberType]
        "roc-of-series@1 lookback=20": _series(talib.ROCP(array, timeperiod=20)),  # pyright: ignore[reportUnknownMemberType]
        "rsi-cross-back@1 period=14": _series(rsi),
        _percentile_case(20): _rolling_percentile(array, 20.0, 500),
        _percentile_case(80): _rolling_percentile(array, 80.0, 500),
    }
    golden = {
        "generator": "tools/dictionary/golden_talib.py",
        "talib": version,
        "numpy": str(numpy.__version__),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        "seed": SEED,
        "close": closes,
        "cases": cases,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(golden, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"golden_talib: wrote {len(cases)} cases over {BARS} bars to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
