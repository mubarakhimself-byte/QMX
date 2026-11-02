"""Write the golden values and the sanity series the wave's statistics blocks are tested against
(A13b).

This script is the only QMX code that imports arch, statsmodels and numpy for the statistics.
QML and its tests read the committed JSON and never import them. Run it from the repository root:

    uv run --no-project --python 3.14 --with arch==8.0.0 --with statsmodels==0.15.0 \
        --with numpy==2.5.4 python qml/tests/golden/statistics/reference_run.py

Each case's reference is named in the fixture. ``arch`` gives the variance ratio, ``statsmodels``
the Dickey-Fuller statistic, the regression behind the half-life, the autocorrelation and the
local-level Kalman filter. The rest are the formula of the page each entry cites, computed here
with numpy on every window afresh, so no running sum is shared with the blocks. The bars are a
seeded random walk written as five-decimal strings, so the fixture is the same on every run, and
the script refuses any other library version.
"""
# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportAttributeAccessIssue=false

from __future__ import annotations

import json
import math
import random
import sys
import warnings
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import arch
import numpy
import statsmodels
from arch.unitroot import VarianceRatio
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from statsmodels.tsa.statespace.structural import UnobservedComponents
from statsmodels.tsa.stattools import acf, adfuller

VERSIONS = {"arch": "8.0.0", "statsmodels": "0.15.0", "numpy": "2.5.4"}
SEED = 20261103
BARS = 2000
OUT = Path(__file__).resolve().parent
NP: Any = numpy
Values = list[float | None]
Window = Callable[[Any], float | None]


def _bars() -> list[dict[str, str]]:
    walk = random.Random(SEED)  # noqa: S311 - a seeded fixture walk, not a secret
    close = 1.10000
    bars: list[dict[str, str]] = []
    for _ in range(BARS):
        opened = close
        close = max(0.5, opened * math.exp(walk.gauss(0.0, 0.0012)))
        high = max(opened, close) * (1 + abs(walk.gauss(0.0, 0.0006)))
        low = min(opened, close) * (1 - abs(walk.gauss(0.0, 0.0006)))
        row = [opened, high, low, close]
        bars.append(
            dict(zip(("open", "high", "low", "close"), (f"{v:.5f}" for v in row), strict=True))
        )
    return bars


def _rolling(values: Any, size: int, of: Window) -> Values:
    """``of`` over each window of ``size`` values ending at each index; None before the first."""
    return [
        None if end < size else of(values[end - size : end]) for end in range(1, len(values) + 1)
    ]


def _text(values: Values) -> list[str | None]:
    return [None if v is None or math.isnan(v) else repr(float(v)) for v in values]


def _hurst(max_lag: int) -> Window:
    """QuantConnect LEAN's HurstExponent: the slope of log(standard deviation of lagged
    differences) on log(lag) for lags 2 to ``max_lag``, population variance, raw prices."""

    def of(prices: Any) -> float:
        lags = NP.arange(2, max_lag + 1)
        taus = []
        for lag in lags:
            diffs = prices[lag:] - prices[:-lag]
            sd = math.sqrt(float(NP.mean(diffs * diffs) - NP.mean(diffs) ** 2))
            taus.append(0.0 if sd == 0.0 else math.log(sd))
        return float(NP.polyfit(NP.log(lags), NP.array(taus), 1)[0])

    return of


def _variance_ratio(horizon: int, z: bool) -> Window:
    def of(prices: Any) -> float:
        test = VarianceRatio(NP.log(prices), lags=horizon, trend="c", debiased=True, robust=False)
        return float(test.stat if z else test.vr)

    return of


def _efficiency_ratio(prices: Any) -> float | None:
    path = float(NP.sum(NP.abs(NP.diff(prices))))
    return None if path == 0.0 else abs(float(prices[-1] - prices[0])) / path


def _half_life(prices: Any) -> float | None:
    fit = OLS(NP.diff(prices), add_constant(prices[:-1])).fit()
    beta = float(fit.params[1])
    return -math.log(2.0) / beta if beta < 0.0 else None


def _dickey_fuller(lags: int) -> Window:
    def of(prices: Any) -> float:
        return float(
            adfuller(prices, maxlag=lags, regression="c", autolag=None, result_object=False)[0]
        )

    return of


def _autocorrelation(lag: int) -> Window:
    def of(prices: Any) -> float:
        return float(acf(NP.diff(NP.log(prices)), nlags=lag, fft=False)[lag])

    return of


def _z_score(prices: Any) -> float | None:
    sd = float(NP.std(prices))
    return None if sd == 0.0 else (float(prices[-1]) - float(NP.mean(prices))) / sd


def _close_to_close(prices: Any) -> float:
    return float(NP.std(NP.diff(NP.log(prices)), ddof=1))


def _entropy(order: int) -> Window:
    """Bandt and Pompe's permutation entropy of the window, normalised by log(order!); a tie
    keeps the earlier value first."""

    def of(prices: Any) -> float:
        patterns: dict[tuple[int, ...], int] = {}
        for i in range(len(prices) - order + 1):
            key = tuple(int(k) for k in NP.argsort(prices[i : i + order], kind="stable"))
            patterns[key] = patterns.get(key, 0) + 1
        total = sum(patterns.values())
        h = -sum((c / total) * math.log(c / total) for c in patterns.values())
        return h / math.log(math.factorial(order))

    return of


def _cusum(window: int, drift: float, threshold: float, moment: int, closes: Any) -> Values:
    """NIST's tabular CUSUM on each log return standardised by the mean and sample standard
    deviation of the ``window`` returns before it; the signed larger side, both reset after an
    alarm."""
    returns = NP.diff(NP.log(closes))
    out: Values = [None]
    high = low = 0.0
    for t in range(len(returns)):
        if t < window:
            out.append(None)
            continue
        before = returns[t - window : t]
        sd = float(NP.std(before, ddof=1))
        if sd == 0.0:
            out.append(None)
            continue
        z = (float(returns[t]) - float(NP.mean(before))) / sd
        x = z if moment == 1 else z * z - 1.0
        high = max(0.0, high + x - drift)
        low = max(0.0, low - x - drift)
        out.append(high if high >= low else -low)
        if high > threshold or low > threshold:
            high = low = 0.0
    return out


def _kalman(signal_to_noise: float, closes: Any) -> Values:
    model = UnobservedComponents(closes, "llevel", use_exact_diffuse=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        level = model.filter([1.0, signal_to_noise]).filtered_state[0]
    return [float(v) for v in level]


def _range_estimator(kind: str, window: int, bars: Sequence[dict[str, str]]) -> Values:
    o, h, lo, c = (NP.array([float(b[k]) for b in bars]) for k in ("open", "high", "low", "close"))
    hl, co = NP.log(h / lo), NP.log(c / o)
    if kind == "parkinson":
        per_bar = hl * hl / (4.0 * math.log(2.0))
    elif kind == "garman-klass":
        per_bar = 0.5 * hl * hl - (2.0 * math.log(2.0) - 1.0) * co * co
    else:
        per_bar = NP.log(h / c) * NP.log(h / o) + NP.log(lo / c) * NP.log(lo / o)
    return _rolling(per_bar, window, lambda w: math.sqrt(float(NP.mean(w))))


def _choppiness(period: int, bars: Sequence[dict[str, str]]) -> Values:
    """LEAN's ChoppinessIndex: the first bar's true range is its high less its low."""
    h, lo, c = (NP.array([float(b[k]) for b in bars]) for k in ("high", "low", "close"))
    tr = NP.concatenate(([h[0] - lo[0]], NP.maximum(h[1:], c[:-1]) - NP.minimum(lo[1:], c[:-1])))
    out: Values = []
    for end in range(1, len(bars) + 1):
        if end < period:
            out.append(None)
            continue
        top, bottom = float(NP.max(h[end - period : end])), float(NP.min(lo[end - period : end]))
        if top == bottom:
            out.append(100.0)
            continue
        ratio = float(NP.sum(tr[end - period : end])) / (top - bottom)
        out.append(100.0 * math.log10(ratio) / math.log10(period))
    return out


def _momersion(period: int, closes: Any) -> Values:
    """LEAN's Momersion with no minimum period, missing where LEAN prints its placeholder 50."""
    out: Values = [None, None]
    products = [
        float((closes[t] - closes[t - 1]) * (closes[t - 1] - closes[t - 2]))
        for t in range(2, len(closes))
    ]
    for count in range(1, len(products) + 1):
        window = products[max(0, count - period) : count]
        zeros = sum(1 for p in window if p == 0.0)
        if count <= period or zeros >= 0.5 * len(window):
            out.append(None)
            continue
        up, down = sum(1 for p in window if p > 0.0), sum(1 for p in window if p < 0.0)
        out.append(100.0 * up / (up + down))
    return out


def _sanity() -> dict[str, Any]:
    """A random walk, a persistent walk (AR(1) returns, phi 0.5) and a pulled-back series
    (AR(1) prices, phi 0.8), with the bounds each statistic must read inside."""
    walk = random.Random(SEED + 1)  # noqa: S311 - a seeded fixture walk, not a secret
    n = 3000
    random_walk, persistent, reverting = [1.1], [1.1], [1.1]
    last = 0.0
    for _ in range(n - 1):
        e = walk.gauss(0.0, 0.001)
        random_walk.append(random_walk[-1] * math.exp(e))
        last = 0.5 * last + e
        persistent.append(persistent[-1] * math.exp(last))
        reverting.append(1.1 + 0.8 * (reverting[-1] - 1.1) + e)
    written = {"random_walk": random_walk, "persistent": persistent, "reverting": reverting}
    series = {k: [float(f"{v:.6f}") for v in values] for k, values in written.items()}
    bounds = {
        "hurst-exponent@1 window=1000 max_lag=20": {
            "random_walk": ["0.45", "0.55"],
            "persistent": ["0.55", "1.00"],
            "reverting": ["0.00", "0.45"],
        },
        "variance-ratio@1 window=1000 horizon=4": {
            "random_walk": ["0.90", "1.10"],
            "persistent": ["1.20", "3.00"],
            "reverting": ["0.00", "0.90"],
        },
    }
    readings = {
        name: {
            kind: _text(_rolling(NP.array(values), 1000, of))[-1] for kind, values in series.items()
        }
        for name, of in (
            ("hurst-exponent@1 window=1000 max_lag=20", _hurst(20)),
            ("variance-ratio@1 window=1000 horizon=4", _variance_ratio(4, z=False)),
        )
    }
    return {
        "series": {k: [f"{v:.6f}" for v in values] for k, values in series.items()},
        "bounds": bounds,
        "reference_reading_at_last_bar": readings,
    }


def main() -> int:
    found = {"arch": arch.__version__, "statsmodels": statsmodels.__version__}
    found["numpy"] = NP.__version__
    if found != VERSIONS:
        print(f"refused: this fixture is written with {VERSIONS}, found {found}", file=sys.stderr)
        return 1
    bars = _bars()
    closes = NP.array([float(b["close"]) for b in bars])
    cases: dict[str, Values] = {}
    references: dict[str, list[str]] = {}

    def add(name: str, values: Values, reference: str) -> None:
        cases[name] = values
        references.setdefault(reference, []).append(name)

    lean, formula = "formula: QuantConnect LEAN", "formula: the cited page, numpy 2.5.4"
    for max_lag in (20, 5):
        name = f"hurst-exponent@1 window=1000 max_lag={max_lag}"
        add(name, _rolling(closes, 1000, _hurst(max_lag)), f"{lean} HurstExponent.cs")
    for horizon in (2, 4, 8, 16):
        vr = _rolling(closes, 1000, _variance_ratio(horizon, z=False))
        add(f"variance-ratio@1 window=1000 horizon={horizon}", vr, "arch 8.0.0 VarianceRatio.vr")
    for horizon in (2, 16):
        z = _rolling(closes, 1000, _variance_ratio(horizon, z=True))
        name = f"variance-ratio-z-statistic@1 window=1000 horizon={horizon}"
        add(name, z, "arch 8.0.0 VarianceRatio.stat, robust=False")
    for period in (10, 30):
        er = _rolling(closes, period + 1, _efficiency_ratio)
        add(f"efficiency-ratio@1 period={period}", er, formula)
    hl = _rolling(closes, 100, _half_life)
    add("half-life-of-mean-reversion@1 window=100", hl, "statsmodels 0.15.0 OLS")
    for lags in (0, 1):
        df = _rolling(closes, 100, _dickey_fuller(lags))
        add(f"dickey-fuller-statistic@1 window=100 lags={lags}", df, "statsmodels 0.15.0 adfuller")
    for moment in (1, 2):
        name = f"cusum-change-point@1 window=100 drift=0.5 threshold=5 moment={moment}"
        add(name, _cusum(100, 0.5, 5.0, moment, closes), f"{formula} (NIST tabular CUSUM)")
    for ratio in ("0.01", "0.1"):
        name = f"kalman-local-level@1 signal_to_noise={ratio}"
        add(name, _kalman(float(ratio), closes), "statsmodels 0.15.0 UnobservedComponents")
    for lag in (1, 5):
        ac = _rolling(closes, 100, _autocorrelation(lag))
        add(f"return-autocorrelation@1 window=100 lag={lag}", ac, "statsmodels 0.15.0 acf")
    add("z-score@1 window=20", _rolling(closes, 20, _z_score), formula)
    add("close-to-close-volatility@1 window=20", _rolling(closes, 21, _close_to_close), formula)
    for kind in ("parkinson", "garman-klass", "rogers-satchell"):
        add(f"{kind}-volatility@1 window=20", _range_estimator(kind, 20, bars), formula)
    add("choppiness-index@1 period=14", _choppiness(14, bars), f"{lean} ChoppinessIndex.cs")
    add("momersion@1 period=20", _momersion(20, closes), f"{lean} Momersion.cs")
    add("permutation-entropy@1 window=100 order=3", _rolling(closes, 100, _entropy(3)), formula)
    fixture = {
        "generator": "qml/tests/golden/statistics/reference_run.py",
        **VERSIONS,
        "seed": SEED,
        "reference": references,
        "close": [b["close"] for b in bars],
        "bars": bars,
        "cases": {name: _text(cases[name]) for name in sorted(cases)},
    }
    (OUT / "reference.json").write_text(json.dumps(fixture, indent=1) + "\n", "utf-8")
    (OUT / "sanity.json").write_text(json.dumps(_sanity(), indent=1) + "\n", "utf-8")
    print(f"wrote {len(cases)} cases over {BARS} bars, and the sanity series")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
