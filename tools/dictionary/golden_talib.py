"""Write the golden values QML's stdlib blocks are tested against (A4, A13a).

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
from typing import Any, cast

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


INDICATORS_OUT = OUT.parent / "indicators" / "talib-0.7.1.json"
INDICATOR_SEED = 20261102
INDICATOR_BARS = 1000
BAR_NS = 15 * 60 * 10**9
FIRST_CLOSE_NS = 1_767_571_200 * 10**9 + BAR_NS
"""The first M15 bar closes at 2026-01-05 00:15 UTC, a Monday."""
DAY_NS = 86_400 * 10**9

TA: Any = talib
NP: Any = numpy
Values = list[float | None]


def _bars() -> list[dict[str, Any]]:
    walk = random.Random(INDICATOR_SEED)  # noqa: S311 - a seeded fixture walk, not a secret
    close = 1.10000
    bars: list[dict[str, Any]] = []
    for i in range(INDICATOR_BARS):
        opened = close
        close = max(0.5, opened * (1 + walk.gauss(0.0, 0.0012)))
        high = max(opened, close) * (1 + abs(walk.gauss(0.0, 0.0006)))
        low = min(opened, close) * (1 - abs(walk.gauss(0.0, 0.0006)))
        bars.append(
            {
                "open": f"{opened:.5f}",
                "high": f"{high:.5f}",
                "low": f"{low:.5f}",
                "close": f"{close:.5f}",
                "volume": str(walk.randint(40, 600)),
                "time": FIRST_CLOSE_NS + i * BAR_NS,
            }
        )
    return bars


def _plain(values: Values) -> list[str | None]:
    return [None if v is None else repr(float(v)) for v in values]


def _list(array: Any) -> Values:
    return [None if NP.isnan(v) else float(v) for v in array]


def _smma(values: Values, period: int) -> Values:
    """MetaQuotes' smoothed moving average: the simple mean of the first ``period`` values,
    then ``(previous * (period - 1) + value) / period``."""
    out: Values = [None] * len(values)
    known = [v for v in values if v is not None]
    start = len(values) - len(known)
    if len(known) < period:
        return out
    level = sum(known[:period]) / period
    out[start + period - 1] = level
    for i in range(start + period, len(values)):
        level = (level * (period - 1) + cast(float, values[i])) / period
        out[i] = level
    return out


def _shift(values: Values, bars: int) -> Values:
    return [None] * bars + values[: len(values) - bars] if bars else list(values)


def _sessions(bars: list[dict[str, Any]], start_seconds: int) -> list[int]:
    return [(int(b["time"]) - 1 - start_seconds * 10**9) // DAY_NS for b in bars]


def _session_runs(bars: list[dict[str, Any]], start_seconds: int) -> tuple[Values, Values, Values]:
    vwap: Values = []
    highs: Values = []
    lows: Values = []
    day = None
    weighted = volume = 0.0
    high = low = 0.0
    for bar, session in zip(bars, _sessions(bars, start_seconds), strict=True):
        h, lo, c, v = (float(bar[k]) for k in ("high", "low", "close", "volume"))
        if session != day:
            day, weighted, volume, high, low = session, 0.0, 0.0, h, lo
        weighted += (h + lo + c) / 3 * v
        volume += v
        high, low = max(high, h), min(low, lo)
        vwap.append(weighted / volume if volume > 0 else None)
        highs.append(high)
        lows.append(low)
    return vwap, highs, lows


def _heikin_ashi(bars: list[dict[str, Any]]) -> tuple[Values, Values]:
    opens: Values = []
    closes: Values = []
    for bar in bars:
        o, h, lo, c = (float(bar[k]) for k in ("open", "high", "low", "close"))
        ha_close = (o + h + lo + c) / 4
        ha_open = (cast(float, opens[-1]) + cast(float, closes[-1])) / 2 if closes else (o + c) / 2
        opens.append(ha_open)
        closes.append(ha_close)
    return opens, closes


def _rvi(o: Values, h: Values, lo: Values, c: Values, period: int) -> tuple[Values, Values]:
    def weighted(values: list[float], i: int) -> float:
        return (values[i] + 2 * values[i - 1] + 2 * values[i - 2] + values[i - 3]) / 6

    body = [cast(float, c[i]) - cast(float, o[i]) for i in range(len(c))]
    span = [cast(float, h[i]) - cast(float, lo[i]) for i in range(len(c))]
    move = NP.array([NP.nan] * 3 + [weighted(body, i) for i in range(3, len(c))])
    reach = NP.array([NP.nan] * 3 + [weighted(span, i) for i in range(3, len(c))])
    rvi = _list(TA.SUM(move, timeperiod=period) / TA.SUM(reach, timeperiod=period))
    signal: Values = [None] * len(rvi)
    for i in range(3, len(rvi)):
        window = rvi[i - 3 : i + 1]
        if all(v is not None for v in window):
            r = cast(list[float], window)
            signal[i] = (r[3] + 2 * r[2] + 2 * r[1] + r[0]) / 6
    return rvi, signal


def _indicators(version: str) -> dict[str, Any]:
    bars = _bars()
    o, h, lo, c, v = (
        NP.array([float(b[k]) for b in bars], dtype=NP.float64)
        for k in ("open", "high", "low", "close", "volume")
    )
    med = TA.MEDPRICE(h, lo)
    ema12, ema26 = TA.EMA(c, timeperiod=12), TA.EMA(c, timeperiod=26)
    macd = ema12 - ema26
    signal = TA.EMA(macd, timeperiod=9)
    upper, middle, lower = TA.BBANDS(c, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    sma14 = TA.SMA(c, timeperiod=14)
    ao = TA.SMA(med, timeperiod=5) - TA.SMA(med, timeperiod=34)
    wma10, wma20 = TA.WMA(c, timeperiod=10), TA.WMA(c, timeperiod=20)
    jaw, teeth, lips = (_shift(_smma(_list(med), p), s) for p, s in ((13, 8), (8, 5), (5, 3)))
    rise = NP.concatenate(([NP.nan], NP.maximum(h[1:] - h[:-1], 0.0)))
    fall = NP.concatenate(([NP.nan], NP.maximum(lo[:-1] - lo[1:], 0.0)))
    demax, demin = TA.SMA(rise, timeperiod=14), TA.SMA(fall, timeperiod=14)
    force = NP.concatenate(([NP.nan], (c[1:] - c[:-1]) * v[1:]))
    ema13 = TA.EMA(c, timeperiod=13)
    fastk, _ = TA.STOCHF(h, lo, c, fastk_period=5, fastd_period=1, fastd_matype=0)
    _, slowd = TA.STOCH(h, lo, c, 5, 3, 0, 3, 0)
    down, up = TA.AROON(h, lo, timeperiod=14)
    mid9, mid26 = TA.MIDPRICE(h, lo, timeperiod=9), TA.MIDPRICE(h, lo, timeperiod=26)
    rvi, rvi_signal = _rvi(_list(o), _list(h), _list(lo), _list(c), 10)
    vwap, session_high, session_low = _session_runs(bars, 0)
    _, london_high, london_low = _session_runs(bars, 28_800)
    ha_open, ha_close = _heikin_ashi(bars)

    def gap(a: Values, b: Values) -> Values:
        return [None if x is None or y is None else abs(x - y) for x, y in zip(a, b, strict=True)]

    def span(a: Values, b: Values) -> Values:
        return [None if x is None or y is None else x - y for x, y in zip(a, b, strict=True)]

    talib_cases: dict[str, Any] = {
        "moving-average-simple@1 period=20": TA.SMA(c, timeperiod=20),
        "moving-average-linear-weighted@1 period=20": wma20,
        "moving-average-double-exponential@1 period=14": TA.DEMA(c, timeperiod=14),
        "moving-average-triple-exponential@1 period=14": TA.TEMA(c, timeperiod=14),
        "moving-average-kaufman-adaptive@1 period=10": TA.KAMA(c, timeperiod=10),
        "moving-average-hull@1 period=20": TA.WMA(2 * wma10 - wma20, timeperiod=4),
        "macd-line@1 fast=12 slow=26": macd,
        "macd-signal@1 fast=12 slow=26 signal=9": signal,
        "macd-histogram@1 fast=12 slow=26 signal=9": macd - signal,
        "momentum-ratio@1 period=14": TA.ROCR100(c, timeperiod=14),
        "rolling-standard-deviation@1 period=20": TA.STDDEV(c, timeperiod=20, nbdev=1),
        "bollinger-band@1 period=20 deviations=2": upper,
        "bollinger-band@1 period=20 deviations=0": middle,
        "bollinger-band@1 period=20 deviations=-2": lower,
        "envelope-band@1 period=14 deviation=0.001": sma14 * 1.001,
        "envelope-band@1 period=14 deviation=-0.001": sma14 * (1 - 0.001),
        "trix@1 period=15": TA.TRIX(c, timeperiod=15),
        "rsi-series@1 period=14": TA.RSI(c, timeperiod=14),
        "percentage-price-oscillator@1 fast=12 slow=26": macd / ema26 * 100,
        "linear-regression-value@1 period=14": TA.LINEARREG(c, timeperiod=14),
        "linear-regression-slope@1 period=14": TA.LINEARREG_SLOPE(c, timeperiod=14),
        "bar-true-range@1": TA.TRANGE(h, lo, c),
        "atr-wilder@1 period=14": TA.ATR(h, lo, c, timeperiod=14),
        "cci@1 period=14": TA.CCI(h, lo, c, timeperiod=14),
        "parabolic-sar@1 step=0.02 maximum=0.2": TA.SAR(h, lo, acceleration=0.02, maximum=0.2),
        "williams-percent-r@1 period=14": TA.WILLR(h, lo, c, timeperiod=14),
        "awesome-oscillator@1 fast=5 slow=34": ao,
        "accelerator-oscillator@1 fast=5 slow=34 signal=5": ao - TA.SMA(ao, timeperiod=5),
        "demarker@1 period=14": demax / (demax + demin),
        "money-flow-index@1 period=14": TA.MFI(h, lo, c, v, timeperiod=14),
        "market-facilitation-index@1": (h - lo) / v,
        "on-balance-volume@1": TA.OBV(c, v),
        "accumulation-distribution@1": TA.AD(h, lo, c, v),
        "chaikin-oscillator@1 fast=3 slow=10": TA.ADOSC(h, lo, c, v, fastperiod=3, slowperiod=10),
        "force-index@1 period=13": TA.EMA(force, timeperiod=13),
        "bulls-power@1 period=13": h - ema13,
        "bears-power@1 period=13": lo - ema13,
        "adx@1 period=14": TA.ADX(h, lo, c, timeperiod=14),
        "plus-directional-indicator@1 period=14": TA.PLUS_DI(h, lo, c, timeperiod=14),
        "minus-directional-indicator@1 period=14": TA.MINUS_DI(h, lo, c, timeperiod=14),
        "stochastic-k@1 k_period=5 slowing=3": TA.SMA(fastk, timeperiod=3),
        "stochastic-d@1 k_period=5 slowing=3 d_period=3": slowd,
        "aroon-up@1 period=14": up,
        "aroon-down@1 period=14": down,
        "aroon-oscillator@1 period=14": TA.AROONOSC(h, lo, timeperiod=14),
        "ultimate-oscillator@1 short=7 medium=14 long=28": TA.ULTOSC(h, lo, c, 7, 14, 28),
        "price-channel-midpoint@1 period=9 shift=0": mid9,
        "price-channel-midpoint@1 period=26 shift=0": mid26,
        "price-channel-midpoint@1 period=52 shift=26": NP.concatenate(
            ([NP.nan] * 26, TA.MIDPRICE(h, lo, timeperiod=52)[:-26])
        ),
        "ichimoku-senkou-a@1 tenkan=9 kijun=26 shift=26": NP.concatenate(
            ([NP.nan] * 26, ((mid9 + mid26) / 2)[:-26])
        ),
    }
    plain_cases: dict[str, Values] = {
        "moving-average-smoothed@1 period=14": _smma(_list(c), 14),
        "alligator-line@1 period=13 shift=8": jaw,
        "alligator-line@1 period=8 shift=5": teeth,
        "alligator-line@1 period=5 shift=3": lips,
        "gator-oscillator@1 slow_period=13 slow_shift=8 fast_period=8 fast_shift=5": gap(
            jaw, teeth
        ),
        "gator-oscillator@1 slow_period=8 slow_shift=5 fast_period=5 fast_shift=3": gap(
            teeth, lips
        ),
        "relative-vigor-index@1 period=10": rvi,
        "relative-vigor-signal@1 period=10": rvi_signal,
        "vwap-session-anchored@1 session_start=0": vwap,
        "session-running-high@1 session_start=0": session_high,
        "session-running-low@1 session_start=0": session_low,
        "session-running-range@1 session_start=0": span(session_high, session_low),
        "session-running-range@1 session_start=28800": span(london_high, london_low),
        "heikin-ashi-open@1": ha_open,
        "heikin-ashi-close@1": ha_close,
    }
    cases = {name: _series(values) for name, values in talib_cases.items()}
    cases |= {name: _plain(values) for name, values in plain_cases.items()}
    return {
        "generator": "tools/dictionary/golden_talib.py",
        "talib": version,
        "numpy": str(NP.__version__),
        "seed": INDICATOR_SEED,
        "reference": {
            "talib": sorted(talib_cases),
            "formula": sorted(plain_cases),
        },
        "close": [b["close"] for b in bars],
        "bars": bars,
        "cases": dict(sorted(cases.items())),
    }


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
    indicators = _indicators(version)
    INDICATORS_OUT.parent.mkdir(parents=True, exist_ok=True)
    INDICATORS_OUT.write_text(
        json.dumps(indicators, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"golden_talib: wrote {len(indicators['cases'])} cases over {INDICATOR_BARS} bars "
        f"to {INDICATORS_OUT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
